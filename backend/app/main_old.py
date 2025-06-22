import os
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, Session
from typing import List

from .deps import engine, get_db
from .models import Task, Module, History, Setting, TaskDependency, Island
from .crud import TaskCRUD, ModuleCRUD, HistoryCRUD, SettingCRUD, TaskDependencyCRUD, IslandCRUD
from .schemas import (
    TaskCreate, TaskRead, TaskUpdate,
    ModuleCreate, ModuleRead,
    HistoryRead,
    SettingCreate, SettingRead,
    AIParseRequest, AIParseResponse,
    AIAssistantRequest, AIAssistantResponse,
    AISubtaskRequest, AISubtaskResponse,
    WeeklyReportRequest, WeeklyReportResponse,
    WorkloadAnalysisRequest, WorkloadAnalysisResponse,
    SimilarTaskRequest, SimilarTaskResponse,
    RiskAnalysisRequest, RiskAnalysisResponse,
    ThemeIslandRequest, ThemeIslandResponse,
    TaskDependencyCreate, TaskDependencyRead,
    IslandCreate, IslandRead
)
from .routers import ai_v3, tasks, modules, dependencies, settings, history, export_backup, ocr
from .utils.ocr import extract_text
from .utils.ai_client import ask, assistant_command, generate_subtasks, generate_weekly_report, find_similar_tasks, analyze_task_risks, create_theme_islands
from .utils.export import ExportService
from .utils.backup import backup_service

# Create database tables
SQLModel.metadata.create_all(engine)

app = FastAPI(title="TaskWall API", version="1.0.0")

# Start backup scheduler on startup
@app.on_event("startup")
async def startup_event():
    # Get backup interval from settings (default 4 hours)
    try:
        with Session(engine) as db:
            interval_setting = SettingCRUD.read(db, "backup_interval_hours")
            interval = int(interval_setting.value) if interval_setting else 4
            backup_service.start_scheduler(interval)
    except Exception as e:
        print(f"Failed to start backup scheduler: {e}")
        backup_service.start_scheduler(4)  # fallback to 4 hours

@app.on_event("shutdown")
async def shutdown_event():
    backup_service.stop_scheduler()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ai_v3.router)
app.include_router(tasks.router)
app.include_router(modules.router)
app.include_router(dependencies.router)
app.include_router(settings.router)
app.include_router(history.router)
app.include_router(export_backup.router)
app.include_router(ocr.router)

# Mount static files for exports/backups
app.mount("/static", StaticFiles(directory="data"), name="static")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "TaskWall API is running"}

@app.get("/")
async def root():
    return {"message": "TaskWall API", "status": "running"}

# Task endpoints
@app.post("/tasks/", response_model=TaskRead)
async def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    # 转换任务数据，确保priority字段类型正确
    task_data = task_in.dict()
    
    # 处理priority字段的类型转换
    if 'priority' in task_data:
        priority_value = task_data['priority']
        if isinstance(priority_value, str):
            # 如果是字符串，尝试转换为对应的整数枚举值
            priority_mapping = {
                'CRITICAL': 0, 'URGENT': 0, 'HIGH': 1, 
                'MEDIUM': 2, 'LOW': 3, 'BACKLOG': 4
            }
            task_data['priority'] = priority_mapping.get(priority_value.upper(), 2)
        elif isinstance(priority_value, int):
            # 确保整数值在有效范围内
            task_data['priority'] = max(0, min(4, priority_value))
    
    # 处理status字段的类型转换
    if 'status' in task_data:
        status_value = task_data['status']
        if isinstance(status_value, str):
            # 确保状态字符串是有效的TaskStatus值
            valid_statuses = ['todo', 'in_progress', 'done', 'archived']
            if status_value.lower() not in valid_statuses:
                task_data['status'] = 'todo'  # 默认状态
    
    task = Task(**task_data)
    return TaskCRUD.create(db, task)

@app.get("/tasks/", response_model=List[TaskRead])
async def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return TaskCRUD.read_all(db, skip=skip, limit=limit)

