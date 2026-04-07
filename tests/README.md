# HTTP API Testing Guide

这个目录包含了对 Danloo 所有服务的 HTTP API 测试。

## 服务架构

- **Backend** (8000): 主要的 API 服务，处理用户、材料、颗粒等业务逻辑
- **Process** (8001): 处理服务，负责材料的异步处理
- **AI Provider** (8002): AI 服务，提供内容分析和标签提取

## 快速开始

### 1. 启动所有服务

```bash
# 在项目根目录
docker-compose up -d

# 或使用验证脚本
./scripts/verify_docker_deployment.sh
```

### 2. 安装测试依赖

```bash
cd tests
uv sync
```

### 3. 运行所有测试

```bash
# 运行自定义测试套件
uv run python http_tests/run_all_tests.py

# 或使用 pytest
uv run pytest http_tests/ -v

# 运行特定服务的测试
uv run pytest http_tests/test_pytest_backend.py -v -m backend
uv run pytest http_tests/test_pytest_process.py -v -m process  
uv run pytest http_tests/test_pytest_ai_provider.py -v -m ai_provider
```

## 测试文件说明

### 自定义测试套件
- `test_backend_api.py`: Backend 服务完整测试
- `test_process_api.py`: Process 服务完整测试
- `test_ai_provider_api.py`: AI Provider 服务完整测试
- `run_all_tests.py`: 统一测试运行器

### Pytest 测试套件
- `test_pytest_backend.py`: Backend 服务 pytest 测试
- `test_pytest_process.py`: Process 服务 pytest 测试
- `test_pytest_ai_provider.py`: AI Provider 服务 pytest 测试

## 测试功能覆盖

### Backend API 测试
- ✅ 健康检查
- ✅ 用户注册/登录/资料
- ✅ 加密密钥管理
- ✅ 标签 CRUD 操作
- ✅ 文件上传管理
- ✅ 材料 CRUD 操作
- ✅ 颗粒 CRUD 操作
- ✅ 材料处理触发

### Process API 测试
- ✅ 处理任务创建
- ✅ 任务状态查询
- ✅ 优先级处理
- ✅ 并发任务处理
- ✅ 错误处理和验证
- ✅ 工作流程测试

### AI Provider API 测试
- ✅ 文本内容分析
- ✅ 多语言支持 (中文/英文)
- ✅ 多模态内容 (图片/视频 URL)
- ✅ Base64 编码内容
- ✅ 大内容处理
- ✅ 特殊字符处理
- ✅ 并发请求处理
- ✅ 错误处理和验证

## 测试标记

使用 pytest 标记来分组测试：

```bash
# 只运行 backend 测试
uv run pytest -m backend

# 只运行快速测试（排除慢测试）
uv run pytest -m "not slow"

# 运行集成测试
uv run pytest -m integration

# 组合标记
uv run pytest -m "backend and not slow"
```

## 环境要求

- Python 3.11+
- uv 包管理器
- Docker & Docker Compose
- 所有服务正常运行

## 故障排除

### 服务连接失败
```bash
# 检查服务状态
docker-compose ps

# 查看服务日志
docker-compose logs backend
docker-compose logs process
docker-compose logs ai-provider
```

### 认证失败
```bash
# 重新创建用户
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123","email":"test@example.com"}'
```

### 数据库连接问题
```bash
# 重启数据库
docker-compose restart db

# 检查数据库健康
docker-compose exec db mysql -u danloo -ppassword -e "SELECT 1;"
```

## 生成测试报告

```bash
# 生成 HTML 报告
uv run pytest --html=reports/test_report.html --self-contained-html

# 生成覆盖率报告
uv run pytest --cov=http_tests --cov-report=html
```

## 自定义配置

编辑 `pyproject.toml` 来修改测试配置：

```toml
[tool.pytest.ini_options]
# 添加自定义标记
markers = [
    "custom: custom test marker",
]
# 修改测试发现规则
python_files = "test_*.py"
```

## API 文档

各服务的 API 文档：
- Backend: http://localhost:8000/docs
- Process: http://localhost:8001/docs  
- AI Provider: http://localhost:8002/docs