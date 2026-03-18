"""
EmoHealer AI智能体服务 - 增强版
基于多角色智能体架构的CBT疗愈对话系统
"""
import json
import random
import re
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 导入AI配置
try:
    from src.config.ai_config import AI_CONFIG
except ImportError:
    AI_CONFIG = {
        "use_llm": False,
        "llm_provider": "mock",
        "llm": {
            "mock": {"api_key": "", "model": ""},
            "baidu": {"api_key": "", "api_secret": "", "model": "ernie-lite-8k"},
            "openai": {"api_key": "", "api_base": "https://api.openai.com/v1", "model": "gpt-3.5-turbo"}
        }
    }

# 导入知识库
try:
    from src.services.knowledge_base import knowledge_base
    HAS_KNOWLEDGE_BASE = True
except ImportError:
    HAS_KNOWLEDGE_BASE = False
    knowledge_base = None

# 导入RAG增强模块
try:
    from src.services.emotion_rag import emotion_rag
    HAS_EMOTION_RAG = True
except ImportError:
    HAS_EMOTION_RAG = False
    emotion_rag = None


class AgentRole(Enum):
    """智能体角色类型"""
    LISTENER = "listener"      # 倾听者 - 理解、共情
    SUPPORTER = "supporter"    # 支持者 - 鼓励、陪伴
    COACH = "coach"           # 教练 - 引导、启发
    EDUCATOR = "educator"     # 教育者 - 知识、解释


@dataclass
class ConversationContext:
    """对话上下文"""
    user_id: int
    messages: List[Dict] = field(default_factory=list)
    current_emotion: str = "neutral"
    emotion_history: List[Dict] = field(default_factory=list)
    session_start: datetime = field(default_factory=datetime.now)
    crisis_detected: bool = False
    user_name: str = ""
    conversation_turn: int = 0
    last_agent_role: str = "listener"
    user_profile: Dict = field(default_factory=dict)


@dataclass
class PersonaConfig:
    """人设配置"""
    name: str
    description: str
    traits: List[str]
    response_style: str
    expertise: List[str]


class PersonaManager:
    """多角色人设管理器"""
    
    # 智能体人设库
    PERSONAS = {
        "listener": PersonaConfig(
            name="温暖倾听者",
            description="一位富有同理心的倾听者，擅长理解用户的情绪和感受",
            traits=["温暖", "同理心", "耐心", "非评判"],
            response_style="温柔、关怀、专注倾听",
            expertise=["情绪识别", "共情表达", "无条件积极关注"]
        ),
        "supporter": PersonaConfig(
            name="坚定支持者",
            description="一位给人力量的伙伴，擅长鼓励和陪伴",
            traits=["积极", "乐观", "坚定", "温暖"],
            response_style="鼓励、肯定、支持性",
            expertise=["自我效能感提升", "积极心理学", "优势发现"]
        ),
        "coach": PersonaConfig(
            name="成长教练",
            description="一位启发思考的教练，擅长引导用户找到答案",
            traits=["启发性", "好奇心", "引导性", "洞察力"],
            response_style="提问、引导、启发思考",
            expertise=["CBT技术", "焦点解决", "激励性访谈"]
        ),
        "educator": PersonaConfig(
            name="知识导师",
            description="一位专业的知识导师，擅长解释和教授",
            traits=["专业", "清晰", "博学", "耐心"],
            response_style="解释、说明、教育性",
            expertise=["情绪知识", "心理教育", "自我调节技巧"]
        ),
        "mindfulness_guide": PersonaConfig(
            name="正念导师",
            description="一位平和的正念指导者，擅长引导放松和冥想",
            traits=["平和", "宁静", "专业", "温柔"],
            response_style="平静、引导、放松",
            expertise=["正念冥想", "放松技术", "身体扫描"]
        )
    }
    
    @classmethod
    def get_persona(cls, role: str) -> PersonaConfig:
        return cls.PERSONAS.get(role, cls.PERSONAS["listener"])
    
    @classmethod
    def select_role(cls, emotion: str, context: ConversationContext) -> str:
        """根据情绪和对话阶段选择合适的角色"""
        
        # 危机情况优先使用倾听者
        if context.crisis_detected:
            return "listener"
        
        turn = context.conversation_turn
        
        # 初期：倾听者为主
        if turn < 3:
            return "listener"
        
        # 中期：根据情绪和话题类型选择
        if emotion in ["sad", "anxious"]:
            # 负面情绪：倾听 -> 支持 -> 教练
            if turn < 6:
                return "supporter"
            else:
                return "coach"
        elif emotion == "angry":
            # 愤怒情绪：先倾听，再教育
            if turn < 4:
                return "listener"
            else:
                return "educator"
        elif emotion == "happy":
            # 积极情绪：支持者增强
            return "supporter"
        else:
            # 中性：教练引导
            return "coach"


