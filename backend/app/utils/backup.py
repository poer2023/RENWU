import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlmodel import Session
from .export import ExportService
from ..deps import engine

class BackupService:
    def __init__(self, backup_dir: str = "./data/backup"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.scheduler: Optional[BackgroundScheduler] = None
        self.max_backups = 30  # Keep last 30 backups
    
    def create_backup(self) -> tuple[str, str]:
        """
        Create a backup of all data
        Returns: (json_filename, markdown_filename)
        """
        with Session(engine) as db:
            export_service = ExportService(db)
            
            # Create JSON backup
            json_data = export_service.export_to_json()
            json_filename = export_service.create_backup_filename('json')
            json_path = self.backup_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            # Create Markdown backup
            markdown_content = export_service.export_to_markdown()
            markdown_filename = export_service.create_backup_filename('md')
            markdown_path = self.backup_dir / markdown_filename
            
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            return json_filename, markdown_filename
    
    def _cleanup_old_backups(self):
        """Remove old backup files, keeping only the most recent ones"""
        # Get all backup files
        json_files = sorted(self.backup_dir.glob("taskwall_backup_*.json"))
        md_files = sorted(self.backup_dir.glob("taskwall_backup_*.md"))
        
        # Remove old files if we have too many
        if len(json_files) > self.max_backups:
            for file in json_files[:-self.max_backups]:
                file.unlink()
        
        if len(md_files) > self.max_backups:
            for file in md_files[:-self.max_backups]:
                file.unlink()
    
    def start_scheduler(self, interval_hours: int = 4):
        """Start the automatic backup scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
        
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(
            func=self._scheduled_backup,
            trigger=IntervalTrigger(hours=interval_hours),
            id='backup_job',
            name='Automatic TaskWall Backup',
            replace_existing=True
        )
        self.scheduler.start()
        print(f"Backup scheduler started with {interval_hours}-hour interval")
    
    def stop_scheduler(self):
        """Stop the automatic backup scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            print("Backup scheduler stopped")
    
    def _scheduled_backup(self):
        """Internal method for scheduled backups"""
        try:
            json_file, md_file = self.create_backup()
            print(f"Automatic backup created: {json_file}, {md_file}")
        except Exception as e:
            print(f"Backup failed: {e}")
    
    def get_backup_info(self) -> dict:
        """Get information about existing backups"""
        json_files = list(self.backup_dir.glob("taskwall_backup_*.json"))
        md_files = list(self.backup_dir.glob("taskwall_backup_*.md"))
        
        return {
            "backup_count": len(json_files),
            "latest_backup": max([f.stat().st_mtime for f in json_files]) if json_files else None,
            "backup_dir": str(self.backup_dir),
            "scheduler_running": self.scheduler.running if self.scheduler else False
        }

# Global backup service instance
backup_service = BackupService()