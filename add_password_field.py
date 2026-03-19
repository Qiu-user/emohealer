import pymysql

conn = pymysql.connect(host='localhost', user='root', password='19891213', database='emohealer')
cursor = conn.cursor()

# 添加password_hash字段
try:
    cursor.execute("ALTER TABLE user ADD COLUMN password_hash VARCHAR(255) AFTER username")
    print("添加password_hash字段成功!")
except:
    print("字段可能已存在")

conn.commit()
conn.close()
