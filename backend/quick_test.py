import sys
sys.path.insert(0, r"c:\Users\18746\Desktop\biyeshixi\backend")

print("=== 测试开始 ===", flush=True)

try:
    print("1. 导入database...", flush=True)
    from database import engine
    print("   engine ok", flush=True)
    conn = engine.connect()
    print("   connect ok", flush=True)
    conn.close()
    print("   数据库: OK", flush=True)
except Exception as e:
    print(f"   数据库: 失败 - {e}", flush=True)

try:
    print("2. 导入AI模块...", flush=True)
    from src.services.enhanced_ai_agent import enhanced_ai_agent
    print("   AI模块: OK", flush=True)
except Exception as e:
    print(f"   AI模块: 失败 - {e}", flush=True)

try:
    print("3. 导入API路由...", flush=True)
    from src.routes import api
    print("   API路由: OK", flush=True)
except Exception as e:
    print(f"   API路由: 失败 - {e}", flush=True)

try:
    print("4. 导入main...", flush=True)
    from main import app
    print("   main: OK", flush=True)
except Exception as e:
    print(f"   main: 失败 - {e}", flush=True)

print("=== 测试完成 ===", flush=True)
