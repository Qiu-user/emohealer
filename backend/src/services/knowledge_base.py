"""
心理疗愈知识库模块
提供基于关键词的问答检索功能
"""
import json
import os
import random
from typing import List, Dict, Optional


class KnowledgeBase:
    """知识库检索器"""

    def __init__(self, kb_path: str = None):
        if kb_path is None:
            # 路径: backend/knowledge_base/psychology_knowledge.json
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            kb_path = os.path.join(
                base_dir,
                'knowledge_base',
                'psychology_knowledge.json'
            )

        self.kb_path = kb_path
        self.knowledge = self._load_knowledge()

    def _load_knowledge(self) -> dict:
        """加载知识库"""
        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Knowledge base file not found: {self.kb_path}")
            return {"categories": {}}
        except json.JSONDecodeError:
            print(f"Knowledge base JSON format error")
            return {"categories": {}}

    def search(self, query: str, emotion: str = None, max_results: int = 2) -> List[Dict]:
        """
        搜索知识库

        Args:
            query: 用户查询/消息
            emotion: 当前情绪类型
            max_results: 最大返回结果数

        Returns:
            知识库条目列表
        """
        results = []
        query_lower = query.lower()

        # 根据情绪优先搜索相关类别
        emotion_category_map = {
            'anxious': '焦虑缓解',
            'sad': '抑郁应对',
            'angry': '愤怒管理',
            'tired': '睡眠改善',
            'fear': '焦虑缓解',
            'happy': '自我成长',
            'neutral': '情绪管理'
        }

        # 1. 如果有情绪信息，先搜索对应类别
        if emotion and emotion in emotion_category_map:
            category_name = emotion_category_map[emotion]
            category = self.knowledge.get('categories', {}).get(category_name, {})
            entries = category.get('entries', [])
            for entry in entries:
                entry['category'] = category_name
                results.append(entry)

        # 2. 关键词匹配搜索所有类别
        for category_name, category in self.knowledge.get('categories', {}).items():
            keywords = category.get('keywords', [])

            # 检查是否包含关键词
            match_score = 0
            for kw in keywords:
                if kw in query_lower:
                    match_score += 2
                # 模糊匹配
                for word in query_lower:
                    if word in kw:
                        match_score += 0.5

            if match_score > 0:
                entries = category.get('entries', [])
                for entry in entries:
                    entry['category'] = category_name
                    entry['match_score'] = match_score
                    results.append(entry)

        # 3. 去重并按相关度排序
        seen = set()
        unique_results = []
        for r in results:
            if r['title'] not in seen:
                seen.add(r['title'])
                unique_results.append(r)

        # 按匹配度排序
        unique_results.sort(key=lambda x: x.get('match_score', 0), reverse=True)

        # 随机选择以增加多样性
        if len(unique_results) > max_results:
            return random.sample(unique_results, max_results)

        return unique_results

    def get_tip_for_emotion(self, emotion: str) -> Optional[Dict]:
        """获取针对特定情绪的小贴士"""
        tips = {
            'anxious': '当你感到焦虑时，试着做几次深呼吸。吸气4秒，屏住呼吸7秒，呼气8秒。这能帮助身体放松下来。',
            'sad': '难过的时候，允许自己感受这种情绪，但不要沉浸太久。试着写下来，或者做一些小事让自己感觉好一点。',
            'angry': '愤怒时，先停下来，数到10。试着把让你生气的事情写下来，这能帮助你更冷静地思考。',
            'tired': '疲惫是身体在提醒你需要休息了。哪怕只休息5分钟，给自己也充充电吧。',
            'fear': '害怕是人类正常的情绪。试着把害怕的事情分解成小块，一步步面对会更容易。',
            'happy': '太好了！记得把这些美好的时刻记录下来，它们会成为你未来困难时的力量来源。',
            'neutral': '感谢你愿意分享。保持对情绪的觉察是心理健康的重要能力。'
        }
        return {'tip': tips.get(emotion, '记得照顾好自己')}

    def get_random_tip(self) -> str:
        """获取随机小贴士"""
        all_tips = [
            "每天花5分钟做深呼吸练习，能有效缓解压力。",
            "保持规律的睡眠时间对情绪健康很重要。",
            "写下3件让你感恩的事情，能提升幸福感。",
            "运动是天然的情绪调节剂。",
            "与朋友聊天是很好的情感支持。",
            "正念冥想只需要5分钟，随时随地都可以做。",
            "接纳自己的情绪比否定它更有帮助。",
            "小小的进步也值得庆祝。"
        ]
        return random.choice(all_tips)


# 全局知识库实例
knowledge_base = KnowledgeBase()
