const { chromium } = require('playwright');

async function monitorConsoleErrors() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // 收集所有控制台消息
  const consoleLogs = [];
  const errors = [];
  const warnings = [];
  const networkErrors = [];

  // 监听控制台消息
  page.on('console', msg => {
    const logEntry = {
      type: msg.type(),
      text: msg.text(),
      location: msg.location(),
      timestamp: new Date().toISOString()
    };
    
    consoleLogs.push(logEntry);
    
    if (msg.type() === 'error') {
      errors.push(logEntry);
      console.log('🔴 Console Error:', msg.text());
    } else if (msg.type() === 'warning') {
      warnings.push(logEntry);
      console.log('🟡 Console Warning:', msg.text());
    } else if (msg.type() === 'log') {
      console.log('ℹ️  Console Log:', msg.text());
    }
  });

  // 监听页面错误
  page.on('pageerror', error => {
    const errorEntry = {
      type: 'pageerror',
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    };
    
    errors.push(errorEntry);
    console.log('🔴 Page Error:', error.message);
    console.log('Stack:', error.stack);
  });

  // 监听网络请求失败
  page.on('requestfailed', request => {
    const networkError = {
      type: 'network',
      url: request.url(),
      method: request.method(),
      failure: request.failure(),
      timestamp: new Date().toISOString()
    };
    
    networkErrors.push(networkError);
    console.log('🔴 Network Error:', request.url(), request.failure());
  });

  // 监听响应错误
  page.on('response', response => {
    if (response.status() >= 400) {
      const errorEntry = {
        type: 'http',
        url: response.url(),
        status: response.status(),
        statusText: response.statusText(),
        timestamp: new Date().toISOString()
      };
      
      networkErrors.push(errorEntry);
      console.log(`🔴 HTTP Error: ${response.status()} ${response.statusText()} - ${response.url()}`);
    }
  });

  try {
    console.log('🚀 访问 TaskWall 应用...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    
    console.log('⏳ 等待应用加载...');
    await page.waitForSelector('.sticky-canvas', { timeout: 10000 });
    await page.waitForTimeout(2000);

    console.log('✅ 应用已加载，开始测试操作...\n');

    // 测试操作 1: 尝试创建新任务
    console.log('🧪 测试 1: 创建新任务...');
    try {
      await page.dblclick('.sticky-canvas', { 
        position: { x: 300, y: 300 } 
      });
      await page.waitForTimeout(1000);
      
      const input = page.locator('input:visible, textarea:visible').first();
      if (await input.count() > 0) {
        await input.fill('测试任务 - 控制台监控');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(2000);
        console.log('✅ 任务创建测试完成');
      } else {
        console.log('⚠️  未找到输入框');
      }
    } catch (error) {
      console.log('❌ 任务创建失败:', error.message);
    }

    // 测试操作 2: 切换视图
    console.log('\n🧪 测试 2: 切换视图...');
    try {
      await page.keyboard.press('v');
      await page.waitForTimeout(1000);
      console.log('✅ 视图切换测试完成');
    } catch (error) {
      console.log('❌ 视图切换失败:', error.message);
    }

    // 测试操作 3: 尝试使用快捷键
    console.log('\n🧪 测试 3: 快捷键操作...');
    try {
      await page.keyboard.press('q');
      await page.waitForTimeout(1000);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);
      
      await page.keyboard.press('Meta+k');
      await page.waitForTimeout(1000);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);
      
      console.log('✅ 快捷键测试完成');
    } catch (error) {
      console.log('❌ 快捷键测试失败:', error.message);
    }

    // 测试操作 4: 尝试点击各种按钮
    console.log('\n🧪 测试 4: 点击UI元素...');
    try {
      // 尝试点击右侧抽屉
      const drawerButton = page.locator('[data-testid="drawer-toggle"], .drawer-toggle, button:has-text("🗺️")');
      if (await drawerButton.count() > 0) {
        await drawerButton.first().click();
        await page.waitForTimeout(1000);
        console.log('✅ 右侧抽屉按钮点击成功');
      }

      // 尝试点击其他可见按钮
      const buttons = page.locator('button:visible');
      const buttonCount = await buttons.count();
      console.log(`发现 ${buttonCount} 个可见按钮`);
      
      if (buttonCount > 0) {
        for (let i = 0; i < Math.min(3, buttonCount); i++) {
          try {
            const button = buttons.nth(i);
            const text = await button.textContent();
            await button.click();
            await page.waitForTimeout(500);
            console.log(`✅ 点击按钮: "${text || 'unnamed'}"`);
          } catch (buttonError) {
            console.log(`⚠️  按钮 ${i} 点击失败:`, buttonError.message);
          }
        }
      }
    } catch (error) {
      console.log('❌ UI元素测试失败:', error.message);
    }

    // 测试操作 5: 鼠标滚轮缩放
    console.log('\n🧪 测试 5: 缩放操作...');
    try {
      await page.locator('.sticky-canvas').hover();
      await page.keyboard.down('Meta');
      await page.mouse.wheel(0, -120);
      await page.waitForTimeout(500);
      await page.mouse.wheel(0, 120);
      await page.keyboard.up('Meta');
      await page.waitForTimeout(500);
      console.log('✅ 缩放测试完成');
    } catch (error) {
      console.log('❌ 缩放测试失败:', error.message);
    }

    // 等待额外时间来捕获可能的异步错误
    console.log('\n⏳ 等待额外时间来捕获异步错误...');
    await page.waitForTimeout(5000);

  } finally {
    console.log('\n📊 === 错误统计报告 ===');
    console.log(`控制台错误: ${errors.length}`);
    console.log(`控制台警告: ${warnings.length}`);
    console.log(`网络错误: ${networkErrors.length}`);
    console.log(`总控制台消息: ${consoleLogs.length}`);

    if (errors.length > 0) {
      console.log('\n🔴 === 详细错误列表 ===');
      errors.forEach((error, index) => {
        console.log(`\n错误 ${index + 1}:`);
        console.log(`类型: ${error.type}`);
        console.log(`时间: ${error.timestamp}`);
        if (error.text) {
          console.log(`消息: ${error.text}`);
        }
        if (error.message) {
          console.log(`消息: ${error.message}`);
        }
        if (error.location) {
          console.log(`位置: ${error.location.url}:${error.location.lineNumber}:${error.location.columnNumber}`);
        }
        if (error.stack) {
          console.log(`堆栈: ${error.stack}`);
        }
      });
    }

    if (warnings.length > 0) {
      console.log('\n🟡 === 警告列表 ===');
      warnings.forEach((warning, index) => {
        console.log(`\n警告 ${index + 1}:`);
        console.log(`时间: ${warning.timestamp}`);
        console.log(`消息: ${warning.text}`);
        if (warning.location) {
          console.log(`位置: ${warning.location.url}:${warning.location.lineNumber}:${warning.location.columnNumber}`);
        }
      });
    }

    if (networkErrors.length > 0) {
      console.log('\n🌐 === 网络错误列表 ===');
      networkErrors.forEach((netError, index) => {
        console.log(`\n网络错误 ${index + 1}:`);
        console.log(`时间: ${netError.timestamp}`);
        console.log(`URL: ${netError.url}`);
        if (netError.method) {
          console.log(`方法: ${netError.method}`);
        }
        if (netError.status) {
          console.log(`状态: ${netError.status} ${netError.statusText}`);
        }
        if (netError.failure) {
          console.log(`失败原因: ${netError.failure}`);
        }
      });
    }

    // 保存详细报告到文件
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalErrors: errors.length,
        totalWarnings: warnings.length,
        totalNetworkErrors: networkErrors.length,
        totalConsoleLogs: consoleLogs.length
      },
      errors,
      warnings,
      networkErrors,
      allLogs: consoleLogs
    };

    require('fs').writeFileSync('console-error-report.json', JSON.stringify(report, null, 2));
    console.log('\n💾 详细报告已保存到: console-error-report.json');

    await browser.close();
  }
}

monitorConsoleErrors().catch(console.error);