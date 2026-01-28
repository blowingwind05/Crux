#!/bin/bash

# Crux Backend 启动脚本

echo "🚀 Starting Crux AgenticRAG Backend..."

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

# 安装依赖（如果虚拟环境不存在）
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
    echo "📦 Installing dependencies..."
    ./venv/bin/pip install -r requirements.txt
fi

# 激活虚拟环境并启动服务
echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "🌟 Starting FastAPI server..."
./venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
