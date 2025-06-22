from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Optional
from datetime import datetime

from ..deps import get_db
from ..models import Task
from ..crud import TaskCRUD
from ..schemas import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.post("/", response_model=TaskRead)
async def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    """创建新任务"""
    task_data = task_in.dict()
    # 设置创建时间
    task_data['created_at'] = datetime.now()
    task_data['updated_at'] = datetime.now()
    
    task = Task(**task_data)
    return TaskCRUD.create(db, task)

@router.get("/", response_model=List[TaskRead])
async def get_tasks(db: Session = Depends(get_db)):
    """获取所有任务"""
    return TaskCRUD.read_all(db)

@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """获取单个任务"""
    task = TaskCRUD.read(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """更新任务"""
    task = TaskCRUD.read(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 更新修改时间
    if not hasattr(task_update, 'updated_at') or task_update.updated_at is None:
        task_update.updated_at = datetime.now()
    
    return TaskCRUD.update(db, task, task_update)

@router.patch("/{task_id}", response_model=TaskRead)
async def patch_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """部分更新任务"""
    task = TaskCRUD.read(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 确保设置更新时间
    task_update_dict = task_update.dict(exclude_unset=True)
    task_update_dict['updated_at'] = datetime.now()
    
    # 重新创建TaskUpdate对象
    final_update = TaskUpdate(**task_update_dict)
    
    return TaskCRUD.update(db, task, final_update)

@router.delete("/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务"""
    task = TaskCRUD.read(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    TaskCRUD.delete(db, task)
    return {"message": "Task deleted successfully"}

@router.patch("/{task_id}/position")
async def update_task_position(
    task_id: int, 
    x: float, 
    y: float, 
    db: Session = Depends(get_db)
):
    """更新任务位置"""
    task = TaskCRUD.read(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    position_update = TaskUpdate(x_position=x, y_position=y, updated_at=datetime.now())
    return TaskCRUD.update(db, task, position_update)

@router.get("/search/{query}")
async def search_tasks(query: str, db: Session = Depends(get_db)):
    """搜索任务"""
    all_tasks = TaskCRUD.read_all(db)
    query_lower = query.lower()
    
    matching_tasks = []
    for task in all_tasks:
        if (query_lower in task.title.lower() or 
            (task.description and query_lower in task.description.lower())):
            matching_tasks.append(task)
    
    return matching_tasks 