from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
import json

# v3.0 Enums for AI features
class PriorityLevel(int, Enum):
    CRITICAL = 0    # 紧急
    HIGH = 1        # 高
    MEDIUM = 2      # 中
    LOW = 3         # 低
    BACKLOG = 4     # 待办

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"

class DependencyType(str, Enum):
    BLOCKS = "blocks"           # 阻塞关系
    ENABLES = "enables"         # 启用关系
    RELATES = "relates"         # 相关关系
    SUBTASK = "subtask"         # 子任务关系
    RESOURCE_SHARED = "shared"  # 资源共享

class Module(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    color: str = "#FFE58F"  # default sticky yellow
    tasks: List["Task"] = Relationship(back_populates="module")

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str = ""
    urgency: int = 2  # P0‑P4 → 0‑4 (backwards compatible)
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM)  # v3.0 enum priority
    status: TaskStatus = Field(default=TaskStatus.TODO)
    
    # Classification and categorization 
    module_id: Optional[int] = Field(default=None, foreign_key="module.id")
    category: Optional[str] = Field(max_length=50)
    tags: Optional[str] = Field(default="")  # JSON string storing tags list
    
    # Hierarchical structure
    parent_id: Optional[int] = Field(default=None, foreign_key="task.id")
    
    # Time information
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None  # Backwards compatibility
    
    # Work estimation
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    
    # Canvas position
    position_x: float = Field(default=0.0)
    position_y: float = Field(default=0.0)
    
    # AI-related fields
    ai_generated: bool = Field(default=False)
    ai_confidence: float = Field(default=0.0)
    ai_reasoning: Optional[str] = None
    ai_suggested_priority: Optional[int] = None
    ai_suggested_category: Optional[str] = None
    
    # Theme Island fields (backwards compatibility)
    island_id: int = Field(default=-1)  # -1 means not clustered (noise)
    island_override: Optional[int] = Field(default=None)  # Manual island assignment
    
    # OCR source (backwards compatibility)
    ocr_src: Optional[str] = None
    
    # Vector database reference
    vector_id: Optional[str] = Field(max_length=100)  # ChromaDB vector ID
    last_vector_update: Optional[datetime] = None

    module: Optional[Module] = Relationship(back_populates="tasks")
    children: List["Task"] = Relationship(back_populates="parent", sa_relationship_kwargs={"cascade": "all, delete"})
    parent: Optional["Task"] = Relationship(back_populates="children", sa_relationship_kwargs={"remote_side": "Task.id"})
    
    # Task dependencies (many-to-many through TaskDependency)
    dependencies_from: List["TaskDependency"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[TaskDependency.from_task_id]"}
    )
    dependencies_to: List["TaskDependency"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[TaskDependency.to_task_id]"}
    )
    
    def get_tags(self) -> List[str]:
        """Get tags as a list"""
        try:
            return json.loads(self.tags) if self.tags else []
        except:
            return []
    
    def set_tags(self, tags_list: List[str]):
        """Set tags from a list"""
        self.tags = json.dumps(tags_list)
    
    def get_content_for_vectorization(self) -> str:
        """Get combined content for AI vectorization"""
        content_parts = [self.title]
        if self.description:
            content_parts.append(self.description)
        if self.category:
            content_parts.append(f"Category: {self.category}")
        tags = self.get_tags()
        if tags:
            content_parts.append(f"Tags: {', '.join(tags)}")
        return " ".join(content_parts)
    
    def is_ai_enhanced(self) -> bool:
        """Check if task has AI enhancements"""
        return (self.ai_generated or 
                self.ai_confidence > 0 or 
                self.ai_suggested_priority is not None or
                self.ai_suggested_category is not None)
    
    def needs_vector_update(self) -> bool:
        """Check if task vector needs updating"""
        return (self.last_vector_update is None or 
                self.updated_at > self.last_vector_update)

class History(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    field: str
    old_val: str
    new_val: str
    ts: datetime = Field(default_factory=datetime.utcnow)

class TaskDependency(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    from_task_id: int = Field(foreign_key="task.id")
    to_task_id: int = Field(foreign_key="task.id")
    dependency_type: DependencyType = Field(default=DependencyType.BLOCKS)
    
    # AI inference related
    ai_inferred: bool = Field(default=False)
    confidence: float = Field(default=1.0)
    reasoning: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Island(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    color: str
    size: int = 0  # Number of tasks in this island
    keywords: str = "[]"  # JSON string of keywords list
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_keywords(self) -> List[str]:
        """Get keywords as a list"""
        try:
            return json.loads(self.keywords)
        except:
            return []
    
    def set_keywords(self, keywords_list: List[str]):
        """Set keywords from a list"""
        self.keywords = json.dumps(keywords_list)

class Setting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str

# v3.0 New AI-related models

class TaskVector(SQLModel, table=True):
    """Task vector storage for similarity detection"""
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id", unique=True)
    vector_id: str = Field(max_length=100)  # ChromaDB vector ID
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class AIFeedback(SQLModel, table=True):
    """User feedback on AI suggestions for learning"""
    id: Optional[int] = Field(default=None, primary_key=True)
    operation: str = Field(max_length=50)  # parse, classify, priority, etc.
    input_hash: str = Field(max_length=64)  # Input data hash
    ai_result: str = Field()  # AI result JSON
    user_correction: Optional[str] = None  # User correction JSON
    feedback_type: str = Field(max_length=20)  # accept, reject, modify
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AILog(SQLModel, table=True):
    """Enhanced AI operation logging"""
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: Optional[int] = Field(default=None, foreign_key="task.id")
    operation: str = Field(max_length=50)  # parse, classify, priority, dependency, etc.
    model: str = Field(max_length=50)  # gemini-pro, gpt-4, etc.
    
    # Input/Output tracking
    input_data: Optional[str] = None  # JSON input
    output_data: Optional[str] = None  # JSON output
    
    # Performance metrics
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    duration_ms: int = 0  # Processing time in milliseconds
    
    # Quality metrics
    confidence: float = 0.0
    accepted: Optional[bool] = None  # User acceptance
    accuracy: Optional[float] = None  # If ground truth available
    
    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserPreference(SQLModel, table=True):
    """User preferences for AI personalization"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(max_length=100, default="default")  # Future user system
    preference_type: str = Field(max_length=50)  # classification, priority, etc.
    preference_key: str = Field(max_length=100)
    preference_value: str = Field()  # JSON value
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TaskSimilarity(SQLModel, table=True):
    """Precomputed task similarity for faster lookup"""
    id: Optional[int] = Field(default=None, primary_key=True)
    task1_id: int = Field(foreign_key="task.id")
    task2_id: int = Field(foreign_key="task.id")
    similarity_score: float = Field()
    similarity_type: str = Field(max_length=20)  # semantic, temporal, etc.
    computed_at: datetime = Field(default_factory=datetime.utcnow)