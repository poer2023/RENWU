#!/usr/bin/env python3
"""
测试任务的不同区域点击
"""
import asyncio
from playwright.async_api import async_playwright

async def test_task_regions():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=400)
        context = await browser.new_context()
        page = await context.new_page()
        
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(3000)
        
        # 找到任务
        canvas = page.locator('.sticky-canvas').first
        canvas_box = await canvas.bounding_box()
        center_x = canvas_box['x'] + canvas_box['width'] / 2
        center_y = canvas_box['y'] + canvas_box['height'] / 2
        
        # 调整画布
        await page.mouse.move(center_x, center_y)
        await page.mouse.down(button="middle")
        await page.mouse.move(center_x + 100, center_y + 400)
        await page.mouse.up(button="middle")
        await page.wait_for_timeout(1000)
        
        task = page.locator('.task-wrapper').first
        if not await task.is_visible():
            print("❌ 任务不可见")
            await browser.close()
            return
            
        task_box = await task.bounding_box()
        print(f"任务边界: x={task_box['x']:.1f}, y={task_box['y']:.1f}, w={task_box['width']:.1f}, h={task_box['height']:.1f}")
        
        # 测试任务不同区域的点击
        test_points = [
            (task_box['x'] + 10, task_box['y'] + 10, "左上角边缘"),
            (task_box['x'] + 50, task_box['y'] + 30, "左上区域"),
            (task_box['x'] + task_box['width']/2, task_box['y'] + 30, "顶部中央"),
            (task_box['x'] + task_box['width']/2, task_box['y'] + task_box['height']/2, "正中心"),
            (task_box['x'] + task_box['width']/2, task_box['y'] + task_box['height'] - 30, "底部中央"),
            (task_box['x'] + task_box['width'] - 20, task_box['y'] + task_box['height'] - 20, "右下角"),
        ]
        
        for i, (x, y, desc) in enumerate(test_points):
            print(f"\\n测试点 {i+1}: {desc} ({x:.1f}, {y:.1f})")
            
            # 检查该点的元素
            element_info = await page.evaluate(f"""
                () => {{
                    const el = document.elementFromPoint({x}, {y});
                    if (!el) return null;
                    
                    return {{
                        tagName: el.tagName,
                        className: el.className,
                        id: el.id,
                        taskWrapper: !!el.closest('.task-wrapper'),
                        taskNode: !!el.closest('.task-node'),
                        dataTaskId: el.closest('.task-wrapper')?.dataset?.taskId || 'none'
                    }};
                }}
            """)
            
            print(f"  元素: {element_info}")
            
            # 如果找到了可以识别任务的点，测试拖动
            if element_info and (element_info['taskWrapper'] or element_info['taskNode']):
                print(f"  ✅ 找到可用的点击区域！")
                
                console_messages.clear()
                
                # 执行简单的拖动测试
                await page.mouse.move(x, y)
                await page.wait_for_timeout(200)
                await page.mouse.down(button="left")
                await page.wait_for_timeout(300)
                await page.mouse.move(x + 30, y + 20)
                await page.wait_for_timeout(300)
                await page.mouse.up(button="left")
                await page.wait_for_timeout(300)
                
                print("  拖动测试消息:")
                for msg in console_messages[-5:]:
                    print(f"    {msg}")
                    
                # 检查是否成功触发任务拖动
                task_drag_detected = any('任务拖动' in msg for msg in console_messages)
                if task_drag_detected:
                    print("  🎉 成功检测到任务拖动！")
                    break
                else:
                    print("  ❌ 未检测到任务拖动")
            else:
                print(f"  ❌ 该点无法识别任务")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_task_regions())