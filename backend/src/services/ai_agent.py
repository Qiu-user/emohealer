"""
EmoHealer AI智能体服务
基于CBT疗愈方法的智能对话系统
"""
import json
import random
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ConversationContext:
    """对话上下文"""
    user_id: int
    messages: List[Dict] = field(default_factory=list)
    current_emotion: str = "neutral"
    emotion_history: List[Dict] = field(default_factory=list)
    session_start: datetime = field(default_factory=datetime.now)
    crisis_detected: bool = False


@dataclass  
class PromptTemplate:
    """Prompt模板"""
    name: str
    template: str
    description: str = ""


class PromptManager:
    """Prompt模板管理器"""
    
    # 系统角色设定
    SYSTEM_PROMPT = """你是EmoHealer，一个专业的AI情绪疗愈助手。

## 角色设定
- 你是一位温暖、专业、有同理心的情绪教练
- 你运用CBT（认知行为疗法）技术帮助用户认识和管理情绪
- 你善于倾听，提供非评判性的支持
- 你的回复要简洁、温暖、有建设性

## 核心能力
1. 情绪识别与标注
2. 认知重构引导
3. 正念练习指导
4. 自我关怀建议
5. 危机识别与转介

## 沟通原则
- 始终保持温暖和同理心
- 不直接给出建议，而是引导用户思考
- 认可用户的情绪是合理的
- 适度使用emoji增加亲切感
- 回复长度控制在100-300字

## 安全边界
- 如果用户表达自杀/自伤念头，立即提供危机干预信息
- 不诊断精神疾病，建议严重情况寻求专业帮助
- 保护用户隐私，不记录敏感个人信息"""

    # 情绪识别Prompt
    EMOTION_ANALYSIS_PROMPT = """分析用户的情绪状态。

用户消息：{message}
当前情绪：{current_emotion}

请分析：
1. 用户当前的主要情绪是什么？（开心/难过/焦虑/愤怒/疲惫/平静）
2. 情绪强度如何？（1-10分）
3. 可能的情绪触发因素是什么？

请用JSON格式返回："""

    # 疗愈对话Prompt
    THERAPY_PROMPT = """基于CBT疗愈方法，生成温暖的对话回复。

用户当前情绪：{emotion}
情绪强度：{intensity}/10
对话历史：
{history}

用户最新消息：{message}

请生成回复，要求：
1. 运用CBT技术帮助用户认知情绪
2. 引导用户思考可能的认知扭曲
3. 提供实用的情绪管理建议
4. 保持温暖、支持性的语气
5. 适当使用emoji

回复："""

    # 危机干预Prompt
    CRISIS_INTERVENTION_PROMPT = """用户表达了一些令人担忧的内容。

用户消息：{message}

这可能表明用户处于危机状态。请：
1. 表达深切的关心
2. 不评判、不争论
3. 提供专业帮助资源
4. 温和地鼓励用户寻求帮助

请生成一段温暖的危机干预回复，长度约200字。"""

    # 疗愈方案生成Prompt
    HEALING_PLAN_PROMPT = """基于用户的情绪状态，生成个性化的每日疗愈方案。

用户信息：
- 当前情绪：{emotion}
- 情绪历史：{emotion_history}
- 使用天数：{usage_days}

请生成今天的疗愈任务，包含：
1. 晨间仪式（5-10分钟）
2. 正念练习（10-15分钟）
3. 情绪记录任务
4. 晚间感恩（5分钟）

要求：
- 任务要简单可行
- 结合CBT疗愈方法
- 体现个性化

请用JSON格式返回："""


