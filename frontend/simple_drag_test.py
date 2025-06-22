#!/usr/bin/env python3
"""
简单拖动测试 - 检查任务拖动是否被触发
"""
import asyncio
from playwright.async_api import async_playwright

async def simple_drag_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context()
        page = await context.new_page()
        
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(3000)
        
        # 简单画布调整
        canvas = page.locator('.sticky-canvas').first
        canvas_box = await canvas.bounding_box()
        center_x = canvas_box['x'] + canvas_box['width'] / 2
        center_y = canvas_box['y'] + canvas_box['height'] / 2
        
        await page.mouse.move(center_x, center_y)
        await page.mouse.down(button="middle")
        await page.mouse.move(center_x, center_y + 200)
        await page.mouse.up(button="middle")
        await page.wait_for_timeout(1000)
        
        # 找任务
        task = page.locator('.task-wrapper').first
        if not await task.is_visible():
            print("❌ 任务不可见")
            await browser.close()
            return
            
        task_box = await task.bounding_box()
        print(f"任务位置: ({task_box['x']:.1f}, {task_box['y']:.1f})")
        
        console_messages.clear()
        
        # 简单点击和拖动
        click_x = task_box['x'] + 50
        click_y = task_box['y'] + 50
        
        print(f"点击位置: ({click_x:.1f}, {click_y:.1f})")
        
        await page.mouse.move(click_x, click_y)
        await page.wait_for_timeout(300)
        await page.mouse.down(button="left")
        await page.wait_for_timeout(500)
        await page.mouse.move(click_x + 100, click_y + 50)
        await page.wait_for_timeout(500)
        await page.mouse.up(button="left")
        await page.wait_for_timeout(500)
        
        print("\\n所有控制台消息:")
        for msg in console_messages:
            print(f"  {msg}")
            
        # 检查关键消息
        drag_start_msgs = [msg for msg in console_messages if '开始拖动' in msg]
        task_drag_msgs = [msg for msg in console_messages if '任务拖动' in msg]
        coord_msgs = [msg for msg in console_messages if '坐标计算' in msg]
        
        print(f"\\n消息统计:")
        print(f"  拖动开始: {len(drag_start_msgs)}")
        print(f"  任务拖动: {len(task_drag_msgs)}")
        print(f"  坐标计算: {len(coord_msgs)}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(simple_drag_test())