import sys
sys.path.insert(0, '.')
from src.services.enhanced_ai_agent import enhanced_ai_agent
import asyncio

async def test():
    result = await enhanced_ai_agent.chat(19, '你好', None, None)
    print('Result:', result)

asyncio.run(test())
