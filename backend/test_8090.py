# -*- coding: utf-8 -*-
import requests
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

r = requests.post('http://localhost:8090/api/chat/send', json={'user_id':1,'message':'我最近失眠了'})
print(f"Status: {r.status_code}")
d = r.json()
print(f"Reply: {d.get('reply', 'N/A')[:80]}")
print(f"Has tips: {'knowledge_tips' in d}")
