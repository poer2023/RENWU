#!/usr/bin/env python3
"""
简单的API测试 - 直接测试数据库查询
"""
from fastapi import FastAPI, Depends
from sqlmodel import Session
from app.deps import get_db
from app.crud import TaskCRUD
import json

app = FastAPI()

@app.get("/test-tasks")
async def test_tasks(db: Session = Depends(get_db)):
    """测试任务查询，返回简化的JSON"""
    try:
        tasks = TaskCRUD.read_all(db, limit=5)
        
        # 手动序列化，避免Pydantic问题
        result = []
        for task in tasks:
            result.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "urgency": task.urgency,
                "island_id": task.island_id,
                "created_at": task.created_at.isoformat() if task.created_at else None
            })
        
        return {"tasks": result, "count": len(result)}
        
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

@app.get("/test-raw-tasks")
async def test_raw_tasks(db: Session = Depends(get_db)):
    """测试原始任务查询"""
    try:
        tasks = TaskCRUD.read_all(db, limit=1)
        if tasks:
            task = tasks[0]
            return {
                "raw_task": str(task.__dict__),
                "id": task.id,
                "title": task.title
            }
        return {"tasks": [], "message": "No tasks found"}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8766) 