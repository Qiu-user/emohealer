import os
import sys
import subprocess

# 改变工作目录
os.chdir(r"c:\Users\18746\Desktop\biyeshixi\backend")

# 用sys.executable确保使用同一个Python解释器
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8088", "--reload"],
    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
)

print(f"Server started. PID: {proc.pid}")
input("Press Enter to exit...")
proc.terminate()
