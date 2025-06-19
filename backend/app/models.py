from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Module(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    color: str = "#FFE58F"  # default sticky yellow
    tasks: List["Task"] = Relationship(back_populates="module")

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str = ""
    urgency: int = 2  # P0‑P4 → 0‑4
    module_id: Optional[int] = Field(default=None, foreign_key="module.id")
    parent_id: Optional[int] = Field(default=None, foreign_key="task.id")
    estimated_hours: float = 0.0  # Work hour estimation
    due_date: Optional[datetime] = None  # Due date for scheduling

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ocr_src: Optional[str] = None

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
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Setting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str

class AILog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: Optional[int] = Field(default=None, foreign_key="task.id")
    model: str
    operation: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    accepted: Optional[bool] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)