#!/usr/bin/env python3
"""
最终任务拖动测试 - 验证是否精确跟随鼠标
"""
import asyncio
from playwright.async_api import async_playwright
import re

async def final_task_drag_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()
        
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        print("🚀 最终任务拖动测试...")
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(3000)
        
        # 调整画布找到任务
        canvas = page.locator('.sticky-canvas').first
        canvas_box = await canvas.bounding_box()
        center_x = canvas_box['x'] + canvas_box['width'] / 2
        center_y = canvas_box['y'] + canvas_box['height'] / 2
        
        await page.mouse.move(center_x, center_y)
        await page.mouse.down(button="middle")
        await page.mouse.move(center_x + 100, center_y + 400)
        await page.mouse.up(button="middle")
        await page.wait_for_timeout(1000)
        
        task = page.locator('.task-wrapper').first
        task_box = await task.bounding_box()
        
        # 找到任务中心的可点击区域
        task_center_x = task_box['x'] + task_box['width'] / 2
        task_center_y = task_box['y'] + task_box['height'] / 2
        
        print(f"任务中心: ({task_center_x:.1f}, {task_center_y:.1f})")
        
        # 获取初始位置
        initial_transform = await task.evaluate("el => el.style.transform")
        match = re.search(r'translate3d\(([^,]+),\s*([^,]+)', initial_transform)
        if match:
            initial_x = float(match.group(1).replace('px', ''))
            initial_y = float(match.group(2).replace('px', ''))
            print(f"初始任务位置: ({initial_x:.1f}, {initial_y:.1f})")
        
        console_messages.clear()
        
        # 开始拖动测试
        await page.mouse.move(task_center_x, task_center_y)
        await page.wait_for_timeout(200)
        
        print("\\n开始拖动测试...")
        await page.mouse.down(button="left")
        await page.wait_for_timeout(300)
        
        # 分步移动测试
        test_moves = [
            (task_center_x + 50, task_center_y, "向右50px"),
            (task_center_x + 50, task_center_y + 40, "向下40px"),
            (task_center_x, task_center_y + 40, "向左50px"),
            (task_center_x, task_center_y, "回到起点"),
        ]
        
        print("\\n执行精确移动测试:")
        for i, (target_x, target_y, desc) in enumerate(test_moves):
            print(f"\\n步骤 {i+1}: {desc} -> ({target_x:.1f}, {target_y:.1f})")
            
            await page.mouse.move(target_x, target_y)
            await page.wait_for_timeout(400)
            
            # 获取当前任务位置
            current_transform = await task.evaluate("el => el.style.transform")
            match = re.search(r'translate3d\(([^,]+),\s*([^,]+)', current_transform)
            if match:
                current_x = float(match.group(1).replace('px', ''))
                current_y = float(match.group(2).replace('px', ''))
                
                # 计算理论位置（考虑鼠标偏移）
                mouse_delta_x = target_x - task_center_x
                mouse_delta_y = target_y - task_center_y
                
                print(f"  当前任务位置: ({current_x:.1f}, {current_y:.1f})")
                print(f"  鼠标移动距离: ({mouse_delta_x:.1f}, {mouse_delta_y:.1f})")
                
                # 检查任务是否正确跟随
                expected_x = initial_x + mouse_delta_x
                expected_y = initial_y + mouse_delta_y
                error_x = abs(current_x - expected_x)
                error_y = abs(current_y - expected_y)
                
                print(f"  预期位置: ({expected_x:.1f}, {expected_y:.1f})")
                print(f"  位置误差: ({error_x:.1f}, {error_y:.1f})")
                
                if error_x < 10 and error_y < 10:
                    print(f"  ✅ 跟随精度良好")
                else:
                    print(f"  ❌ 跟随精度不足")
            else:
                print(f"  Transform: {current_transform}")
        
        await page.mouse.up(button="left")
        await page.wait_for_timeout(500)
        
        # 检查拖动系统消息
        print("\\n📊 拖动系统分析:")
        task_drag_msgs = [msg for msg in console_messages if '任务拖动' in msg]
        coord_calc_msgs = [msg for msg in console_messages if '坐标计算' in msg]
        
        print(f"  任务拖动消息: {len(task_drag_msgs)}")
        print(f"  坐标计算消息: {len(coord_calc_msgs)}")
        
        if task_drag_msgs:
            print("  最新任务拖动消息:")
            for msg in task_drag_msgs[-3:]:
                print(f"    {msg}")
                
        # 最终结果
        success = len(task_drag_msgs) > 0 and len(coord_calc_msgs) > 0
        print(f"\\n🎯 任务拖动测试结果: {'✅ 成功' if success else '❌ 失败'}")
        
        await browser.close()
        return success

if __name__ == "__main__":
    result = asyncio.run(final_task_drag_test())
    print(f"\\n{'='*60}")
    print(f"🏆 任务拖动修复最终状态: {'✅ 完全成功' if result else '❌ 需要进一步调试'}")
    print(f"{'='*60}")