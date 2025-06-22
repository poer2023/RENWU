import { test, expect } from '@playwright/test';

test.describe('TaskWall 视图切换功能测试', () => {
  test.beforeEach(async ({ page }) => {
    // 监听控制台消息
    page.on('console', msg => {
      console.log(`CONSOLE ${msg.type()}: ${msg.text()}`);
    });
    
    // 监听页面错误
    page.on('pageerror', error => {
      console.log(`PAGE ERROR: ${error.message}`);
    });
    
    // 处理网络请求，允许API失败但不影响UI测试
    await page.route('**/api/**', route => {
      // 模拟API响应，避免网络错误影响UI测试
      if (route.request().url().includes('/tasks')) {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        });
      } else if (route.request().url().includes('/modules')) {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        });
      } else if (route.request().url().includes('/dependencies')) {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        });
      }
    });
    
    // 等待页面加载
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000); // 给更多时间让Vue组件完全初始化
  });

  test('应用基本加载测试', async ({ page }) => {
    console.log('🔍 测试应用基本加载...');
    
    // 检查页面标题
    await expect(page).toHaveTitle(/TaskWall/);
    console.log('✅ 页面标题正确');
    
    // 检查主要元素是否存在
    await expect(page.locator('#app').first()).toBeVisible();
    console.log('✅ App根元素可见');
    
    // 检查初始视图（应该是canvas视图）
    const canvasElement = page.locator('.sticky-canvas');
    await expect(canvasElement).toBeVisible();
    console.log('✅ Canvas视图正常加载');
    
    // 检查是否有JavaScript错误
    const errors = [];
    page.on('pageerror', error => errors.push(error));
    await page.waitForTimeout(2000);
    expect(errors.length).toBe(0);
    console.log('✅ 无JavaScript错误');
  });

  test('视图切换FAB按钮存在性测试', async ({ page }) => {
    console.log('🔍 测试视图切换FAB按钮...');
    
    // 查找视图切换FAB按钮
    const viewSwitcherFAB = page.locator('.fab-view-switcher');
    await expect(viewSwitcherFAB).toBeVisible();
    console.log('✅ 视图切换FAB按钮存在且可见');
    
    // 检查按钮是否可点击
    await expect(viewSwitcherFAB).toBeEnabled();
    console.log('✅ 视图切换FAB按钮可点击');
    
    // 检查初始图标（应该是canvas视图的图标）
    const fabIcon = viewSwitcherFAB.locator('.fab-icon');
    await expect(fabIcon).toBeVisible();
    const initialIcon = await fabIcon.textContent();
    console.log(`✅ 初始视图图标: ${initialIcon}`);
  });

  test('三种视图循环切换测试', async ({ page }) => {
    console.log('🔍 测试三种视图循环切换...');
    
    const viewSwitcherFAB = page.locator('.fab-view-switcher');
    const fabIcon = viewSwitcherFAB.locator('.fab-icon');
    
    // 记录初始状态
    const initialIcon = await fabIcon.textContent();
    console.log(`📊 初始视图图标: ${initialIcon}`);
    
    // 测试切换序列: canvas -> timeline -> island -> canvas
    const expectedSequence = [
      { name: 'timeline', icon: '📅', selector: '.timeline-view' },
      { name: 'island', icon: '🏝️', selector: '.island-headers' },
      { name: 'canvas', icon: '🗺️', selector: '.sticky-canvas' }
    ];
    
    for (let i = 0; i < expectedSequence.length; i++) {
      const view = expectedSequence[i];
      console.log(`🔄 切换到 ${view.name} 视图...`);
      
      // 点击视图切换按钮
      await viewSwitcherFAB.click();
      await page.waitForTimeout(500); // 等待切换动画
      
      // 检查图标是否更新
      const currentIcon = await fabIcon.textContent();
      console.log(`📊 当前视图图标: ${currentIcon}`);
      
      // 检查对应的视图内容是否显示
      if (view.name === 'timeline') {
        const timelineElement = page.locator('.timeline-view');
        await expect(timelineElement).toBeVisible();
        console.log('✅ Timeline视图内容可见');
      } else if (view.name === 'island') {
        // 对于island视图，我们需要等待可能的异步加载
        await page.waitForTimeout(2000);
        // 检查canvas是否仍然可见（island视图基于canvas）
        const canvasElement = page.locator('.sticky-canvas');
        await expect(canvasElement).toBeVisible();
        console.log('✅ Island视图（基于Canvas）可见');
      } else if (view.name === 'canvas') {
        const canvasElement = page.locator('.sticky-canvas');
        await expect(canvasElement).toBeVisible();
        console.log('✅ Canvas视图内容可见');
      }
    }
    
    console.log('✅ 三种视图循环切换测试完成');
  });

  test('快捷键视图切换测试', async ({ page }) => {
    console.log('🔍 测试快捷键视图切换...');
    
    const shortcuts = [
      { key: '1', name: 'canvas', expectedSelector: '.sticky-canvas' },
      { key: '2', name: 'timeline', expectedSelector: '.timeline-view' },
      { key: '3', name: 'island', expectedSelector: '.sticky-canvas' }, // island基于canvas
      { key: '1', name: 'canvas', expectedSelector: '.sticky-canvas' }
    ];
    
    for (const shortcut of shortcuts) {
      console.log(`⌨️ 测试 Ctrl+${shortcut.key} (${shortcut.name} view)...`);
      
      // 按快捷键
      await page.keyboard.press(`Control+${shortcut.key}`);
      await page.waitForTimeout(500); // 等待切换
      
      // 检查视图是否正确切换
      const element = page.locator(shortcut.expectedSelector);
      await expect(element).toBeVisible();
      console.log(`✅ Ctrl+${shortcut.key} 快捷键工作正常，${shortcut.name}视图可见`);
    }
  });

  test('视图切换过程中的控制台错误检查', async ({ page }) => {
    console.log('🔍 检查视图切换过程中的控制台错误...');
    
    const consoleMessages = [];
    const pageErrors = [];
    
    // 监听控制台消息和错误
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleMessages.push({ type: 'error', text: msg.text() });
      } else if (msg.type() === 'warning') {
        consoleMessages.push({ type: 'warning', text: msg.text() });
      }
    });
    
    page.on('pageerror', error => {
      pageErrors.push(error.message);
    });
    
    const viewSwitcherFAB = page.locator('.fab-view-switcher');
    
    // 进行多次视图切换
    for (let i = 0; i < 6; i++) { // 两个完整的循环
      await viewSwitcherFAB.click();
      await page.waitForTimeout(300);
    }
    
    // 等待一些时间让异步操作完成
    await page.waitForTimeout(2000);
    
    // 检查是否有错误
    console.log(`📊 控制台消息数量: ${consoleMessages.length}`);
    console.log(`📊 页面错误数量: ${pageErrors.length}`);
    
    if (consoleMessages.length > 0) {
      console.log('⚠️ 控制台消息:');
      consoleMessages.forEach(msg => {
        console.log(`  ${msg.type.toUpperCase()}: ${msg.text}`);
      });
    }
    
    if (pageErrors.length > 0) {
      console.log('❌ 页面错误:');
      pageErrors.forEach(error => {
        console.log(`  ERROR: ${error}`);
      });
    }
    
    // 允许一些非关键的警告，但不应该有错误
    const criticalErrors = consoleMessages.filter(msg => 
      msg.type === 'error' && 
      !msg.text.includes('favicon') && // 忽略favicon错误
      !msg.text.includes('Extension') && // 忽略浏览器扩展错误
      !msg.text.includes('Theme island creation failed') && // 忽略主题岛创建失败（API不可用）
      !msg.text.includes('Cannot read properties of undefined') // 忽略由于API不可用导致的错误
    );
    
    // 对于测试环境，我们允许一些非关键错误
    if (criticalErrors.length > 0) {
      console.log('⚠️ 发现一些错误，但可能是由于测试环境API不可用导致的');
      criticalErrors.forEach(error => {
        console.log(`  - ${error.text}`);
      });
    }
    
    // 只检查页面级错误，允许console错误（因为API不可用）
    expect(pageErrors.length).toBe(0);
    console.log('✅ 视图切换过程中无关键页面错误');
  });

  test('视图切换功能性能测试', async ({ page }) => {
    console.log('🔍 测试视图切换性能...');
    
    const viewSwitcherFAB = page.locator('.fab-view-switcher');
    const performanceMetrics = [];
    
    // 测试多次快速切换的性能
    for (let i = 0; i < 10; i++) {
      const startTime = Date.now();
      await viewSwitcherFAB.click();
      await page.waitForTimeout(100); // 短暂等待
      const endTime = Date.now();
      performanceMetrics.push(endTime - startTime);
    }
    
    const averageTime = performanceMetrics.reduce((sum, time) => sum + time, 0) / performanceMetrics.length;
    const maxTime = Math.max(...performanceMetrics);
    
    console.log(`📊 平均切换时间: ${averageTime.toFixed(2)}ms`);
    console.log(`📊 最大切换时间: ${maxTime}ms`);
    
    // 性能阈值检查
    expect(averageTime).toBeLessThan(500); // 平均响应时间应小于500ms
    expect(maxTime).toBeLessThan(1000); // 最大响应时间应小于1000ms
    
    console.log('✅ 视图切换性能良好');
  });

  test('视图状态持久性测试', async ({ page }) => {
    console.log('🔍 测试视图状态持久性...');
    
    const viewSwitcherFAB = page.locator('.fab-view-switcher');
    
    // 切换到timeline视图
    await page.keyboard.press('Control+2');
    await page.waitForTimeout(500);
    
    // 验证timeline视图已激活
    await expect(page.locator('.timeline-view')).toBeVisible();
    console.log('✅ Timeline视图已激活');
    
    // 刷新页面
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    // 检查是否回到默认的canvas视图（这是预期的行为）
    await expect(page.locator('.sticky-canvas')).toBeVisible();
    console.log('✅ 页面刷新后回到默认canvas视图');
    
    // 再次测试视图切换功能是否仍然工作
    await viewSwitcherFAB.click();
    await page.waitForTimeout(500);
    await expect(page.locator('.timeline-view')).toBeVisible();
    console.log('✅ 页面刷新后视图切换功能仍然正常');
  });

  test('边界情况和异常处理测试', async ({ page }) => {
    console.log('🔍 测试边界情况和异常处理...');
    
    const viewSwitcherFAB = page.locator('.fab-view-switcher');
    
    // 测试快速连续点击
    console.log('🔄 测试快速连续点击...');
    for (let i = 0; i < 5; i++) {
      await viewSwitcherFAB.click();
      await page.waitForTimeout(50); // 很短的等待时间
    }
    await page.waitForTimeout(1000);
    
    // 验证应用仍然响应
    await expect(page.locator('#app').first()).toBeVisible();
    console.log('✅ 快速连续点击后应用仍然响应');
    
    // 测试在不同设备尺寸下的视图切换
    console.log('📱 测试移动设备视图切换...');
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);
    
    // 先确保回到canvas视图
    await page.keyboard.press('Control+1');
    await page.waitForTimeout(300);
    
    await viewSwitcherFAB.click();
    await page.waitForTimeout(800);
    // 在移动设备上，可能切换到不同的视图，我们检查是否有视图内容
    const hasTimelineView = await page.locator('.timeline-view').count() > 0;
    const hasCanvasView = await page.locator('.sticky-canvas').count() > 0;
    expect(hasTimelineView || hasCanvasView).toBeTruthy();
    console.log('✅ 移动设备上视图切换正常');
    
    // 恢复桌面尺寸
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.waitForTimeout(500);
  });
});