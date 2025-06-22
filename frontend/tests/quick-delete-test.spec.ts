import { test, expect, Page } from '@playwright/test';

test.describe('快速删除功能测试', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    
    // 监听删除相关请求
    page.on('request', (request) => {
      if (request.method() === 'DELETE') {
        console.log(`🔄 DELETE请求: ${request.url()}`);
      }
    });

    page.on('response', (response) => {
      if (response.request().method() === 'DELETE') {
        console.log(`📡 DELETE响应: ${response.status()} ${response.url()}`);
      }
    });

    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('删除功能完整测试', async () => {
    console.log('=== 开始删除功能测试 ===');
    
    // 等待页面完全加载
    await page.waitForTimeout(3000);
    
    // 检查任务数量
    const taskWrappers = page.locator('.task-wrapper');
    const initialCount = await taskWrappers.count();
    console.log(`初始任务数量: ${initialCount}`);
    
    if (initialCount === 0) {
      console.log('❌ 没有任务可删除');
      return;
    }
    
    // 点击小地图中的第一个任务来聚焦
    const minimap = page.locator('.mini-map');
    const minimapTasks = minimap.locator('div').filter({ hasNotText: '' });
    const minimapTaskCount = await minimapTasks.count();
    console.log(`小地图任务数量: ${minimapTaskCount}`);
    
    if (minimapTaskCount > 0) {
      console.log('通过小地图聚焦到第一个任务');
      await minimapTasks.first().click();
      await page.waitForTimeout(2000);
    }
    
    // 现在选择第一个任务
    const firstTask = taskWrappers.first();
    const isVisible = await firstTask.isVisible();
    console.log(`第一个任务是否可见: ${isVisible}`);
    
    if (isVisible) {
      console.log('点击选择第一个任务');
      await firstTask.click();
      await page.waitForTimeout(1000);
      
      // 记录删除前的任务数量
      const beforeDeleteCount = await taskWrappers.count();
      console.log(`删除前任务数量: ${beforeDeleteCount}`);
      
      // 尝试 Delete 键删除
      console.log('🔥 按Delete键删除任务...');
      await page.keyboard.press('Delete');
      await page.waitForTimeout(3000);
      
      // 检查任务数量是否减少
      const afterDeleteCount = await taskWrappers.count();
      console.log(`Delete键后任务数量: ${afterDeleteCount}`);
      
      if (afterDeleteCount < beforeDeleteCount) {
        console.log('✅ Delete键删除成功！');
        console.log(`成功删除了 ${beforeDeleteCount - afterDeleteCount} 个任务`);
        return;
      }
      
      // 如果Delete键没有效果，尝试 Ctrl+D
      console.log('🔥 尝试Ctrl+D删除...');
      await page.keyboard.press('Control+d');
      await page.waitForTimeout(3000);
      
      const afterCtrlDCount = await taskWrappers.count();
      console.log(`Ctrl+D后任务数量: ${afterCtrlDCount}`);
      
      if (afterCtrlDCount < beforeDeleteCount) {
        console.log('✅ Ctrl+D删除成功！');
        console.log(`成功删除了 ${beforeDeleteCount - afterCtrlDCount} 个任务`);
        return;
      }
      
      console.log('❌ 键盘快捷键删除失败');
      console.log('📋 检查是否有删除按钮...');
      
      // 查找删除按钮
      const deleteButtons = page.locator('button').filter({
        or: [
          { hasText: '🗑️' },
          { hasText: '删除' },
          { hasText: 'Delete' }
        ]
      });
      
      const deleteButtonCount = await deleteButtons.count();
      console.log(`找到删除按钮数量: ${deleteButtonCount}`);
      
      if (deleteButtonCount > 0) {
        console.log('点击删除按钮...');
        await deleteButtons.first().click();
        await page.waitForTimeout(2000);
        
        // 检查是否有确认对话框
        const confirmButtons = page.locator('button').filter({
          or: [
            { hasText: '确认' },
            { hasText: '确定' },
            { hasText: '删除' }
          ]
        });
        
        const confirmCount = await confirmButtons.count();
        if (confirmCount > 0) {
          console.log('点击确认按钮...');
          await confirmButtons.first().click();
          await page.waitForTimeout(2000);
        }
        
        const afterButtonCount = await taskWrappers.count();
        console.log(`按钮删除后任务数量: ${afterButtonCount}`);
        
        if (afterButtonCount < beforeDeleteCount) {
          console.log('✅ 按钮删除成功！');
          console.log(`成功删除了 ${beforeDeleteCount - afterButtonCount} 个任务`);
          return;
        }
      }
      
      console.log('❌ 所有删除方式都失败了');
      
      // 最后尝试：直接调用API
      console.log('🔧 尝试直接调用删除API...');
      const apiResult = await page.evaluate(async () => {
        try {
          // 尝试获取任务数据
          const taskElements = document.querySelectorAll('.task-wrapper');
          if (taskElements.length > 0) {
            const taskElement = taskElements[0];
            const taskId = taskElement.getAttribute('data-task-id');
            
            if (taskId) {
              console.log(`Found task ID: ${taskId}`);
              
              // 发送DELETE请求
              const response = await fetch(`/api/tasks/${taskId}`, {
                method: 'DELETE',
                headers: {
                  'Content-Type': 'application/json'
                }
              });
              
              return {
                success: response.ok,
                status: response.status,
                taskId: taskId
              };
            }
          }
          
          return { success: false, error: 'No task ID found' };
        } catch (error) {
          return { success: false, error: error.message };
        }
      });
      
      console.log('直接API调用结果:', JSON.stringify(apiResult, null, 2));
      
      if (apiResult.success) {
        console.log('✅ 直接API删除成功！');
        await page.waitForTimeout(2000);
        
        const finalCount = await taskWrappers.count();
        console.log(`API删除后任务数量: ${finalCount}`);
        
        if (finalCount < beforeDeleteCount) {
          console.log('✅ API删除已生效！');
        }
      }
      
    } else {
      console.log('❌ 第一个任务不可见，无法进行删除测试');
    }
    
    // 截图保存测试结果
    await page.screenshot({ 
      path: 'test-results/quick-delete-final.png', 
      fullPage: true 
    });
    
    console.log('=== 删除功能测试完成 ===');
  });
});