#!/usr/bin/env python3
"""
测试当前API状态和真实Gemini API功能
"""
import requests
import json

BASE_URL = "http://localhost:8765"

def check_current_api_key():
    """检查当前API key状态"""
    print("=== 检查当前API Key状态 ===")
    
    response = requests.get(f"{BASE_URL}/settings/gemini_api_key")
    if response.status_code == 200:
        setting = response.json()
        api_key = setting['value']
        
        if not api_key or len(api_key.strip()) == 0:
            print("❌ 未找到API key")
            return None
        elif api_key == "test-api-key-12345":
            print("⚠️  检测到测试API key，需要设置真实的API key")
            return None
        elif len(api_key) < 20:
            print(f"⚠️  API key过短 ({len(api_key)} 字符)，可能不是有效的Gemini API key")
            return api_key
        else:
            print(f"✅ 检测到API key: {api_key[:10]}...{api_key[-4:]} (长度: {len(api_key)})")
            return api_key
    else:
        print(f"❌ 无法获取API key: {response.status_code}")
        return None

def test_subtask_generation_with_real_task():
    """测试真实任务的子任务生成"""
    print("\n=== 测试子任务生成 ===")
    
    # 使用具体的、易于验证的任务
    test_data = {
        "parent_task_title": "为咖啡店设计点餐系统",
        "parent_task_description": "开发一个完整的咖啡店点餐系统，包括顾客下单、支付处理、订单管理和库存跟踪功能",
        "max_subtasks": 5
    }
    
    print(f"测试任务: {test_data['parent_task_title']}")
    
    response = requests.post(f"{BASE_URL}/ai/subtasks", json=test_data)
    print(f"API响应状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result['success']:
            subtasks = result['subtasks']
            print(f"\n🎯 生成了 {len(subtasks)} 个子任务:")
            
            is_ai_generated = True
            fallback_patterns = ["Plan:", "Research:", "Implement:", "Review:", "Document:"]
            
            for i, subtask in enumerate(subtasks, 1):
                title = subtask['title']
                description = subtask['description']
                
                print(f"\n  {i}. 📌 {title}")
                print(f"     📝 {description}")
                print(f"     🏷️  优先级: P{subtask['urgency']}")
                
                # 检查是否是fallback模式
                if any(pattern in title for pattern in fallback_patterns):
                    is_ai_generated = False
                    print(f"     🤖 类型: Fallback生成 (模板化)")
                else:
                    print(f"     🤖 类型: 可能是AI生成 (具体化)")
            
            print(f"\n🔍 总体评估:")
            if is_ai_generated:
                print("✅ 子任务内容具体且个性化，很可能是真实AI生成")
                print("✨ Gemini API工作正常！")
            else:
                print("⚠️  子任务使用模板化内容，可能是fallback方法")
                print("🔧 建议检查API key是否有效")
                
        else:
            print(f"❌ 生成失败: {result.get('error', 'Unknown error')}")
    else:
        print(f"❌ API请求失败: {response.text}")

def test_ai_assistant_rewrite():
    """测试AI助手的文本重写功能"""
    print("\n=== 测试AI助手文本重写功能 ===")
    
    test_data = {
        "command": "rewrite",
        "content": "我们需要做一个网站，要有很多功能，包括用户可以注册和登录，还要能发帖子和评论",
        "context": "技术文档"
    }
    
    response = requests.post(f"{BASE_URL}/ai/assistant", json=test_data)
    print(f"API响应状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result['success']:
            original = test_data['content']
            rewritten = result['result']
            
            print(f"📝 原文: {original}")
            print(f"✏️  重写: {rewritten}")
            
            if rewritten != original and len(rewritten) > len(original) * 0.8:
                print("✅ 文本已重写，可能是AI生成")
            else:
                print("⚠️  文本未改变或改变很小，可能是fallback")
        else:
            print(f"❌ 重写失败: {result.get('error', 'Unknown error')}")
    else:
        print(f"❌ API请求失败: {response.text}")

if __name__ == "__main__":
    print("🔬 TaskWall API状态检测")
    print("=" * 50)
    
    # 检查当前API key
    current_api_key = check_current_api_key()
    
    if current_api_key is None:
        print("\n💡 如何设置真实的Gemini API Key:")
        print("1. 访问 https://makersuite.google.com/app/apikey")
        print("2. 创建新的API key")
        print("3. 打开TaskWall前端 → 按⌘K → 搜索'设置' → AI设置 → 粘贴API key → 保存")
        print("4. 重新运行此测试")
    else:
        print(f"\n📊 当前API key: {current_api_key[:15]}...")
        
        # 运行测试
        test_subtask_generation_with_real_task()
        test_ai_assistant_rewrite()
        
        print("\n" + "=" * 50)
        print("🎯 测试完成!")
        print("如果看到具体、个性化的内容 → 真实AI正常工作 ✅")
        print("如果看到模板化、通用的内容 → 使用fallback方法 ⚠️")