// 自动化测试中键拖动功能
const puppeteer = require('puppeteer');

async function testMiddleClickDrag() {
    console.log('🚀 开始测试中键拖动功能...');
    
    let browser;
    try {
        // 启动浏览器
        browser = await puppeteer.launch({
            headless: false, // 显示浏览器窗口
            defaultViewport: { width: 1200, height: 800 },
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        const page = await browser.newPage();
        
        // 监听控制台消息
        page.on('console', msg => {
            const text = msg.text();
            if (text.includes('🎯') || text.includes('🚀') || text.includes('📊') || text.includes('🛑')) {
                console.log(`[浏览器控制台] ${text}`);
            }
        });
        
        // 导航到应用
        console.log('📱 打开TaskWall应用...');
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });
        
        // 等待页面加载
        console.log('⏳ 等待页面加载...');
        await page.waitForTimeout(3000);
        
        // 查找画布元素
        console.log('🔍 查找画布元素...');
        const canvasSelector = '.sticky-canvas';
        await page.waitForSelector(canvasSelector);
        
        // 获取画布位置
        const canvasElement = await page.$(canvasSelector);
        const canvasBox = await canvasElement.boundingBox();
        
        console.log('📏 画布位置:', canvasBox);
        
        // 计算画布中心点
        const centerX = canvasBox.x + canvasBox.width / 2;
        const centerY = canvasBox.y + canvasBox.height / 2;
        
        console.log('🎯 画布中心点:', { x: centerX, y: centerY });
        
        // 测试中键拖动
        console.log('🖱️ 开始测试中键拖动...');
        
        // 模拟中键按下
        await page.mouse.move(centerX, centerY);
        await page.mouse.down({ button: 'middle' });
        
        // 等待一下确保事件被处理
        await page.waitForTimeout(100);
        
        // 拖动鼠标
        const dragDistance = 100;
        await page.mouse.move(centerX + dragDistance, centerY + dragDistance, { steps: 10 });
        
        // 等待拖动过程
        await page.waitForTimeout(500);
        
        // 松开中键
        await page.mouse.up({ button: 'middle' });
        
        console.log('✅ 中键拖动测试完成');
        
        // 等待一下看结果
        await page.waitForTimeout(2000);
        
        console.log('📊 测试总结:');
        console.log('   - 如果看到上述控制台日志，说明事件被正确触发');
        console.log('   - 如果看到拖动相关日志，说明功能正常工作');
        console.log('   - 浏览器窗口将保持打开，可以手动继续测试');
        
    } catch (error) {
        console.error('❌ 测试失败:', error);
    }
    
    // 不关闭浏览器，方便手动测试
    console.log('🔍 浏览器窗口保持打开，可以手动测试中键拖动功能');
    console.log('💡 请在画布空白区域按住鼠标中键拖动测试');
}

// 检查是否有puppeteer
async function checkPuppeteer() {
    try {
        require('puppeteer');
        return true;
    } catch (e) {
        console.log('📦 需要安装puppeteer来进行自动化测试');
        console.log('💡 执行: npm install puppeteer');
        return false;
    }
}

checkPuppeteer().then(hasPuppeteer => {
    if (hasPuppeteer) {
        testMiddleClickDrag();
    } else {
        console.log('⚠️ 跳过自动化测试，请手动在浏览器中测试');
        console.log('🌐 访问: http://localhost:3000');
        console.log('🖱️ 在画布空白区域按住鼠标中键拖动测试');
    }
});