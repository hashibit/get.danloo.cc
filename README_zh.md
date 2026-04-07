# 丹炉 (Danloo) - AI 内容提炼平台

丹炉是一个 AI 驱动的内容提炼平台，将原始技术材料转化为结构化的知识胶囊。用户作为"炼丹师"，上传对话记录、PDF 文档或文本笔记，通过 AI 智能提取和分类，生成精炼的知识内容。

## 功能特性

- 智能提炼 - AI 自动分析内容，提取知识点，生成摘要
- 智能分类 - 自动识别高质量内容（金丹），支持自定义标签
- 多格式支持 - 支持文本、PDF、图片、视频等多种格式
- 安全认证 - JWT 用户认证 + AK/SK 服务认证
- 多语言 - 支持中文和英文界面

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14 + TypeScript + Tailwind CSS |
| 后端 | FastAPI + Python 3.11+ |
| 数据库 | MySQL 8.0 |
| 存储 | MinIO (S3 兼容) |
| AI | Claude / OpenAI / AWS Bedrock |
| 部署 | Docker Compose |

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (反向代理)                       │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    Frontend     │  │     Backend     │  │   AI Provider   │
│   (Next.js)     │  │   (FastAPI)     │  │   (FastAPI)     │
│   Port: 3000    │  │   Port: 8000    │  │   Port: 8002    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│      MySQL      │  │     MinIO       │  │    AI Proxy     │
│   Port: 3306    │  │   Port: 9000    │  │   Port: 8091    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 设计亮点

### 安全与认证

**双认证体系**
- JWT 认证 - 标准用户认证，支持 access/refresh token 刷新机制
- AK/SK 认证 - 访问密钥/秘密密钥对，用于服务间认证，支持 HMAC 签名验证

**加密模块**
- 使用 `secrets` 模块安全生成密钥对
- bcrypt + salt 密码哈希
- HMAC 内容完整性校验
- Bearer Token 创建与验证

### 限流与保护

**多级限流**
- API 限流（每 IP 100 请求/秒）
- 邮件限流（每地址 2 封/5 分钟）
- 短信限流（每号码 1 条/2 分钟）

**熔断器模式**
- 自动故障检测，可配置阈值
- 三态切换：CLOSED -> OPEN -> HALF_OPEN
- 优雅降级与自动恢复

### 配额管理

**用户配额系统**
- 每日配额分配与追踪
- 午夜自动重置
- 使用日志与分析
- 配额升级支持

**Token 配额集成**
- 按 AI 模型追踪 token 消耗
- 实时配额扣减
- 跨服务 token 统计

### 异步任务处理

**基于数据库的任务队列**
- MySQL 持久化任务存储
- 优先级调度
- ThreadPoolExecutor 并行执行
- 指数退避自动重试

**任务分解**
- Job 拆分为细粒度 Task
- 独立执行，互不阻塞
- 进度追踪与状态更新

### 通知系统

**多渠道通知**
- 邮件通知（SMTP TLS/SSL）
- 微信集成支持
- 限流保护防止滥用
- 模板化消息生成

### 统一数据模型

**共享数据库模型** (`common/database_models/`)
- `UserDB` - 用户账户与配额追踪
- `MaterialDB` - 上传材料元数据
- `PelletDB` - 生成的知识胶囊
- `JobDB` / `TaskDB` - 异步处理状态
- `TokenUsageDB` - AI token 消耗日志
- `UserQuotaDB` - 每日配额追踪

**优势**
- 跨服务单一数据源
- 类型安全的模型定义
- Alembic 迁移管理 schema 演进

## 快速开始

### 环境要求

- Docker & Docker Compose
- Python 3.11+ (本地开发)
- Node.js 18+ (本地开发)
- uv (Python 包管理器)

### Docker 部署（推荐）

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑 .env 文件，填入必要的配置
#    - DATABASE_URL: 数据库连接
#    - JWT_SECRET: JWT 密钥
#    - AI API Keys: OPENAI_TOKEN / ANTHROPIC_API_KEY

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps
```

服务启动后：
- 前端: http://localhost:3000
- API 文档: http://localhost:8000/docs
- MinIO 控制台: http://localhost:9001

### 本地开发

#### 后端

```bash
cd backend
uv venv && source .venv/bin/activate
uv sync