class EnhancedPromptManager:
    """增强版Prompt管理器"""
    
    # 系统角色设定
    SYSTEM_PROMPT = """你是EmoHealer AI，一位专业的AI情绪疗愈助手。

## 角色设定
- 你是一位温暖、专业、有同理心的情绪教练
- 你运用CBT（认知行为疗法）技术帮助用户认识和管理情绪
- 你善于倾听，提供非评判性的支持
- 你的回复要简洁、温暖、有建设性

## 核心能力
1. 情绪识别与精准标注
2. 认知重构引导（CBT技术）
3. 正念练习指导
4. 自我关怀建议
5. 危机识别与转介

## 沟通原则
- 始终保持温暖和同理心
- 不直接给出建议，而是引导用户思考
- 认可用户的情绪是合理的
- 适度使用emoji增加亲切感
- 回复长度控制在100-300字
- 根据对话阶段选择合适的角色

## 安全边界
- 如果用户表达自杀/自伤念头，立即提供危机干预信息
- 不诊断精神疾病，建议严重情况寻求专业帮助
- 保护用户隐私，不记录敏感个人信息"""

    # 角色特定Prompt
    ROLE_PROMPTS = {
        "listener": """你现在的角色是【温暖倾听者】。
你的主要任务是：
1. 认真倾听用户的表达，不急于给出建议
2. 用自己的语言复述用户的感受，确认理解
3. 表达真诚的同理心，让用户感到被理解
4. 避免打断或转变话题

回复要求：
- 语气温柔、关怀
- 重点表达理解和支持
- 适当使用"我听到..."、"我理解..."等句式
- 可以适当提问引导用户进一步表达""",

        "supporter": """你现在的角色是【坚定支持者】。
你的主要任务是：
1. 发现用户身上的优点和力量
2. 提供鼓励和支持，增强用户信心
3. 帮助用户看到自己的进步
4. 激发用户的积极情绪

回复要求：
- 语气积极、乐观
- 重点发现用户的积极面
- 使用鼓励性语言
- 适当使用"我相信..."、"你很棒..."等句式""",

        "coach": """你现在的角色是【成长教练】。
你的主要任务是：
1. 通过提问引导用户思考
2. 帮助用户发现自己的认知模式
3. 引导用户找到自己的解决方案
4. 促进用户的自我成长

回复要求：
- 语气启发性、引导性
- 多用开放式问题
- 引导用户反思
- 使用"如果...会怎样"、"你觉得..."等句式""",

        "educator": """你现在的角色是【知识导师】。
你的主要任务是：
1. 解释情绪产生的原理
2. 教授情绪管理的技巧
3. 提供专业的心理知识
4. 分享有效的应对策略

回复要求：
- 语气专业、清晰
- 解释要通俗易懂
- 提供实用的技巧
- 可以适当使用比喻""",

        "mindfulness_guide": """你现在的角色是【正念导师】。
你的主要任务是：
1. 引导用户进行正念练习
2. 帮助用户放松身心
3. 教授冥想和呼吸技巧
4. 创造平静、宁静的氛围

回复要求：
- 语气平和、缓慢、温柔
- 引导语清晰、具体
- 步骤要简单易行
- 创造放松的氛围"""
    }

    # 情绪分析Prompt
    EMOTION_ANALYSIS_PROMPT = """请分析用户的情绪状态。

用户消息：{message}
对话历史：{history}
当前情绪：{current_emotion}

请分析并返回JSON格式：
{{
    "primary_emotion": "主要情绪类型",
    "emotion_intensity": 1-10,
    "emotion_triggers": ["可能的触发因素"],
    "cognitive_pattern": "可能的认知模式（如果适用）",
    "suggested_approach": "建议的应对方式"
}}

情绪类型选项：开心、难过、焦虑、愤怒、恐惧、惊讶、厌恶、平静、疲惫、困惑"""


class EmotionAnalyzer:
    """增强版情绪分析器"""
    
    # 基础情绪关键词
    EMOTION_KEYWORDS = {
        'happy': ['开心', '高兴', '快乐', '愉快', '棒', '不错', '好', '幸福', '满足', '喜悦', '兴奋', '欢乐', '美好', '惊喜', '激动'],
        'sad': ['难过', '伤心', '哭', '低落', '抑郁', '失望', '沮丧', '悲伤', '痛苦', '绝望', '无助', '心碎', '失落', '遗憾'],
        'anxious': ['焦虑', '担心', '紧张', '害怕', '压力', '不安', '恐惧', '恐慌', '忐忑', '忧虑', '慌乱', '六神无主', '坐立不安'],
        'angry': ['生气', '愤怒', '烦躁', '恼火', '不满', '怨恨', '恼怒', '气愤', '火大', '愤怒', '暴怒', '讨厌', '厌烦'],
        'tired': ['累', '疲惫', '困', '疲倦', '无力', '疲劳', '困倦', '精力不足', '没精神', '倦怠', '虚脱'],
        'fear': ['害怕', '恐惧', '担心', '惊恐', '畏惧', '后怕', '胆战心惊'],
        'surprised': ['惊讶', '意外', '吃惊', '震惊', '没想到', '突然', '居然'],
        'disgusted': ['讨厌', '恶心', '厌恶', '反感', '嫌弃', '恶心想吐'],
        'neutral': ['一般', '还好', '正常', '没什么', '普通', '平淡']
    }
    
    # 情绪强度修饰词
    INTENSITY_MODIFIERS = {
        'very': ['非常', '特别', '极其', '十分', '超级', '太', '好'],
        'slightly': ['有点', '稍微', '轻度', '略微', '有些'],
        'slightly_negative': ['有点', '略微', '有些', '轻度']
    }
    
    # 表情符号映射
    EMOJI_MAP = {
        'happy': '😊', 'sad': '😢', 'anxious': '😰', 'angry': '😠',
        'tired': '😴', 'fear': '😨', 'surprised': '😲', 'disgusted': '🤢', 'neutral': '🙂'
    }
    
    # 情绪维度映射（用于数据分析）
    EMOTION_DIMENSIONS = {
        'happy': {'valence': 0.8, 'arousal': 0.7, 'dominance': 0.6},
        'sad': {'valence': -0.7, 'arousal': 0.3, 'dominance': 0.3},
        'anxious': {'valence': -0.5, 'arousal': 0.8, 'dominance': 0.2},
        'angry': {'valence': -0.6, 'arousal': 0.9, 'dominance': 0.5},
        'tired': {'valence': -0.3, 'arousal': -0.5, 'dominance': 0.4},
        'fear': {'valence': -0.7, 'arousal': 0.8, 'dominance': 0.2},
        'surprised': {'valence': 0.2, 'arousal': 0.8, 'dominance': 0.5},
        'disgusted': {'valence': -0.6, 'arousal': 0.5, 'dominance': 0.5},
        'neutral': {'valence': 0.0, 'arousal': 0.0, 'dominance': 0.5}
    }
    
    def analyze(self, message: str, context: ConversationContext = None) -> Dict:
        """
        综合分析用户情绪
        返回详细的情绪分析结果
        """
        message_lower = message.lower()
        
        # 1. 基础情绪检测
        primary_emotion, intensity, triggers = self._detect_emotion(message_lower)
        
        # 2. 强度调整
        intensity = self._adjust_intensity(message_lower, intensity)
        
        # 3. 认知模式识别
        cognitive_pattern = self._identify_cognitive_pattern(message_lower)
        
        # 4. 建议的应对方式
        suggested_approach = self._get_suggested_approach(primary_emotion, cognitive_pattern)
        
        return {
            'primary_emotion': primary_emotion,
            'emotion_intensity': intensity,
            'emotion_triggers': triggers,
            'cognitive_pattern': cognitive_pattern,
            'suggested_approach': suggested_approach,
            'dimensions': self.EMOTION_DIMENSIONS.get(primary_emotion, self.EMOTION_DIMENSIONS['neutral'])
        }
    
    def _detect_emotion(self, message: str) -> Tuple[str, int, List[str]]:
        """检测基础情绪"""
        triggers = []
        emotion_scores = {}
        
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            score = 0
            found_triggers = []
            for keyword in keywords:
                if keyword in message:
                    score += 1
                    found_triggers.append(keyword)
            if score > 0:
                emotion_scores[emotion] = score
                triggers.extend(found_triggers)
        
        if not emotion_scores:
            return 'neutral', 5, []
        
        # 优先级判断
        priority = ['sad', 'angry', 'anxious', 'fear', 'disgusted', 'tired', 'surprised', 'happy', 'neutral']
        for e in priority:
            if e in emotion_scores:
                return e, min(5 + emotion_scores[e], 10), triggers[:5]
        
        return 'neutral', 5, []
    
    def _adjust_intensity(self, message: str, base_intensity: int) -> int:
        """根据修饰词调整情绪强度"""
        for modifier in self.INTENSITY_MODIFIERS['very']:
            if modifier in message:
                return min(base_intensity + 2, 10)
        
        for modifier in self.INTENSITY_MODIFIERS['slightly']:
            if modifier in message:
                return max(base_intensity - 1, 1)
        
        return base_intensity
    
    def _identify_cognitive_pattern(self, message: str) -> Optional[str]:
        """识别认知模式"""
        patterns = {
            '全或无思维': ['总是', '永远', '从不', '全部', '彻底'],
            '过度概括': ['一切', '所有', '每次', '所有人'],
            '心理过滤': ['只', '只有', '总是负面'],
            '否定正面': ['不算什么', '没什么', '运气好'],
            '读心术': ['一定觉得', '肯定认为', '他们在想'],
            '预测未来': ['肯定会', '一定会', '肯定要', '注定'],
            '情绪推理': ['所以', '说明', '就是', '肯定是'],
            '应该陈述': ['应该', '必须', '一定要', '不该'],
            '标签化': ['我是', '我就是', '就是个'],
            '个人化': ['都怪', '都是因为我', '我的错']
        }
        
        for pattern, keywords in patterns.items():
            for keyword in keywords:
                if keyword in message:
                    return pattern
        
        return None
    
    def _get_suggested_approach(self, emotion: str, cognitive_pattern: Optional[str]) -> str:
        """获取建议的应对方式"""
        approaches = {
            'happy': '继续保持这种积极情绪，可以记录下让你感到快乐的事情',
            'sad': '允许自己感受悲伤，可以写日记或寻求支持',
            'anxious': '尝试放松技术，把担心的事情写下来',
            'angry': '先冷静下来，用力深呼吸，离开让你生气的场景',
            'tired': '允许自己休息，做一些简单的自我照顾',
            'fear': '面对恐惧，可以把害怕的事情分解成小步骤',
            'neutral': '保持觉察，关注当下的感受'
        }
        
        base_approach = approaches.get(emotion, '保持觉察')
        
        if cognitive_pattern:
            cbt_approaches = {
                '全或无思维': '尝试看到事物的中间地带',
                '过度概括': '关注具体的情况，而不是全部',
                '读心术': '可以通过直接沟通来确认别人的想法',
                '预测未来': '问自己：这件事真的会发生吗？',
                '应该陈述': '尝试把"应该"换成"希望"',
            }
            if cognitive_pattern in cbt_approaches:
                base_approach += '。' + cbt_approaches[cognitive_pattern]
        
        return base_approach
    
    def get_emoji(self, emotion: str) -> str:
        """获取情绪对应的emoji"""
        return self.EMOJI_MAP.get(emotion, '🙂')


