import { test, expect, Page } from '@playwright/test';

test.describe('TaskWall 最终删除功能测试', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    
    // 监听所有删除相关的请求
    page.on('request', (request) => {
      if (request.method() === 'DELETE' || request.url().includes('delete')) {
        console.log(`🔄 DELETE Request: ${request.method()} ${request.url()}`);
      }
    });

    page.on('response', (response) => {
      if (response.request().method() === 'DELETE' || response.url().includes('delete')) {
        console.log(`📡 DELETE Response: ${response.status()} ${response.url()}`);
      }
    });

    // 监听控制台中的删除相关消息
    page.on('console', (msg) => {
      const text = msg.text();
      if (text.includes('删除') || text.includes('delete') || text.includes('Delete') || 
          text.includes('任务') || msg.type() === 'error') {
        console.log(`Console ${msg.type()}: ${text}`);
      }
    });

    // 访问页面
    await page.goto('http://localhost:3000');
    
    // 等待页面完全加载
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('使用小地图定位和测试删除功能', async () => {
    console.log('=== 使用小地图定位任务并测试删除 ===');
    
    // 等待页面稳定
    await page.waitForTimeout(3000);
    
    // 检查小地图是否存在
    const minimap = page.locator('.mini-map, .minimap');
    const minimapExists = await minimap.count();
    console.log(`小地图数量: ${minimapExists}`);
    
    if (minimapExists > 0) {
      console.log('找到小地图，尝试点击任务点');
      
      // 在小地图中查找任务点
      const taskDots = minimap.locator('.task-dot, .minimap-task, div').filter({
        hasNotText: ''
      });
      const dotCount = await taskDots.count();
      console.log(`小地图中的任务点数量: ${dotCount}`);
      
      if (dotCount > 0) {
        // 点击第一个任务点来聚焦
        console.log('点击小地图中的第一个任务点');
        await taskDots.first().click();
        await page.waitForTimeout(2000);
        
        // 截图查看聚焦后的状态
        await page.screenshot({ 
          path: 'test-results/after-minimap-focus.png', 
          fullPage: true 
        });
      }
    }
    
    // 检查主画布中的任务
    const taskWrappers = page.locator('.task-wrapper');
    const wrapperCount = await taskWrappers.count();
    console.log(`主画布任务包装器数量: ${wrapperCount}`);
    
    if (wrapperCount > 0) {
      console.log('在主画布中找到任务，开始删除测试');
      
      // 检查第一个任务的位置和可见性
      const firstTask = taskWrappers.first();
      const isVisible = await firstTask.isVisible();
      const boundingBox = await firstTask.boundingBox();
      
      console.log(`第一个任务可见性: ${isVisible}`);
      console.log(`第一个任务位置: ${JSON.stringify(boundingBox)}`);
      
      if (isVisible) {
        // 点击选择任务
        console.log('点击选择第一个任务');
        await firstTask.click();
        await page.waitForTimeout(1000);
        
        // 测试Delete键删除
        console.log('测试Delete键删除...');
        await page.keyboard.press('Delete');
        await page.waitForTimeout(3000);
        
        // 检查任务数量是否减少
        const newWrapperCount = await taskWrappers.count();
        console.log(`Delete键删除后任务数量: ${newWrapperCount}`);
        
        if (newWrapperCount < wrapperCount) {
          console.log('✅ Delete键删除成功！');
          return;
        }
        
        // 如果Delete键没用，尝试Ctrl+D
        console.log('测试Ctrl+D删除...');
        await page.keyboard.press('Control+d');
        await page.waitForTimeout(3000);
        
        const ctrlDCount = await taskWrappers.count();
        console.log(`Ctrl+D删除后任务数量: ${ctrlDCount}`);
        
        if (ctrlDCount < wrapperCount) {
          console.log('✅ Ctrl+D删除成功！');
          return;
        }
        
        // 查找删除按钮
        console.log('查找UI删除按钮...');
        const deleteButtons = [
          page.locator('button:has-text("🗑️")'),
          page.locator('button:has-text("删除")'),
          page.locator('.delete-button'),
          page.locator('[aria-label*="删除"]'),
          page.locator('[title*="删除"]')
        ];
        
        for (const btnLocator of deleteButtons) {
          const btnCount = await btnLocator.count();
          if (btnCount > 0 && await btnLocator.first().isVisible()) {
            console.log(`找到删除按钮，点击删除`);
            await btnLocator.first().click();
            await page.waitForTimeout(2000);
            
            // 查找确认按钮
            const confirmBtn = page.locator('button:has-text("确认")').or(page.locator('button:has-text("确定")'));
            if (await confirmBtn.first().isVisible()) {
              console.log('点击确认删除');
              await confirmBtn.first().click();
              await page.waitForTimeout(2000);
            }
            
            const btnDeleteCount = await taskWrappers.count();
            console.log(`按钮删除后任务数量: ${btnDeleteCount}`);
            
            if (btnDeleteCount < wrapperCount) {
              console.log('✅ 按钮删除成功！');
              return;
            }
            break;
          }
        }
        
        console.log('❌ 所有删除方式都失败了');
      } else {
        console.log('❌ 任务不可见，无法进行删除测试');
      }
    } else {
      console.log('❌ 未找到任务包装器');
    }
  });

  test('重置视图并手动删除测试', async () => {
    console.log('=== 重置视图并手动删除测试 ===');
    
    // 等待页面稳定
    await page.waitForTimeout(3000);
    
    // 尝试重置视图到中心
    console.log('尝试重置视图...');
    
    // 查找重置/居中按钮
    const resetButtons = [
      page.locator('button:has-text("重置")'),
      page.locator('button:has-text("居中")'),
      page.locator('button:has-text("🏠")'),
      page.locator('.reset-view'),
      page.locator('.center-view')
    ];
    
    for (const btn of resetButtons) {
      if (await btn.first().isVisible()) {
        console.log('找到重置按钮，点击重置视图');
        await btn.first().click();
        await page.waitForTimeout(2000);
        break;
      }
    }
    
    // 尝试使用键盘快捷键重置视图
    console.log('尝试键盘快捷键重置视图...');
    await page.keyboard.press('Home'); // 通常Home键用于重置视图
    await page.waitForTimeout(1000);
    
    await page.keyboard.press('Control+0'); // Ctrl+0通常用于重置缩放
    await page.waitForTimeout(1000);
    
    // 尝试滚轮重置缩放
    console.log('尝试滚轮操作...');
    await page.mouse.wheel(0, -500); // 向上滚动放大
    await page.waitForTimeout(1000);
    
    // 检查任务是否现在可见
    const taskWrappers = page.locator('.task-wrapper');
    const wrapperCount = await taskWrappers.count();
    console.log(`重置后任务包装器数量: ${wrapperCount}`);
    
    if (wrapperCount > 0) {
      // 检查任务的可见性
      for (let i = 0; i < Math.min(3, wrapperCount); i++) {
        const task = taskWrappers.nth(i);
        const isVisible = await task.isVisible();
        const boundingBox = await task.boundingBox();
        
        console.log(`任务 ${i + 1}: 可见=${isVisible}, 位置=${JSON.stringify(boundingBox)}`);
        
        if (isVisible && boundingBox) {
          console.log(`测试删除任务 ${i + 1}`);
          
          // 点击选择任务
          await task.click();
          await page.waitForTimeout(1000);
          
          // 尝试删除
          await page.keyboard.press('Delete');
          await page.waitForTimeout(2000);
          
          // 检查是否删除成功
          const newCount = await taskWrappers.count();
          if (newCount < wrapperCount) {
            console.log(`✅ 成功删除任务 ${i + 1}！`);
            break;
          }
        }
      }
    }
    
    // 截图保存最终状态
    await page.screenshot({ 
      path: 'test-results/reset-view-final.png', 
      fullPage: true 
    });
  });

  test('命令面板删除测试', async () => {
    console.log('=== 命令面板删除测试 ===');
    
    // 等待页面稳定
    await page.waitForTimeout(3000);
    
    // 尝试打开命令面板 (通常是Ctrl+K或Ctrl+P)
    console.log('尝试打开命令面板...');
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(1000);
    
    // 检查命令面板是否打开
    const commandPalette = page.locator('.command-palette, .command-panel, [role="dialog"]').filter({
      hasText: /命令|command/i
    });
    
    if (await commandPalette.first().isVisible()) {
      console.log('找到命令面板');
      
      // 搜索删除命令
      const searchInput = commandPalette.locator('input');
      if (await searchInput.first().isVisible()) {
        await searchInput.first().fill('删除');
        await page.waitForTimeout(1000);
        
        // 查找删除选项
        const deleteOptions = commandPalette.locator('text*="删除"');
        if (await deleteOptions.first().isVisible()) {
          console.log('找到删除选项，点击执行');
          await deleteOptions.first().click();
          await page.waitForTimeout(2000);
        }
      }
    } else {
      console.log('❌ 未找到命令面板');
    }
  });

  test('直接API删除测试', async () => {
    console.log('=== 直接API删除测试 ===');
    
    // 等待页面稳定
    await page.waitForTimeout(3000);
    
    // 使用JavaScript直接调用删除API
    console.log('尝试直接调用删除API...');
    
    const result = await page.evaluate(async () => {
      try {
        // 获取第一个任务ID
        const taskStore = (window as any).Vue?.config?.globalProperties?.$stores?.tasks;
        if (taskStore && taskStore.tasks.length > 0) {
          const firstTaskId = taskStore.tasks[0].id;
          console.log(`尝试删除任务ID: ${firstTaskId}`);
          
          // 直接调用删除方法
          if (taskStore.deleteTask) {
            await taskStore.deleteTask(firstTaskId);
            return { success: true, taskId: firstTaskId, method: 'store' };
          }
          
          // 或者直接发起DELETE请求
          const response = await fetch(`/api/tasks/${firstTaskId}`, {
            method: 'DELETE'
          });
          
          return { 
            success: response.ok, 
            status: response.status, 
            taskId: firstTaskId,
            method: 'fetch'
          };
        }
        
        return { success: false, error: 'No tasks found' };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
    
    console.log('直接API删除结果:', JSON.stringify(result, null, 2));
    
    if (result.success) {
      console.log('✅ 直接API删除成功！');
    } else {
      console.log('❌ 直接API删除失败：', result.error);
    }
  });
});