"""
用户认证API模块
提供注册、登录、登出、token验证等功能
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import get_db

router = APIRouter(prefix="/auth", tags=["认证"])

# Token过期时间（天）
TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """密码哈希"""
    salt = "EmoHealer2026"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


def generate_token() -> str:
    """生成随机Token"""
    return secrets.token_urlsafe(32)


# ==================== 请求模型 ====================

class RegisterRequest(BaseModel):
    username: str
    password: str
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[str] = None
    avatar_url: Optional[str] = None


# ==================== API接口 ====================

@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册
    """
    # 检查用户名是否已存在
    existing = db.execute(
        "SELECT id FROM user WHERE username = %s",
        (request.username,)
    ).fetchone()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已注册
    if request.email:
        existing_email = db.execute(
            "SELECT id FROM user WHERE email = %s",
            (request.email,)
        ).fetchone()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

    # 创建用户
    password_hash = hash_password(request.password)
    nickname = request.nickname or request.username

    result = db.execute(
        """INSERT INTO user (username, password_hash, nickname, email, phone, status, role)
           VALUES (%s, %s, %s, %s, %s, 'user', 'user')""",
        (request.username, password_hash, nickname, request.email, request.phone)
    )
    db.commit()

    user_id = result.lastrowid

    # 生成Token
    token = generate_token()
    expires_at = datetime.now() + timedelta(days=TOKEN_EXPIRE_DAYS)

    db.execute(
        """INSERT INTO user_token (user_id, token, expires_at)
           VALUES (%s, %s, %s)""",
        (user_id, token, expires_at)
    )
    db.commit()

    # 获取用户信息
    user = db.execute(
        "SELECT id, username, nickname, avatar_url, email, role FROM user WHERE id = %s",
        (user_id,)
    ).fetchone()

    return {
        "code": 200,
        "message": "注册成功",
        "data": {
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "avatar_url": user.avatar_url,
                "email": user.email,
                "role": user.role
            }
        }
    }


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录
    """
    # 查找用户
    user = db.execute(
        "SELECT id, username, password_hash, nickname, avatar_url, email, phone, status, role FROM user WHERE username = %s",
        (request.username,)
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 验证密码
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 检查账号状态
    if user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )

    # 更新最后登录时间
    db.execute(
        "UPDATE user SET last_login = %s WHERE id = %s",
        (datetime.now(), user.id)
    )

    # 生成新Token
    token = generate_token()
    expires_at = datetime.now() + timedelta(days=TOKEN_EXPIRE_DAYS)

    # 删除旧Token
    db.execute("DELETE FROM user_token WHERE user_id = %s", (user.id,))

    # 插入新Token
    db.execute(
        "INSERT INTO user_token (user_id, token, expires_at) VALUES (%s, %s, %s)",
        (user.id, token, expires_at)
    )
    db.commit()

    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "avatar_url": user.avatar_url,
                "email": user.email,
                "phone": user.phone,
                "role": user.role
            }
        }
    }


@router.post("/logout")
def logout(token: str, db: Session = Depends(get_db)):
    """
    用户登出
    """
    db.execute("DELETE FROM user_token WHERE token = %s", (token,))
    db.commit()

    return {
        "code": 200,
        "message": "登出成功"
    }


@router.get("/verify")
def verify_token(token: str, db: Session = Depends(get_db)):
    """
    验证Token是否有效
    """
    # 查找Token
    token_record = db.execute(
        """SELECT ut.user_id, u.id, u.username, u.nickname, u.avatar_url,
                  u.email, u.phone, u.bio, u.gender, u.birthday, u.role, u.status
           FROM user_token ut
           JOIN user u ON ut.user_id = u.id
           WHERE ut.token = %s AND ut.expires_at > %s""",
        (token, datetime.now())
    ).fetchone()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效或已过期"
        )

    return {
        "code": 200,
        "data": {
            "user": {
                "id": token_record.id,
                "username": token_record.username,
                "nickname": token_record.nickname,
                "avatar_url": token_record.avatar_url,
                "email": token_record.email,
                "phone": token_record.phone,
                "bio": token_record.bio,
                "gender": token_record.gender,
                "birthday": str(token_record.birthday) if token_record.birthday else None,
                "role": token_record.role
            }
        }
    }


@router.get("/profile")
def get_profile(token: str, db: Session = Depends(get_db)):
    """
    获取用户资料
    """
    # 查找用户
    token_record = db.execute(
        "SELECT user_id FROM user_token WHERE token = %s AND expires_at > %s",
        (token, datetime.now())
    ).fetchone()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录"
        )

    user = db.execute(
        """SELECT id, username, nickname, avatar_url, email, phone, bio,
                  gender, birthday, role, last_login, created_at
           FROM user WHERE id = %s""",
        (token_record.user_id,)
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return {
        "code": 200,
        "data": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "email": user.email,
            "phone": user.phone,
            "bio": user.bio,
            "gender": user.gender,
            "birthday": str(user.birthday) if user.birthday else None,
            "role": user.role,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }


@router.post("/profile")
def update_profile(
    request: UpdateProfileRequest,
    token: str,
    db: Session = Depends(get_db)):
    """
    更新用户资料
    """
    # 查找用户
    token_record = db.execute(
        "SELECT user_id FROM user_token WHERE token = %s AND expires_at > %s",
        (token, datetime.now())
    ).fetchone()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录"
        )

    # 构建更新语句
    updates = []
    params = []

    if request.nickname is not None:
        updates.append("nickname = %s")
        params.append(request.nickname)
    if request.email is not None:
        updates.append("email = %s")
        params.append(request.email)
    if request.phone is not None:
        updates.append("phone = %s")
        params.append(request.phone)
    if request.bio is not None:
        updates.append("bio = %s")
        params.append(request.bio)
    if request.gender is not None:
        updates.append("gender = %s")
        params.append(request.gender)
    if request.birthday is not None:
        updates.append("birthday = %s")
        params.append(request.birthday)
    if request.avatar_url is not None:
        updates.append("avatar_url = %s")
        params.append(request.avatar_url)

    if updates:
        params.append(token_record.user_id)
        sql = f"UPDATE user SET {', '.join(updates)} WHERE id = %s"
        db.execute(sql, tuple(params))
        db.commit()

    # 获取更新后的用户信息
    user = db.execute(
        "SELECT id, username, nickname, avatar_url, email, phone, bio, gender, birthday, role FROM user WHERE id = %s",
        (token_record.user_id,)
    ).fetchone()

    return {
        "code": 200,
        "message": "更新成功",
        "data": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "email": user.email,
            "phone": user.phone,
            "bio": user.bio,
            "gender": user.gender,
            "birthday": str(user.birthday) if user.birthday else None,
            "role": user.role
        }
    }


@router.post("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    token: str,
    db: Session = Depends(get_db)):
    """
    修改密码
    """
    # 查找用户
    token_record = db.execute(
        "SELECT user_id FROM user_token WHERE token = %s AND expires_at > %s",
        (token, datetime.now())
    ).fetchone()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录"
        )

    # 获取用户
    user = db.execute(
        "SELECT password_hash FROM user WHERE id = %s",
        (token_record.user_id,)
    ).fetchone()

    # 验证旧密码
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )

    # 更新密码
    new_hash = hash_password(new_password)
    db.execute(
        "UPDATE user SET password_hash = %s WHERE id = %s",
        (new_hash, token_record.user_id)
    )

    # 使所有旧Token失效
    db.execute("DELETE FROM user_token WHERE user_id = %s", (token_record.user_id,))
    db.commit()

    return {
        "code": 200,
        "message": "密码修改成功，请重新登录"
    }
