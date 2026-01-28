#!/bin/bash

# Crux AgenticRAG 全栈启动脚本

echo "🚀 Starting Crux AgenticRAG Full Stack..."

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# 启动后端服务（后台运行）
echo "🔧 Starting Backend API Server..."
cd backend

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 启动FastAPI服务（后台）
echo "🌐 Starting FastAPI on http://localhost:8000"
python main.py &
BACKEND_PID=$!

cd ..

# 等待后端启动
sleep 3

# 启动前端服务
echo "🎨 Starting Frontend Development Server..."
cd frontend

# 安装依赖（如果不存在）
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# 启动Vite开发服务器
echo "🚀 Starting Vite on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

cd ..

# 等待服务启动
sleep 5

echo ""
echo "🎉 Crux AgenticRAG is now running!"
echo ""
echo "📊 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# 清理函数
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 等待用户中断
wait
