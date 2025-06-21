from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class ModuleBase(BaseModel):
    name: str
    color: str = "#FFE58F"

class ModuleCreate(ModuleBase):
    pass

class ModuleRead(ModuleBase):
    id: int

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    title: str
    description: str = ""
    urgency: int = 2
    module_id: Optional[int] = None
    parent_id: Optional[int] = None
    estimated_hours: float = 0.0
    due_date: Optional[datetime] = None
    island_id: int = -1
    island_override: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskRead(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    ocr_src: Optional[str] = None

    class Config:
        from_attributes = True

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    urgency: Optional[int] = None
    module_id: Optional[int] = None
    parent_id: Optional[int] = None
    estimated_hours: Optional[float] = None
    due_date: Optional[datetime] = None

class HistoryRead(BaseModel):
    id: int
    task_id: int
    field: str
    old_val: str
    new_val: str
    ts: datetime

    class Config:
        from_attributes = True

class SettingBase(BaseModel):
    key: str
    value: str

class SettingCreate(SettingBase):
    pass

class SettingRead(SettingBase):
    class Config:
        from_attributes = True

class AIParseRequest(BaseModel):
    prompt: str

class AIParseResponse(BaseModel):
    tasks: List[dict]

class AIAssistantRequest(BaseModel):
    command: str  # 'rewrite', 'add-emoji', 'summarize', 'make-subtasks'
    content: str
    context: Optional[str] = None

class AIAssistantResponse(BaseModel):
    result: str
    success: bool = True
    error: Optional[str] = None

class AISubtaskRequest(BaseModel):
    parent_task_title: str
    parent_task_description: str
    max_subtasks: int = 5

class AISubtaskResponse(BaseModel):
    subtasks: List[dict]
    success: bool = True
    error: Optional[str] = None

class WeeklyReportRequest(BaseModel):
    start_date: Optional[str] = None  # ISO format date, defaults to 7 days ago
    end_date: Optional[str] = None    # ISO format date, defaults to today

class WeeklyReportResponse(BaseModel):
    report: str
    success: bool = True
    error: Optional[str] = None

class WorkloadAnalysisRequest(BaseModel):
    date: Optional[str] = None  # ISO format date, defaults to today

class WorkloadAnalysisResponse(BaseModel):
    total_hours: float
    capacity_hours: float = 6.0  # Default daily capacity
    workload_percentage: float
    conflict_level: str  # 'green', 'yellow', 'red'
    tasks: List[dict]
    success: bool = True
    error: Optional[str] = None

class SimilarTaskRequest(BaseModel):
    task_title: str
    task_description: str = ""
    similarity_threshold: float = 0.85

class SimilarTaskResponse(BaseModel):
    similar_tasks: List[dict]
    suggestions: List[str]  # merge/link suggestions
    success: bool = True
    error: Optional[str] = None

class RiskAnalysisRequest(BaseModel):
    tasks: Optional[List[dict]] = None  # If not provided, analyze all tasks

class RiskAnalysisResponse(BaseModel):
    risk_summary: dict
    risky_tasks: List[dict]
    suggestions: List[str]
    success: bool = True
    error: Optional[str] = None

class ThemeIslandRequest(BaseModel):
    tasks: Optional[List[dict]] = None  # If not provided, analyze all tasks

class ThemeIslandResponse(BaseModel):
    islands: List[dict]  # List of theme islands with tasks
    island_stats: dict
    suggestions: List[str]
    success: bool = True
    error: Optional[str] = None

class TaskDependencyBase(BaseModel):
    from_task_id: int
    to_task_id: int

class TaskDependencyCreate(TaskDependencyBase):
    pass

class TaskDependencyRead(TaskDependencyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Island schemas
class IslandBase(BaseModel):
    name: str
    color: str
    size: int = 0
    keywords: List[str] = []

class IslandCreate(IslandBase):
    pass

class IslandRead(IslandBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True