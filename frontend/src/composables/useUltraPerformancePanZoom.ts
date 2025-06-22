import { ref, Ref, computed, nextTick } from 'vue'

interface ViewportState {
  x: number
  y: number
  scale: number
  minScale: number
  maxScale: number
}

interface PanState {
  isPanning: boolean
  startX: number
  startY: number
  startViewportX: number
  startViewportY: number
  bounds: {
    maxX: number
    maxY: number
    minX: number
    minY: number
  }
}

interface PanZoomOptions {
  minScale?: number
  maxScale?: number
  onViewportChange?: (viewport: ViewportState) => void
}

// 超级性能常量
const ULTRA_WHEEL_THROTTLE = 4 // 240fps for ultra smooth zoom  
const ULTRA_PAN_THROTTLE = 4 // 240fps for ultra smooth pan
const VIEWPORT_UPDATE_DEBOUNCE = 100 // 减少状态更新
const TRANSFORM_CACHE_SIZE = 100
const PRECISION = 0.1 // 亚像素精度

export function useUltraPerformancePanZoom(
  canvasContainer: Ref<HTMLElement | undefined>,
  canvasSize: Ref<{ width: number; height: number }>,
  options: PanZoomOptions = {}
) {
  // 视口状态
  const viewport = ref<ViewportState>({
    x: 0,
    y: 0,
    scale: 1,
    minScale: options.minScale || 0.1,
    maxScale: options.maxScale || 3
  })

  // 平移状态
  const panState = ref<PanState>({
    isPanning: false,
    startX: 0,
    startY: 0,
    startViewportX: 0,
    startViewportY: 0,
    bounds: { maxX: 0, maxY: 0, minX: 0, minY: 0 }
  })

  // 超级性能优化变量
  let canvasContentElement: HTMLElement | null = null
  let primaryRafId: number | null = null
  let secondaryRafId: number | null = null
  let wheelRafId: number | null = null
  let lastWheelTime = 0
  let lastPanTime = 0
  let viewportUpdateTimer: number | null = null
  
  // 超级缓存的变换矩阵
  let ultraCachedTransform = {
    x: 0,
    y: 0,
    scale: 1,
    dirty: false,
    timestamp: 0
  }
  
  // 变换历史缓存（用于预测）
  const transformHistory: Array<{ x: number; y: number; scale: number; timestamp: number }> = []
  const maxHistorySize = 10
  
  // 性能监控
  const perfMetrics = {
    panFps: 0,
    zoomFps: 0,
    avgPanTime: 0,
    avgZoomTime: 0,
    lastUpdate: 0
  }

  // 获取超级优化的canvas内容元素
  function getUltraCanvasContentElement(): HTMLElement | null {
    if (canvasContentElement) return canvasContentElement
    
    if (canvasContainer.value) {
      canvasContentElement = canvasContainer.value.querySelector('.canvas-content') as HTMLElement
      if (canvasContentElement) {
        // 超级GPU加速配置
        canvasContentElement.style.willChange = 'transform'
        canvasContentElement.style.backfaceVisibility = 'hidden'
        canvasContentElement.style.perspective = '1000px'
        canvasContentElement.style.transformStyle = 'preserve-3d'
        canvasContentElement.style.contain = 'layout style paint size'
        canvasContentElement.style.isolation = 'isolate'
        
        // 预热GPU层
        for (let i = 0; i < 5; i++) {
          canvasContentElement.style.transform = `translate3d(0,0,0) scale(1)`
        }
        
        console.log('Canvas GPU超级加速已启用')
      }
    }
    
    return canvasContentElement
  }

  // 超高精度transform更新
  function ultraUpdateCanvasTransform(x: number, y: number, scale: number, force = false) {
    const element = getUltraCanvasContentElement()
    if (!element) return
    
    // 亚像素精度对齐
    const alignedX = Math.round(x / PRECISION) * PRECISION
    const alignedY = Math.round(y / PRECISION) * PRECISION
    const alignedScale = Math.round(scale * 10000) / 10000
    
    const now = performance.now()
    
    // 超智能缓存检查
    if (!force && 
        Math.abs(ultraCachedTransform.x - alignedX) < PRECISION &&
        Math.abs(ultraCachedTransform.y - alignedY) < PRECISION &&
        Math.abs(ultraCachedTransform.scale - alignedScale) < 0.0001) {
      return
    }
    
    // 记录变换历史（用于预测和平滑）
    transformHistory.push({ x: alignedX, y: alignedY, scale: alignedScale, timestamp: now })
    if (transformHistory.length > maxHistorySize) {
      transformHistory.shift()
    }
    
    const transform = `translate3d(${alignedX}px, ${alignedY}px, 0) scale(${alignedScale})`
    element.style.transform = transform
    
    ultraCachedTransform = { x: alignedX, y: alignedY, scale: alignedScale, dirty: false, timestamp: now }
  }

  // 智能预测边界计算
  function ultraCalculateBounds(containerRect: DOMRect, scale: number) {
    const maxX = containerRect.width * 0.5
    const maxY = containerRect.height * 0.5
    const minX = -(canvasSize.value.width * scale - containerRect.width * 0.5)
    const minY = -(canvasSize.value.height * scale - containerRect.height * 0.5)
    
    return { maxX, maxY, minX, minY }
  }

  // 高精度约束应用
  function ultraConstrainViewport(x: number, y: number, bounds: any) {
    return {
      x: Math.max(bounds.minX, Math.min(bounds.maxX, x)),
      y: Math.max(bounds.minY, Math.min(bounds.maxY, y))
    }
  }

  // 预测性平滑（基于历史数据）
  function predictSmoothing(currentX: number, currentY: number) {
    if (transformHistory.length < 3) return { x: currentX, y: currentY }
    
    const recent = transformHistory.slice(-3)
    const velocityX = (recent[2].x - recent[0].x) / (recent[2].timestamp - recent[0].timestamp)
    const velocityY = (recent[2].y - recent[0].y) / (recent[2].timestamp - recent[0].timestamp)
    
    // 预测下一帧位置并微调
    const predictedX = currentX + velocityX * 16 * 0.1 // 10%预测
    const predictedY = currentY + velocityY * 16 * 0.1
    
    return { x: predictedX, y: predictedY }
  }

  // 超级防抖视口更新
  function ultraScheduleViewportUpdate() {
    if (viewportUpdateTimer) {
      clearTimeout(viewportUpdateTimer)
    }
    
    viewportUpdateTimer = window.setTimeout(() => {
      if (options.onViewportChange) {
        options.onViewportChange(viewport.value)
      }
    }, VIEWPORT_UPDATE_DEBOUNCE)
  }

  // 超级高性能滚轮处理（240fps）
  function handleUltraWheel(event: WheelEvent) {
    // 安全地阻止默认行为
    if (event.cancelable) {
      event.preventDefault()
    }
    
    const now = performance.now()
    const deltaTime = now - lastWheelTime
    if (deltaTime < ULTRA_WHEEL_THROTTLE) return
    
    const startTime = now
    
    // 取消之前的RAF
    if (wheelRafId) cancelAnimationFrame(wheelRafId)
    
    // 双重RAF确保超流畅
    wheelRafId = requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        const container = canvasContainer.value
        if (!container) return
        
        const rect = container.getBoundingClientRect()
        
        // 鼠标位置
        const mouseX = event.clientX - rect.left
        const mouseY = event.clientY - rect.top
        
        // 世界坐标
        const worldX = (mouseX - viewport.value.x) / viewport.value.scale
        const worldY = (mouseY - viewport.value.y) / viewport.value.scale
        
        // 动态缩放因子（自适应速度）
        const speed = Math.abs(event.deltaY) > 50 ? 0.85 : 0.92 // 快速滚动时更大步长
        const scaleFactor = event.deltaY > 0 ? speed : (1 / speed)
        
        const newScale = Math.max(
          viewport.value.minScale, 
          Math.min(viewport.value.maxScale, viewport.value.scale * scaleFactor)
        )
        
        if (Math.abs(newScale - viewport.value.scale) < 0.0001) return
        
        // 计算新位置
        const newX = mouseX - worldX * newScale
        const newY = mouseY - worldY * newScale
        
        // 应用约束
        const bounds = ultraCalculateBounds(rect, newScale)
        const constrained = ultraConstrainViewport(newX, newY, bounds)
        
        // 预测性平滑
        const smoothed = predictSmoothing(constrained.x, constrained.y)
        
        // 直接更新DOM
        ultraUpdateCanvasTransform(smoothed.x, smoothed.y, newScale)
        
        // 延迟更新状态
        viewport.value.x = smoothed.x
        viewport.value.y = smoothed.y
        viewport.value.scale = newScale
        
        ultraScheduleViewportUpdate()
        
        // 性能监控
        const processTime = performance.now() - startTime
        perfMetrics.zoomFps = 1000 / deltaTime
        perfMetrics.avgZoomTime = (perfMetrics.avgZoomTime + processTime) / 2
        
        lastWheelTime = now
      })
    })
  }

  // 超级开始平移（支持左键和中键）
  function startUltraPan(event: MouseEvent) {
    console.log('🎯 startUltraPan 函数被调用, 按键:', event.button)
    console.log('🔍 Event details:', {
      button: event.button,
      clientX: event.clientX,
      clientY: event.clientY,
      type: event.type,
      target: event.target
    })
    
    // 支持左键和中键拖动
    if (event.button !== 0 && event.button !== 1) {
      console.log('❌ 按键不支持，退出:', event.button)
      return
    }
    
    const container = canvasContainer.value
    if (!container) {
      console.log('❌ 没有找到canvas容器')
      return
    }
    
    const rect = container.getBoundingClientRect()
    const bounds = ultraCalculateBounds(rect, viewport.value.scale)
    
    console.log(`🚀 画布拖动开始: 按键=${event.button}, 起始位置=(${event.clientX}, ${event.clientY})`)
    console.log('📊 当前视口状态:', viewport.value)
    console.log('📊 计算边界:', bounds)
    
    // 同步超级缓存的变换
    ultraCachedTransform.x = viewport.value.x
    ultraCachedTransform.y = viewport.value.y
    ultraCachedTransform.scale = viewport.value.scale
    
    panState.value = {
      isPanning: true,
      startX: event.clientX,
      startY: event.clientY,
      startViewportX: viewport.value.x,
      startViewportY: viewport.value.y,
      bounds
    }
    
    console.log('📊 设置拖动状态:', panState.value)
    
    // 获取canvas元素并启用超级优化
    const element = getUltraCanvasContentElement()
    if (element) {
      element.style.pointerEvents = 'none' // 避免子元素干扰
      element.style.cursor = 'grabbing'
      console.log('✅ Canvas元素样式已设置')
    } else {
      console.log('❌ 没有找到canvas内容元素')
    }
    
    document.body.style.cursor = 'grabbing'
    document.body.style.userSelect = 'none'
    document.body.style.pointerEvents = 'none' // 全局禁用交互
    
    // 🚨 修复：高性能事件监听，移除 passive 配置
    document.addEventListener('mousemove', handleUltraPan, { 
      passive: false,
      capture: true
    })
    document.addEventListener('mouseup', stopUltraPan, { 
      passive: false, // ✅ 修复：确保 preventDefault 正常工作
      capture: true,
      once: true
    })
    document.addEventListener('mouseleave', stopUltraPan, { 
      passive: false, // ✅ 修复：确保 preventDefault 正常工作
      capture: true,
      once: true
    })
    
    console.log('✅ 超级画布拖动开始 - 事件已绑定')
    console.log('📊 最终拖动状态:', panState.value.isPanning)
  }

  // 超级处理平移（240fps）
  function handleUltraPan(event: MouseEvent) {
    if (!panState.value.isPanning) return
    
    const now = performance.now()
    const deltaTime = now - lastPanTime
    if (deltaTime < ULTRA_PAN_THROTTLE) return
    
    // 安全地阻止默认行为
    if (event.cancelable) {
      event.preventDefault()
    }
    
    const startTime = now
    
    // 取消之前的RAF
    if (primaryRafId) cancelAnimationFrame(primaryRafId)
    
    // 双重RAF确保超流畅
    primaryRafId = requestAnimationFrame(() => {
      secondaryRafId = requestAnimationFrame(() => {
        if (!panState.value.isPanning) return
        
        const deltaX = event.clientX - panState.value.startX
        const deltaY = event.clientY - panState.value.startY
        
        const newX = panState.value.startViewportX + deltaX
        const newY = panState.value.startViewportY + deltaY
        
        const constrained = ultraConstrainViewport(newX, newY, panState.value.bounds)
        
        // 预测性平滑
        const smoothed = predictSmoothing(constrained.x, constrained.y)
        
        // 直接更新DOM
        ultraUpdateCanvasTransform(smoothed.x, smoothed.y, ultraCachedTransform.scale)
        
        // 🚨 修复：同步更新视口状态
        viewport.value.x = smoothed.x
        viewport.value.y = smoothed.y
        
        // 性能监控
        const processTime = performance.now() - startTime
        perfMetrics.panFps = 1000 / deltaTime
        perfMetrics.avgPanTime = (perfMetrics.avgPanTime + processTime) / 2
        
        // 🚨 修复：实时输出画布拖动性能和位移信息
        if (Math.random() < 0.05) { // 5%概率输出，避免过多日志
          console.log(`📊 画布拖动: FPS=${perfMetrics.panFps.toFixed(1)}, 处理时间=${perfMetrics.avgPanTime.toFixed(2)}ms, 位移=(${deltaX.toFixed(1)}, ${deltaY.toFixed(1)})`)
        }
        
        lastPanTime = now
      })
    })
  }

  // 超级停止平移
  function stopUltraPan() {
    if (!panState.value.isPanning) return
    
    console.log('🛑 超级画布拖动结束')
    
    // 立即取消所有RAF
    if (primaryRafId) {
      cancelAnimationFrame(primaryRafId)
      primaryRafId = null
    }
    if (secondaryRafId) {
      cancelAnimationFrame(secondaryRafId)
      secondaryRafId = null
    }
    
    // 同步最终状态
    viewport.value.x = ultraCachedTransform.x
    viewport.value.y = ultraCachedTransform.y
    
    panState.value.isPanning = false
    
    // 恢复样式
    const element = getUltraCanvasContentElement()
    if (element) {
      element.style.pointerEvents = ''
      element.style.cursor = ''
    }
    
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    document.body.style.pointerEvents = ''
    
    // 移除事件监听（已经使用once自动移除）
    document.removeEventListener('mousemove', handleUltraPan, { capture: true } as any)
    
    ultraScheduleViewportUpdate()
    
    // 性能报告
    console.log(`📈 画布拖动性能报告: FPS=${perfMetrics.panFps.toFixed(1)}, 平均处理时间=${perfMetrics.avgPanTime.toFixed(2)}ms, 最终位置=(${viewport.value.x.toFixed(1)}, ${viewport.value.y.toFixed(1)})`)
  }

  // 计算视口尺寸
  const viewportWidth = computed(() => {
    if (!canvasContainer.value) return 1200 / viewport.value.scale
    return canvasContainer.value.clientWidth / viewport.value.scale
  })

  const viewportHeight = computed(() => {
    if (!canvasContainer.value) return 800 / viewport.value.scale
    return canvasContainer.value.clientHeight / viewport.value.scale
  })

  // 超级Canvas内容样式
  const ultraCanvasContentStyle = computed(() => {
    if (panState.value.isPanning) {
      // 平移时使用缓存变换，避免响应式开销
      return {
        width: `${canvasSize.value.width}px`,
        height: `${canvasSize.value.height}px`,
        transformOrigin: '0 0',
        position: 'relative' as const,
        willChange: 'transform',
        backfaceVisibility: 'hidden' as const,
        perspective: '1000px' as const,
        transformStyle: 'preserve-3d' as const,
        contain: 'layout style paint size' as const,
        isolation: 'isolate' as const
      }
    }
    
    return {
      width: `${canvasSize.value.width}px`,
      height: `${canvasSize.value.height}px`,
      transform: `translate3d(${viewport.value.x}px, ${viewport.value.y}px, 0) scale(${viewport.value.scale})`,
      transformOrigin: '0 0',
      position: 'relative' as const,
      willChange: 'auto',
      backfaceVisibility: 'hidden' as const,
      perspective: '1000px' as const,
      transformStyle: 'preserve-3d' as const,
      contain: 'layout style paint size' as const,
      isolation: 'isolate' as const
    }
  })

  // 工具函数
  function centerViewport() {
    if (!canvasContainer.value) return
    
    const containerRect = canvasContainer.value.getBoundingClientRect()
    const newX = (containerRect.width - canvasSize.value.width * viewport.value.scale) / 2
    const newY = (containerRect.height - canvasSize.value.height * viewport.value.scale) / 2
    
    viewport.value.x = newX
    viewport.value.y = newY
    
    ultraUpdateCanvasTransform(newX, newY, viewport.value.scale, true)
  }

  function resetZoom() {
    viewport.value.scale = 1
    centerViewport()
  }

  function focusOnPosition(x: number, y: number, scale?: number) {
    if (!canvasContainer.value) return
    
    const containerRect = canvasContainer.value.getBoundingClientRect()
    const centerX = containerRect.width / 2
    const centerY = containerRect.height / 2
    
    if (scale !== undefined) {
      viewport.value.scale = Math.max(
        viewport.value.minScale,
        Math.min(viewport.value.maxScale, scale)
      )
    }
    
    const newX = centerX - (x * viewport.value.scale)
    const newY = centerY - (y * viewport.value.scale)
    
    viewport.value.x = newX
    viewport.value.y = newY
    
    ultraUpdateCanvasTransform(newX, newY, viewport.value.scale, true)
  }

  // 超高性能增量平移 - 用于统一拖拽系统集成
  function panBy(deltaX: number, deltaY: number) {
    if (!canvasContainer.value) return
    
    // 计算边界约束
    const containerRect = canvasContainer.value.getBoundingClientRect()
    const bounds = ultraCalculateBounds(containerRect, viewport.value.scale)
    
    // 应用增量偏移
    const newX = viewport.value.x + deltaX
    const newY = viewport.value.y + deltaY
    
    // 应用边界约束
    const constrainedPos = ultraConstrainViewport(newX, newY, bounds)
    
    // 更新viewport状态
    viewport.value.x = constrainedPos.x
    viewport.value.y = constrainedPos.y
    
    // 高性能变换更新
    ultraUpdateCanvasTransform(constrainedPos.x, constrainedPos.y, viewport.value.scale)
    
    // 防抖视口更新通知
    ultraScheduleViewportUpdate()
  }

  // 超级清理函数
  function ultraCleanup() {
    if (primaryRafId) {
      cancelAnimationFrame(primaryRafId)
      primaryRafId = null
    }
    
    if (secondaryRafId) {
      cancelAnimationFrame(secondaryRafId)
      secondaryRafId = null
    }
    
    if (wheelRafId) {
      cancelAnimationFrame(wheelRafId)
      wheelRafId = null
    }
    
    if (viewportUpdateTimer) {
      clearTimeout(viewportUpdateTimer)
      viewportUpdateTimer = null
    }
    
    // 恢复canvas元素
    if (canvasContentElement) {
      canvasContentElement.style.willChange = 'auto'
      canvasContentElement.style.backfaceVisibility = ''
      canvasContentElement.style.perspective = ''
      canvasContentElement.style.transformStyle = ''
      canvasContentElement.style.contain = ''
      canvasContentElement.style.isolation = ''
      canvasContentElement = null
    }
    
    document.removeEventListener('mousemove', handleUltraPan, { capture: true } as any)
    document.removeEventListener('mouseup', stopUltraPan, { capture: true } as any)
    document.removeEventListener('mouseleave', stopUltraPan, { capture: true } as any)
    
    console.log('画布系统超级清理完成')
  }

  // 超级预热
  function ultraWarmup() {
    nextTick(() => {
      getUltraCanvasContentElement()
      console.log('画布系统超级预热完成')
    })
  }

  return {
    viewport,
    panState,
    viewportWidth,
    viewportHeight,
    canvasContentStyle: ultraCanvasContentStyle,
    handleWheel: handleUltraWheel,
    startPan: startUltraPan,
    panBy,
    centerViewport,
    resetZoom,
    focusOnPosition,
    cleanup: ultraCleanup,
    warmup: ultraWarmup
  }
} 