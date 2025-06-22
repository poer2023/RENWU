from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from ..deps import get_db
from ..crud import SettingCRUD
from ..schemas import SettingCreate, SettingRead

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/", response_model=List[SettingRead])
async def read_settings(db: Session = Depends(get_db)):
    """获取所有设置"""
    return SettingCRUD.read_all(db)

@router.get("/{key}", response_model=SettingRead)
async def read_setting(key: str, db: Session = Depends(get_db)):
    """获取特定设置"""
    setting = SettingCRUD.read(db, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@router.put("/{key}", response_model=SettingRead)  
async def create_or_update_setting(key: str, request: dict, db: Session = Depends(get_db)):
    """创建或更新设置"""
    value = request.get("value", "")
    setting = SettingCRUD.create_or_update(db, key, value)
    
    # If this is the Gemini API key, refresh the AI client
    if key == "gemini_api_key":
        from ..utils.ai_client import ai_client
        ai_client.refresh_api_key()
        print(f"Refreshed AI client after API key update")
    
    return setting 