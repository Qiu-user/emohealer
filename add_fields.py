import pymysql

conn = pymysql.connect(host='localhost', user='root', password='19891213', database='emohealer')
cursor = conn.cursor()

# 添加缺失的字段
fields = [
    ("bio", "TEXT"),
    ("gender", "VARCHAR(10) DEFAULT 'unknown'"),
    ("birthday", "DATE")
]

for field_name, field_type in fields:
    try:
        cursor.execute(f"ALTER TABLE user ADD COLUMN {field_name} {field_type}")
        print(f"添加 {field_name} 成功!")
    except Exception as e:
        print(f"添加 {field_name}: {e}")

conn.commit()
conn.close()
print("\n字段添加完成!")
