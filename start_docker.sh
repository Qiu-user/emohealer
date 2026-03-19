#!/bin/bash

# EmoHealer Docker 启动脚本

set -e

echo "🚀 启动 EmoHealer Docker 环境..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 docker-compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose 未安装，请先安装"
    exit 1
fi

# 复制环境变量文件
if [ ! -f .env ]; then
    echo "📝 创建 .env 文件..."
    cp .env.example .env
fi

# 创建网络
echo "🌐 创建 Docker 网络..."
docker network create emohealer_network 2>/dev/null || true

# 启动 MySQL
echo "📦 启动 MySQL 数据库..."
docker-compose up -d mysql

# 等待 MySQL 启动
echo "⏳ 等待 MySQL 启动..."
sleep 10

# 检查 MySQL 是否就绪
for i in {1..30}; do
    if docker-compose exec -T mysql mysqladmin ping -h localhost -u root -p"$MYSQL_ROOT_PASSWORD" &> /dev/null; then
        echo "✅ MySQL 已就绪"
        break
    fi
    echo "⏳ 等待 MySQL 启动... ($i/30)"
    sleep 2
done

echo ""
echo "✅ EmoHealer Docker 环境已启动!"
echo ""
echo "📊 MySQL 连接信息:"
echo "   主机: localhost"
echo "   端口: 3306"
echo "   用户: emohealer"
echo "   密码: emohealer_pass_2026"
echo "   数据库: emohealer"
echo ""
echo "🔧 常用命令:"
echo "   查看日志: docker-compose logs -f mysql"
echo "   停止服务: ./stop_docker.sh"
echo "   完整重启: docker-compose restart mysql"
echo ""
