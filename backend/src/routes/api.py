from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, date
import hashlib
import secrets
from database import get_db
from src.models.models import User, ChatRecord, EmotionLog, HealingPlan, CrisisAlert, PsychologicalAssessment, ConsultationAppointment, UserToken
from src.services.ai_service import ai_service
from src.services.ai_agent import ai_agent
from src.services.enhanced_ai_agent import enhanced_ai_agent

router = APIRouter()

# ==================== 数据模型 ====================

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    nickname: Optional[str] = None
    email: Optional[str] = None

class TokenResponse(BaseModel):
    token: str
    user_id: int
    nickname: str
    expires_at: str

class ChatRequest(BaseModel):
    user_id: Optional[int] = None  # 可选，已登录用户不需要传
    message: str
    emotion: Optional[str] = None

    class Config:
        extra = "allow"  # 允许额外字段

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

class EmotionTrendRequest(BaseModel):
    user_id: int
    period: str = "month"  # week, month, year

class EmotionData(BaseModel):
    date: str
    overall: float
    anxiety: float
    happiness: float

# ==================== 工具函数 ====================

def hash_password(password: str) -> str:
    """密码加密"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return hash_password(plain_password) == hashed_password

def generate_token() -> str:
    """生成随机Token"""
    return secrets.token_urlsafe(32)

# ==================== 认证依赖 ====================

def get_token_from_header(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """从请求头中提取Token"""
    if not authorization:
        return None
    
    # 支持 "Bearer <token>" 格式
    if authorization.startswith("Bearer "):
        return authorization[7:]
    
    return authorization

def get_current_user(
    token: Optional[str] = Depends(get_token_from_header), 
    db: Session = Depends(get_db)
):
    """获取当前用户（依赖注入）"""
    if not token:
        raise HTTPException(status_code=401, detail="缺少Token")
    
    # 验证Token
    user_token = db.query(UserToken).filter(
        UserToken.token == token,
        UserToken.expires_at > datetime.now()
    ).first()
    
    if not user_token:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
    
    # 获取用户信息
    user = db.query(User).filter(User.id == user_token.user_id).first()
    if not user or user.status != 1:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    
    return user

# ==================== 需要认证的接口 ====================

@router.post("/chat/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发送消息，获取AI回复（使用增强版AI智能体）"""
    # 使用增强版AI智能体生成回复
    ai_result = await enhanced_ai_agent.chat(current_user.id, request.message, request.emotion)
    
    # 保存对话记录
    chat_record = ChatRecord(
        user_id=current_user.id,
        user_message=request.message,
        ai_reply=ai_result["reply"],
        emotion_type=ai_result["emotion"],
        emotion_score=ai_result.get("confidence", 0.8) * 100,
        is_crisis=ai_result["is_crisis"],
        created_at=datetime.now()
    )
    db.add(chat_record)
    
    # 保存情绪日志
    emotion_log = EmotionLog(
        user_id=current_user.id,
        emotion_type=ai_result["emotion"],
        emotion_score=ai_result.get("confidence", 0.8) * 100,
        confidence=ai_result.get("confidence", 0.8),
        source="text",
        trigger_context=request.message[:100],
        created_at=datetime.now()
    )
    db.add(emotion_log)
    
    # 如果是危机，生成预警
    if ai_result["is_crisis"]:
        crisis_level = ai_result.get("crisis_level", "high")
        crisis_alert = CrisisAlert(
            user_id=current_user.id,
            alert_level=crisis_level,
            reason=f"检测到危机关键词: {request.message[:50]}",
            chat_record_id=chat_record.id,
            is_handled=False,
            created_at=datetime.now()
        )
        db.add(crisis_alert)
    
    db.commit()
    db.refresh(chat_record)
    
    return ChatResponse(**ai_result)

# ==================== 用户认证接口 ====================

