import sys
sys.path.insert(0, '.')

from database import SessionLocal, engine
from src.models.models import User
from sqlalchemy import text

print("=== 测试数据库连接 ===")

# 测试1: 使用text()
db = SessionLocal()
try:
    result = db.execute(text("SELECT COUNT(*) FROM user"))
    count = result.fetchone()[0]
    print(f"用户数量 (text): {count}")
except Exception as e:
    print(f"text() 错误: {e}")

# 测试2: 使用ORM
try:
    users = db.query(User).limit(3).all()
    print(f"用户数量 (ORM): {len(users)}")
except Exception as e:
    print(f"ORM 错误: {e}")

db.close()
print("测试完成")
