"""
Workload Analysis Service for TaskWall v3.0

Handles:
- Work capacity analysis
- Task distribution optimization
- Resource allocation recommendations
- Burnout prevention
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .base import AIServiceBase, AIResult, AIOperationType
from ..models import Task, PriorityLevel


class WorkloadLevel(str, Enum):
    """Workload intensity levels"""
    UNDERUTILIZED = "underutilized"
    OPTIMAL = "optimal"
    HIGH = "high"
    OVERLOADED = "overloaded"
    CRITICAL = "critical"


class TimeFrame(str, Enum):
    """Time frames for workload analysis"""
    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    THIS_QUARTER = "this_quarter"


@dataclass
class WorkloadMetrics:
    """Workload analysis metrics"""
    total_hours: float
    available_hours: float
    utilization_rate: float
    workload_level: WorkloadLevel
    task_count: int
    high_priority_count: int
    overdue_count: int
    avg_task_complexity: float
    stress_indicators: List[str]
    recommendations: List[str]
    
    def __post_init__(self):
        if self.stress_indicators is None:
            self.stress_indicators = []
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class WorkloadDistribution:
    """Workload distribution analysis"""
    by_category: Dict[str, float]
    by_priority: Dict[int, float]
    by_time_period: Dict[str, float]
    bottlenecks: List[str]
    optimization_suggestions: List[str]
    
    def __post_init__(self):
        if self.bottlenecks is None:
            self.bottlenecks = []
        if self.optimization_suggestions is None:
            self.optimization_suggestions = []


class WorkloadAnalyzer:
    """Advanced workload analysis engine"""
    
    def __init__(self):
        # Workload thresholds
        self.utilization_thresholds = {
            WorkloadLevel.UNDERUTILIZED: 0.6,
            WorkloadLevel.OPTIMAL: 0.85,
            WorkloadLevel.HIGH: 1.0,
            WorkloadLevel.OVERLOADED: 1.2,
            WorkloadLevel.CRITICAL: float('inf')
        }
        
        # Category complexity multipliers
        self.complexity_multipliers = {
            '开发': 1.3,
            '设计': 1.2,
            '测试': 1.1,
            '文档': 0.8,
            '会议': 0.9,
            '管理': 1.0
        }
        
        # Priority stress factors
        self.priority_stress_factors = {
            0: 2.0,  # Critical
            1: 1.5,  # High
            2: 1.0,  # Medium
            3: 0.7,  # Low
            4: 0.3   # Backlog
        }
        
        # Standard work hours by time frame
        self.standard_hours = {
            TimeFrame.TODAY: 8,
            TimeFrame.THIS_WEEK: 40,
            TimeFrame.THIS_MONTH: 160,
            TimeFrame.THIS_QUARTER: 480
        }
    
    def analyze_workload(
        self, 
        tasks: List[Dict[str, Any]], 
        time_frame: TimeFrame = TimeFrame.THIS_WEEK,
        context: Optional[Dict[str, Any]] = None
    ) -> WorkloadMetrics:
        """Comprehensive workload analysis"""
        
        # Filter tasks for the time frame
        filtered_tasks = self._filter_tasks_by_timeframe(tasks, time_frame)
        
        # Calculate basic metrics
        total_hours = self._calculate_total_hours(filtered_tasks)
        available_hours = self._get_available_hours(time_frame, context)
        utilization_rate = total_hours / available_hours if available_hours > 0 else 0
        
        # Determine workload level
        workload_level = self._determine_workload_level(utilization_rate)
        
        # Calculate task metrics
        task_count = len(filtered_tasks)
        high_priority_count = len([t for t in filtered_tasks if t.get('priority', t.get('urgency', 2)) <= 1])
        overdue_count = self._count_overdue_tasks(filtered_tasks)
        avg_complexity = self._calculate_average_complexity(filtered_tasks)
        
        # Identify stress indicators
        stress_indicators = self._identify_stress_indicators(
            filtered_tasks, utilization_rate, high_priority_count, overdue_count
        )
        
        # Generate recommendations
        recommendations = self._generate_workload_recommendations(
            workload_level, stress_indicators, filtered_tasks, context
        )
        
        return WorkloadMetrics(
            total_hours=total_hours,
            available_hours=available_hours,
            utilization_rate=utilization_rate,
            workload_level=workload_level,
            task_count=task_count,
            high_priority_count=high_priority_count,
            overdue_count=overdue_count,
            avg_task_complexity=avg_complexity,
            stress_indicators=stress_indicators,
            recommendations=recommendations
        )
    
    def analyze_workload_distribution(
        self, 
        tasks: List[Dict[str, Any]], 
        time_frame: TimeFrame = TimeFrame.THIS_WEEK
    ) -> WorkloadDistribution:
        """Analyze workload distribution patterns"""
        
        filtered_tasks = self._filter_tasks_by_timeframe(tasks, time_frame)
        
        # Distribution by category
        by_category = self._distribute_by_category(filtered_tasks)
        
        # Distribution by priority
        by_priority = self._distribute_by_priority(filtered_tasks)
        
        # Distribution by time period
        by_time_period = self._distribute_by_time_period(filtered_tasks, time_frame)
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(by_category, by_priority, by_time_period)
        
        # Generate optimization suggestions
        optimization_suggestions = self._generate_optimization_suggestions(
            by_category, by_priority, by_time_period, bottlenecks
        )
        
        return WorkloadDistribution(
            by_category=by_category,
            by_priority=by_priority,
            by_time_period=by_time_period,
            bottlenecks=bottlenecks,
            optimization_suggestions=optimization_suggestions
        )
    
    def predict_workload_impact(
        self, 
        current_tasks: List[Dict[str, Any]], 
        new_tasks: List[Dict[str, Any]],
        time_frame: TimeFrame = TimeFrame.THIS_WEEK
    ) -> Dict[str, Any]:
        """Predict impact of adding new tasks"""
        
        # Current workload
        current_metrics = self.analyze_workload(current_tasks, time_frame)
        
        # Projected workload with new tasks
        all_tasks = current_tasks + new_tasks
        projected_metrics = self.analyze_workload(all_tasks, time_frame)
        
        # Calculate impact
        impact = {
            "current_utilization": current_metrics.utilization_rate,
            "projected_utilization": projected_metrics.utilization_rate,
            "utilization_increase": projected_metrics.utilization_rate - current_metrics.utilization_rate,
            "current_level": current_metrics.workload_level.value,
            "projected_level": projected_metrics.workload_level.value,
            "level_change": projected_metrics.workload_level != current_metrics.workload_level,
            "additional_hours": projected_metrics.total_hours - current_metrics.total_hours,
            "additional_tasks": len(new_tasks),
            "risk_assessment": self._assess_workload_risk(projected_metrics),
            "recommendations": self._generate_impact_recommendations(
                current_metrics, projected_metrics, new_tasks
            )
        }
        
        return impact
    
    def _filter_tasks_by_timeframe(
        self, 
        tasks: List[Dict[str, Any]], 
        time_frame: TimeFrame
    ) -> List[Dict[str, Any]]:
        """Filter tasks relevant to the time frame"""
        
        now = datetime.now()
        
        if time_frame == TimeFrame.TODAY:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        elif time_frame == TimeFrame.THIS_WEEK:
            days_since_monday = now.weekday()
            start_date = now - timedelta(days=days_since_monday)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=7)
        elif time_frame == TimeFrame.THIS_MONTH:
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end_date = start_date.replace(year=now.year + 1, month=1)
            else:
                end_date = start_date.replace(month=now.month + 1)
        elif time_frame == TimeFrame.THIS_QUARTER:
            quarter = (now.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            start_date = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_month = start_month + 3
            if end_month > 12:
                end_date = start_date.replace(year=now.year + 1, month=end_month - 12)
            else:
                end_date = start_date.replace(month=end_month)
        else:
            return tasks
        
        filtered_tasks = []
        for task in tasks:
            task_in_timeframe = False
            
            # Check deadline
            deadline = task.get('deadline')
            if deadline:
                try:
                    if isinstance(deadline, str):
                        deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    else:
                        deadline_dt = deadline
                    
                    if start_date <= deadline_dt <= end_date:
                        task_in_timeframe = True
                except Exception:
                    pass
            
            # Check creation date if no deadline
            if not task_in_timeframe:
                created_at = task.get('created_at')
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            created_dt = created_at
                        
                        if created_dt >= start_date:
                            task_in_timeframe = True
                    except Exception:
                        pass
            
            # Include active tasks without specific dates
            if not task_in_timeframe and task.get('status') in ['active', 'in_progress', None]:
                task_in_timeframe = True
            
            if task_in_timeframe:
                filtered_tasks.append(task)
        
        return filtered_tasks
    
    def _calculate_total_hours(self, tasks: List[Dict[str, Any]]) -> float:
        """Calculate total estimated hours for tasks"""
        total_hours = 0.0
        
        for task in tasks:
            hours = task.get('estimated_hours', 0)
            if hours <= 0:
                # Estimate hours based on category and complexity
                hours = self._estimate_task_hours(task)
            
            # Apply complexity multiplier
            category = task.get('category', '')
            multiplier = self.complexity_multipliers.get(category, 1.0)
            total_hours += hours * multiplier
        
        return total_hours
    
    def _estimate_task_hours(self, task: Dict[str, Any]) -> float:
        """Estimate hours for a task without explicit duration"""
        
        # Base estimates by category
        category_estimates = {
            '开发': 6.0,
            '设计': 4.0,
            '测试': 3.0,
            '文档': 2.0,
            '会议': 1.0,
            '管理': 1.5
        }
        
        category = task.get('category', '')
        base_hours = category_estimates.get(category, 2.0)
        
        # Adjust based on title/description length
        title = task.get('title', '')
        description = task.get('description', '')
        
        if len(title) > 50 or len(description) > 100:
            base_hours *= 1.3
        elif len(title) < 20 and len(description) < 50:
            base_hours *= 0.7
        
        return base_hours
    
    def _get_available_hours(
        self, 
        time_frame: TimeFrame, 
        context: Optional[Dict[str, Any]]
    ) -> float:
        """Get available working hours for the time frame"""
        
        if context and 'available_hours' in context:
            return context['available_hours']
        
        # Use standard work hours
        standard = self.standard_hours.get(time_frame, 40)
        
        # Adjust for weekends and holidays if context provides info
        if context:
            work_days_per_week = context.get('work_days_per_week', 5)
            hours_per_day = context.get('hours_per_day', 8)
            
            if time_frame == TimeFrame.THIS_WEEK:
                return work_days_per_week * hours_per_day
            elif time_frame == TimeFrame.THIS_MONTH:
                return work_days_per_week * hours_per_day * 4.3  # Average weeks per month
            elif time_frame == TimeFrame.THIS_QUARTER:
                return work_days_per_week * hours_per_day * 13  # Average weeks per quarter
        
        return standard
    
    def _determine_workload_level(self, utilization_rate: float) -> WorkloadLevel:
        """Determine workload level based on utilization rate"""
        
        if utilization_rate <= self.utilization_thresholds[WorkloadLevel.UNDERUTILIZED]:
            return WorkloadLevel.UNDERUTILIZED
        elif utilization_rate <= self.utilization_thresholds[WorkloadLevel.OPTIMAL]:
            return WorkloadLevel.OPTIMAL
        elif utilization_rate <= self.utilization_thresholds[WorkloadLevel.HIGH]:
            return WorkloadLevel.HIGH
        elif utilization_rate <= self.utilization_thresholds[WorkloadLevel.OVERLOADED]:
            return WorkloadLevel.OVERLOADED
        else:
            return WorkloadLevel.CRITICAL
    
    def _count_overdue_tasks(self, tasks: List[Dict[str, Any]]) -> int:
        """Count overdue tasks"""
        now = datetime.now()
        overdue_count = 0
        
        for task in tasks:
            deadline = task.get('deadline')
            if deadline:
                try:
                    if isinstance(deadline, str):
                        deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    else:
                        deadline_dt = deadline
                    
                    if deadline_dt < now:
                        overdue_count += 1
                except Exception:
                    pass
        
        return overdue_count
    
    def _calculate_average_complexity(self, tasks: List[Dict[str, Any]]) -> float:
        """Calculate average task complexity"""
        if not tasks:
            return 0.0
        
        total_complexity = 0.0
        for task in tasks:
            # Base complexity from estimated hours
            hours = task.get('estimated_hours', 0) or self._estimate_task_hours(task)
            complexity = min(hours / 8.0, 3.0)  # Normalize to 0-3 scale
            
            # Adjust for priority (higher priority = higher perceived complexity)
            priority = task.get('priority', task.get('urgency', 2))
            priority_factor = self.priority_stress_factors.get(priority, 1.0)
            complexity *= priority_factor
            
            total_complexity += complexity
        
        return total_complexity / len(tasks)
    
    def _identify_stress_indicators(
        self, 
        tasks: List[Dict[str, Any]], 
        utilization_rate: float,
        high_priority_count: int, 
        overdue_count: int
    ) -> List[str]:
        """Identify workload stress indicators"""
        
        indicators = []
        
        if utilization_rate > 1.0:
            indicators.append(f"Utilization rate exceeds 100% ({utilization_rate:.1%})")
        
        if high_priority_count > 5:
            indicators.append(f"High number of priority tasks ({high_priority_count})")
        
        if overdue_count > 0:
            indicators.append(f"Overdue tasks present ({overdue_count})")
        
        if len(tasks) > 20:
            indicators.append(f"Large number of active tasks ({len(tasks)})")
        
        # Check for task clustering around deadlines
        deadline_clusters = self._detect_deadline_clusters(tasks)
        if deadline_clusters:
            indicators.append(f"Task clustering detected around {len(deadline_clusters)} deadlines")
        
        return indicators
    
    def _detect_deadline_clusters(self, tasks: List[Dict[str, Any]]) -> List[datetime]:
        """Detect clusters of tasks with similar deadlines"""
        deadlines = []
        
        for task in tasks:
            deadline = task.get('deadline')
            if deadline:
                try:
                    if isinstance(deadline, str):
                        deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    else:
                        deadline_dt = deadline
                    deadlines.append(deadline_dt)
                except Exception:
                    pass
        
        # Find clusters (tasks within 2 days of each other)
        clusters = []
        deadlines.sort()
        
        i = 0
        while i < len(deadlines):
            cluster_start = deadlines[i]
            cluster_tasks = 1
            j = i + 1
            
            while j < len(deadlines) and (deadlines[j] - cluster_start).days <= 2:
                cluster_tasks += 1
                j += 1
            
            if cluster_tasks >= 3:  # Cluster if 3+ tasks within 2 days
                clusters.append(cluster_start)
            
            i = j
        
        return clusters
    
    def _generate_workload_recommendations(
        self, 
        workload_level: WorkloadLevel,
        stress_indicators: List[str], 
        tasks: List[Dict[str, Any]], 
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate workload management recommendations"""
        
        recommendations = []
        
        if workload_level == WorkloadLevel.UNDERUTILIZED:
            recommendations.append("Consider taking on additional tasks or projects")
            recommendations.append("Look for opportunities to help team members")
        
        elif workload_level == WorkloadLevel.OPTIMAL:
            recommendations.append("Current workload is well-balanced")
            recommendations.append("Monitor for any upcoming deadline clusters")
        
        elif workload_level == WorkloadLevel.HIGH:
            recommendations.append("Consider prioritizing tasks and deferring non-critical items")
            recommendations.append("Look for opportunities to delegate or get help")
        
        elif workload_level == WorkloadLevel.OVERLOADED:
            recommendations.append("Urgent action needed - workload exceeds capacity")
            recommendations.append("Defer or delegate non-critical tasks immediately")
            recommendations.append("Negotiate deadline extensions where possible")
        
        elif workload_level == WorkloadLevel.CRITICAL:
            recommendations.append("Critical workload situation - immediate intervention required")
            recommendations.append("Stop taking new tasks and delegate existing ones")
            recommendations.append("Review priorities with manager or team lead")
        
        # Add specific recommendations based on stress indicators
        if "Overdue tasks present" in " ".join(stress_indicators):
            recommendations.append("Address overdue tasks as highest priority")
        
        if "Task clustering detected" in " ".join(stress_indicators):
            recommendations.append("Redistribute tasks to avoid deadline conflicts")
        
        return recommendations
    
    def _distribute_by_category(self, tasks: List[Dict[str, Any]]) -> Dict[str, float]:
        """Distribute workload by category"""
        category_hours = defaultdict(float)
        
        for task in tasks:
            category = task.get('category', '其他')
            hours = task.get('estimated_hours', 0) or self._estimate_task_hours(task)
            multiplier = self.complexity_multipliers.get(category, 1.0)
            category_hours[category] += hours * multiplier
        
        return dict(category_hours)
    
    def _distribute_by_priority(self, tasks: List[Dict[str, Any]]) -> Dict[int, float]:
        """Distribute workload by priority"""
        priority_hours = defaultdict(float)
        
        for task in tasks:
            priority = task.get('priority', task.get('urgency', 2))
            hours = task.get('estimated_hours', 0) or self._estimate_task_hours(task)
            priority_hours[priority] += hours
        
        return dict(priority_hours)
    
    def _distribute_by_time_period(
        self, 
        tasks: List[Dict[str, Any]], 
        time_frame: TimeFrame
    ) -> Dict[str, float]:
        """Distribute workload by time periods within the frame"""
        
        time_distribution = defaultdict(float)
        
        for task in tasks:
            period = self._get_task_time_period(task, time_frame)
            hours = task.get('estimated_hours', 0) or self._estimate_task_hours(task)
            time_distribution[period] += hours
        
        return dict(time_distribution)
    
    def _get_task_time_period(self, task: Dict[str, Any], time_frame: TimeFrame) -> str:
        """Determine which time period a task belongs to"""
        
        deadline = task.get('deadline')
        if not deadline:
            return "no_deadline"
        
        try:
            if isinstance(deadline, str):
                deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            else:
                deadline_dt = deadline
            
            now = datetime.now()
            
            if time_frame == TimeFrame.THIS_WEEK:
                day_diff = (deadline_dt - now).days
                if day_diff <= 1:
                    return "next_1_day"
                elif day_diff <= 3:
                    return "next_3_days"
                else:
                    return "rest_of_week"
            
            elif time_frame == TimeFrame.THIS_MONTH:
                week_diff = (deadline_dt - now).days // 7
                return f"week_{min(week_diff + 1, 4)}"
            
            else:
                return "period_1"
                
        except Exception:
            return "unknown"
    
    def _identify_bottlenecks(
        self, 
        by_category: Dict[str, float],
        by_priority: Dict[int, float], 
        by_time_period: Dict[str, float]
    ) -> List[str]:
        """Identify workload bottlenecks"""
        
        bottlenecks = []
        
        # Category bottlenecks (>40% of workload in one category)
        total_hours = sum(by_category.values())
        if total_hours > 0:
            for category, hours in by_category.items():
                if hours / total_hours > 0.4:
                    bottlenecks.append(f"Category '{category}' represents {hours/total_hours:.1%} of workload")
        
        # Priority bottlenecks (too many high-priority tasks)
        high_priority_hours = by_priority.get(0, 0) + by_priority.get(1, 0)
        if total_hours > 0 and high_priority_hours / total_hours > 0.6:
            bottlenecks.append(f"High-priority tasks represent {high_priority_hours/total_hours:.1%} of workload")
        
        # Time period bottlenecks
        if by_time_period:
            max_period_hours = max(by_time_period.values())
            total_period_hours = sum(by_time_period.values())
            if total_period_hours > 0 and max_period_hours / total_period_hours > 0.5:
                max_period = max(by_time_period.items(), key=lambda x: x[1])[0]
                bottlenecks.append(f"Time period '{max_period}' has {max_period_hours/total_period_hours:.1%} of workload")
        
        return bottlenecks
    
    def _generate_optimization_suggestions(
        self, 
        by_category: Dict[str, float],
        by_priority: Dict[int, float], 
        by_time_period: Dict[str, float],
        bottlenecks: List[str]
    ) -> List[str]:
        """Generate workload optimization suggestions"""
        
        suggestions = []
        
        if not bottlenecks:
            suggestions.append("Workload distribution appears balanced")
            return suggestions
        
        # Category-based suggestions
        if any("Category" in b for b in bottlenecks):
            suggestions.append("Consider cross-training to balance category workload")
            suggestions.append("Delegate tasks in over-represented categories")
        
        # Priority-based suggestions
        if any("High-priority" in b for b in bottlenecks):
            suggestions.append("Review priority assignments - too many high-priority tasks")
            suggestions.append("Consider breaking down large high-priority tasks")
        
        # Time-based suggestions
        if any("Time period" in b for b in bottlenecks):
            suggestions.append("Redistribute tasks to avoid deadline clustering")
            suggestions.append("Negotiate timeline adjustments for better distribution")
        
        return suggestions
    
    def _assess_workload_risk(self, metrics: WorkloadMetrics) -> str:
        """Assess overall workload risk level"""
        
        risk_score = 0
        
        # Utilization risk
        if metrics.utilization_rate > 1.2:
            risk_score += 3
        elif metrics.utilization_rate > 1.0:
            risk_score += 2
        elif metrics.utilization_rate > 0.9:
            risk_score += 1
        
        # Priority risk
        if metrics.high_priority_count > 10:
            risk_score += 3
        elif metrics.high_priority_count > 5:
            risk_score += 2
        elif metrics.high_priority_count > 3:
            risk_score += 1
        
        # Overdue risk
        if metrics.overdue_count > 0:
            risk_score += metrics.overdue_count
        
        # Complexity risk
        if metrics.avg_task_complexity > 2.5:
            risk_score += 2
        elif metrics.avg_task_complexity > 2.0:
            risk_score += 1
        
        if risk_score >= 8:
            return "critical"
        elif risk_score >= 5:
            return "high"
        elif risk_score >= 3:
            return "medium"
        else:
            return "low"
    
    def _generate_impact_recommendations(
        self, 
        current: WorkloadMetrics, 
        projected: WorkloadMetrics,
        new_tasks: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for workload impact"""
        
        recommendations = []
        
        utilization_increase = projected.utilization_rate - current.utilization_rate
        
        if utilization_increase > 0.3:
            recommendations.append("High workload increase - consider deferring some new tasks")
        
        if projected.workload_level in [WorkloadLevel.OVERLOADED, WorkloadLevel.CRITICAL]:
            recommendations.append("Projected workload exceeds safe capacity")
            recommendations.append("Recommend declining or delegating new tasks")
        
        if projected.high_priority_count > current.high_priority_count + 3:
            recommendations.append("Too many new high-priority tasks - review priorities")
        
        # Task-specific recommendations
        high_impact_tasks = [
            task for task in new_tasks 
            if task.get('estimated_hours', 0) > 8 or task.get('priority', 2) <= 1
        ]
        
        if high_impact_tasks:
            recommendations.append(f"{len(high_impact_tasks)} high-impact tasks identified - consider phased approach")
        
        return recommendations


class WorkloadService(AIServiceBase):
    """Workload analysis service for TaskWall v3.0"""
    
    def __init__(self, db, cache=None):
        super().__init__(db, cache)
        self.analyzer = WorkloadAnalyzer()
    
    def get_operation_type(self) -> AIOperationType:
        return AIOperationType.WORKLOAD
    
    def _process_internal(self, input_data: Dict[str, Any]) -> AIResult:
        """Analyze workload using various metrics"""
        
        operation = input_data.get("operation", "analyze")
        
        if operation == "analyze":
            return self._analyze_workload(input_data)
        elif operation == "distribution":
            return self._analyze_distribution(input_data)
        elif operation == "predict_impact":
            return self._predict_impact(input_data)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def _analyze_workload(self, input_data: Dict[str, Any]) -> AIResult:
        """Analyze current workload"""
        self._validate_input(input_data, ["tasks"])
        
        tasks = input_data["tasks"]
        time_frame = TimeFrame(input_data.get("time_frame", "this_week"))
        context = input_data.get("context", {})
        
        # Perform workload analysis
        metrics = self.analyzer.analyze_workload(tasks, time_frame, context)
        
        return AIResult(
            success=True,
            data={
                "total_hours": metrics.total_hours,
                "available_hours": metrics.available_hours,
                "utilization_rate": metrics.utilization_rate,
                "workload_level": metrics.workload_level.value,
                "task_count": metrics.task_count,
                "high_priority_count": metrics.high_priority_count,
                "overdue_count": metrics.overdue_count,
                "avg_task_complexity": metrics.avg_task_complexity,
                "stress_indicators": metrics.stress_indicators,
                "recommendations": metrics.recommendations
            },
            confidence=0.85,  # Workload analysis has good confidence
            reasoning=[
                f"Analyzed {metrics.task_count} tasks for {time_frame.value}",
                f"Utilization rate: {metrics.utilization_rate:.1%}",
                f"Workload level: {metrics.workload_level.value}"
            ],
            model_used="workload-analyzer"
        )
    
    def _analyze_distribution(self, input_data: Dict[str, Any]) -> AIResult:
        """Analyze workload distribution"""
        self._validate_input(input_data, ["tasks"])
        
        tasks = input_data["tasks"]
        time_frame = TimeFrame(input_data.get("time_frame", "this_week"))
        
        # Perform distribution analysis
        distribution = self.analyzer.analyze_workload_distribution(tasks, time_frame)
        
        return AIResult(
            success=True,
            data={
                "by_category": distribution.by_category,
                "by_priority": distribution.by_priority,
                "by_time_period": distribution.by_time_period,
                "bottlenecks": distribution.bottlenecks,
                "optimization_suggestions": distribution.optimization_suggestions
            },
            confidence=0.8,
            reasoning=[
                f"Analyzed workload distribution across {len(distribution.by_category)} categories",
                f"Identified {len(distribution.bottlenecks)} bottlenecks"
            ],
            model_used="distribution-analyzer"
        )
    
    def _predict_impact(self, input_data: Dict[str, Any]) -> AIResult:
        """Predict workload impact of new tasks"""
        self._validate_input(input_data, ["current_tasks", "new_tasks"])
        
        current_tasks = input_data["current_tasks"]
        new_tasks = input_data["new_tasks"]
        time_frame = TimeFrame(input_data.get("time_frame", "this_week"))
        
        # Predict impact
        impact = self.analyzer.predict_workload_impact(current_tasks, new_tasks, time_frame)
        
        return AIResult(
            success=True,
            data=impact,
            confidence=0.75,  # Impact prediction has some uncertainty
            reasoning=[
                f"Predicted impact of adding {len(new_tasks)} new tasks",
                f"Utilization increase: {impact['utilization_increase']:.1%}",
                f"Risk level: {impact['risk_assessment']}"
            ],
            model_used="impact-predictor"
        )