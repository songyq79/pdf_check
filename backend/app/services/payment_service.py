"""
支付服务 — 微信Native支付 + 支付宝当面付
"""

import json
from typing import Optional

from loguru import logger

from app.config import settings


# ── 微信支付 ──────────────────────────────────────────────────


def create_wechat_pay(order_no: str, amount_cents: int, description: str) -> Optional[str]:
    """
    创建微信Native支付，返回 code_url（用于生成二维码）。
    返回 None 表示失败。
    """
    # 开发环境：如果配置不完整或证书缺失，模拟返回code_url
    from pathlib import Path
    cert_exists = (
        settings.WECHAT_PRIVATE_KEY_PATH
        and Path(settings.WECHAT_PRIVATE_KEY_PATH).exists()
    )
    if settings.DEBUG and (not settings.WECHAT_API_V3_KEY or not cert_exists):
        logger.warning(f"[DEV MODE] 微信支付未配置完整，模拟返回code_url: {order_no}")
        return f"weixin://wxpay/bizpayurl?pr={order_no[:16]}"

    try:
        from wechatpayv3 import WeChatPay

        wxpay = _get_wechat_client()
        resp_code, resp_data = wxpay.pay(
            description=description,
            out_trade_no=order_no,
            amount={"total": amount_cents},
            notify_url=settings.WECHAT_NOTIFY_URL,
        )
        if resp_code == 200:
            data = json.loads(resp_data) if isinstance(resp_data, str) else resp_data
            code_url = data.get("code_url")
            logger.info(f"微信支付创建成功: {order_no}, code_url: {code_url}")
            return code_url
        else:
            logger.error(f"微信支付创建失败: {resp_code} {resp_data}")
            return None
    except Exception as e:
        logger.error(f"微信支付异常: {e}")
        # 开发模式下异常也模拟返回code_url
        if settings.DEBUG:
            logger.warning(f"[DEV MODE] 微信支付异常，模拟返回code_url: {e}")
            return f"weixin://wxpay/bizpayurl?pr={order_no[:16]}"
        return None


def verify_wechat_callback(headers: dict, body: bytes) -> Optional[dict]:
    """
    验证微信支付回调签名，返回解密后的通知数据。
    返回 None 表示验签失败。
    """
    try:
        wxpay = _get_wechat_client()
        result = wxpay.callback(headers=headers, body=body)
        if result:
            resource = result.get("resource", {})
            logger.info(f"微信回调验签成功: {resource.get('out_trade_no')}")
            return result
        return None
    except Exception as e:
        logger.error(f"微信回调验签失败: {e}")
        return None


def refund_wechat(order_no: str, refund_no: str, amount_cents: int) -> bool:
    """微信退款"""
    # 开发环境：如果配置不完整或证书缺失，模拟成功
    from pathlib import Path
    cert_exists = (
        settings.WECHAT_PRIVATE_KEY_PATH
        and Path(settings.WECHAT_PRIVATE_KEY_PATH).exists()
    )
    if settings.DEBUG and (not settings.WECHAT_API_V3_KEY or not cert_exists):
        logger.warning(f"[DEV MODE] 微信支付未配置完整，模拟退款成功: {order_no}")
        return True

    try:
        wxpay = _get_wechat_client()
        resp_code, resp_data = wxpay.refund(
            out_trade_no=order_no,
            out_refund_no=refund_no,
            amount={"refund": amount_cents, "total": amount_cents, "currency": "CNY"},
        )
        if resp_code == 200:
            logger.info(f"微信退款成功: {order_no}")
            return True
        else:
            logger.error(f"微信退款失败: {resp_code} {resp_data}")
            return False
    except Exception as e:
        logger.error(f"微信退款异常: {e}")
        # 开发模式下异常也尝试模拟成功
        if settings.DEBUG:
            logger.warning(f"[DEV MODE] 微信退款异常，模拟成功: {e}")
            return True
        return False


