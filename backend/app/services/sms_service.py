"""
短信服务 — 阿里云短信验证码
"""

import random
import json

import redis
from loguru import logger

from app.config import settings


_redis_client = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
    return _redis_client


def send_code(phone: str) -> dict:
    """
    发送短信验证码。
    返回 {"success": bool, "message": str}
    """
    r = _get_redis()

    # 60秒发送间隔限制
    cd_key = f"sms:cd:{phone}"
    if r.exists(cd_key):
        return {"success": False, "message": "发送太频繁，请60秒后再试"}

    # 每日发送上限
    daily_key = f"sms:daily:{phone}"
    daily_count = int(r.get(daily_key) or 0)
    if daily_count >= 10:
        return {"success": False, "message": "今日短信发送已达上限"}

    # 生成6位验证码
    code = f"{random.randint(0, 999999):06d}"

    # 调用阿里云短信API
    try:
        _send_aliyun_sms(phone, code)
    except Exception as e:
        logger.error(f"短信发送失败 {phone}: {e}")
        return {"success": False, "message": "短信发送失败，请稍后再试"}

    # 存储验证码到 Redis（5分钟过期）
    code_key = f"sms:code:{phone}"
    r.setex(code_key, 300, code)

    # 设置60秒冷却
    r.setex(cd_key, 60, "1")

    # 累加每日计数（首次设置24小时过期）
    pipe = r.pipeline()
    pipe.incr(daily_key)
    pipe.expire(daily_key, 86400)
    pipe.execute()

    logger.info(f"验证码已发送至 {phone[:3]}****{phone[-4:]}")
    return {"success": True, "message": "验证码已发送"}


def verify_code(phone: str, code: str) -> bool:
    """校验验证码"""
    r = _get_redis()
    code_key = f"sms:code:{phone}"
    stored = r.get(code_key)
    if stored and stored == code:
        r.delete(code_key)  # 验证成功后删除
        return True
    return False


def _send_aliyun_sms(phone: str, code: str):
    """调用阿里云短信 API"""
    from alibabacloud_dysmsapi20170525.client import Client
    from alibabacloud_dysmsapi20170525.models import SendSmsRequest
    from alibabacloud_tea_openapi.models import Config

    config = Config(
        access_key_id=settings.ALIYUN_SMS_ACCESS_KEY,
        access_key_secret=settings.ALIYUN_SMS_ACCESS_SECRET,
        endpoint="dysmsapi.aliyuncs.com",
    )
    client = Client(config)

    request = SendSmsRequest(
        phone_numbers=phone,
        sign_name=settings.ALIYUN_SMS_SIGN_NAME,
        template_code=settings.ALIYUN_SMS_TEMPLATE_CODE,
        template_param=json.dumps({"code": code}),
    )
    response = client.send_sms(request)
    body = response.body

    if body.code != "OK":
        raise RuntimeError(f"阿里云短信错误: {body.code} - {body.message}")
