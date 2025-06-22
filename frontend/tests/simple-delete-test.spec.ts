import { test, expect, Page } from '@playwright/test';

test.describe('TaskWall 删除功能简化测试', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    
    // 监听控制台消息
    page.on('console', (msg) => {
      if (msg.type() === 'error' || msg.text().includes('删除') || msg.text().includes('DELETE')) {
        console.log(`Console ${msg.type()}: ${msg.text()}`);
      }
    });

    // 监听网络请求
    page.on('request', (request) => {
      if (request.method() === 'DELETE') {
        console.log(`🔄 DELETE request: ${request.url()}`);
      }
    });

    page.on('response', (response) => {
      if (response.request().method() === 'DELETE') {
        console.log(`📡 DELETE response: ${response.status()} - ${response.url()}`);
      }
    });

    // 访问页面
    await page.goto('http://localhost:3000');
    
    // 等待页面加载完成
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('检查页面状态和任务', async () => {
    console.log('=== 检查页面状态 ===');
    
    // 等待页面稳定
    await page.waitForTimeout(3000);
    
    // 检查各种可能的任务选择器
    const selectors = [
      '.sticky-note',
      '.task-card', 
      '.task-item',
      '[data-testid="task-item"]',
      '.note',
      '.task',
      'div[draggable="true"]',
      'div:has-text("任务")',
      'div:has-text("Task")'
    ];
    
    for (const selector of selectors) {
      const count = await page.locator(selector).count();
      console.log(`选择器 "${selector}": ${count} 个元素`);
    }
    
    // 截图
    await page.screenshot({ path: 'test-results/page-state.png', fullPage: true });
    
    // 检查页面HTML内容
    const bodyHTML = await page.locator('body').innerHTML();
    console.log('页面HTML长度:', bodyHTML.length);
    
    // 查找包含文本的div元素
    const allDivs = page.locator('div');
    const divCount = await allDivs.count();
    console.log(`总共有 ${divCount} 个div元素`);
    
    // 查找可能是任务的元素
    const possibleTasks = page.locator('div').filter({
      has: page.locator('text')
    });
    const possibleTaskCount = await possibleTasks.count();
    console.log(`包含文本的div元素: ${possibleTaskCount} 个`);
  });

  test('手动查找和删除任务', async () => {
    console.log('=== 手动查找和删除任务 ===');
    
    // 等待页面稳定
    await page.waitForTimeout(3000);
    
    // 尝试找到任何可点击的任务元素
    const clickableElements = page.locator('div, span, button').filter({
      has: page.locator('text')
    });
    
    const count = await clickableElements.count();
    console.log(`找到 ${count} 个包含文本的可点击元素`);
    
    if (count > 0) {
      // 获取前几个元素的信息
      for (let i = 0; i < Math.min(5, count); i++) {
        const element = clickableElements.nth(i);
        const text = await element.textContent();
        const tagName = await element.evaluate(el => el.tagName);
        const className = await element.getAttribute('class') || '';
        
        console.log(`元素 ${i}: <${tagName}> class="${className}" text="${text?.slice(0, 50)}"`);
        
        // 如果看起来像任务，尝试点击并测试删除
        if (text && text.length > 0 && text.length < 200) {
          console.log(`尝试点击元素 ${i}`);
          
          try {
            await element.click();
            await page.waitForTimeout(1000);
            
            console.log('测试Delete键删除...');
            await page.keyboard.press('Delete');
            await page.waitForTimeout(2000);
            
            console.log('测试Ctrl+D删除...');
            await page.keyboard.press('Control+d');
            await page.waitForTimeout(2000);
            
            // 查找删除按钮
            const deleteBtn = page.locator('button').filter({
              or: [
                { hasText: '🗑️' },
                { hasText: '删除' },
                { hasText: 'Delete' }
              ]
            });
            
            const deleteBtnCount = await deleteBtn.count();
            if (deleteBtnCount > 0) {
              console.log(`找到 ${deleteBtnCount} 个删除按钮`);
              await deleteBtn.first().click();
              await page.waitForTimeout(2000);
            }
            
            break; // 只测试第一个有效元素
          } catch (error) {
            console.log(`点击元素 ${i} 失败: ${error}`);
          }
        }
      }
    }
  });

  test('键盘快捷键测试', async () => {
    console.log('=== 键盘快捷键测试 ===');
    
    // 等待页面稳定
    await page.waitForTimeout(3000);
    
    // 确保焦点在页面上
    await page.click('body');
    await page.waitForTimeout(500);
    
    console.log('测试Delete键...');
    await page.keyboard.press('Delete');
    await page.waitForTimeout(2000);
    
    console.log('测试Ctrl+D...');
    await page.keyboard.press('Control+d');
    await page.waitForTimeout(2000);
    
    console.log('测试其他可能的删除快捷键...');
    await page.keyboard.press('Backspace');
    await page.waitForTimeout(1000);
    
    await page.keyboard.press('Control+Delete');
    await page.waitForTimeout(1000);
  });

  test('右键菜单测试', async () => {
    console.log('=== 右键菜单测试 ===');
    
    // 等待页面稳定
    await page.waitForTimeout(3000);
    
    // 在页面中心右键
    await page.click('body', { button: 'right', position: { x: 400, y: 300 } });
    await page.waitForTimeout(1000);
    
    // 查找右键菜单
    const contextMenu = page.locator('.context-menu, .menu, [role="menu"]');
    const menuVisible = await contextMenu.isVisible();
    
    if (menuVisible) {
      console.log('✅ 找到右键菜单');
      
      // 查找删除选项
      const deleteOption = page.locator('text="删除"').or(page.locator('text="Delete"'));
      const deleteVisible = await deleteOption.isVisible();
      
      if (deleteVisible) {
        console.log('✅ 找到删除选项');
        await deleteOption.click();
        await page.waitForTimeout(2000);
      } else {
        console.log('❌ 未找到删除选项');
      }
    } else {
      console.log('❌ 未找到右键菜单');
    }
  });

  test('全面错误监控测试', async () => {
    console.log('=== 全面错误监控测试 ===');
    
    const requests: any[] = [];
    const responses: any[] = [];
    const errors: string[] = [];
    const consoleLogs: string[] = [];

    // 监听各种事件
    page.on('request', (request) => {
      requests.push({
        method: request.method(),
        url: request.url(),
        timestamp: new Date().toISOString()
      });
    });

    page.on('response', (response) => {
      responses.push({
        status: response.status(),
        url: response.url(),
        method: response.request().method(),
        timestamp: new Date().toISOString()
      });
    });

    page.on('pageerror', (error) => {
      errors.push(error.message);
      console.log(`❌ JavaScript Error: ${error.message}`);
    });

    page.on('console', (msg) => {
      if (msg.type() === 'error' || msg.text().includes('删除') || msg.text().includes('DELETE')) {
        consoleLogs.push(`${msg.type()}: ${msg.text()}`);
      }
    });

    // 等待页面稳定
    await page.waitForTimeout(3000);
    
    // 执行各种可能触发删除的操作
    console.log('执行删除相关操作...');
    
    await page.click('body');
    await page.keyboard.press('Delete');
    await page.waitForTimeout(1000);
    
    await page.keyboard.press('Control+d');
    await page.waitForTimeout(1000);
    
    // 报告结果
    console.log('\n=== 监控结果 ===');
    console.log(`总请求数: ${requests.length}`);
    console.log(`总响应数: ${responses.length}`);
    console.log(`JavaScript错误数: ${errors.length}`);
    console.log(`相关控制台日志数: ${consoleLogs.length}`);
    
    // DELETE请求
    const deleteRequests = requests.filter(r => r.method === 'DELETE');
    console.log(`DELETE请求数: ${deleteRequests.length}`);
    deleteRequests.forEach((req, index) => {
      console.log(`  ${index + 1}. ${req.method} ${req.url} at ${req.timestamp}`);
    });
    
    // DELETE响应
    const deleteResponses = responses.filter(r => r.method === 'DELETE');
    console.log(`DELETE响应数: ${deleteResponses.length}`);
    deleteResponses.forEach((res, index) => {
      console.log(`  ${index + 1}. ${res.status} ${res.url} at ${res.timestamp}`);
    });
    
    // 错误详情
    if (errors.length > 0) {
      console.log('JavaScript错误详情:');
      errors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error}`);
      });
    }
    
    // 控制台日志
    if (consoleLogs.length > 0) {
      console.log('相关控制台日志:');
      consoleLogs.forEach((log, index) => {
        console.log(`  ${index + 1}. ${log}`);
      });
    }
    
    // 验证
    if (deleteRequests.length === 0) {
      console.log('⚠️  没有发现DELETE请求，删除功能可能未被触发');
    } else {
      console.log('✅ 发现DELETE请求，删除功能已被触发');
    }
    
    if (errors.length === 0) {
      console.log('✅ 没有JavaScript错误');
    } else {
      console.log(`❌ 发现 ${errors.length} 个JavaScript错误`);
    }
  });
});