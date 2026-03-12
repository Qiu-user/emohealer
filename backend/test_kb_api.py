# -*- coding: utf-8 -*-
import requests
import json
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

r = requests.post('http://localhost:8089/api/chat/send', json={'user_id':1,'message':'我最近压力很大'})
d = r.json()

print(f"Status: {r.status_code}")
print(f"Has knowledge_tips: {'knowledge_tips' in d}")

if 'knowledge_tips' in d:
    tips = d['knowledge_tips']
    print(f"Tips count: {len(tips)}")
    if tips:
        print(f"First tip: {tips[0].get('title', 'N/A')}")
        print(f"Content: {tips[0].get('content', 'N/A')[:100]}...")
else:
    print("Reply:", d.get('reply', 'N/A')[:100])
