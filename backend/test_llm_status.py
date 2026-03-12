# -*- coding: utf-8 -*-
import requests
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 测试聊天接口
r = requests.post('http://localhost:8089/api/chat/send', json={'user_id':1,'message':'我今天工作压力很大'})
print(f"Status: {r.status_code}")
result = r.json()
reply = result.get('reply', 'N/A')
print(f"Reply: {reply[:100]}")
print(f"Agent Role: {result.get('agent_role', 'N/A')}")
