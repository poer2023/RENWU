#!/usr/bin/env python3
"""
测试子任务生成功能
"""
import requests
import json

BASE_URL = "http://localhost:8765"

def test_settings_api():
    """测试设置API"""
    print("=== 测试设置API ===")
    
    # 测试保存API key
    test_api_key = "test-api-key-12345"
    response = requests.put(f"{BASE_URL}/settings/gemini_api_key", 
                           json={"value": test_api_key})
    print(f"保存API key响应: {response.status_code}")
    if response.status_code == 200:
        print(f"保存成功: {response.json()}")
    else:
        print(f"保存失败: {response.text}")
    
    # 测试读取API key
    response = requests.get(f"{BASE_URL}/settings/gemini_api_key")
    print(f"读取API key响应: {response.status_code}")
    if response.status_code == 200:
        print(f"读取成功: {response.json()}")
    else:
        print(f"读取失败: {response.text}")
    
    print()

def test_subtask_generation():
    """测试子任务生成"""
    print("=== 测试子任务生成 ===")
    
    # 测试数据
    test_data = {
        "parent_task_title": "开发新功能",
        "parent_task_description": "为TaskWall应用开发一个新的任务管理功能，包括前端界面和后端API",
        "max_subtasks": 5
    }
    
    response = requests.post(f"{BASE_URL}/ai/subtasks", json=test_data)
    print(f"子任务生成响应: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"生成成功: {result['success']}")
        print(f"子任务数量: {len(result['subtasks'])}")
        print("生成的子任务:")
        for i, subtask in enumerate(result['subtasks'], 1):
            print(f"  {i}. {subtask['title']}")
            print(f"     描述: {subtask['description']}")
            print(f"     优先级: P{subtask['urgency']}")
            print()
    else:
        print(f"生成失败: {response.text}")
    
    print()

def test_ai_assistant():
    """测试AI助手make-subtasks命令"""
    print("=== 测试AI助手make-subtasks命令 ===")
    
    test_data = {
        "command": "make-subtasks",
        "content": "设计并实现用户认证系统",
        "context": "包括登录、注册、密码重置功能"
    }
    
    response = requests.post(f"{BASE_URL}/ai/assistant", json=test_data)
    print(f"AI助手响应: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"执行成功: {result['success']}")
        print(f"结果: {result['result']}")
    else:
        print(f"执行失败: {response.text}")

if __name__ == "__main__":
    print("开始测试TaskWall子任务生成功能...\n")
    
    try:
        test_settings_api()
        test_subtask_generation()
        test_ai_assistant()
        print("测试完成!")
    except Exception as e:
        print(f"测试出错: {e}")