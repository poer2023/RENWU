#!/usr/bin/env python3
"""
测试拖动修复效果 - 检测漂移问题是否解决
"""
import asyncio
from playwright.async_api import async_playwright
import json
import time

async def test_drag_precision():
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
        
        print("📋 查找画布容器...")
        canvas = page.locator('.sticky-canvas').first
        if not await canvas.is_visible():
            print("❌ 画布容器未找到")
            await browser.close()
            return False
            
        print("✅ 画布容器已找到")
        
        # 获取画布位置
        box = await canvas.bounding_box()
        center_x = box['x'] + box['width'] / 2
        center_y = box['y'] + box['height'] / 2
        
        print(f"🎯 测试中键拖动精度，起始位置: ({center_x:.1f}, {center_y:.1f})")
        
        # 清空控制台消息
        console_messages.clear()
        
        # === 测试1: 中键拖动画布 ===
        print("\n=== 测试1: 中键拖动画布 ===")
        
        # 获取初始视口位置
        initial_viewport = await page.evaluate("""
            () => {
                const canvas = document.querySelector('.sticky-canvas .canvas-content');
                if (canvas) {
                    const transform = canvas.style.transform;
                    const match = transform.match(/translate3d\\(([^,]+),\\s*([^,]+),/);
                    if (match) {
                        return {
                            x: parseFloat(match[1]),
                            y: parseFloat(match[2])
                        };
                    }
                }
                return { x: 0, y: 0 };
            }
        """)
        
        print(f"初始视口位置: {initial_viewport}")
        
        # 中键拖动
        await page.mouse.move(center_x, center_y)
        await page.mouse.down(button="middle")
        
        # 精确拖动100像素
        target_x = center_x + 100
        target_y = center_y + 50
        
        await page.mouse.move(target_x, target_y)
        await page.wait_for_timeout(100)
        await page.mouse.up(button="middle")
        
        # 获取最终视口位置
        final_viewport = await page.evaluate("""
            () => {
                const canvas = document.querySelector('.sticky-canvas .canvas-content');
                if (canvas) {
                    const transform = canvas.style.transform;
                    const match = transform.match(/translate3d\\(([^,]+),\\s*([^,]+),/);
                    if (match) {
                        return {
                            x: parseFloat(match[1]),
                            y: parseFloat(match[2])
                        };
                    }
                }
                return { x: 0, y: 0 };
            }
        """)
        
        print(f"最终视口位置: {final_viewport}")
        
        # 计算实际位移
        actual_delta_x = final_viewport['x'] - initial_viewport['x']
        actual_delta_y = final_viewport['y'] - initial_viewport['y']
        
        print(f"预期位移: (100, 50)")
        print(f"实际位移: ({actual_delta_x:.1f}, {actual_delta_y:.1f})")
        
        # 检查漂移误差（应该在合理范围内）
        error_x = abs(actual_delta_x - 100)
        error_y = abs(actual_delta_y - 50)
        
        canvas_drag_success = error_x < 10 and error_y < 10  # 允许10像素误差
        
        print(f"X轴误差: {error_x:.1f}px, Y轴误差: {error_y:.1f}px")
        print(f"画布拖动精度: {'✅ 通过' if canvas_drag_success else '❌ 失败'}")
        
        # === 测试2: 查找并拖动任务卡片 ===
        print("\n=== 测试2: 左键拖动任务卡片 ===")
        
        # 查找第一个任务卡片
        task_card = page.locator('.task-wrapper').first
        if await task_card.is_visible():
            task_box = await task_card.bounding_box()
            task_x = task_box['x'] + task_box['width'] / 2
            task_y = task_box['y'] + task_box['height'] / 2
            
            print(f"找到任务卡片，位置: ({task_x:.1f}, {task_y:.1f})")
            
            # 获取任务初始位置
            initial_task_pos = await page.evaluate("""
                () => {
                    const task = document.querySelector('.task-wrapper');
                    if (task) {
                        const transform = task.style.transform;
                        const match = transform.match(/translate3d\\(([^,]+),\\s*([^,]+),/);
                        if (match) {
                            return {
                                x: parseFloat(match[1]),
                                y: parseFloat(match[2])
                            };
                        }
                    }
                    return { x: 0, y: 0 };
                }
            """)
            
            print(f"任务初始位置: {initial_task_pos}")
            
            # 左键拖动任务
            await page.mouse.move(task_x, task_y)
            await page.mouse.down(button="left")
            
            # 拖动50像素
            await page.mouse.move(task_x + 50, task_y + 30)
            await page.wait_for_timeout(100)
            await page.mouse.up(button="left")
            
            # 获取任务最终位置
            final_task_pos = await page.evaluate("""
                () => {
                    const task = document.querySelector('.task-wrapper');
                    if (task) {
                        const transform = task.style.transform;
                        const match = transform.match(/translate3d\\(([^,]+),\\s*([^,]+),/);
                        if (match) {
                            return {
                                x: parseFloat(match[1]),
                                y: parseFloat(match[2])
                            };
                        }
                    }
                    return { x: 0, y: 0 };
                }
            """)
            
            print(f"任务最终位置: {final_task_pos}")
            
            # 计算任务位移
            task_delta_x = final_task_pos['x'] - initial_task_pos['x']
            task_delta_y = final_task_pos['y'] - initial_task_pos['y']
            
            print(f"任务预期位移: (50, 30)")
            print(f"任务实际位移: ({task_delta_x:.1f}, {task_delta_y:.1f})")
            
            # 检查任务拖动精度
            task_error_x = abs(task_delta_x - 50)
            task_error_y = abs(task_delta_y - 30)
            
            task_drag_success = task_error_x < 10 and task_error_y < 10
            
            print(f"任务X轴误差: {task_error_x:.1f}px, Y轴误差: {task_error_y:.1f}px")
            print(f"任务拖动精度: {'✅ 通过' if task_drag_success else '❌ 失败'}")
        else:
            print("⚠️ 未找到任务卡片，跳过任务拖动测试")
            task_drag_success = True
        
        # 等待一下查看控制台消息
        await page.wait_for_timeout(500)
        
        print("\n📊 相关控制台消息:")
        drag_messages = [msg for msg in console_messages if any(keyword in msg.lower() for keyword in ['drag', '拖动', 'unified', 'pan', '平移'])]
        for msg in drag_messages[-10:]:  # 显示最后10条相关消息
            print(f"  {msg}")
        
        await browser.close()
        
        # 综合结果
        overall_success = canvas_drag_success and task_drag_success
        
        print(f"\n🎯 总体测试结果: {'✅ 成功' if overall_success else '❌ 失败'}")
        print(f"   - 画布拖动: {'✅' if canvas_drag_success else '❌'}")
        print(f"   - 任务拖动: {'✅' if task_drag_success else '❌'}")
        
        return overall_success

if __name__ == "__main__":
    result = asyncio.run(test_drag_precision())
    print(f"\n最终结果: {'修复成功' if result else '仍需调试'}")