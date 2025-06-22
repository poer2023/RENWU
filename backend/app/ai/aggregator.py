"""
AI Service Aggregator for TaskWall v3.0

Coordinates all AI services and provides unified interface for:
- Task parsing and creation
- Task analysis and optimization
- Intelligent recommendations
- Batch processing
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import AIServiceBase, AIResult, AIOperationType, AIError
from .nlp_service import NLPService
from .classification_service import ClassificationService
from .similarity_service import SimilarityService
from .priority_service import PriorityService
from .dependency_service import DependencyService
from .workload_service import WorkloadService
from .vector_db import VectorDBManager


@dataclass
class TaskAnalysisResult:
    """Comprehensive task analysis result"""
    nlp_result: Optional[AIResult] = None
    classification_result: Optional[AIResult] = None
    similarity_result: Optional[AIResult] = None
    priority_result: Optional[AIResult] = None
    dependency_result: Optional[AIResult] = None
    workload_result: Optional[AIResult] = None
    overall_confidence: float = 0.0
    processing_time: float = 0.0
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class TaskCreationSuggestion:
    """Task creation suggestion from AI analysis"""
    suggested_task: Dict[str, Any]
    confidence: float
    reasoning: List[str]
    ai_enhancements: Dict[str, Any]
    similar_tasks: List[Dict[str, Any]]
    
    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = []
        if self.similar_tasks is None:
            self.similar_tasks = []


class AIServiceAggregator:
    """Central coordinator for all AI services"""
    
    def __init__(self, db_session, cache=None):
        self.db = db_session
        
        # Initialize all AI services
        self.nlp_service = NLPService(db_session, cache)
        self.classification_service = ClassificationService(db_session, cache)
        self.similarity_service = SimilarityService(db_session, cache)
        self.priority_service = PriorityService(db_session, cache)
        self.dependency_service = DependencyService(db_session, cache)
        self.workload_service = WorkloadService(db_session, cache)
        
        # Vector database manager
        self.vector_db = VectorDBManager(db_session)
        
        # Service registry
        self.services = {
            AIOperationType.PARSE: self.nlp_service,
            AIOperationType.CLASSIFY: self.classification_service,
            AIOperationType.SIMILARITY: self.similarity_service,
            AIOperationType.PRIORITY: self.priority_service,
            AIOperationType.DEPENDENCY: self.dependency_service,
            AIOperationType.WORKLOAD: self.workload_service
        }
    
    def process_natural_language_task(
        self, 
        text: str, 
        context: Optional[Dict[str, Any]] = None,
        full_analysis: bool = True
    ) -> TaskCreationSuggestion:
        """Process natural language input into a complete task suggestion"""
        
        start_time = datetime.now()
        all_reasoning = []
        
        try:
            # Step 1: Parse natural language
            nlp_result = self.nlp_service.process({
                "text": text,
                "context": context or {}
            })
            
            if not nlp_result.success or not nlp_result.data:
                raise AIError("Failed to parse natural language input", "nlp")
            
            # Extract parsed task data
            parsed_tasks = nlp_result.data if isinstance(nlp_result.data, list) else [nlp_result.data]
            main_task = parsed_tasks[0]  # Use first task for analysis
            
            all_reasoning.extend(nlp_result.reasoning or [])
            
            if not full_analysis:
                # Quick processing - just return parsed task
                return TaskCreationSuggestion(
                    suggested_task=main_task,
                    confidence=nlp_result.confidence,
                    reasoning=all_reasoning,
                    ai_enhancements={},
                    similar_tasks=[]
                )
            
            # Step 2: Enhance with AI analysis (parallel processing)
            enhancements = self._enhance_task_with_ai(main_task, context)
            
            # Step 3: Find similar tasks
            similar_tasks = self._find_similar_tasks(main_task)
            
            # Step 4: Combine all results
            enhanced_task = self._merge_task_enhancements(main_task, enhancements)
            
            # Calculate overall confidence
            confidence_scores = [nlp_result.confidence]
            if enhancements.get('classification'):
                confidence_scores.append(enhancements['classification'].confidence)
            if enhancements.get('priority'):
                confidence_scores.append(enhancements['priority'].confidence)
            
            overall_confidence = sum(confidence_scores) / len(confidence_scores)
            
            # Collect all reasoning
            for service_name, result in enhancements.items():
                if result and result.reasoning:
                    all_reasoning.extend([f"[{service_name}] {r}" for r in result.reasoning])
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return TaskCreationSuggestion(
                suggested_task=enhanced_task,
                confidence=overall_confidence,
                reasoning=all_reasoning,
                ai_enhancements=enhancements,
                similar_tasks=similar_tasks
            )
            
        except Exception as e:
            raise AIError(
                f"Task processing failed: {str(e)}", 
                "aggregator", 
                original_error=e
            )
    
    def analyze_existing_task(
        self, 
        task_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> TaskAnalysisResult:
        """Perform comprehensive analysis of an existing task"""
        
        start_time = datetime.now()
        
        # Prepare analysis input
        analysis_context = context or {}
        analysis_context.update({
            "task_id": task_data.get("id"),
            "existing_task": True
        })
        
        # Run all analyses in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            
            # Classification analysis
            futures['classification'] = executor.submit(
                self._safe_service_call,
                self.classification_service,
                {"task_content": self._get_task_content(task_data), "user_context": analysis_context}
            )
            
            # Similarity analysis
            futures['similarity'] = executor.submit(
                self._safe_service_call,
                self.similarity_service,
                {"task_id": task_data.get("id"), "threshold": 0.6}
            )
            
            # Priority analysis
            futures['priority'] = executor.submit(
                self._safe_service_call,
                self.priority_service,
                {"task_data": task_data, "context": analysis_context}
            )
            
            # Dependency analysis (if other tasks provided)
            if analysis_context.get("all_tasks"):
                futures['dependency'] = executor.submit(
                    self._safe_service_call,
                    self.dependency_service,
                    {"tasks": analysis_context["all_tasks"], "context": analysis_context}
                )
            
            # Workload analysis (if user tasks provided)
            if analysis_context.get("user_tasks"):
                futures['workload'] = executor.submit(
                    self._safe_service_call,
                    self.workload_service,
                    {"tasks": analysis_context["user_tasks"], "context": analysis_context}
                )
            
            # Collect results
            results = {}
            for service_name, future in futures.items():
                try:
                    results[service_name] = future.result(timeout=30)  # 30 second timeout
                except Exception as e:
                    print(f"Service {service_name} failed: {e}")
                    results[service_name] = None
        
        # Calculate overall confidence
        confidences = [r.confidence for r in results.values() if r and r.success]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Generate recommendations
        recommendations = self._generate_task_recommendations(task_data, results, analysis_context)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return TaskAnalysisResult(
            classification_result=results.get('classification'),
            similarity_result=results.get('similarity'),
            priority_result=results.get('priority'),
            dependency_result=results.get('dependency'),
            workload_result=results.get('workload'),
            overall_confidence=overall_confidence,
            processing_time=processing_time,
            recommendations=recommendations
        )
    
    def optimize_task_list(
        self, 
        tasks: List[Dict[str, Any]], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Optimize a list of tasks using AI insights"""
        
        start_time = datetime.now()
        optimization_results = {}
        
        try:
            # Analyze workload distribution
            workload_result = self.workload_service.process({
                "operation": "analyze",
                "tasks": tasks,
                "time_frame": context.get("time_frame", "this_week"),
                "context": context or {}
            })
            
            optimization_results["workload_analysis"] = workload_result.data if workload_result.success else None
            
            # Analyze dependencies
            dependency_result = self.dependency_service.process({
                "operation": "detect",
                "tasks": tasks,
                "context": context or {}
            })
            
            optimization_results["dependencies"] = dependency_result.data if dependency_result.success else None
            
            # Get priority insights
            priority_insights = self.priority_service.get_priority_insights(tasks, context)
            optimization_results["priority_insights"] = priority_insights
            
            # Find task similarities and potential duplicates
            similar_groups = self._find_task_similarity_groups(tasks)
            optimization_results["similarity_groups"] = similar_groups
            
            # Generate optimization recommendations
            recommendations = self._generate_optimization_recommendations(
                tasks, optimization_results, context
            )
            
            # Calculate optimized task order
            optimized_order = self._calculate_optimal_task_order(tasks, optimization_results)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "original_task_count": len(tasks),
                "analysis_results": optimization_results,
                "recommendations": recommendations,
                "optimized_order": optimized_order,
                "processing_time": processing_time,
                "success": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
    
    def batch_process_tasks(
        self, 
        task_inputs: List[str], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[TaskCreationSuggestion]:
        """Process multiple natural language inputs in batch"""
        
        results = []
        
        # Process in parallel with limited concurrency
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            for i, text in enumerate(task_inputs):
                task_context = (context or {}).copy()
                task_context["batch_index"] = i
                
                future = executor.submit(
                    self.process_natural_language_task,
                    text,
                    task_context,
                    full_analysis=False  # Quick processing for batch
                )
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    # Create error result
                    error_result = TaskCreationSuggestion(
                        suggested_task={"title": "Failed to process", "error": str(e)},
                        confidence=0.0,
                        reasoning=[f"Processing failed: {str(e)}"],
                        ai_enhancements={},
                        similar_tasks=[]
                    )
                    results.append(error_result)
        
        return results
    
    def get_ai_insights(
        self, 
        user_id: str = "default", 
        time_frame: str = "this_week"
    ) -> Dict[str, Any]:
        """Get AI-powered insights about user's tasks and patterns"""
        
        try:
            # Get user's tasks from database
            from ..models import Task
            user_tasks_query = self.db.query(Task)
            
            # Filter by user if needed (assuming user_id field exists)
            # user_tasks_query = user_tasks_query.filter(Task.user_id == user_id)
            
            user_tasks = user_tasks_query.all()
            
            # Convert to dict format
            task_data = []
            for task in user_tasks:
                task_dict = {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "category": task.category,
                    "priority": task.urgency,  # Use urgency for backward compatibility
                    "status": task.status,
                    "deadline": task.deadline.isoformat() if task.deadline else None,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "estimated_hours": task.estimated_hours,
                    "tags": task.get_tags()
                }
                task_data.append(task_dict)
            
            # Generate insights
            insights = {}
            
            # Workload insights
            workload_analysis = self.workload_service.process({
                "operation": "analyze",
                "tasks": task_data,
                "time_frame": time_frame,
                "context": {"user_id": user_id}
            })
            
            if workload_analysis.success:
                insights["workload"] = workload_analysis.data
            
            # Priority insights
            priority_insights = self.priority_service.get_priority_insights(task_data)
            insights["priorities"] = priority_insights
            
            # Task similarity insights
            similarity_groups = self._find_task_similarity_groups(task_data)
            insights["potential_duplicates"] = len([g for g in similarity_groups if len(g) > 1])
            
            # Vector database stats
            if self.vector_db.is_available():
                vector_stats = self.vector_db.get_vector_stats()
                insights["vector_database"] = vector_stats
            
            # Overall recommendations
            insights["recommendations"] = self._generate_user_insights_recommendations(
                task_data, insights
            )
            
            return {
                "success": True,
                "insights": insights,
                "task_count": len(task_data),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # Helper methods
    
    def _enhance_task_with_ai(
        self, 
        task_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Enhance task with AI analysis in parallel"""
        
        enhancements = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            # Classification
            futures['classification'] = executor.submit(
                self._safe_service_call,
                self.classification_service,
                {"task_content": self._get_task_content(task_data), "user_context": context}
            )
            
            # Priority assessment
            futures['priority'] = executor.submit(
                self._safe_service_call,
                self.priority_service,
                {"task_data": task_data, "context": context}
            )
            
            # Collect results
            for service_name, future in futures.items():
                try:
                    result = future.result(timeout=15)
                    enhancements[service_name] = result
                except Exception as e:
                    print(f"Enhancement {service_name} failed: {e}")
                    enhancements[service_name] = None
        
        return enhancements
    
    def _find_similar_tasks(self, task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar existing tasks"""
        
        try:
            content = self._get_task_content(task_data)
            similar_result = self.similarity_service.process({
                "task_content": content,
                "threshold": 0.7,
                "max_results": 3
            })
            
            if similar_result.success and similar_result.data:
                return similar_result.data
        except Exception as e:
            print(f"Similarity search failed: {e}")
        
        return []
    
    def _merge_task_enhancements(
        self, 
        base_task: Dict[str, Any], 
        enhancements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge AI enhancements into the base task"""
        
        enhanced_task = base_task.copy()
        
        # Apply classification results
        if enhancements.get('classification') and enhancements['classification'].success:
            class_data = enhancements['classification'].data
            if not enhanced_task.get('category') and class_data.get('category'):
                enhanced_task['category'] = class_data['category']
        
        # Apply priority results
        if enhancements.get('priority') and enhancements['priority'].success:
            priority_data = enhancements['priority'].data
            if priority_data.get('priority_level') is not None:
                enhanced_task['ai_suggested_priority'] = priority_data['priority_level']
                enhanced_task['priority_confidence'] = priority_data['confidence']
        
        # Add AI metadata
        enhanced_task['ai_generated'] = True
        enhanced_task['ai_confidence'] = max([
            r.confidence for r in enhancements.values() 
            if r and hasattr(r, 'confidence')
        ] + [0.5])
        
        return enhanced_task
    
    def _get_task_content(self, task_data: Dict[str, Any]) -> str:
        """Extract text content from task data"""
        return " ".join([
            task_data.get('title', ''),
            task_data.get('description', ''),
            " ".join(task_data.get('tags', []))
        ]).strip()
    
    def _safe_service_call(self, service: AIServiceBase, input_data: Dict[str, Any]) -> Optional[AIResult]:
        """Safely call an AI service with error handling"""
        try:
            return service.process(input_data)
        except Exception as e:
            print(f"Service call failed: {e}")
            return None
    
    def _find_task_similarity_groups(self, tasks: List[Dict[str, Any]]) -> List[List[int]]:
        """Find groups of similar tasks"""
        
        similarity_groups = []
        processed_tasks = set()
        
        for i, task1 in enumerate(tasks):
            if i in processed_tasks:
                continue
                
            group = [i]
            
            for j, task2 in enumerate(tasks[i+1:], i+1):
                if j in processed_tasks:
                    continue
                
                # Check similarity
                try:
                    content1 = self._get_task_content(task1)
                    similar_result = self.similarity_service.process({
                        "task_content": content1,
                        "threshold": 0.8,
                        "max_results": 1
                    })
                    
                    if (similar_result.success and similar_result.data and
                        any(match.get('task_id') == task2.get('id') for match in similar_result.data)):
                        group.append(j)
                        processed_tasks.add(j)
                        
                except Exception:
                    continue
            
            if len(group) > 1:
                similarity_groups.append(group)
                processed_tasks.update(group)
        
        return similarity_groups
    
    def _generate_task_recommendations(
        self, 
        task_data: Dict[str, Any], 
        analysis_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate task-specific recommendations"""
        
        recommendations = []
        
        # Priority recommendations
        if analysis_results.get('priority') and analysis_results['priority'].success:
            priority_data = analysis_results['priority'].data
            if priority_data.get('priority_level', 2) <= 1:
                recommendations.append("Consider this a high-priority task - schedule it soon")
        
        # Similarity recommendations
        if analysis_results.get('similarity') and analysis_results['similarity'].success:
            similar_tasks = analysis_results['similarity'].data
            if similar_tasks and len(similar_tasks) > 0:
                recommendations.append(f"Found {len(similar_tasks)} similar tasks - consider if this is a duplicate")
        
        # Workload recommendations
        if analysis_results.get('workload') and analysis_results['workload'].success:
            workload_data = analysis_results['workload'].data
            if workload_data.get('workload_level') in ['overloaded', 'critical']:
                recommendations.append("Current workload is high - consider deferring this task")
        
        return recommendations
    
    def _generate_optimization_recommendations(
        self, 
        tasks: List[Dict[str, Any]], 
        analysis_results: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate task list optimization recommendations"""
        
        recommendations = []
        
        # Workload recommendations
        workload_analysis = analysis_results.get("workload_analysis")
        if workload_analysis:
            recommendations.extend(workload_analysis.get("recommendations", []))
        
        # Priority recommendations
        priority_insights = analysis_results.get("priority_insights")
        if priority_insights:
            recommendations.extend(priority_insights.get("recommendations", []))
        
        # Similarity recommendations
        similarity_groups = analysis_results.get("similarity_groups", [])
        if similarity_groups:
            recommendations.append(f"Found {len(similarity_groups)} groups of similar tasks - review for potential duplicates")
        
        return recommendations
    
    def _calculate_optimal_task_order(
        self, 
        tasks: List[Dict[str, Any]], 
        analysis_results: Dict[str, Any]
    ) -> List[int]:
        """Calculate optimal task execution order"""
        
        # Simple priority-based ordering for now
        # In practice, this would consider dependencies, deadlines, etc.
        
        task_scores = []
        
        for i, task in enumerate(tasks):
            score = 0
            
            # Priority score (lower priority number = higher score)
            priority = task.get('priority', task.get('urgency', 2))
            score += (4 - priority) * 10
            
            # Deadline score
            deadline = task.get('deadline')
            if deadline:
                try:
                    if isinstance(deadline, str):
                        deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    else:
                        deadline_dt = deadline
                    
                    days_until_deadline = (deadline_dt - datetime.now()).days
                    if days_until_deadline <= 1:
                        score += 20
                    elif days_until_deadline <= 3:
                        score += 15
                    elif days_until_deadline <= 7:
                        score += 10
                except Exception:
                    pass
            
            task_scores.append((i, score))
        
        # Sort by score (highest first)
        task_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [task_id for task_id, score in task_scores]
    
    def _generate_user_insights_recommendations(
        self, 
        tasks: List[Dict[str, Any]], 
        insights: Dict[str, Any]
    ) -> List[str]:
        """Generate user-level insights and recommendations"""
        
        recommendations = []
        
        # Workload recommendations
        workload = insights.get("workload", {})
        workload_level = workload.get("workload_level")
        if workload_level in ["overloaded", "critical"]:
            recommendations.append("Your workload is very high - consider delegating or deferring tasks")
        elif workload_level == "underutilized":
            recommendations.append("You have capacity for additional tasks")
        
        # Priority distribution recommendations
        priorities = insights.get("priorities", {})
        if priorities.get("total_tasks", 0) > 0:
            distribution = priorities.get("priority_distribution", {})
            critical_high = distribution.get(0, 0) + distribution.get(1, 0)
            total = priorities["total_tasks"]
            
            if critical_high / total > 0.6:
                recommendations.append("Too many high-priority tasks - review and adjust priorities")
        
        # Vector database recommendations
        vector_db = insights.get("vector_database", {})
        if vector_db.get("available") and vector_db.get("vector_coverage", 0) < 80:
            recommendations.append("Update task vectors for better similarity detection")
        
        return recommendations
    
    # Service status and health methods
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all AI services"""
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "vector_database": None,
            "overall_health": "unknown"
        }
        
        # Test each service
        healthy_services = 0
        total_services = len(self.services)
        
        for operation_type, service in self.services.items():
            try:
                # Simple health check - this could be more sophisticated
                test_result = True  # Placeholder
                status["services"][operation_type.value] = {
                    "healthy": test_result,
                    "last_check": datetime.now().isoformat()
                }
                if test_result:
                    healthy_services += 1
            except Exception as e:
                status["services"][operation_type.value] = {
                    "healthy": False,
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
        
        # Vector database status
        if self.vector_db.is_available():
            status["vector_database"] = self.vector_db.get_vector_stats()
        else:
            status["vector_database"] = {"available": False}
        
        # Overall health
        health_ratio = healthy_services / total_services
        if health_ratio >= 0.9:
            status["overall_health"] = "excellent"
        elif health_ratio >= 0.7:
            status["overall_health"] = "good"
        elif health_ratio >= 0.5:
            status["overall_health"] = "fair"
        else:
            status["overall_health"] = "poor"
        
        return status