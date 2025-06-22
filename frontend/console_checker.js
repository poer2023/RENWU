const puppeteer = require('puppeteer');

async function checkConsoleErrors() {
  const browser = await puppeteer.launch({
    headless: false,
    devtools: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // 收集控制台消息
  const consoleMessages = [];
  const errors = [];
  const warnings = [];
  
  page.on('console', msg => {
    const message = {
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    };
    
    consoleMessages.push(message);
    
    if (msg.type() === 'error') {
      errors.push(message);
    } else if (msg.type() === 'warning') {
      warnings.push(message);
    }
    
    console.log(`${msg.type().toUpperCase()}: ${msg.text()}`);
    if (msg.location()) {
      console.log(`  at ${msg.location().url}:${msg.location().lineNumber}:${msg.location().columnNumber}`);
    }
  });
  
  // 监听页面错误
  page.on('pageerror', error => {
    console.log('PAGE ERROR:', error.message);
    errors.push({
      type: 'pageerror',
      text: error.message,
      stack: error.stack
    });
  });
  
  // 监听网络请求失败
  page.on('requestfailed', request => {
    console.log('REQUEST FAILED:', request.url(), request.failure().errorText);
  });
  
  try {
    console.log('正在访问 http://localhost:3000...');
    await page.goto('http://localhost:3000', { 
      waitUntil: 'networkidle2', 
      timeout: 30000 
    });
    
    console.log('页面加载完成，等待2秒以收集更多日志...');
    await page.waitForTimeout(2000);
    
    // 尝试获取页面标题
    const title = await page.title();
    console.log('页面标题:', title);
    
    // 检查页面是否正常渲染
    const bodyText = await page.evaluate(() => document.body.innerText);
    console.log('页面是否包含内容:', bodyText.length > 0 ? '是' : '否');
    
    // 检查是否有Vue应用挂载
    const hasVueApp = await page.evaluate(() => {
      return document.querySelector('#app') !== null;
    });
    console.log('Vue应用是否存在:', hasVueApp ? '是' : '否');
    
    // 检查是否有特定的Vue组件
    const hasTasks = await page.evaluate(() => {
      return document.querySelector('.task-card') !== null;
    });
    console.log('是否有任务卡片:', hasTasks ? '是' : '否');
    
  } catch (error) {
    console.log('访问页面时出错:', error.message);
    errors.push({
      type: 'navigation',
      text: error.message
    });
  }
  
  console.log('\n=== 错误统计 ===');
  console.log(`总错误数: ${errors.length}`);
  console.log(`总警告数: ${warnings.length}`);
  console.log(`总控制台消息数: ${consoleMessages.length}`);
  
  if (errors.length > 0) {
    console.log('\n=== 详细错误信息 ===');
    errors.forEach((error, index) => {
      console.log(`错误 ${index + 1}:`);
      console.log(`  类型: ${error.type}`);
      console.log(`  信息: ${error.text}`);
      if (error.location) {
        console.log(`  位置: ${error.location.url}:${error.location.lineNumber}:${error.location.columnNumber}`);
      }
      if (error.stack) {
        console.log(`  堆栈: ${error.stack}`);
      }
      console.log('');
    });
  }
  
  if (warnings.length > 0) {
    console.log('\n=== 详细警告信息 ===');
    warnings.forEach((warning, index) => {
      console.log(`警告 ${index + 1}:`);
      console.log(`  信息: ${warning.text}`);
      if (warning.location) {
        console.log(`  位置: ${warning.location.url}:${warning.location.lineNumber}:${warning.location.columnNumber}`);
      }
      console.log('');
    });
  }
  
  // 保持浏览器打开10秒以便手动检查
  console.log('\n浏览器将保持打开10秒，请手动检查页面...');
  await page.waitForTimeout(10000);
  
  await browser.close();
  
  return {
    errors,
    warnings,
    consoleMessages
  };
}

checkConsoleErrors().catch(console.error);