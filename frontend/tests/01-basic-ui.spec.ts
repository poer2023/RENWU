import { test, expect } from '@playwright/test';

test.describe('TaskWall 基础UI测试', () => {
  test.beforeEach(async ({ page }) => {
    // 等待页面加载
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('页面标题和基本元素加载', async ({ page }) => {
    // 检查页面标题
    await expect(page).toHaveTitle(/TaskWall/);
    
    // 检查主要布局元素
    await expect(page.locator('#app').first()).toBeVisible();
    await expect(page.locator('.sticky-canvas')).toBeVisible();
    
    // 检查顶部导航栏
    const topBar = page.locator('.top-bar, .header, nav').first();
    if (await topBar.count() > 0) {
      await expect(topBar).toBeVisible();
    }
  });

  test('响应式设计测试', async ({ page }) => {
    // 测试桌面视图
    await page.setViewportSize({ width: 1200, height: 800 });
    await expect(page.locator('.sticky-canvas')).toBeVisible();
    
    // 测试平板视图
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);
    await expect(page.locator('.sticky-canvas')).toBeVisible();
    
    // 测试移动设备视图
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);
    await expect(page.locator('.sticky-canvas')).toBeVisible();
  });

  test('加载状态和错误处理', async ({ page }) => {
    // 检查是否有加载指示器
    const loadingIndicator = page.locator('.loading, .spinner, [data-testid="loading"]');
    if (await loadingIndicator.count() > 0) {
      // 等待加载完成
      await expect(loadingIndicator).toHaveCount(0, { timeout: 10000 });
    }
    
    // 检查是否有错误消息
    const errorMessage = page.locator('.error, .alert-error, [role="alert"]');
    await expect(errorMessage).toHaveCount(0);
  });

  test('网络请求和API连接', async ({ page }) => {
    // 监听网络请求
    const apiRequests: string[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push(request.url());
      }
    });
    
    // 刷新页面触发API调用
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // 检查是否有API请求
    expect(apiRequests.length).toBeGreaterThan(0);
    
    // 检查是否请求了任务数据
    const hasTasksRequest = apiRequests.some(url => url.includes('/tasks'));
    expect(hasTasksRequest).toBeTruthy();
  });
});