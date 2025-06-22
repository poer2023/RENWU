#!/usr/bin/env python3
"""
重新创建表结构脚本
"""
import os
from sqlmodel import SQLModel, create_engine
from app.models import Task, Module, History, Setting, TaskDependency, Island, AILog
from app.deps import DB_PATH, DATABASE_URL

def recreate_tables():
    print(f"重新创建表结构: {DB_PATH}")
    
    # 创建引擎
    engine = create_engine(DATABASE_URL, echo=True)
    
    try:
        # 删除所有表并重新创建
        print("删除所有表...")
        SQLModel.metadata.drop_all(engine)
        
        print("重新创建所有表...")
        SQLModel.metadata.create_all(engine)
        
        print("✅ 表结构重新创建完成!")
        
    except Exception as e:
        print(f"❌ 重新创建表失败: {e}")

if __name__ == "__main__":
    recreate_tables() 