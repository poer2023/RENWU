import { Page, expect } from '@playwright/test';

export class TaskWallTestHelper {
  constructor(private page: Page) {}

  /**
   * 等待应用初始化完成
   */
  async waitForAppReady() {
    await this.page.waitForLoadState('networkidle');
    await expect(this.page.locator('.sticky-canvas')).toBeVisible({ timeout: 10000 });
    await this.page.waitForTimeout(1000); // 额外等待动画完成
  }

  /**
   * 创建测试任务
   */
  async createTask(title: string, position?: { x: number; y: number }) {
    const pos = position || { x: 200 + Math.random() * 400, y: 200 + Math.random() * 300 };
    
    await this.page.locator('.sticky-canvas').dblclick({ position: pos });
    await this.page.waitForTimeout(500);
    
    const input = this.page.locator('input:visible, textarea:visible').first();
    if (await input.count() > 0) {
      await input.fill(title);
      await this.page.keyboard.press('Enter');
      await this.page.waitForTimeout(1500);
      
      // 验证任务是否创建成功
      const taskCard = this.page.locator(`.task-card:has-text("${title}")`);
      await expect(taskCard).toBeVisible({ timeout: 5000 });
      return taskCard;
    }
    
    throw new Error('Could not find input field to create task');
  }

  /**
   * 安全地查找元素，带重试机制
   */
  async findElementSafely(selector: string, timeout: number = 5000) {
    try {
      const element = this.page.locator(selector);
      await expect(element).toBeVisible({ timeout });
      return element;
    } catch (error) {
      console.warn(`Element not found: ${selector}`);
      return null;
    }
  }

  /**
   * 尝试多种方式触发功能
   */
  async tryMultipleTriggers(triggers: Array<() => Promise<void>>) {
    for (const trigger of triggers) {
      try {
        await trigger();
        await this.page.waitForTimeout(1000);
        return true;
      } catch (error) {
        console.warn('Trigger failed, trying next:', error);
        continue;
      }
    }
    return false;
  }

  /**
   * 等待网络请求完成
   */
  async waitForApiRequests() {
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForTimeout(500);
  }

  /**
   * 检查是否有错误消息
   */
  async checkForErrors() {
    const errorElements = this.page.locator('.error, .alert-error, [role="alert"]');
    const errorCount = await errorElements.count();
    
    if (errorCount > 0) {
      const errorTexts = await errorElements.allTextContents();
      console.warn('Found error messages:', errorTexts);
    }
    
    return errorCount === 0;
  }

  /**
   * 清理测试数据
   */
  async cleanup() {
    // 尝试删除测试创建的任务
    const testTasks = this.page.locator('.task-card:has-text("测试"), .task-card:has-text("Test")');
    const count = await testTasks.count();
    
    for (let i = 0; i < count; i++) {
      const task = testTasks.nth(i);
      try {
        await task.click({ button: 'right' });
        await this.page.waitForTimeout(500);
        
        const deleteOption = this.page.locator('text="删除", text="Delete"').first();
        if (await deleteOption.count() > 0) {
          await deleteOption.click();
          
          const confirmButton = this.page.locator('button:has-text("确认"), button:has-text("删除")').first();
          if (await confirmButton.count() > 0) {
            await confirmButton.click();
          }
          
          await this.page.waitForTimeout(500);
        }
      } catch (error) {
        console.warn('Failed to delete test task:', error);
      }
    }
  }

  /**
   * 截取错误时的屏幕截图
   */
  async captureErrorState(testName: string) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `error-${testName}-${timestamp}.png`;
    
    await this.page.screenshot({ 
      path: `test-results/${filename}`, 
      fullPage: true 
    });
    
    console.log(`Error screenshot saved: ${filename}`);
  }

  /**
   * 模拟用户真实操作延迟
   */
  async humanDelay(min: number = 100, max: number = 300) {
    const delay = Math.random() * (max - min) + min;
    await this.page.waitForTimeout(delay);
  }

  /**
   * 检查性能指标
   */
  async checkPerformance() {
    const metrics = await this.page.evaluate(() => {
      return {
        loadTime: performance.now(),
        memory: (performance as any).memory ? {
          used: (performance as any).memory.usedJSHeapSize,
          total: (performance as any).memory.totalJSHeapSize
        } : null,
        connectionMetrics: (window as any).taskConnectionsDebug ? 
          (window as any).taskConnectionsDebug.getPerformanceMetrics() : null
      };
    });

    console.log('Performance metrics:', metrics);
    return metrics;
  }

  /**
   * 验证响应式设计
   */
  async testResponsive() {
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop Large' },
      { width: 1366, height: 768, name: 'Desktop Medium' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' }
    ];

    for (const viewport of viewports) {
      await this.page.setViewportSize(viewport);
      await this.page.waitForTimeout(1000);
      
      // 检查关键元素是否仍然可见
      await expect(this.page.locator('.sticky-canvas')).toBeVisible();
      
      console.log(`✓ ${viewport.name} (${viewport.width}x${viewport.height}) - OK`);
    }

    // 恢复默认视图
    await this.page.setViewportSize({ width: 1200, height: 800 });
  }

  /**
   * 检查辅助功能
   */
  async checkAccessibility() {
    // 检查键盘导航
    await this.page.keyboard.press('Tab');
    await this.page.waitForTimeout(500);
    
    // 检查焦点是否可见
    const focusedElement = this.page.locator(':focus');
    if (await focusedElement.count() > 0) {
      console.log('✓ Keyboard navigation working');
    }

    // 检查ARIA标签
    const ariaElements = this.page.locator('[aria-label], [aria-describedby], [role]');
    const ariaCount = await ariaElements.count();
    console.log(`Found ${ariaCount} accessibility elements`);

    return ariaCount > 0;
  }

  /**
   * 监控控制台错误
   */
  setupConsoleMonitoring() {
    const errors: string[] = [];
    
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
        console.error('Console Error:', msg.text());
      }
    });

    this.page.on('pageerror', error => {
      errors.push(error.message);
      console.error('Page Error:', error.message);
    });

    return () => errors;
  }
}

/**
 * 智能等待策略
 */
export async function smartWait(page: Page, condition: () => Promise<boolean>, timeout: number = 5000) {
  const start = Date.now();
  
  while (Date.now() - start < timeout) {
    try {
      if (await condition()) {
        return true;
      }
    } catch (error) {
      // 继续等待
    }
    
    await page.waitForTimeout(100);
  }
  
  return false;
}

/**
 * 批量创建测试数据
 */
export async function createTestData(helper: TaskWallTestHelper, count: number = 5) {
  const tasks = [];
  
  for (let i = 0; i < count; i++) {
    try {
      const task = await helper.createTask(`测试任务 ${i + 1}`, {
        x: 200 + (i % 3) * 250,
        y: 200 + Math.floor(i / 3) * 150
      });
      tasks.push(task);
    } catch (error) {
      console.warn(`Failed to create test task ${i + 1}:`, error);
    }
  }
  
  return tasks;
}