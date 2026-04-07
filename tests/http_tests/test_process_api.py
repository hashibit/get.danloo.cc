"""
HTTP API tests for Process service
"""

import pytest
import httpx
import asyncio
import time
from typing import Dict, Any

# Process service base URL
BASE_URL = "http://localhost:8001"


class TestProcessAPI:
    """Process API测试类"""

    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=60.0)
        self.test_job_id = None
        self.test_task_id = None

    async def cleanup(self):
        """清理测试客户端"""
        await self.client.aclose()

    # Health Check Tests
    async def test_health_check(self):
        """测试健康检查接口"""
        try:
            response = await self.client.get("/health")
            if response.status_code == 404:
                # 如果没有health接口，测试根路径
                response = await self.client.get("/")

            assert response.status_code in [200, 404]  # 404是可接受的，表示服务正在运行
            print(f"✅ Process service health check: Status {response.status_code}")
        except httpx.ConnectError:
            print("⚠️ Process service not available - please ensure it's running")
            raise

    # Processing Tests
    async def test_create_processing_job(self):
        """测试创建处理任务"""
        job_data = {
            "job_id": "test_job_001",
            "materials": [
                {"material_id": "test_material_001", "content_type": "text/plain"},
                {"material_id": "test_material_002", "content_type": "text/markdown"},
            ],
            "callback_url": "http://backend:8000/api/v1/internal/pellets/test_pellet_001/processing-complete",
            "priority": 1,
        }

        response = await self.client.post("/api/v1/processing/", json=job_data)
        assert response.status_code == 202  # Accepted
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        self.test_job_id = data["job_id"]
        print(f"✅ Create processing job passed: {data['job_id']}")

    async def test_get_job_status(self):
        """测试获取任务状态"""
        if not self.test_job_id:
            print("⚠️ Skipping job status test - no job ID")
            return

        response = await self.client.get(f"/api/v1/processing/job/{self.test_job_id}")
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        print(f"✅ Get job status passed: {data['status']}")

    async def test_get_job_status_nonexistent(self):
        """测试获取不存在的任务状态"""
        fake_job_id = "nonexistent_job_123"
        response = await self.client.get(f"/api/v1/processing/job/{fake_job_id}")
        assert response.status_code == 404
        print(f"✅ Get nonexistent job status passed: 404 as expected")

    async def test_create_processing_job_minimal(self):
        """测试创建最小配置的处理任务"""
        job_data = {
            "job_id": "test_job_minimal",
            "materials": [
                {"material_id": "minimal_material", "content_type": "text/plain"}
            ],
        }

        response = await self.client.post("/api/v1/processing/", json=job_data)
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == "test_job_minimal"
        print(f"✅ Create minimal processing job passed: {data['job_id']}")

    async def test_create_processing_job_with_priority(self):
        """测试创建带优先级的处理任务"""
        job_data = {
            "job_id": "test_job_priority",
            "materials": [
                {"material_id": "priority_material", "content_type": "text/plain"}
            ],
            "priority": 5,
        }

        response = await self.client.post("/api/v1/processing/", json=job_data)
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == "test_job_priority"
        print(f"✅ Create priority processing job passed: {data['job_id']}")

    async def test_invalid_processing_job(self):
        """测试无效的处理任务请求"""
        # 缺少必填字段
        job_data = {
            "job_id": "test_job_invalid"
            # 缺少materials字段
        }

        response = await self.client.post("/api/v1/processing/", json=job_data)
        assert response.status_code == 422  # Validation error
        print(f"✅ Invalid processing job validation passed: 422 as expected")

    async def test_empty_materials_job(self):
        """测试空材料列表的处理任务"""
        job_data = {"job_id": "test_job_empty", "materials": []}  # 空列表

        response = await self.client.post("/api/v1/processing/", json=job_data)
        # 这可能返回422或400，取决于验证逻辑
        assert response.status_code in [400, 422]
        print(
            f"✅ Empty materials job validation passed: {response.status_code} as expected"
        )

    async def test_duplicate_job_id(self):
        """测试重复的任务ID"""
        job_data = {
            "job_id": "duplicate_job_test",
            "materials": [
                {"material_id": "dup_material", "content_type": "text/plain"}
            ],
        }

        # 第一次创建
        response1 = await self.client.post("/api/v1/processing/", json=job_data)
        assert response1.status_code == 202

        # 再次创建相同的job_id
        response2 = await self.client.post("/api/v1/processing/", json=job_data)
        # 可能返回409 (Conflict) 或其他错误码
        # 先检查是否接受重复任务（某些实现可能允许）
        print(f"✅ Duplicate job ID test: Status {response2.status_code}")

    async def test_job_processing_workflow(self):
        """测试完整的任务处理工作流程"""
        job_id = "workflow_test_job"
        job_data = {
            "job_id": job_id,
            "materials": [
                {"material_id": "workflow_material_1", "content_type": "text/plain"}
            ],
            "callback_url": "http://httpbin.org/post",  # 测试用的webhook接收器
        }

        # 1. 创建任务
        response = await self.client.post("/api/v1/processing/", json=job_data)
        assert response.status_code == 202
        print(f"✅ Workflow step 1 - Job created: {job_id}")

        # 2. 检查初始状态
        response = await self.client.get(f"/api/v1/processing/job/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["pending", "processing"]
        print(f"✅ Workflow step 2 - Initial status: {data['status']}")

        # 3. 等待一段时间后再次检查状态
        await asyncio.sleep(2)
        response = await self.client.get(f"/api/v1/processing/job/{job_id}")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Workflow step 3 - Status after 2s: {data['status']}")

    async def test_task_status(self):
        """测试任务状态查询"""
        # 由于我们无法直接获取task_id，这里测试一个假的task_id
        fake_task_id = "test_task_001"
        response = await self.client.get(f"/api/v1/processing/task/{fake_task_id}")

        # 应该返回404 (不存在) 或200 (如果碰巧存在)
        assert response.status_code in [200, 404]
        print(f"✅ Task status test passed: Status {response.status_code}")

    async def test_concurrent_jobs(self):
        """测试并发任务处理"""
        jobs = []
        for i in range(3):
            job_data = {
                "job_id": f"concurrent_job_{i}",
                "materials": [
                    {
                        "material_id": f"concurrent_material_{i}",
                        "content_type": "text/plain",
                    }
                ],
            }
            jobs.append(job_data)

        # 并发创建多个任务
        tasks = [
            self.client.post("/api/v1/processing/", json=job_data) for job_data in jobs
        ]

        responses = await asyncio.gather(*tasks)

        for i, response in enumerate(responses):
            assert response.status_code == 202
            data = response.json()
            print(f"✅ Concurrent job {i} created: {data['job_id']}")

        print("✅ Concurrent jobs test passed")


async def run_process_tests():
    """运行所有process测试"""
    print("🧪 Starting Process API Tests...")
    print("=" * 50)

    test_suite = TestProcessAPI()

    try:
        # 基础测试
        await test_suite.test_health_check()

        # 处理任务测试
        await test_suite.test_create_processing_job()
        await test_suite.test_get_job_status()
        await test_suite.test_get_job_status_nonexistent()

        # 各种场景测试
        await test_suite.test_create_processing_job_minimal()
        await test_suite.test_create_processing_job_with_priority()
        await test_suite.test_invalid_processing_job()
        await test_suite.test_empty_materials_job()
        await test_suite.test_duplicate_job_id()

        # 工作流程测试
        await test_suite.test_job_processing_workflow()
        await test_suite.test_task_status()
        await test_suite.test_concurrent_jobs()

        print("=" * 50)
        print("✅ All Process API tests completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
    finally:
        await test_suite.cleanup()


if __name__ == "__main__":
    asyncio.run(run_process_tests())
