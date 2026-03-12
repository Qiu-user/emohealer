import pymysql
from datetime import datetime, timedelta

# 连接数据库
conn = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    password='19891213',
    database='emohealer',
    charset='utf8mb4'
)

cursor = conn.cursor()

print("=== 检查数据库中的情绪日志 ===\n")

# 查询最近的30条情绪日志
cursor.execute("""
    SELECT id, user_id, emotion_type, emotion_score, created_at 
    FROM emotion_log 
    ORDER BY created_at DESC 
    LIMIT 30
""")

logs = cursor.fetchall()
print(f"情绪日志总数: {len(logs)}")
print("\n最近的情绪日志记录:")
for log in logs[:10]:
    print(f"  ID: {log[0]}, 用户ID: {log[1]}, 情绪: {log[2]}, 分数: {log[3]}, 时间: {log[4]}")

# 检查最近30天是否有数据
print("\n=== 检查日期范围 ===")
cursor.execute("""
    SELECT MIN(created_at), MAX(created_at) FROM emotion_log
""")
result = cursor.fetchone()
print(f"最早记录: {result[0]}")
print(f"最新记录: {result[1]}")

# 检查当前日期
print(f"\n当前日期: {datetime.now()}")
print(f"30天前: {datetime.now() - timedelta(days=30)}")

conn.close()