class EmotionDetector:
    """情绪检测器"""
    
    # 情绪关键词（中文）
    EMOTION_KEYWORDS = {
        'happy': ['开心', '高兴', '快乐', '愉快', '棒', '不错', '好', '幸福', '满足', '喜悦', '兴奋', '欢乐'],
        'sad': ['难过', '伤心', '哭', '低落', '抑郁', '失望', '沮丧', '悲伤', '痛苦', '绝望', '无助'],
        'anxious': ['焦虑', '担心', '紧张', '害怕', '压力', '不安', '恐惧', '恐慌', '忐忑', '忧虑'],
        'angry': ['生气', '愤怒', '烦躁', '恼火', '不满', '怨恨', '恼怒', '气愤', '火大'],
        'tired': ['累', '疲惫', '困', '疲倦', '无力', '疲劳', '困倦', '精力不足'],
        'neutral': ['一般', '还好', '正常', '没什么', '普通']
    }
    
    # 表情符号映射
    EMOJI_MAP = {
        'happy': '😊',
        'sad': '😢',
        'anxious': '😰',
        'angry': '😠',
        'tired': '😴',
        'neutral': '🙂'
    }
    
    def detect(self, message: str, context: ConversationContext = None) -> Tuple[str, float, List[str]]:
        """
        检测用户情绪
        返回: (情绪类型, 置信度, 触发关键词列表)
        """
        message = message.lower()
        triggers = []
        
        # 关键词匹配
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message:
                    triggers.append(keyword)
        
        if not triggers:
            return 'neutral', 0.5, []
        
        # 计算置信度
        confidence = min(0.6 + len(triggers) * 0.1, 0.95)
        
        # 优先级判断
        emotion_priority = ['sad', 'angry', 'anxious', 'tired', 'happy', 'neutral']
        detected_emotion = 'neutral'
        
        for e in emotion_priority:
            if e in [k for k, v in self.EMOTION_KEYWORDS.items() if any(t in v for t in triggers)]:
                detected_emotion = e
                break
        
        return detected_emotion, confidence, triggers
    
    def get_emoji(self, emotion: str) -> str:
        """获取情绪对应的emoji"""
        return self.EMOJI_MAP.get(emotion, '🙂')


class CrisisDetector:
    """危机检测器"""
    
    # 高危机关键词
    HIGH_RISK_KEYWORDS = [
        '自杀', '自伤', '想死', '不想活', '结束一切', '抹脖子', '上吊',
        '跳楼', '割腕', '安眠药', '氰化物'
    ]
    
    # 中危机关键词
    MEDIUM_RISK_KEYWORDS = [
        '放弃', '绝望', '没用', '活着没意思', '拖累', '不如死了',
        '一了百了', '解脱', '消失', '不存在'
    ]
    
    # 低危机关键词
    LOW_RISK_KEYWORDS = [
        '难过', '痛苦', '无助', '孤独', '绝望', '崩溃'
    ]
    
    # 危机干预热线
    HOTLINE = "400-161-9995"
    
    def detect(self, message: str) -> Tuple[str, bool, str]:
        """
        检测危机级别
        返回: (危机级别, 是否需要干预, 建议)
        """
        message = message.lower()
        
        # 高危机检测
        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in message:
                return 'high', True, self._get_high_intervention()
        
        # 中危机检测
        for keyword in self.MEDIUM_RISK_KEYWORDS:
            if keyword in message:
                return 'medium', True, self._get_medium_intervention()
        
        # 低危机检测
        count = sum(1 for k in self.LOW_RISK_KEYWORDS if k in message)
        if count >= 2:
            return 'low', False, self._get_low_intervention()
        
        return 'none', False, ""
    
    def _get_high_intervention(self) -> str:
        return f"""💙 我感受到你正在经历非常困难的时刻。请记住，你的生命是宝贵的。

如果你有伤害自己的念头，请立即寻求帮助：
📞 24小时心理援助热线：{self.HOTLINE}
🏥 或者前往最近医院的急诊科

你愿意告诉我更多你的感受吗？我在这里陪你。"""
    
    def _get_medium_intervention(self) -> str:
        return f"""💙 我听到你正在经历很难的感受。我想让你知道，你不是一个人。

如果这种绝望感持续存在，建议你：
📞 拨打心理援助热线：{self.HOTLINE}
👥 联系信任的家人或朋友

愿意和我多说说吗？我想了解你的感受。"""
    
    def _get_low_intervention(self) -> str:
        return "💙 我感受到你最近可能过得不太容易。如果想聊聊，我在这里倾听。"


