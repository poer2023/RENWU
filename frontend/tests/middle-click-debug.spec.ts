import { test, expect } from '@playwright/test';

test('中键拖动功能调试 - 检查控制台错误', async ({ page }) => {
  // 收集控制台消息
  const consoleMessages: string[] = [];
  const consoleErrors: string[] = [];
  
  page.on('console', msg => {
    const text = msg.text();
    consoleMessages.push(`[${msg.type()}] ${text}`);
    
    if (msg.type() === 'error') {
      consoleErrors.push(text);
    }
    
    // 打印所有控制台消息到测试输出
    console.log(`[Browser Console ${msg.type()}] ${text}`);
  });

  // 监听页面错误
  page.on('pageerror', error => {
    console.log(`[Page Error] ${error.message}`);
    console.log(`[Stack] ${error.stack}`);
  });

  // 访问应用
  console.log('🚀 导航到 TaskWall 应用...');
  await page.goto('http://localhost:3000');

  // 等待页面加载
  console.log('⏳ 等待页面加载...');
  await page.waitForLoadState('networkidle');
  
  // 等待一点时间让Vue应用初始化
  await page.waitForTimeout(3000);

  // 查找画布元素
  console.log('🔍 查找画布元素...');
  const canvas = page.locator('.sticky-canvas');
  await expect(canvas).toBeVisible();

  // 获取画布位置
  const canvasBox = await canvas.boundingBox();
  if (!canvasBox) {
    throw new Error('无法获取画布位置');
  }

  console.log('📏 画布位置信息:', canvasBox);

  // 计算画布中心点
  const centerX = canvasBox.x + canvasBox.width / 2;
  const centerY = canvasBox.y + canvasBox.height / 2;

  console.log('🎯 画布中心点:', { x: centerX, y: centerY });

  // 首先检查是否有初始化错误
  console.log('📊 当前控制台消息数量:', consoleMessages.length);
  console.log('❌ 当前控制台错误数量:', consoleErrors.length);

  if (consoleErrors.length > 0) {
    console.log('🚨 发现控制台错误:');
    consoleErrors.forEach((error, index) => {
      console.log(`   ${index + 1}. ${error}`);
    });
  }

  // 测试鼠标移动到画布中心
  console.log('🖱️ 移动鼠标到画布中心...');
  await page.mouse.move(centerX, centerY);

  // 等待一下
  await page.waitForTimeout(500);

  // 模拟中键按下
  console.log('🖱️ 按下鼠标中键...');
  await page.mouse.down({ button: 'middle' });

  // 等待事件处理
  await page.waitForTimeout(200);

  // 检查是否有新的控制台消息
  console.log('📊 中键按下后的控制台消息数量:', consoleMessages.length);

  // 拖动鼠标
  console.log('🖱️ 拖动鼠标...');
  await page.mouse.move(centerX + 100, centerY + 100, { steps: 5 });

  // 等待拖动过程
  await page.waitForTimeout(500);

  // 松开中键
  console.log('🖱️ 松开鼠标中键...');
  await page.mouse.up({ button: 'middle' });

  // 等待一下
  await page.waitForTimeout(1000);

  // 打印所有控制台消息
  console.log('📋 完整的控制台消息列表:');
  consoleMessages.forEach((msg, index) => {
    console.log(`   ${index + 1}. ${msg}`);
  });

  // 检查是否看到了预期的日志
  const hasMouseDownLog = consoleMessages.some(msg => 
    msg.includes('画布鼠标按下事件') && msg.includes('1')
  );
  
  const hasMiddleClickLog = consoleMessages.some(msg => 
    msg.includes('开始中键画布拖动')
  );

  const hasStartPanLog = consoleMessages.some(msg => 
    msg.includes('startUltraPan 函数被调用')
  );

  console.log('🔍 关键日志检查:');
  console.log(`   📍 鼠标按下事件日志: ${hasMouseDownLog ? '✅' : '❌'}`);
  console.log(`   🚀 中键拖动开始日志: ${hasMiddleClickLog ? '✅' : '❌'}`);
  console.log(`   📞 拖动函数调用日志: ${hasStartPanLog ? '✅' : '❌'}`);

  // 检查特定的错误类型
  const hasVueErrors = consoleErrors.some(error => error.includes('Vue'));
  const hasJSErrors = consoleErrors.some(error => error.includes('TypeError') || error.includes('ReferenceError'));
  const hasNetworkErrors = consoleErrors.some(error => error.includes('Failed to fetch') || error.includes('404'));

  console.log('🔍 错误类型分析:');
  console.log(`   📦 Vue相关错误: ${hasVueErrors ? '❌ 有' : '✅ 无'}`);
  console.log(`   🔧 JavaScript错误: ${hasJSErrors ? '❌ 有' : '✅ 无'}`);
  console.log(`   🌐 网络请求错误: ${hasNetworkErrors ? '❌ 有' : '✅ 无'}`);

  // 如果有错误，记录详细信息
  if (consoleErrors.length > 0) {
    console.log('🚨 详细错误信息:');
    consoleErrors.forEach((error, index) => {
      console.log(`\n❌ 错误 ${index + 1}:`);
      console.log(`   ${error}`);
    });
  }

  // 最后的诊断
  console.log('\n🏥 诊断总结:');
  if (consoleErrors.length === 0 && hasMouseDownLog && hasMiddleClickLog && hasStartPanLog) {
    console.log('✅ 功能应该正常工作 - 所有事件都被正确触发');
  } else if (consoleErrors.length > 0) {
    console.log('❌ 发现错误 - 需要修复控制台错误');
  } else if (!hasMouseDownLog) {
    console.log('❌ 鼠标事件未被触发 - 可能是事件绑定问题');
  } else if (!hasMiddleClickLog) {
    console.log('❌ 中键事件未被识别 - 可能是事件处理逻辑问题');
  } else if (!hasStartPanLog) {
    console.log('❌ 拖动函数未被调用 - 可能是函数调用问题');
  } else {
    console.log('🤔 功能可能有其他问题 - 需要进一步调试');
  }
});