"""
TaskWall v3.0 AI Services Package

This package contains all AI-related services for TaskWall v3.0:
- Natural Language Processing (NLP)
- Task Classification
- Similarity Detection  
- Priority Assessment
- Dependency Analysis
- Workload Management
- Vector Database Integration
- Unified AI Service Coordination
"""

from .base import AIServiceBase, AIResult, AIError, AIOperationType, AICache, AIMonitor
from .nlp_service import NLPService
from .classification_service import ClassificationService
from .similarity_service import SimilarityService
from .priority_service import PriorityService
from .dependency_service import DependencyService
from .workload_service import WorkloadService
from .vector_db import VectorDBManager
from .aggregator import AIServiceAggregator

__all__ = [
    'AIServiceBase',
    'AIResult', 
    'AIError',
    'AIOperationType',
    'AICache',
    'AIMonitor',
    'NLPService',
    'ClassificationService',
    'SimilarityService',
    'PriorityService',
    'DependencyService',
    'WorkloadService',
    'VectorDBManager',
    'AIServiceAggregator'
]