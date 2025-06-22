"""
Task Classification Service for TaskWall v3.0

Handles:
- Automatic task categorization
- Multi-dimensional classification
- Learning from user feedback
"""

import json
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .base import AIServiceBase, AIResult, AIOperationType
from ..models import Task, UserPreference


@dataclass
class ClassificationResult:
    """Task classification result"""
    category: str
    subcategory: Optional[str] = None
    confidence: float = 0.0
    reasoning: List[str] = None
    alternative_suggestions: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = []
        if self.alternative_suggestions is None:
            self.alternative_suggestions = []


class TaskClassifier:
    """Advanced task classification engine"""
    
    def __init__(self):
        # Hierarchical classification system
        self.classification_hierarchy = {
            "开发": {
                "前端开发": ["前端", "界面", "ui", "ux", "vue", "react", "angular", "页面", "组件"],
                "后端开发": ["后端", "api", "服务器", "数据库", "接口", "服务", "microservice"],
                "移动开发": ["移动", "app", "ios", "android", "flutter", "react native"],
                "DevOps": ["部署", "运维", "docker", "kubernetes", "ci/cd", "pipeline", "监控"]
            },
            "测试": {
                "功能测试": ["功能测试", "集成测试", "端到端", "e2e", "功能验证"],
                "性能测试": ["性能", "负载", "压力", "benchmark", "优化", "performance"],
                "安全测试": ["安全", "漏洞", "渗透", "安全扫描", "security"]
            },
            "文档": {
                "技术文档": ["api文档", "技术文档", "开发文档", "架构文档", "设计文档"],
                "用户文档": ["用户手册", "使用指南", "帮助文档", "教程"],
                "项目文档": ["需求文档", "项目计划", "进度报告", "总结报告"]
            },
            "会议": {
                "项目会议": ["项目会议", "站会", "scrum", "sprint", "评审"],
                "技术会议": ["技术讨论", "架构评审", "代码评审", "技术分享"],
                "管理会议": ["管理会议", "汇报", "决策会议", "规划会议"]
            },
            "设计": {
                "UI设计": ["界面设计", "ui设计", "视觉设计", "交互设计"],
                "架构设计": ["系统设计", "架构设计", "数据库设计", "api设计"],
                "产品设计": ["产品设计", "原型设计", "用户体验", "需求设计"]
            },
            "管理": {
                "项目管理": ["项目管理", "计划", "调度", "资源分配", "进度跟踪"],
                "团队管理": ["团队管理", "人员安排", "绩效", "培训"],
                "流程管理": ["流程优化", "制度建设", "规范制定", "标准化"]
            }
        }
        
        # Category priority weights (higher priority categories get preference)
        self.category_weights = {
            "开发": 1.0,
            "测试": 0.9,
            "文档": 0.7,
            "会议": 0.8,
            "设计": 0.9,
            "管理": 0.6
        }
        
        # Action verb mappings
        self.action_category_mapping = {
            "开发": ["开发", "编程", "实现", "构建", "编写代码", "develop", "implement", "code", "build"],
            "测试": ["测试", "验证", "检查", "调试", "test", "verify", "debug", "validate"],
            "设计": ["设计", "原型", "设计", "design", "prototype", "mockup"],
            "文档": ["编写", "文档", "记录", "总结", "write", "document", "record"],
            "会议": ["开会", "讨论", "沟通", "汇报", "meeting", "discuss", "communicate"],
            "管理": ["管理", "规划", "安排", "组织", "manage", "plan", "organize", "schedule"]
        }
    
    def classify_task(self, task_content: str, user_context: Optional[Dict[str, Any]] = None) -> ClassificationResult:
        """Classify a task using multiple strategies"""
        content_lower = task_content.lower()
        
        # Strategy 1: Keyword matching
        keyword_result = self._classify_by_keywords(content_lower)
        
        # Strategy 2: Action verb analysis
        action_result = self._classify_by_actions(content_lower)
        
        # Strategy 3: Context analysis
        context_result = self._classify_by_context(content_lower, user_context)
        
        # Strategy 4: Pattern matching
        pattern_result = self._classify_by_patterns(content_lower)
        
        # Combine results
        combined_result = self._combine_classification_results([
            keyword_result,
            action_result,
            context_result,
            pattern_result
        ])
        
        return combined_result
    
    def _classify_by_keywords(self, content: str) -> Dict[str, Any]:
        """Classify based on keyword matching"""
        category_scores = defaultdict(float)
        subcategory_scores = defaultdict(float)
        matched_keywords = []
        
        for category, subcategories in self.classification_hierarchy.items():
            for subcategory, keywords in subcategories.items():
                for keyword in keywords:
                    if keyword in content:
                        # Calculate score based on keyword length and frequency
                        keyword_score = len(keyword) * content.count(keyword)
                        category_scores[category] += keyword_score
                        subcategory_scores[subcategory] += keyword_score
                        matched_keywords.append(f"{keyword} -> {category}/{subcategory}")
        
        # Apply category weights
        for category in category_scores:
            category_scores[category] *= self.category_weights.get(category, 1.0)
        
        best_category = max(category_scores, key=category_scores.get) if category_scores else None
        best_subcategory = max(subcategory_scores, key=subcategory_scores.get) if subcategory_scores else None
        
        # Calculate confidence
        total_score = sum(category_scores.values())
        confidence = (category_scores.get(best_category, 0) / total_score) if total_score > 0 else 0
        
        return {
            "method": "keywords",
            "category": best_category,
            "subcategory": best_subcategory,
            "confidence": min(confidence, 1.0),
            "reasoning": matched_keywords,
            "scores": dict(category_scores)
        }
    
    def _classify_by_actions(self, content: str) -> Dict[str, Any]:
        """Classify based on action verbs"""
        action_scores = defaultdict(float)
        matched_actions = []
        
        for category, actions in self.action_category_mapping.items():
            for action in actions:
                if action in content:
                    # Higher score for actions at the beginning of text
                    if content.startswith(action):
                        score = 3.0
                    elif content.find(action) < 20:  # First 20 characters
                        score = 2.0
                    else:
                        score = 1.0
                    
                    action_scores[category] += score
                    matched_actions.append(f"{action} -> {category}")
        
        best_category = max(action_scores, key=action_scores.get) if action_scores else None
        total_score = sum(action_scores.values())
        confidence = (action_scores.get(best_category, 0) / total_score) if total_score > 0 else 0
        
        return {
            "method": "actions",
            "category": best_category,
            "subcategory": None,
            "confidence": min(confidence, 1.0),
            "reasoning": matched_actions,
            "scores": dict(action_scores)
        }
    
    def _classify_by_context(self, content: str, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Classify based on user context and history"""
        if not user_context:
            return {
                "method": "context",
                "category": None,
                "subcategory": None,
                "confidence": 0.0,
                "reasoning": ["No context provided"],
                "scores": {}
            }
        
        context_scores = defaultdict(float)
        reasoning = []
        
        # User's recent task patterns
        recent_categories = user_context.get("recent_categories", [])
        if recent_categories:
            for category in recent_categories:
                context_scores[category] += 0.5
                reasoning.append(f"Recent pattern: {category}")
        
        # Current project context
        current_project = user_context.get("current_project")
        if current_project:
            project_category = user_context.get("project_category")
            if project_category:
                context_scores[project_category] += 1.0
                reasoning.append(f"Project context: {project_category}")
        
        # Time-based patterns
        current_time = user_context.get("current_time")
        if current_time:
            # Meeting tasks more likely in work hours
            if 9 <= current_time.hour <= 17:
                context_scores["会议"] += 0.3
                reasoning.append("Work hours: meeting more likely")
        
        best_category = max(context_scores, key=context_scores.get) if context_scores else None
        total_score = sum(context_scores.values())
        confidence = (context_scores.get(best_category, 0) / total_score) if total_score > 0 else 0
        
        return {
            "method": "context",
            "category": best_category,
            "subcategory": None,
            "confidence": min(confidence, 1.0),
            "reasoning": reasoning,
            "scores": dict(context_scores)
        }
    
    def _classify_by_patterns(self, content: str) -> Dict[str, Any]:
        """Classify based on text patterns"""
        pattern_scores = defaultdict(float)
        matched_patterns = []
        
        patterns = {
            "会议": [
                r"(和|与).*(讨论|沟通|开会)",
                r"会议|meeting",
                r"\d+[点:]\d*.*开会",
                r"参加.*会"
            ],
            "开发": [
                r"(开发|实现|编写).*功能",
                r"(修复|fix).*bug",
                r"(优化|重构).*代码",
                r"(创建|build).*项目"
            ],
            "测试": [
                r"测试.*功能",
                r"验证.*结果",
                r"(性能|压力)测试",
                r"(单元|集成)测试"
            ],
            "文档": [
                r"(编写|更新).*文档",
                r"(完成|整理).*报告",
                r"(记录|总结).*",
                r".*手册"
            ]
        }
        
        import re
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, content, re.IGNORECASE):
                    pattern_scores[category] += 1.0
                    matched_patterns.append(f"Pattern '{pattern}' -> {category}")
        
        best_category = max(pattern_scores, key=pattern_scores.get) if pattern_scores else None
        total_score = sum(pattern_scores.values())
        confidence = (pattern_scores.get(best_category, 0) / total_score) if total_score > 0 else 0
        
        return {
            "method": "patterns",
            "category": best_category,
            "subcategory": None,
            "confidence": min(confidence, 1.0),
            "reasoning": matched_patterns,
            "scores": dict(pattern_scores)
        }
    
    def _combine_classification_results(self, results: List[Dict[str, Any]]) -> ClassificationResult:
        """Combine multiple classification results"""
        combined_scores = defaultdict(float)
        all_reasoning = []
        method_weights = {
            "keywords": 0.4,
            "actions": 0.3,
            "context": 0.2,
            "patterns": 0.1
        }
        
        # Combine weighted scores
        for result in results:
            method = result.get("method", "unknown")
            weight = method_weights.get(method, 0.1)
            category = result.get("category")
            confidence = result.get("confidence", 0)
            
            if category and confidence > 0:
                combined_scores[category] += confidence * weight
                all_reasoning.extend([f"[{method}] {r}" for r in result.get("reasoning", [])])
        
        if not combined_scores:
            return ClassificationResult(
                category="其他",
                confidence=0.5,
                reasoning=["No clear category indicators found, using default"]
            )
        
        # Find best category
        best_category = max(combined_scores, key=combined_scores.get)
        best_confidence = combined_scores[best_category]
        
        # Find best subcategory for the chosen category
        best_subcategory = None
        for result in results:
            if result.get("category") == best_category and result.get("subcategory"):
                best_subcategory = result.get("subcategory")
                break
        
        # Generate alternatives
        alternatives = []
        sorted_categories = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        for category, score in sorted_categories[1:4]:  # Top 3 alternatives
            alternatives.append({
                "category": category,
                "confidence": score,
                "reason": f"Alternative with {score:.2f} confidence"
            })
        
        return ClassificationResult(
            category=best_category,
            subcategory=best_subcategory,
            confidence=min(best_confidence, 1.0),
            reasoning=all_reasoning,
            alternative_suggestions=alternatives
        )
    
    def learn_from_feedback(self, task_content: str, predicted_category: str, 
                          actual_category: str, user_id: str = "default"):
        """Learn from user feedback to improve classification"""
        # This would update user preferences and model weights
        # For now, we'll just log the feedback
        print(f"Classification feedback: {task_content[:50]}... "
              f"predicted={predicted_category}, actual={actual_category}")


class ClassificationService(AIServiceBase):
    """Task classification service for TaskWall v3.0"""
    
    def __init__(self, db, cache=None):
        super().__init__(db, cache)
        self.classifier = TaskClassifier()
    
    def get_operation_type(self) -> AIOperationType:
        return AIOperationType.CLASSIFY
    
    def _process_internal(self, input_data: Dict[str, Any]) -> AIResult:
        """Classify tasks using various strategies"""
        
        # Handle both single task and batch classification
        if "tasks" in input_data:
            return self._classify_batch(input_data)
        else:
            return self._classify_single(input_data)
    
    def _classify_single(self, input_data: Dict[str, Any]) -> AIResult:
        """Classify a single task"""
        self._validate_input(input_data, ["task_content"])
        
        task_content = input_data["task_content"]
        user_context = input_data.get("user_context", {})
        
        # Perform classification
        result = self.classifier.classify_task(task_content, user_context)
        
        return AIResult(
            success=True,
            data={
                "category": result.category,
                "subcategory": result.subcategory,
                "confidence": result.confidence,
                "alternatives": result.alternative_suggestions
            },
            confidence=result.confidence,
            reasoning=result.reasoning,
            model_used="multi-strategy-classifier"
        )
    
    def _classify_batch(self, input_data: Dict[str, Any]) -> AIResult:
        """Classify multiple tasks"""
        self._validate_input(input_data, ["tasks"])
        
        tasks = input_data["tasks"]
        user_context = input_data.get("user_context", {})
        
        results = []
        total_confidence = 0.0
        all_reasoning = []
        
        for i, task in enumerate(tasks):
            task_content = task.get("content") or task.get("title", "")
            if not task_content:
                continue
            
            classification_result = self.classifier.classify_task(task_content, user_context)
            
            task_result = {
                "task_id": task.get("id", i),
                "original_content": task_content,
                "category": classification_result.category,
                "subcategory": classification_result.subcategory,
                "confidence": classification_result.confidence,
                "alternatives": classification_result.alternative_suggestions
            }
            
            results.append(task_result)
            total_confidence += classification_result.confidence
            if classification_result.reasoning:
                all_reasoning.extend([f"Task {i+1}: {r}" for r in classification_result.reasoning])
        
        # Calculate average confidence
        avg_confidence = total_confidence / len(results) if results else 0.0
        
        return AIResult(
            success=len(results) > 0,
            data=results,
            confidence=avg_confidence,
            reasoning=all_reasoning,
            model_used="batch-classifier"
        )
    
    def get_user_classification_preferences(self, user_id: str = "default") -> Dict[str, Any]:
        """Get user's classification preferences"""
        try:
            preferences = self.db.query(UserPreference).filter(
                UserPreference.user_id == user_id,
                UserPreference.preference_type == "classification"
            ).all()
            
            prefs = {}
            for pref in preferences:
                prefs[pref.preference_key] = json.loads(pref.preference_value)
            
            return prefs
        except Exception as e:
            print(f"Failed to load user preferences: {e}")
            return {}
    
    def update_user_classification_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Update user's classification preferences"""
        try:
            for key, value in preferences.items():
                # Check if preference already exists
                existing = self.db.query(UserPreference).filter(
                    UserPreference.user_id == user_id,
                    UserPreference.preference_type == "classification",
                    UserPreference.preference_key == key
                ).first()
                
                if existing:
                    existing.preference_value = json.dumps(value)
                    existing.updated_at = datetime.utcnow()
                else:
                    new_pref = UserPreference(
                        user_id=user_id,
                        preference_type="classification",
                        preference_key=key,
                        preference_value=json.dumps(value)
                    )
                    self.db.add(new_pref)
            
            self.db.commit()
        except Exception as e:
            print(f"Failed to update user preferences: {e}")
            self.db.rollback()