import uvicorn
import sys
import os

os.chdir(r'c:\Users\18746\Desktop\biyeshixi\backend')
sys.path.insert(0, '.')

print("Starting server on port 8089...")
uvicorn.run('main:app', host='0.0.0.0', port=8089, reload=False)
