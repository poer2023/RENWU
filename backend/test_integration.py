#!/usr/bin/env python3
"""
TaskWall v3.0 集成测试
测试完整的AI智能任务创建流程
"""

import json
import requests
import time

# API base URL
BASE_URL = "http://localhost:8000"
API_PREFIX = f"{BASE_URL}/api/ai/v3"

def test_complete_workflow():
    """测试完整的AI任务创建工作流"""
    print("🚀 开始TaskWall v3.0 集成测试")
    print("=" * 50)
    
    # Test 1: AI任务解析
    print("\n📝 测试1: AI任务解析")
    parse_data = {
        "text": "下周五前完成用户登录功能开发和测试，高优先级",
        "context": {"user_id": "test_user"},
        "full_analysis": True
    }
    
    try:
        response = requests.post(f"{API_PREFIX}/parse-task", json=parse_data)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 解析成功")
            print(f"建议标题: {result['suggested_task']['title']}")
            print(f"优先级: {result['suggested_task']['priority']}")
            print(f"置信度: {result['confidence']:.2f}")
        else:
            print(f"❌ 解析失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # Test 2: 批量任务处理
    print("\n📦 测试2: 批量任务处理")
    batch_data = {
        "task_inputs": [
            "设计用户界面原型",
            "实现前端组件",
            "编写单元测试",
            "部署到测试环境"
        ],
        "context": {"project": "web_app"}
    }
    
    try:
        response = requests.post(f"{API_PREFIX}/batch-process", json=batch_data)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 批量处理成功")
            print(f"处理任务数: {len(result['results'])}")
            for i, task_result in enumerate(result['results'], 1):
                print(f"  {i}. {task_result['suggested_task']['title']}")
        else:
            print(f"❌ 批量处理失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # Test 3: AI洞察
    print("\n🔍 测试3: AI洞察")
    try:
        response = requests.get(f"{API_PREFIX}/insights", params={
            "user_id": "test_user",
            "time_frame": "this_week"
        })
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 洞察获取成功")
            if 'insights' in result and 'workload' in result['insights']:
                workload = result['insights']['workload']
                print(f"任务数量: {workload.get('task_count', 'N/A')}")
                print(f"利用率: {workload.get('utilization_rate', 'N/A')}")
        else:
            print(f"❌ 洞察获取失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # Test 4: 任务分析
    print("\n🔬 测试4: 任务分析")
    analyze_data = {
        "task_data": {
            "title": "开发用户认证系统",
            "description": "包括登录、注册、密码重置功能",
            "priority": 1
        },
        "context": {"department": "engineering"}
    }
    
    try:
        response = requests.post(f"{API_PREFIX}/analyze-task", json=analyze_data)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 任务分析成功")
            print(f"总体置信度: {result.get('overall_confidence', 'N/A')}")
            if 'classification_result' in result:
                cls_result = result['classification_result']
                print(f"分类建议: {cls_result['data']['category']}")
        else:
            print(f"❌ 任务分析失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 TaskWall v3.0 集成测试完成！")

if __name__ == "__main__":
    test_complete_workflow()