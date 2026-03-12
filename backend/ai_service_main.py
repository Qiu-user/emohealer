"""
AI服务入口脚本
启动独立的AI服务（可选）
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.enhanced_ai_agent import enhanced_ai_agent, PersonaManager, EmotionAnalyzer
from src.config.ai_config import AI_CONFIG, update_llm_provider

app = FastAPI(title="EmoHealer AI Service", version="2.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    user_id: int
    message: str
    emotion: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    emotion: str
    confidence: float
    is_crisis: bool
    crisis_level: str = "none"
    agent_role: str = "listener"
    cognitive_pattern: Optional[str] = None
    suggested_approach: Optional[str] = None
    timestamp: str


class LLMConfigRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_secret: Optional[str] = None
    model: Optional[str] = None


# ==================== 对话接口 ====================

@app.post("/ai/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """AI对话接口"""
    result = await enhanced_ai_agent.chat(
        user_id=request.user_id,
        message=request.message,
        emotion=request.emotion
    )
    return ChatResponse(**result)


@app.get("/ai/personas")
def get_personas():
    """获取可用的智能体角色"""
    personas = {}
    for role, config in PersonaManager.PERSONAS.items():
        personas[role] = {
            "name": config.name,
            "description": config.description,
            "traits": config.traits,
            "response_style": config.response_style
        }
    return {"code": 200, "data": personas}


@app.post("/ai/config/llm")
def config_llm(request: LLMConfigRequest):
    """配置LLM"""
    params = {
        "api_key": request.api_key or "",
        "api_base": request.api_base or "",
        "model": request.model or ""
    }
    if request.api_secret:
        params["api_secret"] = request.api_secret
    
    update_llm_provider(request.provider, **params)
    enhanced_ai_agent.set_llm_config(
        provider=request.provider,
        api_key=request.api_key or "",
        api_base=request.api_base or "",
        model=request.model or ""
    )
    
    return {
        "code": 200,
        "message": f"LLM已切换到 {request.provider} 模式",
        "data": {
            "provider": request.provider,
            "use_llm": request.provider != "mock"
        }
    }


@app.get("/ai/config/status")
def get_config_status():
    """获取当前配置状态"""
    return {
        "code": 200,
        "data": {
            "use_llm": enhanced_ai_agent.use_llm,
            "provider": enhanced_ai_agent.llm.provider,
            "model": enhanced_ai_agent.llm.model
        }
    }


@app.post("/ai/emotion/analyze")
def analyze_emotion(message: str):
    """情绪分析接口"""
    analyzer = EmotionAnalyzer()
    result = analyzer.analyze(message)
    return {"code": 200, "data": result}


@app.post("/ai/context/clear/{user_id}")
def clear_context(user_id: int):
    """清除用户对话上下文"""
    enhanced_ai_agent.clear_context(user_id)
    return {"code": 200, "message": "上下文已清除"}


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "service": "EmoHealer AI Service v2.0"}


def start_server(host: str = "0.0.0.0", port: int = 8089):
    """启动AI服务"""
    print(f"启动 EmoHealer AI Service v2.0...")
    print(f"当前LLM模式: {enhanced_ai_agent.llm.provider}")
    print(f"LLM启用: {enhanced_ai_agent.use_llm}")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
