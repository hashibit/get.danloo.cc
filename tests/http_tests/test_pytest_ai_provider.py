"""
Pytest version of AI Provider API tests
"""

import pytest
import httpx
import asyncio
import base64
from typing import Dict, Any

BASE_URL = "http://localhost:8002"


class TestAIProviderAPIPytest:
    """AI Provider API pytest测试类"""

    @pytest.fixture(scope="class")
    async def client(self):
        """HTTP客户端fixture"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
            yield client

    @pytest.mark.ai_provider
    async def test_service_availability(self, client):
        """测试服务可用性"""
        try:
            response = await client.get("/")
            # 任何响应都表示服务在运行
            assert response.status_code in [200, 404, 405]
        except httpx.ConnectError:
            pytest.skip("AI Provider service not available")

    @pytest.mark.ai_provider
    async def test_extract_text_content(self, client):
        """测试文本内容提取"""
        request_data = {
            "content_id": "pytest_text_001",
            "text_content": "这是一个测试文本，用于AI内容分析和标签提取。内容包含技术、教育等主题。",
            "extras": {"title": "Pytest测试文档", "content_type": "text/plain"},
        }

        response = await client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert "categories" in data
        assert "tags" in data
        assert "language" in data
        assert isinstance(data["categories"], list)
        assert isinstance(data["tags"], list)

    @pytest.mark.ai_provider
    async def test_extract_chinese_content(self, client):
        """测试中文内容提取"""
        request_data = {
            "content_id": "pytest_chinese_001",
            "text_content": "这是一篇关于人工智能和机器学习的中文技术文档。",
            "extras": {"title": "AI技术文档", "language": "zh"},
        }

        response = await client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert "language" in data
        assert "tags" in data
        assert "categories" in data

    @pytest.mark.ai_provider
    async def test_extract_english_content(self, client):
        """测试英文内容提取"""
        request_data = {
            "content_id": "pytest_english_001",
            "text_content": "This is a technical document about artificial intelligence and machine learning.",
            "extras": {"title": "AI Technical Document", "language": "en"},
        }

        response = await client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert "language" in data
        assert "tags" in data

    @pytest.mark.ai_provider
    async def test_extract_with_image_urls(self, client):
        """测试带图片URL的内容提取"""
        request_data = {
            "content_id": "pytest_image_001",
            "text_content": "这是一个包含图片的文档",
            "http_image_urls": ["https://via.placeholder.com/300x200"],
            "extras": {"title": "带图片的文档"},
        }

        response = await client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert "categories" in data
        assert "tags" in data

    @pytest.mark.ai_provider
    async def test_extract_with_base64_content(self, client):
        """测试base64编码内容提取"""
        text_content = "这是base64编码的测试内容"
        encoded_content = base64.b64encode(text_content.encode("utf-8")).decode("ascii")

        request_data = {
            "content_id": "pytest_base64_001",
            "object_content_base64": encoded_content,
            "object_content_type": "text/plain",
            "extras": {"title": "Base64编码内容"},
        }

        response = await client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert "language" in data
        assert "tags" in data

    @pytest.mark.ai_provider
    async def test_invalid_request_missing_content_id(self, client):
        """测试缺少content_id的请求"""
        request_data = {"text_content": "测试内容"}

        response = await client.post("/api/extract-content", json=request_data)
        assert response.status_code == 422

    @pytest.mark.ai_provider
    async def test_empty_content(self, client):
        """测试空内容"""
        request_data = {
            "content_id": "pytest_empty_001",
            "text_content": "",
            "extras": {},
        }

        response = await client.post("/api/extract-content", json=request_data)
        assert response.status_code in [200, 400, 422]

    @pytest.mark.ai_provider
    async def test_malformed_json(self, client):
        """测试格式错误的JSON"""
        malformed_json = '{"content_id": "test", "text_content": '

        response = await client.post(
            "/api/extract-content",
            content=malformed_json,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.ai_provider
    @pytest.mark.slow
    async def test_large_content(self, client):
        """测试大内容处理"""
        large_text = "这是一个很长的测试文档。" * 500  # 约6KB

        request_data = {
            "content_id": "pytest_large_001",
            "text_content": large_text,
            "extras": {"title": "大文档测试", "size": len(large_text)},
        }

        response = await client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert "tags" in data