class CBTProcessor:
    """CBT认知行为疗愈处理器"""
    
    # 认知扭曲类型
    COGNITIVE_DISTORTIONS = {
        '全或无': '看事情总是非黑即白，没有中间地带',
        '过度概括': '因为一次失败就否定全部',
        '心理过滤': '只关注负面细节而忽略整体',
        '否定正面': '拒绝正面的经历或反馈',
        '读心术': '假设别人在负面评价你',
        '预测未来': '预测坏事一定会发生',
        '情绪推理': '因为我感觉这样，所以就是真的',
        '应该陈述': '对自己或他人有过多的"应该"要求',
        '标签化': "给自己贴上消极的标签",
        '个人化': '把不相关的事归咎于自己'
    }
    
    # 正念练习
    MINDFULNESS_EXERCISES = {
        'breathing': [
            '4-7-8呼吸法：吸气4秒，屏住呼吸7秒，呼气8秒，重复3-5次',
            '腹式呼吸：把手放在腹部，慢慢吸气让腹部鼓起，慢慢呼气',
            'box breathing：吸气4秒，屏气4秒，呼气4秒，屏气4秒'
        ],
        'grounding': [
            '5-4-3-2-1 grounding：说出5样看到的东西、4样摸到的、3样听到的、2样闻到的、1样尝到的',
            '感受双脚站在地上的感觉，感受身体的重量'
        ],
        'body_scan': [
            '从脚趾开始，慢慢向上移动注意力，觉察身体每个部位的感觉',
            '如果有紧张的地方，尝试深呼吸并放松'
        ]
    }
    
    # 情绪调节技术
    EMOTION_REGULATION = {
        'sad': [
            '允许自己感受悲伤，不要压抑',
            '可以尝试写日记记录当下的感受',
            '做一些让自己感到温暖的事情',
            '回忆一些让你感到安慰的回忆'
        ],
        'anxious': [
            '把担心的事情写下来',
            '问自己：最坏的结果是什么？发生的概率有多大？',
            '专注于当下能控制的事情',
            '使用4-7-8呼吸法放松身体'
        ],
        'angry': [
            '先离开让你生气的场景',
            '尝试用慢速深呼吸',
            '把感受写下来而不是说出来',
            '思考对方行为背后的可能原因'
        ],
        'tired': [
            '允许自己休息，这不是懒惰',
            '列出你能做的最小的一件事',
            '尝试小睡15-20分钟',
            '喝一杯温热的饮料'
        ]
    }
    
    def generate_response(self, message: str, emotion: str, context: ConversationContext) -> str:
        """生成CBT疗愈回复"""
        
        # 选择回复策略
        if emotion in ['sad', 'anxious', 'angry']:
            return self._emotional_support(message, emotion, context)
        elif emotion == 'happy':
            return self._positive_enhancement(message, context)
        else:
            return self._neutral_response(message, context)
    
    def _emotional_support(self, message: str, emotion: str, context: ConversationContext) -> str:
        """情绪支持性回复"""
        
        emotion_words = {
            'sad': ['难过', '伤心', '低落'],
            'anxious': ['焦虑', '担心', '紧张'],
            'angry': ['生气', '愤怒', '烦躁']
        }
        
        # 基础回应
        responses = [
            f"我听到你{emotion_words.get(emotion, ['感到'])[0]}，谢谢愿意告诉我。💙",
            f"感谢你分享你的感受。{emotion_words.get(emotion, [''])[0]}的时候真的不容易。",
            f"我能感受到你的{emotion_words.get(emotion, [''])[0]}。这种感受是合理的。"
        ]
        
        # 添加调节建议
        regulation_tips = self.EMOTION_REGULATION.get(emotion, [])
        if regulation_tips:
            tip = random.choice(regulation_tips)
            responses.append(f"\n\n或许你可以尝试：{tip}")
        
        # 添加正念练习
        mindfulness = random.choice(self.MINDFULNESS_EXERCISES['breathing'])
        responses.append(f"\n\n现在要不要一起做个简单的呼吸练习？{mindfulness}")
        
        return "".join(responses)
    
    def _positive_enhancement(self, message: str, context: ConversationContext) -> str:
        """积极情绪增强"""
        responses = [
            "太棒了！听到你好消息我也跟着开心起来！🌟",
            "快乐的心情值得被珍惜。有什么特别的原因吗？",
            "真好！记得把这份快乐记在心里，难过的时候可以回想起来。💙"
        ]
        
        # 引导正向行为
        responses.append("\n\n或许你可以做一些事情让这份快乐延续：")
        responses.append("- 和重要的人分享这份快乐")
        responses.append("- 记录下让你开心的小事")
        responses.append("- 做一个让你感到满足的计划")
        
        return "".join(responses)
    
    def _neutral_response(self, message: str, context: ConversationContext) -> str:
        """中性/一般情绪回复"""
        responses = [
            "我在这里倾听你。愿意多说说吗？",
            "谢谢你分享。任何情绪都值得被看见。",
            "我在听。你最近过得怎么样？"
        ]
        return random.choice(responses)


