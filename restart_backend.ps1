# 停止所有8092端口的Python进程
Get-NetTCPConnection -LocalPort 8092 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped process $($_.OwningProcess)"
}

Start-Sleep -Seconds 2

# 检查端口是否已释放
if (Get-NetTCPConnection -LocalPort 8092 -ErrorAction SilentlyContinue) {
    Write-Host "[WARNING] Port 8092 still in use"
} else {
    Write-Host "[OK] Port 8092 is now free"
}

Write-Host "Ready to start backend server"
