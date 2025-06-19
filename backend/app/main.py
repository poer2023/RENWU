import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, Session
from typing import List, Optional

from .deps import engine, get_db
from .models import Task, Module, History, Setting, TaskDependency, AILog
from .crud import TaskCRUD, ModuleCRUD, HistoryCRUD, SettingCRUD, TaskDependencyCRUD, AILogCRUD
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
    AISubtaskGenerationRequest, AISubtaskGenerationResponse,
    SubtaskConfirmationRequest, SubtaskSuggestion, AILogRead
)
from .utils.ocr import extract_text
from .utils.ai_client import ask, assistant_command, generate_subtasks, generate_weekly_report, find_similar_tasks, analyze_task_risks, create_theme_islands
from .utils.export import ExportService
from .utils.backup import backup_service

# Load environment variables from .env file
load_dotenv()

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
    task = Task(**task_in.dict())
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
    return TaskCRUD.update(db, task, task_in)

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
async def create_or_update_setting(key: str, value: str, db: Session = Depends(get_db)):
    return SettingCRUD.create_or_update(db, key, value)

@app.post("/ai/test")
async def test_gemini_api(db: Session = Depends(get_db)):
    """测试Gemini API连接状态"""
    from .utils.ai_client import AIClient
    ai_client = AIClient(db_session=db)
    
    result = {
        "api_key_configured": bool(ai_client.api_key),
        "api_key_source": "database" if ai_client.api_key and not os.getenv("GEMINI_API_KEY") else "environment",
        "model_available": bool(ai_client.model),
        "api_key_preview": ai_client.api_key[:10] + "..." if ai_client.api_key else None
    }
    
    if ai_client.model:
        try:
            # 简单的测试请求
            response = ai_client.model.generate_content("Hello, respond with 'API Working!'")
            result["test_response"] = response.text if response else "No response"
            result["api_working"] = True
        except Exception as e:
            result["test_response"] = f"Error: {str(e)}"
            result["api_working"] = False
    else:
        result["api_working"] = False
        result["test_response"] = "No model configured"
    
    return result

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
async def ai_generate_subtasks(request: AISubtaskRequest, db: Session = Depends(get_db)):
    try:
        # The function now returns a tuple (subtasks, metadata)
        subtasks, metadata = generate_subtasks(
            request.parent_task_title, 
            request.parent_task_description, 
            request.max_subtasks
        )

        # Log the AI interaction
        log_entry = AILog(
            task_id=None,  # This is a generic call, not tied to a specific task yet
            model=metadata.get("model", "unknown"),
            operation="generate_subtasks",
            tokens_in=metadata.get("prompt_tokens", 0),
            tokens_out=metadata.get("completion_tokens", 0),
            cost=metadata.get("cost", 0.0),
            accepted=None,  # Not known at this stage
            error_message=metadata.get("error_message")
        )
        AILogCRUD.create(db, log_entry)
        db.commit()


        if metadata.get("success", False) and subtasks is not None:
            return AISubtaskResponse(subtasks=subtasks, success=True)
        else:
            return AISubtaskResponse(
                subtasks=[],
                success=False,
                error=metadata.get("error_message", "Subtask generation failed for an unknown reason.")
            )
            
    except Exception as e:
        return AISubtaskResponse(
            subtasks=[],
            success=False,
            error=f"An unexpected error occurred in the endpoint: {str(e)}"
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
@app.post("/workload/analyze", response_model=WorkloadAnalysisResponse)
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

# 按PRD规范的AI子任务生成端点
@app.post("/ai/subtasks/generate", response_model=AISubtaskGenerationResponse)
async def generate_subtasks_endpoint(request: AISubtaskGenerationRequest, db: Session = Depends(get_db)):
    """
    按PRD规范生成子任务建议
    """
    try:
        # 验证父任务存在
        parent_task = TaskCRUD.read(db, request.parent_task_id)
        if not parent_task:
            raise HTTPException(status_code=404, detail="Parent task not found")
        
        # 检查是否已存在子任务
        from sqlmodel import select
        existing_subtasks = db.exec(
            select(Task).where(Task.parent_id == request.parent_task_id)
        ).all()
        
        if existing_subtasks and not request.auto_accept:
            raise HTTPException(
                status_code=409, 
                detail=f"Task already has {len(existing_subtasks)} subtasks. Set auto_accept=true to override."
            )
        
        # 调用AI服务生成子任务
        from .utils.ai_client import AIClient
        ai_client = AIClient(db_session=db)
        subtasks, metadata = ai_client.generate_subtasks_advanced(
            request.parent_task_title,
            request.parent_task_description,
            request.max_subtasks
        )
        
        # 创建AI日志记录
        ai_log = AILog(
            task_id=request.parent_task_id,
            model=metadata["model_used"],
            operation="subtask_generation",
            tokens_in=metadata["tokens_in"],
            tokens_out=metadata["tokens_out"],
            cost=metadata["cost"],
            error_message=metadata["error_message"]
        )
        ai_log = AILogCRUD.create(db, ai_log)
        
        # 转换为响应格式
        suggestions = []
        for subtask in subtasks:
            suggestions.append(SubtaskSuggestion(
                title=subtask["title"],
                description=subtask["description"],
                order=subtask.get("order", 1),
                urgency=subtask.get("urgency", 2)
            ))
        
        return AISubtaskGenerationResponse(
            suggestions=suggestions,
            model_used=metadata["model_used"],
            tokens_in=metadata["tokens_in"],
            tokens_out=metadata["tokens_out"],
            cost=metadata["cost"],
            log_id=ai_log.id,
            success=True,
            error=metadata["error_message"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # 记录失败日志
        ai_log = AILog(
            task_id=request.parent_task_id,
            model="error",
            operation="subtask_generation",
            error_message=str(e)
        )
        ai_log = AILogCRUD.create(db, ai_log)
        
        raise HTTPException(status_code=500, detail=f"Subtask generation failed: {str(e)}")

@app.post("/ai/subtasks/confirm")
async def confirm_subtasks_endpoint(request: SubtaskConfirmationRequest, db: Session = Depends(get_db)):
    """
    用户确认子任务建议，创建实际的子任务
    """
    try:
        # 更新AI日志的接受状态
        ai_log = AILogCRUD.update_acceptance(db, request.log_id, request.accepted)
        if not ai_log:
            raise HTTPException(status_code=404, detail="AI log not found")
        
        if not request.accepted:
            return {"message": "Subtasks rejected", "created_count": 0}
        
        # 获取父任务
        parent_task = TaskCRUD.read(db, ai_log.task_id)
        if not parent_task:
            raise HTTPException(status_code=404, detail="Parent task not found")
        
        created_tasks = []
        
        # 创建确认的子任务
        for suggestion in request.accepted_suggestions:
            subtask = Task(
                title=suggestion.title,
                description=suggestion.description,
                urgency=suggestion.urgency,
                parent_id=parent_task.id,
                module_id=parent_task.module_id  # 继承父任务的模块
            )
            created_task = TaskCRUD.create(db, subtask)
            created_tasks.append(created_task)
            
            # 创建依赖关系（子任务依赖父任务）
            if created_task.id and parent_task.id:
                dependency = TaskDependency(
                    from_task_id=parent_task.id,
                    to_task_id=created_task.id
                )
                TaskDependencyCRUD.create(db, dependency)
        
        return {
            "message": f"Successfully created {len(created_tasks)} subtasks",
            "created_count": len(created_tasks),
            "subtask_ids": [task.id for task in created_tasks]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subtask confirmation failed: {str(e)}")

# AI使用指标端点
@app.get("/ai/metrics")
async def get_ai_metrics(days: int = 7, db: Session = Depends(get_db)):
    """
    获取AI功能使用指标
    """
    try:
        metrics = AILogCRUD.get_metrics(db, days)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

# AI日志查询端点
@app.get("/ai/logs", response_model=List[AILogRead])
async def get_ai_logs(
    skip: int = 0, 
    limit: int = 50, 
    task_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    查询AI使用日志
    """
    try:
        if task_id:
            return AILogCRUD.read_by_task(db, task_id)
        else:
            return AILogCRUD.read_all(db, skip, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")