import asyncio
from src.services.enhanced_ai_agent import enhanced_ai_agent

async def test():
    result = await enhanced_ai_agent.chat(1, "我今天工作压力很大，感觉很焦虑")
    print("Reply:", result['reply'])
    print("Emotion:", result['emotion'])
    print("Role:", result['agent_role'])

asyncio.run(test())
