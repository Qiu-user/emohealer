import pymysql

conn = pymysql.connect(host='localhost', user='root', password='19891213', database='emohealer')
cursor = conn.cursor()

# 添加last_login字段
try:
    cursor.execute("ALTER TABLE user ADD COLUMN last_login DATETIME AFTER role")
    print("添加last_login字段成功!")
except Exception as e:
    print(f"错误: {e}")

conn.commit()
conn.close()
