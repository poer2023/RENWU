const puppeteer = require('puppeteer');

async function testStyleFixes() {
  console.log('🧪 Testing style fixes for TaskWall...');
  
  const browser = await puppeteer.launch({ 
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    devtools: true
  });
  
  const page = await browser.newPage();
  
  // Set viewport to see more content
  await page.setViewport({ width: 1920, height: 1080 });
  
  const errors = [];
  const warnings = [];
  
  // Monitor console
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
  
  page.on('pageerror', (error) => {
    errors.push(error.message);
    console.log(`❌ PAGE ERROR: ${error.message}`);
  });
  
  try {
    console.log('🔗 Connecting to frontend...');
    await page.goto('http://localhost:3000', { 
      waitUntil: 'networkidle2', 
      timeout: 15000 
    });
    
    console.log('✅ Page loaded successfully');
    
    // Wait for components to render
    await page.waitForTimeout(2000);
    
    // Check for task cards
    const taskCards = await page.$$eval('.task-card, .task-node, .lod-simplified', 
      cards => cards.map(card => ({
        visible: card.offsetWidth > 0 && card.offsetHeight > 0,
        hasStyles: window.getComputedStyle(card).backgroundColor !== 'rgba(0, 0, 0, 0)',
        classes: card.className
      }))
    );
    
    console.log(`📊 Found ${taskCards.length} task cards`);
    console.log(`✅ Visible cards: ${taskCards.filter(c => c.visible).length}`);
    console.log(`🎨 Styled cards: ${taskCards.filter(c => c.hasStyles).length}`);
    
    // Check for connections
    const connections = await page.$$eval('path[class*="connection"], line[stroke]', 
      paths => paths.map(path => ({
        visible: path.getBoundingClientRect().width > 0,
        hasStroke: path.getAttribute('stroke') && path.getAttribute('stroke') !== 'none',
        strokeWidth: path.getAttribute('stroke-width') || path.style.strokeWidth
      }))
    );
    
    console.log(`🔗 Found ${connections.length} connections`);
    console.log(`✅ Visible connections: ${connections.filter(c => c.visible).length}`);
    console.log(`🎨 Styled connections: ${connections.filter(c => c.hasStroke).length}`);
    
    // Check for CSS containment issues
    const containmentElements = await page.$$eval('[style*="contain"], .task-card-lod, .task-connections-lazy', 
      elements => elements.map(el => ({
        containValue: window.getComputedStyle(el).contain,
        hasLayoutOnly: window.getComputedStyle(el).contain === 'layout',
        tag: el.tagName,
        classes: el.className
      }))
    );
    
    console.log(`🔧 CSS Containment Check:`);
    containmentElements.forEach((el, i) => {
      console.log(`  ${i + 1}. ${el.tag}.${el.classes}: contain: ${el.containValue} ${el.hasLayoutOnly ? '✅' : '❌'}`);
    });
    
    // Test lazy loading by scrolling
    console.log('🔄 Testing lazy loading...');
    await page.evaluate(() => {
      window.scrollTo(0, 500);
    });
    await page.waitForTimeout(1000);
    
    await page.evaluate(() => {
      window.scrollTo(500, 0);
    });
    await page.waitForTimeout(1000);
    
    console.log('\n📈 Test Summary:');
    console.log(`- Console Errors: ${errors.length}`);
    console.log(`- Console Warnings: ${warnings.length}`);
    console.log(`- Task Cards: ${taskCards.length} total, ${taskCards.filter(c => c.visible && c.hasStyles).length} properly styled`);
    console.log(`- Connections: ${connections.length} total, ${connections.filter(c => c.visible && c.hasStroke).length} properly styled`);
    
    if (errors.length === 0 && taskCards.filter(c => c.visible && c.hasStyles).length > 0) {
      console.log('🎉 Style fixes appear to be working!');
    } else {
      console.log('⚠️  Some issues remain to be fixed');
    }
    
    // Keep browser open for manual inspection
    console.log('\n🔍 Browser kept open for manual inspection. Press Ctrl+C to close.');
    await new Promise(resolve => process.on('SIGINT', resolve));
    
  } catch (error) {
    console.log(`❌ Test failed: ${error.message}`);
  } finally {
    await browser.close();
  }
}

testStyleFixes();