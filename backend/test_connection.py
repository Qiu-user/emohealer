import requests

# 测试API连接
print("=== 测试前后端连接 ===\n")

# 1. 健康检查
try:
    r = requests.get('http://localhost:8088/api/health', timeout=5)
    print(f"1. 健康检查: {r.status_code} - {r.json()}")
except Exception as e:
    print(f"1. 健康检查失败: {e}")

# 2. 情绪趋势API
try:
    r = requests.post('http://localhost:8088/api/emotion/trend', 
                      json={'user_id': 1, 'period': 'month'}, timeout=5)
    print(f"2. 情绪趋势API: {r.status_code}")
    data = r.json()
    if data.get('code') == 200:
        print(f"   数据条数: {len(data.get('data', []))}")
    else:
        print(f"   响应: {data}")
except Exception as e:
    print(f"2. 情绪趋势API失败: {e}")

# 3. 对话API
try:
    r = requests.post('http://localhost:8088/api/chat/send',
                      json={'user_id': 1, 'message': '我今天心情不好', 'emotion_type': '难过'}, timeout=5)
    print(f"3. 对话API: {r.status_code}")
    data = r.json()
    print(f"   AI回复: {data.get('reply', '无回复')[:50]}...")
except Exception as e:
    print(f"3. 对话API失败: {e}")

print("\n=== 测试完成 ===")
