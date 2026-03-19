#!/bin/bash

# EmoHealer Docker 停止脚本

echo "🛑 停止 EmoHealer Docker 环境..."

# 停止所有服务
docker-compose down

echo "✅ 所有服务已停止"
echo ""
echo "💡 提示: 数据已保存在 docker volume 中，下次启动会自动恢复"
echo "   如需完全清除数据: docker-compose down -v"
