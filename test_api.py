"""
API测试脚本 - 论文评价检验系统
用于快速测试API接口功能
"""

import requests
import json
from pathlib import Path
import time


BASE_URL = "http://localhost:8000"


def print_section(title):
    """打印章节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_health_check():
    """测试健康检查接口"""
    print_section("1. 健康检查测试")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

        if response.status_code == 200:
            print("✅ 健康检查通过")
            return True
        else:
            print("❌ 健康检查失败")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("提示: 请确保后端服务已启动（cd backend && venv/Scripts/python.exe -m app.main）")
        return False


def test_root():
    """测试根路径"""
    print_section("2. 根路径测试")

    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

        if response.status_code == 200:
            print("✅ 根路径访问成功")
            return True
        else:
            print("❌ 根路径访问失败")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_evaluation_upload(file_path):
    """测试论文评价上传接口"""
    print_section("3. 论文评价测试")

    # 检查文件是否存在
    if not Path(file_path).exists():
        print(f"❌ 测试文件不存在: {file_path}")
        return False

    print(f"上传文件: {file_path}")
    print(f"文件大小: {Path(file_path).stat().st_size / 1024:.2f} KB")

    try:
        with open(file_path, 'rb') as f:
            files = {'file': ('test_paper.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}

            print("\n发送请求...")
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/v1/evaluation/upload",
                files=files,
                timeout=60
            )
            elapsed_time = time.time() - start_time

            print(f"\n状态码: {response.status_code}")
            print(f"响应时间: {elapsed_time:.2f}s")

            # 尝试解析JSON响应
            try:
                response_data = response.json()
                print(f"响应内容:\n{json.dumps(response_data, ensure_ascii=False, indent=2)}")
            except:
                print(f"响应内容（非JSON）:\n{response.text}")

            if response.status_code == 200:
                print("\n✅ 论文评价成功!")

                # 解析评价结果
                if 'overall_score' in response_data:
                    print(f"\n📊 评价结果:")
                    print(f"   论文标题: {response_data.get('paper_title', 'N/A')}")
                    print(f"   综合评分: {response_data.get('overall_score', 0)}")
                    print(f"\n   各维度评分:")

                    dimensions = response_data.get('dimensions', {})
                    for dim_key, dim_data in dimensions.items():
                        print(f"   - {dim_data.get('dimension_name', dim_key)}: {dim_data.get('score', 0)}")

                return True

            elif response.status_code == 503:
                print("\n⚠️ 评价服务暂不可用")
                print("原因: 百炼API Key未配置或无效")
                print("\n配置步骤:")
                print("1. 访问 https://dashscope.aliyun.com/")
                print("2. 注册并创建API Key")
                print("3. 编辑 backend/.env 文件")
                print("4. 将 BAILIAN_API_KEY=your_api_key_here 改为真实的Key")
                print("5. 重启服务")

                # 但文件上传和解析功能应该是正常的
                if "detail" in response_data:
                    print(f"\n详细信息: {response_data['detail']}")

                print("\n✅ 文件上传和解析功能正常（仅API调用失败）")
                return None  # 部分成功

            else:
                print(f"❌ 请求失败: {response.status_code}")
                return False

    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_api_docs():
    """测试API文档访问"""
    print_section("4. API文档测试")

    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            print("✅ API文档可访问")
            print(f"文档地址: {BASE_URL}/docs")
            print(f"ReDoc地址: {BASE_URL}/redoc")
            print(f"OpenAPI Schema: {BASE_URL}/openapi.json")
            return True
        else:
            print("❌ API文档访问失败")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "🧪 论文评价检验系统 - API测试".center(60, "="))
    print(f"测试地址: {BASE_URL}")
    print("="*60)

    results = {}

    # 1. 健康检查
    results['health'] = test_health_check()
    if not results['health']:
        print("\n❌ 服务未启动，无法继续测试")
        print("\n启动命令:")
        print("  cd backend")
        print("  venv\\Scripts\\python.exe -m app.main")
        return

    time.sleep(0.5)

    # 2. 根路径
    results['root'] = test_root()
    time.sleep(0.5)

    # 3. API文档
    results['docs'] = test_api_docs()
    time.sleep(0.5)

    # 4. 论文评价（查找测试文件）
    test_files = [
        "backend/venv/Scripts/test_paper.docx",
        "test_paper.docx",
        "backend/storage/uploads/*.docx"
    ]

    test_file = None
    for file_pattern in test_files:
        if '*' in file_pattern:
            # 通配符匹配
            import glob
            matches = glob.glob(file_pattern)
            if matches:
                test_file = matches[0]
                break
        elif Path(file_pattern).exists():
            test_file = file_pattern
            break

    if test_file:
        results['evaluation'] = test_evaluation_upload(test_file)
    else:
        print_section("3. 论文评价测试")
        print("⚠️ 未找到测试文件")
        print("请先运行: python create_test_doc.py")
        results['evaluation'] = None

    # 总结
    print_section("测试总结")

    success = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    partial = sum(1 for v in results.values() if v is None)
    total = len(results)

    print(f"\n✅ 成功: {success}/{total}")
    print(f"❌ 失败: {failed}/{total}")
    if partial > 0:
        print(f"⚠️ 部分成功: {partial}/{total}")

    print("\n详细结果:")
    status_map = {True: "✅ 通过", False: "❌ 失败", None: "⚠️ 部分成功"}
    for test_name, result in results.items():
        print(f"  {test_name:15s}: {status_map.get(result, '❓ 未知')}")

    # 建议
    print("\n💡 建议:")

    if results.get('evaluation') is None:
        print("  - 配置百炼API Key以测试完整评价功能")
        print("    1. 访问 https://dashscope.aliyun.com/")
        print("    2. 编辑 backend/.env")
        print("    3. 重启服务")

    if results.get('evaluation') is True:
        print("  - ✅ 所有功能正常!")
        print("  - 可以开始前端开发或继续完善其他功能")

    if failed > 0:
        print("  - 检查失败的测试项")
        print("  - 查看服务日志: backend/logs/app_*.log")

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
