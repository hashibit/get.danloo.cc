"""
Pytest version of Backend API tests
"""

import pytest
import httpx
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


class TestBackendAPIPytest:
    """Backend API pytest测试类"""

    @pytest.fixture(scope="class")
    async def client(self):
        """HTTP客户端fixture"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client

    @pytest.fixture(scope="class")
    async def auth_token(self, client):
        """认证token fixture"""
        # 先注册用户
        user_data = {
            "username": "pytest_user",
            "password": "testpassword123",
            "email": "pytest@example.com",
        }

        register_response = await client.post("/api/v1/users/register", json=user_data)
        if register_response.status_code != 201:
            # 用户可能已存在，尝试登录
            pass

        # 登录获取token
        login_data = {"username": "pytest_user", "password": "testpassword123"}

        login_response = await client.post("/api/v1/users/login", json=login_data)
        assert login_response.status_code == 200
        data = login_response.json()
        return data["access_token"]

    @pytest.fixture
    def auth_headers(self, auth_token):
        """认证头fixture"""
        return {"Authorization": f"Bearer {auth_token}"}

    @pytest.mark.backend
    async def test_health_check(self, client):
        """测试健康检查"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.backend
    async def test_root_endpoint(self, client):
        """测试根接口"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.backend
    async def test_user_profile(self, client, auth_headers):
        """测试用户资料"""
        response = await client.get("/api/v1/users/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data

    @pytest.mark.backend
    async def test_get_tags(self, client):
        """测试获取标签"""
        response = await client.get("/api/v1/tags/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.backend
    async def test_get_materials(self, client, auth_headers):
        """测试获取材料"""
        response = await client.get("/api/v1/materials/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.backend
    async def test_get_pellets(self, client, auth_headers):
        """测试获取颗粒"""
        response = await client.get("/api/v1/pellets/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.backend
    async def test_create_material(self, client, auth_headers):
        """测试创建材料"""
        material_data = {
            "title": "Pytest测试材料",
            "content_type": "text/plain",
            "file_size": 1024,
        }

        response = await client.post(
            "/api/v1/materials/", json=material_data, headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == material_data["title"]

    @pytest.mark.backend
    async def test_invalid_auth(self, client):
        """测试无效认证"""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/api/v1/users/profile", headers=invalid_headers)
        assert response.status_code == 401
