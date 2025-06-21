#!/usr/bin/env python3
"""
最终Gemini API功能验证测试
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_advanced_subtask_generation():
    """测试高级子任务生成"""
    print("🚀 测试高级子任务生成功能")
    print("=" * 50)
    
    # 使用复杂的现实项目测试
    test_cases = [
        {
            "title": "开发电商网站支付模块",
            "description": "为在线商城开发完整的支付处理模块，需要支持多种支付方式、安全验证、订单跟踪和退款功能",
            "expected_quality": "应该包含具体的技术实现步骤"
        },
        {
            "title": "设计移动应用用户界面",
            "description": "为健身追踪应用设计现代化的用户界面，包括仪表板、进度追踪、社交功能和个人设置",
            "expected_quality": "应该包含UI/UX设计的具体步骤"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试案例 {i}: {test_case['title']}")
        
        response = requests.post(f"{BASE_URL}/ai/subtasks", json={
            "parent_task_title": test_case["title"],
            "parent_task_description": test_case["description"],
            "max_subtasks": 4
        })
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                subtasks = result['subtasks']
                print(f"✅ 生成了 {len(subtasks)} 个子任务:")
                
                quality_score = 0
                for j, subtask in enumerate(subtasks, 1):
                    title = subtask['title']
                    description = subtask['description']
                    
                    print(f"\n  {j}. 🎯 {title}")
                    print(f"     📄 {description}")
                    
                    # 评估质量 - 检查是否是具体的、非模板化的内容
                    if not any(pattern in title for pattern in ["Plan:", "Research:", "Implement:", "Review:", "Document:"]):
                        quality_score += 1
                    
                    if len(description) > 50 and any(keyword in description.lower() for keyword in ['具体', '实现', '开发', '设计', '集成', '测试']):
                        quality_score += 1
                
                quality_percentage = (quality_score / (len(subtasks) * 2)) * 100
                print(f"\n📊 质量评分: {quality_score}/{len(subtasks) * 2} ({quality_percentage:.1f}%)")
                
                if quality_percentage >= 75:
                    print("🎉 高质量AI生成内容 - Gemini API工作优秀！")
                elif quality_percentage >= 50:
                    print("✅ 中等质量AI生成内容 - Gemini API基本正常")
                else:
                    print("⚠️ 低质量内容 - 可能是fallback方法")
            else:
                print(f"❌ 生成失败: {result.get('error')}")
        else:
            print(f"❌ API请求失败: {response.status_code}")

def test_ai_assistant_commands():
    """测试AI助手的各种命令"""
    print("\n\n🤖 测试AI助手各种命令")
    print("=" * 50)
    
    test_commands = [
        {
            "command": "rewrite",
            "content": "这个系统功能很复杂，有很多模块要做，包括用户管理、数据处理、报表生成等等，需要仔细规划。",
            "expected": "应该重写为更清晰的表述"
        },
        {
            "command": "add-emoji",
            "content": "数据库设计完成，开始前端开发，然后进行测试",
            "expected": "应该添加合适的表情符号"
        },
        {
            "command": "summarize",
            "content": "项目管理系统需要包含以下功能：用户注册和登录模块，用户可以创建账户并安全登录；项目创建和管理功能，用户可以创建新项目、编辑项目信息、分配团队成员；任务管理系统，支持创建任务、分配给成员、设置截止日期、跟踪进度；团队协作工具，包括实时聊天、文件共享、评论系统；报告和分析功能，生成项目进度报告、团队效率分析、时间统计等；通知系统，及时提醒用户重要事件和截止日期。",
            "expected": "应该生成简洁的摘要"
        }
    ]
    
    for i, test_cmd in enumerate(test_commands, 1):
        print(f"\n🔧 测试命令 {i}: {test_cmd['command']}")
        print(f"原文: {test_cmd['content'][:50]}...")
        
        response = requests.post(f"{BASE_URL}/ai/assistant", json={
            "command": test_cmd["command"],
            "content": test_cmd["content"],
            "context": "技术文档"
        })
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                ai_result = result['result']
                print(f"AI结果: {ai_result[:100]}...")
                
                # 简单的质量检查
                if ai_result != test_cmd['content'] and len(ai_result) > 10:
                    print("✅ AI处理成功 - 内容已改变")
                else:
                    print("⚠️ 内容未变化 - 可能是fallback")
            else:
                print(f"❌ 处理失败: {result.get('error')}")
        else:
            print(f"❌ API请求失败: {response.status_code}")

def test_api_key_validation():
    """验证API key状态"""
    print("\n\n🔑 验证API Key状态")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/settings/gemini_api_key")
    if response.status_code == 200:
        setting = response.json()
        api_key = setting['value']
        
        if api_key and len(api_key) > 20:
            print(f"✅ API Key有效: {api_key[:10]}...{api_key[-4:]} (长度: {len(api_key)})")
            return True
        else:
            print("❌ API Key无效或过短")
            return False
    else:
        print("❌ 无法获取API Key")
        return False

def main():
    print("🧪 TaskWall Gemini API 最终验证测试")
    print("=" * 60)
    
    # 验证API Key
    if not test_api_key_validation():
        print("\n❌ 测试终止：请先设置有效的Gemini API Key")
        return
    
    # 测试子任务生成
    test_advanced_subtask_generation()
    
    # 测试AI助手命令
    test_ai_assistant_commands()
    
    print("\n" + "=" * 60)
    print("🎯 最终验证完成！")
    print("如果看到高质量、具体的AI生成内容，说明Gemini API完全正常工作！")

if __name__ == "__main__":
    main()