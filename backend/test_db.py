"""测试数据库连接"""
from database import engine
from sqlalchemy import text

try:
    print("Testing database connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"Database connected! Result: {result.fetchone()}")
except Exception as e:
    print(f"Database error: {e}")
