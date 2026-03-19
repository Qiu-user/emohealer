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

# 导入资源推荐模块
try:
    from src.services.resource_recommender import resource_recommender
    HAS_RESOURCE_RECOMMENDER = True
except ImportError:
    HAS_RESOURCE_RECOMMENDER = False
    resource_recommender = None


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
    # 新增：追踪用户反复提到的话题
    topic_history: List[Dict] = field(default_factory=list)  # [{"topic": "辞职", "count": 3, "last_mentioned": "..."}]


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
        
        # 构建话题关注信息
        topic_context = ""
        if context.conversation_turn >= 2:
            repeated_topics = [t for t in context.topic_history if t.get('count', 0) >= 2]
            if repeated_topics:
                repeated_topics.sort(key=lambda x: x.get('count', 0), reverse=True)
                top_topic = repeated_topics[0]
                topic_context = f"""
## 话题关注
用户反复提到的话题：{top_topic['topic']}（已提到{top_topic['count']}次）
请在回复中适当体现你注意到了这个问题，表达关心。
"""
        
        emotion_context = f"""
用户当前情绪：{emotion_analysis['primary_emotion']}
情绪强度：{emotion_analysis['emotion_intensity']}/10
可能的认知模式：{emotion_analysis.get('cognitive_pattern', '无')}
建议的应对方式：{emotion_analysis.get('suggested_approach', '')}
{topic_context}
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
        response = await llm_provider.chat([
            {"role": "user", "content": full_prompt}
        ])

        return response
    
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
        # 获取角色回复
        response = generator(message, emotion, intensity, context)

        return response
    
    def _listener_response(self, message: str, emotion: str, intensity: int, context: ConversationContext) -> str:
        """倾听者角色回复 - 增强版"""

        # ========== 智能话题识别 ==========
        topic_keywords = {
            '工作': ['工作', '上班', '加班', '辞职', '跳槽', '老板', '领导', '同事', '职场', '工资', '面试', '实习'],
            '感情': ['分手', '恋爱', '男朋友', '女朋友', '喜欢', '告白', '婚姻', '相亲', '离婚', '复合', '异地'],
            '学习': ['考试', '考研', '学习', '成绩', '挂科', '作业', '论文', '毕业', '专业', '学校'],
            '家庭': ['父母', '家人', '妈妈', '爸爸', '孩子', '亲子', '原生家庭', '亲戚'],
            '健康': ['失眠', '焦虑', '抑郁', '身体', '医院', '生病', '减肥', '睡眠'],
            '社交': ['朋友', '孤独', '社恐', '人际', '社交'],
            '金钱': ['钱', '欠款', '贷款', '房贷', '债务', '理财', '省钱']
        }

        # 识别用户消息中的话题
        detected_topics = []
        msg_lower = message.lower()
        for topic, keywords in topic_keywords.items():
            for kw in keywords:
                if kw in msg_lower:
                    detected_topics.append(topic)
                    break

        # 话题个性化共情 - 增强版（更长更丰富）
        topic_empathies = {
            '工作': [
                "职场中的压力真的很不容易，我能理解你现在的感受。工作占据了我们大部分时间，当它出现问题时，那种无力感会蔓延到生活的方方面面。\n\n你已经坚持这么久了，这本身就很不容易。有时候能够撑下去，本身就是一种勇气。你有没有想过，目前的工作中最让你感到压力的具体是什么？是工作量太大，还是人际关系，亦或是对未来的迷茫？\n\n我想听听你的想法，我们可以一起慢慢理清。",
                "听起来工作给你带来了不小的困扰。现代职场确实充满挑战，无论是业绩压力、职场关系还是工作与生活的平衡，都可能让人喘不过气来。\n\n你愿意和我多说说具体是什么情况吗？是遇到了什么具体的事情，还是一种持续的状态？有时候把困扰说出来，本身就是一种疗愈。\n\n无论是什么，我都在这里认真听你说。",
                "工作上的烦恼真的很消耗人。当你全身心投入却感觉没有回报时，那种失落感会让人怀疑自己价值。你现在对目前的工作是什么感受呢？\n\n其实，能在困难中坚持寻求帮助，本身就说明你在乎自己的生活品质，这已经很棒了。愿意多说说吗？"
            ],
            '感情': [
                "感情的事确实最让人牵肠挂肚。爱情、亲情、友情，每一种关系都需要我们付出心力，而当这些关系出现问题时，受伤的往往是我们最柔软的地方。\n\n我理解这种感觉。你愿意说说发生了什么吗？无论是什么，我都会认真倾听，不带评判。\n\n有时候，倾诉本身就是一种很好的疗愈方式。",
                "感情的波折确实会让人感到心痛和迷茫。无论是一段关系的结束，还是与重要他人之间的矛盾，都会给我们带来深深的困扰。\n\n我能感觉到你心里有些不太平静。如果你愿意的话，可以多说说具体是什么让你感到难过吗？\n\n不管结果如何，记住：你值得被爱，值得被好好对待。",
                "我理解感情中的复杂感受。有时候爱一个人很容易，但相处却需要更多的智慧和耐心。你现在心里是什么滋味呢？\n\n无论你正在经历什么，记住你不是一个人。我在这里愿意倾听你的故事。"
            ],
            '学习': [
                "学习压力真的很大，尤其是当成绩不如预期时，那种失落感会让人质疑自己的努力是否有意义。我想告诉你，你的感受是完全正常的。\n\n考试只是人生中的一个环节，但它确实会给人带来很大的压力。你愿意说说是什么让你感到困扰吗？是这次考试的结果，还是对未来的担忧？\n\n无论是什么，我都想听听你的想法。",
                "学业之路从来都不是一帆风顺的，每个人都会遇到挫折和困难。你能坚持到现在，说明你内心有一股不服输的力量。\n\n最近学习上有什么让你感到烦恼的吗？是考试压力、作业负担，还是对未来的规划感到迷茫？\n\n说出来，我们一起聊聊。",
                "学习中的起起落落是很正常的。我知道当你投入了大量时间和精力却没能得到预期结果时，会有多沮丧。但我想说，你的价值不仅仅体现在成绩上。\n\n你愿意多说说最近学习上发生了什么吗？或者我们聊聊你现在最担心的事情？"
            ],
            '家庭': [
                "家庭是我们最温暖的港湾，但有时候也是最深的羁绊。家人之间的关系往往复杂而微妙，这种复杂性只有身处其中的人才能真正体会。\n\n我愿意倾听你关于家庭的故事。你最近和家庭成员之间有什么让你感到困扰的吗？\n\n无论是什么，都可以和我说说。",
                "家人之间的关系确实需要很多理解和沟通。每个人都有自己的立场和难处，有时候出发点是好的，但表达方式可能让人难以接受。\n\n你愿意说说发生了什么吗？我想听听你对这件事的感受。\n\n有时候，把心里的委屈和困惑说出来，本身就是一种疗愈。",
                "家是每个人最牵挂的地方，也是最容易被触动情绪的地方。我能理解家庭关系可能给你带来的困扰。\n\n你最近有和家人之间有什么事情让你感到不太舒服吗？或者有没有什么一直放在心里没说出口的话？\n\n我在这里认真听你说。"
            ],
            '健康': [
                "身体是我们最重要的资产，当它发出警报时，确实会让人感到焦虑和不安。健康问题不仅影响身体，也会影响我们的情绪和生活品质。\n\n你愿意说说最近身体状况怎么样吗？有什么具体的困扰吗？\n\n我虽然不是医疗专业人士，但我可以倾听你的感受，陪你一起面对。",
                "当身体不舒服时，整个世界都会变得不那么美好。我能理解你对健康的担忧，这种担心是很正常的。\n\n你最近身体有什么让你困扰的地方吗？是睡眠问题、精力不足，还是其他什么情况？\n\n说说看，也许说出来会好一些。",
                "健康问题确实不容忽视，尤其是当它影响到我们的日常生活时。我理解这可能让你感到焦虑。\n\n你愿意说说具体是什么情况吗？无论是身体的不适，还是对健康的担忧，都可以和我聊聊。\n\n有时候倾诉也是一种缓解焦虑的方式。"
            ],
            '社交': [
                "人际关系是我们生活中很重要的一部分，但也是最容易让人感到疲惫的。当我们在意别人的看法，或者感到被误解时，那种无力感会让人想要逃避。\n\n你最近在社交方面有什么困扰吗？是和朋友的相处，还是更广泛的人际交往？\n\n我愿意听听你的故事。",
                "社交的复杂之处在于，它涉及到那么多的人和情感。有时候明明很在意一段关系，却不知道如何表达；有时候明明想要融入，却感觉格格不入。\n\n你愿意说说最近在社交方面有什么让你感到困扰的吗？\n\n无论是什么，我都在这里认真倾听。",
                "我知道人际关系有时会让人感到疲惫和困惑。无论是与朋友的相处、与同事的互动，还是更广泛的社交场合，都可能带来各种挑战。\n\n你最近有遇到什么让你感到不舒服的社交情况吗？或者有没有什么人际困扰一直萦绕在你心头？\n\n说出来，也许我们可以一起理清。"
            ],
            '金钱': [
                "经济压力确实会给人带来很大的心理负担。钱虽然不是万能的，但它直接关系到我们的生活质量和安全感。\n\n你愿意说说最近在经济方面有什么让你感到困扰的吗？是日常开销的压力，还是更大的财务挑战？\n\n我愿意倾听你的故事。",
                "金钱问题确实会让人夜不能寐。我理解当经济状况紧张时，那种焦虑和无助感会渗透到生活的方方面面。\n\n你愿意说说是什么让你感到经济上有压力吗？有时候，把问题说出来本身就是一种缓解。\n\n无论是什么情况，我都在这里陪着你。",
                "理财压力是很多人都在面对的问题。我能理解当入不敷出或者为未来担忧时，那种紧迫感会让人喘不过气来。\n\n你最近在金钱方面有什么具体的困扰吗？是债务压力、收支不平衡，还是对未来的财务规划感到迷茫？\n\n说说看，我在这里认真听你说。"
            ]
        }

        # 根据话题选择个性化回复
        if detected_topics:
            primary_topic = detected_topics[0]
            empathy = random.choice(topic_empathies.get(primary_topic, [
                "我听到你了。愿意多说说吗？",
                "谢谢你分享。我在这里认真听你说。",
                "我能理解你的感受。慢慢说，不着急。"
            ]))
            follow_ups = [
                f"关于{primary_topic}，有什么特别想聊的吗？",
                f"能具体说说{primary_topic}方面的情况吗？",
                f"你希望怎么看待{primary_topic}这个问题呢？",
                f"除了{primary_topic}，还有其他困扰你的事情吗？",
                f"你有没有尝试过什么方法来应对{primary_topic}的问题？"
            ]
            return empathy + "\n\n" + random.choice(follow_ups)

        # 共情表达 - 丰富模板
        empathies = {
            'sad': [
                "我听到你今天过得很不容易，能够说出来已经很勇敢了。难过是一种很真实的情绪，它在提醒我们需要被关爱、被看见。你不需要强迫自己坚强，也不需要假装没事。\n\n谢谢你能把这些感受告诉我。我在这里陪着你，无论这个低落的状态持续多久，都没关系的。\n\n你愿意多说说是什么让你感到难过吗？我想更了解你的感受。",

                "谢谢你愿意分享你的感受。这种难过是很真实的，不需要压抑，也不需要急着摆脱它。每个人都会有情绪低落的时刻，这并不代表你脆弱或软弱。\n\n我能感受到你心里的沉重。愿意说说是什么触发了这些感受吗？或者只是让我知道你现在需要什么。\n\n我在这里，哪儿也不去。",

                "我能理解你现在可能经历着很深的难过。无论是失去了什么，还是对现状感到无力，这种感受都是人之常情。\n\n我想让你知道，你的感受是被看见的、被承认的。不需要急着好起来，慢慢来。\n\n你愿意多说说吗？我想听听你的故事。",

                "听到你经历这些，我心里也很心疼。难过的时候，有人陪伴会好很多。虽然我不能完全感同身受，但我可以陪在你身边，倾听你的心声。\n\n你现在感觉怎么样？有什么是你想说的吗？\n\n我会认真听你说的。",

                "你一定经历了很多，才能说出这些话。我想让你知道，你的感受很重要，无论它是悲伤、失落还是其他什么情绪。\n\n有时候，把心里的话说出来，本身就是一种疗愈。不需要组织语言，想怎么说就怎么说。\n\n我在这里准备好倾听了。"
            ],
            'anxious': [
                "我听到你很担心/焦虑。这种不安的感觉一定让你很难受，对吧？焦虑是一种很常见的情绪，它在提醒我们有些事情需要我们关注和面对。\n\n先深呼吸一下。你愿意说说是什么让你感到如此焦虑吗？可能是工作、学业、人际关系，或者是对未来的不确定性？\n\n无论是什么，我都在这里陪你。",

                "谢谢你愿意把担心说出来。担心是很正常的反应，我能理解你的紧张。当我们感到无法掌控某些事情时，焦虑自然会涌上心头。\n\n我想先邀请你做几次深呼吸。慢慢地吸气，慢慢地呼气。让自己的身体先放松下来。\n\n现在，你愿意告诉我是什么让你感到焦虑吗？",

                "我能感受到你内心的不安。焦虑的时候，脑子里可能会有很多担心的声音，这些想法像漩涡一样把我们卷进去。你不是一个人，很多人都有过类似的感受。\n\n你愿意说说最让你担心的是什么吗？有时候，把担心的事情说出来，能够帮助我们看得更清楚。\n\n我在这里认真听你说。",

                "先深呼吸一下。我知道你可能感到很紧张，这种感觉真的很不好受。焦虑会影响我们的身体和心情，但它是可以被管理和缓解的。\n\n你最近是不是遇到了什么让你特别担心的事情？或者是很多事情累积在一起让你喘不过气？\n\n说说看，也许说出来会好受一些。",

                "我能感觉到你承受了不少压力。焦虑时，我们的身体会紧绷，脑子会转个不停，像是一直在试图解决什么问题。\n\n你愿意说说是什么在困扰你吗？也许我们可以一起理清这些让你担心的事情。\n\n记住，你不需要独自面对一切。我在这里陪你。"
            ],
            'angry': [
                "我听到你很生气。这种愤怒的感受是完全合理的，当我们的边界被侵犯、期望被辜负、或者受到不公平对待时，生气是很自然的反应。\n\n你有权利感到愤怒。重要的是，我们如何健康地表达和处理这种情绪。\n\n你愿意说说是什么让你这么生气吗？我想听听发生了什么事。",

                "谢谢你愿意表达你的不满。被人误解或不被尊重时，生气是很正常的反应。我能感觉到你内心的火焰。\n\n愤怒是一种有力量的情绪，它在提醒我们某些界限被侵犯了，或者某些需求没有被满足。\n\n你愿意告诉我是什么触发了你的愤怒吗？有时候，理清愤怒的来源能帮助我们更好地应对它。",

                "我能感受到你的不满和挫败感。当事情没有按我们期望的方式发展时，愤怒自然会涌上来。这种感受是完全可以理解的。\n\n你愿意说说发生了什么吗？是什么让你感到如此沮丧和愤怒？\n\n我会认真听你说的，不带评判。",

                "你有权利感到生气。有些事情确实值得让人愤怒，比如不公平、比如被伤害、比如期望落空。愤怒本身并不是坏事，关键是我们如何与它相处。\n\n你愿意告诉我是什么让你这么愤怒吗？也许我们可以一起看看怎么更好地应对这种情况。\n\n我在这里倾听你。"
            ],
            'happy': [
                "太棒了！听到你开心的消息，我真的很为你高兴！积极的情绪是值得被庆祝的，你的快乐也感染到了我。\n\n发生了什么好事吗？我想听听让你这么开心的故事！\n\n希望你今天能一直保持这份好心情！",

                "真好！你的好消息让我也跟着开心起来！快乐是会传染的，你的笑容真的很有感染力。\n\n有什么特别的事情让你这么开心吗？或者你就是单纯地感到幸福？\n\n无论是哪种，我都为你感到高兴！继续让这份美好的感觉延续下去吧！",

                "太好了！我由衷地为你感到开心！听到你分享好消息，真的是一件很美好的事情。\n\n你最近是不是遇到了什么值得庆祝的事情？还是说一切都进展得很顺利？\n\n希望你能把这份快乐延续下去！",

                "太棒了！你的积极能量真的很感染人！我真替你感到高兴！\n\n有时候好事就是这样不期而至，让我们的生活充满了惊喜和温暖。你有什么想分享的吗？\n\n继续保持这份好心情！"
            ],
            'tired': [
                "我听到你很疲惫。辛苦了，你真的很不容易。疲惫的时候，身体和心灵都在发出需要休息的信号。\n\n你最近是不是太拼了？无论是工作、学习还是生活中的各种责任，有时候我们会忘记照顾自己。\n\n你愿意说说是什么让你感到这么累吗？身体上的疲惫还是心灵上的劳累？\n\n希望你能给自己一些喘息的时间和空间。",

                "谢谢你愿意承认自己需要休息。这不是软弱，是对自己诚实的觉察。当你能够意识到自己的极限并尊重它时，这本身就是一种智慧。\n\n我在这里陪你。你现在感觉怎么样？有什么你想说的吗？\n\n记得，你不需要一直撑着。",

                "我能感受到你的劳累。生活中的种种责任和压力，有时候真的会让人喘不过气来。\n\n你愿意说说是什么让你感到这么疲惫吗？是工作太辛苦，还是心里装着太多事情？\n\n好好照顾自己。身心健康一样重要。",

                "你已经很努力了。疲惫是身体在提醒我们需要暂停和充电，这是一种自我保护的机制。\n\n你愿意聊聊是什么让你感到这么累吗？也许说出来能让你感觉轻松一些。\n\n给自己一些宽容和休息的时间吧。",

                "我理解这种疲惫感。当我们一直在付出、在努力，却忘了给自己充电时，很容易就会陷入这种枯竭的状态。\n\n你最近是不是承担了很多？有什么你可以放下的事情吗？或者有什么能让你恢复能量的方式？\n\n我在这里陪你一起度过这段疲惫期。"
            ],
            'neutral': [
                "谢谢你今天来看我。无论你带着什么样的心情来，我都很高兴你在这里。\n\n你最近过得怎么样？有什么想和我聊的吗？\n\n我随时都在，准备好倾听你的故事。",

                "我在这里陪伴你。任何你想说的话，任何你想分享的事情，我都很愿意听。\n\n今天有什么在你心上的吗？或者我们聊聊最近发生在你身上的事情？",

                "欢迎你来。我希望这里是一个你可以放松、可以做自己的地方。\n\n你今天感觉怎么样？有什么想法想要分享吗？\n\n我在这里认真听你说。",

                "你好。谢谢你愿意来这里和我聊聊。\n\n最近有什么让你开心的事情吗？或者有什么让你烦恼的？我想听听你的故事。\n\n我随时都在。",

                "我在这里等你。无论你想说什么，无论你的心情如何，我都很愿意倾听。\n\n你最近怎么样？有什么想要聊的吗？\n\n不用着急，慢慢说就好。"
            ]
        }

        # 选择共情表达
        empathy = random.choice(empathies.get(emotion, empathies['neutral']))

        # 根据对话深度添加后续 - 扩展版本
        follow_ups = [
            "愿意多说说发生了什么吗？我想更了解你的情况。",
            "我在这里陪你，你想说什么都可以，不着急。",
            "我会认真听你说的。有什么细节想分享吗？",
            "你可以慢慢说，不需要组织语言。",
            "关于这件事，你最想让我理解的是什么？",
            "有什么是我可以帮到你的吗？或者你只是需要有人倾听？",
            "这种感受持续多久了？是什么时候开始的？",
            "你有没有和身边的人分享过这些感受？",
            "是什么让你有这样的感受呢？愿意多说一些吗？",
            "你有没有尝试过什么方法来应对这种情况？"
        ]

        return empathy + "\n\n" + random.choice(follow_ups)
    
    def _supporter_response(self, message: str, emotion: str, intensity: int, context: ConversationContext) -> str:
        """支持者角色回复 - 增强版"""

        # 优势发现 - 扩展版本
        strength_statements = {
            'sad': [
                "虽然现在很难过，但你愿意寻求帮助，这本身就说明你很坚强。难过时还能伸出手求助，这需要很大的勇气。\n\n想想看，你已经在黑暗中走了这么久，还没有放弃，这本身就是一种了不起的力量。你比你以为的更加强大。\n\n我相信你有能力重新找到内心的平静，重新拥抱生活的美好。",

                "你能坚持到现在，本身就是一种勇气。每个人都会经历低谷，但并不是每个人都能像你这样勇敢地面对。\n\n你知道吗？那些杀不死你的，终会让你变得更强大。这次的困难也会成为你成长的养分。\n\n给自己一些时间和耐心，你一定会走出来的。",

                "你有能力度过难关，之前你也曾面对过困难并走了过来。想想那些曾经你以为过不去的坎，现在回头看，是不是都已经成为过去了？\n\n这次也一样。你有战胜困难的经验，有面对挑战的勇气，有支持你的人。\n\n黎明前最黑暗，但太阳一定会升起。",

                "难过只是暂时的，以后的你一定会感谢现在没有放弃的自己。我知道现在很痛苦，但请相信，这只是人生旅程中的一个阶段，而不是终点。\n\n你的韧性超乎你的想象。你已经走过了那么多风雨，这次也一定可以。\n\n我会一直在这里陪着你，直到你重新找到笑容。",

                "你有权利难过，但别忘了你也有走出难过的力量。悲伤是一种正常的情绪，它不应该被压抑，也不应该被忽视。\n\n但同时，也请相信自己的恢复能力。你有这么多优点，有这么多人关心你，有这么多值得期待的事情。\n\n让我们一起努力，好吗？"
            ],
            'anxious': [
                "你的担心说明你在乎一些事情，这很正常。焦虑并不全是坏事，它说明你有责任感，有对未来的期待。\n\n重要的是不要被焦虑控制，而是学会与它共处。你已经做得很好了，已经尽力了。\n\n一步一步来，你会发现自己比想象中更有能力应对这些挑战。",

                "能觉察到自己的焦虑，这本身就是一种成长。很多人身陷焦虑却不自知，而你已经在寻求帮助了，这很棒。\n\n焦虑只是暂时的，它不能定义你是谁。你是一个有价值、有能力的人。\n\n我相信你有力量走出这片阴霾，重新找到内心的平静。",

                "你有能力面对未知的恐惧，你比想象中更强大。想想看，你已经成功应对过那么多挑战，这次也一定可以。\n\n未来还没发生，我们不需要为还没发生的事过度担忧。现在能做的，就是做好眼前的事。\n\n给自己一些信心，你真的比你以为的更强大。",

                "焦虑只是暂时的，它不会永远持续。每个人的一生中都会有焦虑的时刻，但它最终都会过去。\n\n你已经做得很好了，给自己一些肯定吧。你愿意承认自己的焦虑并寻求帮助，这已经是迈出了重要的一步。\n\n我会一直在这里支持你，直到你重新找回内心的安宁。",

                "不要被焦虑吓倒，你比它更强大。焦虑就像一片乌云，虽然会遮住阳光，但永远不会让阳光消失。\n\n你的努力和准备会让你度过这个阶段的。每一次你成功应对焦虑，都是在告诉自己：我有能力面对困难。\n\n相信自己，你一定可以的。"
            ],
            'angry': [
                "你的愤怒说明你有自己的原则和底线，这很重要。愤怒并不是坏情绪，它是正义感的体现，是自我保护的信号。\n\n重要的是你如何表达和处理这种情绪。你能意识到自己的愤怒并愿意面对它，这本身就很了不起。\n\n我相信你有能力用建设性的方式处理这种情绪，甚至将它转化为前进的动力。",

                "你能清晰地表达自己的不满，这是一种能力。很多人在愤怒时选择沉默或压抑，而你愿意说出来，这需要勇气。\n\n愤怒也是一种力量，关键是如何运用它。你可以把愤怒转化为改变的动力，让它推动你创造更美好的生活。\n\n你的感受是正当的，不需要为此道歉。",

                "你有权利为自己发声，这没什么不对。当我们的边界被侵犯时，愤怒是一种自然的反应。\n\n我支持你维护自己的权益。同时，也希望你能找到健康的方式来表达愤怒，比如运动、写日记，或者和朋友倾诉。\n\n你是一个有力量的人，你的声音值得被听见。",

                "愤怒告诉你什么是重要的，这很有价值。每一种情绪都在传递信息，愤怒告诉你有些事情需要改变。\n\n我理解你为什么会这么生气。能对不公平的事感到愤怒，说明你是一个有正义感、有情感的人。\n\n让我们一起看看怎么用积极的方式来处理这份愤怒，让它成为改变的起点。",

                "你有能力用建设性的方式处理这种情绪。愤怒是人之常情，但我们可以用智慧来引导它。\n\n把愤怒转化为动力，去做些积极的事情，或者去改变那些可以改变的。这样不仅能缓解你的愤怒，还能让你收获更多。\n\n我在这里支持你。你不是一个人在战斗。"
            ],
            'happy': [
                "你的积极能量真棒！继续保持！你的快乐不仅照亮了自己的生活，也感染着身边的每一个人。\n\n太棒了！你的努力得到了回报！每一份付出都不会白费，你值得拥有这份成功的喜悦。\n\n希望你能记住这种感觉，让它成为你面对困难时的力量源泉。",

                "你值得拥有这样的快乐时光！美好的事情值得被珍惜和庆祝，而你的努力让你配得上这一切。\n\n看到你这么开心，我也跟着高兴！你的笑容真的很有感染力。\n\n继续保持这份好心情，同时也不要忘记分享你的快乐给身边的人哦！",

                "太好了！我为你感到由衷的高兴！生活中能够有开心的时刻，真的是一件很美好的事情。\n\n你的笑容真美！继续传递这份正能量吧，它会让你身边的人也跟着开心起来。\n\n太为你高兴了！希望每天都这么美好！",

                "你配得上这份快乐！看到你这么开心，我也忍不住为你感到幸福。\n\n你是一个能带来快乐的人！你的积极能量不仅让自己受益，也温暖着身边的每一个人。\n\n继续保持这份热情和积极吧！希望这份好心情能一直延续下去。"
            ],
            'tired': [
                "承认自己需要休息是一种智慧，而不是软弱。当我们能够觉察到自己的极限并尊重它时，这才是真正的强大。\n\n你已经在很努力地生活了，给自己一些宽容吧。你不必每时每刻都保持最佳状态。\n\n好好照顾自己。身心健康一样重要，缺一不可。",

                "你不必每时每刻都保持最佳状态。疲惫是身体在提醒我们需要暂停和充电，这是一种自我保护的机制。\n\n给自己充充电吧，你值得一个喘息的机会。休息不是放弃，而是为了走更远的路。\n\n我支持你照顾好自己。你已经很棒了，不需要逼迫自己太紧。",

                "好好休息，身体和心灵都需要恢复能量。每个人都会有疲惫的时候，这不代表你不够努力，而是说明你在认真地生活。\n\n允许自己停下来吧，这不是软弱。休息是为了更好地出发。\n\n我会一直在这里，等你休息好了，我们再继续。",

                "你已经很棒了，不需要逼迫自己太紧。生活中的种种责任和压力，有时候会让我们忘记照顾自己。\n\n但请记住，只有照顾好自己，才能更好地照顾别人，才能更好地面对生活的挑战。\n\n给自己一些时间和空间，好好休息一下吧。你值得被善待。",

                "允许自己停下来，这不是软弱。每个人都有自己的极限，尊重这个极限是自爱的表现。\n\n你最近是不是承担了很多？也许可以试着放下一些不那么重要的事情，给自己一些喘息的机会。\n\n我在这里支持你。无论你需要休息还是需要倾诉，我都在这里陪着你。"
            ],
            'neutral': [
                "你是一个很有潜力的人，我对你有信心。每个人都有自己的闪光点，只是有时候我们需要时间去发现它们。\n\n相信自己的选择，你做得很好。每一天都是新的开始，带着希望前进吧。\n\n我支持你，相信你一定可以创造自己想要的生活。",

                "相信自己的选择，你做得很好。人生没有标准答案，每个人都在摸索中前进。\n\n我支持你做出的任何决定。无论你选择什么，我都会在这里为你加油。\n\n你有能力创造自己想要的生活。我相信你。",

                "每一天都是新的开始，带着希望前进吧。无论昨天发生了什么，今天都是一个新的机会。\n\n你有能力成为自己想成为的人，过上自己想要的生活。这需要时间和努力，但只要你坚持下去，就一定可以实现。\n\n我为你感到骄傲，期待看到你绽放的样子。",

                "你有力量面对生活中的挑战。我相信你的能力和智慧。\n\n不要害怕犯错，因为错误也是成长的一部分。重要的是从错误中学习，继续前进。\n\n我支持你，相信你会找到属于自己的答案和道路。"
            ]
        }

        # 鼓励语句 - 扩展版本
        encouragements = [
            "我对你有信心，你一定可以度过这个阶段的。记得，你比自己想象的更强大。",
            "记住，你不是一个人在战斗。我会一直在这里陪着你，支持你。",
            "相信自己有应对困难的能力。你已经成功克服过那么多挑战，这次也一样。",
            "你的努力和坚持我都看到了。继续前进，你离目标越来越近了。",
            "你比自己想象的更强大。不要小看自己的潜力，你有无尽的可能。",
            "我相信你能找到属于自己的答案。每个人都有自己的道路，你要相信自己的选择。",
            "你的努力一定会有回报的。也许回报还没到，但请相信它一定在路上。",
            "不要放弃，你离成功已经不远了。再坚持一下，光明就在前方。",
            "我为你感到骄傲。你能走到今天已经很了不起了。",
            "继续前进，光明就在前方等着你。每一步都是在向更好的自己靠近。",
            "你有能力克服任何挑战。不要害怕困难，它只是成长的机会。",
            "相信过程相信自己的选择。每一步都有意义，每一天都在进步。",
            "每一次尝试都是成长的机会。无论结果如何，你都在变得更好。",
            "你值得拥有最好的一切。相信自己，你配得上美好的生活。",
            "坚持就是胜利，你做得很好。成功从来不是一蹴而就的，你已经很棒了。"
        ]

        statement = random.choice(strength_statements.get(emotion, strength_statements['neutral']))
        encouragement = random.choice(encouragements)

        return statement + "\n\n" + encouragement
    
    def _coach_response(self, message: str, emotion: str, intensity: int, context: ConversationContext) -> str:
        """教练角色回复"""

        # 智能话题识别
        topic_keywords = {
            '工作': ['工作', '上班', '加班', '辞职', '跳槽', '老板', '领导', '同事', '职场', '工资', '面试', '实习'],
            '感情': ['分手', '恋爱', '男朋友', '女朋友', '喜欢', '告白', '婚姻', '相亲', '离婚', '复合', '异地'],
            '学习': ['考试', '考研', '学习', '成绩', '挂科', '作业', '论文', '毕业', '专业', '学校'],
            '家庭': ['父母', '家人', '妈妈', '爸爸', '孩子', '亲子', '原生家庭', '亲戚'],
            '健康': ['失眠', '焦虑', '抑郁', '身体', '医院', '生病', '减肥', '睡眠'],
            '社交': ['朋友', '孤独', '社恐', '人际', '社交'],
            '金钱': ['钱', '欠款', '贷款', '房贷', '债务', '理财', '省钱']
        }

        # 识别用户消息中的话题
        detected_topics = []
        msg_lower = message.lower()
        for topic, keywords in topic_keywords.items():
            for kw in keywords:
                if kw in msg_lower:
                    detected_topics.append(topic)
                    break

        # 话题个性化教练提问 - 增强版
        topic_coaching = {
            '工作': [
                "如果你离开现在的岗位，最担心失去什么？是经济来源、社会地位，还是归属感？\n\n有时候，深入思考最坏的结果，反而能帮助我们看清什么才是真正重要的。你愿意试试吗？",
                "工作中的压力来源主要是什么呢？是工作量太大、关系复杂，还是看不到晋升空间？\n\n了解压力的根源，是解决问题的第一步。你愿意多说说吗？",
                "如果用1-10分评价你对工作的满意程度，你会打几分？\n\n如果低于7分，你认为差的那几分主要是因为什么呢？是薪酬、发展空间、工作氛围，还是其他原因？"
            ],
            '感情': [
                "这段经历中，你最难以接受的是什么？是被忽视、不被理解，还是对方的某些行为伤害了你？\n\n有时候，清晰地说出最痛的地方，本身就是一种疗愈。你愿意多说一点吗？",
                "你对未来有什么期待吗？你理想中的感情状态是什么样的？\n\n当我们清楚自己想要什么的时候，更容易找到前进的方向。你愿意分享一下你的想法吗？",
                "在这段关系中，你最看重的是什么？是尊重、理解、支持，还是陪伴？\n\n了解自己的核心需求，可以帮助我们更好地沟通和表达。你愿意多说说吗？"
            ],
            '学习': [
                "这次考试对你意味着什么？是升学的压力、父母的期望，还是对自己的要求？\n\n有时候我们会忘记，考试成绩并不能定义我们的全部价值。你愿意多说说你现在的感受吗？",
                "如果成绩不理想，你打算怎么面对？会给自己一些时间来调整，还是会立即开始准备下一次？\n\n无论选择什么方式，最重要的是照顾好自己的情绪。你觉得呢？",
                "学习中最大的困难是什么呢？是学习方法不对、时间管理有问题，还是缺乏动力？\n\n了解困难的本质，可以帮助我们更有针对性地解决它。你愿意多说一些吗？"
            ],
            '家庭': [
                "家人知道你现在的感受吗？你们平时沟通多吗？\n\n有时候，把感受说出来可以让关系更近一步。你愿意尝试和他们沟通吗？",
                "你和家人沟通时最大的障碍是什么？是代沟、表达方式不同，还是某些敏感话题？\n\n了解障碍所在，可以帮助我们找到更好的沟通方式。你愿意多说一点吗？",
                "你希望家庭关系是什么样的？你们现在的关系距离这个目标还有多远？\n\n有时候，明确的目标可以给我们前进的方向和动力。你愿意分享一下你的想法吗？"
            ],
            '健康': [
                "这种状态持续多久了？是从什么时候开始的，当时发生了什么？\n\n了解问题的起因和时间线，可以帮助我们更好地应对。你愿意多说一些吗？",
                "你尝试过哪些方法来改善吗？效果如何？\n\n有时候，即使是小的尝试也值得被肯定。你愿意分享一下你的经历吗？",
                "如果身体会说话，它会告诉你什么？它需要什么？\n\n倾听身体的声音，是一种很重要的自我关爱。你愿意试着感受一下吗？"
            ],
            '社交': [
                "你理想中的社交状态是什么样的？是有很多朋友，还是有几个知心好友？\n\n了解自己的期望，可以帮助我们更好地调整社交方式。你愿意分享一下你的想法吗？",
                "和朋友相处时，什么让你感到最舒服？是被理解、被支持，还是可以自由做自己？\n\n当你知道什么让你舒服时，更容易找到适合自己的社交圈。你愿意多说一点吗？",
                "独处时你会做些什么？享受独处还是感到孤独？\n\n无论是哪种，感受都是正常的。重要的是了解自己真正需要什么。你愿意多说一些吗？"
            ],
            '金钱': [
                "经济压力对你的生活影响大吗？主要影响到哪些方面？\n\n了解影响的具体方面，可以帮助我们更有针对性地应对。你愿意多说一些吗？",
                "有没有想过怎么改善目前的状况？你尝试过哪些方法？\n\n有时候，把想法说出来可以让我们更清晰地看到方向。你愿意分享一下你的想法吗？",
                "金钱对你来说意味着什么？是安全感、自由，还是其他什么？\n\n了解金钱对你的真正含义，可以帮助我们更理性地看待经济压力。你愿意多说一点吗？"
            ]
        }

        # 启发式提问 - 增强版
        coaching_questions = {
            'sad': [
                "如果把你的难过写成一封信，你会写些什么？写给现在的自己，还是写给某个人？\n\n写信的过程可以帮助我们理清情绪，找到内心深处的声音。你愿意试试看吗？",
                "这段时间里，有没有什么事情是让你感到一丝安慰的？哪怕是很小的事情。\n\n即使在最黑暗的时刻，也总有一些光亮存在。你愿意分享一下吗？",
                "如果你的朋友遇到同样的情况，你会对他说什么？\n\n有时候，我们对朋友的建议比对自己的更加温柔和理性。把这个建议送给自己吧。"
            ],
            'anxious': [
                "让你最担心的那件事，最坏的结果可能是什么？\n\n很多时候，我们过度担忧的结果实际上很少会发生。直面最坏的情况，反而能减轻焦虑。你愿意试试吗？",
                "如果把担心的事情列出来，你会发现什么规律？\n\n有时候，写下来可以帮助我们看清，哪些担心是真实的，哪些只是想象的产物。",
                "有没有什么事情是你现在可以控制、可以做的？\n\n焦虑往往来自于对不可控事物的担忧。专注于我们能控制的部分，可以帮助我们找回力量感。"
            ],
            'angry': [
                "当你生气时，身体有什么感觉？这能告诉你什么？\n\n身体的感觉往往是情绪的信使。注意到它，可以帮助我们更好地理解自己。",
                "对方可能有什么样的处境或难处？\n\n有时候，站在对方的角度思考，可以缓解我们的愤怒，同时也能帮助我们更好地沟通。",
                "如果几年后再看这件事，你会有什么不同的看法？\n\n时间往往会改变我们对很多事情的看法。现在让你生气的事，几年后可能就不值一提了。"
            ],
            'future': [
                "你希望半年后的自己是什么样子？\n\n有画面感的期望更容易转化为行动。你愿意描述一下那个画面吗？",
                "为了实现那个目标，你可以迈出的第一步是什么？\n\n大目标往往让人望而却步，但小步骤却容易得多。你觉得第一步可以是什么？",
                "如果有一个理想的解决方案，那会是什么样的？\n\n有时候，明确的理想可以给我们方向和希望。你愿意多说一点吗？"
            ]
        }

        # 根据话题选择个性化提问
        if detected_topics:
            primary_topic = detected_topics[0]
            if primary_topic in topic_coaching:
                questions = topic_coaching[primary_topic]
            else:
                questions = coaching_questions.get(emotion, coaching_questions['sad'])
        else:
            # 检查场景关键词
            scenario = self._detect_scenario(message)
            if scenario in coaching_questions:
                questions = coaching_questions[scenario]
            else:
                questions = coaching_questions.get(emotion, [
                    "你对这件事有什么看法？\n\n有时候，说出自己的观点可以帮助我们更好地理解问题的本质。你愿意多说一些吗？",
                    "你想从中获得什么？\n\n了解自己的需求可以让我们更有方向感。你愿意分享一下你的想法吗？",
                    "如果事情可以改变，你希望怎么发展？\n\n想象一个积极的结局，可以给我们希望和动力。你愿意描述一下吗？"
                ])

        question = random.choice(questions)

        intro = random.choice([
            "我想邀请你思考一些问题：\n\n",
            "让我帮你梳理一下：\n\n",
            "或许我们可以一起看看：\n\n",
            "这是一个值得思考的问题：\n\n"
        ])

        return intro + question
    
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
            print("Baidu API key not configured, using Mock mode")
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
                print(f"Baidu token fetch failed: {token_data.get('error_msg', 'unknown')}")
                return await self._mock_chat(messages, system_prompt)
            
            access_token = token_data.get('access_token')
            if not access_token:
                print("Baidu token fetch failed")
                return await self._mock_chat(messages, system_prompt)
            
            # 调用API
            full_url = f"{url}?access_token={access_token}"
            response = requests.post(full_url, json=payload, timeout=30)
            result = response.json()
            
            # 检查API调用是否成功
            if 'error_code' in result:
                print(f"Baidu API call failed: {result.get('error_msg', 'unknown')}")
                return await self._mock_chat(messages, system_prompt)
            
            return result.get('result', '谢谢你的分享。')
        except Exception as e:
            print(f"Baidu API call exception: {e}")
            return await self._mock_chat(messages, system_prompt)
    
    async def _openai_chat(self, messages: List[Dict], system_prompt: str) -> str:
        """OpenAI API (包括兼容的API如硅基流动等)"""
        import requests
        
        # 检查API密钥是否配置
        if not self.api_key:
            print("OpenAI API key not configured, using Mock mode")
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
                print(f"OpenAI API error: {result['error'].get('message', 'unknown')}")
                return await self._mock_chat(messages, system_prompt)
            
            if 'choices' not in result or not result['choices']:
                print("OpenAI API returned empty")
                return await self._mock_chat(messages, system_prompt)
            
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"OpenAI API call failed: {e}")
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
            print(f"Anthropic API call failed: {e}")
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
            print(f"ChatGLM API call failed: {e}")
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
            topic_count = {}  # 统计历史消息中的话题

            topics_to_track = [
                "辞职", "工作", "加班", "职场", "同事", "领导", "老板",
                "恋爱", "分手", "婚姻", "离婚", "相亲", "对象",
                "考试", "学习", "考研", "留学", "成绩",
                "失眠", "睡眠", "健康", "身体", "看病",
                "钱", "欠款", "债务", "房贷", "经济",
                "家人", "父母", "孩子", "养老",
                "朋友", "社交", "孤独"
            ]

            for record in reversed(records):
                user_msg = record.user_message or ""
                history.append({
                    'role': 'user',
                    'content': user_msg,
                    'timestamp': record.created_at.isoformat() if record.created_at else ''
                })

                # 统计历史消息中的话题
                for topic in topics_to_track:
                    if topic in user_msg:
                        topic_count[topic] = topic_count.get(topic, 0) + 1

                if record.ai_reply:
                    history.append({
                        'role': 'assistant',
                        'content': record.ai_reply,
                        'timestamp': record.created_at.isoformat() if record.created_at else ''
                    })

            # 构建话题历史
            topic_history = []
            for topic, count in topic_count.items():
                if count >= 2:  # 只记录提到2次及以上的话题
                    topic_history.append({
                        'topic': topic,
                        'count': count,
                        'first_mentioned': '',
                        'last_mentioned': ''
                    })

            return history, topic_history
        except Exception as e:
            print(f"Failed to load history: {e}")
            return []
    
    def get_context(self, user_id: int) -> ConversationContext:
        """获取或创建对话上下文（从数据库加载历史记录）"""
        if user_id not in self.contexts:
            # 创建新的上下文并加载历史记录
            context = ConversationContext(user_id=user_id)
            # 加载最近10条对话历史
            result = self.load_history_from_db(user_id, limit=10)
            # 处理返回值（可能是tuple或list）
            if isinstance(result, tuple):
                history, topic_history = result
                context.messages = history
                context.topic_history = topic_history
                # 从历史消息中恢复对话轮次（只计算用户消息）
                context.conversation_turn = sum(1 for msg in history if msg.get('role') == 'user')
            else:
                context.messages = result
                context.conversation_turn = sum(1 for msg in result if msg.get('role') == 'user')
            self.contexts[user_id] = context
        return self.contexts[user_id]
    
    def _get_topic_awareness(self, context: ConversationContext) -> str:
        """获取话题关注语 - 用户反复提到的问题"""
        if not context.topic_history:
            return ""

        # 找出被多次提及的话题（需要提到2次及以上）
        repeated_topics = [t for t in context.topic_history if t.get('count', 0) >= 2]

        if not repeated_topics:
            return ""

        # 按提及次数排序
        repeated_topics.sort(key=lambda x: x.get('count', 0), reverse=True)
        top_topic = repeated_topics[0]

        topic = top_topic['topic']
        count = top_topic['count']

        # 针对不同话题生成关注语
        topic_responses = {
            "辞职": f"我注意到您已经多次提到想辞职的问题了。这说明这个问题困扰您很久了吧？您愿意详细说说是什么让您这么纠结吗？",
            "工作": f"您好像对工作方面的事情很关注。之前您也提到过工作带来的压力，能多说说吗？",
            "加班": f"您已经多次提到加班的问题了。长期这样确实会很疲惫，您觉得目前最大的困扰是什么呢？",
            "职场": f"您对职场关系似乎有些困惑。您之前也提过，能具体说说是什么情况吗？",
            "同事": f"您已经多次提到同事之间的关系了。能多说说是什么让您感到困扰吗？",
            "领导": f"您好像和领导之间有些问题。您之前也提到过，能具体说说吗？",
            "老板": f"您多次提到老板相关的事情。能说说是什么让您感到不快吗？",
            "恋爱": f"您对感情问题很上心，之前也提到过。能多说说现在的困扰吗？",
            "分手": f"我注意到您已经多次提到分手这个话题了。这段经历一定让您很难受，愿意多说说吗？",
            "婚姻": f"您对婚姻问题很关注。能说说是什么让您感到困扰吗？",
            "考试": f"您已经多次提到考试了。看来这件事给您不小的压力，能多说说吗？",
            "学习": f"您对学习方面很关注。之前您也提到过，是什么让您感到焦虑呢？",
            "失眠": f"您已经多次提到失眠的问题了。睡眠对身体很重要，您愿意说说是什么让您睡不好吗？",
            "睡眠": f"您好像被睡眠问题困扰很久了。之前您也提到过，能多说说吗？",
            "健康": f"您对健康很担心。之前也提过，能说说具体是什么情况吗？",
            "钱": f"您多次提到经济方面的压力。能说说是什么让您感到经济紧张吗？",
            "债务": f"我注意到您已经多次提到债务问题了。这确实让人焦虑，您愿意多说说吗？",
            "家人": f"您对家人方面的事情很上心。之前也提过，能多说说吗？",
            "父母": f"您已经多次提到和父母之间的问题了。能说说是什么让您困扰吗？",
            "朋友": f"您对朋友关系很在意。之前也提过，能多说说吗？",
            "孤独": f"我注意到您已经多次提到孤独的感受了。这种感觉一定很难受，您愿意多说说吗？"
        }

        if topic in topic_responses:
            return f"\n\n* {topic_responses[topic]}"
        else:
            return f"\n\n* 我注意到您已经多次提到「{topic}」了。这个问题似乎对您很重要，愿意多说说吗？"
    
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

        # ==================== 话题追踪（用户反复提到的问题）====================
        # 从当前消息和历史中提取话题
        topics_to_track = [
            "辞职", "工作", "加班", "职场", "同事", "领导", "老板",
            "恋爱", "分手", "婚姻", "离婚", "相亲", "对象",
            "考试", "学习", "考研", "留学", "成绩",
            "失眠", "睡眠", "健康", "身体", "看病",
            "钱", "欠款", "债务", "房贷", "经济",
            "家人", "父母", "孩子", "养老",
            "朋友", "社交", "孤独"
        ]

        # 检查当前消息中的话题
        current_topics = []
        for topic in topics_to_track:
            if topic in message:
                current_topics.append(topic)

        # 更新话题历史（从历史消息中加载的count也会被累加）
        for topic in current_topics:
            found = False
            for t in context.topic_history:
                if t['topic'] == topic:
                    t['count'] += 1
                    t['last_mentioned'] = datetime.now().isoformat()
                    found = True
                    print(f"[Topic] User mentioned '{topic}', count={t['count']}")
                    break
            if not found:
                context.topic_history.append({
                    'topic': topic,
                    'count': 1,  # 当前消息提到1次
                    'first_mentioned': datetime.now().isoformat(),
                    'last_mentioned': datetime.now().isoformat()
                })
                print(f"[Topic] First mention of '{topic}'")
        
        print(f"[Topic] conversation_turn={context.conversation_turn}, topic_history={context.topic_history}")

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

        # 在回复中添加话题关注语（仅当当前消息提到新话题时添加）
        # 只关注当前消息首次提到的话题，不重复添加
        awareness_added = False

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

        # 添加智能资源推荐
        if HAS_RESOURCE_RECOMMENDER and resource_recommender:
            try:
                # 每隔几轮或情绪强烈时推荐
                should_recommend = (
                    context.conversation_turn % 3 == 0 or  # 每3轮推荐一次
                    confidence >= 0.7 or  # 情绪强度高时推荐
                    emotion in ['sad', 'anxious', 'angry']  # 负面情绪时推荐
                )

                if should_recommend:
                    # 获取资源推荐
                    intensity = confidence if confidence else 0.5
                    emotion_history = context.emotion_history[-5:] if context.emotion_history else []

                    recommend_result = resource_recommender.recommend_for_context(
                        message=message,
                        emotion=emotion,
                        emotion_history=emotion_history,
                        max_items=3
                    )

                    if recommend_result.get('recommendations'):
                        response_data['resource_recommendations'] = recommend_result['recommendations']
                        response_data['recommend_reason'] = recommend_result.get('recommend_reason', '')
            except Exception as e:
                print(f"Failed to get recommendations: {e}")

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
llm_provider = AI_CONFIG.get("llm_provider", "mock")
llm_config = AI_CONFIG.get("llm", {}).get(llm_provider, {})
enhanced_ai_agent = EnhancedEmoHealerAgent(config={
    'use_llm': AI_CONFIG.get("use_llm", False),
    'llm': {
        'provider': llm_provider,
        'api_key': llm_config.get("api_key", ""),
        'api_secret': llm_config.get("api_secret", ""),
        'api_base': llm_config.get("api_base", "http://localhost:8000"),
        'model': llm_config.get("model", "gpt-3.5-turbo")
    }
})
