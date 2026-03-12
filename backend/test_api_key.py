import requests
import json

# 测试SiliconFlow API
api_key = "sk-yvrlkvsdjcocuqaflmemkcevtgacjzclofysaetmztwhulcm"
url = "https://api.siliconflow.cn/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100
}

try:
    r = requests.post(url, headers=headers, json=data, timeout=10)
    print("Status:", r.status_code)
    print("Response:", r.text[:500])
except Exception as e:
    print("Error:", e)
