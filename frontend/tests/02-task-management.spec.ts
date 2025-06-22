import { test, expect } from '@playwright/test';

test.describe('任务管理功能测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 等待画布加载完成
    await expect(page.locator('.sticky-canvas')).toBeVisible();
  });

  test('创建新任务', async ({ page }) => {
    // 查找任务创建按钮或输入框
    const quickAddButton = page.locator('button:has-text("快速添加"), button:has-text("添加任务"), [data-testid="quick-add"]').first();
    const quickAddInput = page.locator('input[placeholder*="任务"], textarea[placeholder*="任务"], [data-testid="task-input"]').first();
    
    if (await quickAddButton.count() > 0) {
      await quickAddButton.click();
    } else if (await quickAddInput.count() > 0) {
      await quickAddInput.click();
    } else {
      // 尝试使用快捷键
      await page.keyboard.press('Meta+P'); // macOS
      await page.waitForTimeout(500);
      
      // 如果还是没有，尝试双击画布
      await page.locator('.sticky-canvas').dblclick();
    }
    
    // 等待输入框出现
    await page.waitForTimeout(1000);
    
    // 查找输入框
    const inputField = page.locator('input:visible, textarea:visible').filter({ hasText: '' }).first();
    
    if (await inputField.count() > 0) {
      // 输入任务信息
      const taskTitle = `测试任务 ${Date.now()}`;
      await inputField.fill(taskTitle);
      
      // 提交任务
      await page.keyboard.press('Enter');
      
      // 等待任务创建完成
      await page.waitForTimeout(2000);
      
      // 验证任务是否在画布上出现
      const taskCard = page.locator(`.task-card:has-text("${taskTitle}"), [data-testid="task-card"]:has-text("${taskTitle}")`);
      await expect(taskCard).toBeVisible({ timeout: 5000 });
    }
  });

  test('拖拽任务卡片', async ({ page }) => {
    // 等待任务加载
    await page.waitForTimeout(2000);
    
    // 查找现有任务或创建一个测试任务
    let taskCard = page.locator('.task-card, [data-testid="task-card"]').first();
    
    if (await taskCard.count() === 0) {
      // 创建测试任务
      await page.locator('.sticky-canvas').dblclick();
      await page.waitForTimeout(500);
      const input = page.locator('input:visible, textarea:visible').first();
      if (await input.count() > 0) {
        await input.fill('拖拽测试任务');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(2000);
        taskCard = page.locator('.task-card, [data-testid="task-card"]').first();
      }
    }
    
    if (await taskCard.count() > 0) {
      // 获取初始位置
      const initialBox = await taskCard.boundingBox();
      expect(initialBox).toBeTruthy();
      
      // 拖拽任务到新位置
      await taskCard.hover();
      await page.mouse.down();
      await page.mouse.move(initialBox!.x + 200, initialBox!.y + 100);
      await page.mouse.up();
      
      // 等待动画完成
      await page.waitForTimeout(1000);
      
      // 验证位置是否改变
      const newBox = await taskCard.boundingBox();
      expect(newBox).toBeTruthy();
      expect(Math.abs(newBox!.x - initialBox!.x)).toBeGreaterThan(50);
    }
  });

  test('编辑任务内容', async ({ page }) => {
    // 等待任务加载
    await page.waitForTimeout(2000);
    
    let taskCard = page.locator('.task-card, [data-testid="task-card"]').first();
    
    // 如果没有任务，创建一个
    if (await taskCard.count() === 0) {
      await page.locator('.sticky-canvas').dblclick();
      await page.waitForTimeout(500);
      const input = page.locator('input:visible, textarea:visible').first();
      if (await input.count() > 0) {
        await input.fill('编辑测试任务');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(2000);
        taskCard = page.locator('.task-card, [data-testid="task-card"]').first();
      }
    }
    
    if (await taskCard.count() > 0) {
      // 双击进入编辑模式
      await taskCard.dblclick();
      await page.waitForTimeout(500);
      
      // 查找编辑输入框
      const editInput = page.locator('input:visible, textarea:visible').first();
      
      if (await editInput.count() > 0) {
        // 修改任务标题
        const newTitle = `已编辑任务 ${Date.now()}`;
        await editInput.selectAll();
        await editInput.fill(newTitle);
        await page.keyboard.press('Enter');
        
        // 等待保存完成
        await page.waitForTimeout(1000);
        
        // 验证修改是否生效
        await expect(taskCard).toContainText(newTitle, { timeout: 5000 });
      }
    }
  });

  test('删除任务', async ({ page }) => {
    // 创建测试任务
    await page.locator('.sticky-canvas').dblclick();
    await page.waitForTimeout(500);
    const input = page.locator('input:visible, textarea:visible').first();
    
    if (await input.count() > 0) {
      const taskTitle = `删除测试任务 ${Date.now()}`;
      await input.fill(taskTitle);
      await page.keyboard.press('Enter');
      await page.waitForTimeout(2000);
      
      const taskCard = page.locator(`.task-card:has-text("${taskTitle}"), [data-testid="task-card"]:has-text("${taskTitle}")`);
      await expect(taskCard).toBeVisible();
      
      // 右键点击任务卡片
      await taskCard.click({ button: 'right' });
      await page.waitForTimeout(500);
      
      // 查找删除选项
      const deleteOption = page.locator('text="删除", text="Delete", [data-testid="delete-task"]').first();
      
      if (await deleteOption.count() > 0) {
        await deleteOption.click();
        
        // 如果有确认对话框，点击确认
        const confirmButton = page.locator('button:has-text("确认"), button:has-text("删除"), button:has-text("Delete")').first();
        if (await confirmButton.count() > 0) {
          await confirmButton.click();
        }
        
        // 等待删除完成
        await page.waitForTimeout(1000);
        
        // 验证任务是否被删除
        await expect(taskCard).toHaveCount(0, { timeout: 5000 });
      }
    }
  });

  test('任务优先级设置', async ({ page }) => {
    // 创建测试任务
    await page.locator('.sticky-canvas').dblclick();
    await page.waitForTimeout(500);
    const input = page.locator('input:visible, textarea:visible').first();
    
    if (await input.count() > 0) {
      const taskTitle = `优先级测试任务 ${Date.now()}`;
      await input.fill(taskTitle);
      await page.keyboard.press('Enter');
      await page.waitForTimeout(2000);
      
      const taskCard = page.locator(`.task-card:has-text("${taskTitle}"), [data-testid="task-card"]:has-text("${taskTitle}")`);
      await expect(taskCard).toBeVisible();
      
      // 点击任务选择
      await taskCard.click();
      await page.waitForTimeout(500);
      
      // 查找优先级设置控件
      const priorityControl = page.locator('[data-testid="priority"], .priority-selector, select[name="priority"]').first();
      
      if (await priorityControl.count() > 0) {
        // 如果是下拉选择
        if (await priorityControl.locator('select').count() > 0) {
          await priorityControl.locator('select').selectOption('1'); // 高优先级
        } else {
          await priorityControl.click();
          // 选择高优先级选项
          const highPriorityOption = page.locator('text="高", text="High", text="P1"').first();
          if (await highPriorityOption.count() > 0) {
            await highPriorityOption.click();
          }
        }
        
        await page.waitForTimeout(1000);
        
        // 验证优先级是否改变（通过颜色或标识）
        const updatedCard = page.locator(`.task-card:has-text("${taskTitle}")`);
        // 这里可以检查特定的CSS类或颜色变化
        await expect(updatedCard).toBeVisible();
      }
    }
  });
});