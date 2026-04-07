#!/bin/bash

# Docker部署验证脚本
echo "🐳 Docker Deployment Verification Script"
echo "========================================"

# 检查Docker和docker-compose是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed or not in PATH"
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# 检查docker-compose.yml文件
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found in current directory"
    exit 1
fi

echo "✅ docker-compose.yml found"

# 验证docker-compose配置
echo "🔍 Validating docker-compose configuration..."
if docker-compose config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml syntax is valid"
else
    echo "❌ docker-compose.yml has syntax errors:"
    docker-compose config
    exit 1
fi

# 检查必要的文件是否存在
echo "🔍 Checking required files..."

required_files=(
    "backend/Dockerfile"
    "process/Dockerfile" 
    "ai-provider/ai-provider/Dockerfile"
    "frontend/Dockerfile"
    "nginx-minio.conf"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
        echo "❌ Missing: $file"
    else
        echo "✅ Found: $file"
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "❌ Missing ${#missing_files[@]} required files. Please create them before deployment."
    exit 1
fi

# 构建所有服务
echo "🏗️  Building all services..."
if docker-compose build --no-cache; then
    echo "✅ All services built successfully"
else
    echo "❌ Build failed"
    exit 1
fi

# 启动服务（后台模式）
echo "🚀 Starting services..."
if docker-compose up -d; then
    echo "✅ Services started successfully"
else
    echo "❌ Failed to start services"
    exit 1
fi

# 等待服务启动
echo "⏳ Waiting for services to be ready..."
sleep 10

# 检查服务状态
echo "📊 Checking service status..."
docker-compose ps

# 检查服务健康状况
echo "🏥 Checking service health..."

services=("backend:8000" "process:8001" "ai-provider:8002" "frontend:3000")
healthy_services=0
total_services=${#services[@]}

for service in "${services[@]}"; do
    service_name=$(echo $service | cut -d':' -f1)
    port=$(echo $service | cut -d':' -f2)
    
    echo -n "Checking $service_name on port $port... "
    
    if curl -f -s "http://localhost:$port/" > /dev/null 2>&1; then
        echo "✅ Healthy"
        ((healthy_services++))
    elif curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ Healthy (via /health)"
        ((healthy_services++))
    else
        echo "❌ Not responding"
        echo "   Checking container logs for $service_name:"
        docker-compose logs --tail=10 $service_name
    fi
done

echo ""
echo "📈 Health Summary: $healthy_services/$total_services services healthy"

# 检查数据库连接
echo "🗄️  Checking database connection..."
if docker-compose exec -T db mysql -u danloo -ppassword -e "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
fi

# 检查MinIO
echo "💾 Checking MinIO..."
if curl -f -s "http://localhost:9000/minio/health/live" > /dev/null 2>&1; then
    echo "✅ MinIO is healthy"
else
    echo "❌ MinIO is not responding"
fi

# 显示端口映射
echo ""
echo "🌐 Service URLs:"
echo "   Backend:     http://localhost:8000"
echo "   Process:     http://localhost:8001"
echo "   AI Provider: http://localhost:8002"
echo "   Frontend:    http://localhost:3000"
echo "   MinIO Console: http://localhost:9001"
echo "   MinIO API:   http://localhost:9000"
echo "   Database:    localhost:33060"

# 最终状态
if [ $healthy_services -eq $total_services ]; then
    echo ""
    echo "🎉 All services are healthy! Deployment successful."
    echo "💡 You can now run the API tests:"
    echo "   cd tests && uv run python http_tests/run_all_tests.py"
    exit 0
else
    echo ""
    echo "⚠️  Some services are not healthy. Check the logs above."
    echo "🔧 To troubleshoot:"
    echo "   docker-compose logs [service-name]"
    echo "   docker-compose ps"
    exit 1
fi