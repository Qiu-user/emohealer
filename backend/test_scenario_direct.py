import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

from src.services.ai_agent import EmoHealerAgent

# 创建AI智能体
agent = EmoHealerAgent()

print("=" * 60)
print("Test Multi-Scenario AI Response")
print("=" * 60)

scenarios = [
    ("我工作压力很大，想辞职", "anxious"),
    ("和女朋友分手了，好难过", "sad"),
    ("和父母吵架了，他们管太多", "angry"),
    ("考研考不上怎么办", "anxious"),
    ("晚上失眠睡不着", "tired"),
    ("感觉融不入圈子，一个人", "sad"),
    ("房贷压力好大，焦虑", "anxious"),
    ("对未来很迷茫，不知道干嘛", "neutral"),
]

import asyncio

async def test():
    for message, emotion in scenarios:
        result = await agent.chat(1, message, emotion)
        print(f"\n输入: {message}")
        print(f"回复: {result['reply'][:200]}...")
        print("-" * 40)

asyncio.run(test())

print("\n" + "=" * 60)
print("Test completed!")
