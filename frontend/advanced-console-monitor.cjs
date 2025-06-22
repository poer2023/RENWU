const { chromium } = require('playwright');

async function advancedConsoleMonitor() {
  const browser = await chromium.launch({ 
    headless: false,
    devtools: true 
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  // 收集更详细的错误信息
  const allIssues = [];
  
  // 监听所有类型的控制台消息
  page.on('console', msg => {
    const entry = {
      type: msg.type(),
      text: msg.text(),
      location: msg.location(),
      timestamp: new Date().toISOString(),
      args: msg.args().length
    };
    
    allIssues.push(entry);
    
    // 详细输出不同级别的消息
    const emoji = {
      'error': '🔴',
      'warning': '🟡', 
      'info': 'ℹ️',
      'log': '📝',
      'debug': '🔍',
      'trace': '📍'
    };
    
    console.log(`${emoji[msg.type()] || '❓'} [${msg.type().toUpperCase()}] ${msg.text()}`);
    
    if (msg.location() && msg.location().url) {
      console.log(`   📍 ${msg.location().url}:${msg.location().lineNumber}:${msg.location().columnNumber}`);
    }
  });

  // 监听页面错误
  page.on('pageerror', error => {
    allIssues.push({
      type: 'pageerror',
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
    
    console.log('🔴 [PAGE ERROR]', error.message);
    if (error.stack) {
      console.log('   📋 Stack trace:');
      error.stack.split('\n').forEach(line => {
        if (line.trim()) console.log(`      ${line.trim()}`);
      });
    }
  });

  // 监听未处理的Promise拒绝
  page.on('crash', () => {
    console.log('💥 [CRASH] Page crashed!');
    allIssues.push({
      type: 'crash',
      timestamp: new Date().toISOString()
    });
  });

  // 监听请求失败
  page.on('requestfailed', request => {
    const failure = request.failure();
    console.log(`🌐 [REQUEST FAILED] ${request.method()} ${request.url()}`);
    console.log(`   ❌ Failure: ${failure ? failure.errorText : 'Unknown error'}`);
    
    allIssues.push({
      type: 'requestfailed',
      url: request.url(),
      method: request.method(),
      failure: failure ? failure.errorText : 'Unknown',
      timestamp: new Date().toISOString()
    });
  });

  // 监听响应错误
  page.on('response', response => {
    if (response.status() >= 400) {
      console.log(`🌐 [HTTP ERROR] ${response.status()} ${response.statusText()} - ${response.url()}`);
      
      allIssues.push({
        type: 'httperror',
        url: response.url(),
        status: response.status(),
        statusText: response.statusText(),
        timestamp: new Date().toISOString()
      });
    }
  });

  try {
    console.log('🚀 Starting comprehensive console monitoring...');
    console.log('📱 Opening TaskWall application...');
    
    await page.goto('http://localhost:3000', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    console.log('⏳ Waiting for application to fully load...');
    await page.waitForSelector('.sticky-canvas', { timeout: 15000 });
    await page.waitForTimeout(3000);

    // 获取页面性能信息
    const performance = await page.evaluate(() => {
      const perf = performance.getEntriesByType('navigation')[0];
      return {
        domContentLoaded: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
        loadComplete: perf.loadEventEnd - perf.loadEventStart,
        totalLoadTime: perf.loadEventEnd - perf.navigationStart
      };
    });
    
    console.log('📊 Performance metrics:');
    console.log(`   DOM Content Loaded: ${performance.domContentLoaded.toFixed(2)}ms`);
    console.log(`   Load Complete: ${performance.loadComplete.toFixed(2)}ms`);
    console.log(`   Total Load Time: ${performance.totalLoadTime.toFixed(2)}ms`);

    console.log('\n🧪 Starting comprehensive testing...');

    // 测试 1: 基本UI交互
    console.log('\n🧪 Test 1: Basic UI interactions...');
    try {
      // 检查关键元素是否存在
      const stickyCanvas = await page.locator('.sticky-canvas').count();
      const taskCards = await page.locator('.task-card').count();
      
      console.log(`✅ Sticky Canvas found: ${stickyCanvas > 0}`);
      console.log(`✅ Task Cards found: ${taskCards}`);
      
      // 尝试悬停操作
      if (taskCards > 0) {
        await page.locator('.task-card').first().hover();
        await page.waitForTimeout(1000);
        console.log('✅ Task card hover successful');
      }
      
    } catch (error) {
      console.log('❌ Basic UI test failed:', error.message);
    }

    // 测试 2: 任务创建
    console.log('\n🧪 Test 2: Task creation...');
    try {
      // 尝试双击创建任务
      await page.locator('.sticky-canvas').dblclick({ 
        position: { x: 400, y: 300 },
        timeout: 5000
      });
      await page.waitForTimeout(1500);
      
      // 检查是否出现输入框
      const inputs = await page.locator('input:visible, textarea:visible').count();
      console.log(`Input fields visible: ${inputs}`);
      
      if (inputs > 0) {
        const input = page.locator('input:visible, textarea:visible').first();
        await input.fill('Console Monitor Test Task');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(2000);
        console.log('✅ Task creation test completed');
        
        // 验证任务是否创建成功
        const newTaskExists = await page.locator('.task-card:has-text("Console Monitor Test Task")').count();
        console.log(`✅ New task visible: ${newTaskExists > 0}`);
      } else {
        console.log('⚠️  No input field appeared for task creation');
      }
      
    } catch (error) {
      console.log('❌ Task creation test failed:', error.message);
    }

    // 测试 3: 键盘快捷键
    console.log('\n🧪 Test 3: Keyboard shortcuts...');
    const shortcuts = [
      { key: 'q', name: 'Quick add' },
      { key: 'Meta+k', name: 'Command palette' },
      { key: 'v', name: 'View toggle' },
      { key: 'Escape', name: 'Escape' }
    ];
    
    for (const shortcut of shortcuts) {
      try {
        console.log(`   Testing ${shortcut.name} (${shortcut.key})...`);
        await page.keyboard.press(shortcut.key);
        await page.waitForTimeout(1000);
        
        // 如果是ESC，不需要再按ESC
        if (shortcut.key !== 'Escape') {
          await page.keyboard.press('Escape');
          await page.waitForTimeout(500);
        }
        
        console.log(`   ✅ ${shortcut.name} shortcut test completed`);
      } catch (error) {
        console.log(`   ❌ ${shortcut.name} shortcut failed:`, error.message);
      }
    }

    // 测试 4: 拖拽操作
    console.log('\n🧪 Test 4: Drag and drop operations...');
    try {
      const taskCards = page.locator('.task-card');
      const count = await taskCards.count();
      
      if (count > 0) {
        const firstTask = taskCards.first();
        const box = await firstTask.boundingBox();
        
        if (box) {
          // 执行拖拽
          await firstTask.hover();
          await page.mouse.down();
          await page.mouse.move(box.x + 100, box.y + 100);
          await page.mouse.up();
          await page.waitForTimeout(1000);
          console.log('✅ Drag and drop test completed');
        }
      }
    } catch (error) {
      console.log('❌ Drag and drop test failed:', error.message);
    }

    // 测试 5: 缩放操作
    console.log('\n🧪 Test 5: Zoom operations...');
    try {
      const canvas = page.locator('.sticky-canvas');
      await canvas.hover();
      
      // 放大
      await page.keyboard.down('Meta');
      await page.mouse.wheel(0, -120);
      await page.waitForTimeout(500);
      
      // 缩小
      await page.mouse.wheel(0, 120);
      await page.keyboard.up('Meta');
      await page.waitForTimeout(500);
      
      console.log('✅ Zoom operations test completed');
    } catch (error) {
      console.log('❌ Zoom operations test failed:', error.message);
    }

    // 测试 6: 边界情况
    console.log('\n🧪 Test 6: Edge cases and stress tests...');
    try {
      // 快速连续点击
      for (let i = 0; i < 5; i++) {
        await page.keyboard.press('v');
        await page.waitForTimeout(100);
      }
      
      // 尝试在边界位置点击
      await page.locator('body').click({ position: { x: 10, y: 10 } });
      await page.waitForTimeout(500);
      
      console.log('✅ Edge cases test completed');
    } catch (error) {
      console.log('❌ Edge cases test failed:', error.message);
    }

    // 等待额外时间捕获任何延迟的错误
    console.log('\n⏳ Waiting for delayed errors...');
    await page.waitForTimeout(5000);

    // 获取最终的内存和性能信息
    const finalMetrics = await page.evaluate(() => {
      const memInfo = performance.memory;
      return {
        memory: memInfo ? {
          used: memInfo.usedJSHeapSize,
          total: memInfo.totalJSHeapSize,
          limit: memInfo.jsHeapSizeLimit
        } : null,
        timing: performance.now()
      };
    });

    if (finalMetrics.memory) {
      console.log('\n💾 Memory Usage:');
      console.log(`   Used: ${(finalMetrics.memory.used / 1024 / 1024).toFixed(2)} MB`);
      console.log(`   Total: ${(finalMetrics.memory.total / 1024 / 1024).toFixed(2)} MB`);
      console.log(`   Limit: ${(finalMetrics.memory.limit / 1024 / 1024).toFixed(2)} MB`);
    }

  } finally {
    // 生成最终报告
    console.log('\n📊 === FINAL CONSOLE MONITORING REPORT ===');
    
    const errorCount = allIssues.filter(issue => 
      issue.type === 'error' || issue.type === 'pageerror' || issue.type === 'crash'
    ).length;
    
    const warningCount = allIssues.filter(issue => issue.type === 'warning').length;
    const networkErrorCount = allIssues.filter(issue => 
      issue.type === 'requestfailed' || issue.type === 'httperror'
    ).length;
    
    console.log(`🔴 Critical Errors: ${errorCount}`);
    console.log(`🟡 Warnings: ${warningCount}`);
    console.log(`🌐 Network Errors: ${networkErrorCount}`);
    console.log(`📝 Total Console Messages: ${allIssues.length}`);

    // 按类型分组显示所有问题
    const criticalIssues = allIssues.filter(issue => 
      issue.type === 'error' || issue.type === 'pageerror' || issue.type === 'crash'
    );
    
    if (criticalIssues.length > 0) {
      console.log('\n🔴 === CRITICAL ISSUES ===');
      criticalIssues.forEach((issue, index) => {
        console.log(`\n${index + 1}. ${issue.type.toUpperCase()}`);
        console.log(`Time: ${issue.timestamp}`);
        if (issue.text) console.log(`Message: ${issue.text}`);
        if (issue.message) console.log(`Message: ${issue.message}`);
        if (issue.location) {
          console.log(`Location: ${issue.location.url}:${issue.location.lineNumber}:${issue.location.columnNumber}`);
        }
        if (issue.stack) {
          console.log('Stack trace:');
          issue.stack.split('\n').forEach(line => {
            if (line.trim()) console.log(`  ${line.trim()}`);
          });
        }
      });
    } else {
      console.log('\n✅ === NO CRITICAL ERRORS DETECTED ===');
      console.log('The application appears to be running without any critical JavaScript errors!');
    }

    // 警告总结
    const warnings = allIssues.filter(issue => issue.type === 'warning');
    if (warnings.length > 0) {
      console.log('\n🟡 === WARNINGS SUMMARY ===');
      warnings.forEach((warning, index) => {
        console.log(`${index + 1}. ${warning.text}`);
        if (warning.location) {
          console.log(`   Location: ${warning.location.url}:${warning.location.lineNumber}`);
        }
      });
    }

    // 网络问题总结
    const networkIssues = allIssues.filter(issue => 
      issue.type === 'requestfailed' || issue.type === 'httperror'
    );
    
    if (networkIssues.length > 0) {
      console.log('\n🌐 === NETWORK ISSUES SUMMARY ===');
      networkIssues.forEach((netIssue, index) => {
        console.log(`${index + 1}. ${netIssue.type.toUpperCase()}: ${netIssue.url}`);
        if (netIssue.status) console.log(`   Status: ${netIssue.status} ${netIssue.statusText}`);
        if (netIssue.failure) console.log(`   Failure: ${netIssue.failure}`);
        console.log(`   Time: ${netIssue.timestamp}`);
      });
    }

    // 保存详细报告
    const detailedReport = {
      timestamp: new Date().toISOString(),
      summary: {
        criticalErrors: errorCount,
        warnings: warningCount,
        networkErrors: networkErrorCount,
        totalMessages: allIssues.length,
        testingCompleted: true
      },
      performance: finalMetrics,
      allIssues: allIssues
    };

    require('fs').writeFileSync('detailed-console-report.json', JSON.stringify(detailedReport, null, 2));
    console.log('\n💾 Detailed report saved to: detailed-console-report.json');

    console.log('\n🏁 Console monitoring completed successfully!');
    
    // 稍等一下再关闭浏览器，让用户看到结果
    await page.waitForTimeout(3000);
    await browser.close();
  }
}

advancedConsoleMonitor().catch(console.error);