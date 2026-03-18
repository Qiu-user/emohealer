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
    # 使用增强版AI智能体生成回复（传递db session以加载历史记录）
    ai_result = await enhanced_ai_agent.chat(current_user.id, request.message, request.emotion, db)
    
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

    # 记录Token消耗（如果有）
    if ai_result.get("token_usage"):
        try:
            from src.models.models import TokenUsage
            token_info = ai_result["token_usage"]
            token_usage = TokenUsage(
                user_id=current_user.id,
                model_provider=token_info.get("provider", "mock"),
                model_name=token_info.get("model", "mock"),
                prompt_tokens=token_info.get("prompt_tokens", 0),
                completion_tokens=token_info.get("completion_tokens", 0),
                total_tokens=token_info.get("total_tokens", 0),
                cost=token_info.get("cost", 0),
                conversation_type="chat",
                response_time=token_info.get("response_time", 0),
                created_at=datetime.now()
            )
            db.add(token_usage)
        except Exception as e:
            print(f"记录Token消耗失败: {e}")

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


# ==================== 多模态情绪识别 ====================

class EmotionAnalyzeRequest(BaseModel):
    text: Optional[str] = None
    audio_data: Optional[str] = None
    image_data: Optional[str] = None
    user_id: Optional[int] = None


@router.post("/emotion/analyze")
async def analyze_emotion(
    request: EmotionAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """多模态情绪分析接口"""
    result = {
        "emotion": "neutral",
        "confidence": 0.5,
        "emotions": {
            "happy": 0.1, "sad": 0.1, "angry": 0.1,
            "anxious": 0.1, "fear": 0.1, "neutral": 0.5
        }
    }

    if request.text:
        text_emotion = analyze_text_emotion(request.text)
        result.update(text_emotion)

    return {"code": 200, "data": result}


def analyze_text_emotion(text: str) -> dict:
    """基于关键词的文本情绪分析"""
    text_lower = text.lower()
    
    emotion_keywords = {
        "happy": ["开心", "高兴", "快乐", "愉快", "喜悦", "happy", "joy"],
        "sad": ["难过", "伤心", "痛苦", "悲伤", "沮丧", "sad", "cry"],
        "angry": ["生气", "愤怒", "恼火", "气愤", "angry", "mad"],
        "anxious": ["焦虑", "担心", "紧张", "不安", "压力", "anxious", "worry"],
        "fear": ["害怕", "恐惧", "担心", "惊恐", "fear", "scared"],
    }

    emotion_scores = {}
    for emotion, keywords in emotion_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        emotion_scores[emotion] = score

    total = sum(emotion_scores.values())
    if total > 0:
        emotions = {k: round(v / total, 2) for k, v in emotion_scores.items()}
    else:
        emotions = {k: 0.1 for k in emotion_keywords.keys()}
        emotions["neutral"] = 0.5

    max_emotion = max(emotions, key=emotions.get)
    
    return {
        "emotion": max_emotion,
        "confidence": round(emotions[max_emotion], 2),
        "emotions": emotions
    }


@router.post("/emotion/voice/analyze")
async def analyze_voice_emotion(
    audio_data: str,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """语音情绪分析接口"""
    return {
        "code": 200,
        "data": {
            "emotion": "neutral",
            "confidence": 0.65,
            "emotions": {
                "happy": 0.15, "sad": 0.1, "angry": 0.05,
                "anxious": 0.1, "fear": 0.05, "neutral": 0.55
            }
        }
    }


@router.post("/emotion/face/analyze")
async def analyze_face_emotion(
    image_data: str,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """表情情绪分析接口"""
    return {
        "code": 200,
        "data": {
            "emotion": "happy",
            "confidence": 0.78,
            "emotions": {
                "happy": 0.78, "sad": 0.05, "angry": 0.02,
                "surprise": 0.1, "fear": 0.02, "neutral": 0.03
            }
        }
    }


# ==================== 情绪报告接口 ====================

@router.get("/emotion/report/{user_id}")
def get_emotion_report(
    user_id: int,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """获取用户情绪报告"""
    from datetime import datetime, timedelta
    
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 获取对话记录
    chat_records = db.query(ChatRecord).filter(
        ChatRecord.user_id == user_id,
        ChatRecord.created_at >= start_date
    ).order_by(ChatRecord.created_at.desc()).all()
    
    # 获取情绪日志
    emotion_logs = db.query(EmotionLog).filter(
        EmotionLog.user_id == user_id,
        EmotionLog.created_at >= start_date
    ).all()
    
    # 统计情绪分布
    emotion_distribution = {}
    emotion_scores = []
    crisis_count = 0
    
    for record in chat_records:
        if record.emotion_type:
            emotion_distribution[record.emotion_type] = emotion_distribution.get(record.emotion_type, 0) + 1
        if record.emotion_score:
            emotion_scores.append(float(record.emotion_score))
        if record.is_crisis:
            crisis_count += 1
    
    for log in emotion_logs:
        if log.emotion_type:
            emotion_distribution[log.emotion_type] = emotion_distribution.get(log.emotion_type, 0) + 1
        if log.emotion_score:
            emotion_scores.append(float(log.emotion_score))
    
    # 计算平均情绪得分
    avg_emotion_score = sum(emotion_scores) / len(emotion_scores) if emotion_scores else 50
    
    # 每日情绪趋势
    daily_emotions = {}
    for record in chat_records:
        date_key = record.created_at.strftime("%Y-%m-%d")
        if date_key not in daily_emotions:
            daily_emotions[date_key] = {"happy": 0, "sad": 0, "anxious": 0, "angry": 0, "neutral": 0, "tired": 0}
        if record.emotion_type:
            daily_emotions[date_key][record.emotion_type] = daily_emotions[date_key].get(record.emotion_type, 0) + 1
    
    # 生成AI分析报告
    dominant_emotion = max(emotion_distribution, key=emotion_distribution.get) if emotion_distribution else "neutral"
    
    # 构建报告
    report = {
        "user_id": user_id,
        "report_period": f"最近{days}天",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "statistics": {
            "total_conversations": len(chat_records),
            "total_emotion_logs": len(emotion_logs),
            "crisis_alerts": crisis_count,
            "avg_emotion_score": round(avg_emotion_score, 2)
        },
        "emotion_distribution": emotion_distribution,
        "daily_trends": daily_emotions,
        "dominant_emotion": dominant_emotion,
        "analysis": generate_emotion_analysis(dominant_emotion, emotion_distribution, crisis_count, len(chat_records))
    }
    
    return {
        "code": 200,
        "data": report
    }


def generate_emotion_analysis(dominant_emotion: str, distribution: dict, crisis_count: int, total_chats: int) -> str:
    """生成情绪分析文字报告"""
    emotion_descriptions = {
        "happy": "积极乐观",
        "sad": "情绪低落",
        "anxious": "焦虑不安",
        "angry": "愤怒不满",
        "tired": "疲惫倦怠",
        "neutral": "心态平和",
        "fear": "恐惧担忧"
    }
    
    desc = emotion_descriptions.get(dominant_emotion, "心态平和")
    
    analysis_parts = []
    analysis_parts.append(f"您近期的主要情绪状态为【{desc}】")
    
    if total_chats > 0:
        analysis_parts.append(f"共进行了{total_chats}次对话交流")
    
    if crisis_count > 0:
        analysis_parts.append(f"检测到{crisis_count}次危机预警信号，建议关注自身安全")
        analysis_parts.append("如感到持续低落或有无助感，请考虑寻求专业心理咨询帮助")
    else:
        analysis_parts.append("未检测到明显的危机信号")
    
    # 根据情绪给出建议
    if dominant_emotion == "sad":
        analysis_parts.append("建议：可以尝试写情绪日记记录心情，或者进行适度的运动来改善情绪")
    elif dominant_emotion == "anxious":
        analysis_parts.append("建议：深呼吸练习和正念冥想可以帮助缓解焦虑")
    elif dominant_emotion == "happy":
        analysis_parts.append("建议：继续保持积极心态，您的情绪状态很好")
    elif dominant_emotion == "tired":
        analysis_parts.append("建议：注意休息，保证充足睡眠，适当放松身心")
    
    return "；".join(analysis_parts) + "。"


@router.get("/emotion/trend/{user_id}")
def get_emotion_trend(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """获取用户情绪趋势数据"""
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 获取指定时间范围内的情绪数据
    emotion_logs = db.query(EmotionLog).filter(
        EmotionLog.user_id == user_id,
        EmotionLog.created_at >= start_date
    ).order_by(EmotionLog.created_at.asc()).all()
    
    # 按日期分组统计
    daily_data = {}
    for log in emotion_logs:
        date_key = log.created_at.strftime("%Y-%m-%d")
        if date_key not in daily_data:
            daily_data[date_key] = {"scores": [], "emotions": {}}
        
        if log.emotion_score:
            daily_data[date_key]["scores"].append(float(log.emotion_score))
        
        if log.emotion_type:
            daily_data[date_key]["emotions"][log.emotion_type] = daily_data[date_key]["emotions"].get(log.emotion_type, 0) + 1
    
    # 计算每日平均得分和主导情绪
    trend_data = []
    for date_key in sorted(daily_data.keys()):
        data = daily_data[date_key]
        avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 50
        dominant = max(data["emotions"], key=data["emotions"].get) if data["emotions"] else "neutral"
        
        trend_data.append({
            "date": date_key,
            "avg_score": round(avg_score, 2),
            "dominant_emotion": dominant,
            "emotion_count": sum(data["emotions"].values())
        })
    
    return {
        "code": 200,
        "data": {
            "user_id": user_id,
            "period_days": days,
            "trend": trend_data
        }
    }


@router.get("/chat/history/{user_id}")
def get_chat_history(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """获取用户对话历史"""
    records = db.query(ChatRecord).filter(
        ChatRecord.user_id == user_id
    ).order_by(ChatRecord.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "code": 200,
        "data": [
            {
                "id": r.id,
                "user_message": r.user_message,
                "ai_reply": r.ai_reply,
                "emotion_type": r.emotion_type,
                "emotion_score": float(r.emotion_score) if r.emotion_score else None,
                "is_crisis": bool(r.is_crisis),
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None
            }
            for r in records
        ]
    }

# ==================== 运维管理接口 ====================

@router.get("/admin/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """数据驾驶舱 - 获取系统整体统计数据"""
    from datetime import datetime, timedelta

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    # 用户统计
    total_users = db.query(User).count()
    active_users_today = db.query(User).filter(User.last_login >= today_start).count()
    active_users_week = db.query(User).filter(User.last_login >= week_start).count()

    # 对话统计
    total_chats = db.query(ChatRecord).count()
    chats_today = db.query(ChatRecord).filter(ChatRecord.created_at >= today_start).count()
    chats_week = db.query(ChatRecord).filter(ChatRecord.created_at >= week_start).count()

    # 情绪记录统计
    total_emotions = db.query(EmotionLog).count()
    emotions_today = db.query(EmotionLog).filter(EmotionLog.created_at >= today_start).count()

    # 危机预警统计
    total_crisis = db.query(CrisisAlert).count()
    crisis_today = db.query(CrisisAlert).filter(CrisisAlert.created_at >= today_start).count()
    crisis_unhandled = db.query(CrisisAlert).filter(CrisisAlert.is_handled == False).count()

    # 测评统计
    total_assessments = db.query(PsychologicalAssessment).count()

    return {
        "code": 200,
        "data": {
            "users": {
                "total": total_users,
                "active_today": active_users_today,
                "active_week": active_users_week
            },
            "chats": {
                "total": total_chats,
                "today": chats_today,
                "week": chats_week
            },
            "emotions": {
                "total": total_emotions,
                "today": emotions_today
            },
            "crisis": {
                "total": total_crisis,
                "today": crisis_today,
                "unhandled": crisis_unhandled
            },
            "assessments": {
                "total": total_assessments
            },
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
        }
    }


@router.get("/admin/dashboard/trend")
def get_dashboard_trend(days: int = 7, db: Session = Depends(get_db)):
    """数据驾驶舱 - 获取趋势数据"""
    from datetime import datetime, timedelta

    now = datetime.now()
    start_date = now - timedelta(days=days)

    # 按日期统计
    daily_data = []
    for i in range(days):
        date = (now - timedelta(days=days - 1 - i)).date()
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())

        chats = db.query(ChatRecord).filter(
            ChatRecord.created_at >= date_start,
            ChatRecord.created_at <= date_end
        ).count()

        users = db.query(User).filter(
            User.last_login >= date_start,
            User.last_login <= date_end
        ).count()

        emotions = db.query(EmotionLog).filter(
            EmotionLog.created_at >= date_start,
            EmotionLog.created_at <= date_end
        ).count()

        daily_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "chats": chats,
            "users": users,
            "emotions": emotions
        })

    return {
        "code": 200,
        "data": daily_data
    }


@router.get("/admin/users")
def get_admin_users(
    page: int = 1,
    page_size: int = 20,
    status: int = None,
    db: Session = Depends(get_db)):
    """数据管理 - 用户列表"""
    query = db.query(User)

    if status is not None:
        query = query.filter(User.status == status)

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page-1) * page_size).limit(page_size).all()

    return {
        "code": 200,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": [
                {
                    "id": u.id,
                    "username": u.username,
                    "nickname": u.nickname,
                    "email": u.email,
                    "status": u.status,
                    "role": u.role,
                    "last_login": u.last_login.strftime("%Y-%m-%d %H:%M:%S") if u.last_login else None,
                    "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else None
                }
                for u in users
            ]
        }
    }


@router.post("/admin/user/{user_id}/status")
def update_user_status(user_id: int, status: int, db: Session = Depends(get_db)):
    """数据管理 - 修改用户状态"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"code": 404, "message": "用户不存在"}

    user.status = status
    db.commit()

    return {"code": 200, "message": "状态更新成功"}


@router.get("/admin/chats")
def get_admin_chats(
    user_id: int = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)):
    """数据管理 - 对话记录"""
    query = db.query(ChatRecord)

    if user_id:
        query = query.filter(ChatRecord.user_id == user_id)

    total = query.count()
    chats = query.order_by(ChatRecord.created_at.desc()).offset((page-1) * page_size).limit(page_size).all()

    return {
        "code": 200,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": [
                {
                    "id": c.id,
                    "user_id": c.user_id,
                    "user_message": c.user_message[:100] + "..." if len(c.user_message) > 100 else c.user_message,
                    "ai_reply": c.ai_reply[:100] + "..." if c.ai_reply and len(c.ai_reply) > 100 else c.ai_reply,
                    "emotion_type": c.emotion_type,
                    "is_crisis": bool(c.is_crisis),
                    "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else None
                }
                for c in chats
            ]
        }
    }


@router.get("/admin/crisis")
def get_admin_crisis(
    is_handled: bool = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)):
    """运维报表 - 危机预警记录"""
    query = db.query(CrisisAlert)

    if is_handled is not None:
        query = query.filter(CrisisAlert.is_handled == is_handled)

    total = query.count()
    alerts = query.order_by(CrisisAlert.created_at.desc()).offset((page-1) * page_size).limit(page_size).all()

    return {
        "code": 200,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": [
                {
                    "id": a.id,
                    "user_id": a.user_id,
                    "alert_level": a.alert_level,
                    "reason": a.reason,
                    "keywords": a.keywords,
                    "is_handled": a.is_handled,
                    "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else None
                }
                for a in alerts
            ]
        }
    }


@router.post("/admin/crisis/{alert_id}/handle")
def handle_crisis(alert_id: int, note: str = "", db: Session = Depends(get_db)):
    """运维报表 - 处理危机预警"""
    alert = db.query(CrisisAlert).filter(CrisisAlert.id == alert_id).first()
    if not alert:
        return {"code": 404, "message": "预警不存在"}

    alert.is_handled = True
    alert.handler_note = note
    alert.handled_at = datetime.now()
    db.commit()

    return {"code": 200, "message": "处理成功"}


@router.get("/admin/token/usage")
def get_token_usage(
    provider: str = None,
    days: int = 7,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)):
    """Token消耗报表 - Token使用统计"""
    from datetime import datetime, timedelta

    start_date = datetime.now() - timedelta(days=days)

    # 尝试导入TokenUsage模型
    try:
        from src.models.models import TokenUsage

        query = db.query(TokenUsage).filter(TokenUsage.created_at >= start_date)

        if provider:
            query = query.filter(TokenUsage.model_provider == provider)

        total = query.count()
        usage_records = query.order_by(TokenUsage.created_at.desc()).offset((page-1) * page_size).limit(page_size).all()

        # 按提供商汇总
        summary_query = db.query(
            TokenUsage.model_provider,
            db.func.sum(TokenUsage.total_tokens).label("total_tokens"),
            db.func.sum(TokenUsage.cost).label("total_cost"),
            db.func.count(TokenUsage.id).label("request_count")
        ).filter(TokenUsage.created_at >= start_date)

        if provider:
            summary_query = summary_query.filter(TokenUsage.model_provider == provider)

        summary = summary_query.group_by(TokenUsage.model_provider).all()

        return {
            "code": 200,
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "summary": [
                    {
                        "provider": s.model_provider,
                        "total_tokens": int(s.total_tokens or 0),
                        "total_cost": float(s.total_cost or 0),
                        "request_count": s.request_count
                    }
                    for s in summary
                ],
                "list": [
                    {
                        "id": u.id,
                        "user_id": u.user_id,
                        "provider": u.model_provider,
                        "model": u.model_name,
                        "prompt_tokens": u.prompt_tokens,
                        "completion_tokens": u.completion_tokens,
                        "total_tokens": u.total_tokens,
                        "cost": float(u.cost),
                        "conversation_type": u.conversation_type,
                        "response_time": u.response_time,
                        "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else None
                    }
                    for u in usage_records
                ]
            }
        }
    except Exception as e:
        # 如果表不存在，返回空数据
        return {
            "code": 200,
            "data": {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "summary": [],
                "list": [],
                "message": "Token记录表未初始化"
            }
        }


