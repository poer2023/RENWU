import { test, expect } from '@playwright/test';

test.describe('烟雾测试 - 基本功能验证', () => {
  test('应用基本加载测试', async ({ page }) => {
    // 设置超时时间
    test.setTimeout(60000);
    
    console.log('开始访问应用...');
    
    // 访问首页
    await page.goto('/', { waitUntil: 'networkidle', timeout: 30000 });
    
    console.log('页面已加载，检查基本元素...');
    
    // 检查页面标题
    const title = await page.title();
    console.log('页面标题:', title);
    expect(title).toBeTruthy();
    
    // 检查主要容器
    const appContainer = page.locator('#app').first();
    await expect(appContainer).toBeVisible({ timeout: 10000 });
    console.log('✓ App容器已加载');
    
    // 检查画布元素
    const canvas = page.locator('.sticky-canvas');
    await expect(canvas).toBeVisible({ timeout: 10000 });
    console.log('✓ 画布已加载');
    
    // 等待任何异步加载完成
    await page.waitForTimeout(2000);
    
    // 检查是否有明显的错误
    const errorElements = page.locator('.error, [role="alert"]');
    const errorCount = await errorElements.count();
    
    if (errorCount > 0) {
      const errorTexts = await errorElements.allTextContents();
      console.warn('发现错误元素:', errorTexts);
    }
    
    expect(errorCount).toBe(0);
    console.log('✓ 无错误提示');
    
    console.log('烟雾测试完成 - 应用基本功能正常');
  });

  test('API连接测试', async ({ page, request }) => {
    console.log('测试API连接...');
    
    // 直接测试API端点
    try {
      const response = await request.get('http://localhost:8000/health');
      expect(response.status()).toBe(200);
      console.log('✓ 后端API连接正常');
    } catch (error) {
      console.error('❌ 后端API连接失败:', error);
      throw error;
    }
    
    // 测试前端页面
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 监听网络请求
    const apiRequests: string[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push(request.url());
        console.log('API请求:', request.url());
      }
    });
    
    // 刷新页面触发API调用
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    console.log('捕获到的API请求:', apiRequests);
    
    // 应该至少有一些API请求
    expect(apiRequests.length).toBeGreaterThan(0);
    console.log('✓ 前端API调用正常');
  });

  test('基本交互测试', async ({ page }) => {
    console.log('测试基本交互功能...');
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 等待画布加载
    const canvas = page.locator('.sticky-canvas');
    await expect(canvas).toBeVisible();
    
    // 测试画布点击
    await canvas.click();
    console.log('✓ 画布可点击');
    
    // 测试鼠标移动
    await canvas.hover();
    console.log('✓ 鼠标悬停正常');
    
    // 测试键盘事件
    await page.keyboard.press('Tab');
    console.log('✓ 键盘事件正常');
    
    // 检查是否有任务卡片（可能为空）
    const taskCards = page.locator('.task-card');
    const taskCount = await taskCards.count();
    console.log(`发现 ${taskCount} 个任务卡片`);
    
    console.log('✓ 基本交互测试完成');
  });

  test('响应式布局测试', async ({ page }) => {
    console.log('测试响应式布局...');
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 测试不同视口尺寸
    const viewports = [
      { width: 1920, height: 1080, name: '桌面大屏' },
      { width: 1366, height: 768, name: '桌面中等' },
      { width: 768, height: 1024, name: '平板' },
      { width: 375, height: 667, name: '手机' }
    ];
    
    for (const viewport of viewports) {
      console.log(`测试 ${viewport.name} (${viewport.width}x${viewport.height})`);
      
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.waitForTimeout(1000);
      
      // 检查主要元素是否仍然可见
      await expect(page.locator('.sticky-canvas')).toBeVisible();
      
      console.log(`✓ ${viewport.name} 布局正常`);
    }
    
    // 恢复默认视口
    await page.setViewportSize({ width: 1200, height: 800 });
    console.log('✓ 响应式布局测试完成');
  });
});