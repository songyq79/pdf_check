"""
智能评价API接口
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
import os
from pathlib import Path
from datetime import datetime

from app.config import settings
from app.schemas.evaluation import EvaluationResponse, EvaluationResult
from app.core.evaluator.bailian_client import (
    get_upload_client,
    get_text_client,
    BailianAPIError
)
from app.core.evaluator.prompts import get_prompt, get_all_dimensions, get_dimension_name
from app.core.evaluator.report_generator import generate_report, ReportGenerationError
from app.services.file_service import save_upload_file, validate_file
from docx import Document
import uuid

router = APIRouter()


@router.post("/upload", response_model=EvaluationResponse)
async def evaluate_paper(file: UploadFile = File(...)):
    """
    上传论文并进行智能评价

    :param file: 上传的Word文档
    :return: 评价结果
    """
    try:
        # API Key 检查：给出明确提示而非神秘的 503
        if not settings.BAILIAN_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="智能评价服务未配置：请在 backend/.env 中设置 BAILIAN_API_KEY",
            )

        # 验证文件
        validate_file(file, max_size_mb=settings.MAX_FILE_SIZE)

        # 保存上传文件
        file_path = await save_upload_file(file, settings.UPLOAD_PATH)
        logger.info(f"文件已保存: {file_path}")

        # 解析Word文档
        try:
            doc = Document(file_path)
            title = extract_title(doc)
            content = extract_content(doc)
            logger.info(f"文档解析完成，标题: {title}, 内容长度: {len(content)}")
        except Exception as e:
            logger.error(f"文档解析失败: {str(e)}")
            raise HTTPException(status_code=400, detail="Word文档解析失败，请检查文件格式")

        # 调用百炼API进行评价
        try:
            # 优先使用文件上传模式（如果配置了必要的凭据）
            use_file_upload = (
                settings.BAILIAN_ACCESS_KEY_ID and
                settings.BAILIAN_ACCESS_KEY_SECRET and
                settings.BAILIAN_WORKSPACE_ID
            )

            if use_file_upload:
                try:
                    logger.info("使用文件上传模式进行评价")
                    with open(file_path, 'rb') as f:
                        file_bytes = f.read()
                    upload_client = get_upload_client(
                        access_key_id=settings.BAILIAN_ACCESS_KEY_ID,
                        access_key_secret=settings.BAILIAN_ACCESS_KEY_SECRET,
                        workspace_id=settings.BAILIAN_WORKSPACE_ID,
                        category_id=settings.BAILIAN_CATEGORY_ID
                    )
                    upload_result = upload_client.upload_file(
                        file_name=file.filename,
                        file_bytes=file_bytes
                    )
                    logger.info(f"文件上传成功，文件ID: {upload_result['file_id']}")
                    logger.warning("文件上传成功，但评价功能尚未实现，回退到文本模式")
                    use_file_upload = False
                except ImportError:
                    logger.warning("阿里云百炼SDK未安装，自动切换到文本对话模式")
                    use_file_upload = False

            if not use_file_upload:
                logger.info("使用文本对话模式进行评价")
                # 创建文本对话客户端
                client = get_text_client(
                    api_key=settings.BAILIAN_API_KEY,
                    model=settings.BAILIAN_MODEL,
                    timeout=settings.BAILIAN_TIMEOUT,
                    max_retries=settings.BAILIAN_MAX_RETRIES
                )

                # 逐个维度调用API
                dimensions = get_all_dimensions()
                results = {}

                for dimension in dimensions:
                    logger.info(f"开始评价维度: {dimension}")
                    prompt = get_prompt(dimension, title, content)
                    evaluation = client.evaluate_paper(prompt)
                    results[dimension] = evaluation
                    logger.info(f"维度 {dimension} 评价完成，得分: {evaluation['score']}")

        except BailianAPIError as e:
            logger.error(f"API调用失败: {str(e)}")
            raise HTTPException(status_code=503, detail=f"评价服务暂时不可用: {str(e)}")

        # 计算综合评分
        avg_score = sum(r["score"] for r in results.values()) / len(results)

        # 构建评价响应
        response = EvaluationResponse(
            paper_title=title,
            overall_score=round(avg_score, 1),
            dimensions={
                dimension: EvaluationResult(
                    dimension_name=get_dimension_name(dimension),
                    score=results[dimension]["score"],
                    strengths=results[dimension]["strengths"],
                    weaknesses=results[dimension]["weaknesses"],
                    suggestions=results[dimension]["suggestions"]
                )
                for dimension in dimensions
            },
            evaluated_at=datetime.now()
        )

        logger.info(f"评价完成，综合得分: {avg_score}")

        # 生成评价报告
        report_id = None
        report_download_url = None

        try:
            report_id = str(uuid.uuid4())
            report_filename = f"{report_id}_report.docx"
            report_path = settings.OUTPUT_PATH / report_filename

            generate_report(
                evaluation=response,
                output_path=report_path,
                include_chart=True
            )

            logger.info(f"评价报告生成成功: {report_path}")
            report_download_url = f"/api/v1/evaluation/download/{report_id}"

        except ReportGenerationError as e:
            logger.error(f"报告生成失败: {str(e)}")
            logger.warning("报告生成失败，仅返回评价结果")

        # 更新响应对象
        response.report_id = report_id
        response.report_download_url = report_download_url

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"评价过程出错: {str(e)}")
        raise HTTPException(status_code=500, detail="评价过程出错，请稍后重试")

    finally:
        # 清理临时文件（可选：延后到定时任务）
        pass


def extract_title(doc: Document) -> str:
    """
    从Word文档中提取标题

    :param doc: Document对象
    :return: 标题
    """
    # 尝试从第一段或第一个标题段落提取
    for para in doc.paragraphs:
        text = para.text.strip()
        if text and len(text) > 0:
            return text[:100]  # 限制标题长度

    return "未命名论文"


def extract_content(doc: Document) -> str:
    """
    从Word文档中提取正文内容

    :param doc: Document对象
    :return: 正文内容
    """
    paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    content = "\n".join(paragraphs)

    # 限制内容长度（避免超过API限制）
    max_length = 10000
    if len(content) > max_length:
        logger.warning(f"文档内容过长({len(content)}字符)，将截取前{max_length}字符")
        content = content[:max_length] + "\n...(内容已截断)"

    return content


@router.get("/download/{report_id}")
async def download_report(report_id: str):
    """
    下载评价报告

    :param report_id: 报告ID
    :return: Word文档
    """
    try:
        # 构建报告路径
        report_filename = f"{report_id}_report.docx"
        report_path = settings.OUTPUT_PATH / report_filename

        # 检查文件是否存在
        if not report_path.exists():
            logger.warning(f"报告文件不存在: {report_path}")
            raise HTTPException(status_code=404, detail="报告文件不存在或已过期")

        logger.info(f"开始下载报告: {report_path}")

        # 返回文件
        return FileResponse(
            path=str(report_path),
            filename=f"论文评价报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail="下载报告失败，请稍后重试")
