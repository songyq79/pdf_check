"""
统一 AI 客户端
- 百炼（通义千问）主力，DeepSeek 自动备用
- 支持 async（主流）和 sync（同步场景）
- 内置重试、超时、详细日志
"""

import asyncio
import json
import re
import time
from typing import Optional
from loguru import logger


# ─────────────────────────────────────────────────────────────
# 底层：各模型异步调用
# ─────────────────────────────────────────────────────────────

async def _call_qwen(prompt: str) -> str:
    """通义千问（百炼）异步调用"""
    try:
        import dashscope
        from dashscope import Generation
    except ImportError:
        raise RuntimeError("请安装 dashscope: pip install dashscope")

    from app.config import settings
    if not settings.BAILIAN_API_KEY:
        raise RuntimeError("BAILIAN_API_KEY 未配置")

    dashscope.api_key = settings.BAILIAN_API_KEY

    def _sync_call():
        resp = Generation.call(
            model=settings.BAILIAN_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        if resp.status_code != 200:
            raise RuntimeError(f"百炼错误 {resp.status_code}: {resp.message}")
        return resp.output.text

    return await asyncio.to_thread(_sync_call)


async def _call_deepseek(prompt: str) -> str:
    """DeepSeek 异步调用（百炼失败时自动备用）"""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise RuntimeError("请安装 openai>=1.0: pip install openai")

    from app.config import settings
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY 未配置")

    client = AsyncOpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )
    resp = await client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return resp.choices[0].message.content


# 调用优先级：百炼 → DeepSeek
_MODEL_POOL = [
    ("百炼/千问", _call_qwen),
    ("DeepSeek",  _call_deepseek),
]


# ─────────────────────────────────────────────────────────────
# 核心：带重试、fallback 的异步调用
# ─────────────────────────────────────────────────────────────

async def call_ai(
    prompt: str,
    retries: int = 1,
    timeout: float = 20.0,
) -> str:
    """
    统一 AI 调用入口（异步）

    - 按优先级依次尝试各模型
    - 每个模型最多重试 retries 次（默认1次，校对场景失败直接跳过段落）
    - timeout 默认 20s（原60s）：单段落校对无需长等待，超时直接换模型
    - 全部失败时抛出 RuntimeError（由调用方决定是跳过还是报错）
    """
    last_error: Optional[Exception] = None

    for model_name, model_fn in _MODEL_POOL:
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"[AI] 调用 {model_name}（第 {attempt} 次）")
                t0  = time.perf_counter()
                raw = await asyncio.wait_for(model_fn(prompt), timeout=timeout)
                elapsed = time.perf_counter() - t0
                logger.info(f"[AI] {model_name} 成功，耗时 {elapsed:.2f}s，返回 {len(raw)} 字符")
                return raw

            except asyncio.TimeoutError:
                logger.warning(f"[AI] {model_name} 第 {attempt} 次超时（>{timeout}s）")
                last_error = asyncio.TimeoutError(f"{model_name} 超时")

            except Exception as e:
                logger.warning(f"[AI] {model_name} 第 {attempt} 次失败: {e}")
                last_error = e

            if attempt < retries:
                await asyncio.sleep(1.0)

        logger.warning(f"[AI] {model_name} 全部 {retries} 次失败，切换下一模型")

    raise RuntimeError(f"所有 AI 模型均失败，最后一个错误: {last_error}")


# ─────────────────────────────────────────────────────────────
# 同步包装（给非 async 场景使用）
# ─────────────────────────────────────────────────────────────

def call_ai_sync(prompt: str, retries: int = 1, timeout: float = 20.0) -> str:
    """同步版 call_ai，内部用新事件循环运行 async 协程"""
    try:
        loop = asyncio.get_running_loop()
        # 如果已经在事件循环中，使用线程池
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            # 在线程池中创建新的事件循环
            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(call_ai(prompt, retries=retries, timeout=timeout))
                finally:
                    new_loop.close()
            
            future = pool.submit(run_in_new_loop)
            return future.result(timeout=timeout + 5)
    except RuntimeError:
        # 没有运行中的事件循环，创建新的
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(call_ai(prompt, retries=retries, timeout=timeout))
        finally:
            loop.close()


# ─────────────────────────────────────────────────────────────
# 便捷：JSON 解析
# ─────────────────────────────────────────────────────────────

def parse_json_response(raw: str, fallback: dict) -> dict:
    """
    安全解析 AI 返回的 JSON，去除 markdown 代码块包裹。
    解析失败时返回 fallback，不抛异常。
    """
    try:
        clean = raw.strip()
        clean = re.sub(r'^```(?:json)?\s*', '', clean)
        clean = re.sub(r'\s*```$', '', clean)
        return json.loads(clean.strip())
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"[AI] JSON 解析失败: {e}，原始内容前100字: {raw[:100]}")
        return fallback
