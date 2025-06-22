from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from ..deps import get_db
from ..crud import HistoryCRUD, TaskCRUD
from ..schemas import HistoryRead

router = APIRouter(prefix="/api/tasks", tags=["history"])

@router.get("/{task_id}/history", response_model=List[HistoryRead])
async def read_task_history(task_id: int, db: Session = Depends(get_db)):
    """获取任务历史记录"""
    # Verify task exists
    task = TaskCRUD.read(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return HistoryCRUD.read_by_task(db, task_id) 