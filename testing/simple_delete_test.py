#!/usr/bin/env python3
"""
简单的删除功能测试 - 专注于API和网络请求
"""

import requests
import json
import time

def test_api_connection():
    """测试API连接"""
    try:
        response = requests.get("http://localhost:8000/tasks/", timeout=5)
        print(f"✅ 后端连接成功，状态码: {response.status_code}")
        return True, response
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务器 (localhost:8000)")
        return False, None
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False, None

def test_frontend_connection():
    """测试前端连接"""
    try:
        response = requests.get("http://localhost:3000/", timeout=5)
        print(f"✅ 前端连接成功，状态码: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到前端服务器 (localhost:3000)")
        return False
    except Exception as e:
        print(f"❌ 前端连接测试失败: {e}")
        return False

def test_delete_api():
    """测试删除API功能"""
    print("\n🔧 测试删除API功能...")
    
    try:
        # 1. 获取现有任务列表
        response = requests.get("http://localhost:8000/tasks/")
        if response.status_code != 200:
            print(f"❌ 获取任务列表失败: {response.status_code}")
            return False
        
        tasks = response.json()
        print(f"📋 当前任务数量: {len(tasks)}")
        
        # 2. 创建一个测试任务
        test_task = {
            "title": "删除测试任务",
            "description": "用于测试删除功能的临时任务",
            "urgency": 2
        }
        
        response = requests.post("http://localhost:8000/tasks/", json=test_task)
        if response.status_code != 200:
            print(f"❌ 创建测试任务失败: {response.status_code} - {response.text}")
            return False
        
        created_task = response.json()
        task_id = created_task['id']
        print(f"✅ 创建测试任务成功，ID: {task_id}")
        
        # 3. 验证任务存在
        response = requests.get(f"http://localhost:8000/tasks/{task_id}")
        if response.status_code != 200:
            print(f"❌ 验证任务存在失败: {response.status_code}")
            return False
        print(f"✅ 任务存在验证成功")
        
        # 4. 删除任务
        response = requests.delete(f"http://localhost:8000/tasks/{task_id}")
        if response.status_code != 200:
            print(f"❌ 删除任务失败: {response.status_code} - {response.text}")
            print(f"📝 响应内容: {response.content}")
            return False
        
        print(f"✅ 删除任务API调用成功")
        
        # 5. 验证任务已被删除
        response = requests.get(f"http://localhost:8000/tasks/{task_id}")
        if response.status_code == 404:
            print(f"✅ 任务删除验证成功 - 任务不存在")
            return True
        else:
            print(f"❌ 任务删除验证失败 - 任务仍然存在: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ 删除API测试异常: {e}")
        return False

def test_frontend_api_calls():
    """测试前端到后端的API调用"""
    print("\n🌐 测试前端API代理...")
    
    try:
        # 测试通过前端代理访问后端API
        response = requests.get("http://localhost:3000/api/tasks/")
        if response.status_code == 200:
            print("✅ 前端API代理工作正常")
            return True
        else:
            print(f"❌ 前端API代理失败: {response.status_code}")
            print(f"📝 响应内容: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ 前端API代理测试异常: {e}")
        return False

def main():
    print("🚀 TaskWall删除功能API测试")
    print("=" * 40)
    
    # 测试连接
    backend_ok, backend_response = test_api_connection()
    frontend_ok = test_frontend_connection()
    
    if not backend_ok:
        print("\n❌ 后端服务器未运行，请先启动后端服务")
        return
    
    if not frontend_ok:
        print("\n⚠️ 前端服务器未运行，但可以继续API测试")
    
    # 显示现有任务
    if backend_response and backend_response.status_code == 200:
        tasks = backend_response.json()
        print(f"\n📋 现有任务数量: {len(tasks)}")
        if tasks:
            print("现有任务:")
            for task in tasks[:3]:  # 只显示前3个
                print(f"   - ID:{task['id']} - {task['title']}")
    
    # 测试删除API
    delete_ok = test_delete_api()
    
    # 测试前端代理（如果前端运行）
    proxy_ok = False
    if frontend_ok:
        proxy_ok = test_frontend_api_calls()
    
    # 总结
    print("\n" + "=" * 40)
    print("📊 测试结果:")
    print(f"   后端服务: {'✅' if backend_ok else '❌'}")
    print(f"   前端服务: {'✅' if frontend_ok else '❌'}")
    print(f"   删除API: {'✅' if delete_ok else '❌'}")
    print(f"   API代理: {'✅' if proxy_ok else '❌' if frontend_ok else '⏭️'}")
    
    if delete_ok:
        print("\n✅ 删除功能API测试通过！")
        print("💡 建议检查项目:")
        print("   1. 前端是否正确调用删除API")
        print("   2. 前端是否正确处理删除响应")
        print("   3. 任务列表是否正确更新")
        print("   4. 键盘快捷键是否正确绑定")
    else:
        print("\n❌ 删除功能存在问题，需要进一步调试")

if __name__ == "__main__":
    main()