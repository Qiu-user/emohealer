import random
from datetime import datetime

class AIService:
    """AI对话服务 - 模拟基于CBT的疗愈对话"""
    
    # 情绪关键词映射
    emotion_keywords = {
        'happy': ['开心', '高兴', '快乐', '快乐', '棒', '不错', '好'],
        'sad': ['难过', '伤心', '哭', '难过', '低落', '抑郁', '失望'],
        'anxious': ['焦虑', '担心', '紧张', '害怕', '压力', '不安'],
        'angry': ['生气', '愤怒', '烦躁', '恼火', '不满'],
        'tired': ['累', '疲惫', '困', '疲倦', '无力']
    }
    
    # 预设回复
    responses = {
        'happy': [
            "听到你今天心情不错，我也很为你高兴！😊 有什么特别的事情想分享吗？",
            "太棒了！快乐的心情值得延续。继续保持这份好心情吧！🌟",
            "很高兴你能感受到快乐。记得珍惜这份美好的感觉，也可以把它记录下来哦！"
        ],
        'sad': [
            "我在这里陪你。难过的时候，能说出来就已经是很好的开始。💙 你想聊聊发生了什么吗？",
            "感到难过是很正常的情绪，不要责怪自己。慢慢说，我在这里倾听。",
            "感谢你愿意分享你的难过。每个人都会有低潮期，你并不孤单。让我陪你好吗？"
        ],
        'anxious': [
            "焦虑是一种很常见的情绪。深呼吸一下，告诉我是什么让你感到焦虑呢？🫁",
            "我能感受到你的不安。先放松一下，焦虑的时候我们更需要好好照顾自己。",
            "面对焦虑，你可以尝试先把让你担心的事情写下来，然后一步一步来解决。"
        ],
        'angry': [
            "愤怒是很有力量的情绪，它可能在提醒我们某些边界被侵犯了。💪 发生了什么让你生气的事情？",
            "感受到愤怒是很正常的。给自己一点空间和时间来处理这种强烈的情绪。",
            "愤怒时，先深呼吸冷静一下是很好的做法。你想聊聊是什么引起了你的愤怒吗？"
        ],
        'tired': [
            "你看起来很累了。休息一下很重要，你的身心都在提醒你需要充电了。😴",
            "疲惫的时候，允许自己停下来很重要。你最近是不是太辛苦了呢？",
            "记得照顾好自己。如果可以的话，给自己安排一些休息时间吧。"
        ]
    }
    
    default_responses = [
        "感谢你的分享。每一种情绪都值得被看见和理解。💙",
        "我在这里倾听你。慢慢说，不要着急。",
        "你能愿意表达自己的情绪，这本身就是一种勇气。🌟",
        "我理解你的感受。愿意多说说吗？"
    ]
    
    crisis_keywords = ['自杀', '自伤', '放弃', '不想活', '结束一切', '绝望']
    
    def detect_emotion(self, message: str) -> tuple[str, float]:
        """检测用户情绪"""
        message_lower = message.lower()
        
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    return emotion, 0.85
        
        return 'neutral', 0.6
    
    def check_crisis(self, message: str) -> bool:
        """检查是否涉及危机"""
        for keyword in self.crisis_keywords:
            if keyword in message:
                return True
        return False
    
    def generate_response(self, message: str, emotion: str = None) -> dict:
        """生成AI回复"""
        # 如果未指定情绪，自动检测
        if emotion is None:
            emotion, confidence = self.detect_emotion(message)
        else:
            confidence = 0.85
        
        # 检查危机
        is_crisis = self.check_crisis(message)
        
        # 选择回复
        if emotion in self.responses:
            response_text = random.choice(self.responses[emotion])
        else:
            response_text = random.choice(self.default_responses)
        
        # 危机干预回复
        if is_crisis:
            response_text = (
                "我感受到你正在经历非常困难的时刻。💙\n\n"
                "请记住，你不是一个人。你的生命是宝贵的，值得被珍惜。\n\n"
                "如果你有伤害自己的念头，建议你立即寻求帮助：\n"
                "- 拨打心理援助热线：400-161-9995\n"
                "- 或联系家人朋友陪伴\n\n"
                "我在这里陪着你，你可以告诉我更多你的感受。"
            )
        
        return {
            "reply": response_text,
            "emotion": emotion,
            "confidence": confidence,
            "is_crisis": is_crisis,
            "timestamp": datetime.now().isoformat()
        }

# 创建全局AI服务实例
ai_service = AIService()
