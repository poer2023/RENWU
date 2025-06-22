"""
Priority Assessment Service for TaskWall v3.0

Handles:
- Intelligent priority evaluation
- Multi-factor priority assessment
- Dynamic priority adjustment
- Deadline-based priority calculation
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .base import AIServiceBase, AIResult, AIOperationType
from ..models import Task, PriorityLevel


class PriorityFactor(str, Enum):
    """Priority assessment factors"""
    DEADLINE = "deadline"
    KEYWORD = "keyword"
    DEPENDENCY = "dependency"
    USER_CONTEXT = "user_context"
    WORKLOAD = "workload"
    BUSINESS_IMPACT = "business_impact"


@dataclass
class PriorityAssessment:
    """Priority assessment result"""
    priority_level: int
    confidence: float
    factors: Dict[str, float]
    reasoning: List[str]
    suggested_deadline: Optional[datetime] = None
    urgency_score: float = 0.0
    importance_score: float = 0.0
    
    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = []


class PriorityAnalyzer:
    """Advanced priority analysis engine"""
    
    def __init__(self):
        # Priority factor weights
        self.factor_weights = {
            PriorityFactor.DEADLINE: 0.35,        # Deadline proximity
            PriorityFactor.KEYWORD: 0.25,         # Keyword indicators
            PriorityFactor.DEPENDENCY: 0.15,      # Task dependencies
            PriorityFactor.USER_CONTEXT: 0.10,    # User patterns
            PriorityFactor.WORKLOAD: 0.10,        # Current workload
            PriorityFactor.BUSINESS_IMPACT: 0.05   # Business importance
        }
        
        # Priority keywords with weights
        self.priority_keywords = {
            0: {  # Critical/Urgent
                'keywords': ['紧急', '立即', '马上', '今天必须', '关键', '严重', 'urgent', 'critical', 'asap', 'emergency', '火急'],
                'weight': 1.0
            },
            1: {  # High
                'keywords': ['重要', '尽快', '优先', '这周', '高优先级', 'important', 'high', 'priority', '优先处理'],
                'weight': 0.8
            },
            2: {  # Medium (default)
                'keywords': ['一般', '正常', '常规', 'normal', 'medium', '中等', '普通'],
                'weight': 0.5
            },
            3: {  # Low
                'keywords': ['不急', '有时间', '低优先级', 'low', 'later', '次要', '可延后'],
                'weight': 0.3
            },
            4: {  # Backlog
                'keywords': ['以后', '有空', '备用', 'backlog', 'someday', '待办', '可选'],
                'weight': 0.1
            }
        }
        
        # Business impact keywords
        self.business_impact_keywords = {
            'high': ['客户', '生产', '收入', '安全', 'customer', 'production', 'revenue', 'security', '上线', '发布'],
            'medium': ['功能', '优化', '改进', 'feature', 'optimization', 'improvement', '测试'],
            'low': ['文档', '清理', '重构', 'documentation', 'cleanup', 'refactor', '培训']
        }
        
        # Category priority multipliers
        self.category_multipliers = {
            '开发': 1.0,
            '测试': 0.9,
            '文档': 0.6,
            '会议': 0.8,
            '设计': 0.9,
            '管理': 0.7
        }
    
    def assess_priority(
        self, 
        task_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> PriorityAssessment:
        """Comprehensive priority assessment"""
        
        factor_scores = {}
        all_reasoning = []
        
        # Factor 1: Deadline analysis
        deadline_score, deadline_reasoning = self._analyze_deadline(task_data)
        factor_scores[PriorityFactor.DEADLINE] = deadline_score
        all_reasoning.extend(deadline_reasoning)
        
        # Factor 2: Keyword analysis
        keyword_score, keyword_reasoning = self._analyze_keywords(task_data)
        factor_scores[PriorityFactor.KEYWORD] = keyword_score
        all_reasoning.extend(keyword_reasoning)
        
        # Factor 3: Dependency analysis
        dependency_score, dependency_reasoning = self._analyze_dependencies(task_data, context)
        factor_scores[PriorityFactor.DEPENDENCY] = dependency_score
        all_reasoning.extend(dependency_reasoning)
        
        # Factor 4: User context analysis
        user_score, user_reasoning = self._analyze_user_context(task_data, context)
        factor_scores[PriorityFactor.USER_CONTEXT] = user_score
        all_reasoning.extend(user_reasoning)
        
        # Factor 5: Workload analysis
        workload_score, workload_reasoning = self._analyze_workload(task_data, context)
        factor_scores[PriorityFactor.WORKLOAD] = workload_score
        all_reasoning.extend(workload_reasoning)
        
        # Factor 6: Business impact analysis
        impact_score, impact_reasoning = self._analyze_business_impact(task_data)
        factor_scores[PriorityFactor.BUSINESS_IMPACT] = impact_score
        all_reasoning.extend(impact_reasoning)
        
        # Calculate weighted priority score
        weighted_score = self._calculate_weighted_score(factor_scores)
        
        # Map to priority level (0-4)
        priority_level = self._score_to_priority_level(weighted_score)
        
        # Calculate urgency and importance separately
        urgency_score = self._calculate_urgency(factor_scores)
        importance_score = self._calculate_importance(factor_scores)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(factor_scores, task_data)
        
        # Suggest deadline if not provided
        suggested_deadline = self._suggest_deadline(priority_level, task_data)
        
        return PriorityAssessment(
            priority_level=priority_level,
            confidence=confidence,
            factors=factor_scores,
            reasoning=all_reasoning,
            suggested_deadline=suggested_deadline,
            urgency_score=urgency_score,
            importance_score=importance_score
        )
    
    def _analyze_deadline(self, task_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze deadline proximity for priority"""
        reasoning = []
        
        deadline = task_data.get('deadline')
        if not deadline:
            reasoning.append("No deadline specified")
            return 0.3, reasoning  # Neutral score for no deadline
        
        try:
            if isinstance(deadline, str):
                deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            else:
                deadline_dt = deadline
            
            now = datetime.now(deadline_dt.tzinfo) if deadline_dt.tzinfo else datetime.now()
            time_diff = (deadline_dt - now).total_seconds()
            
            if time_diff < 0:
                reasoning.append("Deadline has passed - extremely urgent")
                return 1.0, reasoning
            elif time_diff <= 3600:  # 1 hour
                reasoning.append("Deadline within 1 hour - critical")
                return 0.95, reasoning
            elif time_diff <= 86400:  # 1 day
                reasoning.append("Deadline within 1 day - very urgent")
                return 0.85, reasoning
            elif time_diff <= 259200:  # 3 days
                reasoning.append("Deadline within 3 days - urgent")
                return 0.7, reasoning
            elif time_diff <= 604800:  # 1 week
                reasoning.append("Deadline within 1 week - moderate urgency")
                return 0.5, reasoning
            elif time_diff <= 2592000:  # 1 month
                reasoning.append("Deadline within 1 month - low urgency")
                return 0.3, reasoning
            else:
                reasoning.append("Deadline more than 1 month away")
                return 0.1, reasoning
                
        except Exception as e:
            reasoning.append(f"Failed to parse deadline: {e}")
            return 0.3, reasoning
    
    def _analyze_keywords(self, task_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze priority keywords in task content"""
        reasoning = []
        
        # Combine title and description for analysis
        content = " ".join([
            task_data.get('title', ''),
            task_data.get('description', '')
        ]).lower()
        
        if not content.strip():
            reasoning.append("No content to analyze")
            return 0.5, reasoning
        
        max_score = 0.0
        matched_keywords = []
        
        # Check for priority keywords
        for priority_level, data in self.priority_keywords.items():
            keywords = data['keywords']
            weight = data['weight']
            
            for keyword in keywords:
                if keyword in content:
                    max_score = max(max_score, weight)
                    matched_keywords.append((keyword, priority_level, weight))
        
        if matched_keywords:
            best_match = max(matched_keywords, key=lambda x: x[2])
            reasoning.append(f"Found priority keyword: '{best_match[0]}' (level {best_match[1]})")
            return max_score, reasoning
        else:
            reasoning.append("No explicit priority keywords found")
            return 0.5, reasoning  # Default/neutral score
    
    def _analyze_dependencies(self, task_data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Analyze task dependencies impact on priority"""
        reasoning = []
        
        if not context:
            reasoning.append("No dependency context available")
            return 0.5, reasoning
        
        # Check if this task blocks others
        blocking_tasks = context.get('blocking_tasks', [])
        blocked_by_tasks = context.get('blocked_by_tasks', [])
        
        score = 0.5  # Base score
        
        if blocking_tasks:
            # Task that blocks others should have higher priority
            block_count = len(blocking_tasks)
            boost = min(0.4, block_count * 0.1)  # Up to 0.4 boost
            score += boost
            reasoning.append(f"Blocks {block_count} other tasks - priority boost: +{boost:.2f}")
        
        if blocked_by_tasks:
            # Task blocked by others may have lower immediate priority
            reduction = min(0.2, len(blocked_by_tasks) * 0.05)  # Up to 0.2 reduction
            score -= reduction
            reasoning.append(f"Blocked by {len(blocked_by_tasks)} tasks - priority reduction: -{reduction:.2f}")
        
        if not blocking_tasks and not blocked_by_tasks:
            reasoning.append("No dependency information available")
        
        return min(1.0, max(0.0, score)), reasoning
    
    def _analyze_user_context(self, task_data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Analyze user context and patterns"""
        reasoning = []
        
        if not context:
            reasoning.append("No user context available")
            return 0.5, reasoning
        
        score = 0.5  # Base score
        
        # User's current focus area
        current_focus = context.get('current_focus_category')
        task_category = task_data.get('category')
        
        if current_focus and task_category and current_focus.lower() == task_category.lower():
            score += 0.2
            reasoning.append(f"Matches current focus area: {current_focus}")
        
        # User's recent priority patterns
        recent_priorities = context.get('recent_priority_patterns', {})
        if recent_priorities:
            avg_priority = sum(recent_priorities.values()) / len(recent_priorities)
            if avg_priority < 2:  # User tends to set high priorities
                score += 0.1
                reasoning.append("User tends to work on high-priority tasks")
        
        # Time-based context
        current_time = context.get('current_time')
        if current_time:
            # Higher priority during work hours for work-related tasks
            if 9 <= current_time.hour <= 17:
                if task_category in ['开发', '测试', '会议', '设计']:
                    score += 0.1
                    reasoning.append("Work task during business hours")
        
        return min(1.0, max(0.0, score)), reasoning
    
    def _analyze_workload(self, task_data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Analyze current workload impact on priority"""
        reasoning = []
        
        if not context:
            reasoning.append("No workload context available")
            return 0.5, reasoning
        
        score = 0.5  # Base score
        
        # Current active tasks
        active_task_count = context.get('active_task_count', 0)
        high_priority_count = context.get('high_priority_count', 0)
        
        if active_task_count > 10:
            score -= 0.1
            reasoning.append(f"High workload ({active_task_count} active tasks) - slightly lower priority")
        elif active_task_count < 5:
            score += 0.1
            reasoning.append(f"Light workload ({active_task_count} active tasks) - can take higher priority")
        
        if high_priority_count > 5:
            score -= 0.15
            reasoning.append(f"Many high-priority tasks already ({high_priority_count}) - competing priorities")
        
        # Estimated hours vs available time
        estimated_hours = task_data.get('estimated_hours', 0)
        available_hours = context.get('available_hours_today', 8)
        
        if estimated_hours > available_hours:
            score -= 0.1
            reasoning.append(f"Task duration ({estimated_hours}h) exceeds available time ({available_hours}h)")
        
        return min(1.0, max(0.0, score)), reasoning
    
    def _analyze_business_impact(self, task_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze business impact indicators"""
        reasoning = []
        
        content = " ".join([
            task_data.get('title', ''),
            task_data.get('description', '')
        ]).lower()
        
        if not content.strip():
            reasoning.append("No content for business impact analysis")
            return 0.5, reasoning
        
        score = 0.5  # Base score
        
        # Check for high-impact keywords
        for keyword in self.business_impact_keywords['high']:
            if keyword in content:
                score += 0.2
                reasoning.append(f"High business impact keyword: '{keyword}'")
                break
        
        # Check for medium-impact keywords
        for keyword in self.business_impact_keywords['medium']:
            if keyword in content:
                score += 0.1
                reasoning.append(f"Medium business impact keyword: '{keyword}'")
                break
        
        # Check for low-impact keywords
        for keyword in self.business_impact_keywords['low']:
            if keyword in content:
                score -= 0.1
                reasoning.append(f"Low business impact keyword: '{keyword}'")
                break
        
        if score == 0.5:
            reasoning.append("No specific business impact indicators found")
        
        return min(1.0, max(0.0, score)), reasoning
    
    def _calculate_weighted_score(self, factor_scores: Dict[str, float]) -> float:
        """Calculate weighted priority score"""
        total_score = 0.0
        total_weight = 0.0
        
        for factor, score in factor_scores.items():
            weight = self.factor_weights.get(factor, 0.1)
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.5
    
    def _score_to_priority_level(self, score: float) -> int:
        """Map weighted score to priority level (0-4)"""
        if score >= 0.8:
            return 0  # Critical
        elif score >= 0.65:
            return 1  # High
        elif score >= 0.35:
            return 2  # Medium
        elif score >= 0.2:
            return 3  # Low
        else:
            return 4  # Backlog
    
    def _calculate_urgency(self, factor_scores: Dict[str, float]) -> float:
        """Calculate urgency score (time-sensitive factors)"""
        urgency_factors = [
            PriorityFactor.DEADLINE,
            PriorityFactor.DEPENDENCY,
            PriorityFactor.WORKLOAD
        ]
        
        urgency_score = 0.0
        count = 0
        
        for factor in urgency_factors:
            if factor in factor_scores:
                urgency_score += factor_scores[factor]
                count += 1
        
        return urgency_score / count if count > 0 else 0.5
    
    def _calculate_importance(self, factor_scores: Dict[str, float]) -> float:
        """Calculate importance score (value-based factors)"""
        importance_factors = [
            PriorityFactor.BUSINESS_IMPACT,
            PriorityFactor.KEYWORD,
            PriorityFactor.USER_CONTEXT
        ]
        
        importance_score = 0.0
        count = 0
        
        for factor in importance_factors:
            if factor in factor_scores:
                importance_score += factor_scores[factor]
                count += 1
        
        return importance_score / count if count > 0 else 0.5
    
    def _calculate_confidence(self, factor_scores: Dict[str, float], task_data: Dict[str, Any]) -> float:
        """Calculate assessment confidence"""
        confidence = 0.5  # Base confidence
        
        # More information available = higher confidence
        if task_data.get('title'):
            confidence += 0.1
        if task_data.get('description'):
            confidence += 0.1
        if task_data.get('deadline'):
            confidence += 0.15
        if task_data.get('category'):
            confidence += 0.1
        if task_data.get('estimated_hours'):
            confidence += 0.05
        
        # Factor diversity increases confidence
        non_default_factors = [f for f, score in factor_scores.items() if score != 0.5]
        confidence += len(non_default_factors) * 0.02
        
        return min(1.0, confidence)
    
    def _suggest_deadline(self, priority_level: int, task_data: Dict[str, Any]) -> Optional[datetime]:
        """Suggest deadline based on priority level"""
        if task_data.get('deadline'):
            return None  # Already has deadline
        
        now = datetime.now()
        
        # Suggest deadline based on priority
        if priority_level == 0:  # Critical
            return now + timedelta(hours=4)
        elif priority_level == 1:  # High
            return now + timedelta(days=1)
        elif priority_level == 2:  # Medium
            return now + timedelta(days=3)
        elif priority_level == 3:  # Low
            return now + timedelta(weeks=1)
        else:  # Backlog
            return now + timedelta(weeks=4)


class PriorityService(AIServiceBase):
    """Priority assessment service for TaskWall v3.0"""
    
    def __init__(self, db, cache=None):
        super().__init__(db, cache)
        self.analyzer = PriorityAnalyzer()
    
    def get_operation_type(self) -> AIOperationType:
        return AIOperationType.PRIORITY
    
    def _process_internal(self, input_data: Dict[str, Any]) -> AIResult:
        """Assess task priority using multiple factors"""
        
        # Handle both single task and batch processing
        if "tasks" in input_data:
            return self._assess_batch_priorities(input_data)
        else:
            return self._assess_single_priority(input_data)
    
    def _assess_single_priority(self, input_data: Dict[str, Any]) -> AIResult:
        """Assess priority for a single task"""
        self._validate_input(input_data, ["task_data"])
        
        task_data = input_data["task_data"]
        context = input_data.get("context", {})
        
        # Perform priority assessment
        assessment = self.analyzer.assess_priority(task_data, context)
        
        return AIResult(
            success=True,
            data={
                "priority_level": assessment.priority_level,
                "priority_name": PriorityLevel(assessment.priority_level).name,
                "confidence": assessment.confidence,
                "urgency_score": assessment.urgency_score,
                "importance_score": assessment.importance_score,
                "factors": assessment.factors,
                "suggested_deadline": assessment.suggested_deadline.isoformat() if assessment.suggested_deadline else None
            },
            confidence=assessment.confidence,
            reasoning=assessment.reasoning,
            model_used="multi-factor-priority-analyzer"
        )
    
    def _assess_batch_priorities(self, input_data: Dict[str, Any]) -> AIResult:
        """Assess priorities for multiple tasks"""
        self._validate_input(input_data, ["tasks"])
        
        tasks = input_data["tasks"]
        context = input_data.get("context", {})
        
        results = []
        total_confidence = 0.0
        all_reasoning = []
        
        for i, task_data in enumerate(tasks):
            assessment = self.analyzer.assess_priority(task_data, context)
            
            task_result = {
                "task_id": task_data.get("id", i),
                "original_data": task_data.get("title", f"Task {i+1}"),
                "priority_level": assessment.priority_level,
                "priority_name": PriorityLevel(assessment.priority_level).name,
                "confidence": assessment.confidence,
                "urgency_score": assessment.urgency_score,
                "importance_score": assessment.importance_score,
                "factors": assessment.factors,
                "suggested_deadline": assessment.suggested_deadline.isoformat() if assessment.suggested_deadline else None
            }
            
            results.append(task_result)
            total_confidence += assessment.confidence
            if assessment.reasoning:
                all_reasoning.extend([f"Task {i+1}: {r}" for r in assessment.reasoning])
        
        # Calculate average confidence
        avg_confidence = total_confidence / len(results) if results else 0.0
        
        return AIResult(
            success=len(results) > 0,
            data=results,
            confidence=avg_confidence,
            reasoning=all_reasoning,
            model_used="batch-priority-analyzer"
        )
    
    def compare_task_priorities(self, task1_data: Dict[str, Any], task2_data: Dict[str, Any], 
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Compare priorities between two tasks"""
        
        assessment1 = self.analyzer.assess_priority(task1_data, context)
        assessment2 = self.analyzer.assess_priority(task2_data, context)
        
        return {
            "task1_priority": assessment1.priority_level,
            "task2_priority": assessment2.priority_level,
            "higher_priority_task": 1 if assessment1.priority_level < assessment2.priority_level else 2,
            "priority_difference": abs(assessment1.priority_level - assessment2.priority_level),
            "urgency_comparison": {
                "task1_urgency": assessment1.urgency_score,
                "task2_urgency": assessment2.urgency_score,
                "more_urgent": 1 if assessment1.urgency_score > assessment2.urgency_score else 2
            },
            "importance_comparison": {
                "task1_importance": assessment1.importance_score,
                "task2_importance": assessment2.importance_score,
                "more_important": 1 if assessment1.importance_score > assessment2.importance_score else 2
            },
            "reasoning": {
                "task1": assessment1.reasoning,
                "task2": assessment2.reasoning
            }
        }
    
    def get_priority_insights(self, tasks: List[Dict[str, Any]], 
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get insights about task priorities"""
        
        if not tasks:
            return {"error": "No tasks provided"}
        
        priority_distribution = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        high_urgency_tasks = []
        high_importance_tasks = []
        overdue_tasks = []
        
        for task in tasks:
            assessment = self.analyzer.assess_priority(task, context)
            priority_distribution[assessment.priority_level] += 1
            
            if assessment.urgency_score > 0.7:
                high_urgency_tasks.append({
                    "task": task.get("title", "Untitled"),
                    "urgency_score": assessment.urgency_score
                })
            
            if assessment.importance_score > 0.7:
                high_importance_tasks.append({
                    "task": task.get("title", "Untitled"),
                    "importance_score": assessment.importance_score
                })
            
            # Check for overdue tasks
            deadline = task.get("deadline")
            if deadline:
                try:
                    if isinstance(deadline, str):
                        deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    else:
                        deadline_dt = deadline
                    
                    if deadline_dt < datetime.now(deadline_dt.tzinfo if deadline_dt.tzinfo else None):
                        overdue_tasks.append({
                            "task": task.get("title", "Untitled"),
                            "deadline": deadline_dt.isoformat()
                        })
                except Exception:
                    pass
        
        return {
            "priority_distribution": priority_distribution,
            "total_tasks": len(tasks),
            "high_urgency_tasks": high_urgency_tasks,
            "high_importance_tasks": high_importance_tasks,
            "overdue_tasks": overdue_tasks,
            "recommendations": self._generate_priority_recommendations(
                priority_distribution, len(tasks)
            )
        }
    
    def _generate_priority_recommendations(self, distribution: Dict[int, int], total: int) -> List[str]:
        """Generate priority management recommendations"""
        recommendations = []
        
        critical_count = distribution[0]
        high_count = distribution[1]
        
        if critical_count > 3:
            recommendations.append(
                f"You have {critical_count} critical tasks. Consider delegating or breaking them down."
            )
        
        if (critical_count + high_count) / total > 0.5:
            recommendations.append(
                "More than 50% of tasks are high/critical priority. Review if all are truly urgent."
            )
        
        if distribution[4] / total > 0.3:
            recommendations.append(
                "Many tasks in backlog. Consider scheduling or removing outdated items."
            )
        
        if not recommendations:
            recommendations.append("Priority distribution looks balanced.")
        
        return recommendations