class ScenarioDetector:
    """场景检测器 - 检测用户谈论的话题场景"""
    
    SCENARIOS = {
        'work': {
            'keywords': ['工作', '上班', '下班', '老板', '同事', '客户', '项目', '会议', '辞职', '加班', '职场', 'KPI', '考核', '升职', '加薪'],
            'name': '工作'
        },
        'relationship': {
            'keywords': ['恋爱', '分手', '婚姻', '老公', '老婆', '男朋友', '女朋友', '约会', '相亲', '出轨', '离婚', '追求', '表白'],
            'name': '人际关系'
        },
        'family': {
            'keywords': ['父母', '爸爸', '妈妈', '家里', '家人', '亲子', '孩子', '教育', '家庭', '兄弟姐妹', '养老'],
            'name': '家庭'
        },
        'study': {
            'keywords': ['学习', '考试', '考研', '高考', '大学', '学校', '作业', '论文', '成绩', '升学', '留学'],
            'name': '学习'
        },
        'health': {
            'keywords': ['身体', '生病', '健康', '失眠', '睡眠', '减肥', '运动', '头疼', '焦虑症', '抑郁症', '心理'],
            'name': '健康'
        },
        'social': {
            'keywords': ['朋友', '社交', '孤独', '合群', '人际', '圈子', '饭局', '聚会', '微信'],
            'name': '社交'
        },
        'finance': {
            'keywords': ['钱', '房贷', '车贷', '信用卡', '投资', '理财', '负债', '工资', '收入', '省钱', '赚钱'],
            'name': '财务'
        },
        'future': {
            'keywords': ['未来', '迷茫', '方向', '选择', '规划', '目标', '梦想', '人生', '意义', '价值'],
            'name': '未来规划'
        }
    }
    
    # 问题类型
    QUESTION_TYPES = {
        'venting': {'keywords': ['烦', '气', '郁闷', '无语', '累', '崩溃', '不爽'], 'name': '倾诉'},
        'seeking_help': {'keywords': ['怎么办', '怎么处理', '如何', '求解', '帮忙', '建议'], 'name': '求助'},
        'asking': {'keywords': ['为什么', '是不是', '是不是我', '会不会'], 'name': '询问'},
        'sharing': {'keywords': ['今天', '刚才', '刚刚', '然后', '后来'], 'name': '分享'},
        'question_mark': {'keywords': ['?'], 'name': '提问'}
    }
    
    def detect_scenario(self, message: str) -> str:
        """检测场景类型"""
        for scenario, info in self.SCENARIOS.items():
            for keyword in info['keywords']:
                if keyword in message:
                    return scenario
        return 'general'
    
    def detect_question_type(self, message: str) -> str:
        """检测问题类型"""
        for qtype, info in self.QUESTION_TYPES.items():
            for keyword in info['keywords']:
                if keyword in message:
                    return qtype
        return 'sharing'


