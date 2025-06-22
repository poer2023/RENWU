#!/usr/bin/env python3
"""
确保任务在视口内并测试拖动
"""
import asyncio
from playwright.async_api import async_playwright

async def test_viewport_task():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context()
        page = await context.new_page()
        
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(3000)
        
        canvas = page.locator('.sticky-canvas').first
        canvas_box = await canvas.bounding_box()
        
        print("📍 调整画布位置，确保任务在视口内...")
        
        # 大幅度调整画布，确保任务进入视口
        center_x = canvas_box['x'] + canvas_box['width'] / 2
        center_y = canvas_box['y'] + canvas_box['height'] / 2
        
        # 多次调整找到任务
        for attempt in range(3):
            await page.mouse.move(center_x, center_y)
            await page.mouse.down(button="middle")
            await page.mouse.move(center_x + 100, center_y + 400)  # 大幅移动
            await page.mouse.up(button="middle")
            await page.wait_for_timeout(1000)
            
            # 检查是否有任务在合理位置
            tasks = page.locator('.task-wrapper')
            task_count = await tasks.count()
            
            found_visible = False
            for i in range(min(task_count, 5)):
                task = tasks.nth(i)
                if await task.is_visible():
                    task_box = await task.bounding_box()
                    if (task_box and 
                        task_box['y'] > 50 and task_box['y'] < 600 and 
                        task_box['x'] > 50 and task_box['x'] < 1000):
                        
                        print(f"找到合适的任务 {i}: ({task_box['x']:.1f}, {task_box['y']:.1f})")
                        
                        # 测试这个任务的DOM结构
                        task_info = await task.evaluate("""
                            el => ({
                                className: el.className,
                                dataTaskId: el.dataset.taskId,
                                innerHTML: el.innerHTML.substring(0, 200)
                            })
                        """)
                        print(f"任务信息: ID={task_info['dataTaskId']}, class={task_info['className']}")
                        
                        # 测试点击这个任务
                        console_messages.clear()
                        
                        click_x = task_box['x'] + 50
                        click_y = task_box['y'] + 50
                        
                        print(f"\\n测试点击位置: ({click_x:.1f}, {click_y:.1f})")
                        
                        # 获取点击位置的元素信息
                        click_target = await page.evaluate(f"""
                            () => {{
                                const el = document.elementFromPoint({click_x}, {click_y});
                                if (!el) return null;
                                return {{
                                    tagName: el.tagName,
                                    className: el.className,
                                    closestTaskWrapper: !!el.closest('.task-wrapper'),
                                    closestTaskNode: !!el.closest('.task-node')
                                }};
                            }}
                        """)
                        print(f"点击目标元素: {click_target}")
                        
                        # 执行拖动
                        await page.mouse.move(click_x, click_y)
                        await page.wait_for_timeout(200)
                        await page.mouse.down(button="left")
                        await page.wait_for_timeout(300)
                        await page.mouse.move(click_x + 50, click_y + 30)
                        await page.wait_for_timeout(300)
                        await page.mouse.up(button="left")
                        await page.wait_for_timeout(500)
                        
                        print("\\n拖动后的控制台消息:")
                        for msg in console_messages:
                            print(f"  {msg}")
                            
                        found_visible = True
                        break
                        
            if found_visible:
                break
            else:
                print(f"尝试 {attempt + 1}: 未找到合适的可见任务，继续调整...")
        
        if not found_visible:
            print("❌ 经过多次调整仍未找到合适的任务")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_viewport_task())