@echo off
chcp 65001 >nul
title Git安装与项目初始化

echo ========================================
echo   EmoHealer 项目 Git 版本管理
echo ========================================
echo.

:: 检查Git
where git >nul 2>&1
if %errorlevel% equ 0 goto :git_installed

echo [步骤1] Git未安装，正在下载安装向导...
echo.
echo 请访问以下链接下载Git:
echo   https://git-scm.com/download/win
echo.
echo 下载完成后运行此脚本
echo.
pause
exit /b 1

:git_installed
echo [OK] Git已安装
echo.

:: 设置项目目录
set PROJECT_DIR=c:\Users\18746\Desktop\biyeshixi
cd /d "%PROJECT_DIR%"

:: 检查是否已有仓库
if exist ".git" (
    echo [提示] Git仓库已存在
) else (
    echo [2] 初始化Git仓库...
    git init
)
echo.

:: 添加.gitignore
echo [3] 添加.gitignore文件...
if exist ".gitignore" (
    git add .gitignore
    echo    已添加 .gitignore
)
echo.

:: 添加README
echo [4] 创建README...
if not exist "README.md" (
    echo # EmoHealer 情绪疗愈平台 > README.md
    echo. >> README.md
    echo 基于AI的情绪疗愈系统 >> README.md
    echo. >> README.md
    echo ## 功能 >> README.md
    echo - AI对话陪伴 >> README.md
    echo - 情绪趋势分析 >> README.md
    echo - 心理测评 >> README.md
    echo - 疗愈方案 >> README.md
    echo - 预约咨询 >> README.md
)
git add README.md
echo.

:: 添加所有文件
echo [5] 添加项目文件...
git add .
echo.

:: 提交
echo [6] 提交代码...
git commit -m "Initial commit - EmoHealer情绪疗愈平台"
echo.

:: 检查远程仓库
git remote -v >nul 2>&1
if %errorlevel% neq 0 (
    echo ========================================
    echo   仓库初始化完成！
    echo ========================================
    echo.
    echo 请在GitHub创建仓库后运行:
    echo   git remote add origin https://github.com/你的用户名/仓库名.git
    echo   git push -u origin main
    echo.
) else (
    echo [7] 推送代码...
    git push -u origin main 2>nul
    if %errorlevel% equ 0 (
        echo.
        echo ========================================
        echo   项目已成功发布到GitHub！
        echo ========================================
    ) else (
        echo.
        echo [提示] 推送失败，请检查远程仓库配置
    )
)

echo.
pause
