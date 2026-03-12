import requests
import json

BASE_URL = "http://localhost:8088/api"

def test_api(name, method, url, data=None):
    """测试单个API"""
    print(f"\n{'='*50}")
    print(f"测试: {name}")
    print(f"URL: {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)[:200]}...")
            return True
        else:
            print(f"错误: {response.text}")
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False

print("=== EmoHealer API 完整接口测试 ===\n")

# 1. 健康检查
test_api("健康检查", "GET", f"{BASE_URL}/health")

# 2. 获取用户列表
test_api("获取用户列表", "GET", f"{BASE_URL}/users")

# 3. 获取用户信息
test_api("获取用户信息", "GET", f"{BASE_URL}/user/1")

# 4. 发送消息
test_api("发送消息", "POST", f"{BASE_URL}/chat/send", {
    "user_id": 1,
    "message": "我今天心情不好",
    "emotion_type": "sad"
})

# 5. 获取对话历史
test_api("获取对话历史", "GET", f"{BASE_URL}/chat/history/1")

# 6. 获取情绪趋势(周)
test_api("情绪趋势(周)", "POST", f"{BASE_URL}/emotion/trend", {
    "user_id": 1,
    "period": "week"
})

# 7. 获取情绪趋势(月)
test_api("情绪趋势(月)", "POST", f"{BASE_URL}/emotion/trend", {
    "user_id": 1,
    "period": "month"
})

# 8. 获取疗愈方案
test_api("获取疗愈方案", "GET", f"{BASE_URL}/healing-plan/1")

# 9. 获取疗愈方案列表
test_api("获取疗愈方案列表", "GET", f"{BASE_URL}/plans/1")

# 10. 提交心理测评
test_api("提交心理测评", "POST", f"{BASE_URL}/assessment/submit", {
    "user_id": 1,
    "assessment_type": "PHQ-9",
    "answers": [0, 1, 1, 2, 0, 1, 0, 0, 0],
    "level": "mild",
    "suggestions": "建议多参加户外活动"
})

# 11. 获取测评历史
test_api("获取测评历史", "GET", f"{BASE_URL}/assessment/1")

# 12. 提交预约咨询
test_api("提交预约咨询", "POST", f"{BASE_URL}/appointment/submit", {
    "user_id": 1,
    "name": "张三",
    "phone": "13800138000",
    "consultation_type": "video",
    "appointment_date": "2026-03-15",
    "description": "情绪困扰"
})

# 13. 获取预约列表
test_api("获取预约列表", "GET", f"{BASE_URL}/appointment/1")

# 14. 获取用户统计
test_api("获取用户统计", "GET", f"{BASE_URL}/stats/1")

print("\n" + "="*50)
print("=== 所有接口测试完成 ===")
