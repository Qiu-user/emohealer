"""
WebSocket 实时通信模块
支持实时聊天、在线状态、危机预警推送
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Optional
import json
import asyncio
from datetime import datetime
import hashlib
import secrets

from database import get_db
from src.models.models import User, UserToken
from src.services.enhanced_ai_agent import enhanced_ai_agent

router = APIRouter()


# ==================== WebSocket 连接管理 ====================

class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # user_id -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}
        # websocket -> user_id
        self.connection_user_map: Dict[WebSocket, int] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """建立连接"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.connection_user_map[websocket] = user_id
        print(f"User {user_id} WebSocket connected, online: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        user_id = self.connection_user_map.pop(websocket, None)
        if user_id and user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} WebSocket disconnected, online: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, user_id: int):
        """发送消息给指定用户"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                print(f"Failed to send message: {e}")
    
    async def broadcast(self, message: dict):
        """广播消息给所有在线用户"""
        for connection in self.active_connections.values():
            try:
                await connection.send_json(message)
            except Exception:
                pass
    
    def get_online_users(self) -> List[int]:
        """获取在线用户列表"""
        return list(self.active_connections.keys())


# 全局连接管理器
manager = ConnectionManager()


# ==================== 认证依赖 ====================

async def get_websocket_current_user(
    websocket: WebSocket,
    db: Session = Depends(get_db)
) -> User:
    """WebSocket 认证依赖"""
    # 从查询参数获取token
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=4001, reason="缺少Token")
        raise Exception("缺少Token")
    
    # 验证Token
    user_token = db.query(UserToken).filter(
        UserToken.token == token,
        UserToken.expires_at > datetime.now()
    ).first()
    
    if not user_token:
        await websocket.close(code=4001, reason="Token无效或已过期")
        raise Exception("Token无效或已过期")
    
    # 获取用户信息
    user = db.query(User).filter(User.id == user_token.user_id).first()
    if not user or user.status != 1:
        await websocket.close(code=4001, reason="用户不存在或已被禁用")
        raise Exception("用户不存在或已被禁用")
    
    return user


# ==================== WebSocket 路由 ====================

@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket 实时聊天接口
    
    连接时传递token参数: ws://localhost:8092/ws/chat?token=xxx
    
    客户端发送消息格式:
    {
        "type": "message",
        "content": "用户消息",
        "emotion": "sad"
    }
    
    服务端返回消息格式:
    {
        "type": "message",
        "content": "AI回复",
        "emotion": "emotion_type",
        "confidence": 0.95,
        "is_crisis": false,
        "crisis_level": "none",
        "timestamp": "2024-01-01T12:00:00"
    }
    """
    user = None
    
    try:
        # 获取token并进行认证
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="缺少Token")
            return
        
        # 验证Token
        user_token = db.query(UserToken).filter(
            UserToken.token == token,
            UserToken.expires_at > datetime.now()
        ).first()
        
        if not user_token:
            await websocket.close(code=4001, reason="Token无效或已过期")
            return
        
        user = db.query(User).filter(User.id == user_token.user_id).first()
        if not user or user.status != 1:
            await websocket.close(code=4001, reason="用户不存在或已被禁用")
            return
        
        # 建立连接
        await manager.connect(websocket, user.id)
        
        # 发送欢迎消息
        await websocket.send_json({
            "type": "system",
            "content": f"欢迎回来，{user.nickname or user.username}！",
            "timestamp": datetime.now().isoformat()
        })
        
        # 发送在线用户数
        await websocket.send_json({
            "type": "online_count",
            "count": len(manager.get_online_users()),
            "timestamp": datetime.now().isoformat()
        })
        
        # 消息循环
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                msg_type = message_data.get("type", "message")
                
                if msg_type == "heartbeat":
                    # 心跳保活
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif msg_type == "message":
                    # 处理聊天消息
                    user_message = message_data.get("content", "")
                    emotion = message_data.get("emotion", "neutral")
                    
                    if not user_message:
                        continue
                    
                    # 发送"正在输入"状态
                    await websocket.send_json({
                        "type": "typing",
                        "content": "AI正在思考..."
                    })
                    
                    # 调用AI服务生成回复（传递db session以加载历史记录）
                    try:
                        ai_result = await enhanced_ai_agent.chat(
                            user.id,
                            user_message,
                            emotion,
                            db
                        )
                        
                        # 保存对话记录到数据库
                        from src.models.models import ChatRecord, EmotionLog, CrisisAlert
                        
                        chat_record = ChatRecord(
                            user_id=user.id,
                            user_message=user_message,
                            ai_reply=ai_result["reply"],
                            emotion_type=ai_result["emotion"],
                            emotion_score=ai_result.get("confidence", 0.8) * 100,
                            is_crisis=ai_result["is_crisis"],
                            created_at=datetime.now()
                        )
                        db.add(chat_record)
                        
                        # 保存情绪日志
                        emotion_log = EmotionLog(
                            user_id=user.id,
                            emotion_type=ai_result["emotion"],
                            emotion_score=ai_result.get("confidence", 0.8) * 100,
                            confidence=ai_result.get("confidence", 0.8),
                            source="text",
                            trigger_context=user_message[:100],
                            created_at=datetime.now()
                        )
                        db.add(emotion_log)
                        
                        # 如果是危机，生成预警
                        if ai_result["is_crisis"]:
                            crisis_alert = CrisisAlert(
                                user_id=user.id,
                                alert_level=ai_result.get("crisis_level", "high"),
                                reason=f"检测到危机关键词: {user_message[:50]}",
                                chat_record_id=chat_record.id,
                                is_handled=False,
                                created_at=datetime.now()
                            )
                            db.add(crisis_alert)
                        
                        db.commit()
                        
                        # 发送AI回复
                        response_data = {
                            "type": "message",
                            "content": ai_result["reply"],
                            "emotion": ai_result["emotion"],
                            "confidence": ai_result.get("confidence", 0.8),
                            "is_crisis": ai_result["is_crisis"],
                            "crisis_level": ai_result.get("crisis_level", "none"),
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send_json(response_data)
                        
                        # 如果是危机，发送预警
                        if ai_result["is_crisis"]:
                            crisis_message = {
                                "type": "crisis_alert",
                                "content": "检测到您可能处于危机状态，请立即寻求专业帮助。\n紧急求助热线：400-161-9995",
                                "level": ai_result.get("crisis_level", "high"),
                                "timestamp": datetime.now().isoformat()
                            }
                            await websocket.send_json(crisis_message)
                            
                    except Exception as e:
                        print(f"AI processing error: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "content": "AI服务暂时不可用，请稍后重试",
                            "timestamp": datetime.now().isoformat()
                        })
                        
                elif msg_type == "emotion_update":
                    # 更新用户当前情绪状态
                    emotion = message_data.get("emotion", "neutral")
                    # 可以选择保存到数据库或内存
                    print(f"User {user.id} emotion updated: {emotion}")
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "消息格式错误",
                    "timestamp": datetime.now().isoformat()
                })
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        print(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket)


@router.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):
    """
    管理员 WebSocket 接口
    用于监控所有用户在线状态、接收危机预警
    """
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            msg_type = message_data.get("type")
            
            if msg_type == "get_online_users":
                # 获取在线用户列表
                online_users = manager.get_online_users()
                await websocket.send_json({
                    "type": "online_users",
                    "users": online_users,
                    "count": len(online_users)
                })
                
            elif msg_type == "broadcast":
                # 广播消息（管理员功能）
                content = message_data.get("content", "")
                await manager.broadcast({
                    "type": "broadcast",
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif msg_type == "send_to_user":
                # 发送消息给指定用户
                target_user_id = message_data.get("user_id")
                content = message_data.get("content", "")
                await manager.send_personal_message({
                    "type": "admin_message",
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }, target_user_id)
                
    except WebSocketDisconnect:
        print("Admin WebSocket disconnected")
    except Exception as e:
        print(f"Admin WebSocket error: {e}")


# ==================== 辅助接口 ====================

@router.get("/ws/status")
async def get_websocket_status():
    """获取WebSocket状态"""
    return {
        "code": 200,
        "data": {
            "online_count": len(manager.get_online_users()),
            "online_users": manager.get_online_users()
        }
    }
