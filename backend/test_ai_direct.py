"""直接测试AI智能体"""
import asyncio
import sys
sys.path.insert(0, '.')

from src.services.enhanced_ai_agent import enhanced_ai_agent

async def test_ai():
    print("Testing AI agent...")
    try:
        result = await enhanced_ai_agent.chat(1, "你好")
        print(f"AI Result: {result}")
        return result
    except Exception as e:
        print(f"AI Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_ai())
