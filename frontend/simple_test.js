// 简单的控制台错误检测脚本
console.log('🔍 开始检查TaskWall应用...');

// 基本的页面测试
setTimeout(() => {
  console.log('⏰ 延迟检查开始...');
  
  // 检查页面基本元素
  const appElement = document.querySelector('#app');
  console.log('📱 App元素存在:', !!appElement);
  
  if (appElement) {
    console.log('📱 App元素内容长度:', appElement.innerHTML.length);
  }
  
  // 检查Vue应用是否挂载
  const hasVueApp = document.querySelector('.home-layout');
  console.log('🏠 Home布局存在:', !!hasVueApp);
  
  // 检查任务相关元素
  const taskCards = document.querySelectorAll('.task-card, .task-card-lod');
  console.log('📋 任务卡片数量:', taskCards.length);
  
  // 检查Canvas
  const canvas = document.querySelector('.sticky-canvas');
  console.log('🎨 画布存在:', !!canvas);
  
  // 检查连线
  const connections = document.querySelector('.task-connections-lazy');
  console.log('🔗 连线组件存在:', !!connections);
  
  // 检查控制台错误（通过劫持console.error）
  let errorCount = 0;
  const originalError = console.error;
  console.error = function(...args) {
    errorCount++;
    console.log('❌ 错误 #' + errorCount + ':', ...args);
    originalError.apply(console, args);
  };
  
  console.log('✅ 基本检查完成');
  
}, 3000); // 3秒后检查

// 监听未捕获的错误
window.addEventListener('error', function(e) {
  console.log('🚨 全局错误:', {
    message: e.message,
    filename: e.filename,
    lineno: e.lineno,
    colno: e.colno,
    error: e.error
  });
});

// 监听未处理的Promise拒绝
window.addEventListener('unhandledrejection', function(e) {
  console.log('🚨 未处理的Promise拒绝:', {
    reason: e.reason,
    promise: e.promise
  });
});

console.log('🚀 错误监听器已设置，等待页面加载...');