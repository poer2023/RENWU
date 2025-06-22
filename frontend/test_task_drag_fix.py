#!/usr/bin/env python3
"""
测试任务拖动修复效果
"""
import asyncio
from playwright.async_api import async_playwright

async def test_task_drag_fix():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=150)
        context = await browser.new_context()
        page = await context.new_page()
        
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        print("🚀 测试任务拖动修复...")
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(3000)
        
        canvas = page.locator('.sticky-canvas').first
        if not await canvas.is_visible():
            print("❌ 画布容器未找到")
            await browser.close()
            return False
            
        canvas_box = await canvas.bounding_box()
        center_x = canvas_box['x'] + canvas_box['width'] / 2
        center_y = canvas_box['y'] + canvas_box['height'] / 2
        
        print("📍 第一步：调整画布位置找到可见任务")
        
        # 调整画布位置
        await page.mouse.move(center_x, center_y)
        await page.mouse.down(button="middle")
        await page.mouse.move(center_x, center_y + 300)
        await page.mouse.up(button="middle")
        await page.wait_for_timeout(1000)
        
        # 查找可见任务
        task_cards = page.locator('.task-wrapper')
        task_count = await task_cards.count()
        
        visible_task = None
        for i in range(min(task_count, 8)):
            task = task_cards.nth(i)
            if await task.is_visible():
                task_box = await task.bounding_box()
                if (task_box and 
                    task_box['y'] > 100 and task_box['y'] < 500 and 
                    task_box['x'] > 100 and task_box['x'] < 1000):
                    visible_task = task
                    print(f"找到可见任务 {i}，位置: ({task_box['x']:.1f}, {task_box['y']:.1f})")
                    break
                    
        if not visible_task:
            print("❌ 无法找到合适的可见任务")
            await browser.close()
            return False
            
        print("\\n📍 第二步：详细测试任务拖动")
        console_messages.clear()
        
        task_box = await visible_task.bounding_box()
        start_x = task_box['x'] + 50  # 点击任务左上角附近
        start_y = task_box['y'] + 30
        
        task_id = await visible_task.get_attribute('data-task-id')
        print(f"任务ID: {task_id}")
        print(f"点击位置: ({start_x:.1f}, {start_y:.1f})")
        
        # 获取初始transform
        initial_transform = await visible_task.evaluate("el => el.style.transform")
        print(f"初始transform: {initial_transform}")
        
        # 开始拖动
        await page.mouse.move(start_x, start_y)
        await page.wait_for_timeout(200)
        
        print("按下左键开始拖动...")
        await page.mouse.down(button="left")
        await page.wait_for_timeout(300)
        
        # 缓慢拖动，观察是否跟随
        drag_steps = [
            (start_x + 20, start_y + 10),
            (start_x + 40, start_y + 20),
            (start_x + 60, start_y + 30),
            (start_x + 80, start_y + 40),
            (start_x + 100, start_y + 50)
        ]
        
        print("开始分步拖动...")
        for i, (x, y) in enumerate(drag_steps):
            await page.mouse.move(x, y)
            await page.wait_for_timeout(200)
            
            # 检查位置是否更新
            current_transform = await visible_task.evaluate("el => el.style.transform")
            print(f"步骤 {i+1}: 鼠标位置({x:.1f}, {y:.1f}) -> transform: {current_transform}")
            
        print("松开左键...")
        await page.mouse.up(button="left")
        await page.wait_for_timeout(500)
        
        # 获取最终transform
        final_transform = await visible_task.evaluate("el => el.style.transform")
        print(f"最终transform: {final_transform}")
        
        # 分析结果
        transform_changed = initial_transform != final_transform
        
        print("\\n📊 控制台消息分析:")
        coordinate_messages = [msg for msg in console_messages if '坐标计算' in msg or '📍' in msg or '📊' in msg]
        task_drag_messages = [msg for msg in console_messages if '任务拖动' in msg]
        
        if coordinate_messages:
            print("✅ 坐标计算消息:")
            for msg in coordinate_messages[-3:]:
                print(f"  {msg}")
        else:
            print("❌ 没有坐标计算消息")
            
        if task_drag_messages:
            print("\\n✅ 任务拖动消息:")
            for msg in task_drag_messages[-3:]:
                print(f"  {msg}")
        else:
            print("\\n❌ 没有任务拖动消息")
            
        # 检查是否有错误
        error_messages = [msg for msg in console_messages if '❌' in msg or 'error' in msg.lower()]
        if error_messages:
            print("\\n⚠️ 错误消息:")
            for msg in error_messages:
                print(f"  {msg}")
                
        success = (transform_changed and 
                  len(coordinate_messages) > 0 and 
                  len(task_drag_messages) > 0 and
                  len(error_messages) == 0)
        
        print(f"\\n🎯 任务拖动测试结果:")
        print(f"   - Transform变化: {'✅' if transform_changed else '❌'}")
        print(f"   - 坐标计算: {'✅' if len(coordinate_messages) > 0 else '❌'}")
        print(f"   - 拖动检测: {'✅' if len(task_drag_messages) > 0 else '❌'}")
        print(f"   - 无错误: {'✅' if len(error_messages) == 0 else '❌'}")
        print(f"   - 总体: {'✅ 成功' if success else '❌ 失败'}")
        
        await browser.close()
        return success

if __name__ == "__main__":
    result = asyncio.run(test_task_drag_fix())
    print(f"\\n{'='*50}")
    print(f"🎯 任务拖动修复状态: {'✅ 成功' if result else '❌ 仍需调试'}")
    print(f"{'='*50}")