from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from ..deps import get_db
from ..models import TaskDependency, Task
from ..crud import TaskDependencyCRUD, TaskCRUD
from ..schemas import TaskDependencyCreate, TaskDependencyRead

router = APIRouter(prefix="/api/dependencies", tags=["dependencies"])

@router.get("/", response_model=List[TaskDependencyRead])
def get_dependencies(db: Session = Depends(get_db)):
    """获取所有任务依赖关系"""
    return TaskDependencyCRUD.read_all(db)

@router.post("/", response_model=TaskDependencyRead)
def create_dependency(dependency: TaskDependencyCreate, db: Session = Depends(get_db)):
    """创建任务依赖关系"""
    # Check if both tasks exist
    from_task = TaskCRUD.read(db, dependency.from_task_id)
    to_task = TaskCRUD.read(db, dependency.to_task_id)
    
    if not from_task:
        raise HTTPException(status_code=404, detail=f"From task {dependency.from_task_id} not found")
    if not to_task:
        raise HTTPException(status_code=404, detail=f"To task {dependency.to_task_id} not found")
    
    # Check for circular dependencies
    if dependency.from_task_id == dependency.to_task_id:
        raise HTTPException(status_code=400, detail="Cannot create dependency to self")
    
    dependency_obj = TaskDependency(**dependency.dict())
    return TaskDependencyCRUD.create(db, dependency_obj)

@router.get("/task/{task_id}", response_model=List[TaskDependencyRead])
def get_task_dependencies(task_id: int, db: Session = Depends(get_db)):
    """获取特定任务的所有依赖关系"""
    # Verify task exists
    task = TaskCRUD.read(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskDependencyCRUD.read_by_task(db, task_id)

@router.delete("/{from_task_id}/{to_task_id}")
def delete_dependency(from_task_id: int, to_task_id: int, db: Session = Depends(get_db)):
    """删除任务依赖关系"""
    dependency = TaskDependencyCRUD.read_by_tasks(db, from_task_id, to_task_id)
    if not dependency:
        raise HTTPException(status_code=404, detail="Dependency not found")
    TaskDependencyCRUD.delete(db, dependency)
    return {"message": "Dependency deleted successfully"} 