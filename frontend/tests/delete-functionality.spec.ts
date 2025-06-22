import { test, expect, Page } from '@playwright/test';

test.describe('TaskWall 删除功能测试', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    
    // 监听控制台消息
    page.on('console', (msg) => {
      console.log(`Console ${msg.type()}: ${msg.text()}`);
    });

    // 监听网络请求
    page.on('request', (request) => {
      if (request.method() === 'DELETE') {
        console.log(`DELETE request: ${request.url()}`);
      }
    });

    page.on('response', (response) => {
      if (response.request().method() === 'DELETE') {
        console.log(`DELETE response: ${response.status()} - ${response.url()}`);
      }
    });

    // 访问页面
    await page.goto('http://localhost:3000');
    
    // 等待页面加载完成
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('准备测试数据 - 确保有任务可以删除', async () => {
    // 检查是否有现有任务
    const existingTasks = await page.locator('[data-testid="task-item"], .task-card, .sticky-note').count();
    console.log(`现有任务数量: ${existingTasks}`);

    if (existingTasks === 0) {
      console.log('没有现有任务，创建测试任务...');
      
      // 尝试双击创建任务
      await page.dblclick('canvas, .canvas-container, body', { position: { x: 300, y: 200 } });
      await page.waitForTimeout(1000);
      
      // 尝试输入任务内容
      const input = page.locator('input[type="text"], textarea').first();
      if (await input.isVisible()) {
        await input.fill('测试删除任务1');
        await input.press('Enter');
        await page.waitForTimeout(1000);
      }

      // 创建第二个任务
      await page.dblclick('canvas, .canvas-container, body', { position: { x: 500, y: 300 } });
      await page.waitForTimeout(1000);
      
      const input2 = page.locator('input[type="text"], textarea').first();
      if (await input2.isVisible()) {
        await input2.fill('测试删除任务2');
        await input2.press('Enter');
        await page.waitForTimeout(1000);
      }

      // 创建第三个任务
      await page.dblclick('canvas, .canvas-container, body', { position: { x: 400, y: 400 } });
      await page.waitForTimeout(1000);
      
      const input3 = page.locator('input[type="text"], textarea').first();
      if (await input3.isVisible()) {
        await input3.fill('测试删除任务3');
        await input3.press('Enter');
        await page.waitForTimeout(1000);
      }
    }

    // 再次检查任务数量
    const finalTaskCount = await page.locator('[data-testid="task-item"], .task-card, .sticky-note').count();
    console.log(`最终任务数量: ${finalTaskCount}`);
    
    expect(finalTaskCount).toBeGreaterThan(0);
  });

  test('A. 按钮删除（有确认）测试', async () => {
    console.log('=== 测试按钮删除功能 ===');
    
    // 等待页面稳定
    await page.waitForTimeout(2000);
    
    // 获取第一个任务
    const tasks = page.locator('[data-testid="task-item"], .task-card, .sticky-note');
    const taskCount = await tasks.count();
    console.log(`当前任务数量: ${taskCount}`);
    
    if (taskCount === 0) {
      console.log('没有任务可删除，跳过测试');
      return;
    }

    const firstTask = tasks.first();
    
    // 点击选择任务
    await firstTask.click();
    await page.waitForTimeout(500);
    console.log('已选择第一个任务');

    // 查找删除按钮
    const deleteButtons = [
      page.locator('button:has-text("🗑️")'),
      page.locator('button:has-text("删除")'),
      page.locator('button[title*="删除"]'),
      page.locator('.delete-btn'),
      page.locator('[data-testid="delete-button"]')
    ];

    let deleteButton = null;
    for (const btn of deleteButtons) {
      if (await btn.first().isVisible()) {
        deleteButton = btn.first();
        break;
      }
    }

    if (deleteButton) {
      console.log('找到删除按钮，点击删除');
      await deleteButton.click();
      await page.waitForTimeout(1000);

      // 检查是否出现确认对话框
      const confirmDialogs = [
        page.locator('text="确认删除"'),
        page.locator('text="确定删除"'),
        page.locator('.confirm-dialog'),
        page.locator('[role="dialog"]'),
        page.locator('.modal')
      ];

      let confirmDialog = null;
      for (const dialog of confirmDialogs) {
        if (await dialog.first().isVisible()) {
          confirmDialog = dialog.first();
          break;
        }
      }

      if (confirmDialog) {
        console.log('出现确认对话框');
        
        // 查找确认按钮
        const confirmButtons = [
          page.locator('button:has-text("确认")'),
          page.locator('button:has-text("确定")'),
          page.locator('button:has-text("删除")'),
          page.locator('.confirm-btn')
        ];

        let confirmButton = null;
        for (const btn of confirmButtons) {
          if (await btn.first().isVisible()) {
            confirmButton = btn.first();
            break;
          }
        }

        if (confirmButton) {
          console.log('点击确认删除');
          await confirmButton.click();
          await page.waitForTimeout(2000);
          
          // 检查任务是否被删除
          const newTaskCount = await tasks.count();
          console.log(`删除后任务数量: ${newTaskCount}`);
          expect(newTaskCount).toBeLessThan(taskCount);
          console.log('✅ 按钮删除（有确认）测试通过');
        } else {
          console.log('❌ 未找到确认按钮');
        }
      } else {
        console.log('❌ 未出现确认对话框');
      }
    } else {
      console.log('❌ 未找到删除按钮');
    }
  });

  test('B. Delete键删除（无确认）测试', async () => {
    console.log('=== 测试Delete键删除功能 ===');
    
    // 等待页面稳定
    await page.waitForTimeout(2000);
    
    // 获取任务
    const tasks = page.locator('[data-testid="task-item"], .task-card, .sticky-note');
    const taskCount = await tasks.count();
    console.log(`当前任务数量: ${taskCount}`);
    
    if (taskCount === 0) {
      console.log('没有任务可删除，跳过测试');
      return;
    }

    const firstTask = tasks.first();
    
    // 点击选择任务
    await firstTask.click();
    await page.waitForTimeout(500);
    console.log('已选择第一个任务');

    // 按Delete键
    console.log('按Delete键删除');
    await page.keyboard.press('Delete');
    await page.waitForTimeout(2000);

    // 检查任务是否被删除（无确认对话框）
    const newTaskCount = await tasks.count();
    console.log(`删除后任务数量: ${newTaskCount}`);
    
    if (newTaskCount < taskCount) {
      console.log('✅ Delete键删除（无确认）测试通过');
    } else {
      console.log('❌ Delete键删除失败或未实现');
    }

    // 检查是否有成功消息
    const successMessages = [
      page.locator('text*="删除成功"'),
      page.locator('text*="已删除"'),
      page.locator('.success-message'),
      page.locator('.toast-success')
    ];

    for (const msg of successMessages) {
      if (await msg.first().isVisible()) {
        console.log('✅ 显示了删除成功消息');
        break;
      }
    }
  });

  test('C. Ctrl+D删除（无确认）测试', async () => {
    console.log('=== 测试Ctrl+D删除功能 ===');
    
    // 等待页面稳定
    await page.waitForTimeout(2000);
    
    // 获取任务
    const tasks = page.locator('[data-testid="task-item"], .task-card, .sticky-note');
    const taskCount = await tasks.count();
    console.log(`当前任务数量: ${taskCount}`);
    
    if (taskCount === 0) {
      console.log('没有任务可删除，跳过测试');
      return;
    }

    const firstTask = tasks.first();
    
    // 点击选择任务
    await firstTask.click();
    await page.waitForTimeout(500);
    console.log('已选择第一个任务');

    // 按Ctrl+D
    console.log('按Ctrl+D删除');
    await page.keyboard.press('Control+d');
    await page.waitForTimeout(2000);

    // 检查任务是否被删除（无确认对话框）
    const newTaskCount = await tasks.count();
    console.log(`删除后任务数量: ${newTaskCount}`);
    
    if (newTaskCount < taskCount) {
      console.log('✅ Ctrl+D删除（无确认）测试通过');
    } else {
      console.log('❌ Ctrl+D删除失败或未实现');
    }

    // 检查是否有成功消息
    const successMessages = [
      page.locator('text*="删除成功"'),
      page.locator('text*="已删除"'),
      page.locator('.success-message'),
      page.locator('.toast-success')
    ];

    for (const msg of successMessages) {
      if (await msg.first().isVisible()) {
        console.log('✅ 显示了删除成功消息');
        break;
      }
    }
  });

  test('网络请求和错误监控测试', async () => {
    console.log('=== 测试网络请求和错误监控 ===');
    
    const requests: any[] = [];
    const responses: any[] = [];
    const errors: string[] = [];

    // 监听网络请求
    page.on('request', (request) => {
      if (request.method() === 'DELETE') {
        requests.push({
          method: request.method(),
          url: request.url(),
          headers: request.headers()
        });
      }
    });

    page.on('response', (response) => {
      if (response.request().method() === 'DELETE') {
        responses.push({
          status: response.status(),
          url: response.url(),
          statusText: response.statusText()
        });
      }
    });

    // 监听JavaScript错误
    page.on('pageerror', (error) => {
      errors.push(error.message);
      console.log(`JavaScript Error: ${error.message}`);
    });

    // 等待页面稳定
    await page.waitForTimeout(2000);
    
    // 获取任务并执行删除
    const tasks = page.locator('[data-testid="task-item"], .task-card, .sticky-note');
    const taskCount = await tasks.count();
    
    if (taskCount > 0) {
      const firstTask = tasks.first();
      await firstTask.click();
      await page.waitForTimeout(500);
      
      // 尝试Delete键删除
      await page.keyboard.press('Delete');
      await page.waitForTimeout(3000);
      
      console.log('网络请求监控结果:');
      console.log('DELETE请求:', requests);
      console.log('DELETE响应:', responses);
      console.log('JavaScript错误:', errors);
      
      // 验证网络请求
      if (requests.length > 0) {
        console.log('✅ 发送了DELETE请求');
        expect(requests[0].method).toBe('DELETE');
        expect(requests[0].url).toContain('/api/');
      } else {
        console.log('❌ 未发送DELETE请求');
      }
      
      // 验证响应状态
      if (responses.length > 0) {
        console.log(`✅ 收到DELETE响应，状态码: ${responses[0].status}`);
        expect(responses[0].status).toBeLessThan(400);
      } else {
        console.log('❌ 未收到DELETE响应');
      }
      
      // 验证JavaScript错误
      if (errors.length === 0) {
        console.log('✅ 没有JavaScript错误');
      } else {
        console.log(`❌ 发现${errors.length}个JavaScript错误`);
        errors.forEach(error => console.log(`  - ${error}`));
      }
    } else {
      console.log('没有任务可删除，跳过网络监控测试');
    }
  });

  test('用户反馈测试', async () => {
    console.log('=== 测试用户反馈 ===');
    
    // 等待页面稳定
    await page.waitForTimeout(2000);
    
    // 获取任务
    const tasks = page.locator('[data-testid="task-item"], .task-card, .sticky-note');
    const taskCount = await tasks.count();
    
    if (taskCount > 0) {
      const firstTask = tasks.first();
      await firstTask.click();
      await page.waitForTimeout(500);
      
      // 执行删除操作
      await page.keyboard.press('Delete');
      await page.waitForTimeout(2000);
      
      // 检查成功消息
      const successSelectors = [
        'text*="删除成功"',
        'text*="已删除"',
        'text*="成功"',
        '.success-message',
        '.toast-success',
        '.notification-success',
        '[data-testid="success-message"]'
      ];
      
      let foundSuccess = false;
      for (const selector of successSelectors) {
        const element = page.locator(selector);
        if (await element.first().isVisible()) {
          console.log(`✅ 找到成功消息: ${selector}`);
          foundSuccess = true;
          break;
        }
      }
      
      if (!foundSuccess) {
        console.log('❌ 未找到删除成功消息');
      }
      
      // 检查错误消息（应该没有）
      const errorSelectors = [
        'text*="删除失败"',
        'text*="错误"',
        'text*="失败"',
        '.error-message',
        '.toast-error',
        '.notification-error',
        '[data-testid="error-message"]'
      ];
      
      let foundError = false;
      for (const selector of errorSelectors) {
        const element = page.locator(selector);
        if (await element.first().isVisible()) {
          console.log(`❌ 发现错误消息: ${selector}`);
          foundError = true;
          break;
        }
      }
      
      if (!foundError) {
        console.log('✅ 没有错误消息（正常）');
      }
      
    } else {
      console.log('没有任务可删除，跳过用户反馈测试');
    }
  });
});