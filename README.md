# Danloo - AI Powered Knowledge Extraction Platform

Danloo is an AI-powered content refinement platform that transforms raw technical materials into structured knowledge capsules. Users act as "alchemists" who upload dialogue records, PDF documents, or text notes, and through intelligent AI extraction and categorization, generate structured knowledge content.

## Screenshots

![Dashboard](docs/en_1.png)

![Material Analysis](docs/en_2.png)

![Home](docs/cn_1.png)

![Material List](docs/cn_2.png)

![Material Detail](docs/cn_3.png)

![Knowledge Capsule](docs/cn_4.png)

![Profile](docs/cn_5.png)

## Features

- Intelligent Extraction - AI analyzes content, extracts knowledge points, generates summaries
- Smart Categorization - Auto-identifies premium content (Gold Pills), supports custom tags
- Multi-format Support - Text, PDF, images, video and more
- Secure Authentication - JWT user auth + AK/SK service auth
- i18n Support - Chinese and English interfaces

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Backend | FastAPI + Python 3.11+ |
| Database | MySQL 8.0 |
| Storage | MinIO (S3 compatible) |
| AI | Claude / OpenAI / AWS Bedrock |
| Deployment | Docker Compose |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (Reverse Proxy)                 │
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

## Design Highlights

### Security & Authentication

**Dual Authentication System**
- JWT Authentication - Standard user authentication with access/refresh tokens
- AK/SK Authentication - Access Key / Secret Key pair for service-to-service authentication with HMAC signature validation

**Cryptography Module**
- Secure key pair generation using `secrets` module
- Password hashing with bcrypt + salt
- Content integrity verification via HMAC
- Bearer token creation and validation

### Rate Limiting & Protection

**Multi-level Rate Limiting**
- API rate limiting (100 requests/second per IP)
- Email rate limiting (2 emails/5 minutes per address)
- SMS rate limiting (1 SMS/2 minutes per phone)

**Circuit Breaker Pattern**
- Automatic failure detection with configurable thresholds
- Three states: CLOSED -> OPEN -> HALF_OPEN
- Graceful degradation and automatic recovery

### Quota Management

**User Quota System**
- Daily quota allocation and tracking
- Automatic quota reset at midnight
- Usage logging and analytics
- Quota upgrade support

**Token Quota Integration**
- AI token usage tracking per model
- Real-time quota consumption
- Cross-service token accounting

### Async Job Processing

**Database-based Job Queue**
- Persistent job storage in MySQL
- Priority-based job scheduling
- Parallel job execution with ThreadPoolExecutor
- Automatic retry with exponential backoff

**Task Decomposition**
- Jobs split into granular tasks
- Independent task execution
- Progress tracking and status updates

### Notification System

**Multi-channel Notifications**
- Email notifications (SMTP with TLS/SSL)
- WeChat integration support
- Rate-limited sending to prevent abuse
- Template-based message generation

### Unified Data Model

**Shared Database Models** (`common/database_models/`)
- `UserDB` - User accounts with quota tracking
- `MaterialDB` - Uploaded materials metadata
- `PelletDB` - Generated knowledge capsules
- `JobDB` / `TaskDB` - Async processing state
- `TokenUsageDB` - AI token consumption logs
- `UserQuotaDB` - Daily quota tracking

**Benefits**
- Single source of truth across services
- Type-safe model definitions
- Alembic migrations for schema evolution

## Quick Start

### Requirements

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)
- uv (Python package manager)

### Docker Deployment (Recommended)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your configuration
#    - DATABASE_URL: Database connection
#    - JWT_SECRET: JWT signing key
#    - AI API Keys: OPENAI_TOKEN / ANTHROPIC_API_KEY

# 3. Start all services
docker-compose up -d

# 4. Check service status
docker-compose ps
```

After startup:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

### Local Development

#### Backend

```bash
cd backend
uv venv && source .venv/bin/activate
uv sync

# Set environment variables
export DATABASE_URL=mysql+pymysql://danloo:password@localhost:33060/danloo
export JWT_SECRET=your-secret-key

# Run database migrations
uv run alembic upgrade head

# Start server
uv run uvicorn main:app --reload --port 8000
```

#### AI Provider

```bash
cd ai-provider/ai-provider
uv venv && source .venv/bin/activate
uv sync

# Configure AI API Keys
export OPENAI_TOKEN=your-token
export ANTHROPIC_API_KEY=your-key

# Start service
uv run python main.py
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

### Core Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | MySQL connection string | `mysql+pymysql://user:pass@host:3306/db` |
| `JWT_SECRET` | JWT signing secret | Generate with `openssl rand -hex 32` |
| `S3_ENDPOINT` | MinIO/OSS endpoint | `http://localhost:9000` |
| `S3_ACCESS_KEY` | S3 access key | `minioadmin` |
| `S3_SECRET_KEY` | S3 secret key | `minioadmin` |

### AI Configuration

| Variable | Description |
|----------|-------------|
| `OPENAI_TOKEN` | OpenAI compatible API token |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `ANTHROPIC_BASE_URL` | Claude API proxy URL (optional) |

## Project Structure

```
danloo/
├── frontend/           # Next.js frontend application
├── backend/            # FastAPI backend service
│   ├── services/      # Business logic
│   │   ├── user_service.py
│   │   ├── quota_service.py
│   │   ├── rate_limit_service.py
│   │   ├── mail_service.py
│   │   └── ...
│   ├── controllers/   # API endpoints
│   └── migrations/    # Database migrations
├── process/           # Async job processing service
│   └── services/
│       ├── database_job_scheduler.py
│       └── job_processor.py
├── ai-provider/       # AI processing service
├── ai-proxy/          # AI proxy service
├── common/            # Shared libraries
│   ├── crypto/       # Cryptography module
│   ├── database_models/  # Unified data models
│   └── api_models/   # Shared API schemas
├── admin/             # Django admin panel
├── dockerfiles/       # Docker build files
├── nginx/             # Nginx configuration
└── scripts/           # Deployment scripts
```

## API Endpoints

### Authentication

```
POST /api/v1/auth/register   # User registration
POST /api/v1/auth/login      # User login
POST /api/v1/auth/refresh    # Refresh token
```

### Materials

```
GET  /api/v1/materials       # List materials
POST /api/v1/materials       # Create material
GET  /api/v1/materials/{id}  # Get material details
```

### Pellets

```
GET  /api/v1/pellets         # List pellets
GET  /api/v1/pellets/{id}    # Get pellet details
```

### File Upload

```
POST /api/v1/files/init-upload   # Initialize upload
POST /api/v1/files/commit-upload # Commit upload
```

## Testing

```bash
# Run all tests
./scripts/test-all.sh

# Backend tests
cd backend && uv run pytest -v

# Frontend tests
cd frontend && npm test
```

## Deployment

### Ubuntu Server

```bash
# System initialization
./scripts/ubuntu-init.sh

# Configure environment
cp .env.example .env
# Edit .env

# Start services
docker-compose up -d
```

### Production

```bash
# Use production configuration
docker-compose -f docker-compose.yml -f docker-compose-aliyun.yml up -d
```

## Troubleshooting

### Database Connection Failed

Check if MySQL is running and port is correct (Docker mapped port 33060, internal port 3306).

### MinIO Connection Failed

Ensure MinIO container is running and buckets are created. Run `./scripts/init-minio.sh` to initialize buckets.

### AI Service Timeout

Check if AI API configuration is correct and network is accessible.

## License

MIT License
