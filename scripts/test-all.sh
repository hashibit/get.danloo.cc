#!/bin/bash

# 测试执行脚本
set -e

echo "===================="
echo "🧪 运行所有测试"
echo "===================="

# 后端测试
echo ""
echo "📦 后端测试"
echo "----------"
cd backend
echo "使用测试数据库: SQLite"
export DATABASE_URL="sqlite:///./test.db"

echo "运行Python测试..."
if uv run pytest -v; then
    echo "✅ 后端测试通过"
else
    echo "❌ 后端测试失败"
    exit 1
fi

# 前端测试  
echo ""
echo "🎨 前端测试"
echo "----------"
cd ../frontend

echo "运行React组件测试..."
if npm test -- --watchAll=false; then
    echo "✅ 前端测试通过"  
else
    echo "❌ 前端测试失败"
    exit 1
fi

# AI Provider 测试
echo ""
echo "🤖 AI Provider 测试"
echo "----------"
cd ../ai-provider

echo "运行AI Provider测试..."
if command -v uv &> /dev/null; then
    if uv run pytest -v; then
        echo "✅ AI Provider测试通过"
    else
        echo "❌ AI Provider测试失败"
        exit 1
    fi
else
    if python -m pytest -v; then
        echo "✅ AI Provider测试通过"
    else
        echo "❌ AI Provider测试失败"
        exit 1
    fi
fi

echo ""
echo "🎉 所有测试通过!"
echo "===================="