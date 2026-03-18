#!/bin/bash

CONTAINER_NAME="crux"

echo "🚀 开始启动 Crux 开发环境..."

# 1. 检查并启动 Docker 容器
# 如果容器存在且正在运行，则跳过创建；如果停止，则启动它；如果不存在，则全新运行。
if [ "$(docker ps -q -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "✅ 容器 ${CONTAINER_NAME} 已经在运行中。"
elif [ "$(docker ps -a -q -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "▶️ 容器 ${CONTAINER_NAME} 已存在但处于停止状态，正在启动..."
    docker start ${CONTAINER_NAME}
else
    echo "🆕 正在创建并启动新的 ${CONTAINER_NAME} 容器..."
    docker run -itd --name ${CONTAINER_NAME} -v ~/:/workspace --net=host -p 5173:5173 -p 8001:8001 crux:v1.2 /bin/bash
fi

# 给容器一小段启动时间
sleep 2

# 2. 在容器内启动 Python 后端 (后台静默运行)
echo "🐍 正在容器内启动 Python 后端 (日志将输出到 backend.log)..."
docker exec -d ${CONTAINER_NAME} /bin/bash -c "cd /workspace/crux && nohup python Crux/backend/main.py > backend.log 2>&1 &"

# 3. 在容器内启动 Node.js 前端 (保留在前台以便你查看控制台输出和进行热更新)
echo "⚛️ 正在容器内启动前端 (npm run dev)..."
docker exec -it ${CONTAINER_NAME} /bin/bash -c "cd /workspace/crux/Crux/frontend && npm run dev"