"""测试后端服务启动"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("1. 测试数据库连接...", flush=True)
    from database import engine
    conn = engine.connect()
    print("   数据库连接成功", flush=True)
    conn.close()
except Exception as e:
    print(f"   数据库连接失败: {e}", flush=True)

try:
    print("\n2. 测试AI智能体导入...", flush=True)
    from src.services.enhanced_ai_agent import enhanced_ai_agent
    print("   AI智能体导入成功", flush=True)
except Exception as e:
    print(f"   AI智能体导入失败: {e}", flush=True)

try:
    print("\n3. 测试API路由...", flush=True)
    from src.routes import api
    print("   API路由导入成功", flush=True)
except Exception as e:
    print(f"   API路由导入失败: {e}", flush=True)

print("\n测试完成!")