@app.get("/tasks/{task_id}", response_model=TaskRead)
async def read_task(task_id: int, db: Session = Depends(get_db)):
    task = TaskCRUD.read(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task_in: TaskUpdate, db: Session = Depends(get_db)):
    task = TaskCRUD.read(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 转换更新数据，确保priority和status字段类型正确
    update_data = task_in.dict(exclude_unset=True)
    
    # 处理priority字段的类型转换
    if 'priority' in update_data and update_data['priority'] is not None:
        priority_value = update_data['priority']
        if isinstance(priority_value, str):
            # 如果是字符串，尝试转换为对应的整数枚举值
            priority_mapping = {
                'CRITICAL': 0, 'URGENT': 0, 'HIGH': 1, 
                'MEDIUM': 2, 'LOW': 3, 'BACKLOG': 4
            }
            update_data['priority'] = priority_mapping.get(priority_value.upper(), 2)
        elif isinstance(priority_value, int):
            # 确保整数值在有效范围内
            update_data['priority'] = max(0, min(4, priority_value))
    
    # 处理status字段的类型转换
    if 'status' in update_data and update_data['status'] is not None:
        status_value = update_data['status']
        if isinstance(status_value, str):
            # 确保状态字符串是有效的TaskStatus值
            valid_statuses = ['todo', 'in_progress', 'done', 'archived']
            if status_value.lower() not in valid_statuses:
                update_data['status'] = 'todo'  # 默认状态
    
    # 创建TaskUpdate对象用于更新
    task_update = TaskUpdate(**update_data)
    return TaskCRUD.update(db, task, task_update)

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = TaskCRUD.read(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    TaskCRUD.delete(db, task)
    return {"message": "Task deleted successfully"}

# Module endpoints
@app.post("/modules/", response_model=ModuleRead)
async def create_module(module_in: ModuleCreate, db: Session = Depends(get_db)):
    module = Module(**module_in.dict())
    return ModuleCRUD.create(db, module)

@app.get("/modules/", response_model=List[ModuleRead])
async def read_modules(db: Session = Depends(get_db)):
    return ModuleCRUD.read_all(db)

@app.get("/modules/{module_id}", response_model=ModuleRead)
async def read_module(module_id: int, db: Session = Depends(get_db)):
    module = ModuleCRUD.read(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module

@app.delete("/modules/{module_id}")
async def delete_module(module_id: int, db: Session = Depends(get_db)):
    module = ModuleCRUD.read(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    ModuleCRUD.delete(db, module)
    return {"message": "Module deleted successfully"}

# History endpoints
@app.get("/tasks/{task_id}/history", response_model=List[HistoryRead])
async def read_task_history(task_id: int, db: Session = Depends(get_db)):
    # Verify task exists
    task = TaskCRUD.read(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return HistoryCRUD.read_by_task(db, task_id)

# Settings endpoints
@app.get("/settings/", response_model=List[SettingRead])
async def read_settings(db: Session = Depends(get_db)):
    return SettingCRUD.read_all(db)

@app.get("/settings/{key}", response_model=SettingRead)
async def read_setting(key: str, db: Session = Depends(get_db)):
    setting = SettingCRUD.read(db, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@app.put("/settings/{key}", response_model=SettingRead)  
async def create_or_update_setting(key: str, request: dict, db: Session = Depends(get_db)):
    value = request.get("value", "")
    setting = SettingCRUD.create_or_update(db, key, value)
    
    # If this is the Gemini API key, refresh the AI client
    if key == "gemini_api_key":
        from .utils.ai_client import ai_client
        ai_client.refresh_api_key()
        print(f"Refreshed AI client after API key update")
    
    return setting

# OCR endpoint
@app.post("/ocr/")
async def ocr_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        content = await file.read()
        text = extract_text(content)
        return {"text": text, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

# AI parsing endpoint
@app.post("/ai/parse", response_model=AIParseResponse)
async def ai_parse(request: AIParseRequest):
    try:
        tasks = ask(request.prompt)
        return AIParseResponse(tasks=tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI parsing failed: {str(e)}")

# AI assistant endpoint
@app.post("/ai/assistant", response_model=AIAssistantResponse)
async def ai_assistant(request: AIAssistantRequest):
    try:
        result = assistant_command(request.command, request.content, request.context)
        return AIAssistantResponse(result=result, success=True)
    except Exception as e:
        return AIAssistantResponse(
            result="",
            success=False,
            error=f"AI assistant failed: {str(e)}"
        )

# AI subtask generation endpoint
@app.post("/ai/subtasks", response_model=AISubtaskResponse)
async def ai_generate_subtasks(request: AISubtaskRequest):
    try:
        subtasks = generate_subtasks(
            request.parent_task_title, 
            request.parent_task_description, 
            request.max_subtasks
        )
        return AISubtaskResponse(subtasks=subtasks, success=True)
    except Exception as e:
        return AISubtaskResponse(
            subtasks=[],
            success=False,
            error=f"Subtask generation failed: {str(e)}"
        )

# Weekly report generation endpoint
@app.post("/ai/weekly-report", response_model=WeeklyReportResponse)
async def ai_generate_weekly_report(request: WeeklyReportRequest, db: Session = Depends(get_db)):
    try:
        from datetime import datetime, timedelta
        
        # Set default dates if not provided
        end_date = datetime.fromisoformat(request.end_date) if request.end_date else datetime.now()
        start_date = datetime.fromisoformat(request.start_date) if request.start_date else end_date - timedelta(days=7)
        
        # Get tasks within the date range
        tasks = TaskCRUD.read_all(db)
        
        # Filter tasks by date range and convert to dict format
        filtered_tasks = []
        for task in tasks:
            task_date = task.updated_at or task.created_at
            if start_date <= task_date <= end_date:
                filtered_tasks.append({
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "urgency": task.urgency,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "status": "completed" if task.urgency == 4 else ("in_progress" if task.urgency <= 1 else "pending")
                })
        
        report = generate_weekly_report(
            filtered_tasks,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
        
        return WeeklyReportResponse(report=report, success=True)
    except Exception as e:
        return WeeklyReportResponse(
            report="",
            success=False,
            error=f"Weekly report generation failed: {str(e)}"
        )

# Workload analysis endpoint
@app.post("/ai/workload-analysis", response_model=WorkloadAnalysisResponse)
async def analyze_workload(request: WorkloadAnalysisRequest, db: Session = Depends(get_db)):
    try:
        from datetime import datetime, date
        
        # Parse target date or use today
        target_date = datetime.fromisoformat(request.date).date() if request.date else date.today()
        
        # Get all tasks and filter by due date
        all_tasks = TaskCRUD.read_all(db)
        daily_tasks = []
        
        for task in all_tasks:
            # Include tasks due on target date or without due date (assume today)
            if task.due_date is None or task.due_date.date() == target_date:
                # Auto-estimate hours based on urgency if not set
                estimated_hours = task.estimated_hours
                if estimated_hours == 0.0:
                    # Default estimates: P0=8h, P1=6h, P2=4h, P3=2h, P4=1h
                    hour_map = {0: 8.0, 1: 6.0, 2: 4.0, 3: 2.0, 4: 1.0}
                    estimated_hours = hour_map.get(task.urgency, 4.0)
                
                daily_tasks.append({
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "urgency": task.urgency,
                    "estimated_hours": estimated_hours,
                    "due_date": task.due_date.isoformat() if task.due_date else None
                })
        
        # Calculate workload metrics
        total_hours = sum(task["estimated_hours"] for task in daily_tasks)
        capacity_hours = 6.0  # Default daily capacity
        workload_percentage = (total_hours / capacity_hours) * 100
        
        # Determine conflict level
        if workload_percentage <= 80:
            conflict_level = "green"
        elif workload_percentage <= 120:
            conflict_level = "yellow" 
        else:
            conflict_level = "red"
        
        return WorkloadAnalysisResponse(
            total_hours=total_hours,
            capacity_hours=capacity_hours,
            workload_percentage=workload_percentage,
            conflict_level=conflict_level,
            tasks=daily_tasks,
            success=True
        )
        
    except Exception as e:
        return WorkloadAnalysisResponse(
            total_hours=0.0,
            capacity_hours=6.0,
            workload_percentage=0.0,
            conflict_level="green",
            tasks=[],
            success=False,
            error=f"Workload analysis failed: {str(e)}"
        )

# Similar task detection endpoint
@app.post("/ai/similar-tasks", response_model=SimilarTaskResponse)
async def find_similar_tasks_api(request: SimilarTaskRequest, db: Session = Depends(get_db)):
    try:
        # Get all existing tasks
        all_tasks = TaskCRUD.read_all(db)
        
        # Convert to dict format for similarity comparison
        existing_tasks = []
        for task in all_tasks:
            existing_tasks.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "urgency": task.urgency,
                "module_id": task.module_id,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            })
        
        # Find similar tasks
        similar_results = find_similar_tasks(
            request.task_title,
            request.task_description,
            existing_tasks,
            request.similarity_threshold
        )
        
        # Generate suggestions based on similarity
        suggestions = []
        for result in similar_results:
            match_type = result.get("match_type", "similar")
            similarity_score = result.get("similarity_score", 0)
            task_data = result.get("task", {})
            
            if match_type == "exact_title" or match_type == "near_duplicate":
                suggestions.append(f"任务 '{task_data.get('title')}' 与新任务几乎完全相同，建议合并或检查是否重复")
            elif match_type == "very_similar":
                suggestions.append(f"建议与任务 '{task_data.get('title')}' (相似度: {similarity_score:.1%}) 建立关联或合并")
            elif match_type == "similar":
                suggestions.append(f"考虑将新任务与 '{task_data.get('title')}' 分组或建立依赖关系")
        
        return SimilarTaskResponse(
            similar_tasks=similar_results,
            suggestions=suggestions,
            success=True
        )
        
    except Exception as e:
        return SimilarTaskResponse(
            similar_tasks=[],
            suggestions=[],
            success=False,
            error=f"Similar task detection failed: {str(e)}"
        )

# Risk analysis endpoint
@app.post("/ai/risk-analysis", response_model=RiskAnalysisResponse)
async def analyze_risks(request: RiskAnalysisRequest, db: Session = Depends(get_db)):
    try:
        # Get tasks to analyze
        if request.tasks:
            tasks_to_analyze = request.tasks
        else:
            # Get all tasks if none specified
            all_tasks = TaskCRUD.read_all(db)
            tasks_to_analyze = []
            for task in all_tasks:
                tasks_to_analyze.append({
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "urgency": task.urgency,
                    "module_id": task.module_id,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat()
                })
        
        # Analyze risks
        risk_analysis = analyze_task_risks(tasks_to_analyze)
        
        return RiskAnalysisResponse(
            risk_summary=risk_analysis["risk_summary"],
            risky_tasks=risk_analysis["risky_tasks"],
            suggestions=risk_analysis["suggestions"],
            success=True
        )
        
    except Exception as e:
        return RiskAnalysisResponse(
            risk_summary={},
            risky_tasks=[],
            suggestions=[],
            success=False,
            error=f"Risk analysis failed: {str(e)}"
        )

# Theme island clustering endpoint
@app.post("/ai/theme-islands", response_model=ThemeIslandResponse)
async def create_theme_islands_api(request: ThemeIslandRequest, db: Session = Depends(get_db)):
    try:
        # Get tasks to analyze
        if request.tasks:
            tasks_to_analyze = request.tasks
        else:
            # Get all tasks if none specified
            all_tasks = TaskCRUD.read_all(db)
            tasks_to_analyze = []
            for task in all_tasks:
                tasks_to_analyze.append({
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "urgency": task.urgency,
                    "module_id": task.module_id,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat()
                })
        
        # Create theme islands
        island_result = create_theme_islands(tasks_to_analyze)
        
        # Save islands to database and update task island_ids
        try:
            # Clear existing islands
            IslandCRUD.clear_all(db)
            
            # Create new islands and update tasks
            for island_data in island_result["islands"]:
                # Create island in database
                new_island = Island(
                    name=island_data["name"],
                    color=island_data["color"],
                    size=island_data.get("size", len(island_data.get("tasks", [])))
                )
                new_island.set_keywords(island_data.get("keywords", []))
                saved_island = IslandCRUD.create(db, new_island)
                
                # Update tasks with island_id
                for task_data in island_data["tasks"]:
                    task = TaskCRUD.read(db, task_data["id"])
                    if task:
                        # Check if there's a manual override
                        if task.island_override is not None:
                            task.island_id = task.island_override
                        else:
                            task.island_id = saved_island.id
                        TaskCRUD.update(db, task, TaskUpdate(island_id=task.island_id))
                
                # Update island data with saved id
                island_data["id"] = saved_island.id
        
        except Exception as db_error:
            print(f"Failed to save islands to database: {db_error}")
            # Continue without saving to database
        
        return ThemeIslandResponse(
            islands=island_result["islands"],
            island_stats=island_result["island_stats"],
            suggestions=island_result["suggestions"],
            success=True
        )
        
    except Exception as e:
        return ThemeIslandResponse(
            islands=[],
            island_stats={},
            suggestions=[],
            success=False,
            error=f"Theme island creation failed: {str(e)}"
        )

# Update task island assignment
@app.put("/tasks/{task_id}/island")
async def update_task_island(task_id: int, island_id: int, db: Session = Depends(get_db)):
    try:
        task = TaskCRUD.read(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Set island override
        task.island_override = island_id
        TaskCRUD.update(db, task, TaskUpdate(island_override=island_id))
        
        return {"success": True, "message": "Task island updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task island: {str(e)}")

# Get islands
@app.get("/islands/", response_model=List[IslandRead])
def get_islands(db: Session = Depends(get_db)):
    return IslandCRUD.read_all(db)

# Task Dependencies endpoints
@app.get("/dependencies/", response_model=List[TaskDependencyRead])
def get_dependencies(db: Session = Depends(get_db)):
    return TaskDependencyCRUD.read_all(db)

@app.post("/dependencies/", response_model=TaskDependencyRead)
def create_dependency(dependency: TaskDependencyCreate, db: Session = Depends(get_db)):
    # Check if both tasks exist
    from_task = TaskCRUD.read(db, dependency.from_task_id)
    to_task = TaskCRUD.read(db, dependency.to_task_id)
    if not from_task or not to_task:
        raise HTTPException(status_code=404, detail="One or both tasks not found")
    
    # Prevent self-dependency
    if dependency.from_task_id == dependency.to_task_id:
        raise HTTPException(status_code=400, detail="Task cannot depend on itself")
    
    db_dependency = TaskDependency(**dependency.dict())
    return TaskDependencyCRUD.create(db, db_dependency)

@app.get("/dependencies/task/{task_id}", response_model=List[TaskDependencyRead])
def get_task_dependencies(task_id: int, db: Session = Depends(get_db)):
    task = TaskCRUD.read(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskDependencyCRUD.read_by_task(db, task_id)

@app.delete("/dependencies/{from_task_id}/{to_task_id}")
def delete_dependency(from_task_id: int, to_task_id: int, db: Session = Depends(get_db)):
    success = TaskDependencyCRUD.delete(db, from_task_id, to_task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dependency not found")
    return {"message": "Dependency deleted successfully"}

# Export endpoints
@app.get("/export/json")
def export_json(db: Session = Depends(get_db)):
    """Export all data to JSON format"""
    export_service = ExportService(db)
    data = export_service.export_to_json()
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f"attachment; filename=\"{export_service.create_backup_filename('json')}\""
        }
    )

@app.get("/export/markdown")
def export_markdown(db: Session = Depends(get_db)):
    """Export all data to Markdown format"""
    export_service = ExportService(db)
    markdown_content = export_service.export_to_markdown()
    return JSONResponse(
        content={"content": markdown_content, "filename": export_service.create_backup_filename('md')},
        headers={
            "Content-Type": "application/json"
        }
    )

# Backup endpoints
@app.post("/backup/create")
def create_manual_backup():
    """Create a manual backup"""
    try:
        json_file, md_file = backup_service.create_backup()
        return {
            "message": "Backup created successfully",
            "files": {
                "json": json_file,
                "markdown": md_file
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@app.get("/backup/info")
def get_backup_info():
    """Get backup information"""
    return backup_service.get_backup_info()

@app.get("/backup/history")
def get_backup_history():
    """Get backup history"""
    try:
        history = backup_service.get_backup_history()
        return {"backups": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load backup history: {str(e)}")

@app.get("/backup/list")
def get_backup_list():
    """Get backup list (alias for history)"""
    try:
        history = backup_service.get_backup_history()
        return {"success": True, "backups": history}
    except Exception as e:
        return {"success": False, "error": f"Failed to load backup history: {str(e)}"}

@app.post("/backup/configure")
def configure_backup(interval_hours: int, db: Session = Depends(get_db)):
    """Configure backup interval"""
    if interval_hours < 1 or interval_hours > 24:
        raise HTTPException(status_code=400, detail="Backup interval must be between 1 and 24 hours")
    
    # Save to settings
    SettingCRUD.create_or_update(db, "backup_interval_hours", str(interval_hours))
    
    # Restart scheduler with new interval
    backup_service.start_scheduler(interval_hours)
    
    return {"message": f"Backup interval set to {interval_hours} hours"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)