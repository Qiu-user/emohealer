@echo off
echo ========================================
echo   EmoHealer 后端服务启动器
echo ========================================
echo.
echo 正在启动后端服务...
echo 服务地址: http://localhost:8088
echo API文档: http://localhost:8088/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

cd /d "%~dp0"
python -m uvicorn main:app --host 0.0.0.0 --port 8088 --reload

pause
