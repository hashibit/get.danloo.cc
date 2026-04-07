# Danloo Systemd Service Files

This directory contains systemd service files for deploying Danloo microservices and frontend.

## Services

- `danloo-frontend.service` - Next.js frontend application (port 3000)
- `danloo-backend.service` - FastAPI backend main service (port 8000)
- `danloo-ai-provider.service` - AI provider service (port 8002)
- `danloo-process.service` - Process service (port 8001)
- `danloo-ai-proxy.service` - AI proxy service (port 8091)
- `danloo-admin.service` - Admin service (port 8003)
- `danloo-nginx.service` - Nginx reverse proxy (port 80)
- `danloo-nginx-minio.service` - Nginx proxy for MinIO CORS (port 9000)

## Installation

1. Copy service files to systemd directory:
   ```bash
   sudo cp systemdfiles/*.service /etc/systemd/system/
   ```

2. Reload systemd:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Create danloo user if not exists:
   ```bash
   sudo useradd -r -s /bin/false danloo
   ```


5. Create environment file:
   ```bash
   sudo cp .env.systemd /opt/danloo/.env.systemd
   sudo chown danloo:danloo /opt/danloo/.env.systemd
   sudo chmod 600 /opt/danloo/.env.systemd
   ```

## Management

Start all services:
```bash
sudo systemctl start danloo-frontend danloo-backend danloo-ai-provider danloo-process danloo-ai-proxy danloo-admin danloo-nginx danloo-nginx-minio
```

Enable services on boot:
```bash
sudo systemctl enable danloo-frontend danloo-backend danloo-ai-provider danloo-process danloo-ai-proxy danloo-admin danloo-nginx danloo-nginx-minio
```

Check status:
```bash
sudo systemctl status danloo-frontend
```

View logs:
```bash
sudo journalctl -u danloo-frontend -f
```

## Environment Variables

All services use the environment file at `/opt/danloo/.env.systemd`. This file contains infrastructure connections:
- MySQL: configured via DATABASE_URL
- MinIO: configured via S3_ENDPOINT

Ensure this file exists with proper permissions before starting services.