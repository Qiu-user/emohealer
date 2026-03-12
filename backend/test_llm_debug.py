import asyncio
import requests

async def test_llm():
    # 模拟LLM调用
    api_key = "sk-yvrlkvsdjcocuqaflmemkcevtgacjzclofysaetmztwhulcm"
    api_base = "https://api.siliconflow.cn/v1"
    model = "Qwen/Qwen2.5-7B-Instruct"
    
    url = f"{api_base}/v1/chat/completions"
    
    messages = [{"role": "user", "content": "我今天工作压力很大"}]
    system_prompt = "你是一个温暖的心理咨询师"
    
    formatted_messages = []
    if system_prompt:
        formatted_messages.append({"role": "system", "content": system_prompt})
    formatted_messages.extend(messages)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": formatted_messages,
        "temperature": 0.8,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print("Status:", response.status_code)
        print("Response text:", response.text[:200])
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print("Content:", content)
        else:
            print("Error response")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_llm())