# 配置环境变量
export DATABASE_URL=mysql+pymysql://danloo:password@localhost:33060/danloo
export JWT_SECRET=your-secret-key

# 运行数据库迁移
uv run alembic upgrade head

# 启动服务
uv run uvicorn main:app --reload --port 8000
```

#### AI Provider

```bash
cd ai-provider/ai-provider
uv venv && source .venv/bin/activate
uv sync

# 配置 AI API Keys
export OPENAI_TOKEN=your-token
export ANTHROPIC_API_KEY=your-key

# 启动服务
uv run python main.py
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

## 环境变量

### 核心配置

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | MySQL 连接字符串 | `mysql+pymysql://user:pass@host:3306/db` |
| `JWT_SECRET` | JWT 签名密钥 | `openssl rand -hex 32` 生成 |
| `S3_ENDPOINT` | MinIO/OSS 端点 | `http://localhost:9000` |
| `S3_ACCESS_KEY` | S3 访问密钥 | `minioadmin` |
| `S3_SECRET_KEY` | S3 密钥 | `minioadmin` |

### AI 配置

| 变量 | 说明 |
|------|------|
| `OPENAI_TOKEN` | OpenAI 兼容 API Token |
| `ANTHROPIC_API_KEY` | Anthropic API Key |
| `ANTHROPIC_BASE_URL` | Claude API 中转地址（可选） |

## 项目结构

```
danloo/
├── frontend/           # Next.js 前端应用
├── backend/            # FastAPI 后端服务
│   ├── services/      # 业务逻辑层
│   │   ├── user_service.py      # 用户管理
│   │   ├── quota_service.py     # 配额管理
│   │   ├── rate_limit_service.py # 限流服务
│   │   ├── mail_service.py      # 邮件通知
│   │   └── ...
│   ├── controllers/   # API 端点
│   └── migrations/    # 数据库迁移
├── process/           # 异步任务处理服务
│   └── services/
│       ├── database_job_scheduler.py  # 任务调度器
│       └── job_processor.py           # 任务处理器
├── ai-provider/       # AI 处理服务
├── ai-proxy/          # AI 代理服务
├── common/            # 共享库
│   ├── crypto/       # 加密模块
│   ├── database_models/  # 统一数据模型
│   └── api_models/   # 共享 API 模型
├── admin/             # Django 管理后台
├── dockerfiles/       # Docker 构建文件
├── nginx/             # Nginx 配置
└── scripts/           # 部署脚本
```

## API 端点

### 认证

```
POST /api/v1/auth/register   # 用户注册
POST /api/v1/auth/login      # 用户登录
POST /api/v1/auth/refresh    # 刷新 Token
```

### 材料

```
GET  /api/v1/materials       # 获取材料列表
POST /api/v1/materials       # 创建材料
GET  /api/v1/materials/{id}  # 获取材料详情
```

### 丹药 (Pellets)

```
GET  /api/v1/pellets         # 获取丹药列表
GET  /api/v1/pellets/{id}    # 获取丹药详情
```

### 文件上传

```
POST /api/v1/files/init-upload   # 初始化上传
POST /api/v1/files/commit-upload # 提交上传
```

## 测试

```bash
# 运行所有测试
./scripts/test-all.sh

# 后端测试
cd backend && uv run pytest -v

# 前端测试
cd frontend && npm test
```

## 部署

### Ubuntu 服务器

```bash
# 系统初始化
./scripts/ubuntu-init.sh

# 配置环境变量
cp .env.example .env
# 编辑 .env

# 启动服务
docker-compose up -d
```

### 生产环境

```bash
# 使用生产配置
docker-compose -f docker-compose.yml -f docker-compose-aliyun.yml up -d
```

## 常见问题

### 数据库连接失败

检查 MySQL 是否运行，端口是否正确（Docker 映射端口 33060，内部端口 3306）。

### MinIO 连接失败

确保 MinIO 容器已启动，bucket 已创建。运行 `./scripts/init-minio.sh` 初始化 bucket。

### AI 服务超时

检查 AI API 配置是否正确，网络是否可达。

## 许可证

MIT License