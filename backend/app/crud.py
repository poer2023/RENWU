from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from .models import Task, Module, History, Setting, TaskDependency
from .schemas import TaskUpdate, ModuleCreate, SettingCreate, TaskDependencyCreate

class TaskCRUD:
    @staticmethod
    def create(db: Session, obj: Task) -> Task:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def read(db: Session, task_id: int) -> Optional[Task]:
        return db.get(Task, task_id)

    @staticmethod
    def read_all(db: Session, skip: int = 0, limit: int = 100) -> List[Task]:
        statement = select(Task).offset(skip).limit(limit)
        return db.exec(statement).all()

    @staticmethod
    def update(db: Session, db_obj: Task, obj_in: TaskUpdate) -> Task:
        obj_data = obj_in.dict(exclude_unset=True)
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                # Log history for changes
                old_val = str(getattr(db_obj, field))
                if str(value) != old_val:
                    history = History(
                        task_id=db_obj.id,
                        field=field,
                        old_val=old_val,
                        new_val=str(value)
                    )
                    db.add(history)
                setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, db_obj: Task) -> Task:
        db.delete(db_obj)
        db.commit()
        return db_obj

class ModuleCRUD:
    @staticmethod
    def create(db: Session, obj: Module) -> Module:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def read(db: Session, module_id: int) -> Optional[Module]:
        return db.get(Module, module_id)

    @staticmethod
    def read_all(db: Session) -> List[Module]:
        statement = select(Module)
        return db.exec(statement).all()

    @staticmethod
    def delete(db: Session, db_obj: Module) -> Module:
        db.delete(db_obj)
        db.commit()
        return db_obj

class HistoryCRUD:
    @staticmethod
    def read_by_task(db: Session, task_id: int) -> List[History]:
        statement = select(History).where(History.task_id == task_id).order_by(History.ts.desc())
        return db.exec(statement).all()

class SettingCRUD:
    @staticmethod
    def create_or_update(db: Session, key: str, value: str) -> Setting:
        setting = db.get(Setting, key)
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.add(setting)
        db.commit()
        db.refresh(setting)
        return setting

    @staticmethod
    def read(db: Session, key: str) -> Optional[Setting]:
        return db.get(Setting, key)

    @staticmethod
    def read_all(db: Session) -> List[Setting]:
        statement = select(Setting)
        return db.exec(statement).all()

class TaskDependencyCRUD:
    @staticmethod
    def create(db: Session, obj: TaskDependency) -> TaskDependency:
        # Check if dependency already exists
        existing = db.exec(
            select(TaskDependency).where(
                TaskDependency.from_task_id == obj.from_task_id,
                TaskDependency.to_task_id == obj.to_task_id
            )
        ).first()
        if existing:
            return existing
        
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def read_all(db: Session) -> List[TaskDependency]:
        statement = select(TaskDependency)
        return db.exec(statement).all()

    @staticmethod
    def read_by_task(db: Session, task_id: int) -> List[TaskDependency]:
        statement = select(TaskDependency).where(
            (TaskDependency.from_task_id == task_id) | 
            (TaskDependency.to_task_id == task_id)
        )
        return db.exec(statement).all()

    @staticmethod
    def delete(db: Session, from_task_id: int, to_task_id: int) -> bool:
        dependency = db.exec(
            select(TaskDependency).where(
                TaskDependency.from_task_id == from_task_id,
                TaskDependency.to_task_id == to_task_id
            )
        ).first()
        if dependency:
            db.delete(dependency)
            db.commit()
            return True
        return False