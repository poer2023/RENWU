#!/usr/bin/env python3
"""
初始化基础数据
"""
from sqlmodel import Session, create_engine
from app.models import Module, Task
from app.deps import DATABASE_URL
from datetime import datetime

def init_data():
    # 使用与应用相同的数据库配置
    engine = create_engine(DATABASE_URL)
    
    print("初始化基础数据...")
    
    with Session(engine) as session:
        # 创建默认模块
        default_module = Module(name="General", color="#FFE58F")
        session.add(default_module)
        session.commit()
        session.refresh(default_module)
        
        # 创建一些测试任务
        test_tasks = [
            Task(
                title="测试任务1",
                description="这是一个测试任务",
                urgency=2,
                module_id=default_module.id,
                island_id=-1
            ),
            Task(
                title="测试任务2", 
                description="另一个测试任务",
                urgency=1,
                module_id=default_module.id,
                island_id=-1
            )
        ]
        
        for task in test_tasks:
            session.add(task)
        
        session.commit()
        
        print(f"✅ 初始化完成！创建了 {len(test_tasks)} 个测试任务")

if __name__ == "__main__":
    init_data() 