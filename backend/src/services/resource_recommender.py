"""
心理健康资源智能推荐模块
根据用户情绪状态和对话上下文，智能推荐相关资源
"""
import json
import os
import random
from typing import Dict, List, Optional
from datetime import datetime


class ResourceRecommender:
    """智能资源推荐器"""

    def __init__(self, kb_path: str = None):
        if kb_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            kb_path = os.path.join(base_dir, 'knowledge_base', 'resources.json')

        self.kb_path = kb_path
        self.knowledge = self._load_knowledge()
        self.rules = self.knowledge.get('recommendation_rules', {})

    def _load_knowledge(self) -> dict:
        """加载知识库"""
        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load resource knowledge base: {e}")
            return {"categories": {}, "recommendation_rules": {}}

    def recommend(
        self,
        emotion: str,
        intensity: float = 0.5,
        conversation_context: List[Dict] = None,
        user_preferences: Dict = None,
        max_per_category: int = 2
    ) -> Dict:
        """
        根据情绪状态推荐资源

        Args:
            emotion: 当前情绪类型
            intensity: 情绪强度 0-1
            conversation_context: 对话上下文
            user_preferences: 用户偏好
            max_per_category: 每个类别最大推荐数

        Returns:
            推荐结果字典
        """
        if not emotion:
            emotion = "neutral"

        # 获取推荐规则
        rule = self.rules.get(emotion, self.rules.get("neutral", {}))
        priority_categories = rule.get("priority", ["article", "meditation"])
        reason = rule.get("reason", "")

        # 根据强度调整推荐策略
        if intensity >= 0.8:
            # 高强度情绪，优先推荐专业帮助
            if "consultation" not in priority_categories:
                priority_categories.insert(0, "consultation")
            reason = "考虑到您目前情绪较为强烈，建议尝试专业帮助"
        elif intensity >= 0.6:
            # 中高强度，增加即时帮助类资源
            reason = "您现在的情绪需要更多关注，这些资源可能有帮助"

        recommendations = []
        categories = self.knowledge.get("categories", {})

        for category_key in priority_categories:
            if category_key in categories:
                category = categories[category_key]
                items = category.get("items", [])

                # 根据情绪匹配度筛选
                scored_items = []
                for item in items:
                    target_emotions = item.get("target_emotions", [])
                    # 匹配度高优先
                    score = 1.0 if emotion in target_emotions else 0.3
                    scored_items.append((score, item))

                # 按得分排序
                scored_items.sort(key=lambda x: x[0], reverse=True)

                # 选择前max_per_category个
                for score, item in scored_items[:max_per_category]:
                    recommendations.append({
                        "category_name": category.get("name", category_key),
                        "category_icon": category.get("icon", ""),
                        "category_key": category_key,
                        "score": score,
                        **item
                    })

        # 构建返回结果
        result = {
            "emotion": emotion,
            "intensity": intensity,
            "recommendations": recommendations,
            "total_count": len(recommendations),
            "recommend_reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        return result

    def recommend_for_context(
        self,
        message: str,
        emotion: str,
        emotion_history: List[Dict] = None,
        max_items: int = 4
    ) -> Dict:
        """
        根据消息内容和情绪历史进行更智能的推荐
        """
        # 分析消息中的关键词
        keywords = self._extract_keywords(message)

        # 分析情绪历史趋势
        emotion_trend = self._analyze_emotion_trend(emotion_history) if emotion_history else "stable"

        # 获取基础推荐
        intensity_map = {"low": 0.3, "medium": 0.5, "high": 0.7, "severe": 0.9}
        intensity = intensity_map.get(emotion_trend, 0.5)

        result = self.recommend(emotion, intensity, max_per_category=2)

        # 根据关键词调整推荐
        if "睡眠" in keywords or "失眠" in keywords:
            # 优先推荐睡眠相关
            self._boost_category(result, "music", "sleep")
            self._boost_category(result, "tool", "sleep")

        if "工作" in keywords or "压力" in keywords:
            self._boost_category(result, "consultation", "职业")

        if "人际关系" in keywords or "社交" in keywords or "朋友" in keywords:
            self._boost_category(result, "consultation", "人际关系")

        # 限制返回数量
        result["recommendations"] = result["recommendations"][:max_items]
        result["total_count"] = len(result["recommendations"])

        return result

    def _extract_keywords(self, message: str) -> List[str]:
        """提取消息中的关键词"""
        keyword_patterns = [
            "睡眠", "失眠", "入睡", "梦", "工作", "压力", "职业",
            "人际关系", "社交", "朋友", "家人", "恋人", "同事",
            "学习", "考试", "焦虑", "抑郁", "悲伤", "愤怒", "恐惧",
            "婚姻", "恋爱", "分手", "失去", "亲人", "死亡"
        ]

        found = []
        for kw in keyword_patterns:
            if kw in message:
                found.append(kw)

        return found

    def _analyze_emotion_trend(self, emotion_history: List[Dict]) -> str:
        """分析情绪历史趋势"""
        if not emotion_history or len(emotion_history) < 3:
            return "stable"

        recent = emotion_history[-3:]
        emotions = [e.get("emotion") for e in recent]

        # 统计负面情绪比例
        negative = ["sad", "anxious", "angry", "fear", "lonely", "guilty"]
        negative_count = sum(1 for e in emotions if e in negative)

        if negative_count >= 3:
            return "severe"
        elif negative_count >= 2:
            return "high"
        elif len(set(emotions)) == 1:
            return "persistent"
        else:
            return "stable"

    def _boost_category(self, result: Dict, category_key: str, keyword: str = ""):
        """提升特定类别的推荐权重"""
        recommendations = result.get("recommendations", [])

        # 找到该类别的推荐
        category_recs = [r for r in recommendations if r.get("category_key") == category_key]

        if not category_recs:
            # 如果没有，尝试从知识库添加
            categories = self.knowledge.get("categories", {})
            if category_key in categories:
                category = categories[category_key]
                for item in category.get("items", []):
                    if not keyword or keyword in item.get("description", "") or keyword in item.get("title", ""):
                        recommendations.append({
                            "category_name": category.get("name", ""),
                            "category_icon": category.get("icon", ""),
                            "category_key": category_key,
                            "score": 1.0,
                            **item
                        })
                        break

    def get_category_resources(self, category_key: str) -> List[Dict]:
        """获取指定类别的所有资源"""
        categories = self.knowledge.get("categories", {})
        if category_key not in categories:
            return []

        category = categories[category_key]
        return category.get("items", [])

    def search_resources(self, keyword: str) -> List[Dict]:
        """搜索资源"""
        results = []
        categories = self.knowledge.get("categories", {})

        keyword_lower = keyword.lower()

        for cat_key, category in categories.items():
            for item in category.get("items", []):
                # 搜索标题、描述
                title = item.get("title", "").lower()
                desc = item.get("description", "").lower()

                if keyword_lower in title or keyword_lower in desc:
                    results.append({
                        "category_name": category.get("name", ""),
                        "category_icon": category.get("icon", ""),
                        "category_key": cat_key,
                        **item
                    })

        return results


# 全局推荐器实例
resource_recommender = ResourceRecommender()
