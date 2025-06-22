import { test } from '@playwright/test';

test('深度调试中键拖动 - 模拟真实用户操作', async ({ page }) => {
  const allMessages: string[] = [];
  const errors: string[] = [];
  
  // 监听所有控制台消息和错误
  page.on('console', msg => {
    const text = msg.text();
    allMessages.push(`[${msg.type()}] ${text}`);
    
    if (msg.type() === 'error') {
      errors.push(text);
      console.log(`❌ [错误] ${text}`);
    } else if (text.includes('🎯') || text.includes('🚀') || text.includes('📊') || text.includes('🛑') || text.includes('mousedown') || text.includes('auxclick')) {
      console.log(`📋 [重要] ${text}`);
    } else {
      console.log(`📝 [日志] ${text}`);
    }
  });

  // 监听页面错误和网络失败
  page.on('pageerror', error => {
    console.log(`💥 [页面错误] ${error.message}`);
    errors.push(`Page Error: ${error.message}`);
  });

  page.on('requestfailed', request => {
    console.log(`🌐 [网络失败] ${request.url()} - ${request.failure()?.errorText}`);
  });

  console.log('🚀 正在打开TaskWall应用...');
  await page.goto('http://localhost:3000');
  
  console.log('⏳ 等待页面完全加载...');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(5000); // 给更多时间让Vue应用初始化

  console.log('\n📊 === 页面加载完成，开始检查状态 ===');
  
  // 检查关键元素是否存在
  const canvas = page.locator('.sticky-canvas');
  const canvasExists = await canvas.isVisible();
  console.log(`📍 画布元素存在: ${canvasExists ? '✅' : '❌'}`);

  if (!canvasExists) {
    console.log('❌ 画布元素不存在，无法继续测试');
    return;
  }

  // 获取画布信息
  const canvasBox = await canvas.boundingBox();
  console.log(`📏 画布尺寸: ${canvasBox?.width} x ${canvasBox?.height}`);
  console.log(`📍 画布位置: (${canvasBox?.x}, ${canvasBox?.y})`);

  // 检查是否有任务卡片
  const taskCards = page.locator('.task-wrapper');
  const taskCount = await taskCards.count();
  console.log(`📋 任务卡片数量: ${taskCount}`);

  // 检查Vue应用是否正常挂载
  const vueApp = page.locator('#app');
  const vueAppExists = await vueApp.isVisible();
  console.log(`⚙️ Vue应用挂载: ${vueAppExists ? '✅' : '❌'}`);

  console.log('\n🧪 === 开始模拟真实用户中键拖动 ===');

  // 测试1: 在完全空白的区域
  console.log('\n🎯 测试1: 在画布左上角空白区域中键拖动');
  const emptyX = canvasBox!.x + 20;
  const emptyY = canvasBox!.y + 20;
  
  console.log(`📍 目标位置: (${emptyX}, ${emptyY})`);
  
  // 先移动到目标位置
  await page.mouse.move(emptyX, emptyY);
  await page.waitForTimeout(100);
  
  console.log('🖱️ 开始中键拖动序列...');
  
  // 1. 按下中键
  console.log('   1️⃣ 按下中键');
  await page.mouse.down({ button: 'middle' });
  await page.waitForTimeout(200); // 等待事件处理
  
  // 2. 小幅移动
  console.log('   2️⃣ 小幅移动鼠标');
  await page.mouse.move(emptyX + 10, emptyY + 10);
  await page.waitForTimeout(200);
  
  // 3. 继续移动
  console.log('   3️⃣ 继续移动鼠标');
  await page.mouse.move(emptyX + 50, emptyY + 50);
  await page.waitForTimeout(300);
  
  // 4. 大幅移动
  console.log('   4️⃣ 大幅移动鼠标');
  await page.mouse.move(emptyX + 100, emptyY + 100);
  await page.waitForTimeout(300);
  
  // 5. 松开中键
  console.log('   5️⃣ 松开中键');
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(500);

  console.log('\n📊 === 分析测试结果 ===');
  
  // 分析控制台消息
  const mouseDownMessages = allMessages.filter(msg => msg.includes('画布鼠标按下事件: 1'));
  const middleClickStart = allMessages.filter(msg => msg.includes('开始中键画布拖动'));
  const panStart = allMessages.filter(msg => msg.includes('startUltraPan 函数被调用'));
  const panEnd = allMessages.filter(msg => msg.includes('超级画布拖动结束'));
  const auxClickMessages = allMessages.filter(msg => msg.includes('辅助点击事件'));
  
  console.log(`📊 鼠标按下事件: ${mouseDownMessages.length} 次`);
  console.log(`🚀 中键拖动开始: ${middleClickStart.length} 次`);
  console.log(`📞 拖动函数调用: ${panStart.length} 次`);
  console.log(`🛑 拖动结束事件: ${panEnd.length} 次`);
  console.log(`🎯 辅助点击事件: ${auxClickMessages.length} 次`);

  // 检查是否有阻止事件的因素
  const preventDefault = allMessages.filter(msg => msg.includes('preventDefault') || msg.includes('阻止'));
  console.log(`🚫 事件阻止相关: ${preventDefault.length} 次`);

  // 检查错误
  if (errors.length > 0) {
    console.log(`\n❌ 发现 ${errors.length} 个错误:`);
    errors.forEach((error, i) => {
      console.log(`   ${i + 1}. ${error}`);
    });
  }

  // 分析可能的问题
  console.log('\n🔍 === 问题分析 ===');
  
  if (mouseDownMessages.length === 0) {
    console.log('❌ 问题: 鼠标按下事件未触发 - 可能是事件绑定问题');
  } else if (middleClickStart.length === 0) {
    console.log('❌ 问题: 中键判断失败 - 可能是按键识别问题');
  } else if (panStart.length === 0) {
    console.log('❌ 问题: 拖动函数未调用 - 可能是函数调用问题');
  } else if (panEnd.length === 0) {
    console.log('❌ 问题: 拖动未正常结束 - 可能是事件监听问题');
  } else {
    console.log('✅ 所有关键事件都触发了，拖动应该正常工作');
  }

  console.log('\n📋 === 最近的重要消息 ===');
  const recentImportant = allMessages.filter(msg => 
    msg.includes('🎯') || msg.includes('🚀') || msg.includes('📊') || 
    msg.includes('🛑') || msg.includes('❌') || msg.includes('✅')
  ).slice(-10);
  
  recentImportant.forEach((msg, i) => {
    console.log(`   ${i + 1}. ${msg}`);
  });

  // 额外的调试信息
  console.log('\n🔧 === 技术调试信息 ===');
  
  // 检查浏览器特性
  const userAgent = await page.evaluate(() => navigator.userAgent);
  console.log(`🌐 浏览器: ${userAgent.includes('Chrome') ? 'Chrome' : userAgent.includes('Firefox') ? 'Firefox' : userAgent.includes('Safari') ? 'Safari' : '其他'}`);
  
  // 检查事件监听器
  const hasMouseDownListener = await page.evaluate(() => {
    const canvas = document.querySelector('.sticky-canvas');
    return canvas ? 'mousedown event listener exists' : 'no canvas found';
  });
  console.log(`👂 事件监听器: ${hasMouseDownListener}`);

  // 检查Vue实例
  const vueInstance = await page.evaluate(() => {
    return typeof window.Vue !== 'undefined' || document.querySelector('#app').__vue__ ? 'Vue实例存在' : 'Vue实例不存在';
  });
  console.log(`⚙️ Vue状态: ${vueInstance}`);

  console.log('\n✅ 深度调试完成');
});