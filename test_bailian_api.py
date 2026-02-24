"""
测试百炼API调用
用于诊断API Key和调用格式
"""

import requests
import json

API_KEY = "sk-1a01c6b2d67b4262bcf5220c9a8c568b"

def test_dashscope_v1():
    """测试DashScope V1 API"""
    print("=" * 60)
    print("测试 1: DashScope V1 Generation API")
    print("=" * 60)

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen-turbo",
        "input": {
            "prompt": "你好"
        },
        "parameters": {
            "result_format": "message"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def test_dashscope_compatible():
    """测试DashScope兼容模式API"""
    print("\n" + "=" * 60)
    print("测试 2: DashScope Compatible Mode (OpenAI-like)")
    print("=" * 60)

    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen-turbo",
        "messages": [
            {"role": "user", "content": "你好"}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def test_bailian_app():
    """测试百炼应用API"""
    print("\n" + "=" * 60)
    print("测试 3: 百炼应用 API")
    print("=" * 60)

    url = "https://dashscope.aliyuncs.com/api/v1/apps/completion"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 注意：这需要应用ID
    payload = {
        "input": {
            "prompt": "你好"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def test_key_validity():
    """测试API Key有效性"""
    print("\n" + "=" * 60)
    print("测试 4: API Key 有效性检查")
    print("=" * 60)

    # 使用一个简单的API来验证Key
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-SSE": "disable"
    }

    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "hi"}
            ]
        },
        "parameters": {
            "result_format": "message"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


if __name__ == "__main__":
    print("\n🔍 开始诊断百炼API调用...")
    print(f"API Key: {API_KEY[:20]}...")

    results = []

    # 运行所有测试
    results.append(("DashScope V1", test_dashscope_v1()))
    results.append(("兼容模式", test_dashscope_compatible()))
    results.append(("Key有效性", test_key_validity()))
    results.append(("百炼应用", test_bailian_app()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{name:15s}: {status}")

    if any(r[1] for r in results):
        print("\n✅ 至少有一个API调用成功!")
        print("建议：根据成功的API格式修改 bailian_client.py")
    else:
        print("\n❌ 所有测试都失败了")
        print("可能的原因：")
        print("  1. API Key无效或已过期")
        print("  2. 需要在控制台开通相应服务")
        print("  3. API格式需要调整")
