# -*- coding: utf-8 -*-
import sys
import asyncio
sys.path.insert(0, '.')

async def test():
    from src.services.enhanced_ai_agent import enhanced_ai_agent

    result = await enhanced_ai_agent.chat(1, "我最近压力很大")
    print("Reply:", result.get('reply', 'N/A')[:100])
    print("Has knowledge_tips:", 'knowledge_tips' in result)
    if 'knowledge_tips' in result:
        print("Tips:", result['knowledge_tips'])

asyncio.run(test())
