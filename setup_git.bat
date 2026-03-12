@echo off
chcp 65001 >nul
echo ========================================
echo   Git 安装检查与项目初始化
echo ========================================
echo.

:: 检查Git是否安装
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Git未安装
    echo.
    echo 请先下载安装Git:
    echo   https://git-scm.com/download/win
    echo.
    echo 安装时选择"Use Git from the Windows Command Prompt"
    echo.
    pause
    exit /b 1
)

echo [OK] Git已安装
echo.

:: 设置项目目录
set PROJECT_DIR=c:\Users\18746\Desktop\biyeshixi
cd /d "%PROJECT_DIR%"

:: 初始化Git仓库
echo [1/5] 初始化Git仓库...
if not exist ".git" (
    git init
    echo.
) else (
    echo 仓库已存在
    echo.
)

:: 添加.gitignore
echo [2/5] 添加.gitignore...
git add .gitignore
echo.

:: 添加所有文件
echo [3/5] 添加项目文件...
git add .
echo.

:: 首次提交
echo [4/5] 提交代码...
git commit -m "Initial commit - EmoHealer情绪疗愈平台"
echo.

:: 提示下一步
echo [5/5] 完成!
echo.
echo ========================================
echo   下一步操作：
echo ========================================
echo 1. 访问 https://github.com/new 创建仓库
echo 2. 复制仓库URL (如: https://github.com/用户名/emohealer.git)
echo 3. 执行以下命令:
echo.
echo    cd %PROJECT_DIR%
echo    git remote add origin 你的仓库URL
echo    git push -u origin main
echo.
echo ========================================
pause
