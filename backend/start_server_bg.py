import subprocess
import time
import os

os.chdir(r'c:\Users\18746\Desktop\biyeshixi\backend')

time.sleep(2)

# 启动服务器
proc = subprocess.Popen(
    ['python', 'run_8089.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)

print(f"Started server with PID: {proc.pid}")
print("Waiting for server to start...")

# 等待几秒
time.sleep(3)

# 检查是否还在运行
if proc.poll() is None:
    print("Server is running!")
else:
    print("Server exited with code:", proc.poll())
