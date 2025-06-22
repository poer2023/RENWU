#!/usr/bin/env python3
"""
TaskWall删除功能测试脚本
测试删除功能的各个方面，包括前端和后端的交互
"""

import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

class TaskWallDeleteTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.session = requests.Session()
        self.driver = None
        
    def setup_browser(self):
        """设置浏览器驱动"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 无头模式
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            print(f"❌ 浏览器设置失败: {e}")
            return False

    def test_backend_api(self):
        """测试后端删除API"""
        print("🔧 测试后端删除API...")
        
        try:
            # 1. 创建一个测试任务
            test_task = {
                "title": "删除测试任务",
                "description": "这是一个用于测试删除功能的任务",
                "urgency": 2
            }
            
            # 创建任务
            response = self.session.post(f"{self.base_url}/tasks/", json=test_task)
            if response.status_code != 200:
                print(f"❌ 创建测试任务失败: {response.status_code} - {response.text}")
                return False
            
            task_data = response.json()
            task_id = task_data['id']
            print(f"✅ 创建测试任务成功，ID: {task_id}")
            
            # 2. 验证任务存在
            response = self.session.get(f"{self.base_url}/tasks/{task_id}")
            if response.status_code != 200:
                print(f"❌ 获取任务失败: {response.status_code}")
                return False
            print(f"✅ 任务获取成功")
            
            # 3. 删除任务
            response = self.session.delete(f"{self.base_url}/tasks/{task_id}")
            if response.status_code != 200:
                print(f"❌ 删除任务失败: {response.status_code} - {response.text}")
                return False
            print(f"✅ 删除任务API调用成功")
            
            # 4. 验证任务已被删除
            response = self.session.get(f"{self.base_url}/tasks/{task_id}")
            if response.status_code == 404:
                print(f"✅ 任务删除验证成功 - 任务不存在")
                return True
            else:
                print(f"❌ 任务删除验证失败 - 任务仍然存在: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 后端API测试异常: {e}")
            return False

    def test_frontend_deletion(self):
        """测试前端删除功能"""
        if not self.driver:
            print("❌ 浏览器未初始化，跳过前端测试")
            return False
            
        print("🖥️ 测试前端删除功能...")
        
        try:
            # 访问前端页面
            self.driver.get(self.frontend_url)
            time.sleep(3)  # 等待页面加载
            
            # 检查页面是否加载成功
            if "TaskWall" not in self.driver.title and "Vite" not in self.driver.title:
                print(f"❌ 前端页面加载失败，标题: {self.driver.title}")
                return False
            print("✅ 前端页面加载成功")
            
            # 等待任务加载
            wait = WebDriverWait(self.driver, 10)
            
            # 检查是否有任务卡片
            tasks = self.driver.find_elements(By.CSS_SELECTOR, "[data-task-id]")
            if not tasks:
                print("⚠️ 没有找到任务卡片，可能需要先创建任务")
                return False
                
            print(f"✅ 找到 {len(tasks)} 个任务")
            
            # 选择第一个任务
            first_task = tasks[0]
            task_id = first_task.get_attribute("data-task-id")
            print(f"📝 选择任务 ID: {task_id}")
            
            # 点击任务选择它
            first_task.click()
            time.sleep(1)
            
            # 查找删除按钮
            delete_button = None
            try:
                # 方法1: 通过删除图标查找
                delete_button = self.driver.find_element(By.XPATH, "//button[contains(@title, '删除') or contains(., '🗑️')]")
            except:
                try:
                    # 方法2: 通过class查找
                    delete_button = self.driver.find_element(By.CSS_SELECTOR, ".node-action-btn.danger")
                except:
                    pass
            
            if delete_button:
                print("✅ 找到删除按钮")
                
                # 点击删除按钮
                delete_button.click()
                time.sleep(1)
                
                # 查找确认对话框
                try:
                    confirm_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '删除') or contains(text(), '确定')]"))
                    )
                    print("✅ 找到确认对话框")
                    
                    # 点击确认删除
                    confirm_button.click()
                    time.sleep(2)
                    
                    # 检查任务是否消失
                    remaining_tasks = self.driver.find_elements(By.CSS_SELECTOR, f"[data-task-id='{task_id}']")
                    if not remaining_tasks:
                        print("✅ 前端删除功能测试成功")
                        return True
                    else:
                        print("❌ 任务删除后仍然存在于DOM中")
                        return False
                        
                except Exception as e:
                    print(f"❌ 确认对话框处理失败: {e}")
                    return False
            else:
                print("❌ 未找到删除按钮")
                return False
                
        except Exception as e:
            print(f"❌ 前端测试异常: {e}")
            return False

    def test_keyboard_shortcuts(self):
        """测试键盘快捷键删除"""
        if not self.driver:
            print("❌ 浏览器未初始化，跳过键盘测试")
            return False
            
        print("⌨️ 测试键盘快捷键删除...")
        
        try:
            # 刷新页面
            self.driver.refresh()
            time.sleep(3)
            
            # 选择任务
            tasks = self.driver.find_elements(By.CSS_SELECTOR, "[data-task-id]")
            if not tasks:
                print("⚠️ 没有找到任务进行键盘测试")
                return False
                
            first_task = tasks[0]
            task_id = first_task.get_attribute("data-task-id")
            
            # 点击选择任务
            first_task.click()
            time.sleep(1)
            
            # 确保任务获得焦点
            first_task.send_keys("")  # 激活元素
            
            # 测试Delete键
            print("🔑 测试Delete键...")
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.DELETE).perform()
            time.sleep(1)
            
            # 检查是否出现确认对话框
            try:
                wait = WebDriverWait(self.driver, 5)
                confirm_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '删除') or contains(text(), '确定')]"))
                )
                print("✅ Delete键触发确认对话框成功")
                
                # 取消删除以测试其他快捷键
                cancel_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '取消')]")
                cancel_button.click()
                time.sleep(1)
                
            except:
                print("❌ Delete键未触发确认对话框")
                return False
            
            # 测试Ctrl+D
            print("🔑 测试Ctrl+D...")
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('d').key_up(Keys.CONTROL).perform()
            time.sleep(1)
            
            try:
                wait = WebDriverWait(self.driver, 5)
                confirm_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '删除') or contains(text(), '确定')]"))
                )
                print("✅ Ctrl+D键触发确认对话框成功")
                
                # 取消删除
                cancel_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '取消')]")
                cancel_button.click()
                
                return True
                
            except:
                print("❌ Ctrl+D键未触发确认对话框")
                return False
                
        except Exception as e:
            print(f"❌ 键盘测试异常: {e}")
            return False

    def check_console_errors(self):
        """检查浏览器控制台错误"""
        if not self.driver:
            return []
            
        try:
            logs = self.driver.get_log('browser')
            errors = [log for log in logs if log['level'] == 'SEVERE']
            
            if errors:
                print("🚨 浏览器控制台错误:")
                for error in errors:
                    print(f"   ❌ {error['message']}")
            else:
                print("✅ 没有发现严重的控制台错误")
                
            return errors
        except Exception as e:
            print(f"⚠️ 无法获取控制台日志: {e}")
            return []

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始TaskWall删除功能综合测试")
        print("=" * 50)
        
        # 测试后端API
        backend_ok = self.test_backend_api()
        
        # 设置浏览器
        browser_ok = self.setup_browser()
        
        # 测试前端功能
        frontend_ok = False
        keyboard_ok = False
        if browser_ok:
            frontend_ok = self.test_frontend_deletion()
            keyboard_ok = self.test_keyboard_shortcuts()
            self.check_console_errors()
        
        # 清理
        if self.driver:
            self.driver.quit()
        
        # 报告结果
        print("\n" + "=" * 50)
        print("🏁 测试结果总结:")
        print(f"   后端API删除: {'✅ 通过' if backend_ok else '❌ 失败'}")
        print(f"   前端按钮删除: {'✅ 通过' if frontend_ok else '❌ 失败'}")
        print(f"   键盘快捷键删除: {'✅ 通过' if keyboard_ok else '❌ 失败'}")
        
        all_passed = backend_ok and (frontend_ok or keyboard_ok)
        print(f"\n总体评估: {'✅ 删除功能正常' if all_passed else '❌ 删除功能存在问题'}")
        
        return {
            'backend_api': backend_ok,
            'frontend_button': frontend_ok,
            'keyboard_shortcuts': keyboard_ok,
            'overall': all_passed
        }

if __name__ == "__main__":
    tester = TaskWallDeleteTester()
    tester.run_all_tests()