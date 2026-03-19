"""
EmoHealer RAG增强模块
提供更准确的情绪识别和更安全的智能体响应
"""
import json
import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np


class EmotionRAG:
    """情绪RAG增强模块"""

    def __init__(self, kb_path: str = None):
        if kb_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            kb_path = os.path.join(base_dir, 'knowledge_base', 'emotion_rag.json')

        self.kb_path = kb_path
        self.knowledge = self._load_knowledge()

        # 情绪分析权重配置
        self.emotion_weights = {
            'keyword': 0.4,      # 关键词匹配
            'context': 0.3,     # 上下文分析
            'intensity': 0.3    # 强度评估
        }

    def _load_knowledge(self) -> dict:
        """加载知识库"""
        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load knowledge base: {e}")
            return {}

    def analyze_emotion(self, message: str, context: Dict = None) -> Dict:
        """
        综合分析用户情绪
        返回详细的情绪分析结果
        """
        message = message.strip()
        message_lower = message.lower()

        # 1. 关键词匹配分析
        keyword_result = self._keyword_analysis(message_lower)

        # 2. 上下文分析
        context_result = self._context_analysis(message, context)

        # 3. 强度评估
        intensity_result = self._intensity_analysis(message)

        # 综合判断
        primary_emotion = self._combine_results(keyword_result, context_result, intensity_result)

        return {
            'primary_emotion': primary_emotion,
            'emotion_details': keyword_result,
            'context_analysis': context_result,
            'intensity': intensity_result['score'],
            'confidence': self._calculate_confidence(keyword_result, context_result, intensity_result),
            'triggers': self._identify_triggers(message_lower, primary_emotion),
            'suggested_approach': self._get_approach(primary_emotion, intensity_result['score']),
            'requires_immediate_support': self._check_safety(message_lower)['level'] >= 3
        }

    def _keyword_analysis(self, message: str) -> Dict:
        """基于关键词的情绪分析"""
        emotion_keywords = {
            'sad': ['难过', '伤心', '痛苦', '悲伤', '抑郁', '低落', '郁闷', '沮丧', '失望', '绝望', '想哭', '哭', '难过', '心碎', '孤独', '寂寞', '无助', '绝望', '没意思', '不想活', '活着没意思', '没用', '失败', '失去', '失去'],
            'anxious': ['焦虑', '紧张', '担心', '害怕', '不安', '恐惧', '恐慌', '心慌', '失眠', '睡不着', '压力大', '焦虑', '恐慌', '坐立不安', '怎么办', '不确定', '纠结', '犹豫', '慌'],
            'angry': ['生气', '愤怒', '气愤', '恼火', '愤怒', '讨厌', '恨', '气死了', '不公平', '凭什么', '可恶', '火大', '抓狂', '崩溃', '怒'],
            'tired': ['累', '疲惫', '困', '疲倦', '没精力', '无力', '疲劳', '虚弱', '没劲', '筋疲力尽', '撑不住', '好累', '好困'],
            'fear': ['害怕', '恐惧', '怕', '惊恐', '畏惧', '发抖', '颤抖', '担心', '不敢', '危险', '恐惧'],
            'happy': ['开心', '高兴', '快乐', '幸福', '愉快', '兴奋', '喜悦', '欢乐', '棒', '太好了', '喜欢', '爱', '满意', '满足', '开心'],
            'lonely': ['孤独', '寂寞', '一个人', '没人', '孤单', '没人陪', '没人理解', '被孤立', '独处'],
            'guilty': ['愧疚', '自责', '对不起', '后悔', '抱歉', '过意不去', '都是我的错', '不应该', '内疚', '惭愧'],
            'confused': ['困惑', '迷茫', '不确定', '不知道', '怎么办', '迷茫', '纠结', '犹豫', '疑惑', '疑问']
        }

        scores = {}
        matched_keywords = {}

        for emotion, keywords in emotion_keywords.items():
            score = 0
            matches = []
            for kw in keywords:
                if kw in message:
                    score += 1
                    matches.append(kw)

            if score > 0:
                scores[emotion] = score
                matched_keywords[emotion] = matches

        # 归一化分数
        if scores:
            max_score = max(scores.values())
            for emotion in scores:
                scores[emotion] = scores[emotion] / max_score

        return {
            'scores': scores,
            'matched_keywords': matched_keywords,
            'primary': max(scores, key=scores.get) if scores else 'neutral'
        }

    def _context_analysis(self, message: str, context: Dict = None) -> Dict:
        """上下文分析"""
        if not context:
            return {'mood': 'neutral', 'trend': 'stable', 'context_indicators': []}

        indicators = []

        # 检查消息长度（长消息可能表示倾诉欲）
        if len(message) > 50:
            indicators.append('long_message')

        # 检查是否使用问号（疑问/寻求帮助）
        if '?' in message or '？' in message:
            indicators.append('seeking_help')

        # 检查感叹号（强烈情绪）
        if '!' in message or '！' in message:
            indicators.append('strong_emotion')

        # 从上下文获取情绪历史
        emotion_history = context.get('emotion_history', [])
        if len(emotion_history) >= 3:
            recent_emotions = [e.get('emotion') for e in emotion_history[-3:]]
            if len(set(recent_emotions)) == 1:
                trend = 'persistent'
            else:
                trend = 'varying'
        else:
            trend = 'stable'

        return {
            'mood': 'neutral',
            'trend': trend,
            'context_indicators': indicators,
            'conversation_turns': context.get('conversation_turn', 0)
        }

    def _intensity_analysis(self, message: str) -> Dict:
        """情绪强度分析"""
        intensity_indicators = {
            'high': ['非常', '特别', '极其', '极度', '超级', '十分', '太', '真的很', '简直'],
            'medium': ['比较', '有些', '稍微', '有点', '相当'],
            'low': ['轻微', '一点点', '略微']
        }

        # 重复字符检测（如"太累了啊啊啊"）
        repeated_chars = re.findall(r'(.)\1{2,}', message)

        # 标点符号分析（！！！表示强烈）
        exclamation_count = message.count('!') + message.count('！')
        question_count = message.count('?') + message.count('？')

        score = 5  # 默认中等强度

        for level, indicators in intensity_indicators.items():
            for ind in indicators:
                if ind in message:
                    if level == 'high':
                        score = min(10, score + 3)
                    elif level == 'medium':
                        score = min(10, score + 1)
                    else:
                        score = max(1, score - 1)

        if repeated_chars:
            score = min(10, score + 2)

        if exclamation_count >= 2:
            score = min(10, score + 2)

        if question_count >= 2:
            score = min(10, score + 1)

        return {'score': min(10, max(1, score)), 'indicators': []}

    def _combine_results(self, keyword: Dict, context: Dict, intensity: Dict) -> str:
        """综合分析结果"""
        keyword_scores = keyword.get('scores', {})

        if not keyword_scores:
            return 'neutral'

        # 如果情绪持续，权重增加
        if context.get('trend') == 'persistent':
            if keyword['primary'] in keyword_scores:
                keyword_scores[keyword['primary']] *= 1.2

        return max(keyword_scores, key=keyword_scores.get)

    def _calculate_confidence(self, keyword: Dict, context: Dict, intensity: Dict) -> float:
        """计算分析置信度"""
        keyword_scores = keyword.get('scores', {})

        if not keyword_scores:
            return 0.3

        max_score = max(keyword_scores.values()) if keyword_scores else 0

        # 基础置信度
        confidence = max_score * 0.5

        # 匹配关键词数量
        total_matches = sum(len(v) for v in keyword.get('matched_keywords', {}).values())
        confidence += min(0.3, total_matches * 0.05)

        # 强度高时置信度增加
        if intensity['score'] >= 7:
            confidence += 0.1

        return min(0.95, confidence)

    def _identify_triggers(self, message: str, emotion: str) -> List[str]:
        """识别情绪触发因素"""
        triggers_map = {
            'sad': ['失落', '失败', '分离', '失去', '孤独', '批评', '压力'],
            'anxious': ['压力', '不确定性', '担忧', '紧张', '失眠', '健康'],
            'angry': ['不公', '被冒犯', '挫折', '失望', '控制'],
            'tired': ['工作过劳', '睡眠不足', '慢性压力', '照顾他人'],
            'fear': ['危险', '未知', '社交', '健康'],
            'lonely': ['独处', '分离', '人际困难'],
            'guilty': ['犯错', '伤害他人', '错过']
        }

        identified = []
        triggers = triggers_map.get(emotion, [])

        for trigger in triggers:
            if trigger in message:
                identified.append(trigger)

        return identified if identified else ['未知']

    def _get_approach(self, emotion: str, intensity: int) -> str:
        """获取建议的应对方式"""
        approaches = {
            'sad': '共情陪伴，鼓励表达情感，引导积极思考',
            'anxious': '深呼吸放松，识别担忧的具体内容，分解问题',
            'angry': '情绪降温，引导表达感受，讨论应对策略',
            'tired': '关怀提醒，评估疲劳原因，建议休息',
            'fear': '接纳恐惧，逐步暴露，提供安全感',
            'happy': '积极回应，分享喜悦，鼓励延续',
            'lonely': '共情陪伴，鼓励社交，联系支持系统',
            'guilty': '自我宽恕，引导补救，区分行为与人格',
            'confused': '理清思路，帮助分析，提供选择',
            'neutral': '保持对话，关注变化'
        }

        base = approaches.get(emotion, approaches['neutral'])

        if intensity >= 8:
            return f"【重点关注】{base}，建议寻求专业支持"
        elif intensity >= 6:
            return f"【加强支持】{base}"

        return base

    def _check_safety(self, message: str) -> Dict:
        """安全检查 - 检测危机信号"""
        safety_data = self.knowledge.get('safety_keywords', {})

        for level, info in safety_data.items():
            keywords = info.get('keywords', [])
            for kw in keywords:
                if kw in message:
                    level_num = int(level.split('_')[-1])
                    return {
                        'level': level_num,
                        'keyword': kw,
                        'action': info.get('action', ''),
                        'requires_intervention': level_num >= 3
                    }

        return {'level': 0, 'keyword': None, 'action': '', 'requires_intervention': False}

    def get_response_strategy(self, emotion: str, intensity: int, context: Dict = None) -> Dict:
        """获取响应策略"""
        strategies = {
            'sad': {
                'role': 'listener',
                'priority': 'high' if intensity >= 7 else 'normal',
                'max_response_length': 300,
                'techniques': ['共情', '倾听', '验证感受']
            },
            'anxious': {
                'role': 'coach',
                'priority': 'high' if intensity >= 7 else 'normal',
                'max_response_length': 250,
                'techniques': ['放松引导', '问题分解', '认知重构']
            },
            'angry': {
                'role': 'listener',
                'priority': 'high',
                'max_response_length': 200,
                'techniques': ['情绪降温', '确认感受', '非指责倾听']
            },
            'tired': {
                'role': 'supporter',
                'priority': 'normal',
                'max_response_length': 200,
                'techniques': ['关怀', '休息建议', '精力管理']
            },
            'fear': {
                'role': 'coach',
                'priority': 'high' if intensity >= 7 else 'normal',
                'max_response_length': 250,
                'techniques': ['逐步暴露', '安全感建立', '认知重构']
            },
            'happy': {
                'role': 'supporter',
                'priority': 'normal',
                'max_response_length': 150,
                'techniques': ['积极回应', '分享喜悦', '鼓励延续']
            },
            'lonely': {
                'role': 'listener',
                'priority': 'high' if intensity >= 7 else 'normal',
                'max_response_length': 280,
                'techniques': ['共情', '陪伴', '社交建议']
            },
            'guilty': {
                'role': 'educator',
                'priority': 'normal',
                'max_response_length': 280,
                'techniques': ['自我宽恕', '区分行为与人格', '补救导向']
            }
        }

        return strategies.get(emotion, {
            'role': 'listener',
            'priority': 'normal',
            'max_response_length': 200,
            'techniques': ['倾听', '回应']
        })

    def get_safety_response(self, level: int) -> Tuple[str, str]:
        """获取安全响应"""
        safety_responses = {
            4: ("我非常担心你的安全。我听到你现在的状态很不好，我想帮助你。请拨打心理援助热线：400-161-9995，或者告诉我你现在在哪里，我们可以一起想办法。", "危急"),
            3: ("谢谢你的信任告诉我这些。我能感受到你现在的痛苦。请记住，无论发生什么，都有人在乎你、愿意帮助你。如果你想聊聊，我在这里。如果感觉太糟，请联系专业帮助。", "高危"),
            2: ("我能感受到你现在很不容易。如果这种绝望感持续加深，请一定要寻求帮助。你可以告诉信任的人，或者联系心理咨询师。你不是一个人。", "中危"),
            1: ("谢谢愿意分享你的感受。难过的时候，被听见很重要。我在这里陪你聊聊。", "低危")
        }

        return safety_responses.get(level, ("我听到你了。我们慢慢聊。", "关注"))


# 全局实例
emotion_rag = EmotionRAG()
