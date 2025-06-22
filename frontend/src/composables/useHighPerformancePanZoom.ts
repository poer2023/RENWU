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

// 性能常量
const WHEEL_THROTTLE = 8 // 120fps for smooth zoom
const PAN_THROTTLE = 8 // 120fps for smooth pan
const VIEWPORT_UPDATE_DEBOUNCE = 50

export function useHighPerformancePanZoom(
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

  // 性能优化变量
  let canvasContentElement: HTMLElement | null = null
  let rafId: number | null = null
  let wheelRafId: number | null = null
  let lastWheelTime = 0
  let lastPanTime = 0
  let viewportUpdateTimer: number | null = null
  
  // 缓存的变换矩阵
  let cachedTransform = {
    x: 0,
    y: 0,
    scale: 1,
    dirty: false
  }

  // 获取canvas内容元素
  function getCanvasContentElement(): HTMLElement | null {
    if (canvasContentElement) return canvasContentElement
    
    if (canvasContainer.value) {
      canvasContentElement = canvasContainer.value.querySelector('.canvas-content') as HTMLElement
      if (canvasContentElement) {
        // 启用GPU加速
        canvasContentElement.style.willChange = 'transform'
        canvasContentElement.style.backfaceVisibility = 'hidden'
        canvasContentElement.style.perspective = '1000px'
        canvasContentElement.style.contain = 'layout style paint'
      }
    }
    
    return canvasContentElement
  }

  // 高性能transform更新
  function updateCanvasTransform(x: number, y: number, scale: number, force = false) {
    const element = getCanvasContentElement()
    if (!element) return
    
    // 检查是否需要更新
    if (!force && 
        cachedTransform.x === x && 
        cachedTransform.y === y && 
        cachedTransform.scale === scale) {
      return
    }
    
    const transform = `translate3d(${x}px, ${y}px, 0) scale(${scale})`
    element.style.transform = transform
    
    cachedTransform = { x, y, scale, dirty: false }
  }

  // 计算视口边界
  function calculateBounds(containerRect: DOMRect, scale: number) {
    const maxX = containerRect.width * 0.5
    const maxY = containerRect.height * 0.5
    const minX = -(canvasSize.value.width * scale - containerRect.width * 0.5)
    const minY = -(canvasSize.value.height * scale - containerRect.height * 0.5)
    
    return { maxX, maxY, minX, minY }
  }

  // 应用约束
  function constrainViewport(x: number, y: number, bounds: any) {
    return {
      x: Math.max(bounds.minX, Math.min(bounds.maxX, x)),
      y: Math.max(bounds.minY, Math.min(bounds.maxY, y))
    }
  }

  // 防抖的视口更新
  function scheduleViewportUpdate() {
    if (viewportUpdateTimer) {
      clearTimeout(viewportUpdateTimer)
    }
    
    viewportUpdateTimer = window.setTimeout(() => {
      if (options.onViewportChange) {
        options.onViewportChange(viewport.value)
      }
    }, VIEWPORT_UPDATE_DEBOUNCE)
  }

  // 高性能滚轮处理
  function handleWheel(event: WheelEvent) {
    event.preventDefault()
    
    const now = performance.now()
    if (now - lastWheelTime < WHEEL_THROTTLE) return
    
    if (wheelRafId) {
      cancelAnimationFrame(wheelRafId)
    }
    
    wheelRafId = requestAnimationFrame(() => {
      const container = canvasContainer.value
      if (!container) return
      
      const rect = container.getBoundingClientRect()
      
      // 鼠标位置
      const mouseX = event.clientX - rect.left
      const mouseY = event.clientY - rect.top
      
      // 世界坐标
      const worldX = (mouseX - viewport.value.x) / viewport.value.scale
      const worldY = (mouseY - viewport.value.y) / viewport.value.scale
      
      // 计算新缩放
      const scaleFactor = event.deltaY > 0 ? 0.9 : 1.1
      const newScale = Math.max(
        viewport.value.minScale, 
        Math.min(viewport.value.maxScale, viewport.value.scale * scaleFactor)
      )
      
      if (Math.abs(newScale - viewport.value.scale) < 0.001) return
      
      // 计算新位置
      const newX = mouseX - worldX * newScale
      const newY = mouseY - worldY * newScale
      
      // 应用约束
      const bounds = calculateBounds(rect, newScale)
      const constrained = constrainViewport(newX, newY, bounds)
      
      // 直接更新DOM
      updateCanvasTransform(constrained.x, constrained.y, newScale)
      
      // 更新状态（延迟）
      viewport.value.x = constrained.x
      viewport.value.y = constrained.y
      viewport.value.scale = newScale
      
      scheduleViewportUpdate()
      lastWheelTime = now
    })
  }

  // 开始平移
  function startPan(event: MouseEvent) {
    // 支持左键和中键拖动
    if (event.button !== 0 && event.button !== 1) return
    
    const container = canvasContainer.value
    if (!container) return
    
    const rect = container.getBoundingClientRect()
    const bounds = calculateBounds(rect, viewport.value.scale)
    
    // 同步缓存的变换
    cachedTransform.x = viewport.value.x
    cachedTransform.y = viewport.value.y
    cachedTransform.scale = viewport.value.scale
    
    panState.value = {
      isPanning: true,
      startX: event.clientX,
      startY: event.clientY,
      startViewportX: viewport.value.x,
      startViewportY: viewport.value.y,
      bounds
    }
    
    // 获取canvas元素并启用优化
    const element = getCanvasContentElement()
    if (element) {
      element.style.pointerEvents = 'none' // 避免子元素干扰
    }
    
    document.body.style.cursor = 'grabbing'
    document.body.style.userSelect = 'none'
    
    // 事件监听
    document.addEventListener('mousemove', handlePan, { passive: false })
    document.addEventListener('mouseup', stopPan, { passive: true })
    document.addEventListener('mouseleave', stopPan, { passive: true })
  }

  // 处理平移
  function handlePan(event: MouseEvent) {
    if (!panState.value.isPanning) return
    
    const now = performance.now()
    if (now - lastPanTime < PAN_THROTTLE) return
    
    event.preventDefault()
    
    const deltaX = event.clientX - panState.value.startX
    const deltaY = event.clientY - panState.value.startY
    
    const newX = panState.value.startViewportX + deltaX
    const newY = panState.value.startViewportY + deltaY
    
    const constrained = constrainViewport(newX, newY, panState.value.bounds)
    
    // 直接更新DOM
    updateCanvasTransform(constrained.x, constrained.y, cachedTransform.scale)
    
    lastPanTime = now
  }

  // 停止平移
  function stopPan() {
    if (!panState.value.isPanning) return
    
    // 同步最终状态
    viewport.value.x = cachedTransform.x
    viewport.value.y = cachedTransform.y
    
    panState.value.isPanning = false
    
    // 恢复样式
    const element = getCanvasContentElement()
    if (element) {
      element.style.pointerEvents = ''
    }
    
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    
    // 移除事件监听
    document.removeEventListener('mousemove', handlePan)
    document.removeEventListener('mouseup', stopPan)
    document.removeEventListener('mouseleave', stopPan)
    
    scheduleViewportUpdate()
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

  // Canvas内容样式
  const canvasContentStyle = computed(() => {
    if (panState.value.isPanning) {
      // 平移时不使用响应式变换，避免性能问题
      return {
        width: `${canvasSize.value.width}px`,
        height: `${canvasSize.value.height}px`,
        transformOrigin: '0 0',
        position: 'relative' as const,
        willChange: 'transform',
        backfaceVisibility: 'hidden' as const,
        perspective: '1000px' as const,
        contain: 'layout style paint' as const
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
      contain: 'layout style paint' as const
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
    
    updateCanvasTransform(newX, newY, viewport.value.scale, true)
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
    
    updateCanvasTransform(newX, newY, viewport.value.scale, true)
  }

  // 清理函数
  function cleanup() {
    if (rafId) {
      cancelAnimationFrame(rafId)
      rafId = null
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
      canvasContentElement.style.contain = ''
      canvasContentElement = null
    }
    
    document.removeEventListener('mousemove', handlePan)
    document.removeEventListener('mouseup', stopPan)
    document.removeEventListener('mouseleave', stopPan)
  }

  // 预热
  function warmup() {
    nextTick(() => {
      getCanvasContentElement()
    })
  }

  return {
    viewport,
    panState,
    viewportWidth,
    viewportHeight,
    canvasContentStyle,
    handleWheel,
    startPan,
    centerViewport,
    resetZoom,
    focusOnPosition,
    cleanup,
    warmup
  }
} 