class ConversationStrategy:
    """对话策略引擎"""
    
    def __init__(self):
        self.emotion_analyzer = EmotionAnalyzer()
        self.persona_manager = PersonaManager()
    
    async def generate_response(
        self,
        message: str,
        emotion: str,
        context: ConversationContext,
        llm_provider=None
    ) -> Dict:
        """
        生成智能回复
        根据对话阶段和用户情绪选择合适的策略
        """
        
        # 分析情绪
        emotion_analysis = self.emotion_analyzer.analyze(message, context)
        
        # 选择角色
        agent_role = self.persona_manager.select_role(
            emotion_analysis['primary_emotion'],
            context
        )
        
        # 更新上下文
        context.last_agent_role = agent_role
        context.conversation_turn += 1
        
        # 构建回复
        if llm_provider:
            # 使用LLM生成回复
            response = await self._generate_llm_response(
                message, emotion_analysis, agent_role, context, llm_provider
            )
        else:
            # 使用规则模板生成回复
            response = self._generate_template_response(
                message, emotion_analysis, agent_role, context
            )
        
        return {
            'response': response,
            'emotion': emotion_analysis['primary_emotion'],
            'emotion_intensity': emotion_analysis['emotion_intensity'],
            'agent_role': agent_role,
            'cognitive_pattern': emotion_analysis.get('cognitive_pattern'),
            'suggested_approach': emotion_analysis.get('suggested_approach'),
            'emotion_analysis': emotion_analysis
        }
    
    async def _generate_llm_response(
        self,
        message: str,
        emotion_analysis: Dict,
        agent_role: str,
        context: ConversationContext,
        llm_provider
    ) -> str:
        """使用LLM生成回复"""
        
        # 构建系统提示
        role_prompt = EnhancedPromptManager.ROLE_PROMPTS.get(agent_role, "")
        
        emotion_context = f"""
用户当前情绪：{emotion_analysis['primary_emotion']}
情绪强度：{emotion_analysis['emotion_intensity']}/10
可能的认知模式：{emotion_analysis.get('cognitive_pattern', '无')}
建议的应对方式：{emotion_analysis.get('suggested_approach', '')}
"""
        
        # 构建对话历史
        history = ""
        for msg in context.messages[-5:]:
            role = "用户" if msg['role'] == 'user' else "AI"
            history += f"{role}：{msg['content'][:100]}\n"
        
        full_prompt = f"""{EnhancedPromptManager.SYSTEM_PROMPT}

{role_prompt}

{emotion_context}

对话历史：
{history}

用户最新消息：{message}

请生成回复（100-300字）：
"""

        # 使用await而不是asyncio.run()
        return await llm_provider.chat([
            {"role": "user", "content": full_prompt}
        ])
    
    def _generate_template_response(
        self,
        message: str,
        emotion_analysis: Dict,
        agent_role: str,
        context: ConversationContext
    ) -> str:
        """使用模板生成回复（备用方案）"""
        
        emotion = emotion_analysis['primary_emotion']
        intensity = emotion_analysis['emotion_intensity']
        
        # 角色特定回复
        role_responses = {
            'listener': self._listener_response,
            'supporter': self._supporter_response,
            'coach': self._coach_response,
            'educator': self._educator_response,
            'mindfulness_guide': self._mindfulness_response
        }
        
        generator = role_responses.get(agent_role, self._listener_response)
        return generator(message, emotion, intensity, context)
    
    def _listener_response(self, message: str, emotion: str, intensity: int, context: ConversationContext) -> str:
        """倾听者角色回复"""

        # 共情表达 - 丰富模板
        empathies = {
            'sad': [
                "我听到你今天过得很不容易，能够说出来已经很勇敢了。💙",
                "谢谢你愿意分享你的感受。这种难过是很真实的，不需要压抑。",
                "我能感受到你心里的沉重，谢谢你信任我告诉我。",
                "难过的时候，有人陪伴会好很多。我在这里陪你。",
                "你的感受很重要，无论是悲伤还是其他情绪，我都愿意倾听。",
                "听起来你经历了不少事情。可以慢慢说，我在这里听着。",
                "我能够理解你现在的心情。每个人都会有低潮期，这很正常。",
                "感谢你愿意打开心扉。分享本身就是一种疗愈的开始。",
                "你的难过是真实的，不需要急着摆脱它。先让它被看见吧。",
                "我在这里，哪儿也不去。你可以放心地把心里的话说出来。"
            ],
            'anxious': [
                "我听到你很担心/焦虑。这种不安的感觉一定让你很难受。",
                "谢谢你说出来。担心是很正常的反应，我能理解。",
                "我能感受到你的紧张，先深呼吸一下，我们一起慢慢聊。",
                "焦虑的时候，脑子里可能会有很多担心的声音。这很正常。",
                "你愿意把担心说出来，这已经是迈出重要的一步了。",
                "我能感觉到你承受了不少压力。慢慢来，我们一起面对。",
                "对于未知的担忧是人之常情。你不是一个人在面对这些。",
                "先深呼吸。让我陪你一起理清这些烦心事。",
                "我能感受到你内心的不安。愿意说说是什么让你如此担心吗？",
                "焦虑只是在提醒我们需要更照顾好自己。这是一种自我保护。"
            ],
            'angry': [
                "我听到你很生气。这种愤怒的感受是完全可以理解的。",
                "谢谢你的分享。被人误解或不被尊重时，生气是很自然的反应。",
                "我能感受到你的不满，说出来是对的。",
                "愤怒是一种有力量的情绪，它在提醒我们某些界限被侵犯了。",
                "你有权利感到生气。重要的是我们如何健康地表达它。",
                "听起来发生了让你很不舒服的事情。能说说是什么吗？",
                "我能感受到你内心的火焰。愤怒有时是在保护我们珍视的东西。",
                "谢谢你愿意表达你的不满。这比把它闷在心里要好得多。",
                "我们不需要否定自己的愤怒，但可以学习如何与它共处。",
                "你的感受是合理的。有人让你受委屈了，对吗？"
            ],
            'happy': [
                "太棒了！听到你好消息我也跟着开心起来！🌟",
                "真好！你的快乐感染到我了！",
                "我能感受到你的开心！这是值得庆祝的时刻！",
                "太好了！我为你感到由衷的高兴！🎉",
                "听到你这么说，我也跟着心情好起来了！",
                "快乐的事情值得分享！谢谢你告诉我这个好消息。",
                "太棒了！继续保持着这份好心情吧！",
                "看到你开心，我也忍不住微笑了呢。😊",
                "这是多么美好的一天啊！为你感到高兴！",
                "你值得拥有这样的快乐！继续让美好发生！"
            ],
            'tired': [
                "我听到你很疲惫。辛苦了，你真的很不容易。💙",
                "谢谢你愿意承认自己累了。这不是软弱，是对自己诚实的觉察。",
                "我能感受到你的劳累。先好好休息一下吧。",
                "疲惫的时候，身体在提醒我们需要暂停和充电了。",
                "你已经很努力了。给自己一些休息的时间吧。",
                "我能感觉到你最近很辛苦。适当的休息不是偷懒。",
                "承认自己需要休息是一种智慧，而不是软弱。",
                "你不需要一直撑着。让我陪你一起度过这段疲惫期。",
                "累的时候，允许自己停下来很重要。",
                "好好照顾自己。身心健康一样重要。"
            ],
            'neutral': [
                "我在这里倾听你。愿意多说说吗？",
                "谢谢你分享。任何情绪都值得被看见。",
                "我在听。你最近过得怎么样？",
                "今天有什么想聊的吗？我随时都在。",
                "谢谢你愿意和我分享。告诉我你最近怎么样？",
                "我在这里陪你。任何话题都可以聊。",
                "愿意和我聊聊你现在的想法吗？",
                "我在认真听。你说吧，我听着呢。",
                "今天过得如何？有什么想分享的吗？",
                "感谢你的到来。有什么想聊的呢？"
            ]
        }

        # 选择共情表达
        empathy = random.choice(empathies.get(emotion, empathies['neutral']))

        # 根据对话深度添加后续 - 扩展版本
        follow_ups = [
            "愿意多说说发生了什么吗？",
            "我在这里陪你，你想说什么都可以。",
            "我会认真听你说的。",
            "你可以慢慢说，不着急。",
            "关于这件事，你想从哪里开始聊呢？",
            "我很好奇，能详细说说吗？",
            "听起来你有不少想法想分享。",
            "我愿意陪你一起梳理这些感受。",
            "你慢慢说，我认真听着呢。",
            "有什么是我可以帮到你的吗？"
        ]

        return empathy + "\n\n" + random.choice(follow_ups)
    
    def _supporter_response(self, message: str, emotion: str, intensity: int, context: ConversationContext) -> str:
        """支持者角色回复"""

        # 优势发现 - 扩展版本
        strength_statements = {
            'sad': [
                "虽然现在很难过，但你愿意寻求帮助，这本身就说明你很坚强。",
                "你能坚持到现在，本身就是一种勇气。",
                "你有能力度过难关，之前你也曾面对过困难并走了过来。",
                "难过只是暂时的，以后的你一定会感谢现在没有放弃的自己。",
                "你有权利难过，但别忘了你也有走出难过的力量。",
                "我相信你有能力重新找到内心的平静。",
                "每一次低谷都是成长的机会，你正在变得更强大。",
                "你的韧性超乎你的想象，之前那么难都过来了。",
                "即使现在看不到光，黎明也一定会到来。",
                "你比自己想象的更勇敢、更坚强。"
            ],
            'anxious': [
                "你的担心说明你在乎一些事情，这很正常。",
                "能觉察到自己的焦虑，这本身就是一种成长。",
                "你有能力面对未知的恐惧，你比想象中更强大。",
                "焦虑只是暂时的，它不能定义你是谁。",
                "一步一步来，你会发现担心的事情并没有那么可怕。",
                "你已经做得很好了，给自己一些肯定吧。",
                "未来还没发生，现在的你已经尽力了，这就足够了。",
                "我相信你有能力处理好这些事情。",
                "你的努力和准备会让你度过这个阶段的。",
                "不要被焦虑吓倒，你比它更强大。"
            ],
            'angry': [
                "你的愤怒说明你有自己的原则和底线，这很重要。",
                "你能清晰地表达自己的不满，这是一种能力。",
                "愤怒也是一种力量，关键是如何运用它。",
                "你有权利为自己发声，这没什么不对。",
                "我支持你维护自己的权益。",
                "你的感受是正当的，不需要为此道歉。",
                "把愤怒转化为动力，你可以创造积极的改变。",
                "你有能力用建设性的方式处理这种情绪。",
                "我理解你为什么会这么生气。",
                "你的愤怒告诉你什么是重要的，这很有价值。"
            ],
            'happy': [
                "你的积极能量真棒！继续保持！",
                "你值得拥有这样的快乐时光！",
                "太棒了！你的努力得到了回报！",
                "看到你这么开心，我也跟着高兴！",
                "你配得上这份快乐！好好享受吧！",
                "你的笑容真美！继续传递这份正能量吧！",
                "生活中美好的事情值得被珍惜和庆祝！",
                "你是一个能带来快乐的人！",
                "继续保持这份热情和积极吧！",
                "太为你高兴了！希望每天都这么美好！"
            ],
            'tired': [
                "承认自己需要休息是一种智慧。",
                "你已经在很努力地生活了，给自己一些宽容。",
                "照顾好自己也是很重要的事情。",
                "你不必每时每刻都保持最佳状态。",
                "给自己充充电，你值得一个喘息的机会。",
                "休息不是放弃，是为了走更远的路。",
                "我支持你给自己放个假。",
                "你已经很棒了，不需要逼迫自己太紧。",
                "好好休息，身体和心灵都需要恢复能量。",
                "允许自己停下来，这不是软弱。"
            ],
            'neutral': [
                "你是一个很有潜力的人，我对你有信心。",
                "相信自己的选择，你做得很好。",
                "每一天都是新的开始，带着希望前进吧。",
                "我支持你做出的任何决定。",
                "你有能力创造自己想要的生活。"
            ]
        }

        # 鼓励语句 - 扩展版本
        encouragements = [
            "我对你有信心，你一定可以度过这个阶段的。",
            "记住，你不是一个人在战斗。",
            "相信自己有应对困难的能力。",
            "你的努力和坚持我看到了。",
            "你比自己想象的更强大。",
            "我相信你能找到属于自己的答案。",
            "你的努力一定会有回报的。",
            "不要放弃，你离成功已经不远了。",
            "我为你感到骄傲。",
            "继续前进，光明就在前方等着你。",
            "你有能力克服任何挑战。",
            "相信过程相信自己的选择。",
            "每一次尝试都是成长的机会。",
            "你值得拥有最好的一切。",
            "坚持就是胜利，你做得很好。"
        ]

        statement = random.choice(strength_statements.get(emotion, strength_statements['neutral']))
        encouragement = random.choice(encouragements)

        return statement + "\n\n" + encouragement
    
    def _coach_response(self, message: str, emotion: str, intensity: int, context: ConversationContext) -> str:
        """教练角色回复"""
        
        # 启发式提问
        coaching_questions = {
            'sad': [
                "如果把你的难过写成一封信，你会写些什么？",
                "这段时间里，有没有什么事情是让你感到一丝安慰的？",
                "如果你的朋友遇到同样的情况，你会对他说什么？"
            ],
            'anxious': [
                "让你最担心的那件事，最坏的结果可能是什么？",
                "如果把担心的事情列出来，你会发现什么规律？",
                "有没有什么事情是你现在可以控制、可以做的？"
            ],
            'angry': [
                "当你生气时，身体有什么感觉？这能告诉你什么？",
                "对方可能有什么样的处境或难处？",
                "如果几年后再看这件事，你会有什么不同的看法？"
            ],
            'future': [
                "你希望半年后的自己是什么样子？",
                "为了实现那个目标，你可以迈出的第一步是什么？",
                "如果有一个理想的解决方案，那会是什么样的？"
            ]
        }
        
        # 检查场景关键词
        scenario = self._detect_scenario(message)
        if scenario in coaching_questions:
            questions = coaching_questions[scenario]
        else:
            questions = coaching_questions.get(emotion, [
                "你对这件事有什么看法？",
                "你想从中获得什么？",
                "如果事情可以改变，你希望怎么发展？"
            ])
        
        question = random.choice(questions)
        
        intro = random.choice([
            "我想邀请你思考一些问题：",
            "让我帮你梳理一下：",
            "或许我们可以一起看看："
        ])
        
        return intro + "\n\n" + question
    
    def _educator_response(self, message: str, emotion: str, intensity: int, context: ConversationContext) -> str:
        """教育者角色回复"""
        
        # 心理教育内容
        education = {
            'anxious': """关于焦虑，你需要知道：
            
焦虑是人类面对威胁时的正常反应。适度的焦虑可以帮助我们更好地应对挑战，但过度焦虑时，我们可以：

1. 身体的应对：深呼吸、放松肌肉
2. 思维的应对：识别过度担忧，挑战不合理的想法
3. 行为的应对：面对恐惧，逐步暴露

焦虑通常是暂时的，你可以尝试把担心的事情写下来，然后逐一分析。""",

            'angry': """关于愤怒，我们需要了解：

愤怒是一种保护性情绪，告诉我们某件事需要改变。但过度的愤怒会伤害我们自己和人际关系。

当你感到愤怒时：
1. 先停下来，深呼吸
2. 识别身体的感觉（心跳快、手抖等）
3. 问问自己：我在为什么而生气？这对我重要吗？
4. 寻找建设性的表达方式

你可以用运动、写日记等方式来释放愤怒的能量。""",

            'sad': """关于悲伤，让我们来理解：

悲伤是对失去的自然反应。无论失去的是一个人、一段关系、还是一个希望，悲伤都是正常的疗愈过程。

应对悲伤的建议：
1. 允许自己感受悲伤，不要压抑
2. 可以寻求支持，但不是依赖
3. 保持基本的日常规律
4. 给自己时间，疗愈需要过程
5. 必要时寻求专业帮助

悲伤不会永远持续，它会随着时间慢慢转化。"""
        }
        
        content = education.get(emotion, education.get('neutral', "我们可以一起学习更多关于情绪的知识。"))
        
        return content
    
    def _mindfulness_response(self, message: str, emotion: str, intensity: int, context: ConversationContext) -> str:
        """正念导师角色回复"""
        
        # 正念引导
        mindfulness_guides = {
            'anxious': """让我们一起做个放松练习：

【4-7-8呼吸法】
1. 吸气4秒，数着1、2、3、4...
2. 屏住呼吸7秒
3. 缓慢呼气8秒
4. 重复3-5次

感受空气从鼻子进来，慢慢充满腹部，然后慢慢呼出去...每一次呼吸都让自己更放松。""",

            'tired': """让我们一起休息一下：

【身体扫描放松】
找一个舒服的姿势...
先感受脚趾...放松...
慢慢向上，感受小腿...放松...
感受大腿、臀部...放松...
继续向上，感受腹部、胸口...每一次呼吸都让身体更放松...

如果有任何紧绷的地方，温柔地把注意力放在那里，深呼吸，让它放松...""",

            'sad': """现在，让我们给自己一个拥抱：

【自我关怀冥想】
闭上眼睛...
想象一个最疼爱你的人...
他/她正温柔地看着你...
对你说：你值得被爱，你很重要...
现在，把手放在自己的胸口...
给自己这样的温暖和关怀...
对自己说：我已经尽力了，我在努力...
我值得被善待..."""
        }
        
        return mindfulness_guides.get(emotion, mindfulness_guides.get('neutral', "让我们一起做个简单的呼吸练习...深呼吸，慢慢吸气...呼气..."))
    
    def _detect_scenario(self, message: str) -> str:
        """检测对话场景"""
        scenarios = {
            'work': ['工作', '上班', '老板', '同事', '加班', '职场'],
            'relationship': ['分手', '恋爱', '婚姻', '老公', '老婆', '女朋友', '男朋友'],
            'family': ['父母', '爸爸', '妈妈', '家人', '孩子', '家庭'],
            'study': ['学习', '考试', '考研', '学校', '论文'],
            'future': ['未来', '迷茫', '选择', '人生', '意义']
        }
        
        for scenario, keywords in scenarios.items():
            if any(k in message for k in keywords):
                return scenario
        
        return 'general'


