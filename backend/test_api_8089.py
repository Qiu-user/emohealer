import requests

r = requests.post('http://localhost:8089/api/chat/send', json={'user_id':1,'message':'你好'})
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")
