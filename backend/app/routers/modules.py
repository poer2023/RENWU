from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from ..deps import get_db
from ..models import Module
from ..crud import ModuleCRUD
from ..schemas import ModuleCreate, ModuleRead

router = APIRouter(prefix="/api/modules", tags=["modules"])

@router.post("/", response_model=ModuleRead)
async def create_module(module_in: ModuleCreate, db: Session = Depends(get_db)):
    """创建新模块"""
    module = Module(**module_in.dict())
    return ModuleCRUD.create(db, module)

@router.get("/", response_model=List[ModuleRead])
async def read_modules(db: Session = Depends(get_db)):
    """获取所有模块"""
    return ModuleCRUD.read_all(db)

@router.get("/{module_id}", response_model=ModuleRead)
async def read_module(module_id: int, db: Session = Depends(get_db)):
    """获取单个模块"""
    module = ModuleCRUD.read(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module

@router.delete("/{module_id}")
async def delete_module(module_id: int, db: Session = Depends(get_db)):
    """删除模块"""
    module = ModuleCRUD.read(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    ModuleCRUD.delete(db, module)
    return {"message": "Module deleted successfully"} 