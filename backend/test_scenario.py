import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Test Multi-Scenario AI Response")
print("=" * 60)

scenarios = [
    ("我工作压力很大，想辞职", "anxious", "工作场景"),
    ("和女朋友分手了，好难过", "sad", "恋爱场景"),
    ("和父母吵架了，他们管太多", "angry", "家庭场景"),
    ("考研考不上怎么办", "anxious", "学习场景"),
    ("晚上失眠睡不着", "tired", "健康场景"),
    ("感觉融不入圈子，一个人", "sad", "社交场景"),
    ("房贷压力好大，焦虑", "anxious", "财务场景"),
    ("对未来很迷茫，不知道干嘛", "neutral", "未来规划场景"),
]

for message, emotion, name in scenarios:
    r = requests.post('http://localhost:8088/api/chat/send', json={
        'user_id': 1,
        'message': message,
        'emotion': emotion
    })
    data = r.json()
    print(f"\n[{name}]")
    print(f"输入: {message}")
    print(f"回复: {data.get('reply', '')[:150]}...")

print("\n" + "=" * 60)
print("Test completed!")
