"""
统一的HTTP API测试运行器
"""

import asyncio
import sys
import time
from typing import List, Tuple

from test_backend_api import run_backend_tests
from test_process_api import run_process_tests
from test_ai_provider_api import run_ai_provider_tests


async def check_service_availability():
    """检查所有服务的可用性"""
    import httpx

    services = [
        ("Backend", "http://localhost:8000"),
        ("Process", "http://localhost:8001"),
        ("AI Provider", "http://localhost:8002"),
    ]

    available_services = []
    unavailable_services = []

    for name, url in services:
        try:
            async with httpx.AsyncClient() as client:
                # 尝试连接服务，使用较短的超时时间
                response = await client.get(f"{url}/", timeout=5.0)
                available_services.append((name, url, response.status_code))
                print(
                    f"✅ {name} service available at {url} (Status: {response.status_code})"
                )
        except Exception as e:
            unavailable_services.append((name, url, str(e)))
            print(f"❌ {name} service unavailable at {url}: {str(e)}")

    return available_services, unavailable_services


async def run_service_tests(service_name: str, test_func):
    """运行单个服务的测试"""
    print(f"\n🔧 Running {service_name} tests...")
    start_time = time.time()

    try:
        await test_func()
        elapsed = time.time() - start_time
        print(f"✅ {service_name} tests completed in {elapsed:.2f}s")
        return True, None
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"❌ {service_name} tests failed after {elapsed:.2f}s: {str(e)}"
        print(error_msg)
        return False, error_msg


async def main():
    """主测试函数"""
    print("🚀 Starting HTTP API Tests for All Services")
    print("=" * 60)

    # 检查服务可用性
    print("📡 Checking service availability...")
    available, unavailable = await check_service_availability()

    if unavailable:
        print(f"\n⚠️  Found {len(unavailable)} unavailable services:")
        for name, url, error in unavailable:
            print(f"   - {name}: {error}")
        print("\n💡 Please ensure all services are running before running tests:")
        print("   docker-compose up -d")
        print("   or start individual services manually")

    if not available:
        print("❌ No services are available. Exiting.")
        sys.exit(1)

    print(f"\n✅ Found {len(available)} available services. Proceeding with tests...\n")

    # 定义测试套件
    test_suites = []

    # 只测试可用的服务
    for name, url, status in available:
        if "Backend" in name:
            test_suites.append(("Backend API", run_backend_tests))
        elif "Process" in name:
            test_suites.append(("Process API", run_process_tests))
        elif "AI Provider" in name:
            test_suites.append(("AI Provider API", run_ai_provider_tests))

    # 运行测试
    results = []
    total_start_time = time.time()

    for service_name, test_func in test_suites:
        success, error = await run_service_tests(service_name, test_func)
        results.append((service_name, success, error))

    total_elapsed = time.time() - total_start_time

    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)

    successful_tests = []
    failed_tests = []

    for service_name, success, error in results:
        if success:
            successful_tests.append(service_name)
            print(f"✅ {service_name}: PASSED")
        else:
            failed_tests.append((service_name, error))
            print(f"❌ {service_name}: FAILED")

    print(f"\n📈 Total: {len(results)} test suites")
    print(f"✅ Passed: {len(successful_tests)}")
    print(f"❌ Failed: {len(failed_tests)}")
    print(f"⏱️  Total time: {total_elapsed:.2f}s")

    if failed_tests:
        print(f"\n🔍 Failed test details:")
        for service_name, error in failed_tests:
            print(f"   - {service_name}: {error}")

    # 返回适当的退出码
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} test suites failed!")
        sys.exit(1)
    else:
        print(f"\n🎉 All {len(successful_tests)} test suites passed!")
        sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)
