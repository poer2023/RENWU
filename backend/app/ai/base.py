"""
AI Service Base Classes and Common Components for TaskWall v3.0
"""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from sqlmodel import Session

from ..models import AILog, AIFeedback


class AIOperationType(str, Enum):
    """AI operation types"""
    PARSE = "parse"
    CLASSIFY = "classify"
    SIMILARITY = "similarity"
    PRIORITY = "priority"
    DEPENDENCY = "dependency"
    WORKLOAD = "workload"


@dataclass
class AIResult:
    """Standardized AI result format"""
    success: bool
    data: Any
    confidence: float
    reasoning: Optional[List[str]] = None
    execution_time: Optional[float] = None
    model_used: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "execution_time": self.execution_time,
            "model_used": self.model_used
        }


class AIError(Exception):
    """Custom AI service exception"""
    def __init__(self, message: str, operation: str, original_error: Optional[Exception] = None):
        self.message = message
        self.operation = operation
        self.original_error = original_error
        super().__init__(message)


class AICache:
    """AI result caching system"""
    
    def __init__(self, redis_client: Optional[Any] = None):
        self.redis_client = redis_client or self._create_redis_client()
        self.cache_ttl = {
            AIOperationType.PARSE: 3600,      # 1 hour
            AIOperationType.CLASSIFY: 7200,   # 2 hours
            AIOperationType.SIMILARITY: 1800, # 30 minutes
            AIOperationType.PRIORITY: 900,    # 15 minutes
            AIOperationType.DEPENDENCY: 1800, # 30 minutes
            AIOperationType.WORKLOAD: 600     # 10 minutes
        }
    
    def _create_redis_client(self) -> Any:
        """Create Redis client with fallback"""
        if not REDIS_AVAILABLE:
            return None
        try:
            return redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
        except Exception:
            # Return a mock client if Redis is not available
            return None
    
    def _generate_cache_key(self, operation: AIOperationType, input_data: Dict[str, Any]) -> str:
        """Generate cache key from operation and input data"""
        input_str = json.dumps(input_data, sort_keys=True)
        input_hash = hashlib.md5(input_str.encode()).hexdigest()
        return f"ai_cache:{operation.value}:{input_hash}"
    
    def get(self, operation: AIOperationType, input_data: Dict[str, Any]) -> Optional[AIResult]:
        """Get cached result"""
        if not self.redis_client:
            return None
            
        try:
            cache_key = self._generate_cache_key(operation, input_data)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                result_dict = json.loads(cached_data)
                return AIResult(
                    success=result_dict["success"],
                    data=result_dict["data"],
                    confidence=result_dict["confidence"],
                    reasoning=result_dict.get("reasoning"),
                    execution_time=result_dict.get("execution_time"),
                    model_used=result_dict.get("model_used")
                )
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    def set(self, operation: AIOperationType, input_data: Dict[str, Any], result: AIResult):
        """Cache result"""
        if not self.redis_client:
            return
            
        try:
            cache_key = self._generate_cache_key(operation, input_data)
            ttl = self.cache_ttl.get(operation, 1800)
            
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result.to_dict())
            )
        except Exception as e:
            print(f"Cache set error: {e}")


class AIMonitor:
    """AI performance and quality monitoring"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_operation(
        self,
        operation: AIOperationType,
        model: str,
        input_data: Dict[str, Any],
        result: AIResult,
        task_id: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Log AI operation for monitoring"""
        try:
            ai_log = AILog(
                task_id=task_id,
                operation=operation.value,
                model=model,
                input_data=json.dumps(input_data),
                output_data=json.dumps(result.to_dict()) if result else None,
                duration_ms=int(result.execution_time * 1000) if result and result.execution_time else 0,
                confidence=result.confidence if result else 0.0,
                error_message=error
            )
            
            self.db.add(ai_log)
            self.db.commit()
        except Exception as e:
            print(f"Failed to log AI operation: {e}")
    
    def record_feedback(
        self,
        operation: AIOperationType,
        input_data: Dict[str, Any],
        ai_result: Dict[str, Any],
        user_correction: Optional[Dict[str, Any]] = None,
        feedback_type: str = "accept"
    ):
        """Record user feedback for learning"""
        try:
            input_hash = hashlib.md5(
                json.dumps(input_data, sort_keys=True).encode()
            ).hexdigest()
            
            feedback = AIFeedback(
                operation=operation.value,
                input_hash=input_hash,
                ai_result=json.dumps(ai_result),
                user_correction=json.dumps(user_correction) if user_correction else None,
                feedback_type=feedback_type
            )
            
            self.db.add(feedback)
            self.db.commit()
        except Exception as e:
            print(f"Failed to record feedback: {e}")


class AIServiceBase(ABC):
    """Base class for all AI services"""
    
    def __init__(self, db: Session, cache: Optional[AICache] = None):
        self.db = db
        self.cache = cache or AICache()
        self.monitor = AIMonitor(db)
        self.operation_type = self.get_operation_type()
    
    @abstractmethod
    def get_operation_type(self) -> AIOperationType:
        """Return the operation type for this service"""
        pass
    
    @abstractmethod
    def _process_internal(self, input_data: Dict[str, Any]) -> AIResult:
        """Internal processing method to be implemented by subclasses"""
        pass
    
    def process(self, input_data: Dict[str, Any], use_cache: bool = True) -> AIResult:
        """Main processing method with caching and monitoring"""
        start_time = time.time()
        
        # Check cache first
        if use_cache:
            cached_result = self.cache.get(self.operation_type, input_data)
            if cached_result:
                return cached_result
        
        try:
            # Process the request
            result = self._process_internal(input_data)
            result.execution_time = time.time() - start_time
            
            # Cache the result
            if use_cache and result.success:
                self.cache.set(self.operation_type, input_data, result)
            
            # Log the operation
            self.monitor.log_operation(
                self.operation_type,
                result.model_used or "unknown",
                input_data,
                result,
                task_id=input_data.get("task_id")
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = AIResult(
                success=False,
                data=None,
                confidence=0.0,
                reasoning=[f"Error: {str(e)}"],
                execution_time=execution_time
            )
            
            # Log the error
            self.monitor.log_operation(
                self.operation_type,
                "unknown",
                input_data,
                error_result,
                task_id=input_data.get("task_id"),
                error=str(e)
            )
            
            raise AIError(
                message=f"AI {self.operation_type.value} operation failed: {str(e)}",
                operation=self.operation_type.value,
                original_error=e
            )
    
    def record_user_feedback(
        self,
        input_data: Dict[str, Any],
        ai_result: Dict[str, Any],
        user_correction: Optional[Dict[str, Any]] = None,
        feedback_type: str = "accept"
    ):
        """Record user feedback for this service"""
        self.monitor.record_feedback(
            self.operation_type,
            input_data,
            ai_result,
            user_correction,
            feedback_type
        )
    
    def _validate_input(self, input_data: Dict[str, Any], required_fields: List[str]):
        """Validate input data has required fields"""
        missing_fields = [field for field in required_fields if field not in input_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
    
    def _generate_reasoning(self, factors: Dict[str, Any]) -> List[str]:
        """Generate human-readable reasoning from factors"""
        reasoning = []
        for factor, value in factors.items():
            if isinstance(value, (int, float)):
                reasoning.append(f"{factor}: {value:.2f}")
            else:
                reasoning.append(f"{factor}: {value}")
        return reasoning