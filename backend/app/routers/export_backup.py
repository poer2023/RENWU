from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session
import tempfile
import os

from ..deps import get_db
from ..crud import SettingCRUD
from ..utils.export import ExportService
from ..utils.backup import backup_service

router = APIRouter(prefix="/api", tags=["export", "backup"])

# Export endpoints
@router.get("/export/json")
def export_json(db: Session = Depends(get_db)):
    """导出数据为JSON格式"""
    try:
        export_service = ExportService(db)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_service.export_to_json(f.name)
            
            # Read the file content
            with open(f.name, 'r') as read_file:
                content = read_file.read()
            
            # Clean up
            os.unlink(f.name)
            
            return JSONResponse(content={"data": content, "filename": "taskwall_export.json"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/export/markdown")
def export_markdown(db: Session = Depends(get_db)):
    """导出数据为Markdown格式"""
    try:
        export_service = ExportService(db)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            export_service.export_to_markdown(f.name)
            
            # Read the file content
            with open(f.name, 'r') as read_file:
                content = read_file.read()
            
            # Clean up
            os.unlink(f.name)
            
            return JSONResponse(content={"data": content, "filename": "taskwall_export.md"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# Backup endpoints
@router.post("/backup/create")
def create_manual_backup():
    """手动创建备份"""
    try:
        backup_path = backup_service.create_backup()
        return {
            "message": "Backup created successfully",
            "backup_path": backup_path,
            "timestamp": backup_service.get_current_timestamp()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@router.get("/backup/info")
def get_backup_info():
    """获取备份信息"""
    return backup_service.get_backup_info()

@router.get("/backup/history")
def get_backup_history():
    """获取备份历史"""
    try:
        return backup_service.get_backup_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get backup history: {str(e)}")

@router.get("/backup/list")
def get_backup_list():
    """获取备份文件列表"""
    try:
        return backup_service.list_backups()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")

@router.post("/backup/configure")
def configure_backup(interval_hours: int, db: Session = Depends(get_db)):
    """配置备份间隔"""
    try:
        # Update setting in database
        SettingCRUD.create_or_update(db, "backup_interval_hours", str(interval_hours))
        
        # Restart scheduler with new interval
        backup_service.stop_scheduler()
        backup_service.start_scheduler(interval_hours)
        
        return {
            "message": "Backup configuration updated successfully",
            "interval_hours": interval_hours
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure backup: {str(e)}") 