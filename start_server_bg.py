import threading
import time
import sys
import os

os.chdir(r'c:\Users\18746\Desktop\biyeshixi\backend')
sys.path.insert(0, r'c:\Users\18746\Desktop\biyeshixi\backend')

def run_server():
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8092, reload=False)

print("Starting backend server...")
t = threading.Thread(target=run_server, daemon=True)
t.start()

# Wait and check
time.sleep(5)

import urllib.request
try:
    r = urllib.request.urlopen('http://localhost:8092/api/health')
    print("[OK] Backend running on http://localhost:8092")
    print("     ", r.read().decode())
except Exception as e:
    print("[ERROR] Backend failed to start:", e)

print("\nFrontend: file:///c:/Users/18746/Desktop/biyeshixi/frontend/emohealer2.html")
