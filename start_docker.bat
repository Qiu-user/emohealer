@echo off
chcp 65001 >nul
echo ========================================
echo   EmoHealer Docker 环境启动脚本
echo ========================================
echo.

:: 检查 Docker 是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 未安装，请先安装 Docker Desktop
    pause
    exit /b 1
)

:: 检查 docker-compose 是否安装
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [错误] docker-compose 未安装
    pause
    exit /b 1
)

:: 复制环境变量文件
if not exist ".env" (
    echo [信息] 创建 .env 文件...
    copy .env.example .env
)

echo [信息] 启动 MySQL 数据库...
docker-compose up -d mysql

echo [信息] 等待 MySQL 启动...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo   Docker 环境已启动!
echo ========================================
echo.
echo 数据库连接信息:
echo   主机: localhost
echo   端口: 3306
echo   用户: emohealer
echo   密码: emohealer_pass_2026
echo   数据库: emohealer
echo.
echo 常用命令:
echo   查看日志: docker-compose logs -f mysql
echo   停止服务: stop_docker.bat
echo.
pause