class ScenarioResponseGenerator:
    """场景化回复生成器"""
    
    def __init__(self):
        self.cbt = CBTProcessor()
        self.scenario_detector = ScenarioDetector()
    
    def generate(self, message: str, emotion: str, context: ConversationContext) -> str:
        """根据场景生成回复"""
        
        # 检测场景
        scenario = self.scenario_detector.detect_scenario(message)
        question_type = self.scenario_detector.detect_question_type(message)
        
        # 根据场景和情绪组合生成回复
        if scenario == 'work':
            return self._work_response(message, emotion, question_type)
        elif scenario == 'relationship':
            return self._relationship_response(message, emotion, question_type)
        elif scenario == 'family':
            return self._family_response(message, emotion, question_type)
        elif scenario == 'study':
            return self._study_response(message, emotion, question_type)
        elif scenario == 'health':
            return self._health_response(message, emotion, question_type)
        elif scenario == 'social':
            return self._social_response(message, emotion, question_type)
        elif scenario == 'finance':
            return self._finance_response(message, emotion, question_type)
        elif scenario == 'future':
            return self._future_response(message, emotion, question_type)
        else:
            # 使用通用CBT回复
            return self.cbt.generate_response(message, emotion, context)
    
    def _work_response(self, message: str, emotion: str, question_type: str) -> str:
        """工作场景回复"""
        
        if '辞职' in message or '不干' in message:
            return """听起来你对工作有些疲惫了。💙
            
在做出重大决定前，不妨先问自己几个问题：
• 这份工作最让你难以忍受的是什么？
• 有没有可能通过沟通或调整来改善？
• 你的经济状况能否支撑你一段时间不工作？

有时候，短暂的休息或调整能帮助我们重新找到方向。如果实在累了，给自己放个假也是不错的选择。"""
        
        if '加班' in message or '忙' in message:
            return """工作很辛苦的话，要记得照顾好自己。💪
            
长期高强度工作可能会导致倦怠，这里有些建议：
• 尝试设置明确的下班时间，到点就停下来
• 每天给自己留15分钟的放空时间
• 周末尽量做一些与工作无关的事情

你的健康比任何工作都重要。如果感到力不从心，不妨和上级沟通一下工作量的调整。"""
        
        if '同事' in message or '老板' in message:
            return """职场人际关系确实不容易处理。🤝
            
面对这种情况，你可以尝试：
• 先冷静下来，客观地看待问题
• 如果是小摩擦，可以主动沟通化解
• 如果对方行为严重影响到你，记录下来，必要时寻求上级或HR帮助

记住，你无法改变他人，但可以调整自己的应对方式。"""
        
        if question_type == 'seeking_help':
            return """关于职场问题，我建议你可以：\n• 先把困扰写下来，理清思路\n• 找一个信任的朋友或导师聊聊\n• 必要时可以咨询职业规划师"""
        
        return """工作中的不容易，我能理解。💙 愿意具体说说发生了什么吗？"""
    
    def _relationship_response(self, message: str, emotion: str, question_type: str) -> str:
        """人际关系场景回复"""
        
        if '分手' in message or '失恋' in message:
            return """分手真的很痛，这种失落感是真实的。💙
            
失恋后，请允许自己悲伤，这是疗愈的一部分：
• 感受来了就让它自然流动，不要压抑
• 可以把思念和难过写下来
• 不要急于走出来，给 自己时间

记住，你值得被爱，现在的痛不代表永远。一段时间后回头看，你会发现自己在成长。"""
        
        if '暗恋' in message or '表白' in message or '追求' in message:
            return """喜欢一个人的感觉既甜蜜又紧张呢！🌸
            
给你一些小建议：
• 先观察对方对你的态度
• 可以先从普通朋友开始，了解彼此
• 表白需要勇气，但也要做好接受任何结果的准备

无论结果如何，勇敢表达心意本身就是一种成长。加油！"""
        
        if '冷战' in message or '吵架' in message:
            return """亲密关系中的冲突很正常，关键是如何处理。💕
            
建议你们：
• 等双方都冷静下来再沟通
• 用"我感受"而不是"你总是"来表达
• 倾听对方的想法，尝试理解对方的立场

良好的沟通能让关系更亲密。"""
        
        return """感情的事确实复杂，我在这里倾听你。💙"""
    
    def _family_response(self, message: str, emotion: str, question_type: str) -> str:
        """家庭场景回复"""
        
        if '父母' in message and ('管' in message or '控制' in message):
            return """父母的过度干涉确实会让人感到窒息。💙
            
这可能是很多子女都会面对的问题：
• 尝试和父母坦诚沟通，表达你的感受
• 设立适当的边界，让父母知道哪些可以管，哪些需要你自己决定
• 理解父母的出发点可能是担心，只是方式需要调整

有时候，成熟地表达自己的观点能让父母更尊重你。"""
        
        if '孩子' in message or '教育' in message:
            return """教育孩子是件不容易的事。👶
            
给你一些建议：
• 给孩子足够的陪伴和关注
• 鼓励比批评更能激发孩子的积极性
• 尊重孩子的兴趣爱好，给他们选择的空间

每个孩子都是独特的，找到适合你们家庭的教育方式最重要。"""
        
        if '养老' in message or '照顾' in message:
            return """照顾家人是很辛苦的事，你也很不容易。💪
            
别忘了照顾好自己：
• 可以寻求其他家庭成员的帮助
• 了解是否有社区或政府资源可以支持
• 给自己留一些休息和放松的时间

你已经在努力了，这本身就值得尊敬。"""
        
        return """家庭关系是我们生命中重要的一部分。💙 愿意多说说吗？"""
    
    def _study_response(self, message: str, emotion: str, question_type: str) -> str:
        """学习场景回复"""
        
        if '考试' in message or '高考' in message or '考研' in message:
            return """考试压力确实很大，这种紧张是很常见的。📚
            
给你一些缓解压力的建议：
• 制定合理的学习计划，不要临时抱佛脚
• 适当的休息和运动能提高学习效率
• 记住：尽力而为就好，结果不是唯一标准

考试只是人生的一个阶段，不是全部。保持好心态！"""
        
        if '失眠' in message or '睡不着' in message:
            return """睡前不要想太多事情，给大脑一些放空的时间。🌙
            
可以尝试：
• 泡个热水澡或喝杯温牛奶
• 做些简单的拉伸放松身体
• 用深呼吸让身体平静下来

如果长期失眠，建议咨询专业医生。"""
        
        if '学不进去' in message or '不想学' in message:
            return """学习动力不足很正常，每个人都会有倦怠期。💙
            
可以尝试：
• 给自己设定小目标，完成后会有成就感
• 改变学习环境或方式
• 适当休息，给大脑充电的时间

不要对自己太苛刻，适当的休息是为了更好地前进。"""
        
        return """学习上的困扰我理解。💙 愿意具体说说吗？"""
    
    def _health_response(self, message: str, emotion: str, question_type: str) -> str:
        """健康场景回复"""
        
        if '失眠' in message or '睡眠' in message:
            return """睡眠质量对身体和情绪都很重要。🌙
            
改善睡眠的小建议：
• 固定作息时间，尽量同一时间睡觉和起床
• 睡前避免使用手机等电子设备
• 创造安静、黑暗的睡眠环境
• 下午以后避免咖啡因

如果长期失眠，建议去看看睡眠专科医生。"""
        
        if '焦虑' in message or '紧张' in message:
            return """焦虑时，尝试这些放松方法：🧘
            
• 4-7-8呼吸法：吸气4秒，屏住呼吸7秒，呼气8秒
• 5-4-3-2-1 grounding：说出看到的5样东西、4样摸到的...
• 把担心的事写下来，然后问自己：这件事真的会发生吗？

如果焦虑严重影响生活，建议寻求专业帮助。"""
        
        if '减肥' in message or '运动' in message:
            return """关注健康是很棒的事！💪
            
减肥建议：
• 不要急于求成，健康减重每周0.5-1公斤为宜
• 均衡饮食比节食更重要
• 选择自己喜欢的运动方式，更容易坚持
• 给自己一些时间改变习惯

身体健康最重要，不要为了减肥而伤害自己。"""
        
        return """身体健康是幸福生活的基础。💙 愿意多说说吗？"""
    
    def _social_response(self, message: str, emotion: str, question_type: str) -> str:
        """社交场景回复"""
        
        if '孤独' in message or '一个人' in message:
            return """孤独感每个人都会有，这很正常。💙
            
应对孤独的建议：
• 培养自己的兴趣爱好，丰富独处时光
• 主动联系老朋友，哪怕是一条消息
• 参加一些兴趣小组或活动，认识新朋友
• 接受独处，把它当成自我成长的机会

记住，孤独不等于孤单，你可以学会与自己相处。"""
        
        if '不合群' in message or '融不入' in message:
            return """不想迎合别人是很正常的想法。✨
            
给你一些建议：
• 真正的朋友不需要你刻意迎合
• 找到志同道合的人，比融入错误的圈子更重要
• 学会独处，也是一种能力
• 质量比数量更重要，有几个知心朋友就够了

做真实的自己，才会遇到真正欣赏你的人。"""
        
        return """人际关系确实需要花心思经营。💙 愿意多说说吗？"""
    
    def _finance_response(self, message: str, emotion: str, question_type: str) -> str:
        """财务场景回复"""
        
        if '焦虑' in message or '压力' in message:
            return """经济压力确实让人焦虑，这很正常。💰
            
给你一些建议：
• 把焦虑写下来，列出你能控制的部分
• 制定合理的理财计划，开源节流
• 寻求额外的收入来源或职业发展机会
• 记住：钱是手段，不是目的

但也要注意，身体和心理健康比金钱更重要。"""
        
        if '省钱' in message or '省钱':
            return """理财是个好习惯！💡
            
省钱建议：
• 记账了解自己的消费习惯
• 区分"需要"和"想要"
• 设置储蓄目标，每月固定存一部分
• 避免冲动消费，购物前列清单

但也不要对自己太苛刻，适度的享受也是必要的。"""
        
        return """经济问题确实很重要。💙 愿意多说说你的困扰吗？"""
    
    def _future_response(self, message: str, emotion: str, question_type: str) -> str:
        """未来规划场景回复"""
        
        if '迷茫' in message:
            return """感到迷茫是很正常的，很多人都会经历这个阶段。🌟
            
给你一些建议：
• 迷茫说明你在思考人生，这是成长的开始
• 可以尝试不同的事物，找到自己的兴趣
• 和不同行业的人聊聊，了解更多信息
• 记住：没有绝对正确的选择，重要的是行动

迷茫时，做好当下的事就是对未来最好的准备。"""
        
        if '选择' in message:
            return """选择困难是很常见的问题。🤔
            
做决定的建议：
• 把选项写下来，列出每个的优缺点
• 问自己：哪个选项更符合我的价值观？
• 接受没有完美选择，每个选择都有代价
• 给自己设定决策的时间限制

有时候，做了决定后全力以赴，比一直纠结更有意义。"""
        
        if '意义' in message or '价值' in message:
            return """思考人生意义是很深刻的话题。💫
            
一些想法：
• 意义不是找到的，而是活出来的
• 关注当下的生活，做好眼前的事
• 关心他人，为社会创造价值
• 接受自己是个普通人，也值得被爱

人生的意义可能不是一个固定答案，而是一段探索的旅程。"""
        
        return """对未来的思考说明你在成长。💙 愿意多说说你的想法吗？"""


