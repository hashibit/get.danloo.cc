"""
HTTP API tests for Backend service
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any

# Backend service base URL
BASE_URL = "http://localhost:8000"


class TestBackendAPI:
    """Backend API测试类"""

    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        self.auth_token = None
        self.test_user_id = None
        self.test_material_id = None
        self.test_pellet_id = None
        self.test_object_id = None

    async def cleanup(self):
        """清理测试客户端"""
        await self.client.aclose()

    # Health Check Tests
    async def test_health_check(self):
        """测试健康检查接口"""
        response = await self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"✅ Health check passed: {data}")

    async def test_root_endpoint(self):
        """测试根接口"""
        response = await self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✅ Root endpoint passed: {data}")

    # User Management Tests
    async def test_user_registration(self):
        """测试用户注册"""
        user_data = {
            "username": "testuser",
            "password": "testpassword123",
            "email": "test@example.com",
        }

        response = await self.client.post("/api/v1/users/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["username"] == user_data["username"]
        self.test_user_id = data["id"]
        print(f"✅ User registration passed: {data['id']}")

    async def test_user_login(self):
        """测试用户登录"""
        login_data = {"username": "testuser", "password": "testpassword123"}

        response = await self.client.post("/api/v1/users/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        self.auth_token = data["access_token"]
        print(f"✅ User login passed, token: {self.auth_token[:20]}...")

    async def test_user_profile(self):
        """测试获取用户资料"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.client.get("/api/v1/users/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        print(f"✅ User profile passed: {data['username']}")

    async def test_user_crypto_keys(self):
        """测试获取用户加密密钥"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.client.get(
            "/api/v1/users/me/crypto-keys", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_key" in data
        print(f"✅ User crypto keys passed: {data['access_key'][:10]}...")

    # Tag Management Tests
    async def test_get_tags(self):
        """测试获取标签列表"""
        response = await self.client.get("/api/v1/tags/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get tags passed: {len(data)} tags found")

    async def test_create_tag(self):
        """测试创建标签"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        tag_data = {
            "name": "测试标签",
            "color": "#ff0000",
            "description": "这是一个测试标签",
        }

        response = await self.client.post(
            "/api/v1/tags/", json=tag_data, headers=headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == tag_data["name"]
        print(f"✅ Create tag passed: {data['name']}")

    # File Management Tests
    async def test_file_upload_init(self):
        """测试文件上传初始化"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        file_data = {
            "name": "test_file.txt",
            "file_info": {"size": 1024, "type": "text/plain"},
        }

        response = await self.client.post(
            "/api/v1/files/upload/init", json=file_data, headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "object_id" in data
        assert "presigned_url" in data
        self.test_object_id = data["object_id"]
        print(f"✅ File upload init passed: {data['object_id']}")

    async def test_get_object(self):
        """测试获取对象信息"""
        if not self.test_object_id:
            print("⚠️ Skipping get object test - no object ID")
            return

        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.client.get(
            f"/api/v1/files/objects/{self.test_object_id}", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✅ Get object passed: {data['id']}")

    # Material Management Tests
    async def test_get_materials(self):
        """测试获取材料列表"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.client.get("/api/v1/materials/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✅ Get materials passed: {len(data['items'])} materials found")

    async def test_create_material(self):
        """测试创建材料"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        material_data = {
            "title": "测试材料",
            "content_type": "text/plain",
            "file_size": 1024,
        }

        response = await self.client.post(
            "/api/v1/materials/", json=material_data, headers=headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == material_data["title"]
        self.test_material_id = data["id"]
        print(f"✅ Create material passed: {data['id']}")

    async def test_get_material(self):
        """测试获取单个材料"""
        if not self.test_material_id:
            print("⚠️ Skipping get material test - no material ID")
            return

        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.client.get(
            f"/api/v1/materials/{self.test_material_id}", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.test_material_id
        print(f"✅ Get material passed: {data['title']}")

    # Pellet Management Tests
    async def test_get_pellets(self):
        """测试获取颗粒列表"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.client.get("/api/v1/pellets/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✅ Get pellets passed: {len(data['items'])} pellets found")

    async def test_create_pellet(self):
        """测试创建颗粒"""
        if not self.test_material_id:
            print("⚠️ Skipping create pellet test - no material ID")
            return

        headers = {"Authorization": f"Bearer {self.auth_token}"}
        pellet_data = {
            "title": "测试颗粒",
            "content": "这是测试颗粒内容",
            "material_ids": [self.test_material_id],
        }

        response = await self.client.post(
            "/api/v1/pellets/", json=pellet_data, headers=headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == pellet_data["title"]
        self.test_pellet_id = data["id"]
        print(f"✅ Create pellet passed: {data['id']}")

    async def test_get_pellet(self):
        """测试获取单个颗粒"""
        if not self.test_pellet_id:
            print("⚠️ Skipping get pellet test - no pellet ID")
            return

        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.client.get(
            f"/api/v1/pellets/{self.test_pellet_id}", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.test_pellet_id
        print(f"✅ Get pellet passed: {data['title']}")

    async def test_get_public_pellets(self):
        """测试获取公开颗粒列表"""
        response = await self.client.get("/api/v1/pellets/public")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(
            f"✅ Get public pellets passed: {len(data['items'])} public pellets found"
        )

    # Processing Tests
    async def test_process_materials(self):
        """测试材料处理"""
        if not self.test_material_id:
            print("⚠️ Skipping process materials test - no material ID")
            return

        headers = {"Authorization": f"Bearer {self.auth_token}"}
        process_data = {"material_ids": [self.test_material_id]}

        response = await self.client.post(
            "/api/v1/processing/materials", json=process_data, headers=headers
        )
        # Note: This might be 202 (accepted) for async processing
        assert response.status_code in [200, 201, 202]
        data = response.json()
        print(f"✅ Process materials passed: {data}")


async def run_backend_tests():
    """运行所有backend测试"""
    print("🧪 Starting Backend API Tests...")
    print("=" * 50)

    test_suite = TestBackendAPI()

    try:
        # 基础测试
        await test_suite.test_health_check()
        await test_suite.test_root_endpoint()

        # 用户管理测试
        await test_suite.test_user_registration()
        await test_suite.test_user_login()
        await test_suite.test_user_profile()
        await test_suite.test_user_crypto_keys()

        # 标签管理测试
        await test_suite.test_get_tags()
        await test_suite.test_create_tag()

        # 文件管理测试
        await test_suite.test_file_upload_init()
        await test_suite.test_get_object()

        # 材料管理测试
        await test_suite.test_get_materials()
        await test_suite.test_create_material()
        await test_suite.test_get_material()

        # 颗粒管理测试
        await test_suite.test_get_pellets()
        await test_suite.test_create_pellet()
        await test_suite.test_get_pellet()
        await test_suite.test_get_public_pellets()

        # 处理测试
        await test_suite.test_process_materials()

        print("=" * 50)
        print("✅ All Backend API tests completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
    finally:
        await test_suite.cleanup()


if __name__ == "__main__":
    asyncio.run(run_backend_tests())
