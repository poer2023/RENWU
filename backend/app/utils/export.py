import json
from datetime import datetime
from typing import Dict, List, Optional
from sqlmodel import Session, select
from ..models import Task, Module, TaskDependency

class ExportService:
    def __init__(self, db: Session):
        self.db = db
    
    def export_to_json(self) -> Dict:
        """
        Export all data to JSON format
        """
        # Get all data
        tasks = self.db.exec(select(Task)).all()
        modules = self.db.exec(select(Module)).all()
        dependencies = self.db.exec(select(TaskDependency)).all()
        
        # Convert to dict format
        export_data = {
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "version": "1.0",
                "app": "TaskWall"
            },
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "urgency": task.urgency,
                    "module_id": task.module_id,
                    "parent_id": task.parent_id,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "ocr_src": task.ocr_src
                } for task in tasks
            ],
            "modules": [
                {
                    "id": module.id,
                    "name": module.name,
                    "color": module.color
                } for module in modules
            ],
            "dependencies": [
                {
                    "id": dep.id,
                    "from_task_id": dep.from_task_id,
                    "to_task_id": dep.to_task_id,
                    "created_at": dep.created_at.isoformat()
                } for dep in dependencies
            ]
        }
        
        return export_data
    
    def export_to_markdown(self) -> str:
        """
        Export all data to Markdown format
        """
        tasks = self.db.exec(select(Task)).all()
        modules = self.db.exec(select(Module)).all()
        dependencies = self.db.exec(select(TaskDependency)).all()
        
        # Create module lookup
        module_lookup = {module.id: module.name for module in modules}
        
        # Group tasks by module
        tasks_by_module = {}
        for task in tasks:
            module_name = module_lookup.get(task.module_id, "General")
            if module_name not in tasks_by_module:
                tasks_by_module[module_name] = []
            tasks_by_module[module_name].append(task)
        
        # Create dependency lookup
        dependencies_map = {}
        for dep in dependencies:
            if dep.from_task_id not in dependencies_map:
                dependencies_map[dep.from_task_id] = []
            dependencies_map[dep.from_task_id].append(dep.to_task_id)
        
        # Build markdown
        lines = [
            "# TaskWall Export",
            "",
            f"**Exported:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Tasks:** {len(tasks)}",
            f"**Total Modules:** {len(modules)}",
            ""
        ]
        
        # Priority mapping
        priority_names = {
            0: "P0 (Critical)",
            1: "P1 (High)", 
            2: "P2 (Medium)",
            3: "P3 (Low)",
            4: "P4 (Backlog)"
        }
        
        for module_name, module_tasks in tasks_by_module.items():
            lines.extend([
                f"## {module_name}",
                ""
            ])
            
            for task in module_tasks:
                priority = priority_names.get(task.urgency, f"P{task.urgency}")
                lines.append(f"### {task.title}")
                lines.append(f"- **Priority:** {priority}")
                lines.append(f"- **Created:** {task.created_at.strftime('%Y-%m-%d %H:%M')}")
                
                if task.description:
                    lines.extend([
                        "- **Description:**",
                        f"  {task.description}"
                    ])
                
                # Add dependencies
                if task.id in dependencies_map:
                    dep_titles = []
                    for dep_id in dependencies_map[task.id]:
                        dep_task = next((t for t in tasks if t.id == dep_id), None)
                        if dep_task:
                            dep_titles.append(dep_task.title)
                    if dep_titles:
                        lines.extend([
                            "- **Dependencies:**",
                            f"  {', '.join(dep_titles)}"
                        ])
                
                if task.ocr_src:
                    lines.append(f"- **Source:** {task.ocr_src}")
                
                lines.append("")
        
        return "\n".join(lines)
    
    def create_backup_filename(self, format: str = "json") -> str:
        """
        Create a backup filename with timestamp
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"taskwall_backup_{timestamp}.{format}"