def _get_wechat_client():
    from wechatpayv3 import WeChatPay, WeChatPayType

    with open(settings.WECHAT_PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
        private_key = f.read()

    kwargs = dict(
        wechatpay_type=WeChatPayType.NATIVE,
        mchid=settings.WECHAT_MCH_ID,
        private_key=private_key,
        cert_serial_no=settings.WECHAT_CERT_SERIAL_NO,
        appid=settings.WECHAT_APP_ID,
        apiv3_key=settings.WECHAT_API_V3_KEY,
        notify_url=settings.WECHAT_NOTIFY_URL,
        cert_dir=str(settings.STORAGE_PATH / "wechat"),
    )
    # 公钥模式：配置了公钥文件和公钥ID时启用
    if settings.WECHAT_PUBLIC_KEY_PATH and settings.WECHAT_PUBLIC_KEY_ID:
        from pathlib import Path
        pub_key_path = Path(settings.WECHAT_PUBLIC_KEY_PATH)
        if pub_key_path.exists():
            with open(pub_key_path, "r", encoding="utf-8") as f:
                kwargs["public_key"] = f.read()
            kwargs["public_key_id"] = settings.WECHAT_PUBLIC_KEY_ID

    return WeChatPay(**kwargs)


# ── 支付宝 ────────────────────────────────────────────────────


def create_alipay(order_no: str, amount_cents: int, description: str) -> Optional[str]:
    """
    创建支付宝当面付，返回二维码链接。
    返回 None 表示失败。
    """
    try:
        client = _get_alipay_client()
        amount_yuan = f"{amount_cents / 100:.2f}"

        from alipay import AliPay
        result = client.api_alipay_trade_precreate(
            subject=description,
            out_trade_no=order_no,
            total_amount=amount_yuan,
            notify_url=settings.ALIPAY_NOTIFY_URL,
        )
        if result.get("code") == "10000":
            qr_code = result.get("qr_code")
            logger.info(f"支付宝当面付创建成功: {order_no}")
            return qr_code
        else:
            logger.error(f"支付宝创建失败: {result}")
            return None
    except Exception as e:
        logger.error(f"支付宝支付异常: {e}")
        return None


def verify_alipay_callback(params: dict) -> bool:
    """验证支付宝回调签名"""
    try:
        client = _get_alipay_client()
        sign = params.pop("sign", None)
        sign_type = params.pop("sign_type", None)
        result = client.verify(params, sign)
        logger.info(f"支付宝回调验签: {result}, 订单: {params.get('out_trade_no')}")
        return result
    except Exception as e:
        logger.error(f"支付宝回调验签失败: {e}")
        return False


def refund_alipay(order_no: str, refund_no: str, amount_cents: int) -> bool:
    """支付宝退款"""
    # 开发环境：如果配置不完整，模拟成功
    from pathlib import Path
    keys_exist = (
        settings.ALIPAY_PRIVATE_KEY_PATH
        and Path(settings.ALIPAY_PRIVATE_KEY_PATH).exists()
        and settings.ALIPAY_APP_CERT_PATH
        and Path(settings.ALIPAY_APP_CERT_PATH).exists()
    )
    if settings.DEBUG and not keys_exist:
        logger.warning(f"[DEV MODE] 支付宝支付未配置完整，模拟退款成功: {order_no}")
        return True

    try:
        client = _get_alipay_client()
        amount_yuan = f"{amount_cents / 100:.2f}"
        result = client.api_alipay_trade_refund(
            out_trade_no=order_no,
            refund_amount=amount_yuan,
            out_request_no=refund_no,
        )
        if result.get("code") == "10000":
            logger.info(f"支付宝退款成功: {order_no}")
            return True
        else:
            logger.error(f"支付宝退款失败: {result}")
            return False
    except Exception as e:
        logger.error(f"支付宝退款异常: {e}")
        # 开发模式下异常也尝试模拟成功
        if settings.DEBUG:
            logger.warning(f"[DEV MODE] 支付宝退款异常，模拟成功: {e}")
            return True
        return False


def _get_alipay_client():
    from alipay import DCAliPay

    with open(settings.ALIPAY_PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
        private_key = f.read()
    with open(settings.ALIPAY_APP_CERT_PATH, "r", encoding="utf-8") as f:
        app_cert = f.read()
    with open(settings.ALIPAY_ALIPAY_CERT_PATH, "r", encoding="utf-8") as f:
        alipay_cert = f.read()
    with open(settings.ALIPAY_ROOT_CERT_PATH, "r", encoding="utf-8") as f:
        root_cert = f.read()

    return DCAliPay(
        appid=settings.ALIPAY_APP_ID,
        app_notify_url=settings.ALIPAY_NOTIFY_URL,
        app_private_key_string=private_key,
        app_public_key_cert_string=app_cert,
        alipay_public_key_cert_string=alipay_cert,
        alipay_root_cert_string=root_cert,
        sign_type="RSA2",
    )
