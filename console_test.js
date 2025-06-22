const puppeteer = require('puppeteer');

async function testConsoleErrors() {
  const browser = await puppeteer.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'] 
  });
  
  const page = await browser.newPage();
  
  const errors = [];
  const warnings = [];
  
  // Listen for console messages
  page.on('console', (msg) => {
    const type = msg.type();
    const text = msg.text();
    
    if (type === 'error') {
      errors.push(text);
      console.log(`❌ ERROR: ${text}`);
    } else if (type === 'warning') {
      warnings.push(text);
      console.log(`⚠️  WARNING: ${text}`);
    }
  });
  
  // Listen for page errors
  page.on('pageerror', (error) => {
    errors.push(error.message);
    console.log(`❌ PAGE ERROR: ${error.message}`);
  });
  
  try {
    console.log('🔍 Testing console for errors...');
    
    // Try different ports
    const urls = ['http://localhost:3000', 'http://localhost:3001'];
    let success = false;
    
    for (const url of urls) {
      try {
        console.log(`Testing ${url}...`);
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 10000 });
        success = true;
        console.log(`✅ Successfully loaded ${url}`);
        break;
      } catch (e) {
        console.log(`❌ Failed to load ${url}: ${e.message}`);
      }
    }
    
    if (!success) {
      console.log('❌ No running frontend found');
      return;
    }
    
    // Wait for app to load
    await page.waitForTimeout(3000);
    
    // Check for specific elements and styles
    const taskCards = await page.$$('.task-card');
    const connections = await page.$$('[class*="connection"]');
    
    console.log(`📊 Found ${taskCards.length} task cards`);
    console.log(`📊 Found ${connections.length} connections`);
    
    // Check for missing styles
    const hasStyles = await page.evaluate(() => {
      const links = document.querySelectorAll('link[rel="stylesheet"]');
      const styles = document.querySelectorAll('style');
      return { links: links.length, styles: styles.length };
    });
    
    console.log(`📊 Style info: ${hasStyles.links} CSS links, ${hasStyles.styles} style tags`);
    
    console.log(`\n📈 Summary:`);
    console.log(`- Errors: ${errors.length}`);
    console.log(`- Warnings: ${warnings.length}`);
    
    if (errors.length > 0) {
      console.log('\n❌ Errors found:');
      errors.forEach((error, i) => console.log(`${i + 1}. ${error}`));
    }
    
  } catch (error) {
    console.log(`❌ Test failed: ${error.message}`);
  } finally {
    await browser.close();
  }
}

testConsoleErrors();