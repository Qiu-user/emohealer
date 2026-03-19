@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 正在初始化Git仓库...
git init

echo 添加远程仓库...
git remote add origin https://github.com/Qiu-user/emohealer.git

echo 添加文件...
git add .

echo 提交代码...
git commit -m "Initial commit - EmoHealer情绪疗愈平台"

echo 推送到GitHub...
git push -u origin main

echo.
echo 完成！
pause
