import { ref, Ref, computed } from 'vue'
import { throttle } from 'lodash'

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
  maxX: number
  maxY: number
  minX: number
  minY: number
}

interface PanZoomOptions {
  minScale?: number
  maxScale?: number
  onViewportChange?: (viewport: ViewportState) => void
}

export function useCanvasPanZoom(
  canvasContainer: Ref<HTMLElement | undefined>,
  canvasSize: Ref<{ width: number; height: number }>,
  options: PanZoomOptions = {}
) {
  // Viewport state (for pan and zoom)
  const viewport = ref<ViewportState>({
    x: 0,
    y: 0,
    scale: 1,
    minScale: options.minScale || 0.1,
    maxScale: options.maxScale || 3
  })

  // Pan state
  const panState = ref<PanState>({
    isPanning: false,
    startX: 0,
    startY: 0,
    startViewportX: 0,
    startViewportY: 0,
    maxX: 0,
    maxY: 0,
    minX: 0,
    minY: 0
  })

  // 缓存的transform值，避免频繁触发响应式更新
  let cachedTransform = {
    x: 0,
    y: 0,
    scale: 1
  }

  // Canvas content元素的引用
  const canvasContentRef = ref<HTMLElement>()

  // 平移RAF ID管理
  const panRafId = ref<number | null>(null)
  const wheelRafId = ref<number | null>(null)

  // 使用 throttle 限制高频操作
  const throttledViewportUpdate = throttle(() => {
    if (!panState.value.isPanning && options.onViewportChange) {
      options.onViewportChange(viewport.value)
    }
  }, 16) // 60fps

  // Computed viewport dimensions
  const viewportWidth = computed(() => {
    if (!canvasContainer.value) return 1200 / viewport.value.scale
    return canvasContainer.value.getBoundingClientRect().width / viewport.value.scale
  })

  const viewportHeight = computed(() => {
    if (!canvasContainer.value) return 800 / viewport.value.scale
    return canvasContainer.value.getBoundingClientRect().height / viewport.value.scale
  })

  // Canvas content style
  const canvasContentStyle = computed(() => {
    if (panState.value.isPanning) {
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

  // 处理滚轮缩放
  function handleWheel(event: WheelEvent) {
    event.preventDefault()
    
    if (wheelRafId.value) {
      cancelAnimationFrame(wheelRafId.value)
    }
    
    wheelRafId.value = requestAnimationFrame(() => {
      const rect = canvasContainer.value?.getBoundingClientRect()
      if (!rect) return
      
      // 获取鼠标在画布中的位置
      const mouseX = event.clientX - rect.left
      const mouseY = event.clientY - rect.top
      
      // 计算缩放前的世界坐标
      const worldX = (mouseX - viewport.value.x) / viewport.value.scale
      const worldY = (mouseY - viewport.value.y) / viewport.value.scale
      
      // 计算缩放因子
      const scaleFactor = event.deltaY > 0 ? 0.9 : 1.1
      const newScale = Math.max(
        viewport.value.minScale, 
        Math.min(viewport.value.maxScale, viewport.value.scale * scaleFactor)
      )
      
      if (newScale === viewport.value.scale) return
      
      // 计算新的视口位置，保持鼠标位置不变
      const newX = mouseX - worldX * newScale
      const newY = mouseY - worldY * newScale
      
      // 应用约束
      const maxX = rect.width * 0.5
      const maxY = rect.height * 0.5
      const minX = -(canvasSize.value.width * newScale - rect.width * 0.5)
      const minY = -(canvasSize.value.height * newScale - rect.height * 0.5)
      
      viewport.value = {
        ...viewport.value,
        x: Math.max(minX, Math.min(maxX, newX)),
        y: Math.max(minY, Math.min(maxY, newY)),
        scale: newScale
      }
      
      throttledViewportUpdate()
    })
  }

  // 开始平移
  function startPan(event: MouseEvent) {
    const rect = canvasContainer.value?.getBoundingClientRect()
    if (!rect) return
    
    // 预计算边界约束
    const maxX = rect.width * 0.5
    const maxY = rect.height * 0.5
    const minX = -(canvasSize.value.width * viewport.value.scale - rect.width * 0.5)
    const minY = -(canvasSize.value.height * viewport.value.scale - rect.height * 0.5)
    
    // 同步当前的viewport到缓存
    cachedTransform.x = viewport.value.x
    cachedTransform.y = viewport.value.y
    cachedTransform.scale = viewport.value.scale
    
    panState.value = {
      isPanning: true,
      startX: event.clientX,
      startY: event.clientY,
      startViewportX: viewport.value.x,
      startViewportY: viewport.value.y,
      maxX,
      maxY,
      minX,
      minY
    }
    
    document.body.style.cursor = 'grabbing'
    
    // 获取canvas content元素的引用
    const contentElement = canvasContainer.value?.querySelector('.canvas-content') as HTMLElement
    if (contentElement) {
      canvasContentRef.value = contentElement
      contentElement.style.willChange = 'transform'
      contentElement.style.transform = `translate3d(${cachedTransform.x}px, ${cachedTransform.y}px, 0) scale(${cachedTransform.scale})`
    }
    
    document.addEventListener('mousemove', handlePan, { passive: false })
    document.addEventListener('mouseup', stopPan, { passive: false })
    document.addEventListener('mouseleave', stopPan, { passive: false })
    
    document.body.style.userSelect = 'none'
  }

  // 处理平移
  function handlePan(event: MouseEvent) {
    if (!panState.value.isPanning || !canvasContentRef.value) return
    
    event.preventDefault()
    
    const deltaX = event.clientX - panState.value.startX
    const deltaY = event.clientY - panState.value.startY
    
    const newX = panState.value.startViewportX + deltaX
    const newY = panState.value.startViewportY + deltaY
    
    const constrainedX = Math.max(panState.value.minX, Math.min(panState.value.maxX, newX))
    const constrainedY = Math.max(panState.value.minY, Math.min(panState.value.maxY, newY))
    
    cachedTransform.x = constrainedX
    cachedTransform.y = constrainedY
    
    // 直接操作DOM，绕过Vue的响应式系统
    canvasContentRef.value.style.transform = `translate3d(${constrainedX}px, ${constrainedY}px, 0) scale(${cachedTransform.scale})`
  }

  // 停止平移
  function stopPan() {
    if (panRafId.value) {
      cancelAnimationFrame(panRafId.value)
      panRafId.value = null
    }
    
    // 同步缓存的值回到响应式数据
    viewport.value.x = cachedTransform.x
    viewport.value.y = cachedTransform.y
    
    panState.value.isPanning = false
    document.body.style.cursor = 'default'
    document.body.style.userSelect = ''
    
    if (canvasContentRef.value) {
      canvasContentRef.value.style.willChange = 'auto'
    }
    
    document.removeEventListener('mousemove', handlePan)
    document.removeEventListener('mouseup', stopPan)
    document.removeEventListener('mouseleave', stopPan)
  }

  // 居中视口
  function centerViewport() {
    if (!canvasContainer.value) return
    
    const containerRect = canvasContainer.value.getBoundingClientRect()
    viewport.value.x = (containerRect.width - canvasSize.value.width * viewport.value.scale) / 2
    viewport.value.y = (containerRect.height - canvasSize.value.height * viewport.value.scale) / 2
  }

  // 重置缩放
  function resetZoom() {
    viewport.value.scale = 1
    centerViewport()
  }

  // 移动视口到指定位置
  function moveViewport(x: number, y: number) {
    viewport.value.x = -x * viewport.value.scale
    viewport.value.y = -y * viewport.value.scale
  }

  // 聚焦到指定位置
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
    
    viewport.value.x = centerX - (x * viewport.value.scale)
    viewport.value.y = centerY - (y * viewport.value.scale)
  }

  // Cleanup
  function cleanup() {
    if (wheelRafId.value) {
      cancelAnimationFrame(wheelRafId.value)
    }
    if (panRafId.value) {
      cancelAnimationFrame(panRafId.value)
    }
    document.removeEventListener('mousemove', handlePan)
    document.removeEventListener('mouseup', stopPan)
    document.removeEventListener('mouseleave', stopPan)
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
    moveViewport,
    focusOnPosition,
    cleanup
  }
} 