@router.get("/admin/token/summary")
def get_token_summary(days: int = 30, db: Session = Depends(get_db)):
    """Token消耗报表 - 汇总统计"""
    from datetime import datetime, timedelta

    start_date = datetime.now() - timedelta(days=days)

    try:
        from src.models.models import TokenUsage
        from sqlalchemy import func

        # 按日期统计
        daily_usage = db.query(
            func.date(TokenUsage.created_at).label("date"),
            func.sum(TokenUsage.total_tokens).label("tokens"),
            func.sum(TokenUsage.cost).label("cost"),
            func.count(TokenUsage.id).label("count")
        ).filter(TokenUsage.created_at >= start_date).group_by(func.date(TokenUsage.created_at)).all()

        # 总计
        total = db.query(
            func.sum(TokenUsage.total_tokens).label("total_tokens"),
            func.sum(TokenUsage.cost).label("total_cost"),
            func.count(TokenUsage.id).label("total_requests")
        ).filter(TokenUsage.created_at >= start_date).first()

        return {
            "code": 200,
            "data": {
                "period_days": days,
                "total_tokens": int(total.total_tokens or 0),
                "total_cost": float(total.total_cost or 0),
                "total_requests": total.total_requests or 0,
                "daily": [
                    {
                        "date": d.date.strftime("%Y-%m-%d") if d.date else "",
                        "tokens": int(d.tokens or 0),
                        "cost": float(d.cost or 0),
                        "count": d.count
                    }
                    for d in daily_usage
                ]
            }
        }
    except Exception as e:
        return {
            "code": 200,
            "data": {
                "period_days": days,
                "total_tokens": 0,
                "total_cost": 0,
                "total_requests": 0,
                "daily": [],
                "message": str(e)
            }
        }


@router.get("/admin/logs")
def get_operation_logs(
    operation_type: str = None,
    user_id: int = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)):
    """运维报表 - 操作日志"""
    try:
        from src.models.models import OperationLog

        query = db.query(OperationLog)

        if operation_type:
            query = query.filter(OperationLog.operation_type == operation_type)
        if user_id:
            query = query.filter(OperationLog.user_id == user_id)

        total = query.count()
        logs = query.order_by(OperationLog.created_at.desc()).offset((page-1) * page_size).limit(page_size).all()

        return {
            "code": 200,
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "list": [
                    {
                        "id": l.id,
                        "user_id": l.user_id,
                        "username": l.username,
                        "operation_type": l.operation_type,
                        "resource_type": l.resource_type,
                        "resource_id": l.resource_id,
                        "operation_detail": l.operation_detail,
                        "ip_address": l.ip_address,
                        "created_at": l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else None
                    }
                    for l in logs
                ]
            }
        }
    except Exception as e:
        return {
            "code": 200,
            "data": {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "list": []
            }
        }