@router.post("/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    # 使用最简单的SQL查询
    result = db.execute(text("SELECT id, password_hash, nickname, status FROM user WHERE username = :username"), {"username": request.username})
    user = result.fetchone()
    
    if not user:
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    
    # 验证密码
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    
    # 检查用户状态
    if user.status != 1:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    
    # 生成Token
    token = generate_token()
    expires_at = datetime.now() + timedelta(days=7)
    
    # 插入Token
    db.execute(
        text("INSERT INTO user_token (user_id, token, expires_at) VALUES (:user_id, :token, :expires_at)"),
        {"user_id": user.id, "token": token, "expires_at": expires_at}
    )
    
    # 更新最后登录时间
    db.execute(text("UPDATE user SET last_login = NOW() WHERE id = :id"), {"id": user.id})
    
    db.commit()
    
    return {
        "code": 200,
        "message": "登录成功",
        "token": token,
        "user_id": user.id,
        "nickname": user.nickname or request.username,
        "expires_at": expires_at.isoformat()
    }

@router.post("/auth/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    result = db.execute(text("SELECT id FROM user WHERE username = :username"), {"username": request.username})
    if result.fetchone():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    if request.email:
        result = db.execute(text("SELECT id FROM user WHERE email = :email"), {"email": request.email})
        if result.fetchone():
            raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 创建用户
    nickname = request.nickname or request.username
    db.execute(
        text("INSERT INTO user (username, password_hash, nickname, email, status, role) VALUES (:username, :password_hash, :nickname, :email, :status, :role)"),
        {"username": request.username, "password_hash": hash_password(request.password), "nickname": nickname, "email": request.email, "status": 1, "role": "user"}
    )
    db.commit()
    
    # 获取用户ID
    result = db.execute(text("SELECT LAST_INSERT_ID()"))
    user_id = result.fetchone()[0]
    
    return {
        "code": 200,
        "message": "注册成功",
        "data": {
            "user_id": user_id,
            "username": request.username,
            "nickname": nickname
        }
    }

@router.post("/auth/logout")
async def logout(token: str, db: Session = Depends(get_db)):
    """用户登出"""
    # 删除Token
    user_token = db.query(UserToken).filter(UserToken.token == token).first()
    if user_token:
        db.delete(user_token)
        db.commit()
    
    return {"code": 200, "message": "登出成功"}

@router.get("/auth/verify")
async def verify_token(token: str, db: Session = Depends(get_db)):
    """验证Token"""
    user_token = db.query(UserToken).filter(
        UserToken.token == token,
        UserToken.expires_at > datetime.now()
    ).first()
    
    if not user_token:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
    
    user = db.query(User).filter(User.id == user_token.user_id).first()
    if not user or user.status != 1:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    
    return {
        "code": 200,
        "data": {
            "user_id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "role": user.role
        }
    }

# ==================== 对话接口 ====================

# 注意：chat/send 路由已合并到上方的带认证版本
    
    # 保存对话记录
    chat_record = ChatRecord(
        user_id=request.user_id,
        user_message=request.message,
        ai_reply=ai_result["reply"],
        emotion_type=ai_result["emotion"],
        emotion_score=ai_result.get("confidence", 0.8) * 100,
        is_crisis=ai_result["is_crisis"],
        created_at=datetime.now()
    )
    db.add(chat_record)
    
    # 保存情绪日志
    emotion_log = EmotionLog(
        user_id=request.user_id,
        emotion_type=ai_result["emotion"],
        emotion_score=ai_result.get("confidence", 0.8) * 100,
        confidence=ai_result.get("confidence", 0.8),
        source="text",
        trigger_context=request.message[:100],
        created_at=datetime.now()
    )
    db.add(emotion_log)
    
    # 如果是危机，生成预警
    if ai_result["is_crisis"]:
        crisis_level = ai_result.get("crisis_level", "high")
        crisis_alert = CrisisAlert(
            user_id=request.user_id,
            alert_level=crisis_level,
            reason=f"检测到危机关键词: {request.message[:50]}",
            chat_record_id=chat_record.id,
            is_handled=False,
            created_at=datetime.now()
        )
        db.add(crisis_alert)
    
    db.commit()
    db.refresh(chat_record)
    
    return ChatResponse(**ai_result)

@router.get("/chat/history")
def get_chat_history(
    limit: int = 20, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的对话历史"""
    records = db.query(ChatRecord).filter(
        ChatRecord.user_id == current_user.id
    ).order_by(ChatRecord.created_at.desc()).limit(limit).all()
    
    return {
        "code": 200,
        "data": [
            {
                "id": r.id,
                "user_message": r.user_message,
                "ai_reply": r.ai_reply,
                "emotion_type": r.emotion_type,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]
    }

# ==================== 情绪数据接口 ====================

@router.post("/emotion/trend")
def get_emotion_trend(request: EmotionTrendRequest, db: Session = Depends(get_db)):
    """获取情绪趋势数据"""
    # 计算日期范围
    if request.period == "week":
        days = 7
    elif request.period == "year":
        days = 365
    else:
        days = 30
    
    start_date = datetime.now() - timedelta(days=days)
    
    # 查询情绪日志
    logs = db.query(EmotionLog).filter(
        EmotionLog.user_id == request.user_id,
        EmotionLog.created_at >= start_date
    ).order_by(EmotionLog.created_at).all()
    
    # 生成数据点
    emotion_data = []
    emotion_map = {
        # 英文
        'happy': {'overall': 80, 'happiness': 90, 'anxiety': 20},
        'sad': {'overall': 40, 'happiness': 30, 'anxiety': 60},
        'anxious': {'overall': 50, 'happiness': 40, 'anxiety': 80},
        'angry': {'overall': 45, 'happiness': 30, 'anxiety': 70},
        'tired': {'overall': 50, 'happiness': 40, 'anxiety': 40},
        'neutral': {'overall': 65, 'happiness': 60, 'anxiety': 30},
        # 中文
        '开心': {'overall': 80, 'happiness': 90, 'anxiety': 20},
        '难过': {'overall': 40, 'happiness': 30, 'anxiety': 60},
        '焦虑': {'overall': 50, 'happiness': 40, 'anxiety': 80},
        '愤怒': {'overall': 45, 'happiness': 30, 'anxiety': 70},
        '疲惫': {'overall': 50, 'happiness': 40, 'anxiety': 40},
    }
    
    if request.period == "year":
        # 按月汇总
        month_data = {}
        for log in logs:
            month_key = log.created_at.strftime("%Y-%m") if log.created_at else "unknown"
            if month_key not in month_data:
                month_data[month_key] = {'scores': [], 'anxiety': [], 'happiness': []}
            
            scores = emotion_map.get(log.emotion_type, emotion_map['neutral'])
            month_data[month_key]['scores'].append(scores['overall'])
            month_data[month_key]['anxiety'].append(scores['anxiety'])
            month_data[month_key]['happiness'].append(scores['happiness'])
        
        for month, data in sorted(month_data.items()):
            emotion_data.append({
                "date": month + "月",
                "overall": round(sum(data['scores']) / len(data['scores']), 1),
                "anxiety": round(sum(data['anxiety']) / len(data['anxiety']), 1),
                "happiness": round(sum(data['happiness']) / len(data['happiness']), 1)
            })
    else:
        # 按天汇总
        day_data = {}
        for log in logs:
            day_key = log.created_at.strftime("%m-%d") if log.created_at else "unknown"
            if day_key not in day_data:
                day_data[day_key] = {'scores': [], 'anxiety': [], 'happiness': []}
            
            scores = emotion_map.get(log.emotion_type, emotion_map['neutral'])
            day_data[day_key]['scores'].append(scores['overall'])
            day_data[day_key]['anxiety'].append(scores['anxiety'])
            day_data[day_key]['happiness'].append(scores['happiness'])
        
        for day, data in sorted(day_data.items()):
            emotion_data.append({
                "date": day,
                "overall": round(sum(data['scores']) / len(data['scores']), 1),
                "anxiety": round(sum(data['anxiety']) / len(data['anxiety']), 1),
                "happiness": round(sum(data['happiness']) / len(data['happiness']), 1)
            })
    
    return {
        "code": 200,
        "data": emotion_data
    }

# ==================== 用户接口 ====================

@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    """获取用户列表"""
    users = db.query(User).all()
    return {
        "code": 200,
        "data": [
            {
                "id": u.id,
                "username": u.username,
                "nickname": u.nickname,
                "avatar_url": u.avatar_url,
                "role": u.role
            }
            for u in users
        ]
    }

@router.get("/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "code": 200,
        "data": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }

# ==================== 疗愈方案接口 ====================

@router.get("/healing-plan/{user_id}")
def get_healing_plan(user_id: int, db: Session = Depends(get_db)):
    """获取今日疗愈方案"""
    today = datetime.now().date()
    plan = db.query(HealingPlan).filter(
        HealingPlan.user_id == user_id,
        HealingPlan.plan_date == today
    ).first()
    
    if not plan:
        # 使用AI智能体生成方案
        ai_plan = ai_agent.generate_healing_plan(user_id)
        return {"code": 200, "data": ai_plan}
    
    return {
        "code": 200,
        "data": {
            "id": plan.id,
            "tasks": plan.tasks,
            "completion_rate": float(plan.completion_rate) if plan.completion_rate else 0,
            "status": plan.status,
            "ai_summary": plan.ai_summary
        }
    }

@router.post("/healing-plan/generate")
def generate_healing_plan(request: dict, db: Session = Depends(get_db)):
    """生成新的疗愈方案（使用AI智能体）"""
    user_id = request.get("user_id", 1)
    emotion = request.get("emotion", None)
    
    # 使用AI智能体生成方案
    ai_plan = ai_agent.generate_healing_plan(user_id, emotion)
    
    # 保存到数据库
    today = datetime.now().date()
    plan = HealingPlan(
        user_id=user_id,
        plan_date=today,
        tasks=ai_plan.get("tasks", {}),
        completion_rate=0,
        status="pending",
        ai_summary=ai_plan.get("theme", ""),
        created_at=datetime.now()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return {
        "code": 200,
        "message": "疗愈方案生成成功",
        "data": ai_plan
    }

# ==================== 心理测评接口 ====================

class AssessmentRequest(BaseModel):
    user_id: int
    assessment_type: str
    answers: List[int]
    level: str
    suggestions: str = ""

@router.post("/assessment/submit")
def submit_assessment(request: AssessmentRequest, db: Session = Depends(get_db)):
    """提交心理测评结果"""
    total_score = sum(request.answers)
    
    assessment = PsychologicalAssessment(
        user_id=request.user_id,
        assessment_type=request.assessment_type,
        total_score=total_score,
        level=request.level,
        answers=request.answers,
        suggestions=request.suggestions,
        created_at=datetime.now()
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    return {
        "code": 200,
        "message": "测评提交成功",
        "data": {
            "id": assessment.id,
            "total_score": total_score,
            "level": request.level
        }
    }

@router.get("/assessment/{user_id}")
def get_assessments(user_id: int, db: Session = Depends(get_db)):
    """获取用户的测评历史"""
    assessments = db.query(PsychologicalAssessment).filter(
        PsychologicalAssessment.user_id == user_id
    ).order_by(PsychologicalAssessment.created_at.desc()).limit(20).all()
    
    return {
        "code": 200,
        "data": [
            {
                "id": a.id,
                "assessment_type": a.assessment_type,
                "total_score": a.total_score,
                "level": a.level,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in assessments
        ]
    }

# ==================== 预约咨询接口 ====================

class AppointmentRequest(BaseModel):
    user_id: int
    name: str
    phone: str
    consultation_type: str
    appointment_date: str
    description: str = ""

@router.post("/appointment/submit")
def submit_appointment(request: AppointmentRequest, db: Session = Depends(get_db)):
    """提交预约咨询"""
    appointment_time = datetime.strptime(request.appointment_date, "%Y-%m-%d")
    
    appointment = ConsultationAppointment(
        user_id=request.user_id,
        counselor_name="待分配",
        appointment_time=appointment_time,
        consultation_type=request.consultation_type,
        status="pending",
        notes=request.description,
        created_at=datetime.now()
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    
    return {
        "code": 200,
        "message": "预约提交成功",
        "data": {
            "id": appointment.id,
            "status": "pending",
            "appointment_time": appointment_time.isoformat()
        }
    }

@router.get("/appointment/{user_id}")
def get_appointments(user_id: int, db: Session = Depends(get_db)):
    """获取用户的预约列表"""
    appointments = db.query(ConsultationAppointment).filter(
        ConsultationAppointment.user_id == user_id
    ).order_by(ConsultationAppointment.appointment_time.desc()).limit(20).all()
    
    return {
        "code": 200,
        "data": [
            {
                "id": a.id,
                "counselor_name": a.counselor_name,
                "appointment_time": a.appointment_time.isoformat() if a.appointment_time else None,
                "consultation_type": a.consultation_type,
                "status": a.status
            }
            for a in appointments
        ]
    }

# ==================== 统计数据接口 ====================

@router.get("/stats/{user_id}")
def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    """获取用户统计数据"""
    # 对话次数
    chat_count = db.query(ChatRecord).filter(
        ChatRecord.user_id == user_id
    ).count()
    
    # 情绪记录数
    emotion_count = db.query(EmotionLog).filter(
        EmotionLog.user_id == user_id
    ).count()
    
    # 测评次数
    assessment_count = db.query(PsychologicalAssessment).filter(
        PsychologicalAssessment.user_id == user_id
    ).count()
    
    # 预约次数
    appointment_count = db.query(ConsultationAppointment).filter(
        ConsultationAppointment.user_id == user_id
    ).count()
    
    # 最近7天的情绪分布
    week_ago = datetime.now() - timedelta(days=7)
    recent_emotions = db.query(EmotionLog).filter(
        EmotionLog.user_id == user_id,
        EmotionLog.created_at >= week_ago
    ).all()
    
    emotion_distribution = {}
    for e in recent_emotions:
        emotion_distribution[e.emotion_type] = emotion_distribution.get(e.emotion_type, 0) + 1
    
    # 使用天数
    first_record = db.query(EmotionLog).filter(
        EmotionLog.user_id == user_id
    ).order_by(EmotionLog.created_at.asc()).first()
    
    if first_record and first_record.created_at:
        days = (datetime.now() - first_record.created_at).days + 1
    else:
        days = 1
    
    return {
        "code": 200,
        "data": {
            "chat_count": chat_count,
            "emotion_count": emotion_count,
            "assessment_count": assessment_count,
            "appointment_count": appointment_count,
            "usage_days": days,
            "emotion_distribution": emotion_distribution
        }
    }

# ==================== 疗愈方案接口 ====================

@router.get("/plans/{user_id}")
def get_healing_plans(user_id: int, db: Session = Depends(get_db)):
    """获取用户的疗愈方案列表"""
    plans = db.query(HealingPlan).filter(
        HealingPlan.user_id == user_id
    ).order_by(HealingPlan.plan_date.desc()).limit(30).all()
    
    return {
        "code": 200,
        "data": [
            {
                "id": p.id,
                "plan_date": p.plan_date.isoformat() if p.plan_date else None,
                "tasks": p.tasks,
                "completion_rate": float(p.completion_rate) if p.completion_rate else 0,
                "status": p.status,
                "ai_summary": p.ai_summary
            }
            for p in plans
        ]
    }

# ==================== AI配置接口 ====================

class LLMConfigRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_secret: Optional[str] = None
    model: Optional[str] = None


@router.post("/ai/config/llm")
def config_llm(request: LLMConfigRequest):
    """配置LLM（动态切换AI模式）"""
    from src.services.enhanced_ai_agent import EnhancedLLMWrapper

    params = {
        "provider": request.provider,
        "api_key": request.api_key or "",
        "api_base": request.api_base or "",
        "model": request.model or ""
    }
    if request.api_secret:
        params["api_secret"] = request.api_secret

    # 更新增强版AI智能体的LLM配置
    enhanced_ai_agent.set_llm_config(**params)

    return {
        "code": 200,
        "message": f"LLM已切换到 {request.provider} 模式",
        "data": {
            "provider": request.provider,
            "use_llm": request.provider != "mock"
        }
    }


@router.get("/ai/config/status")
def get_ai_status():
    """获取AI配置状态"""
    return {
        "code": 200,
        "data": {
            "use_llm": enhanced_ai_agent.use_llm,
            "provider": enhanced_ai_agent.llm.provider,
            "model": enhanced_ai_agent.llm.model
        }
    }


@router.get("/ai/personas")
def get_personas():
    """获取可用的智能体角色"""
    from src.services.enhanced_ai_agent import PersonaManager

    personas = {}
    for role, config in PersonaManager.PERSONAS.items():
        personas[role] = {
            "name": config.name,
            "description": config.description,
            "traits": config.traits,
            "response_style": config.response_style
        }
    return {"code": 200, "data": personas}


# ==================== 健康检查 ====================

@router.get("/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "message": "EmoHealer API is running"}
