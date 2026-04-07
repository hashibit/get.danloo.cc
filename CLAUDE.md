# Danloo 项目指南

## 项目概述

Danloo 是一个 AI 驱动的内容提炼平台，将原始技术材料转化为结构化的知识胶囊。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14 + TypeScript + Tailwind CSS |
| 后端 | FastAPI + Python 3.11+ |
| 数据库 | MySQL 8.0 |
| 存储 | MinIO (S3 兼容) |
| AI | Claude / OpenAI / AWS Bedrock |
| 部署 | Docker Compose |
| 包管理 | uv (Python) / npm (Node.js) |

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

## 开发指南

### 环境要求

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- uv (Python 包管理器)

### 本地开发

```bash
# 后端
cd backend
uv venv && source .venv/bin/activate
uv sync
uv run uvicorn main:app --reload --port 8000

# AI Provider
cd ai-provider/ai-provider
uv venv && source .venv/bin/activate
uv sync
uv run python main.py

# 前端
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
cp .env.example .env
docker-compose up -d
```

服务: 前端 http://localhost:3000 | API 文档 http://localhost:8000/docs

### 数据库迁移

```bash
cd backend
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## 注意事项

- 所有敏感配置通过环境变量注入，不要在代码中硬编码
- `.env` 文件已在 `.gitignore` 中，不会被提交