class CrisisDetector:
    """危机检测器（保持原有功能）"""
    
    HIGH_RISK_KEYWORDS = [
        '自杀', '自伤', '想死', '不想活', '结束一切', '抹脖子', '上吊',
        '跳楼', '割腕', '安眠药', '氰化物', '活着没意义', '不想活了'
    ]
    
    MEDIUM_RISK_KEYWORDS = [
        '放弃', '绝望', '没用', '拖累', '不如死了', '一了百了',
        '解脱', '消失', '不存在', '没意思', '不想再'
    ]
    
    LOW_RISK_KEYWORDS = [
        '难过', '痛苦', '无助', '孤独', '绝望', '崩溃', '撑不住'
    ]
    
    HOTLINE = "400-161-9995"
    
    def detect(self, message: str) -> Tuple[str, bool, str]:
        """检测危机级别"""
        message_lower = message.lower()
        
        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in message_lower:
                return 'high', True, self._get_high_intervention()
        
        for keyword in self.MEDIUM_RISK_KEYWORDS:
            if keyword in message_lower:
                return 'medium', True, self._get_medium_intervention()
        
        count = sum(1 for k in self.LOW_RISK_KEYWORDS if k in message_lower)
        if count >= 2:
            return 'low', False, self._get_low_intervention()
        
        return 'none', False, ""
    
    def _get_high_intervention(self) -> str:
        return f"""💙 我感受到你正在经历非常困难的时刻。你的生命是宝贵的，请记住这一点。

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


class EnhancedLLMWrapper:
    """增强版LLM包装器，支持多种API"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.provider = self.config.get('provider', 'mock')
        self.api_key = self.config.get('api_key', '')
        self.api_base = self.config.get('api_base', '')
        self.model = self.config.get('model', 'default')
    
    async def chat(self, messages: List[Dict], system_prompt: str = None) -> str:
        """调用LLM生成回复"""
        
        if self.provider == 'mock':
            return await self._mock_chat(messages, system_prompt)
        elif self.provider == 'baidu':
            return await self._baidu_chat(messages, system_prompt)
        elif self.provider == 'openai':
            return await self._openai_chat(messages, system_prompt)
        elif self.provider == 'anthropic':
            return await self._anthropic_chat(messages, system_prompt)
        elif self.provider == 'chatglm':
            return await self._chatglm_chat(messages, system_prompt)
        else:
            return await self._mock_chat(messages, system_prompt)
    
    async def _mock_chat(self, messages: List[Dict], system_prompt: str) -> str:
        """模拟回复"""
        await asyncio.sleep(0.1)
        
        last_message = messages[-1]['content'] if messages else ""
        
        # 简单的关键词匹配回复
        responses = [
            "感谢你的分享。我听到你了。💙",
            "我理解你的感受。我们可以聊聊更多细节吗？",
            "谢谢你愿意告诉我这些。你现在感觉怎么样？",
            "我能感受到你今天过得不容易。愿意多说说吗？",
            "你很勇敢能把这些说出来。让我们一起看看可以怎么做。"
        ]
        
        return random.choice(responses)
    
    async def _baidu_chat(self, messages: List[Dict], system_prompt: str) -> str:
        """百度文心一言API"""
        import requests
        
        # 检查API密钥是否配置
        if not self.api_key or not self.config.get('api_secret'):
            print("百度API密钥未配置，使用Mock模式")
            return await self._mock_chat(messages, system_prompt)
        
        url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-lite-8k"
        
        # 构建消息
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)
        
        payload = {
            "messages": formatted_messages,
            "temperature": 0.8,
            "max_tokens": 500
        }
        
        try:
            # 先获取access_token
            token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.api_key}&client_secret={self.config.get('api_secret', '')}"
            token_response = requests.post(token_url)
            token_data = token_response.json()
            
            # 检查token获取是否成功
            if 'error_code' in token_data:
                print(f"百度Token获取失败: {token_data.get('error_msg', '未知错误')}")
                return await self._mock_chat(messages, system_prompt)
            
            access_token = token_data.get('access_token')
            if not access_token:
                print("百度Token获取失败")
                return await self._mock_chat(messages, system_prompt)
            
            # 调用API
            full_url = f"{url}?access_token={access_token}"
            response = requests.post(full_url, json=payload, timeout=30)
            result = response.json()
            
            # 检查API调用是否成功
            if 'error_code' in result:
                print(f"百度API调用失败: {result.get('error_msg', '未知错误')}")
                return await self._mock_chat(messages, system_prompt)
            
            return result.get('result', '谢谢你的分享。')
        except Exception as e:
            print(f"百度API调用异常: {e}")
            return await self._mock_chat(messages, system_prompt)
    
    async def _openai_chat(self, messages: List[Dict], system_prompt: str) -> str:
        """OpenAI API (包括兼容的API如硅基流动等)"""
        import requests
        
        # 检查API密钥是否配置
        if not self.api_key:
            print("OpenAI API密钥未配置，使用Mock模式")
            return await self._mock_chat(messages, system_prompt)
        
        # 避免URL重复 /v1/v1
        base = self.api_base.rstrip('/')
        if base.endswith('/v1'):
            url = f"{base}/chat/completions"
        else:
            url = f"{base}/v1/chat/completions"
        
        # 构建消息
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": 0.8,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            result = response.json()
            
            # 检查是否返回错误
            if 'error' in result:
                print(f"OpenAI API错误: {result['error'].get('message', '未知错误')}")
                return await self._mock_chat(messages, system_prompt)
            
            if 'choices' not in result or not result['choices']:
                print("OpenAI API返回为空")
                return await self._mock_chat(messages, system_prompt)
            
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"OpenAI API调用失败: {e}")
            return await self._mock_chat(messages, system_prompt)
            return await self._mock_chat(messages, system_prompt)
    
    async def _anthropic_chat(self, messages: List[Dict], system_prompt: str) -> str:
        """Anthropic Claude API"""
        import requests
        
        url = "https://api.anthropic.com/v1/messages"
        
        # 构建消息
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "user", "content": f"System: {system_prompt}\n\n"})
        formatted_messages.extend(messages)
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model or "claude-3-sonnet-20240229",
            "max_tokens": 500,
            "messages": formatted_messages
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            result = response.json()
            return result['content'][0]['text']
        except Exception as e:
            print(f"Anthropic API调用失败: {e}")
            return await self._mock_chat(messages, system_prompt)
    
    async def _chatglm_chat(self, messages: List[Dict], system_prompt: str) -> str:
        """ChatGLM本地模型API"""
        import requests
        
        url = f"{self.api_base}/v1/chat/completions"
        
        # 构建消息
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)
        
        payload = {
            "model": self.model or "chatglm3-6b",
            "messages": formatted_messages,
            "temperature": 0.8,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"ChatGLM API调用失败: {e}")
            return await self._mock_chat(messages, system_prompt)


