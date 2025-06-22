#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time

def test_middle_click_drag():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # 监听控制台消息
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        print("🚀 访问TaskWall应用...")
        page.goto("http://localhost:3001")
        
        # 等待页面加载
        page.wait_for_timeout(3000)
        
        print("📋 查找画布容器...")
        canvas = page.locator('.sticky-canvas').first
        if not canvas.is_visible():
            print("❌ 画布容器未找到")
            browser.close()
            return
            
        print("✅ 画布容器已找到")
        
        # 获取画布位置
        box = canvas.bounding_box()
        center_x = box['x'] + box['width'] / 2
        center_y = box['y'] + box['height'] / 2
        
        print(f"🎯 开始中键拖动测试，位置: ({center_x}, {center_y})")
        
        # 清空控制台消息
        console_messages.clear()
        
        # 中键按下
        page.mouse.move(center_x, center_y)
        page.mouse.down(button="middle")
        
        # 等待一帧
        page.wait_for_timeout(50)
        
        # 拖动
        page.mouse.move(center_x + 100, center_y + 50)
        page.wait_for_timeout(100)
        
        # 松开
        page.mouse.up(button="middle")
        
        # 等待事件处理
        page.wait_for_timeout(500)
        
        print("📊 控制台消息:")
        for msg in console_messages[-10:]:  # 只显示最后10条
            print(f"  {msg}")
            
        # 检查是否有拖动相关消息
        drag_messages = [msg for msg in console_messages if any(keyword in msg.lower() for keyword in ['drag', '拖动', 'unifid', 'pan', '平移'])]
        
        if drag_messages:
            print("✅ 检测到拖动相关消息:")
            for msg in drag_messages:
                print(f"  ✓ {msg}")
        else:
            print("❌ 未检测到拖动相关消息")
            
        browser.close()
        
        return len(drag_messages) > 0

if __name__ == "__main__":
    # 运行测试
    result = test_middle_click_drag()
    print(f"\n🎯 测试结果: {'成功' if result else '失败'}")