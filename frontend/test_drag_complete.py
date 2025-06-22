#!/usr/bin/env python3
"""
完整的拖动测试 - 包括将任务移动到视口内
"""
import asyncio
from playwright.async_api import async_playwright

async def test_complete_drag():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 监听控制台消息
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        print("🚀 访问TaskWall应用...")
        await page.goto("http://localhost:3000")
        
        # 等待页面加载
        await page.wait_for_timeout(3000)
        
        # 找到画布
        canvas = page.locator('.sticky-canvas').first
        if not await canvas.is_visible():
            print("❌ 画布容器未找到")
            await browser.close()
            return False
            
        canvas_box = await canvas.bounding_box()
        center_x = canvas_box['x'] + canvas_box['width'] / 2
        center_y = canvas_box['y'] + canvas_box['height'] / 2
        
        print("📍 第一步：先平移画布，让任务卡片进入视口")
        
        # 清空控制台消息
        console_messages.clear()
        
        # 中键拖动画布向下移动，使任务进入视口
        await page.mouse.move(center_x, center_y)
        await page.mouse.down(button="middle")
        await page.mouse.move(center_x, center_y + 400)  # 向下拖动400像素
        await page.wait_for_timeout(100)
        await page.mouse.up(button="middle")
        await page.wait_for_timeout(500)
        
        # 检查画布平移是否成功
        canvas_pan_messages = [msg for msg in console_messages if '画布平移' in msg or 'CANVAS_PAN' in msg]
        if canvas_pan_messages:
            print("✅ 画布平移成功:")
            for msg in canvas_pan_messages[-3:]:
                print(f"  {msg}")
        else:
            print("❌ 画布平移失败")
            
        print("\n📍 第二步：查找现在可见的任务卡片")
        
        # 重新查找任务卡片
        task_cards = page.locator('.task-wrapper')
        task_count = await task_cards.count()
        print(f"找到 {task_count} 个任务卡片")
        
        # 找到第一个在视口内的任务
        visible_task = None
        for i in range(min(task_count, 5)):  # 检查前5个任务
            task = task_cards.nth(i)
            if await task.is_visible():
                task_box = await task.bounding_box()
                if (task_box and task_box['y'] > 0 and task_box['y'] < 600 and 
                    task_box['x'] > 0 and task_box['x'] < 1200):
                    visible_task = task
                    print(f"找到可见任务 {i}，位置: ({task_box['x']:.1f}, {task_box['y']:.1f})")
                    break
                    
        if not visible_task:
            print("❌ 没有找到可见的任务卡片")
            await browser.close()
            return False
            
        print("\n📍 第三步：测试任务拖动")
        
        # 清空控制台消息
        console_messages.clear()
        
        # 获取任务位置
        task_box = await visible_task.bounding_box()
        task_x = task_box['x'] + task_box['width'] / 2
        task_y = task_box['y'] + task_box['height'] / 2
        
        print(f"任务点击位置: ({task_x:.1f}, {task_y:.1f})")
        
        # 获取任务ID
        task_id = await visible_task.get_attribute('data-task-id')
        print(f"任务ID: {task_id}")
        
        # 获取任务初始transform
        initial_transform = await visible_task.evaluate("el => el.style.transform")
        print(f"初始transform: {initial_transform}")
        
        # 左键拖动任务
        await page.mouse.move(task_x, task_y)
        await page.wait_for_timeout(100)
        
        print("开始拖动任务...")
        await page.mouse.down(button="left")
        await page.wait_for_timeout(100)
        
        # 拖动100像素
        await page.mouse.move(task_x + 100, task_y + 60)
        await page.wait_for_timeout(200)
        
        await page.mouse.up(button="left")
        await page.wait_for_timeout(500)
        
        # 获取最终transform
        final_transform = await visible_task.evaluate("el => el.style.transform")
        print(f"最终transform: {final_transform}")
        
        # 检查控制台消息
        print("\n📊 任务拖动控制台消息:")
        for msg in console_messages:
            print(f"  {msg}")
            
        # 检查拖动相关消息
        drag_messages = [msg for msg in console_messages if any(keyword in msg for keyword in ['UnifiedDrag', '任务拖动', 'TASK_DRAG'])]
        
        task_drag_success = len(drag_messages) > 0
        
        if task_drag_success:
            print("\n✅ 任务拖动相关消息:")
            for msg in drag_messages:
                print(f"  ✓ {msg}")
        else:
            print("\n❌ 没有检测到任务拖动消息")
            
        # 检查transform是否发生变化
        transform_changed = initial_transform != final_transform
        print(f"\nTransform变化: {'✅ 是' if transform_changed else '❌ 否'}")
        
        overall_success = task_drag_success and transform_changed
        
        print(f"\n🎯 任务拖动测试结果: {'✅ 成功' if overall_success else '❌ 失败'}")
        
        await browser.close()
        return overall_success

if __name__ == "__main__":
    result = asyncio.run(test_complete_drag())
    print(f"\n最终结果: {'修复成功' if result else '仍需调试'}")