class EnhancedEmoHealerAgent:
    """增强版EmoHealer AI智能体主类"""

    def __init__(self, config: Dict = None, db_session=None):
        self.config = config or {}
        self.db_session = db_session  # 数据库会话

        # 初始化各模块
        self.persona_manager = PersonaManager()
        self.emotion_analyzer = EmotionAnalyzer()
        self.crisis_detector = CrisisDetector()
        self.strategy = ConversationStrategy()

        # LLM配置
        llm_config = self.config.get('llm', {})
        self.llm = EnhancedLLMWrapper(llm_config)
        self.use_llm = self.config.get('use_llm', False)

        # 对话上下文缓存
        self.contexts: Dict[int, ConversationContext] = {}

    def load_history_from_db(self, user_id: int, limit: int = 10):
        """从数据库加载用户历史对话记录"""
        if not self.db_session:
            return []

        try:
            from src.models.models import ChatRecord
            from sqlalchemy import desc

            records = self.db_session.query(ChatRecord).filter(
                ChatRecord.user_id == user_id
            ).order_by(desc(ChatRecord.created_at)).limit(limit).all()

            # 反转顺序（从旧到新）
            history = []
            for record in reversed(records):
                history.append({
                    'role': 'user',
                    'content': record.user_message,
                    'timestamp': record.created_at.isoformat() if record.created_at else ''
                })
                if record.ai_reply:
                    history.append({
                        'role': 'assistant',
                        'content': record.ai_reply,
                        'timestamp': record.created_at.isoformat() if record.created_at else ''
                    })

            return history
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            return []
    
    def get_context(self, user_id: int) -> ConversationContext:
        """获取或创建对话上下文（从数据库加载历史记录）"""
        if user_id not in self.contexts:
            # 创建新的上下文并加载历史记录
            context = ConversationContext(user_id=user_id)
            # 加载最近10条对话历史
            history = self.load_history_from_db(user_id, limit=10)
            context.messages = history
            self.contexts[user_id] = context
        return self.contexts[user_id]
    
    def clear_context(self, user_id: int):
        """清除对话上下文"""
        if user_id in self.contexts:
            del self.contexts[user_id]
    
    async def chat(self, user_id: int, message: str, emotion: str = None, db_session=None) -> Dict:
        """
        处理用户对话
        返回包含AI回复和相关信息的字典
        """
        # 设置数据库会话用于加载历史记录
        if db_session:
            self.db_session = db_session

        # 获取上下文（会自动从数据库加载历史记录）
        context = self.get_context(user_id)

        # 记录用户消息
        context.messages.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })

        # ==================== RAG增强情绪分析 ====================
        if emotion is None:
            # 优先使用RAG模块进行更准确的分析
            if HAS_EMOTION_RAG and emotion_rag:
                rag_result = emotion_rag.analyze_emotion(message, {
                    'emotion_history': context.emotion_history,
                    'conversation_turn': context.conversation_turn
                })
                emotion = rag_result['primary_emotion']
                confidence = rag_result['confidence']
                triggers = rag_result.get('triggers', [])

                # 使用RAG的安全检查
                safety_check = rag_result.get('requires_immediate_support', False)
                if safety_check or rag_result.get('intensity', 0) >= 8:
                    # 重新进行安全检查
                    safety_result = emotion_rag._check_safety(message.lower()) if hasattr(emotion_rag, '_check_safety') else {'level': 0}
                    if safety_result.get('requires_intervention', False) or safety_result.get('level', 0) >= 3:
                        crisis_level = 'high'
                        crisis_message, _ = emotion_rag.get_safety_response(safety_result.get('level', 3))
                        needs_intervention = True
                        return {
                            'reply': crisis_message,
                            'emotion': emotion,
                            'confidence': confidence,
                            'is_crisis': True,
                            'crisis_level': crisis_level,
                            'triggers': triggers,
                            'agent_role': 'listener',
                            'timestamp': datetime.now().isoformat()
                        }
            else:
                # 回退到原有分析器
                emotion_analysis = self.emotion_analyzer.analyze(message, context)
                emotion = emotion_analysis['primary_emotion']
                confidence = emotion_analysis['emotion_intensity'] / 10
                triggers = emotion_analysis.get('emotion_triggers', [])
        else:
            confidence = 0.85
            triggers = []

        # 更新上下文
        context.current_emotion = emotion
        context.emotion_history.append({
            'emotion': emotion,
            'timestamp': datetime.now().isoformat()
        })

        # 检测危机（原有检测器作为备用）
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
                'agent_role': 'listener',
                'timestamp': datetime.now().isoformat()
            }
        
        # 生成回复
        if self.use_llm and self.llm.provider != 'mock':
            llm_provider = self.llm
        else:
            llm_provider = None
        
        result = await self.strategy.generate_response(
            message, emotion, context, llm_provider
        )

        # 记录AI回复
        context.messages.append({
            'role': 'assistant',
            'content': result['response'],
            'timestamp': datetime.now().isoformat()
        })

        # 获取知识库相关内容
        knowledge_tips = []
        if HAS_KNOWLEDGE_BASE and knowledge_base:
            kb_results = knowledge_base.search(message, emotion, max_results=1)
            for kb in kb_results:
                knowledge_tips.append({
                    'title': kb.get('title', ''),
                    'content': kb.get('content', ''),
                    'category': kb.get('category', '')
                })

        # 构建返回结果
        response_data = {
            'reply': result['response'],
            'emotion': result['emotion'],
            'confidence': result.get('emotion_intensity', confidence) / 10,
            'is_crisis': False,
            'crisis_level': 'none',
            'triggers': triggers,
            'agent_role': result.get('agent_role', 'listener'),
            'cognitive_pattern': result.get('cognitive_pattern'),
            'suggested_approach': result.get('suggested_approach'),
            'timestamp': datetime.now().isoformat()
        }

        # 添加知识库内容
        if knowledge_tips:
            response_data['knowledge_tips'] = knowledge_tips

        # 估算Token消耗（用于报表记录）
        prompt_text = message + (result.get('response', '') if isinstance(result, dict) else '')
        estimated_prompt_tokens = len(prompt_text) // 4  # 粗略估算
        estimated_completion_tokens = len(result.get('response', '') if isinstance(result, dict) else '') // 4

        response_data['token_usage'] = {
            'provider': self.llm.provider if hasattr(self, 'llm') else 'mock',
            'model': self.llm.model if hasattr(self, 'llm') else 'mock',
            'prompt_tokens': estimated_prompt_tokens,
            'completion_tokens': estimated_completion_tokens,
            'total_tokens': estimated_prompt_tokens + estimated_completion_tokens,
            'cost': (estimated_prompt_tokens + estimated_completion_tokens) * 0.0001,  # 粗略估算成本
            'response_time': 0
        }

        return response_data
    
    def set_llm_config(self, provider: str, api_key: str = "", api_base: str = "", model: str = ""):
        """动态配置LLM"""
        self.llm = EnhancedLLMWrapper({
            'provider': provider,
            'api_key': api_key,
            'api_base': api_base,
            'model': model
        })
        self.use_llm = (provider != 'mock')
    
    def enable_llm(self, provider: str = "baidu", **kwargs):
        """启用LLM"""
        self.set_llm_config(provider, **kwargs)
    
    def disable_llm(self):
        """禁用LLM"""
        self.use_llm = False
        self.llm = EnhancedLLMWrapper({'provider': 'mock'})


# 创建全局AI智能体实例（从ai_config.py加载配置）
llm_config = AI_CONFIG.get("llm", {}).get(AI_CONFIG.get("llm_provider", "mock"), {})
enhanced_ai_agent = EnhancedEmoHealerAgent(config={
    'use_llm': AI_CONFIG.get("use_llm", False),
    'llm': {
        'provider': AI_CONFIG.get("llm_provider", "mock"),
        'api_key': llm_config.get("api_key", ""),
        'api_secret': llm_config.get("api_secret", ""),
        'api_base': llm_config.get("api_base", "http://localhost:8000"),
        'model': llm_config.get("model", "gpt-3.5-turbo")
    }
})