class LLMWrapper:
    """LLM API包装器（支持多种模型）"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.provider = self.config.get('provider', 'mock')  # mock/baidu/openai/chatglm
    
    async def chat(self, messages: List[Dict], system_prompt: str = None) -> str:
        """调用LLM生成回复"""
        
        if self.provider == 'mock':
            return await self._mock_chat(messages, system_prompt)
        elif self.provider == 'baidu':
            return await self._baidu_chat(messages, system_prompt)
        elif self.provider == 'openai':
            return await self._openai_chat(messages, system_prompt)
        elif self.provider == 'chatglm':
            return await self._chatglm_chat(messages, system_prompt)
        else:
            return await self._mock_chat(messages, system_prompt)
    
    async def _mock_chat(self, messages: List[Dict], system_prompt: str) -> str:
        """模拟LLM回复（用于测试）"""
        import asyncio
        await asyncio.sleep(0.1)  # 模拟延迟
        
        last_message = messages[-1]['content'] if messages else ""
        
        # 简单的关键词匹配回复
        cbt = CBTProcessor()
        detector = EmotionDetector()
        
        emotion, _, _ = detector.detect(last_message)
        return cbt.generate_response(last_message, emotion, None)
    
    async def _baidu_chat(self, messages: List[Dict], system_prompt: str) -> str:
        """百度文心一言API"""
        # TODO: 实现百度API调用
        return await self._mock_chat(messages, system_prompt)
    
    async def _openai_chat(self, messages: List[Dict], system_prompt: str) -> str:
        """OpenAI API"""
        # TODO: 实现OpenAI API调用
        return await self._mock_chat(messages, system_prompt)
    
    async def _chatglm_chat(self, messages: List[Dict], system_prompt: str) -> str:
        """ChatGLM本地模型"""
        # TODO: 实现ChatGLM调用
        return await self._mock_chat(messages, system_prompt)


class HealingPlanGenerator:
    """疗愈方案生成器"""
    
    def generate_daily_plan(self, emotion: str, emotion_history: List[Dict], usage_days: int) -> Dict:
        """生成每日疗愈方案"""
        
        # 根据情绪选择主题
        theme = self._get_theme(emotion)
        
        # 生成任务
        tasks = {
            'morning': self._generate_morning_routine(theme),
            'mindfulness': self._generate_mindfulness_practice(theme),
            'journal': self._generate_journal_prompt(emotion),
            'evening': self._generate_evening_routine(theme)
        }
        
        return {
            'theme': theme,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'tasks': tasks,
            'tips': self._generate_tips(emotion)
        }
    
    def _get_theme(self, emotion: str) -> str:
        themes = {
            'sad': '自我接纳与悲伤疏导',
            'anxious': '放松与压力缓解',
            'angry': '情绪调节与边界设定',
            'tired': '休息与能量恢复',
            'happy': '积极情绪延续',
            'neutral': '情绪觉察与成长'
        }
        return themes.get(emotion, '情绪觉察与成长')
    
    def _generate_morning_routine(self, theme: str) -> str:
        routines = [
            '醒来后先做3次深呼吸，感谢新的一天',
            '花5分钟写下今天想完成的三件事',
            '对镜子里的自己说：我今天会很棒',
            '听一首让你感到平静或愉快的歌'
        ]
        return random.choice(routines)
    
    def _generate_mindfulness_practice(self, theme: str) -> str:
        practices = [
            '10分钟身体扫描冥想',
            '5分钟呼吸冥想（4-7-8呼吸法）',
            '5分钟正念行走，感受脚下的每一步',
            '5分钟自我关怀冥想'
        ]
        return random.choice(practices)
    
    def _generate_journal_prompt(self, emotion: str) -> str:
        prompts = {
            'sad': '今天让我感到难过的具体事情是什么？我对这件事的真实感受是什么？',
            'anxious': '我今天担心的事情是什么？这些事情真的会发生吗？可能性有多大？',
            'angry': '让我生气的具体事件是什么？我为什么会这么生气？',
            'tired': '今天是什么让我感到疲惫？我可以做些什么来照顾自己？',
            'happy': '今天让我感到开心的事情是什么？我可以如何延续这份快乐？',
            'neutral': '今天我的情绪有什么变化？我注意到了什么？'
        }
        return prompts.get(emotion, '今天我的情绪有什么变化？')
    
    def _generate_evening_routine(self, theme: str) -> str:
        routines = [
            '写下3件今天让你感恩的事情',
            '回顾今天的情绪变化，给自己一个拥抱',
            '花5分钟静坐，放空思绪',
            '对明天许下一个美好的愿望'
        ]
        return random.choice(routines)
    
    def _generate_tips(self, emotion: str) -> List[str]:
        tips = {
            'sad': [
                '允许自己难过，情绪没有对错',
                '可以找一个安全的表达方式（如写日记、画画）',
                '做一些简单的自我照顾事情'
            ],
            'anxious': [
                '把担心的事情写下来',
                '专注于你能控制的事情',
                '深呼吸，放松身体'
            ],
            'angry': [
                '先离开让你生气的场景',
                '用力的活动可以帮助释放能量',
                '尝试理解对方行为背后的原因'
            ],
            'tired': [
                '允许自己休息，这不是懒惰',
                '适当的休息会让你更有效率',
                '注意睡眠质量'
            ]
        }
        return tips.get(emotion, ['关注自己的情绪变化', '保持规律的作息'])


class EmoHealerAgent:
    """EmoHealer AI智能体主类"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # 初始化各模块
        self.prompt_manager = PromptManager()
        self.emotion_detector = EmotionDetector()
        self.crisis_detector = CrisisDetector()
        self.cbt_processor = CBTProcessor()
        self.scenario_generator = ScenarioResponseGenerator()  # 新增：场景化回复生成器
        self.llm = LLMWrapper(self.config.get('llm', {}))
        self.plan_generator = HealingPlanGenerator()
        
        # 对话上下文缓存
        self.contexts: Dict[int, ConversationContext] = {}
    
    def get_context(self, user_id: int) -> ConversationContext:
        """获取或创建对话上下文"""
        if user_id not in self.contexts:
            self.contexts[user_id] = ConversationContext(user_id=user_id)
        return self.contexts[user_id]
    
    def clear_context(self, user_id: int):
        """清除对话上下文"""
        if user_id in self.contexts:
            del self.contexts[user_id]
    
    async def chat(self, user_id: int, message: str, emotion: str = None) -> Dict:
        """
        处理用户对话
        返回包含AI回复和相关信息的字典
        """
        context = self.get_context(user_id)
        
        # 记录用户消息
        context.messages.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # 检测情绪
        if emotion is None:
            detected_emotion, confidence, triggers = self.emotion_detector.detect(message)
            emotion = detected_emotion
        else:
            confidence = 0.85
            triggers = []
        
        context.current_emotion = emotion
        context.emotion_history.append({
            'emotion': emotion,
            'timestamp': datetime.now().isoformat()
        })
        
        # 检测危机
        crisis_level, needs_intervention, crisis_message = self.crisis_detector.detect(message)
        
        if crisis_level != 'none':
            context.crisis_detected = True
            return {
                'reply': crisis_message,
                'emotion': emotion,
                'confidence': confidence,
                'is_crisis': True,
                'crisis_level': crisis_level,
                'triggers': triggers,
                'timestamp': datetime.now().isoformat()
            }
        
        # 生成回复（优先使用LLM）
        use_llm = self.config.get('use_llm', False)
        
        if use_llm:
            try:
                # 构建消息列表
                messages = context.messages[-10:]  # 最近10条
                reply = await self.llm.chat(
                    messages,
                    self.prompt_manager.SYSTEM_PROMPT
                )
            except Exception as e:
                print(f"LLM call failed: {e}")
                # 使用场景化回复生成器
                reply = self.scenario_generator.generate(message, emotion, context)
        else:
            # 使用场景化回复生成器（包含CBT和场景策略）
            reply = self.scenario_generator.generate(message, emotion, context)
        
        # 记录AI回复
        context.messages.append({
            'role': 'assistant',
            'content': reply,
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'reply': reply,
            'emotion': emotion,
            'confidence': confidence,
            'is_crisis': False,
            'crisis_level': 'none',
            'triggers': triggers,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_healing_plan(self, user_id: int, emotion: str = None) -> Dict:
        """生成疗愈方案"""
        context = self.get_context(user_id)
        
        if emotion is None:
            emotion = context.current_emotion
        
        return self.plan_generator.generate_daily_plan(
            emotion,
            context.emotion_history,
            (datetime.now() - context.session_start).days + 1
        )


# 创建全局AI智能体实例
ai_agent = EmoHealerAgent(config={
    'use_llm': False,  # 设为True启用LLM
    'llm': {
        'provider': 'mock'
    }
})
