#!/bin/bash

# Docker Compose 运行脚本
# 用法: ./scripts/docker-run.sh [local|prod] [up|down|restart]

set -e

ENV=${1:-local}
CMD=${2:-up}

ENV_FILE=".env.${ENV}"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 环境文件 $ENV_FILE 不存在"
    exit 1
fi

echo "🔧 使用环境文件: $ENV_FILE"
echo "📦 执行命令: docker compose $CMD"

case $CMD in
  up)
    docker compose --env-file "$ENV_FILE" up -d
    ;;
  down)
    docker compose --env-file "$ENV_FILE" down
    ;;
  restart)
    docker compose --env-file "$ENV_FILE" restart
    ;;
  logs)
    docker compose --env-file "$ENV_FILE" logs -f
    ;;
  *)
    docker compose --env-file "$ENV_FILE" $CMD
    ;;
esac

echo "✅ 完成"