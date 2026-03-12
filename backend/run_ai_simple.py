"""简单的服务启动脚本 - 直接双击运行"""
import sys
import os
import functools

# 强制输出刷新
print = functools.partial(print, flush=True)

# 切换到脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

# 切换到脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 40)
print("EmoHealer AI 后端启动")
print("=" * 40)

# 1. 检查依赖
print("\n[1/4] 检查依赖...")
try:
    import fastapi
    import uvicorn
    import sqlalchemy
    import pydantic
    print(" 依赖检查 通过")
except ImportError as e:
    print(f"  缺少依赖: {e}")
    print("  请运行: pip install -r requirements.txt")
    input("按回车退出...")
    sys.exit(1)

# 2. 检查数据库
print("\n[2/4] 检查数据库...")
try:
    from database import engine
    conn = engine.connect()
    conn.close()
    print("  数据库连接成功")
except Exception as e:
    print(f"  数据库连接失败: {e}")
    print("  请检查:")
    print("    1. MySQL服务是否已启动")
    print("    2. config.py中的数据库配置是否正确")
    input("按回车退出...")
    sys.exit(1)

# 3. 检查AI模块
print("\n[3/4] 检查AI模块...")
try:
    from src.services.enhanced_ai_agent import enhanced_ai_agent
    print("  AI模块加载成功")
except Exception as e:
    print(f"  AI模块加载失败: {e}")
    input("按回车退出...")
    sys.exit(1)

# 4. 启动服务
print("\n[4/4] 启动服务...")
print("  服务地址: http://localhost:8088")
print("  API文档: http://localhost:8088/docs")
print("  测试API: http://localhost:8088/api/health")
print("\n" + "=" * 40)
print("按 Ctrl+C 停止服务")
print("=" * 40 + "\n")

import uvicorn
from main import app

try:
    uvicorn.run(app, host="0.0.0.0", port=8088)
except KeyboardInterrupt:
    print("\n服务已停止")
