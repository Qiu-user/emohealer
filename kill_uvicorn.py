import subprocess
import time

# 查找并终止占用8092端口的进程
result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if ':8092' in line and 'LISTENING' in line:
        parts = line.split()
        pid = parts[-1]
        print(f"终止进程 {pid}")
        subprocess.run(['taskkill', '/F', '/PID', pid])
        break

print("等待2秒...")
time.sleep(2)

# 启动新服务
import os
os.chdir(r"c:\Users\18746\Desktop\biyeshixi\backend")
proc = subprocess.Popen(
    ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8092"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
print(f"服务已重启，PID: {proc.pid}")
