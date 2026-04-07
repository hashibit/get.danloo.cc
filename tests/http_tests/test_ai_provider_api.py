"""
HTTP API tests for AI Provider service
"""

import pytest
import httpx
import asyncio
import base64
from typing import Dict, Any

# AI Provider service base URL
BASE_URL = "http://localhost:8002"


class TestAIProviderAPI:
    """AI Provider API测试类"""

    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=60.0)

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

            # AI Provider可能没有标准的health接口，所以任何响应都表示服务在运行
            assert response.status_code in [200, 404, 405]
            print(f"✅ AI Provider service health check: Status {response.status_code}")
        except httpx.ConnectError:
            print("⚠️ AI Provider service not available - please ensure it's running")
            raise

    # Content Extraction Tests
    async def test_extract_text_content(self):
        """测试文本内容提取"""
        request_data = {
            "content_id": "test_text_001",
            "text_content": "这是一个测试文本，用于AI内容分析和标签提取。内容包含技术、教育等主题。",
            "extras": {
                "title": "测试文档",
                "content_type": "text/plain",
                "material_id": "test_material_001",
            },
        }

        response = await self.client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # 检查返回的分类结果结构
        assert "categories" in data
        assert "tags" in data
        assert "language" in data
        assert isinstance(data["categories"], list)
        assert isinstance(data["tags"], list)

        print(f"✅ Text content extraction passed:")
        print(f"   Language: {data['language']}")
        print(f"   Categories: {len(data['categories'])}")
        print(f"   Tags: {len(data['tags'])}")

    async def test_extract_empty_content(self):
        """测试空内容提取"""
        request_data = {
            "content_id": "test_empty_001",
            "text_content": "",
            "extras": {},
        }

        response = await self.client.post("/api/extract-content", json=request_data)
        # 可能返回200（处理空内容）或400（拒绝空内容）
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            assert "categories" in data
            assert "tags" in data
            print("✅ Empty content extraction handled gracefully")
        else:
            print(f"✅ Empty content validation passed: Status {response.status_code}")

    async def test_extract_chinese_content(self):
        """测试中文内容提取"""
        request_data = {
            "content_id": "test_chinese_001",
            "text_content": "这是一篇关于人工智能和机器学习的中文技术文档。内容涵盖深度学习、自然语言处理等前沿技术。",
            "extras": {"title": "AI技术文档", "language": "zh"},
        }

        response = await self.client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert "language" in data
        assert "tags" in data
        assert "categories" in data

        print(f"✅ Chinese content extraction passed:")
        print(f"   Detected language: {data['language']}")
        print(f"   Tags count: {len(data['tags'])}")

    async def test_extract_english_content(self):
        """测试英文内容提取"""
        request_data = {
            "content_id": "test_english_001",
            "text_content": "This is a technical document about artificial intelligence and machine learning. It covers topics like deep learning, natural language processing, and computer vision.",
            "extras": {"title": "AI Technical Document", "language": "en"},
        }

        response = await self.client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        print(f"✅ English content extraction passed:")
        print(f"   Detected language: {data['language']}")
        print(f"   Tags count: {len(data['tags'])}")

    async def test_extract_mixed_content(self):
        """测试混合语言内容提取"""
        request_data = {
            "content_id": "test_mixed_001",
            "text_content": "这是一个中英混合的文档。This document contains both Chinese and English content. 内容涵盖technology和科技topics.",
            "extras": {"title": "Mixed Language Document"},
        }

        response = await self.client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        print(f"✅ Mixed language content extraction passed:")
        print(f"   Detected language: {data['language']}")
        print(f"   Categories: {len(data['categories'])}")

    async def test_extract_with_image_urls(self):
        """测试带图片URL的内容提取"""
        request_data = {
            "content_id": "test_image_001",
            "text_content": "这是一个包含图片的文档",
            "http_image_urls": [
                "https://via.placeholder.com/300x200",
                "https://via.placeholder.com/400x300",
            ],
            "extras": {"title": "带图片的文档", "content_type": "multimodal"},
        }

        response = await self.client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        print(f"✅ Content with image URLs extraction passed:")
        print(f"   Categories: {len(data['categories'])}")
        print(f"   Tags: {len(data['tags'])}")

    async def test_extract_with_video_url(self):
        """测试带视频URL的内容提取"""
        request_data = {
            "content_id": "test_video_001",
            "text_content": "这是一个包含视频的文档",
            "http_video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
            "extras": {"title": "带视频的文档", "content_type": "multimodal"},
        }

        response = await self.client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        print(f"✅ Content with video URL extraction passed:")
        print(f"   Categories: {len(data['categories'])}")
        print(f"   Tags: {len(data['tags'])}")

    async def test_extract_with_base64_content(self):
        """测试base64编码内容提取"""
        # 创建一个简单的文本内容并编码为base64
        text_content = "这是base64编码的测试内容"
        encoded_content = base64.b64encode(text_content.encode("utf-8")).decode("ascii")

        request_data = {
            "content_id": "test_base64_001",
            "object_content_base64": encoded_content,
            "object_content_type": "text/plain",
            "extras": {"title": "Base64编码内容", "encoding": "base64"},
        }

        response = await self.client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        print(f"✅ Base64 content extraction passed:")
        print(f"   Language: {data['language']}")
        print(f"   Tags: {len(data['tags'])}")

    async def test_invalid_request_missing_content_id(self):
        """测试缺少content_id的请求"""
        request_data = {
            # 缺少content_id
            "text_content": "测试内容"
        }

        response = await self.client.post("/api/extract-content", json=request_data)
        assert response.status_code == 422  # Validation error
        print("✅ Missing content_id validation passed")

    async def test_invalid_request_no_content(self):
        """测试没有任何内容的请求"""
        request_data = {
            "content_id": "test_no_content_001"
            # 没有任何内容字段
        }

        response = await self.client.post("/api/extract-content", json=request_data)
        # 可能返回422（验证错误）或400（业务逻辑错误）
        assert response.status_code in [400, 422]
        print(f"✅ No content validation passed: Status {response.status_code}")

    async def test_malformed_json(self):
        """测试格式错误的JSON"""
        malformed_json = '{"content_id": "test", "text_content": '  # 不完整的JSON

        response = await self.client.post(
            "/api/extract-content",
            content=malformed_json,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422  # JSON解析错误
        print("✅ Malformed JSON validation passed")

    async def test_large_content(self):
        """测试大内容处理"""
        # 生成一个较大的文本内容
        large_text = "这是一个很长的测试文档。" * 1000  # 约12KB的内容

        request_data = {
            "content_id": "test_large_001",
            "text_content": large_text,
            "extras": {"title": "大文档测试", "size": len(large_text)},
        }

        response = await self.client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        print(f"✅ Large content extraction passed:")
        print(f"   Content size: {len(large_text)} chars")
        print(f"   Tags extracted: {len(data['tags'])}")

    async def test_special_characters_content(self):
        """测试特殊字符内容处理"""
        special_content = """
        这是包含特殊字符的测试：
        🤖 人工智能 AI
        💻 编程 Programming  
        📊 数据分析 Data Analysis
        🔬 科学研究 Scientific Research
        ⚡ 快速处理 Fast Processing
        """

        request_data = {
            "content_id": "test_special_001",
            "text_content": special_content,
            "extras": {"title": "特殊字符测试文档"},
        }

        response = await self.client.post("/api/extract-content", json=request_data)
        assert response.status_code == 200
        data = response.json()

        print(f"✅ Special characters content extraction passed:")
        print(f"   Tags: {len(data['tags'])}")

    async def test_concurrent_requests(self):
        """测试并发请求处理"""
        requests = []
        for i in range(5):
            request_data = {
                "content_id": f"concurrent_test_{i}",
                "text_content": f"这是并发测试内容 {i}，包含技术和教育主题。",
                "extras": {"title": f"并发测试文档 {i}", "request_id": i},
            }
            requests.append(request_data)

        # 并发发送请求
        tasks = [
            self.client.post("/api/extract-content", json=req_data)
            for req_data in requests
        ]

        responses = await asyncio.gather(*tasks)

        for i, response in enumerate(responses):
            assert response.status_code == 200
            data = response.json()
            print(f"✅ Concurrent request {i} passed: {len(data['tags'])} tags")

        print("✅ Concurrent requests test passed")


async def run_ai_provider_tests():
    """运行所有AI Provider测试"""
    print("🧪 Starting AI Provider API Tests...")
    print("=" * 50)

    test_suite = TestAIProviderAPI()

    try:
        # 基础测试
        await test_suite.test_health_check()

        # 内容提取测试
        await test_suite.test_extract_text_content()
        await test_suite.test_extract_empty_content()
        await test_suite.test_extract_chinese_content()
        await test_suite.test_extract_english_content()
        await test_suite.test_extract_mixed_content()

        # 多模态内容测试
        await test_suite.test_extract_with_image_urls()
        await test_suite.test_extract_with_video_url()
        await test_suite.test_extract_with_base64_content()

        # 错误处理测试
        await test_suite.test_invalid_request_missing_content_id()
        await test_suite.test_invalid_request_no_content()
        await test_suite.test_malformed_json()

        # 边界测试
        await test_suite.test_large_content()
        await test_suite.test_special_characters_content()

        # 性能测试
        await test_suite.test_concurrent_requests()

        print("=" * 50)
        print("✅ All AI Provider API tests completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
    finally:
        await test_suite.cleanup()


if __name__ == "__main__":
    asyncio.run(run_ai_provider_tests())
