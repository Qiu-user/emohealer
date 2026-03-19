@echo off
chcp 65001 >nul
echo ========================================
echo   EmoHealer Docker 环境停止脚本
echo ========================================
echo.

echo [信息] 停止所有 Docker 服务...
docker-compose down

echo.
echo [完成] 所有服务已停止
echo.
echo 提示: 数据已保存在 docker volume 中
echo       如需完全清除数据: docker-compose down -v
echo.
pause
