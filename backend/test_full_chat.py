"""测试完整的AI对话流程"""
import requests
import json

# 先检查AI配置状态
print("=== 1. 检查AI配置 ===")
status_url = "http://localhost:8088/api/ai/config/status"
status_resp = requests.get(status_url)
print(json.dumps(status_resp.json(), indent=2, ensure_ascii=False))

# 测试发送消息
print("\n=== 2. 测试发送消息 ===")
chat_url = "http://localhost:8088/api/chat/send"
data = {"user_id": 1, "message": "我今天心情不好，感觉很烦"}
headers = {"Content-Type": "application/json"}

response = requests.post(chat_url, json=data, headers=headers, timeout=30)
print(f"状态码: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))
