"""
Pytest version of Process API tests
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any

BASE_URL = "http://localhost:8001"


class TestProcessAPIPytest:
    """Process API pytest测试类"""

    @pytest.fixture(scope="class")
    async def client(self):
        """HTTP客户端fixture"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
            yield client

    @pytest.mark.process
    async def test_service_availability(self, client):
        """测试服务可用性"""
        try:
            response = await client.get("/")
            # 任何响应都表示服务在运行
            assert response.status_code in [200, 404, 405]
        except httpx.ConnectError:
            pytest.skip("Process service not available")

    @pytest.mark.process
    async def test_create_processing_job(self, client):
        """测试创建处理任务"""
        job_data = {
            "job_id": "pytest_job_001",
            "materials": [
                {"material_id": "pytest_material_001", "content_type": "text/plain"}
            ],
            "priority": 1,
        }

        response = await client.post("/api/v1/processing/", json=job_data)
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    @pytest.mark.process
    async def test_get_job_status(self, client):
        """测试获取任务状态"""
        # 先创建一个任务
        job_data = {
            "job_id": "pytest_status_test",
            "materials": [
                {"material_id": "status_test_material", "content_type": "text/plain"}
            ],
        }

        create_response = await client.post("/api/v1/processing/", json=job_data)
        assert create_response.status_code == 202

        job_id = create_response.json()["job_id"]

        # 查询状态
        status_response = await client.get(f"/api/v1/processing/job/{job_id}")
        assert status_response.status_code == 200
        data = status_response.json()
        assert "status" in data

    @pytest.mark.process
    async def test_nonexistent_job(self, client):
        """测试不存在的任务"""
        response = await client.get("/api/v1/processing/job/nonexistent_job")
        assert response.status_code == 404

    @pytest.mark.process
    async def test_invalid_job_data(self, client):
        """测试无效任务数据"""
        invalid_data = {
            "job_id": "invalid_job"
            # 缺少materials
        }

        response = await client.post("/api/v1/processing/", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.process
    @pytest.mark.slow
    async def test_job_processing_workflow(self, client):
        """测试任务处理流程"""
        job_id = "pytest_workflow_job"
        job_data = {
            "job_id": job_id,
            "materials": [
                {"material_id": "workflow_material", "content_type": "text/plain"}
            ],
        }

        # 创建任务
        create_response = await client.post("/api/v1/processing/", json=job_data)
        assert create_response.status_code == 202

        # 检查初始状态
        status_response = await client.get(f"/api/v1/processing/job/{job_id}")
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["status"] in ["pending", "processing"]

        # 等待一段时间后再次检查
        await asyncio.sleep(2)
        status_response = await client.get(f"/api/v1/processing/job/{job_id}")
        assert status_response.status_code == 200
