import subprocess
import os

# 启动后端服务
os.chdir(r"c:\Users\18746\Desktop\biyeshixi\backend")
proc = subprocess.Popen(
    ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8088"],
    creationflags=subprocess.CREATE_NEW_CONSOLE
)
print(f"后端服务已启动，PID: {proc.pid}")
print("访问 http://localhost:8088 查看API")
input("按回车键退出...")
proc.terminate()
