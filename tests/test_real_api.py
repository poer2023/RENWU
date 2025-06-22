#!/usr/bin/env python3
"""
测试真实Gemini API功能
"""
import requests
import json

BASE_URL = "http://localhost:8765"

def set_real_api_key():
    """设置真实API key"""
    print("=== 设置真实Gemini API Key ===")
    print("请访问 https://makersuite.google.com/app/apikey 获取你的API key")
    print()
    
    # 这里应该让用户通过前端界面输入
    api_key = input("请通过前端界面设置你的真实Gemini API key，然后按Enter继续...")
    
    # 检查是否已设置
    response = requests.get(f"{BASE_URL}/settings/gemini_api_key")
    if response.status_code == 200:
        setting = response.json()
        if setting['value'] and len(setting['value']) > 20:  # 真实API key通常很长
            print(f"✅ 检测到API key: {setting['value'][:10]}...{setting['value'][-4:]}")
            return True
        else:
            print("❌ 未检测到有效的API key，请确保已通过前端设置页面保存")
            return False
    return False

def test_real_subtask_generation():
    """测试真实的子任务生成"""
    print("\n=== 测试真实子任务生成 ===")
    
    # 测试数据 - 使用更具体的任务描述
    test_data = {
        "parent_task_title": "设计电商网站首页",
        "parent_task_description": "为新的在线商城设计一个现代化的首页，包括产品展示、用户导航、搜索功能和购物车",
        "max_subtasks": 4
    }
    
    response = requests.post(f"{BASE_URL}/ai/subtasks", json=test_data)
    print(f"请求状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"生成成功: {result['success']}")
        
        if result['success']:
            subtasks = result['subtasks']
            print(f"生成的子任务数量: {len(subtasks)}")
            print("\n📋 AI生成的子任务:")
            
            for i, subtask in enumerate(subtasks, 1):
                print(f"\n  {i}. 📌 {subtask['title']}")
                print(f"     📝 {subtask['description']}")
                print(f"     🏷️  优先级: P{subtask['urgency']}")
                
                # 检查是否是fallback生成的内容
                if "Plan:" in subtask['title'] or "Research:" in subtask['title']:
                    print("     ⚠️  这看起来像是fallback生成的内容")
                else:
                    print("     ✅ 这看起来像是AI生成的内容")
        else:
            print(f"生成失败: {result.get('error', 'Unknown error')}")
    else:
        print(f"请求失败: {response.text}")

def test_ai_assistant_with_real_api():
    """测试AI助手的make-subtasks功能"""
    print("\n=== 测试AI助手make-subtasks功能 ===")
    
    test_data = {
        "command": "make-subtasks",
        "content": "开发一个移动端APP的用户注册登录模块",
        "context": "需要支持手机号、邮箱登录，包含短信验证码、找回密码功能"
    }
    
    response = requests.post(f"{BASE_URL}/ai/assistant", json=test_data)
    print(f"请求状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"执行成功: {result['success']}")
        
        if result['success']:
            print("🤖 AI助手返回结果:")
            print(result['result'])
            
            # 尝试解析JSON结果
            try:
                subtasks = json.loads(result['result'])
                if isinstance(subtasks, list):
                    print(f"\n解析到 {len(subtasks)} 个子任务:")
                    for i, subtask in enumerate(subtasks, 1):
                        print(f"  {i}. {subtask.get('title', 'No title')}")
                        print(f"     {subtask.get('description', 'No description')}")
            except:
                print("返回结果不是JSON格式，可能是纯文本描述")
        else:
            print(f"执行失败: {result.get('error', 'Unknown error')}")
    else:
        print(f"请求失败: {response.text}")

if __name__ == "__main__":
    print("🚀 TaskWall 真实Gemini API测试")
    print("=" * 50)
    
    # 检查API key设置
    if set_real_api_key():
        # 测试子任务生成
        test_real_subtask_generation()
        
        # 测试AI助手
        test_ai_assistant_with_real_api()
        
        print("\n" + "=" * 50)
        print("✅ 测试完成！如果看到具体的、非模板化的任务内容，说明真实API工作正常")
        print("❌ 如果看到 'Plan:', 'Research:' 等模板内容，说明仍在使用fallback方法")
    else:
        print("\n❌ 请先设置真实的API key")
        print("步骤: 打开前端 → ⌘K → 搜索'设置' → AI设置 → 填入API key → 保存")