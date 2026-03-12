from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, Date, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50))
    avatar_url = Column(String(255))
    email = Column(String(100))
    phone = Column(String(20))
    bio = Column(Text)
    gender = Column(String(10), default="unknown")
    birthday = Column(Date)
    status = Column(Integer, default=1)
    role = Column(String(20), default="user")
    last_login = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ChatRecord(Base):
    __tablename__ = "chat_record"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    user_message = Column(Text, nullable=False)
    ai_reply = Column(Text)
    emotion_type = Column(String(20))
    emotion_score = Column(DECIMAL(5, 2))
    is_crisis = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

class EmotionLog(Base):
    __tablename__ = "emotion_log"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    emotion_type = Column(String(20), nullable=False)
    emotion_score = Column(DECIMAL(5, 2))
    confidence = Column(DECIMAL(5, 4))
    source = Column(String(20), default="text")
    trigger_context = Column(Text)
    context_tags = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

class HealingPlan(Base):
    __tablename__ = "healing_plan"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    plan_date = Column(Date, nullable=False)
    tasks = Column(JSON, nullable=False)
    completion_rate = Column(DECIMAL(5, 2), default=0)
    status = Column(String(20), default="pending")
    ai_summary = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class CrisisAlert(Base):
    __tablename__ = "crisis_alert"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    alert_level = Column(String(20), nullable=False)
    reason = Column(Text)
    keywords = Column(JSON)
    chat_record_id = Column(Integer)
    is_handled = Column(Boolean, default=False)
    handler_id = Column(Integer)
    handler_note = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    handled_at = Column(DateTime)

class PsychologicalAssessment(Base):
    __tablename__ = "psychological_assessment"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    assessment_type = Column(String(50), nullable=False)
    total_score = Column(Integer)
    level = Column(String(20))
    answers = Column(JSON)
    suggestions = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class ConsultationAppointment(Base):
    __tablename__ = "consultation_appointment"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    counselor_name = Column(String(50))
    counselor_id = Column(Integer)
    appointment_time = Column(DateTime, nullable=False)
    duration = Column(Integer, default=50)
    consultation_type = Column(String(20), default="video")
    status = Column(String(20), default="pending")
    ai_pre_report = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class UserToken(Base):
    __tablename__ = "user_token"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
