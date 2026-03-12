#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EmoHealer 数据库初始化脚本
"""

import pymysql
import sys

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '19891213',
    'charset': 'utf8mb4'
}

def execute_sql_file(connection, sql_file):
    """执行SQL文件"""
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割SQL语句
    statements = []
    current_stmt = []
    
    for line in sql_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        current_stmt.append(line)
        if line.endswith(';'):
            statements.append(' '.join(current_stmt))
            current_stmt = []
    
    cursor = connection.cursor()
    
    for stmt in statements:
        try:
            cursor.execute(stmt)
            connection.commit()
        except pymysql.err.Error as e:
            # 忽略一些已存在的错误
            if 'Duplicate' not in str(e):
                print(f"执行错误: {e}")
                print(f"语句: {stmt[:100]}...")
    
    cursor.close()

def main():
    try:
        # 连接MySQL
        print("正在连接MySQL...")
        conn = pymysql.connect(**DB_CONFIG)
        print("MySQL连接成功!")
        
        # 执行初始化脚本
        print("\n正在创建数据库和表...")
        execute_sql_file(conn, 'c:/Users/18746/Desktop/biyeshixi/database/init.sql')
        print("数据库初始化完成!")
        
        # 执行测试数据
        print("\n正在添加测试数据...")
        execute_sql_file(conn, 'c:/Users/18746/Desktop/biyeshixi/database/test_data.sql')
        print("测试数据添加完成!")
        
        # 验证数据
        cursor = conn.cursor()
        
        print("\n=== 数据验证 ===")
        cursor.execute("SELECT COUNT(*) FROM emohealer.user")
        print(f"用户: {cursor.fetchone()[0]} 条")
        
        cursor.execute("SELECT COUNT(*) FROM emohealer.chat_record")
        print(f"对话记录: {cursor.fetchone()[0]} 条")
        
        cursor.execute("SELECT COUNT(*) FROM emohealer.emotion_log")
        print(f"情绪日志: {cursor.fetchone()[0]} 条")
        
        cursor.execute("SELECT COUNT(*) FROM emohealer.healing_plan")
        print(f"疗愈方案: {cursor.fetchone()[0]} 条")
        
        cursor.execute("SELECT COUNT(*) FROM emohealer.crisis_alert")
        print(f"危机预警: {cursor.fetchone()[0]} 条")
        
        cursor.execute("SELECT COUNT(*) FROM emohealer.psychological_assessment")
        print(f"心理测评: {cursor.fetchone()[0]} 条")
        
        cursor.execute("SELECT COUNT(*) FROM emohealer.consultation_appointment")
        print(f"咨询预约: {cursor.fetchone()[0]} 条")
        
        cursor.close()
        conn.close()
        
        print("\n数据库初始化成功完成!")
        
    except ImportError:
        print("错误: 请先安装 pymysql")
        print("运行: pip install pymysql")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
