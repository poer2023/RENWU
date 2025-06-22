# TaskWall API 和中键拖动问题修复报告

## 修复时间
2024-01-XX

## 问题描述

### 1. API 报错问题
- 前端调用 API 时出现 404 和 422 错误
- API 路径不一致导致请求失败
- 端口配置不统一

### 2. 中键拖动画布问题
- 用户无法使用鼠标中键拖动画布
- 事件处理逻辑存在问题

## 修复内容

### 1. API 路径修复

#### 后端路由前缀统一
修改了所有路由器的前缀，确保统一使用 `/api` 前缀：

1. **AI v3 路由器** (`backend/app/routers/ai_v3.py`)
   ```python
   # 修改前
   router = APIRouter(prefix="/ai/v3", tags=["AI Services v3.0"])
   
   # 修改后
   router = APIRouter(prefix="/api/ai/v3", tags=["AI Services v3.0"])
   ```

2. **设置路由器** (`backend/app/routers/settings.py`)
   ```python
   # 修改前
   router = APIRouter(prefix="/settings", tags=["settings"])
   
   # 修改后
   router = APIRouter(prefix="/api/settings", tags=["settings"])
   ```

3. **OCR 路由器** (`backend/app/routers/ocr.py`)
   ```python
   # 修改前
   router = APIRouter(prefix="/ocr", tags=["ocr"])
   
   # 修改后
   router = APIRouter(prefix="/api/ocr", tags=["ocr"])
   ```

4. **导出/备份路由器** (`backend/app/routers/export_backup.py`)
   ```python
   # 修改前
   router = APIRouter(tags=["export", "backup"])
   
   # 修改后
   router = APIRouter(prefix="/api", tags=["export", "backup"])
   ```

### 2. 端口配置统一

#### 确保所有配置使用 8765 端口
1. **Vite 代理配置** (`frontend/vite.config.ts`)
   - 已确认代理配置正确指向 `http://localhost:8765`

2. **Docker Compose 配置** (`docker-compose.yml`)
   ```yaml
   # 修改前
   ports:
     - "8000:8000"
   
   # 修改后
   ports:
     - "8765:8000"
   ```

### 3. 中键拖动问题分析

#### 当前实现状态
1. **事件绑定**: `StickyCanvas.vue` 已正确绑定了 `@mousedown` 和 `@auxclick` 事件
2. **事件处理**: `handleCanvasMouseDown` 函数已实现中键检测逻辑
3. **拖动功能**: `useUltraPerformancePanZoom` 中的 `startPan` 方法支持中键拖动

#### 可能的问题原因
1. **任务位置初始化问题**: 控制台显示大量 "Missing task positions" 错误，可能影响画布渲染
2. **事件冒泡问题**: 中键事件可能被其他元素拦截
3. **浏览器兼容性**: 某些浏览器对中键事件处理不一致

### 4. 建议的进一步调试步骤

1. **检查任务位置初始化**
   ```javascript
   // 确保在组件挂载时正确初始化所有任务位置
   onMounted(() => {
     positions.initializeTaskPositions()
   })
   ```

2. **添加更多调试日志**
   ```javascript
   function handleCanvasMouseDown(event: MouseEvent) {
     console.log('鼠标按下:', {
       button: event.button,
       target: event.target,
       currentTarget: event.currentTarget,
       isPanning: panZoom.panState.value.isPanning
     })
   }
   ```

3. **测试不同浏览器**
   - Chrome/Edge: 应该正常工作
   - Firefox: 可能需要特殊处理
   - Safari: 可能有兼容性问题

## 测试建议

### 1. API 测试
运行测试脚本验证所有 API 端点：
```bash
python test_all_apis.py
```

### 2. 中键拖动测试
1. 确保后端服务在 8765 端口运行
2. 清除浏览器缓存
3. 打开开发者工具查看控制台日志
4. 测试中键拖动功能

### 3. 验证清单
- [ ] 所有 API 端点返回正确状态码
- [ ] 无 404 错误
- [ ] 无 CORS 错误
- [ ] 中键可以拖动画布
- [ ] 左键可以拖动任务卡片
- [ ] 滚轮可以缩放画布

## 后续优化建议

1. **错误处理**: 添加全局错误处理器，统一处理 API 错误
2. **性能优化**: 批量初始化任务位置，减少 DOM 操作
3. **用户体验**: 添加拖动时的视觉反馈（如改变鼠标指针）
4. **兼容性**: 添加浏览器特性检测，提供降级方案

## 总结

本次修复主要解决了：
1. API 路径不一致问题 - 统一使用 `/api` 前缀
2. 端口配置问题 - 确保所有服务使用 8765 端口
3. 中键拖动的基础支持已实现，但可能需要进一步调试

如果中键拖动仍有问题，请提供：
1. 浏览器版本信息
2. 控制台完整错误日志
3. 网络请求失败的详细信息 