import requests

BASE_URL = "http://localhost:8088/api"

tests = [
    ("GET", "/health", None, "健康检查"),
    ("GET", "/users", None, "获取用户列表"),
    ("GET", "/user/1", None, "获取用户信息"),
    ("GET", "/chat/history/1", None, "获取对话历史"),
    ("GET", "/healing-plan/1", None, "获取疗愈方案"),
]

print("=== 当前可用接口测试 ===\n")

for method, path, data, name in tests:
    url = BASE_URL + path
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json=data, timeout=5)
        
        status = "OK" if r.status_code == 200 else f"ERR({r.status_code})"
        print(f"[{status}] {name}")
        print(f"    {method} {path}")
    except Exception as e:
        print(f"[FAIL] {name} - {e}")

print("\n=== 测试对话功能 ===")
try:
    r = requests.post(BASE_URL + "/chat/send", json={
        "user_id": 1,
        "message": "我今天很开心",
        "emotion_type": "happy"
    }, timeout=5)
    result = r.json()
    print(f"[OK] AI回复: {result.get('reply', '')[:50]}...")
except Exception as e:
    print(f"[FAIL] 对话功能 - {e}")

print("\n=== 测试情绪趋势 ===")
try:
    r = requests.post(BASE_URL + "/emotion/trend", json={
        "user_id": 1,
        "period": "week"
    }, timeout=5)
    result = r.json()
    data_count = len(result.get('data', []))
    print(f"[OK] 情绪数据: {data_count} 条")
except Exception as e:
    print(f"[FAIL] 情绪趋势 - {e}")

print("\n测试完成！")
