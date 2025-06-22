#!/usr/bin/env python3
"""
调试DOM结构和事件目标
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_dom_structure():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(3000)
        
        # 获取任务元素的详细信息
        task_wrapper = page.locator('.task-wrapper').first
        if await task_wrapper.is_visible():
            # 获取HTML结构
            html = await task_wrapper.inner_html()
            print("任务元素HTML结构:")
            print(html[:500] + "..." if len(html) > 500 else html)
            
            # 获取所有子元素的class
            child_classes = await task_wrapper.evaluate("""
                el => {
                    const children = Array.from(el.querySelectorAll('*'));
                    return children.map(child => ({
                        tagName: child.tagName,
                        className: child.className,
                        id: child.id
                    }));
                }
            """)
            
            print("\\n子元素列表:")
            for i, child in enumerate(child_classes[:10]):  # 只显示前10个
                print(f"  {i+1}. {child['tagName']} class='{child['className']}' id='{child['id']}'")
                
            # 测试点击不同位置
            task_box = await task_wrapper.bounding_box()
            test_points = [
                (task_box['x'] + 10, task_box['y'] + 10, "左上角"),
                (task_box['x'] + task_box['width']/2, task_box['y'] + task_box['height']/2, "中心"),
                (task_box['x'] + task_box['width'] - 10, task_box['y'] + task_box['height'] - 10, "右下角")
            ]
            
            print("\\n测试点击不同位置:")
            for x, y, desc in test_points:
                # 获取该位置的元素
                element_info = await page.evaluate(f"""
                    () => {{
                        const el = document.elementFromPoint({x}, {y});
                        if (!el) return null;
                        
                        const taskWrapper = el.closest('.task-wrapper');
                        return {{
                            tagName: el.tagName,
                            className: el.className,
                            id: el.id,
                            hasTaskWrapper: !!taskWrapper,
                            taskWrapperDataId: taskWrapper ? taskWrapper.dataset.taskId : null
                        }};
                    }}
                """)
                
                print(f"  {desc} ({x:.1f}, {y:.1f}): {element_info}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_dom_structure())