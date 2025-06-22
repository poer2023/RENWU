"""
Similarity Detection Service for TaskWall v3.0

Handles:
- Task similarity detection
- Duplicate task identification
- Merge suggestions
- Similarity analytics
"""

import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .base import AIServiceBase, AIResult, AIOperationType
from .vector_db import VectorDBManager
from ..models import Task, TaskSimilarity


@dataclass
class SimilarityMatch:
    """Represents a similarity match between tasks"""
    task_id: int
    similarity_score: float
    similarity_type: str
    reasoning: List[str]
    merge_suggestion: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = []


class TaskSimilarityAnalyzer:
    """Advanced task similarity analysis"""
    
    def __init__(self):
        self.similarity_types = {
            "exact_title": 0.95,      # Exact or near-exact title match
            "semantic": 0.85,         # Semantic similarity via vectors
            "temporal": 0.75,         # Similar timing and context
            "structural": 0.70,       # Similar structure/format
            "keyword": 0.65          # Keyword overlap
        }
    
    def analyze_similarity(
        self, 
        task1: Dict[str, Any], 
        task2: Dict[str, Any],
        vector_similarity: Optional[float] = None
    ) -> SimilarityMatch:
        """Comprehensive similarity analysis between two tasks"""
        
        similarity_scores = {}
        all_reasoning = []
        
        # 1. Title similarity
        title_sim, title_reasoning = self._calculate_title_similarity(
            task1.get("title", ""), 
            task2.get("title", "")
        )
        similarity_scores["title"] = title_sim
        all_reasoning.extend(title_reasoning)
        
        # 2. Description similarity
        desc_sim, desc_reasoning = self._calculate_description_similarity(
            task1.get("description", ""), 
            task2.get("description", "")
        )
        similarity_scores["description"] = desc_sim
        all_reasoning.extend(desc_reasoning)
        
        # 3. Temporal similarity
        temporal_sim, temporal_reasoning = self._calculate_temporal_similarity(task1, task2)
        similarity_scores["temporal"] = temporal_sim
        all_reasoning.extend(temporal_reasoning)
        
        # 4. Category/Priority similarity
        meta_sim, meta_reasoning = self._calculate_metadata_similarity(task1, task2)
        similarity_scores["metadata"] = meta_sim
        all_reasoning.extend(meta_reasoning)
        
        # 5. Vector similarity (if available)
        if vector_similarity is not None:
            similarity_scores["vector"] = vector_similarity
            all_reasoning.append(f"Vector similarity: {vector_similarity:.3f}")
        
        # Determine overall similarity
        overall_similarity, similarity_type = self._calculate_overall_similarity(similarity_scores)
        
        # Generate merge suggestion if highly similar
        merge_suggestion = None
        if overall_similarity >= 0.8:
            merge_suggestion = self._generate_merge_suggestion(task1, task2, similarity_scores)
        
        return SimilarityMatch(
            task_id=task2.get("id", 0),
            similarity_score=overall_similarity,
            similarity_type=similarity_type,
            reasoning=all_reasoning,
            merge_suggestion=merge_suggestion
        )
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> Tuple[float, List[str]]:
        """Calculate title similarity with detailed analysis"""
        reasoning = []
        
        if not title1 or not title2:
            reasoning.append("One or both titles empty")
            return 0.0, reasoning
        
        # Normalize titles
        norm_title1 = self._normalize_text(title1)
        norm_title2 = self._normalize_text(title2)
        
        # Exact match
        if norm_title1 == norm_title2:
            reasoning.append("Exact title match")
            return 1.0, reasoning
        
        # Sequence similarity
        seq_sim = SequenceMatcher(None, norm_title1, norm_title2).ratio()
        reasoning.append(f"Sequence similarity: {seq_sim:.3f}")
        
        # Keyword overlap
        words1 = set(norm_title1.split())
        words2 = set(norm_title2.split())
        
        if words1 and words2:
            overlap_ratio = len(words1 & words2) / len(words1 | words2)
            reasoning.append(f"Keyword overlap: {overlap_ratio:.3f}")
            
            # Combine sequence and keyword similarity
            combined_sim = max(seq_sim, overlap_ratio * 0.8)
        else:
            combined_sim = seq_sim
        
        # Check for common patterns
        if self._has_common_patterns(title1, title2):
            combined_sim = min(1.0, combined_sim + 0.1)
            reasoning.append("Common task patterns detected")
        
        return combined_sim, reasoning
    
    def _calculate_description_similarity(self, desc1: str, desc2: str) -> Tuple[float, List[str]]:
        """Calculate description similarity"""
        reasoning = []
        
        if not desc1 and not desc2:
            reasoning.append("Both descriptions empty")
            return 0.5, reasoning  # Neutral similarity
        
        if not desc1 or not desc2:
            reasoning.append("One description empty")
            return 0.2, reasoning  # Low similarity
        
        # Normalize descriptions
        norm_desc1 = self._normalize_text(desc1)
        norm_desc2 = self._normalize_text(desc2)
        
        # Sequence similarity
        seq_sim = SequenceMatcher(None, norm_desc1, norm_desc2).ratio()
        reasoning.append(f"Description sequence similarity: {seq_sim:.3f}")
        
        return seq_sim, reasoning
    
    def _calculate_temporal_similarity(self, task1: Dict[str, Any], task2: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Calculate temporal similarity (deadlines, creation time)"""
        reasoning = []
        
        # Compare deadlines
        deadline1 = task1.get("deadline")
        deadline2 = task2.get("deadline")
        
        deadline_sim = 0.0
        if deadline1 and deadline2:
            try:
                if isinstance(deadline1, str):
                    deadline1 = datetime.fromisoformat(deadline1.replace('Z', '+00:00'))
                if isinstance(deadline2, str):
                    deadline2 = datetime.fromisoformat(deadline2.replace('Z', '+00:00'))
                
                time_diff = abs((deadline1 - deadline2).total_seconds())
                
                # Similar deadlines within a day
                if time_diff <= 86400:  # 1 day
                    deadline_sim = 1.0
                    reasoning.append("Deadlines within 1 day")
                elif time_diff <= 604800:  # 1 week
                    deadline_sim = 0.7
                    reasoning.append("Deadlines within 1 week")
                elif time_diff <= 2592000:  # 1 month
                    deadline_sim = 0.3
                    reasoning.append("Deadlines within 1 month")
                else:
                    deadline_sim = 0.0
                    reasoning.append("Deadlines far apart")
                    
            except Exception as e:
                reasoning.append(f"Failed to parse deadlines: {e}")
        elif not deadline1 and not deadline2:
            deadline_sim = 0.5  # Both have no deadline
            reasoning.append("Both tasks have no deadline")
        else:
            deadline_sim = 0.1  # One has deadline, one doesn't
            reasoning.append("Deadline mismatch (one has deadline, one doesn't)")
        
        # Compare creation times
        created1 = task1.get("created_at")
        created2 = task2.get("created_at")
        
        creation_sim = 0.0
        if created1 and created2:
            try:
                if isinstance(created1, str):
                    created1 = datetime.fromisoformat(created1.replace('Z', '+00:00'))
                if isinstance(created2, str):
                    created2 = datetime.fromisoformat(created2.replace('Z', '+00:00'))
                
                time_diff = abs((created1 - created2).total_seconds())
                
                # Tasks created close together are more likely similar
                if time_diff <= 3600:  # 1 hour
                    creation_sim = 0.8
                    reasoning.append("Created within 1 hour")
                elif time_diff <= 86400:  # 1 day
                    creation_sim = 0.5
                    reasoning.append("Created within 1 day")
                elif time_diff <= 604800:  # 1 week
                    creation_sim = 0.2
                    reasoning.append("Created within 1 week")
                else:
                    creation_sim = 0.0
                    reasoning.append("Created far apart")
                    
            except Exception as e:
                reasoning.append(f"Failed to parse creation times: {e}")
        
        # Combine temporal similarities
        temporal_sim = (deadline_sim * 0.7 + creation_sim * 0.3)
        
        return temporal_sim, reasoning
    
    def _calculate_metadata_similarity(self, task1: Dict[str, Any], task2: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Calculate metadata similarity (category, priority, etc.)"""
        reasoning = []
        similarities = []
        
        # Category similarity
        cat1 = task1.get("category", "").lower()
        cat2 = task2.get("category", "").lower()
        
        if cat1 and cat2:
            if cat1 == cat2:
                similarities.append(1.0)
                reasoning.append(f"Same category: {cat1}")
            else:
                similarities.append(0.0)
                reasoning.append(f"Different categories: {cat1} vs {cat2}")
        else:
            similarities.append(0.5)  # Neutral if missing
            reasoning.append("Category information missing")
        
        # Priority similarity
        prio1 = task1.get("priority", task1.get("urgency", 2))
        prio2 = task2.get("priority", task2.get("urgency", 2))
        
        if prio1 is not None and prio2 is not None:
            prio_diff = abs(prio1 - prio2)
            prio_sim = max(0, 1 - prio_diff / 4.0)  # Priority range 0-4
            similarities.append(prio_sim)
            reasoning.append(f"Priority similarity: {prio_sim:.3f} (diff: {prio_diff})")
        else:
            similarities.append(0.5)
            reasoning.append("Priority information missing")
        
        # Tags similarity
        tags1 = set(task1.get("tags", []))
        tags2 = set(task2.get("tags", []))
        
        if tags1 or tags2:
            if tags1 and tags2:
                tag_overlap = len(tags1 & tags2) / len(tags1 | tags2)
                similarities.append(tag_overlap)
                reasoning.append(f"Tag overlap: {tag_overlap:.3f}")
            else:
                similarities.append(0.0)
                reasoning.append("One task has tags, other doesn't")
        else:
            similarities.append(0.5)  # Both have no tags
            reasoning.append("Both tasks have no tags")
        
        # Calculate average metadata similarity
        meta_sim = sum(similarities) / len(similarities) if similarities else 0.0
        
        return meta_sim, reasoning
    
    def _calculate_overall_similarity(self, scores: Dict[str, float]) -> Tuple[float, str]:
        """Calculate overall similarity score and determine type"""
        
        # Weights for different similarity types
        weights = {
            "title": 0.4,
            "description": 0.2,
            "vector": 0.25,
            "temporal": 0.1,
            "metadata": 0.05
        }
        
        # Calculate weighted average
        total_weight = 0
        weighted_sum = 0
        
        for score_type, score in scores.items():
            weight = weights.get(score_type, 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Determine similarity type based on highest individual scores
        max_score_type = max(scores.items(), key=lambda x: x[1])
        
        if max_score_type[1] >= 0.95:
            similarity_type = "exact_match"
        elif scores.get("vector", 0) >= 0.85:
            similarity_type = "semantic"
        elif scores.get("title", 0) >= 0.8:
            similarity_type = "title_match"
        elif scores.get("temporal", 0) >= 0.7:
            similarity_type = "temporal"
        else:
            similarity_type = "general"
        
        return overall_score, similarity_type
    
    def _generate_merge_suggestion(
        self, 
        task1: Dict[str, Any], 
        task2: Dict[str, Any], 
        similarity_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate suggestion for merging similar tasks"""
        
        # Determine which task to keep as primary
        primary_task = task1
        secondary_task = task2
        
        # Prefer task with more complete information
        task1_completeness = self._calculate_completeness(task1)
        task2_completeness = self._calculate_completeness(task2)
        
        if task2_completeness > task1_completeness:
            primary_task, secondary_task = task2, task1
        
        # Generate merged task suggestion
        merged_task = {
            "title": primary_task.get("title", ""),
            "description": self._merge_descriptions(
                primary_task.get("description", ""),
                secondary_task.get("description", "")
            ),
            "priority": min(
                primary_task.get("priority", primary_task.get("urgency", 2)),
                secondary_task.get("priority", secondary_task.get("urgency", 2))
            ),
            "category": primary_task.get("category") or secondary_task.get("category"),
            "tags": list(set(
                primary_task.get("tags", []) + secondary_task.get("tags", [])
            )),
            "deadline": self._choose_earlier_deadline(
                primary_task.get("deadline"),
                secondary_task.get("deadline")
            ),
            "estimated_hours": max(
                primary_task.get("estimated_hours", 0),
                secondary_task.get("estimated_hours", 0)
            )
        }
        
        # Calculate merge confidence
        merge_confidence = sum(similarity_scores.values()) / len(similarity_scores)
        
        return {
            "recommended": merge_confidence >= 0.8,
            "confidence": merge_confidence,
            "primary_task_id": primary_task.get("id"),
            "secondary_task_id": secondary_task.get("id"),
            "merged_task": merged_task,
            "reasoning": [
                f"High similarity detected ({merge_confidence:.2f})",
                f"Primary task chosen based on completeness",
                f"Merge would combine best attributes of both tasks"
            ]
        }
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _has_common_patterns(self, text1: str, text2: str) -> bool:
        """Check for common task patterns"""
        patterns = [
            r'(修复|fix).*bug',
            r'(开发|develop).*功能',
            r'(测试|test).*',
            r'(会议|meeting).*',
            r'(文档|document).*'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text1, re.IGNORECASE) and re.search(pattern, text2, re.IGNORECASE):
                return True
        
        return False
    
    def _calculate_completeness(self, task: Dict[str, Any]) -> float:
        """Calculate task information completeness"""
        completeness = 0.0
        
        if task.get("title"):
            completeness += 0.3
        if task.get("description"):
            completeness += 0.2
        if task.get("category"):
            completeness += 0.15
        if task.get("deadline"):
            completeness += 0.15
        if task.get("tags"):
            completeness += 0.1
        if task.get("estimated_hours", 0) > 0:
            completeness += 0.1
        
        return completeness
    
    def _merge_descriptions(self, desc1: str, desc2: str) -> str:
        """Merge two descriptions intelligently"""
        if not desc1 and not desc2:
            return ""
        if not desc1:
            return desc2
        if not desc2:
            return desc1
        
        # If descriptions are very similar, use the longer one
        similarity = SequenceMatcher(None, desc1.lower(), desc2.lower()).ratio()
        if similarity > 0.8:
            return desc1 if len(desc1) > len(desc2) else desc2
        
        # Otherwise, combine them
        return f"{desc1}\n\n补充信息: {desc2}"
    
    def _choose_earlier_deadline(self, deadline1: Any, deadline2: Any) -> Any:
        """Choose the earlier deadline"""
        if not deadline1:
            return deadline2
        if not deadline2:
            return deadline1
        
        try:
            if isinstance(deadline1, str):
                deadline1 = datetime.fromisoformat(deadline1.replace('Z', '+00:00'))
            if isinstance(deadline2, str):
                deadline2 = datetime.fromisoformat(deadline2.replace('Z', '+00:00'))
            
            return deadline1 if deadline1 < deadline2 else deadline2
        except:
            return deadline1  # Fallback


class SimilarityService(AIServiceBase):
    """Similarity detection service for TaskWall v3.0"""
    
    def __init__(self, db, cache=None):
        super().__init__(db, cache)
        self.analyzer = TaskSimilarityAnalyzer()
        self.vector_db = VectorDBManager(db)
    
    def get_operation_type(self) -> AIOperationType:
        return AIOperationType.SIMILARITY
    
    def _process_internal(self, input_data: Dict[str, Any]) -> AIResult:
        """Find similar tasks for given task or content"""
        
        if "task_content" in input_data:
            return self._find_similar_by_content(input_data)
        elif "task_id" in input_data:
            return self._find_similar_by_task_id(input_data)
        else:
            raise ValueError("Either 'task_content' or 'task_id' must be provided")
    
    def _find_similar_by_content(self, input_data: Dict[str, Any]) -> AIResult:
        """Find similar tasks by content"""
        self._validate_input(input_data, ["task_content"])
        
        content = input_data["task_content"]
        threshold = input_data.get("threshold", 0.7)
        max_results = input_data.get("max_results", 5)
        
        similar_matches = []
        reasoning = []
        
        # 1. Vector-based similarity search
        if self.vector_db.is_available():
            vector_results = self.vector_db.find_similar_tasks(
                content=content,
                n_results=max_results * 2,
                threshold=threshold * 0.8  # Lower threshold for vector search
            )
            
            reasoning.append(f"Vector search found {len(vector_results)} candidates")
            
            # Get detailed task information for analysis
            for vector_result in vector_results:
                task_id = vector_result["task_id"]
                task = self.db.query(Task).filter(Task.id == task_id).first()
                
                if task:
                    # Prepare task data for analysis
                    task_data = {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "category": task.category,
                        "priority": task.urgency,  # Use urgency for backward compatibility
                        "tags": task.get_tags(),
                        "deadline": task.deadline.isoformat() if task.deadline else None,
                        "created_at": task.created_at.isoformat(),
                        "estimated_hours": task.estimated_hours
                    }
                    
                    # Analyze detailed similarity
                    query_data = {"title": content, "description": ""}
                    similarity_match = self.analyzer.analyze_similarity(
                        query_data, 
                        task_data,
                        vector_similarity=vector_result["similarity"]
                    )
                    
                    if similarity_match.similarity_score >= threshold:
                        similar_matches.append({
                            "task_id": task.id,
                            "task_title": task.title,
                            "similarity_score": similarity_match.similarity_score,
                            "similarity_type": similarity_match.similarity_type,
                            "reasoning": similarity_match.reasoning,
                            "merge_suggestion": similarity_match.merge_suggestion
                        })
        
        # 2. Fallback: Rule-based similarity if vector search unavailable
        if not similar_matches and not self.vector_db.is_available():
            reasoning.append("Using fallback rule-based similarity")
            similar_matches = self._fallback_similarity_search(content, threshold, max_results)
        
        # Sort by similarity score
        similar_matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        similar_matches = similar_matches[:max_results]
        
        # Calculate overall confidence
        avg_confidence = sum(m["similarity_score"] for m in similar_matches) / len(similar_matches) if similar_matches else 0.0
        
        return AIResult(
            success=True,
            data=similar_matches,
            confidence=avg_confidence,
            reasoning=reasoning,
            model_used="vector+rule-based" if self.vector_db.is_available() else "rule-based"
        )
    
    def _find_similar_by_task_id(self, input_data: Dict[str, Any]) -> AIResult:
        """Find similar tasks by existing task ID"""
        self._validate_input(input_data, ["task_id"])
        
        task_id = input_data["task_id"]
        threshold = input_data.get("threshold", 0.7)
        max_results = input_data.get("max_results", 5)
        
        # Get the source task
        source_task = self.db.query(Task).filter(Task.id == task_id).first()
        if not source_task:
            return AIResult(
                success=False,
                data=[],
                confidence=0.0,
                reasoning=["Source task not found"],
                model_used="error"
            )
        
        # Use task content for similarity search
        content = source_task.get_content_for_vectorization()
        
        # Call content-based search, excluding the source task
        search_input = {
            "task_content": content,
            "threshold": threshold,
            "max_results": max_results,
            "exclude_task_id": task_id
        }
        
        result = self._find_similar_by_content(search_input)
        
        # Filter out the source task from results
        if result.success and result.data:
            result.data = [
                match for match in result.data 
                if match["task_id"] != task_id
            ]
        
        return result
    
    def _fallback_similarity_search(self, content: str, threshold: float, max_results: int) -> List[Dict[str, Any]]:
        """Fallback rule-based similarity search when vector DB unavailable"""
        similar_matches = []
        
        # Get all tasks for comparison
        all_tasks = self.db.query(Task).all()
        
        for task in all_tasks:
            task_data = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "category": task.category,
                "priority": task.urgency,
                "tags": task.get_tags(),
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "created_at": task.created_at.isoformat(),
                "estimated_hours": task.estimated_hours
            }
            
            query_data = {"title": content, "description": ""}
            similarity_match = self.analyzer.analyze_similarity(query_data, task_data)
            
            if similarity_match.similarity_score >= threshold:
                similar_matches.append({
                    "task_id": task.id,
                    "task_title": task.title,
                    "similarity_score": similarity_match.similarity_score,
                    "similarity_type": similarity_match.similarity_type,
                    "reasoning": similarity_match.reasoning,
                    "merge_suggestion": similarity_match.merge_suggestion
                })
        
        return similar_matches