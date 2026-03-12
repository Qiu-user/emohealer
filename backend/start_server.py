import uvicorn
import sys
import time
import os

os.chdir(r'c:\Users\18746\Desktop\biyeshixi\backend')
sys.path.insert(0, '.')

time.sleep(2)

uvicorn.run('main:app', host='0.0.0.0', port=8088, reload=False)
