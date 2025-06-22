#!/usr/bin/env python3
"""
简化的AI v3.0服务测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session
from app.deps import engine
from app.ai import AIServiceAggregator

def test_ai_aggregator():
    """测试AI服务聚合器"""
    try:
        print("正在初始化数据库会话...")
        with Session(engine) as db:
            print("正在初始化AI服务聚合器...")
            aggregator = AIServiceAggregator(db)
            print("AI服务聚合器初始化成功！")
            
            print("正在测试自然语言处理...")
            result = aggregator.process_natural_language_task(
                "明天下午3点开会讨论项目进度",
                context={},
                full_analysis=True
            )
            print(f"处理结果: {result}")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_aggregator()