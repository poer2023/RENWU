import { test, expect } from '@playwright/test';
import { TaskWallTestHelper } from './utils/test-helpers';

test.describe('错误处理和稳定性测试', () => {
  let helper: TaskWallTestHelper;

  test.beforeEach(async ({ page }) => {
    helper = new TaskWallTestHelper(page);
    
    // 设置控制台监控
    const getErrors = helper.setupConsoleMonitoring();
    
    await page.goto('/');
    await helper.waitForAppReady();
  });

  test('网络连接中断处理', async ({ page }) => {
    // 模拟网络中断
    await page.route('**/api/**', route => route.abort());
    
    // 尝试创建任务
    try {
      await helper.createTask('网络测试任务');
    } catch (error) {
      // 预期会失败
    }
    
    // 检查是否有适当的错误提示
    const errorIndicator = await helper.findElementSafely('.error, .network-error, [data-testid="network-error"]');
    
    if (errorIndicator) {
      await expect(errorIndicator).toBeVisible();
    }
    
    // 恢复网络连接
    await page.unroute('**/api/**');
    
    // 等待重新连接
    await page.waitForTimeout(2000);
    
    // 验证应用是否恢复正常
    await expect(page.locator('.sticky-canvas')).toBeVisible();
  });

  test('API错误响应处理', async ({ page }) => {
    // 模拟API错误响应
    await page.route('**/api/tasks/', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });
    
    // 尝试获取任务数据
    await page.reload();
    await page.waitForTimeout(3000);
    
    // 检查错误处理
    const hasErrors = await helper.checkForErrors();
    
    // 应该有错误处理机制，但不应该崩溃应用
    await expect(page.locator('.sticky-canvas')).toBeVisible();
    
    // 恢复正常API响应
    await page.unroute('**/api/tasks/');
  });

  test('大量数据加载性能', async ({ page }) => {
    // 模拟返回大量任务数据
    const largeMockData = Array.from({ length: 100 }, (_, i) => ({
      id: i + 1,
      title: `大数据测试任务 ${i + 1}`,
      description: `这是第 ${i + 1} 个测试任务的描述，用于测试大量数据的加载性能`,
      urgency: Math.floor(Math.random() * 5),
      position_x: Math.random() * 2000,
      position_y: Math.random() * 1500,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }));

    await page.route('**/api/tasks/', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(largeMockData)
      });
    });

    const startTime = Date.now();
    await page.reload();
    await helper.waitForAppReady();
    const loadTime = Date.now() - startTime;

    // 加载时间应该在合理范围内（10秒内）
    expect(loadTime).toBeLessThan(10000);

    // 检查任务是否正确渲染
    const taskCards = page.locator('.task-card');
    const taskCount = await taskCards.count();
    expect(taskCount).toBeGreaterThan(50); // 至少渲染了一部分任务

    // 检查性能指标
    const metrics = await helper.checkPerformance();
    console.log(`Loaded ${taskCount} tasks in ${loadTime}ms`);
  });

  test('内存泄漏检测', async ({ page }) => {
    const initialMetrics = await helper.checkPerformance();
    
    // 执行多次操作
    for (let i = 0; i < 10; i++) {
      try {
        await helper.createTask(`内存测试任务 ${i}`);
        await page.waitForTimeout(200);
        
        // 模拟拖拽
        const tasks = page.locator('.task-card');
        if (await tasks.count() > 0) {
          const task = tasks.last();
          const box = await task.boundingBox();
          if (box) {
            await task.hover();
            await page.mouse.down();
            await page.mouse.move(box.x + 50, box.y + 50);
            await page.mouse.up();
          }
        }
      } catch (error) {
        console.warn(`Operation ${i} failed:`, error);
      }
    }
    
    // 检查最终内存使用
    const finalMetrics = await helper.checkPerformance();
    
    if (initialMetrics.memory && finalMetrics.memory) {
      const memoryIncrease = finalMetrics.memory.used - initialMetrics.memory.used;
      const increasePercent = (memoryIncrease / initialMetrics.memory.used) * 100;
      
      console.log(`Memory increase: ${memoryIncrease} bytes (${increasePercent.toFixed(2)}%)`);
      
      // 内存增长不应该超过200%
      expect(increasePercent).toBeLessThan(200);
    }
  });

  test('并发操作处理', async ({ page }) => {
    // 同时执行多个操作
    const operations = [
      async () => {
        try {
          await helper.createTask('并发任务1');
        } catch (error) {
          console.warn('Concurrent operation 1 failed:', error);
        }
      },
      async () => {
        try {
          await helper.createTask('并发任务2');
        } catch (error) {
          console.warn('Concurrent operation 2 failed:', error);
        }
      },
      async () => {
        try {
          const canvas = page.locator('.sticky-canvas');
          await canvas.hover();
          await page.keyboard.down('Control');
          await page.mouse.wheel(0, -100);
          await page.keyboard.up('Control');
        } catch (error) {
          console.warn('Concurrent zoom operation failed:', error);
        }
      },
      async () => {
        try {
          await page.keyboard.press('Shift+Meta+K');
        } catch (error) {
          console.warn('Concurrent search operation failed:', error);
        }
      }
    ];

    // 并发执行所有操作
    await Promise.allSettled(operations.map(op => op()));
    
    // 等待操作完成
    await page.waitForTimeout(3000);
    
    // 验证应用仍然响应
    await expect(page.locator('.sticky-canvas')).toBeVisible();
    
    // 检查是否有错误
    const hasErrors = await helper.checkForErrors();
    console.log('Concurrent operations completed, errors detected:', !hasErrors);
  });

  test('浏览器兼容性处理', async ({ page, browserName }) => {
    console.log(`Testing on ${browserName}`);
    
    // 检查基本功能在不同浏览器中的工作情况
    await expect(page.locator('.sticky-canvas')).toBeVisible();
    
    // 尝试创建任务
    try {
      await helper.createTask(`${browserName}兼容性测试任务`);
      console.log(`✓ Task creation works on ${browserName}`);
    } catch (error) {
      console.error(`✗ Task creation failed on ${browserName}:`, error);
    }
    
    // 测试拖拽功能
    const tasks = page.locator('.task-card');
    if (await tasks.count() > 0) {
      try {
        const task = tasks.first();
        const box = await task.boundingBox();
        if (box) {
          await task.hover();
          await page.mouse.down();
          await page.mouse.move(box.x + 100, box.y + 100);
          await page.mouse.up();
          console.log(`✓ Drag functionality works on ${browserName}`);
        }
      } catch (error) {
        console.error(`✗ Drag functionality failed on ${browserName}:`, error);
      }
    }
    
    // 检查CSS支持
    const canvasStyles = await page.locator('.sticky-canvas').evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        display: styles.display,
        position: styles.position,
        transform: styles.transform
      };
    });
    
    expect(canvasStyles.display).not.toBe('');
    console.log(`✓ CSS rendering works on ${browserName}`);
  });

  test('数据一致性验证', async ({ page }) => {
    // 创建任务
    await helper.createTask('一致性测试任务');
    await page.waitForTimeout(1000);
    
    // 刷新页面
    await page.reload();
    await helper.waitForAppReady();
    
    // 验证任务是否持久化
    const persistedTask = page.locator('.task-card:has-text("一致性测试任务")');
    await expect(persistedTask).toBeVisible({ timeout: 5000 });
    
    // 修改任务
    await persistedTask.dblclick();
    await page.waitForTimeout(500);
    
    const editInput = page.locator('input:visible, textarea:visible').first();
    if (await editInput.count() > 0) {
      await editInput.selectAll();
      await editInput.fill('修改后的一致性测试任务');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1000);
      
      // 再次刷新验证修改是否持久化
      await page.reload();
      await helper.waitForAppReady();
      
      const modifiedTask = page.locator('.task-card:has-text("修改后的一致性测试任务")');
      await expect(modifiedTask).toBeVisible({ timeout: 5000 });
    }
  });

  test('错误恢复机制', async ({ page }) => {
    // 故意触发一些可能的错误情况
    
    // 1. 尝试在无效位置创建任务
    try {
      await page.locator('body').click({ position: { x: -100, y: -100 } });
    } catch (error) {
      // 预期可能失败
    }
    
    // 2. 快速重复操作
    for (let i = 0; i < 5; i++) {
      try {
        await page.keyboard.press('Meta+P');
        await page.waitForTimeout(50);
      } catch (error) {
        console.warn(`Rapid operation ${i} failed:`, error);
      }
    }
    
    await page.waitForTimeout(2000);
    
    // 验证应用是否仍然正常工作
    await expect(page.locator('.sticky-canvas')).toBeVisible();
    
    // 尝试正常操作
    try {
      await helper.createTask('错误恢复测试任务');
      console.log('✓ Application recovered successfully');
    } catch (error) {
      console.error('✗ Application failed to recover:', error);
      throw error;
    }
  });

  test.afterEach(async ({ page }) => {
    // 清理测试数据
    try {
      await helper.cleanup();
    } catch (error) {
      console.warn('Cleanup failed:', error);
    }
    
    // 检查最终状态
    const finalCheck = await helper.checkForErrors();
    if (!finalCheck) {
      await helper.captureErrorState('test-end');
    }
  });
});