import uvicorn
import sys
sys.path.insert(0, '.')
uvicorn.run('main:app', host='0.0.0.0', port=8088, reload=False)
