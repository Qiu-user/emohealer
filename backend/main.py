from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine, Base
from config import settings
from src.routes import api
from src.routes import websocket
import os

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title="EmoHealer API",
    description="基于AIGC的情绪疗愈医生后端服务",
    version="1.0.0"
)

# 配置静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 配置CORS跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由 - 只注册api.router，auth路由已在api.py中定义
app.include_router(api.router, prefix="/api", tags=["API"])

# 注册WebSocket路由
app.include_router(websocket.router, tags=["WebSocket"])

@app.get("/")
@app.get("/api")
@app.get("/api/health")
def root():
    return {
        "status": "ok",
        "message": "欢迎使用 EmoHealer AI 情绪疗愈平台",
        "version": "2.0.0",
        "docs": "/docs"
    }

# 前端页面路由
@app.get("/emohealer")
def emohealer_page():
    html_path = os.path.join(STATIC_DIR, "emohealer2.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "File not found"}

# 运维管理后台
@app.get("/admin")
def admin_page():
    html_path = os.path.join(TEMPLATE_DIR, "admin.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "Admin page not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
