@echo off
echo ========================================
echo   EmoHealer AI 后端服务启动
echo ========================================
echo.

cd /d "%~dp0"

echo 检查数据库连接...
python -c "from database import engine; conn = engine.connect(); conn.close(); print('OK')" 2>NUL
if errorlevel 1 (
    echo [错误] 数据库连接失败！
    echo 请确保MySQL服务已启动
    pause
    exit /b 1
)

echo 数据库连接成功！
echo.
echo 启动服务...
echo.
echo 服务启动后，请访问: http://localhost:8088
echo 测试API: http://localhost:8088/api/health
echo.
echo 按 Ctrl+C 停止服务
echo.

python main.py
