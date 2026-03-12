"""测试API返回原始内容"""
import requests

API_KEY = "sk-yvrlkvsdjcocuqaflmemkcevtgacjzclofysaetmztwhulcm"
API_BASE = "https://api.siliconflow.cn/v1"
MODEL = "Qwen/Qwen2.5-7B-Instruct"

url = f"{API_BASE}/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "hello"}],
    "temperature": 0.8,
    "max_tokens": 200
}

print("=== 测试原始请求 ===")
try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers.get('content-type')}")
    print(f"Content length: {len(response.content)}")
    print(f"Raw text: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
