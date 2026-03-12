import requests
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 测试聊天API（使用AI智能体）
print("=" * 50)
print("Test AI Agent Chat (Chinese)")
print("=" * 50)

# Test 1: 焦虑
r = requests.post('http://localhost:8088/api/chat/send', json={
    'user_id': 1,
    'message': '我今天工作压力很大',
    'emotion': 'anxious'
})
data = r.json()
print(f"\n1. 焦虑测试:")
print(f"   Emotion: {data.get('emotion')}")
print(f"   Crisis: {data.get('is_crisis')}")

# Test 2: 开心
r2 = requests.post('http://localhost:8088/api/chat/send', json={
    'user_id': 1,
    'message': '我今天升职了，好开心！',
    'emotion': 'happy'
})
data2 = r2.json()
print(f"\n2. 开心测试:")
print(f"   Emotion: {data2.get('emotion')}")

# Test 3: 疗愈方案
r3 = requests.get('http://localhost:8088/api/healing-plan/1')
data3 = r3.json()
print(f"\n3. 疗愈方案测试:")
print(f"   Raw: {str(data3)[:200]}")

print("\n" + "=" * 50)
print("Test completed!")
