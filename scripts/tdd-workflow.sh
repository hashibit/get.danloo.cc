#!/bin/bash

# TDD工作流脚本
# 用法: ./tdd-workflow.sh [backend|frontend|ai-provider]

set -e

TARGET=${1:-"both"}

echo "===================="
echo "🔄 TDD 工作流"
echo "===================="

case $TARGET in
    "backend")
        echo "🐍 后端TDD流程"
        cd backend
        echo "1. 运行失败测试 (Red)"
        export DATABASE_URL="sqlite:///./test.db"
        uv run pytest --tb=short -x || true
        
        echo ""
        echo "2. 修改代码让测试通过 (Green)"
        echo "   请修改代码并重新运行: uv run pytest"
        echo ""
        echo "3. 重构代码 (Refactor)"
        echo "   运行完整测试套件: uv run pytest --cov"
        ;;
        
    "frontend") 
        echo "⚛️  前端TDD流程"
        cd frontend
        echo "1. 运行失败测试 (Red)"
        npm test -- --watchAll=false --verbose || true
        
        echo ""
        echo "2. 修改代码让测试通过 (Green)"
        echo "   请修改代码并重新运行: npm test"
        echo ""
        echo "3. 重构代码 (Refactor)"  
        echo "   运行覆盖率测试: npm run test:coverage"
        ;;
        
    "ai-provider")
        echo "🤖 AI Provider TDD流程"
        cd ai-provider
        echo "1. 运行失败测试 (Red)"
        # Check if uv is available, fallback to pip if not
        if command -v uv &> /dev/null; then
            uv run pytest --tb=short -x || true
        else
            python -m pytest --tb=short -x || true
        fi
        
        echo ""
        echo "2. 修改代码让测试通过 (Green)"
        if command -v uv &> /dev/null; then
            echo "   请修改代码并重新运行: uv run pytest"
        else
            echo "   请修改代码并重新运行: python -m pytest"
        fi
        echo ""
        echo "3. 重构代码 (Refactor)"
        if command -v uv &> /dev/null; then
            echo "   运行完整测试套件: uv run pytest --cov"
        else
            echo "   运行完整测试套件: python -m pytest --cov"
        fi
        ;;
        
    "both")
        echo "🔄 完整TDD流程"
        echo ""
        echo "选择目标:"
        echo "  ./tdd-workflow.sh backend     - 后端TDD"
        echo "  ./tdd-workflow.sh frontend    - 前端TDD"
        echo "  ./tdd-workflow.sh ai-provider - AI Provider TDD"
        ;;
        
    *)
        echo "❌ 无效参数: $TARGET"
        echo "用法: ./tdd-workflow.sh [backend|frontend|ai-provider]"
        exit 1
        ;;
esac

echo "===================="