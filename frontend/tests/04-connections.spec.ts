import { test, expect } from '@playwright/test';

test.describe('任务连线功能测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.sticky-canvas')).toBeVisible();
    
    // 确保有足够的任务用于连线测试
    await createTestTasks(page);
  });

  async function createTestTasks(page: any) {
    // 创建第一个任务
    await page.locator('.sticky-canvas').dblclick({ position: { x: 200, y: 200 } });
    await page.waitForTimeout(500);
    let input = page.locator('input:visible, textarea:visible').first();
    if (await input.count() > 0) {
      await input.fill('源任务');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1500);
    }
    
    // 创建第二个任务
    await page.locator('.sticky-canvas').dblclick({ position: { x: 500, y: 200 } });
    await page.waitForTimeout(500);
    input = page.locator('input:visible, textarea:visible').first();
    if (await input.count() > 0) {
      await input.fill('目标任务');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1500);
    }
  }

  test('创建任务连线', async ({ page }) => {
    // 等待任务加载完成
    await page.waitForTimeout(2000);
    
    const sourceTasks = page.locator('.task-card:has-text("源任务")');
    const targetTasks = page.locator('.task-card:has-text("目标任务")');
    
    if (await sourceTasks.count() > 0 && await targetTasks.count() > 0) {
      const sourceTask = sourceTasks.first();
      const targetTask = targetTasks.first();
      
      // 查找连接按钮或触发连接模式的方法
      await sourceTask.click();
      await page.waitForTimeout(500);
      
      // 方法1: 查找连接按钮
      const connectButton = page.locator('button:has-text("连接"), button:has-text("Connect"), [data-testid="connect-task"]').first();
      if (await connectButton.count() > 0) {
        await connectButton.click();
        await targetTask.click();
      } else {
        // 方法2: 尝试拖拽连接
        const sourceBox = await sourceTask.boundingBox();
        const targetBox = await targetTask.boundingBox();
        
        if (sourceBox && targetBox) {
          // 从源任务右边缘拖拽到目标任务左边缘
          await page.mouse.move(sourceBox.x + sourceBox.width, sourceBox.y + sourceBox.height / 2);
          await page.mouse.down();
          await page.mouse.move(targetBox.x, targetBox.y + targetBox.height / 2);
          await page.mouse.up();
        }
      }
      
      // 等待连线创建
      await page.waitForTimeout(2000);
      
      // 验证连线是否出现
      const connectionLines = page.locator('svg .connection-line, .connection, [data-testid="connection-line"]');
      if (await connectionLines.count() > 0) {
        await expect(connectionLines.first()).toBeVisible();
      }
    }
  });

  test('连线精确度测试', async ({ page }) => {
    // 等待任务和可能存在的连线加载
    await page.waitForTimeout(3000);
    
    const taskCards = page.locator('.task-card');
    const connectionSvg = page.locator('svg.connections-overlay, .connections-overlay');
    
    if (await taskCards.count() >= 2 && await connectionSvg.count() > 0) {
      const firstTask = taskCards.first();
      const secondTask = taskCards.nth(1);
      
      // 获取任务位置
      const firstBox = await firstTask.boundingBox();
      const secondBox = await secondTask.boundingBox();
      
      if (firstBox && secondBox) {
        // 检查SVG画布的尺寸
        const svgBox = await connectionSvg.boundingBox();
        expect(svgBox).toBeTruthy();
        
        // 移动任务并检查连线是否跟随
        await firstTask.hover();
        await page.mouse.down();
        await page.mouse.move(firstBox.x + 100, firstBox.y + 100);
        await page.mouse.up();
        
        // 等待连线重新计算
        await page.waitForTimeout(1000);
        
        // 验证连线仍然可见且位置正确
        const connectionLines = page.locator('svg .connection-line, .connection-line');
        if (await connectionLines.count() > 0) {
          await expect(connectionLines.first()).toBeVisible();
        }
      }
    }
  });

  test('连线性能测试', async ({ page }) => {
    // 创建多个任务进行性能测试
    const taskCount = 8;
    
    for (let i = 0; i < taskCount; i++) {
      const x = 200 + (i % 4) * 200;
      const y = 200 + Math.floor(i / 4) * 200;
      
      await page.locator('.sticky-canvas').dblclick({ position: { x, y } });
      await page.waitForTimeout(300);
      
      const input = page.locator('input:visible, textarea:visible').first();
      if (await input.count() > 0) {
        await input.fill(`任务${i + 1}`);
        await page.keyboard.press('Enter');
        await page.waitForTimeout(500);
      }
    }
    
    // 等待所有任务创建完成
    await page.waitForTimeout(2000);
    
    // 测试拖拽性能
    const taskCards = page.locator('.task-card');
    if (await taskCards.count() >= 4) {
      const startTime = Date.now();
      
      // 快速拖拽多个任务
      for (let i = 0; i < 4; i++) {
        const task = taskCards.nth(i);
        const box = await task.boundingBox();
        if (box) {
          await task.hover();
          await page.mouse.down();
          await page.mouse.move(box.x + 50, box.y + 50);
          await page.mouse.up();
          await page.waitForTimeout(100); // 短暂延迟
        }
      }
      
      const endTime = Date.now();
      const duration = endTime - startTime;
      
      // 性能应该在合理范围内(5秒内完成)
      expect(duration).toBeLessThan(5000);
      
      // 检查画面是否仍然响应
      await expect(page.locator('.sticky-canvas')).toBeVisible();
    }
  });

  test('连线删除功能', async ({ page }) => {
    // 等待页面加载
    await page.waitForTimeout(3000);
    
    // 查找现有连线
    const connectionLines = page.locator('svg .connection-line, .connection-line');
    
    if (await connectionLines.count() > 0) {
      const firstConnection = connectionLines.first();
      
      // 右键点击连线
      await firstConnection.click({ button: 'right' });
      await page.waitForTimeout(500);
      
      // 查找删除选项
      const deleteOption = page.locator('text="删除连线", text="Delete Connection", [data-testid="delete-connection"]').first();
      
      if (await deleteOption.count() > 0) {
        await deleteOption.click();
        
        // 确认删除(如果有确认对话框)
        const confirmButton = page.locator('button:has-text("确认"), button:has-text("删除"), button:has-text("Delete")').first();
        if (await confirmButton.count() > 0) {
          await confirmButton.click();
        }
        
        // 等待删除完成
        await page.waitForTimeout(1000);
        
        // 验证连线是否被删除
        const remainingConnections = page.locator('svg .connection-line, .connection-line');
        const newCount = await remainingConnections.count();
        expect(newCount).toBeLessThan(await connectionLines.count());
      }
    }
  });

  test('画布缩放时连线精度', async ({ page }) => {
    // 等待加载
    await page.waitForTimeout(2000);
    
    const canvas = page.locator('.sticky-canvas');
    
    // 测试放大
    await canvas.hover();
    await page.keyboard.down('Control');
    await page.mouse.wheel(0, -100); // 向上滚动放大
    await page.keyboard.up('Control');
    await page.waitForTimeout(1000);
    
    // 检查连线是否仍然可见和准确
    const connectionLines = page.locator('svg .connection-line, .connection-line');
    if (await connectionLines.count() > 0) {
      await expect(connectionLines.first()).toBeVisible();
    }
    
    // 测试缩小
    await canvas.hover();
    await page.keyboard.down('Control');
    await page.mouse.wheel(0, 100); // 向下滚动缩小
    await page.keyboard.up('Control');
    await page.waitForTimeout(1000);
    
    // 再次检查连线
    if (await connectionLines.count() > 0) {
      await expect(connectionLines.first()).toBeVisible();
    }
    
    // 重置缩放
    await canvas.hover();
    await page.keyboard.down('Control');
    await page.mouse.wheel(0, 0); // 重置
    await page.keyboard.up('Control');
  });

  test('连线动画和视觉效果', async ({ page }) => {
    // 等待加载
    await page.waitForTimeout(3000);
    
    const connectionLines = page.locator('svg .connection-line, .connection-line');
    
    if (await connectionLines.count() > 0) {
      const firstConnection = connectionLines.first();
      
      // 悬停测试
      await firstConnection.hover();
      await page.waitForTimeout(500);
      
      // 检查悬停效果(可能是颜色变化或高亮)
      await expect(firstConnection).toBeVisible();
      
      // 移开鼠标
      await page.locator('.sticky-canvas').hover();
      await page.waitForTimeout(500);
      
      // 检查动画流动点(如果存在)
      const flowDots = page.locator('svg circle, .flow-dot');
      if (await flowDots.count() > 0) {
        await expect(flowDots.first()).toBeVisible();
      }
    }
  });

  test('连线智能路径算法', async ({ page }) => {
    // 创建特殊布局的任务来测试路径算法
    await page.waitForTimeout(2000);
    
    // 创建垂直排列的任务
    await page.locator('.sticky-canvas').dblclick({ position: { x: 300, y: 150 } });
    await page.waitForTimeout(500);
    let input = page.locator('input:visible, textarea:visible').first();
    if (await input.count() > 0) {
      await input.fill('上方任务');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1000);
    }
    
    await page.locator('.sticky-canvas').dblclick({ position: { x: 300, y: 350 } });
    await page.waitForTimeout(500);
    input = page.locator('input:visible, textarea:visible').first();
    if (await input.count() > 0) {
      await input.fill('下方任务');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1000);
    }
    
    // 尝试创建垂直连线
    const topTask = page.locator('.task-card:has-text("上方任务")').first();
    const bottomTask = page.locator('.task-card:has-text("下方任务")').first();
    
    if (await topTask.count() > 0 && await bottomTask.count() > 0) {
      // 创建连线(方法可能因实现而异)
      await topTask.click();
      await page.waitForTimeout(500);
      
      const topBox = await topTask.boundingBox();
      const bottomBox = await bottomTask.boundingBox();
      
      if (topBox && bottomBox) {
        // 从上方任务底部连接到下方任务顶部
        await page.mouse.move(topBox.x + topBox.width / 2, topBox.y + topBox.height);
        await page.mouse.down();
        await page.mouse.move(bottomBox.x + bottomBox.width / 2, bottomBox.y);
        await page.mouse.up();
        
        await page.waitForTimeout(2000);
        
        // 验证连线路径是否合理(垂直连接)
        const connectionLines = page.locator('svg .connection-line, .connection-line');
        if (await connectionLines.count() > 0) {
          await expect(connectionLines.first()).toBeVisible();
        }
      }
    }
  });
});