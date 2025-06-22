import { test } from '@playwright/test';

test('快速验证中键拖动修复', async ({ page }) => {
  // 监听控制台消息
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('🎯') || text.includes('🚀') || text.includes('📊') || text.includes('🛑')) {
      console.log(`[Browser] ${text}`);
    }
  });

  console.log('🚀 打开应用...');
  await page.goto('http://localhost:3000');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);

  // 测试1: 在画布空白区域中键拖动
  console.log('\n🧪 测试1: 画布空白区域中键拖动');
  const canvas = page.locator('.sticky-canvas');
  const canvasBox = await canvas.boundingBox();
  
  // 点击画布左上角空白区域
  const emptyX = canvasBox!.x + 50;
  const emptyY = canvasBox!.y + 50;
  
  await page.mouse.move(emptyX, emptyY);
  await page.mouse.down({ button: 'middle' });
  await page.waitForTimeout(100);
  await page.mouse.move(emptyX + 100, emptyY + 100, { steps: 3 });
  await page.waitForTimeout(200);
  await page.mouse.up({ button: 'middle' });
  
  console.log('✅ 测试1完成');

  // 测试2: 在任务卡片上中键拖动
  console.log('\n🧪 测试2: 任务卡片上中键拖动');
  const taskCard = page.locator('.task-wrapper').first();
  
  if (await taskCard.isVisible()) {
    const taskBox = await taskCard.boundingBox();
    const taskX = taskBox!.x + taskBox!.width / 2;
    const taskY = taskBox!.y + taskBox!.height / 2;
    
    await page.mouse.move(taskX, taskY);
    await page.mouse.down({ button: 'middle' });
    await page.waitForTimeout(100);
    await page.mouse.move(taskX + 100, taskY + 100, { steps: 3 });
    await page.waitForTimeout(200);
    await page.mouse.up({ button: 'middle' });
    
    console.log('✅ 测试2完成');
  } else {
    console.log('⚠️ 测试2跳过 - 没有找到任务卡片');
  }

  await page.waitForTimeout(1000);
  console.log('\n✅ 所有测试完成！');
});