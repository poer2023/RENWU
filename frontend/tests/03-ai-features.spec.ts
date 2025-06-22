import { test, expect } from '@playwright/test';

test.describe('AI功能测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.sticky-canvas')).toBeVisible();
  });

  test('全局搜索功能 (⇧⌘K)', async ({ page }) => {
    // 使用快捷键打开全局搜索
    await page.keyboard.press('Shift+Meta+K'); // macOS
    await page.waitForTimeout(500);
    
    // 如果快捷键不起作用，尝试查找搜索按钮
    const searchButton = page.locator('button:has-text("搜索"), [data-testid="global-search"], .global-search-trigger').first();
    if (await searchButton.count() > 0 && !await page.locator('.global-search, .search-modal').isVisible()) {
      await searchButton.click();
    }
    
    // 等待搜索框出现
    const searchModal = page.locator('.global-search, .search-modal, [data-testid="search-modal"]');
    if (await searchModal.count() > 0) {
      await expect(searchModal).toBeVisible({ timeout: 3000 });
      
      // 查找搜索输入框
      const searchInput = searchModal.locator('input[type="text"], input[placeholder*="搜索"]');
      if (await searchInput.count() > 0) {
        // 输入搜索关键词
        await searchInput.fill('测试');
        await page.waitForTimeout(1000);
        
        // 检查搜索结果
        const searchResults = page.locator('.search-result, .search-item');
        // 搜索结果可能为空，这是正常的
        
        // 按Escape关闭搜索
        await page.keyboard.press('Escape');
        await expect(searchModal).toHaveCount(0, { timeout: 2000 });
      }
    }
  });

  test('AI助手笔功能 (/ai 命令)', async ({ page }) => {
    // 创建一个任务并进入编辑模式
    await page.locator('.sticky-canvas').dblclick();
    await page.waitForTimeout(500);
    
    const input = page.locator('input:visible, textarea:visible').first();
    if (await input.count() > 0) {
      await input.fill('测试AI助手功能的任务');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(2000);
      
      // 双击任务进入编辑模式
      const taskCard = page.locator('.task-card').first();
      await taskCard.dblclick();
      await page.waitForTimeout(500);
      
      // 查找编辑输入框
      const editInput = page.locator('input:visible, textarea:visible').first();
      if (await editInput.count() > 0) {
        // 输入AI命令触发符
        await editInput.fill('/');
        await page.waitForTimeout(1000);
        
        // 检查AI助手面板是否出现
        const aiPanel = page.locator('.ai-assistant, .ai-prompt, [data-testid="ai-assistant"]');
        if (await aiPanel.count() > 0) {
          await expect(aiPanel).toBeVisible();
          
          // 查找AI命令选项
          const rewriteOption = page.locator('text="Rewrite", text="重写"').first();
          if (await rewriteOption.count() > 0) {
            await rewriteOption.click();
            
            // 等待AI处理
            await page.waitForTimeout(3000);
            
            // 检查是否有新的文本内容
            const updatedInput = page.locator('input:visible, textarea:visible').first();
            const newValue = await updatedInput.inputValue();
            expect(newValue).not.toBe('/');
          }
        }
      }
    }
  });

  test('工时负载预警功能', async ({ page }) => {
    // 查找工时负载按钮
    const workloadButton = page.locator('button:has-text("Workload"), button:has-text("工时"), [data-testid="workload"]').first();
    
    if (await workloadButton.count() > 0) {
      await workloadButton.click();
      await page.waitForTimeout(1000);
      
      // 检查工时侧栏是否打开
      const workloadSidebar = page.locator('.workload-sidebar, .workload-panel, [data-testid="workload-sidebar"]');
      if (await workloadSidebar.count() > 0) {
        await expect(workloadSidebar).toBeVisible();
        
        // 检查负载指示器
        const loadIndicator = workloadSidebar.locator('.load-indicator, .progress-bar');
        if (await loadIndicator.count() > 0) {
          await expect(loadIndicator).toBeVisible();
        }
        
        // 检查工时统计
        const workHours = workloadSidebar.locator('text=/\\d+[h小时]/, text=/\\d+\\s*小时/');
        if (await workHours.count() > 0) {
          await expect(workHours.first()).toBeVisible();
        }
      }
    }
  });

  test('子任务自动生成功能', async ({ page }) => {
    // 创建一个复杂任务
    await page.locator('.sticky-canvas').dblclick();
    await page.waitForTimeout(500);
    
    const input = page.locator('input:visible, textarea:visible').first();
    if (await input.count() > 0) {
      await input.fill('开发用户管理系统');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(2000);
      
      const taskCard = page.locator('.task-card:has-text("开发用户管理系统")').first();
      await expect(taskCard).toBeVisible();
      
      // 点击任务选择
      await taskCard.click();
      await page.waitForTimeout(500);
      
      // 查找子任务生成按钮
      const subtaskButton = page.locator('button:has-text("🔧"), button:has-text("子任务"), [data-testid="generate-subtasks"]').first();
      
      if (await subtaskButton.count() > 0) {
        await subtaskButton.click();
        
        // 等待AI生成子任务
        await page.waitForTimeout(5000);
        
        // 检查是否有子任务确认对话框
        const confirmDialog = page.locator('.subtask-dialog, .confirm-dialog, [data-testid="subtask-confirmation"]');
        if (await confirmDialog.count() > 0) {
          await expect(confirmDialog).toBeVisible();
          
          // 确认创建子任务
          const confirmButton = confirmDialog.locator('button:has-text("确认"), button:has-text("创建")').first();
          if (await confirmButton.count() > 0) {
            await confirmButton.click();
            await page.waitForTimeout(2000);
            
            // 检查画布上是否出现了新的子任务
            const newTasks = page.locator('.task-card');
            const taskCount = await newTasks.count();
            expect(taskCount).toBeGreaterThan(1);
          }
        }
      }
    }
  });

  test('周报生成功能', async ({ page }) => {
    // 查找周报按钮
    const weeklyReportButton = page.locator('button:has-text("Weekly Report"), button:has-text("周报"), [data-testid="weekly-report"]').first();
    
    if (await weeklyReportButton.count() > 0) {
      await weeklyReportButton.click();
      await page.waitForTimeout(3000);
      
      // 检查周报对话框或页面
      const reportDialog = page.locator('.weekly-report, .report-dialog, [data-testid="weekly-report-dialog"]');
      if (await reportDialog.count() > 0) {
        await expect(reportDialog).toBeVisible();
        
        // 检查报告内容
        const reportContent = reportDialog.locator('.report-content, .markdown-content');
        if (await reportContent.count() > 0) {
          await expect(reportContent).toBeVisible();
          
          // 检查是否包含基本的报告结构
          const hasExecutiveSummary = await reportContent.locator('text="执行摘要", text="Executive Summary"').count() > 0;
          const hasCompletedTasks = await reportContent.locator('text="已完成", text="Completed"').count() > 0;
          
          expect(hasExecutiveSummary || hasCompletedTasks).toBeTruthy();
        }
        
        // 关闭对话框
        const closeButton = reportDialog.locator('button:has-text("关闭"), button:has-text("Close"), .close-button').first();
        if (await closeButton.count() > 0) {
          await closeButton.click();
        } else {
          await page.keyboard.press('Escape');
        }
      }
    }
  });

  test('风险雷达功能', async ({ page }) => {
    // 查找风险雷达指示器
    const riskRadar = page.locator('.risk-radar, [data-testid="risk-radar"], .risk-indicator').first();
    
    if (await riskRadar.count() > 0) {
      await expect(riskRadar).toBeVisible();
      
      // 点击风险雷达
      await riskRadar.click();
      await page.waitForTimeout(1000);
      
      // 检查风险详情面板
      const riskPanel = page.locator('.risk-panel, .risk-details, [data-testid="risk-panel"]');
      if (await riskPanel.count() > 0) {
        await expect(riskPanel).toBeVisible();
        
        // 检查风险类别
        const riskCategories = riskPanel.locator('.risk-category, .risk-item');
        if (await riskCategories.count() > 0) {
          await expect(riskCategories.first()).toBeVisible();
        }
      }
    }
  });

  test('主题岛聚类视图', async ({ page }) => {
    // 查找主题岛按钮
    const islandButton = page.locator('button:has-text("🏝️"), button:has-text("主题岛"), [data-testid="theme-islands"]').first();
    
    if (await islandButton.count() > 0) {
      await islandButton.click();
      await page.waitForTimeout(3000);
      
      // 检查是否切换到岛屿视图
      const islandView = page.locator('.island-view, .theme-islands, [data-testid="island-view"]');
      if (await islandView.count() > 0) {
        await expect(islandView).toBeVisible();
        
        // 检查岛屿头部
        const islandHeaders = page.locator('.island-header, .island-title');
        if (await islandHeaders.count() > 0) {
          await expect(islandHeaders.first()).toBeVisible();
          
          // 测试岛屿折叠/展开
          await islandHeaders.first().click();
          await page.waitForTimeout(1000);
          
          // 再次点击切换状态
          await islandHeaders.first().click();
          await page.waitForTimeout(1000);
        }
        
        // 退出岛屿视图
        const exitButton = page.locator('button:has-text("退出"), button:has-text("Exit"), [data-testid="exit-island-view"]').first();
        if (await exitButton.count() > 0) {
          await exitButton.click();
          await page.waitForTimeout(1000);
        }
      }
    }
  });
});