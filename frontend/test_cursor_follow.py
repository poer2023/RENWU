#!/usr/bin/env python3
"""
测试任务是否精确跟随鼠标光标
"""
import asyncio
from playwright.async_api import async_playwright

async def test_cursor_follow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()
        
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        print("🚀 测试任务是否精确跟随鼠标...")
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(3000)
        
        canvas = page.locator('.sticky-canvas').first
        canvas_box = await canvas.bounding_box()
        center_x = canvas_box['x'] + canvas_box['width'] / 2
        center_y = canvas_box['y'] + canvas_box['height'] / 2
        
        # 调整画布位置
        await page.mouse.move(center_x, center_y)
        await page.mouse.down(button="middle")
        await page.mouse.move(center_x, center_y + 300)
        await page.mouse.up(button="middle")
        await page.wait_for_timeout(1000)
        
        # 找到任务
        task_cards = page.locator('.task-wrapper')
        task_count = await task_cards.count()
        
        visible_task = None
        for i in range(min(task_count, 5)):
            task = task_cards.nth(i)
            if await task.is_visible():
                task_box = await task.bounding_box()
                if (task_box and 
                    task_box['y'] > 100 and task_box['y'] < 400 and 
                    task_box['x'] > 200 and task_box['x'] < 800):
                    visible_task = task
                    print(f"找到测试任务，位置: ({task_box['x']:.1f}, {task_box['y']:.1f})")
                    break
                    
        if not visible_task:
            print("❌ 无法找到合适的测试任务")
            await browser.close()
            return False
            
        console_messages.clear()
        
        task_box = await visible_task.bounding_box()
        
        # 点击任务的中心位置
        task_center_x = task_box['x'] + task_box['width'] / 2
        task_center_y = task_box['y'] + task_box['height'] / 2
        
        print(f"任务中心位置: ({task_center_x:.1f}, {task_center_y:.1f})")
        
        # 开始拖动
        await page.mouse.move(task_center_x, task_center_y)
        await page.wait_for_timeout(200)
        
        print("开始拖动测试...")
        await page.mouse.down(button="left")
        await page.wait_for_timeout(300)
        
        # 精确移动测试
        test_moves = [
            (task_center_x + 50, task_center_y),      # 向右50px
            (task_center_x + 50, task_center_y + 50), # 向下50px  
            (task_center_x, task_center_y + 50),      # 向左50px
            (task_center_x, task_center_y),           # 回到原点
        ]
        
        for i, (target_x, target_y) in enumerate(test_moves):
            print(f"\\n移动到: ({target_x:.1f}, {target_y:.1f})")
            await page.mouse.move(target_x, target_y)
            await page.wait_for_timeout(300)
            
            # 获取任务当前位置
            current_transform = await visible_task.evaluate("el => el.style.transform")
            
            # 解析transform中的位置
            import re
            match = re.search(r'translate3d\(([^,]+),\s*([^,]+)', current_transform)
            if match:
                task_x = float(match.group(1).replace('px', ''))
                task_y = float(match.group(2).replace('px', ''))
                print(f"任务位置: ({task_x:.1f}, {task_y:.1f})")
                
                # 计算鼠标相对移动和任务相对移动
                mouse_delta_x = target_x - task_center_x
                mouse_delta_y = target_y - task_center_y
                print(f"鼠标移动: ({mouse_delta_x:.1f}, {mouse_delta_y:.1f})")
            else:
                print(f"Transform: {current_transform}")
        
        await page.mouse.up(button="left")
        await page.wait_for_timeout(500)
        
        # 分析坐标计算消息
        print("\\n📊 坐标计算详情:")
        coord_messages = [msg for msg in console_messages if '坐标计算' in msg or '画布变换' in msg or '鼠标' in msg]
        for msg in coord_messages[-10:]:
            print(f"  {msg}")
            
        await browser.close()
        return True

if __name__ == "__main__":
    asyncio.run(test_cursor_follow())