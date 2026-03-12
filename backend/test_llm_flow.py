"""测试LLM调用流程"""
import asyncio
import sys
import requests
sys.path.insert(0, '.')

async def test():
    from src.services.enhanced_ai_agent import enhanced_ai_agent, ConversationContext
    from src.services.enhanced_ai_agent import EmotionAnalyzer, PersonaManager

    # 打印当前配置
    print(f"use_llm: {enhanced_ai_agent.use_llm}")
    print(f"llm provider: {enhanced_ai_agent.llm.provider}")

    # 创建上下文
    context = ConversationContext(user_id=1)
    context.messages = []

    # 分析情绪
    analyzer = EmotionAnalyzer()
    message = "我今天心情不好，很烦"
    emotion_analysis = analyzer.analyze(message, context)
    print(f"\nemotion_analysis: {emotion_analysis}")

    # 测试LLM调用
    print("\n=== 测试LLM调用 ===")
    llm = enhanced_ai_agent.llm

    # 直接测试API
    url = f"{llm.api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {llm.api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": llm.model,
        "messages": [{"role": "user", "content": "hello"}],
        "temperature": 0.8,
        "max_tokens": 200
    }

    print(f"URL: {url}")
    print(f"Model: {llm.model}")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
