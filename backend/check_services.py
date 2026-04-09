#!/usr/bin/env python
"""
系统诊断脚本 - 检查 Redis/Celery/FastAPI 服务状态
运行: python check_services.py
"""

import sys
import subprocess
from pathlib import Path

def check_redis():
    """检查 Redis 连接"""
    print("=" * 60)
    print("🔴 检查 Redis...")
    print("=" * 60)
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=2)
        pong = r.ping()
        if pong:
            print("✅ Redis 连接成功")
            print(f"   主机: localhost:6379")
            print(f"   信息: {r.info('server').get('redis_version', 'unknown')}")
            return True
    except ImportError:
        print("❌ redis 包未安装")
        print("   运行: pip install redis")
        return False
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        print("   " + "=" * 56)
        print("   解决方案:")
        print("   1. 检查 Redis 是否运行")
        print("   2. Windows 用户:")
        print("      - 方法1: docker run -d -p 6379:6379 redis:latest")
        print("      - 方法2: 下载 redis-server.exe 并运行")
        print("   3. Linux/Mac: redis-server &")
        print("   " + "=" * 56)
        return False

def check_celery():
    """检查 Celery 配置"""
    print("\n" + "=" * 60)
    print("🟠 检查 Celery Worker...")
    print("=" * 60)

    try:
        from app.workers.celery_app import celery_app
        from app.config import settings

        print(f"✅ Celery 应用已加载")
        print(f"   Broker:  {settings.CELERY_BROKER_URL}")
        print(f"   Backend: {settings.CELERY_RESULT_BACKEND}")
        print(f"   Queues:  evaluation, proofread, formatter, default")

        # 尝试检查 Celery Worker 是否运行
        print("\n   检查 Celery Worker 进程...")
        try:
            result = subprocess.run(
                ['tasklist' if sys.platform == 'win32' else 'ps aux'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if 'celery' in result.stdout.lower():
                print("   ✅ 检测到 Celery Worker 进程运行")
            else:
                print("   ⚠️  未检测到 Celery Worker 进程")
                print("   " + "-" * 56)
                print("   启动方法:")
                print("   cd backend")
                print("   celery -A app.workers.celery_app worker \\")
                print("     -l info --pool=threads \\")
                print("     -Q evaluation,proofread,formatter,default")
                print("   " + "-" * 56)
        except Exception:
            pass

        return True
    except Exception as e:
        print(f"❌ Celery 配置错误: {e}")
        return False

def check_fastapi():
    """检查 FastAPI 连接"""
    print("\n" + "=" * 60)
    print("🔵 检查 FastAPI...")
    print("=" * 60)
    try:
        import requests
        resp = requests.get('http://localhost:8000/docs', timeout=2)
        if resp.status_code == 200:
            print("✅ FastAPI 服务运行正常")
            print("   地址: http://localhost:8000")
            print("   API文档: http://localhost:8000/docs")
            return True
    except Exception as e:
        print(f"❌ FastAPI 连接失败: {e}")
        print("   " + "-" * 56)
        print("   启动方法:")
        print("   cd backend")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("   " + "-" * 56)
        return False

def check_api_key():
    """检查 API Key 配置"""
    print("\n" + "=" * 60)
    print("🔑 检查 API Key 配置...")
    print("=" * 60)
    try:
        from app.config import settings

        if settings.BAILIAN_API_KEY:
            print("✅ BAILIAN_API_KEY 已配置")
            print(f"   前5位: {settings.BAILIAN_API_KEY[:5]}***")
        elif settings.DEEPSEEK_API_KEY:
            print("✅ DEEPSEEK_API_KEY 已配置")
            print(f"   前5位: {settings.DEEPSEEK_API_KEY[:5]}***")
        else:
            print("❌ AI API Key 未配置")
            print("   " + "-" * 56)
            print("   解决方案:")
            print("   1. 编辑 backend/.env")
            print("   2. 设置以下之一:")
            print("      BAILIAN_API_KEY=sk_xxxxx      (阿里云百炼)")
            print("      DEEPSEEK_API_KEY=sk_xxxxx     (DeepSeek API)")
            print("   3. 重启 FastAPI")
            print("   " + "-" * 56)
            return False
        return True
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False

def diagnose():
    """运行完整诊断"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  论文评价系统 - 服务诊断".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")

    results = {
        "Redis": check_redis(),
        "Celery": check_celery(),
        "FastAPI": check_fastapi(),
        "API Key": check_api_key(),
    }

    print("\n" + "=" * 60)
    print("📋 诊断总结")
    print("=" * 60)

    for service, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {service}")

    all_ok = all(results.values())

    print("\n" + "=" * 60)
    if all_ok:
        print("✅ 所有服务运行正常！")
        print("=" * 60)
        print("\n现在可以开始使用系统：")
        print("  前端: http://localhost:5173/evaluation")
    else:
        failed = [s for s, ok in results.items() if not ok]
        print(f"❌ 以下服务需要修复: {', '.join(failed)}")
        print("=" * 60)
        print("\n请按照上述提示逐一解决问题，然后重新运行此脚本。")

    print()

if __name__ == "__main__":
    try:
        diagnose()
    except KeyboardInterrupt:
        print("\n诊断已中止")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 诊断过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
