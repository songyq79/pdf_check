"""
第三方登录服务 — 微信扫码登录 + 支付宝登录
"""

import urllib.parse
from typing import Optional

import httpx
from loguru import logger

from app.config import settings


# ── 微信扫码登录 ──────────────────────────────────────────────


def get_wechat_login_url(state: str = "login") -> str:
    """生成微信开放平台网站应用扫码登录URL"""
    params = {
        "appid": settings.WECHAT_LOGIN_APP_ID,
        "redirect_uri": settings.WECHAT_REDIRECT_URI,
        "response_type": "code",
        "scope": "snsapi_login",
        "state": state,
    }
    return f"https://open.weixin.qq.com/connect/qrconnect?{urllib.parse.urlencode(params)}#wechat_redirect"


def wechat_code_to_user(code: str) -> Optional[dict]:
    """
    用微信授权 code 换取用户信息。
    返回 {"openid": str, "nickname": str, "avatar": str} 或 None。
    """
    try:
        # 1. code 换 access_token
        token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
        token_params = {
            "appid": settings.WECHAT_LOGIN_APP_ID,
            "secret": settings.WECHAT_APP_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        }
        with httpx.Client(timeout=10) as client:
            resp = client.get(token_url, params=token_params)
            token_data = resp.json()

        if "errcode" in token_data:
            logger.error(f"微信获取token失败: {token_data}")
            return None

        access_token = token_data["access_token"]
        openid = token_data["openid"]

        # 2. 获取用户信息
        userinfo_url = "https://api.weixin.qq.com/sns/userinfo"
        userinfo_params = {
            "access_token": access_token,
            "openid": openid,
            "lang": "zh_CN",
        }
        with httpx.Client(timeout=10) as client:
            resp = client.get(userinfo_url, params=userinfo_params)
            user_data = resp.json()

        if "errcode" in user_data:
            logger.error(f"微信获取用户信息失败: {user_data}")
            return None

        return {
            "openid": openid,
            "nickname": user_data.get("nickname", ""),
            "avatar": user_data.get("headimgurl", ""),
        }
    except Exception as e:
        logger.error(f"微信登录异常: {e}")
        return None


# ── 支付宝登录 ────────────────────────────────────────────────


def get_alipay_login_url(state: str = "login") -> str:
    """生成支付宝授权登录URL"""
    params = {
        "app_id": settings.ALIPAY_APP_ID,
        "scope": "auth_user",
        "redirect_uri": settings.ALIPAY_REDIRECT_URI,
        "state": state,
    }
    return f"https://openauth.alipay.com/oauth2/publicAppAuthorize.htm?{urllib.parse.urlencode(params)}"


def alipay_code_to_user(auth_code: str) -> Optional[dict]:
    """
    用支付宝授权 code 换取用户信息。
    返回 {"uid": str, "nickname": str, "avatar": str} 或 None。
    """
    try:
        from app.services.payment_service import _get_alipay_client

        client = _get_alipay_client()

        # 1. auth_code 换 access_token
        token_result = client.api_alipay_system_oauth_token(grant_type="authorization_code", code=auth_code)
        if "error_response" in str(token_result):
            logger.error(f"支付宝获取token失败: {token_result}")
            return None

        access_token = token_result.get("access_token")
        user_id = token_result.get("user_id")

        # 2. 获取用户信息
        user_result = client.api_alipay_user_info_share(access_token)
        if user_result.get("code") != "10000":
            logger.error(f"支付宝获取用户信息失败: {user_result}")
            return None

        return {
            "uid": user_id,
            "nickname": user_result.get("nick_name", ""),
            "avatar": user_result.get("avatar", ""),
        }
    except Exception as e:
        logger.error(f"支付宝登录异常: {e}")
        return None
