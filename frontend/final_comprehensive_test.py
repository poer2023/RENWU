#!/usr/bin/env python3
"""
最终综合测试 - 完整验证拖动系统
"""
import asyncio
from playwright.async_api import async_playwright

async def final_comprehensive_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=80)
        context = await browser.new_context()
        page = await context.new_page()
        
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        print("🚀 启动最终综合测试...")
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
        
        # === 测试1: 中键拖动画布 ===
        print("\n=== 测试1: 中键拖动画布 ===")
        console_messages.clear()
        
        await page.mouse.move(center_x, center_y)
        await page.mouse.down(button="middle")
        await page.mouse.move(center_x + 150, center_y + 100)
        await page.wait_for_timeout(100)
        await page.mouse.up(button="middle")
        await page.wait_for_timeout(300)
        
        canvas_messages = [msg for msg in console_messages if '画布平移' in msg]
        canvas_success = len(canvas_messages) > 0
        print(f"画布拖动: {'✅ 成功' if canvas_success else '❌ 失败'}")
        
        # === 测试2: 寻找可见任务并拖动 ===
        print("\n=== 测试2: 寻找并拖动可见任务 ===")
        
        # 多次调整视图以找到可见任务
        for attempt in range(3):
            task_cards = page.locator('.task-wrapper')
            task_count = await task_cards.count()
            
            visible_task = None
            for i in range(min(task_count, 10)):
                task = task_cards.nth(i)
                if await task.is_visible():
                    task_box = await task.bounding_box()
                    if (task_box and 
                        task_box['y'] > 50 and task_box['y'] < 500 and 
                        task_box['x'] > 50 and task_box['x'] < 1000):
                        visible_task = task
                        print(f"找到可见任务 {i}，位置: ({task_box['x']:.1f}, {task_box['y']:.1f})")
                        break
                        
            if visible_task:
                break
                
            # 如果没找到，继续调整画布位置
            print(f"尝试 {attempt + 1}: 调整画布位置寻找可见任务...")
            await page.mouse.move(center_x, center_y)
            await page.mouse.down(button="middle")
            await page.mouse.move(center_x + 50, center_y + 200)
            await page.mouse.up(button="middle")
            await page.wait_for_timeout(500)
            
        if not visible_task:
            print("❌ 无法找到可见任务")
            await browser.close()
            return False
            
        # 测试任务拖动
        console_messages.clear()
        
        task_box = await visible_task.bounding_box()
        task_x = task_box['x'] + task_box['width'] / 2
        task_y = task_box['y'] + task_box['height'] / 2
        
        task_id = await visible_task.get_attribute('data-task-id')
        print(f"测试任务ID: {task_id}")
        
        # 获取初始位置
        initial_transform = await visible_task.evaluate("el => el.style.transform")
        
        # 执行拖动
        await page.mouse.move(task_x, task_y)
        await page.wait_for_timeout(100)
        await page.mouse.down(button="left")
        await page.wait_for_timeout(100)
        await page.mouse.move(task_x + 80, task_y + 50)
        await page.wait_for_timeout(200)
        await page.mouse.up(button="left")
        await page.wait_for_timeout(500)
        
        # 获取最终位置
        final_transform = await visible_task.evaluate("el => el.style.transform")
        
        # 分析结果
        task_messages = [msg for msg in console_messages if '任务拖动' in msg]
        unified_messages = [msg for msg in console_messages if 'UnifiedDrag' in msg and ('任务' in msg or 'TASK' in msg)]
        transform_changed = initial_transform != final_transform
        
        task_success = len(task_messages) > 0 and len(unified_messages) > 0 and transform_changed
        
        print(f"任务拖动检测: {'✅ 成功' if len(task_messages) > 0 else '❌ 失败'}")
        print(f"统一拖动系统: {'✅ 正常' if len(unified_messages) > 0 else '❌ 异常'}")
        print(f"位置变化: {'✅ 是' if transform_changed else '❌ 否'}")
        print(f"任务拖动: {'✅ 成功' if task_success else '❌ 失败'}")
        
        if task_success:
            print("\\n✅ 任务拖动相关消息:")
            for msg in (task_messages + unified_messages)[-5:]:
                print(f"  {msg}")
                
        # === 综合结果 ===
        overall_success = canvas_success and task_success
        
        print(f"\\n🎯 最终测试结果:")
        print(f"   - 画布中键拖动: {'✅' if canvas_success else '❌'}")
        print(f"   - 任务左键拖动: {'✅' if task_success else '❌'}")
        print(f"   - 总体评价: {'✅ 完全成功' if overall_success else '❌ 部分失败'}")
        
        await browser.close()
        return overall_success

if __name__ == "__main__":
    result = asyncio.run(final_comprehensive_test())
    print(f"\\n{'='*50}")
    print(f"🏆 拖动系统修复状态: {'✅ 完全成功' if result else '❌ 需要进一步调试'}")
    print(f"{'='*50}")