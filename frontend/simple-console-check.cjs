const { chromium } = require('playwright');

async function simpleConsoleCheck() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  const errors = [];
  const warnings = [];
  const networkErrors = [];
  const allMessages = [];

  // Monitor console messages
  page.on('console', msg => {
    const entry = {
      type: msg.type(),
      text: msg.text(),
      location: msg.location(),
      timestamp: new Date().toISOString()
    };
    
    allMessages.push(entry);
    
    if (msg.type() === 'error') {
      errors.push(entry);
      console.log(`🔴 ERROR: ${msg.text()}`);
      if (entry.location && entry.location.url) {
        console.log(`    Location: ${entry.location.url}:${entry.location.lineNumber}:${entry.location.columnNumber}`);
      }
    } else if (msg.type() === 'warning') {
      warnings.push(entry);
      console.log(`🟡 WARNING: ${msg.text()}`);
    }
  });

  // Monitor page errors
  page.on('pageerror', error => {
    errors.push({
      type: 'pageerror',
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
    
    console.log(`🔴 PAGE ERROR: ${error.message}`);
    if (error.stack) {
      console.log(`    Stack: ${error.stack.split('\n')[0]}`);
    }
  });

  // Monitor network failures
  page.on('requestfailed', request => {
    networkErrors.push({
      type: 'requestfailed',
      url: request.url(),
      method: request.method(),
      failure: request.failure(),
      timestamp: new Date().toISOString()
    });
    
    console.log(`🌐 REQUEST FAILED: ${request.method()} ${request.url()}`);
    console.log(`    Reason: ${request.failure()?.errorText || 'Unknown'}`);
  });

  // Monitor HTTP errors
  page.on('response', response => {
    if (response.status() >= 400) {
      networkErrors.push({
        type: 'httperror',
        url: response.url(),
        status: response.status(),
        statusText: response.statusText(),
        timestamp: new Date().toISOString()
      });
      
      console.log(`🌐 HTTP ERROR: ${response.status()} ${response.statusText()} - ${response.url()}`);
    }
  });

  try {
    console.log('🚀 Starting TaskWall console monitoring...');
    
    // Load the application
    await page.goto('http://localhost:3000', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    console.log('⏳ Waiting for app to load...');
    await page.waitForSelector('.sticky-canvas', { timeout: 10000 });
    await page.waitForTimeout(3000);

    console.log('✅ App loaded successfully');
    console.log('\n🧪 Testing basic operations...');

    // Test 1: Try to create a task
    console.log('Testing task creation...');
    try {
      await page.dblclick('.sticky-canvas', { position: { x: 300, y: 300 } });
      await page.waitForTimeout(1000);
      
      const input = page.locator('input:visible, textarea:visible').first();
      if (await input.count() > 0) {
        await input.fill('Console Test Task');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(1500);
        console.log('✅ Task creation test completed');
      } else {
        console.log('⚠️  No input field found for task creation');
      }
    } catch (error) {
      console.log(`❌ Task creation failed: ${error.message}`);
    }

    // Test 2: Try keyboard shortcuts
    console.log('Testing keyboard shortcuts...');
    const shortcuts = ['q', 'v', 'Meta+k'];
    for (const shortcut of shortcuts) {
      try {
        await page.keyboard.press(shortcut);
        await page.waitForTimeout(500);
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);
      } catch (error) {
        console.log(`❌ Shortcut ${shortcut} failed: ${error.message}`);
      }
    }

    // Test 3: Try UI interactions
    console.log('Testing UI interactions...');
    try {
      const buttons = page.locator('button:visible');
      const count = await buttons.count();
      console.log(`Found ${count} visible buttons`);
      
      if (count > 0) {
        // Try clicking first visible button
        const firstButton = buttons.first();
        const buttonText = await firstButton.textContent();
        await firstButton.click();
        await page.waitForTimeout(1000);
        console.log(`✅ Clicked button: "${buttonText}"`);
      }
    } catch (error) {
      console.log(`❌ UI interaction failed: ${error.message}`);
    }

    // Wait for any async errors
    console.log('⏳ Waiting for async operations...');
    await page.waitForTimeout(5000);

  } catch (error) {
    console.log(`❌ Main test failed: ${error.message}`);
  } finally {
    // Generate final report
    console.log('\n📊 === CONSOLE ERROR ANALYSIS REPORT ===');
    console.log(`Total console messages: ${allMessages.length}`);
    console.log(`🔴 Errors: ${errors.length}`);
    console.log(`🟡 Warnings: ${warnings.length}`);
    console.log(`🌐 Network errors: ${networkErrors.length}`);

    if (errors.length > 0) {
      console.log('\n🔴 === DETAILED ERROR LIST ===');
      errors.forEach((error, i) => {
        console.log(`\n${i + 1}. Type: ${error.type}`);
        console.log(`   Time: ${error.timestamp}`);
        if (error.text) console.log(`   Message: ${error.text}`);
        if (error.message) console.log(`   Message: ${error.message}`);
        if (error.location) {
          console.log(`   Location: ${error.location.url}:${error.location.lineNumber}:${error.location.columnNumber}`);
        }
        if (error.stack) {
          console.log(`   Stack: ${error.stack.split('\n').slice(0, 3).join('\n   ')}`);
        }
      });
    }

    if (warnings.length > 0) {
      console.log('\n🟡 === WARNING LIST ===');
      warnings.forEach((warning, i) => {
        console.log(`${i + 1}. ${warning.text}`);
        if (warning.location) {
          console.log(`   Location: ${warning.location.url}:${warning.location.lineNumber}`);
        }
      });
    }

    if (networkErrors.length > 0) {
      console.log('\n🌐 === NETWORK ERROR LIST ===');
      networkErrors.forEach((netError, i) => {
        console.log(`${i + 1}. ${netError.type}: ${netError.url}`);
        if (netError.status) console.log(`   Status: ${netError.status} ${netError.statusText}`);
        if (netError.failure) console.log(`   Failure: ${netError.failure.errorText}`);
      });
    }

    // Save report
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalMessages: allMessages.length,
        errors: errors.length,
        warnings: warnings.length,
        networkErrors: networkErrors.length
      },
      errors,
      warnings,
      networkErrors,
      allMessages
    };

    require('fs').writeFileSync('final-console-report.json', JSON.stringify(report, null, 2));
    console.log('\n💾 Full report saved to: final-console-report.json');

    if (errors.length === 0) {
      console.log('\n🎉 === GOOD NEWS ===');
      console.log('✅ NO CRITICAL JAVASCRIPT ERRORS DETECTED!');
      console.log('✅ The TaskWall application appears to be running cleanly.');
    } else {
      console.log('\n⚠️  === ATTENTION NEEDED ===');
      console.log(`❌ Found ${errors.length} error(s) that need attention.`);
    }

    await browser.close();
  }
}

simpleConsoleCheck().catch(console.error);