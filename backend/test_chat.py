"""测试后端chat接口"""
import requests
import json

url = "http://localhost:8088/api/chat/send"
data = {"user_id": 1, "message": "你好"}
headers = {"Content-Type": "application/json"}

try:
    print("Testing chat API...")
    response = requests.post(url, json=data, headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response text: {response.text[:500]}")
    if response.text:
        result = response.json()
        print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
except Exception as e:
    print(f"Error: {e}")
