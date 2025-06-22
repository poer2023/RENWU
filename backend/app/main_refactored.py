import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, Session
from datetime import datetime, timedelta, date
from typing import List

from .deps import engine, get_db
from .models import Task, Module, History, Setting, TaskDependency, Island
from .crud import TaskCRUD, ModuleCRUD, HistoryCRUD, SettingCRUD, TaskDependencyCRUD, IslandCRUD
from .schemas import (
    AIParseRequest, AIParseResponse,
    AIAssistantRequest, AIAssistantResponse,
    AISubtaskRequest, AISubtaskResponse,
    WeeklyReportRequest, WeeklyReportResponse,
    WorkloadAnalysisRequest, WorkloadAnalysisResponse,
    SimilarTaskRequest, SimilarTaskResponse,
    RiskAnalysisRequest, RiskAnalysisResponse,
    ThemeIslandRequest, ThemeIslandResponse,
    TaskUpdate, IslandRead
)
from .routers import ai_v3, tasks, modules, dependencies, settings, history, export_backup, ocr
from .utils.ai_client import ask, assistant_command, generate_subtasks, generate_weekly_report, find_similar_tasks, analyze_task_risks, create_theme_islands
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

# Legacy AI endpoints (for backward compatibility)
@app.post("/ai/parse", response_model=AIParseResponse)
async def ai_parse(request: AIParseRequest):
    """AI解析任务（遗留接口）"""
    try:
        tasks = ask(request.prompt)
        return AIParseResponse(tasks=tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI parsing failed: {str(e)}")

@app.post("/ai/assistant", response_model=AIAssistantResponse)
async def ai_assistant(request: AIAssistantRequest):
    """AI助手（遗留接口）"""
    try:
        result = assistant_command(request.command, request.content, request.context)
        return AIAssistantResponse(result=result, success=True)
    except Exception as e:
        return AIAssistantResponse(
            result="",
            success=False,
            error=f"AI assistant failed: {str(e)}"
        )

@app.post("/ai/subtasks", response_model=AISubtaskResponse)
async def ai_generate_subtasks(request: AISubtaskRequest):
    """AI生成子任务（遗留接口）"""
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

@app.post("/ai/weekly-report", response_model=WeeklyReportResponse)
async def ai_generate_weekly_report(request: WeeklyReportRequest, db: Session = Depends(get_db)):
    """AI生成周报（遗留接口）"""
    try:
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

@app.post("/ai/workload-analysis", response_model=WorkloadAnalysisResponse)
async def analyze_workload(request: WorkloadAnalysisRequest, db: Session = Depends(get_db)):
    """工作量分析（遗留接口）"""
    try:
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

@app.post("/ai/similar-tasks", response_model=SimilarTaskResponse)
async def find_similar_tasks_api(request: SimilarTaskRequest, db: Session = Depends(get_db)):
    """相似任务检测（遗留接口）"""
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

@app.post("/ai/risk-analysis", response_model=RiskAnalysisResponse)
async def analyze_risks(request: RiskAnalysisRequest, db: Session = Depends(get_db)):
    """风险分析（遗留接口）"""
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

@app.post("/ai/theme-islands", response_model=ThemeIslandResponse)
async def create_theme_islands_api(request: ThemeIslandRequest, db: Session = Depends(get_db)):
    """主题岛聚类（遗留接口）"""
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

# Islands endpoint
@app.get("/islands/", response_model=List[IslandRead])
def get_islands(db: Session = Depends(get_db)):
    """获取所有主题岛"""
    return IslandCRUD.read_all(db) 