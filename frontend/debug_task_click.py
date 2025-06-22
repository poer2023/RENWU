#!/usr/bin/env python3
"""
调试任务点击问题 - 详细检查任务卡片的点击
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_task_click():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 监听控制台消息
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        print("🚀 访问TaskWall应用...")
        await page.goto("http://localhost:3000")
        
        # 等待页面加载
        await page.wait_for_timeout(3000)
        
        print("📋 查找画布和任务卡片...")
        canvas = page.locator('.sticky-canvas').first
        if not await canvas.is_visible():
            print("❌ 画布容器未找到")
            await browser.close()
            return
            
        # 查找所有任务卡片
        task_cards = page.locator('.task-wrapper')
        task_count = await task_cards.count()
        print(f"找到 {task_count} 个任务卡片")
        
        if task_count == 0:
            print("❌ 没有找到任务卡片")
            await browser.close()
            return
            
        # 检查第一个任务卡片
        first_task = task_cards.first
        if await first_task.is_visible():
            task_box = await first_task.bounding_box()
            print(f"第一个任务卡片边界: {task_box}")
            
            # 获取任务ID
            task_id = await first_task.get_attribute('data-task-id')
            print(f"任务ID: {task_id}")
            
            # 检查任务卡片在视口中的位置
            viewport = page.viewport_size
            print(f"视口大小: {viewport}")
            
            # 如果任务在视口外，先滚动到任务位置
            if task_box and (task_box['x'] < 0 or task_box['y'] < 0 or 
                           task_box['x'] > viewport['width'] or task_box['y'] > viewport['height']):
                print("任务在视口外，滚动到任务位置...")
                await first_task.scroll_into_view_if_needed()
                await page.wait_for_timeout(1000)
                
                # 重新获取边界
                task_box = await first_task.bounding_box()
                print(f"滚动后任务卡片边界: {task_box}")
        
        # 清空控制台消息
        console_messages.clear()
        
        print("🎯 开始点击任务卡片...")
        
        # 计算点击位置
        if task_box:
            click_x = task_box['x'] + task_box['width'] / 2
            click_y = task_box['y'] + task_box['height'] / 2
            
            print(f"点击位置: ({click_x:.1f}, {click_y:.1f})")
            
            # 移动到任务上
            await page.mouse.move(click_x, click_y)
            await page.wait_for_timeout(100)
            
            # 左键按下开始拖动
            print("按下左键...")
            await page.mouse.down(button="left")
            await page.wait_for_timeout(200)
            
            # 拖动50像素
            print("开始拖动...")
            await page.mouse.move(click_x + 50, click_y + 30)
            await page.wait_for_timeout(300)
            
            # 松开鼠标
            print("松开左键...")
            await page.mouse.up(button="left")
            await page.wait_for_timeout(500)
            
            print("\n📊 控制台消息:")
            for msg in console_messages:
                print(f"  {msg}")
                
            # 特别查找UnifiedDrag相关消息
            unified_messages = [msg for msg in console_messages if 'UnifiedDrag' in msg]
            if unified_messages:
                print("\n✅ 统一拖动系统消息:")
                for msg in unified_messages:
                    print(f"  ✓ {msg}")
            else:
                print("\n❌ 没有统一拖动系统消息")
                
            # 检查是否有任务相关消息
            task_messages = [msg for msg in console_messages if any(keyword in msg.lower() for keyword in ['task', '任务', 'sticky'])]
            if task_messages:
                print("\n📝 任务相关消息:")
                for msg in task_messages:
                    print(f"  📝 {msg}")
        else:
            print("❌ 无法获取任务边界")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_task_click())