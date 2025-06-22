import { test, expect, Page } from '@playwright/test';

test.describe('TaskWall 可视化删除功能测试', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    
    // 监听所有请求和响应
    page.on('request', (request) => {
      console.log(`🔄 Request: ${request.method()} ${request.url()}`);
    });

    page.on('response', (response) => {
      console.log(`📡 Response: ${response.status()} ${response.request().method()} ${response.url()}`);
    });

    // 监听控制台
    page.on('console', (msg) => {
      console.log(`Console ${msg.type()}: ${msg.text()}`);
    });

    // 访问页面
    await page.goto('http://localhost:3000');
    
    // 等待页面完全加载
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000); // 给更多时间让Vue组件渲染
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('检查页面DOM结构和任务可见性', async () => {
    console.log('=== 检查页面DOM结构 ===');
    
    // 检查主要容器
    const canvasContainer = page.locator('.sticky-canvas');
    const canvasExists = await canvasContainer.count();
    console.log(`Canvas容器数量: ${canvasExists}`);
    
    const canvasContent = page.locator('.canvas-content');
    const contentExists = await canvasContent.count();
    console.log(`Canvas内容数量: ${contentExists}`);
    
    // 检查任务包装器
    const taskWrappers = page.locator('.task-wrapper');
    const wrapperCount = await taskWrappers.count();
    console.log(`任务包装器数量: ${wrapperCount}`);
    
    // 检查TaskCard组件
    const taskCards = page.locator('.task-card, [data-testid="task-card"]');
    const cardCount = await taskCards.count();
    console.log(`任务卡片数量: ${cardCount}`);
    
    // 如果有任务包装器，检查它们的样式
    if (wrapperCount > 0) {
      console.log('检查任务包装器样式:');
      for (let i = 0; i < Math.min(5, wrapperCount); i++) {
        const wrapper = taskWrappers.nth(i);
        const style = await wrapper.getAttribute('style');
        const isVisible = await wrapper.isVisible();
        const boundingBox = await wrapper.boundingBox();
        
        console.log(`任务 ${i + 1}:`);
        console.log(`  样式: ${style}`);
        console.log(`  可见: ${isVisible}`);
        console.log(`  位置: ${JSON.stringify(boundingBox)}`);
      }
    }
    
    // 检查画布变换
    if (contentExists > 0) {
      const contentStyle = await canvasContent.first().getAttribute('style');
      console.log(`Canvas内容样式: ${contentStyle}`);
    }
    
    // 截图保存当前状态
    await page.screenshot({ 
      path: 'test-results/dom-structure.png', 
      fullPage: true 
    });
  });

  test('手动创建任务并测试删除', async () => {
    console.log('=== 手动创建任务并测试删除 ===');
    
    // 等待页面稳定
    await page.waitForTimeout(3000);
    
    // 尝试在画布中心双击创建任务
    console.log('在画布中心双击创建任务...');
    await page.dblclick('.canvas-content', { position: { x: 400, y: 300 } });
    await page.waitForTimeout(2000);
    
    // 查找可能的输入框
    const inputSelectors = [
      'input[type="text"]',
      'textarea',
      '.task-input',
      '[contenteditable="true"]',
      'input:visible'
    ];
    
    let taskCreated = false;
    for (const selector of inputSelectors) {
      const input = page.locator(selector);
      const inputCount = await input.count();
      
      if (inputCount > 0 && await input.first().isVisible()) {
        console.log(`找到输入框: ${selector}`);
        await input.first().fill('测试删除任务');
        await input.first().press('Enter');
        await page.waitForTimeout(2000);
        taskCreated = true;
        break;
      }
    }
    
    if (!taskCreated) {
      console.log('未能创建任务，尝试其他方式...');
      
      // 尝试点击加号按钮
      const addButtons = [
        page.locator('button:has-text("+")'),
        page.locator('.add-button'),
        page.locator('.fab'),
        page.locator('[title*="添加"]')
      ];
      
      for (const btn of addButtons) {
        if (await btn.first().isVisible()) {
          console.log('点击添加按钮...');
          await btn.first().click();
          await page.waitForTimeout(1000);
          
          // 再次查找输入框
          for (const selector of inputSelectors) {
            const input = page.locator(selector);
            if (await input.first().isVisible()) {
              await input.first().fill('测试删除任务');
              await input.first().press('Enter');
              await page.waitForTimeout(2000);
              taskCreated = true;
              break;
            }
          }
          if (taskCreated) break;
        }
      }
    }
    
    // 检查是否成功创建了任务
    const taskWrappers = page.locator('.task-wrapper');
    const taskCount = await taskWrappers.count();
    console.log(`创建后任务数量: ${taskCount}`);
    
    if (taskCount > 0) {
      console.log('成功创建任务，开始测试删除...');
      
      // 选择第一个任务
      const firstTask = taskWrappers.first();
      await firstTask.click();
      await page.waitForTimeout(1000);
      
      console.log('任务已选中，测试删除方式...');
      
      // 测试1: Delete键删除
      console.log('测试Delete键删除...');
      await page.keyboard.press('Delete');
      await page.waitForTimeout(3000);
      
      let newTaskCount = await taskWrappers.count();
      if (newTaskCount < taskCount) {
        console.log('✅ Delete键删除成功');
      } else {
        console.log('❌ Delete键删除失败');
        
        // 测试2: Ctrl+D删除
        console.log('测试Ctrl+D删除...');
        await page.keyboard.press('Control+d');
        await page.waitForTimeout(3000);
        
        newTaskCount = await taskWrappers.count();
        if (newTaskCount < taskCount) {
          console.log('✅ Ctrl+D删除成功');
        } else {
          console.log('❌ Ctrl+D删除失败');
          
          // 测试3: 查找删除按钮
          console.log('查找删除按钮...');
          const deleteButtons = [
            page.locator('button:has-text("🗑️")'),
            page.locator('button:has-text("删除")'),
            page.locator('.delete-button'),
            page.locator('[title*="删除"]')
          ];
          
          for (const btn of deleteButtons) {
            if (await btn.first().isVisible()) {
              console.log('找到删除按钮，点击删除...');
              await btn.first().click();
              await page.waitForTimeout(1000);
              
              // 查找确认按钮
              const confirmBtn = page.locator('button:has-text("确认")').or(page.locator('button:has-text("确定")')).or(page.locator('button:has-text("删除")'));
              if (await confirmBtn.first().isVisible()) {
                await confirmBtn.first().click();
                await page.waitForTimeout(2000);
              }
              
              newTaskCount = await taskWrappers.count();
              if (newTaskCount < taskCount) {
                console.log('✅ 按钮删除成功');
              } else {
                console.log('❌ 按钮删除失败');
              }
              break;
            }
          }
        }
      }
    } else {
      console.log('❌ 未能创建任务进行删除测试');
    }
    
    // 截图保存最终状态
    await page.screenshot({ 
      path: 'test-results/delete-test-result.png', 
      fullPage: true 
    });
  });

  test('网络请求监控 - 删除API调用', async () => {
    console.log('=== 网络请求监控测试 ===');
    
    const deleteRequests: any[] = [];
    const deleteResponses: any[] = [];
    
    // 监听DELETE请求
    page.on('request', (request) => {
      if (request.method() === 'DELETE') {
        deleteRequests.push({
          url: request.url(),
          method: request.method(),
          timestamp: new Date().toISOString()
        });
      }
    });
    
    page.on('response', (response) => {
      if (response.request().method() === 'DELETE') {
        deleteResponses.push({
          url: response.url(),
          status: response.status(),
          timestamp: new Date().toISOString()
        });
      }
    });
    
    // 等待页面稳定
    await page.waitForTimeout(3000);
    
    // 检查现有任务
    const taskWrappers = page.locator('.task-wrapper');
    const taskCount = await taskWrappers.count();
    console.log(`现有任务数量: ${taskCount}`);
    
    if (taskCount > 0) {
      // 选择并尝试删除第一个任务
      const firstTask = taskWrappers.first();
      await firstTask.click();
      await page.waitForTimeout(1000);
      
      // 执行删除操作
      await page.keyboard.press('Delete');
      await page.waitForTimeout(3000);
      
      await page.keyboard.press('Control+d');
      await page.waitForTimeout(3000);
    } else {
      console.log('没有现有任务，尝试模拟删除操作...');
      // 即使没有任务，也测试键盘事件是否触发网络请求
      await page.keyboard.press('Delete');
      await page.waitForTimeout(2000);
      await page.keyboard.press('Control+d');
      await page.waitForTimeout(2000);
    }
    
    // 报告网络请求结果
    console.log('\n=== 网络请求监控结果 ===');
    console.log(`DELETE请求数量: ${deleteRequests.length}`);
    console.log(`DELETE响应数量: ${deleteResponses.length}`);
    
    if (deleteRequests.length > 0) {
      console.log('DELETE请求详情:');
      deleteRequests.forEach((req, index) => {
        console.log(`  ${index + 1}. ${req.method} ${req.url} at ${req.timestamp}`);
      });
    }
    
    if (deleteResponses.length > 0) {
      console.log('DELETE响应详情:');
      deleteResponses.forEach((res, index) => {
        console.log(`  ${index + 1}. ${res.status} ${res.url} at ${res.timestamp}`);
      });
    }
    
    // 验证结果
    if (deleteRequests.length === 0) {
      console.log('⚠️  没有检测到DELETE请求');
    } else {
      console.log('✅ 检测到DELETE请求，删除功能已触发');
    }
  });

  test('键盘事件监听测试', async () => {
    console.log('=== 键盘事件监听测试 ===');
    
    const keyboardEvents: string[] = [];
    
    // 注入JavaScript来监听键盘事件
    await page.addInitScript(() => {
      const events: string[] = [];
      
      document.addEventListener('keydown', (e) => {
        events.push(`keydown: ${e.key} (${e.code}) - target: ${e.target?.tagName || 'unknown'}`);
        console.log(`🎹 keydown: ${e.key} (${e.code})`);
      });
      
      document.addEventListener('keyup', (e) => {
        events.push(`keyup: ${e.key} (${e.code}) - target: ${e.target?.tagName || 'unknown'}`);
        console.log(`🎹 keyup: ${e.key} (${e.code})`);
      });
      
      // 将事件暴露给测试
      (window as any).getKeyboardEvents = () => events;
    });
    
    // 等待页面稳定
    await page.waitForTimeout(3000);
    
    // 确保焦点在页面上
    await page.click('body');
    await page.waitForTimeout(500);
    
    console.log('测试各种删除相关的键盘操作...');
    
    // 测试Delete键
    console.log('按Delete键...');
    await page.keyboard.press('Delete');
    await page.waitForTimeout(1000);
    
    // 测试Ctrl+D
    console.log('按Ctrl+D...');
    await page.keyboard.press('Control+d');
    await page.waitForTimeout(1000);
    
    // 测试Backspace
    console.log('按Backspace...');
    await page.keyboard.press('Backspace');
    await page.waitForTimeout(1000);
    
    // 获取键盘事件记录
    const events = await page.evaluate(() => {
      return (window as any).getKeyboardEvents?.() || [];
    });
    
    console.log('\n=== 键盘事件记录 ===');
    events.forEach((event: string, index: number) => {
      console.log(`  ${index + 1}. ${event}`);
    });
    
    // 检查是否捕获到了预期的键盘事件
    const deleteEvents = events.filter((e: string) => e.includes('Delete'));
    const ctrlDEvents = events.filter((e: string) => e.includes('KeyD') && e.includes('Control'));
    
    console.log(`\nDelete键事件数量: ${deleteEvents.length}`);
    console.log(`Ctrl+D事件数量: ${ctrlDEvents.length}`);
    
    if (deleteEvents.length > 0) {
      console.log('✅ Delete键事件被正确捕获');
    } else {
      console.log('❌ Delete键事件未被捕获');
    }
    
    if (ctrlDEvents.length > 0) {
      console.log('✅ Ctrl+D事件被正确捕获');
    } else {
      console.log('❌ Ctrl+D事件未被捕获');
    }
  });
});