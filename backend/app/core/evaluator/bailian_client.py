"""
百炼大模型API调用客户端
支持两种模式：
1. 文件上传模式（推荐）- 使用三步走流程上传文件到百炼
2. 文本对话模式 - 直接发送文本到百炼对话API
"""

import json
import logging
import hashlib
import os
from typing import Dict, Any, Optional
from http import HTTPStatus
import requests

logger = logging.getLogger(__name__)


class BailianFileUploadClient:
    """百炼文件上传客户端（使用阿里云SDK）"""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        workspace_id: str,
        category_id: str = "cate_default",
        region: str = "cn-beijing"
    ):
        """
        初始化文件上传客户端

        :param access_key_id: 阿里云访问密钥ID
        :param access_key_secret: 阿里云访问密钥Secret
        :param workspace_id: 百炼工作空间ID
        :param category_id: 文件分类ID
        :param region: 区域
        """
        self.workspace_id = workspace_id
        self.category_id = category_id

        # 导入阿里云SDK
        try:
            from alibabacloud_bailian20231229.client import Client as BailianClient
            from alibabacloud_credentials.client import Client as CredentialClient
            from alibabacloud_tea_openapi import models as open_api_models
            from alibabacloud_bailian20231229 import models as bailian_models
            from alibabacloud_tea_util import models as util_models

            self.bailian_models = bailian_models
            self.util_models = util_models

            # 创建客户端
            credential = CredentialClient()
            config = open_api_models.Config(
                credential=credential,
                access_key_id=access_key_id,
                access_key_secret=access_key_secret
            )
            config.endpoint = f'bailian.{region}.aliyuncs.com'
            self.client = BailianClient(config)

            logger.info(f"百炼文件上传客户端初始化成功，工作空间: {workspace_id}")

        except ImportError as e:
            logger.error(f"阿里云SDK未安装: {str(e)}")
            raise ImportError(
                "请安装阿里云百炼SDK: pip install alibabacloud-bailian20231229 "
                "alibabacloud-credentials alibabacloud-tea-openapi alibabacloud-tea-util"
            )

    @staticmethod
    def calculate_md5_bytes(file_bytes: bytes) -> str:
        """计算字节的MD5"""
        md5_obj = hashlib.md5()
        md5_obj.update(file_bytes)
        return md5_obj.hexdigest()

    def step1_apply_upload_lease(
        self,
        file_name: str,
        file_bytes: bytes
    ) -> Dict[str, Any]:
        """
        第一步：申请文件上传许可，获取临时上传链接

        :param file_name: 文件名
        :param file_bytes: 文件字节数据
        :return: 包含上传参数的字典
        """
        try:
            file_size = len(file_bytes)
            apply_request = self.bailian_models.ApplyFileUploadLeaseRequest(
                category_type="UNSTRUCTURED",
                file_name=file_name,
                md_5=self.calculate_md5_bytes(file_bytes),
                size_in_bytes=file_size,
            )
            runtime = self.util_models.RuntimeOptions()
            headers = {}

            response = self.client.apply_file_upload_lease_with_options(
                workspace_id=self.workspace_id,
                category_id=self.category_id,
                request=apply_request,
                headers=headers,
                runtime=runtime
            )

            # 提取上传参数
            upload_params = {
                'file_upload_lease_id': response.body.data.file_upload_lease_id,
                'upload_url': response.body.data.param.url,
                'headers': response.body.data.param.headers,
                'method': response.body.data.param.method
            }

            logger.info(f"成功获取文件上传许可: {upload_params['file_upload_lease_id']}")
            return upload_params

        except Exception as error:
            error_msg = getattr(error, 'message', str(error))
            logger.error(f"申请文件上传许可失败: {error_msg}")
            raise BailianAPIError(f"申请文件上传许可失败: {error_msg}")

    def step2_upload_file(
        self,
        upload_url: str,
        file_data: bytes,
        headers: Dict[str, str]
    ) -> bool:
        """
        第二步：使用临时链接上传文件

        :param upload_url: 上传链接
        :param file_data: 文件字节数据
        :param headers: 上传所需请求头
        :return: 上传是否成功
        """
        try:
            response = requests.put(upload_url, data=file_data, headers=headers)

            if response.status_code == 200:
                logger.info("文件上传成功")
                return True
            else:
                logger.error(f"文件上传失败，响应码: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"文件上传过程中发生错误: {str(e)}")
            raise BailianAPIError(f"文件上传失败: {str(e)}")

    def step3_add_file_to_workspace(
        self,
        lease_id: str,
        file_name: str
    ) -> Dict[str, Any]:
        """
        第三步：将文件添加到工作空间

        :param lease_id: 文件上传许可ID（来自第一步）
        :param file_name: 文件名
        :return: 添加结果，包含文件ID
        """
        try:
            add_request = self.bailian_models.AddFileRequest(
                category_id=self.category_id,
                lease_id=lease_id,
                original_file_url=file_name,
                parser="DASHSCOPE_DOCMIND",  # 使用文档解析器
            )
            runtime = self.util_models.RuntimeOptions()
            headers = {}

            response = self.client.add_file_with_options(
                self.workspace_id,
                add_request,
                headers,
                runtime
            )

            result = {
                'success': response.body.success,
                'code': response.body.code,
                'file_id': response.body.data.file_id if response.body.data else None,
                'parser': response.body.data.parser if response.body.data else None
            }

            logger.info(f"文件添加到工作空间成功: {result}")
            return result

        except Exception as error:
            error_msg = getattr(error, 'message', str(error))
            logger.error(f"文件添加到工作空间失败: {error_msg}")
            raise BailianAPIError(f"文件添加到工作空间失败: {error_msg}")

    def upload_file(
        self,
        file_name: str,
        file_bytes: bytes
    ) -> Dict[str, Any]:
        """
        完整的文件上传流程（三步走）

        :param file_name: 文件名
        :param file_bytes: 文件字节数据
        :return: 包含文件ID的结果
        """
        try:
            file_size = len(file_bytes)
            if file_size == 0:
                raise ValueError("文件大小为0字节，无法上传")

            logger.info(f"开始上传文件: {file_name}, 大小: {file_size} 字节")

            # 第一步：申请上传许可
            upload_params = self.step1_apply_upload_lease(file_name, file_bytes)

            # 第二步：上传文件
            success = self.step2_upload_file(
                upload_params['upload_url'],
                file_bytes,
                upload_params['headers']
            )

            if not success:
                raise BailianAPIError("文件上传失败")

            # 第三步：添加到工作空间
            workspace_result = self.step3_add_file_to_workspace(
                upload_params['file_upload_lease_id'],
                file_name
            )

            return {
                'file_id': workspace_result['file_id'],
                'file_name': file_name,
                'file_size': file_size,
                'parser': workspace_result['parser']
            }

        except Exception as e:
            logger.error(f"文件上传流程失败: {str(e)}")
            raise

    def get_file_status(self, file_id: str) -> Dict[str, Any]:
        """
        获取文件在知识库中的状态

        :param file_id: 文件ID
        :return: 文件状态信息
        """
        try:
            headers = {}
            runtime = self.util_models.RuntimeOptions()
            response = self.client.describe_file_with_options(
                self.workspace_id,
                file_id,
                headers,
                runtime
            )

            if response.body.success and response.body.data:
                file_info = response.body.data
                return {
                    'file_id': getattr(file_info, 'file_id', None),
                    'status': getattr(file_info, 'status', None),
                    'progress': getattr(file_info, 'progress', None),
                    'message': getattr(file_info, 'message', None)
                }

            return {'status': 'UNKNOWN'}

        except Exception as error:
            error_msg = getattr(error, 'message', str(error))
            logger.error(f"获取文件状态失败: {error_msg}")
            raise BailianAPIError(f"获取文件状态失败: {error_msg}")


class BailianTextClient:
    """百炼文本对话客户端（使用dashscope SDK）"""

    def __init__(
        self,
        api_key: str,
        model: str = "qwen-max",
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        初始化文本对话客户端

        :param api_key: API密钥
        :param model: 模型版本
        :param timeout: 超时时间（秒）
        :param max_retries: 最大重试次数
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        # 导入dashscope
        try:
            from dashscope import Generation
            self.Generation = Generation
            logger.info(f"dashscope SDK加载成功，模型: {self.model}")
        except ImportError:
            logger.error("dashscope SDK未安装")
            raise ImportError("请安装dashscope: pip install dashscope")

    def call_api(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        top_p: float = 0.8
    ) -> Dict[str, Any]:
        """
        调用百炼对话API

        :param prompt: 提示词
        :param max_tokens: 最大token数
        :param temperature: 温度参数
        :param top_p: top_p参数
        :return: API返回结果
        """
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                logger.info(f"调用百炼API，模型: {self.model}, prompt长度: {len(prompt)}")

                messages = [{'role': 'user', 'content': prompt}]

                response = self.Generation.call(
                    api_key=self.api_key,
                    model=self.model,
                    messages=messages,
                    result_format='message',
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    timeout=self.timeout
                )

                if response.status_code != HTTPStatus.OK:
                    error_msg = f"API调用失败: code={response.status_code}, message={response.message}"
                    logger.error(error_msg)

                    if response.status_code in [500, 503, 504]:
                        retry_count += 1
                        logger.warning(f"服务器错误，正在进行第 {retry_count} 次重试")
                        if retry_count >= self.max_retries:
                            raise BailianAPIError(error_msg)
                        continue
                    else:
                        raise BailianAPIError(error_msg)

                logger.info("API调用成功")

                # 提取响应文本（处理message格式）
                output_text = ""
                if hasattr(response.output, 'choices') and response.output.choices:
                    # message格式: 从choices中提取
                    output_text = response.output.choices[0].message.content
                elif hasattr(response.output, 'text') and response.output.text:
                    # text格式: 直接使用text字段
                    output_text = response.output.text
                elif isinstance(response.output, dict):
                    # 字典格式: 尝试多种提取方式
                    if 'choices' in response.output and response.output['choices']:
                        output_text = response.output['choices'][0]['message']['content']
                    elif 'text' in response.output:
                        output_text = response.output['text']

                return {
                    "output": {
                        "text": output_text,
                        "finish_reason": response.output.finish_reason if hasattr(response.output, 'finish_reason') else None
                    },
                    "usage": response.usage if hasattr(response, 'usage') else None,
                    "request_id": response.request_id
                }

            except Exception as e:
                error_str = str(e).lower()
                if "timeout" in error_str or "timed out" in error_str:
                    retry_count += 1
                    logger.warning(f"超时异常，正在进行第 {retry_count} 次重试")
                    if retry_count >= self.max_retries:
                        raise BailianAPIError(f"API调用超时: {str(e)}")
                    continue
                else:
                    logger.error(f"API调用异常: {str(e)}")
                    raise BailianAPIError(f"API调用异常: {str(e)}")

        raise BailianAPIError(f"API调用失败，已重试{self.max_retries}次")

    def evaluate_paper(self, prompt: str) -> Dict[str, Any]:
        """
        评价论文（文本模式）

        :param prompt: 包含论文内容的提示词
        :return: 评价结果
        """
        result = self.call_api(prompt)

        try:
            output_text = result.get("output", {}).get("text", "")

            if not output_text:
                raise ValueError("API返回的文本为空")

            logger.debug(f"API返回文本: {output_text[:200]}...")

            evaluation = json.loads(output_text)

            required_fields = ["score", "strengths", "weaknesses", "suggestions"]
            for field in required_fields:
                if field not in evaluation:
                    raise ValueError(f"评价结果缺少字段: {field}")

            if not (0 <= evaluation["score"] <= 100):
                logger.warning(f"评分超出范围: {evaluation['score']}，将调整为0-100")
                evaluation["score"] = max(0, min(100, evaluation["score"]))

            return evaluation

        except json.JSONDecodeError as e:
            logger.error(f"API返回的JSON解析失败: {str(e)}")
            logger.error(f"原始文本: {output_text}")
            raise BailianAPIError("API返回格式错误，无法解析评价结果")

        except (KeyError, ValueError) as e:
            logger.error(f"评价结果格式错误: {str(e)}")
            raise BailianAPIError(f"评价结果格式错误: {str(e)}")


class BailianAPIError(Exception):
    """百炼API错误"""
    pass


# 客户端工厂函数
def get_upload_client(
    access_key_id: str,
    access_key_secret: str,
    workspace_id: str,
    category_id: str = "cate_default"
) -> BailianFileUploadClient:
    """
    获取文件上传客户端

    :param access_key_id: 阿里云访问密钥ID
    :param access_key_secret: 阿里云访问密钥Secret
    :param workspace_id: 百炼工作空间ID
    :param category_id: 文件分类ID
    :return: 文件上传客户端
    """
    return BailianFileUploadClient(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        workspace_id=workspace_id,
        category_id=category_id
    )


def get_text_client(
    api_key: str,
    model: str = "qwen-max",
    timeout: int = 60,
    max_retries: int = 3
) -> BailianTextClient:
    """
    获取文本对话客户端

    :param api_key: API密钥
    :param model: 模型版本
    :param timeout: 超时时间
    :param max_retries: 最大重试次数
    :return: 文本对话客户端
    """
    return BailianTextClient(
        api_key=api_key,
        model=model,
        timeout=timeout,
        max_retries=max_retries
    )


# 向后兼容的旧接口
def get_client(api_key: str = None, **kwargs):
    """
    向后兼容的客户端获取函数
    默认返回文本对话客户端

    :param api_key: API密钥
    :param kwargs: 其他参数
    :return: 文本对话客户端
    """
    logger.warning("get_client() 已弃用，建议使用 get_text_client() 或 get_upload_client()")
    return get_text_client(api_key=api_key, **kwargs)
