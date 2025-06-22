// 创建一个控制台错误检查工具
(function() {
    console.log('🔍 开始检查控制台错误...');
    
    const errors = [];
    const warnings = [];
    const networkErrors = [];
    
    // 监听所有类型的错误
    const originalError = console.error;
    const originalWarn = console.warn;
    
    console.error = function(...args) {
        errors.push({
            timestamp: new Date().toISOString(),
            type: 'error',
            message: args.join(' '),
            stack: new Error().stack
        });
        originalError.apply(console, args);
    };
    
    console.warn = function(...args) {
        warnings.push({
            timestamp: new Date().toISOString(),
            type: 'warning', 
            message: args.join(' ')
        });
        originalWarn.apply(console, args);
    };
    
    // 检查全局错误
    window.addEventListener('error', (event) => {
        errors.push({
            timestamp: new Date().toISOString(),
            type: 'global_error',
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            stack: event.error?.stack
        });
    });
    
    // 检查Promise rejection
    window.addEventListener('unhandledrejection', (event) => {
        errors.push({
            timestamp: new Date().toISOString(),
            type: 'promise_rejection',
            message: event.reason?.toString() || 'Unknown promise rejection',
            reason: event.reason
        });
    });
    
    // 检查网络请求错误
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args)
            .then(response => {
                if (!response.ok) {
                    networkErrors.push({
                        timestamp: new Date().toISOString(),
                        url: args[0],
                        status: response.status,
                        statusText: response.statusText
                    });
                }
                return response;
            })
            .catch(error => {
                networkErrors.push({
                    timestamp: new Date().toISOString(),
                    url: args[0],
                    error: error.message
                });
                throw error;
            });
    };
    
    // 定期报告结果
    setInterval(() => {
        if (errors.length > 0 || warnings.length > 0 || networkErrors.length > 0) {
            console.log('📊 错误检查报告:');
            console.table([
                { 类型: 'JavaScript错误', 数量: errors.length },
                { 类型: '警告', 数量: warnings.length },
                { 类型: '网络错误', 数量: networkErrors.length }
            ]);
            
            if (errors.length > 0) {
                console.group('🔴 JavaScript错误详情:');
                errors.forEach((error, index) => {
                    console.log(`${index + 1}. [${error.timestamp}] ${error.type}: ${error.message}`);
                    if (error.stack) console.log('Stack:', error.stack);
                    if (error.filename) console.log(`位置: ${error.filename}:${error.lineno}:${error.colno}`);
                });
                console.groupEnd();
            }
            
            if (warnings.length > 0) {
                console.group('🟡 警告详情:');
                warnings.forEach((warning, index) => {
                    console.log(`${index + 1}. [${warning.timestamp}] ${warning.message}`);
                });
                console.groupEnd();
            }
            
            if (networkErrors.length > 0) {
                console.group('🌐 网络错误详情:');
                networkErrors.forEach((error, index) => {
                    console.log(`${index + 1}. [${error.timestamp}] ${error.url} - ${error.status || error.error}`);
                });
                console.groupEnd();
            }
        } else {
            console.log('✅ 目前没有发现错误或警告');
        }
    }, 5000);
    
    // 导出数据到全局变量以便检查
    window.errorChecker = {
        getErrors: () => errors,
        getWarnings: () => warnings,
        getNetworkErrors: () => networkErrors,
        getAllIssues: () => ({ errors, warnings, networkErrors }),
        clear: () => {
            errors.length = 0;
            warnings.length = 0;
            networkErrors.length = 0;
        }
    };
    
    console.log('✅ 控制台错误监控已启动');
    console.log('💡 使用 window.errorChecker 来访问检查结果');
})();