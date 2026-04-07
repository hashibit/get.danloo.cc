#!/bin/bash

# 环境管理脚本
# 用法: ./scripts/env.sh local|prod

set -e

ENV=${1:-local}

case $ENV in
  local)
    echo "🔧 切换到本地开发环境..."
    cp .env.local .env
    echo "✅ 已切换到本地环境 (.env.local -> .env)"
    ;;
  prod)
    echo "🚀 切换到生产环境..."
    cp .env.prod .env
    echo "✅ 已切换到生产环境 (.env.prod -> .env)"
    echo "⚠️  请确保生产环境的敏感信息已正确配置！"
    ;;
  *)
    echo "❌ 无效的环境参数"
    echo "用法: $0 {local|prod}"
    echo ""
    echo "示例:"
    echo "  $0 local   # 切换到本地开发环境"
    echo "  $0 prod    # 切换到生产环境"
    exit 1
    ;;
esac

echo ""
echo "当前环境变量:"
echo "NODE_ENV=$(grep NODE_ENV .env | cut -d'=' -f2)"
echo "S3_EXTERNAL_ENDPOINT=$(grep S3_EXTERNAL_ENDPOINT .env | cut -d'=' -f2)"
echo "FRONTEND_URL=$(grep FRONTEND_URL .env | cut -d'=' -f2)"