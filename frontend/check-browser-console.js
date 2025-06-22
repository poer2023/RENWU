// TaskWall 浏览器控制台错误检查脚本
// 在浏览器控制台中运行此脚本来检查应用状态

console.log('🔍 开始检查 TaskWall 应用状态...');

// 检查 Vue 应用是否正常挂载
function checkVueApp() {
  const app = document.querySelector('#app');
  if (app && app._vnode) {
    console.log('✅ Vue 应用已正常挂载');
    return true;
  } else if (app) {
    console.log('⚠️ Vue 应用容器存在但可能未正常挂载');
    return false;
  } else {
    console.log('❌ 未找到 Vue 应用容器');
    return false;
  }
}

// 检查虚拟化组件
function checkVirtualizationComponents() {
  console.log('\n🎯 检查虚拟化系统组件...');
  
  // 检查 TaskCardLOD 组件
  const lodCards = document.querySelectorAll('.task-card-lod');
  console.log(`📊 TaskCardLOD 组件数量: ${lodCards.length}`);
  
  // 检查不同LOD级别
  for (let i = 0; i <= 5; i++) {
    const lodLevel = document.querySelectorAll(`.lod-${i}`);
    if (lodLevel.length > 0) {
      console.log(`  - LOD ${i} 级别: ${lodLevel.length} 个组件`);
    }
  }
  
  // 检查连线系统
  const connections = document.querySelectorAll('.task-connections-lazy');
  console.log(`🔗 TaskConnectionsLazy 组件数量: ${connections.length}`);
  
  // 检查画布
  const canvas = document.querySelector('.sticky-canvas');
  if (canvas) {
    console.log('✅ StickyCanvas 组件已渲染');
    
    // 检查任务数量
    const tasks = document.querySelectorAll('.task-wrapper');
    console.log(`📋 可见任务数量: ${tasks.length}`);
    
    // 检查虚拟化状态
    const virtualTasks = document.querySelectorAll('[data-task-id]');
    console.log(`🎭 虚拟化任务元素: ${virtualTasks.length}`);
  } else {
    console.log('❌ StickyCanvas 组件未找到');
  }
}

// 检查控制台错误
function checkConsoleErrors() {
  console.log('\n🐛 检查控制台错误...');
  
  // 重写console方法来捕获错误
  let errors = [];
  let warnings = [];
  
  const originalError = console.error;
  const originalWarn = console.warn;
  
  console.error = function(...args) {
    errors.push(args.join(' '));
    originalError.apply(console, args);
  };
  
  console.warn = function(...args) {
    warnings.push(args.join(' '));
    originalWarn.apply(console, args);
  };
  
  // 等待一段时间收集错误
  setTimeout(() => {
    console.log(`❌ 发现错误: ${errors.length} 个`);
    errors.forEach((error, index) => {
      console.log(`  ${index + 1}. ${error}`);
    });
    
    console.log(`⚠️ 发现警告: ${warnings.length} 个`);
    warnings.forEach((warning, index) => {
      console.log(`  ${index + 1}. ${warning}`);
    });
    
    // 恢复原始方法
    console.error = originalError;
    console.warn = originalWarn;
  }, 5000);
}

// 检查网络请求
async function checkAPIConnections() {
  console.log('\n🌐 检查 API 连接...');
  
  try {
    const response = await fetch('/api/tasks/');
    if (response.ok) {
      const data = await response.json();
      console.log(`✅ API 连接正常，获取到 ${data.length} 个任务`);
      
      // 检查任务数据结构
      if (data.length > 0) {
        const sampleTask = data[0];
        const requiredFields = ['id', 'title', 'position_x', 'position_y'];
        const missingFields = requiredFields.filter(field => !(field in sampleTask));
        
        if (missingFields.length === 0) {
          console.log('✅ 任务数据结构完整');
        } else {
          console.log(`⚠️ 任务数据缺少字段: ${missingFields.join(', ')}`);
        }
      }
    } else {
      console.log(`❌ API 响应错误: ${response.status} ${response.statusText}`);
    }
  } catch (error) {
    console.log(`❌ API 连接失败: ${error.message}`);
  }
}

// 检查性能指标
function checkPerformance() {
  console.log('\n⚡ 检查性能指标...');
  
  // 检查渲染时间
  const start = performance.now();
  requestAnimationFrame(() => {
    const renderTime = performance.now() - start;
    console.log(`🎬 渲染时间: ${renderTime.toFixed(2)}ms`);
    
    if (renderTime > 16.67) {
      console.log('⚠️ 渲染时间超过 60fps 阈值');
    } else {
      console.log('✅ 渲染性能良好');
    }
  });
  
  // 检查内存使用
  if (performance.memory) {
    const memory = performance.memory;
    console.log(`💾 内存使用:`);
    console.log(`  - 已使用: ${(memory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`);
    console.log(`  - 总计: ${(memory.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`);
    console.log(`  - 限制: ${(memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`);
  }
}

// 主检查函数
function runFullCheck() {
  console.log('🚀 TaskWall 应用检查开始\n');
  
  // 等待应用完全加载
  setTimeout(() => {
    checkVueApp();
    checkVirtualizationComponents();
    checkAPIConnections();
    checkPerformance();
    checkConsoleErrors();
    
    console.log('\n✨ 检查完成！请查看上述结果。');
  }, 2000);
}

// 立即运行检查
runFullCheck();

// 提供手动检查命令
console.log('\n📋 可用的手动检查命令:');
console.log('- checkVueApp() - 检查 Vue 应用状态');
console.log('- checkVirtualizationComponents() - 检查虚拟化组件');
console.log('- checkAPIConnections() - 检查 API 连接');
console.log('- checkPerformance() - 检查性能指标');
console.log('- runFullCheck() - 运行完整检查');