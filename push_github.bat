@echo off
echo ========================================
echo 推送到 GitHub
echo ========================================
cd /d "%~dp0"
echo.
echo 正在推送...
git push -u origin master
echo.
echo 完成!
pause
