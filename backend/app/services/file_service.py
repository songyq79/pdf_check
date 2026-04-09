"""
文件服务 - 处理文件上传、下载、清理等操作
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from fastapi import UploadFile, HTTPException
from loguru import logger
import uuid


async def save_upload_file(
    upload_file: UploadFile,
    destination_dir: Path,
    filename: Optional[str] = None
) -> Path:
    """
    保存上传的文件

    :param upload_file: 上传的文件
    :param destination_dir: 目标目录
    :param filename: 自定义文件名（可选）
    :return: 保存后的文件路径
    """
    # 确保目标目录存在
    destination_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    if filename is None:
        ext = Path(upload_file.filename).suffix
        filename = f"{uuid.uuid4()}{ext}"

    file_path = destination_dir / filename

    # 保存文件
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)  #内置一个函数，用于将文件对象中的内容从源文件对象复制到目标文件对象。

        logger.info(f"文件已保存: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"保存文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail="文件保存失败")


def validate_file(
    upload_file: UploadFile,
    allowed_types: list = [".docx"],
    max_size_mb: int = 20
) -> None:
    """
    验证上传的文件

    :param upload_file: 上传的文件
    :param allowed_types: 允许的文件类型
    :param max_size_mb: 最大文件大小（MB）
    :raises: HTTPException 如果验证失败
    """
    # 检查文件类型
    ext = Path(upload_file.filename).suffix.lower()
    if ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}，仅支持: {', '.join(allowed_types)}"
        )

    # 检查文件大小
    upload_file.file.seek(0, 2)
    file_size = upload_file.file.tell()
    upload_file.file.seek(0)

    # 检查空文件
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="上传的文件内容为空，请检查文档后重新上传"
        )

    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大: {file_size / 1024 / 1024:.2f}MB，最大允许: {max_size_mb}MB"
        )

    logger.info(f"文件验证通过: {upload_file.filename}, 大小: {file_size / 1024 / 1024:.2f}MB")


def clean_old_files(directory: Path, retention_hours: int = 24) -> int:
    """
    清理旧文件

    :param directory: 目标目录
    :param retention_hours: 保留时间（小时）
    :return: 删除的文件数量
    """
    if not directory.exists():
        return 0

    cutoff_time = datetime.now() - timedelta(hours=retention_hours)
    deleted_count = 0

    for file_path in directory.iterdir():
        if file_path.is_file():
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

            if file_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"已删除旧文件: {file_path}")
                except Exception as e:
                    logger.error(f"删除文件失败: {file_path}, 错误: {str(e)}")

    logger.info(f"清理完成，删除了 {deleted_count} 个文件")
    return deleted_count


def get_file_info(file_path: Path) -> dict:
    """
    获取文件信息

    :param file_path: 文件路径
    :return: 文件信息字典
    """
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    stat = file_path.stat()

    return {
        "name": file_path.name,
        "size": stat.st_size,
        "size_mb": stat.st_size / 1024 / 1024,
        "created_at": datetime.fromtimestamp(stat.st_ctime),
        "modified_at": datetime.fromtimestamp(stat.st_mtime),
    }
