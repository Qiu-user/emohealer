@echo off
echo ============================================================
echo EmoHealer AI服务修复脚本
echo ============================================================
echo.

echo [1/5] 检查当前端口占用...
netstat -ano | findstr :8092 | findstr LISTENING
echo.

echo [2/5] 停止所有Python后端进程...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul
echo.

echo [3/5] 检查端口是否已释放...
netstat -ano | findstr :8092 | findstr LISTENING
if %errorlevel% equ 0 (
    echo [WARNING] 端口8092仍被占用，请手动关闭
) else (
    echo [OK] 端口8092已释放
)
echo.

echo [4/5] 启动后端服务...
cd /d c:\Users\18746\Desktop\biyeshixi\backend
start "Backend Server" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8092 --reload"
echo.

echo [5/5] 等待服务启动...
timeout /t 5 /nobreak >nul
echo.

echo ============================================================
echo 服务状态检查
echo ============================================================
echo.

echo 检查后端API...
curl -s http://localhost:8092/docs | findstr "EmoHealer" >nul
if %errorlevel% equ 0 (
    echo [OK] 后端服务已启动
) else (
    echo [WARNING] 后端服务可能未正常启动
)
echo.

echo ============================================================
echo 下一步操作
echo ============================================================
echo.
echo 1. 打开浏览器访问: http://localhost:5000/emohealer2.html
echo 2. 登录或注册账号
echo 3. 发送消息测试AI对话
echo.
echo 如果仍有问题，请查看:
echo - 后端控制台错误日志
echo - 浏览器F12开发者工具Console
echo - AI_SERVICE_FIX.md 文档
echo.
echo 按任意键退出...
pause >nul
