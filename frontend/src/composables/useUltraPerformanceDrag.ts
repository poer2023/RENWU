import { ref, Ref, nextTick } from 'vue'
import { type Task } from '@/stores/tasks'

interface DragState {
  isDragging: boolean
  task: Task | null
  startX: number
  startY: number
  offsetX: number
  offsetY: number
  element: HTMLElement | null
  ghost?: HTMLElement | null
}

interface DragOptions {
  onDragStart?: (task: Task) => void
  onDragEnd?: (task: Task, position: { x: number; y: number }) => void
  onPositionUpdate?: (taskId: number, x: number, y: number) => void
}

interface CachedRect {
  rect: DOMRect
  timestamp: number
}

// 超级性能优化常量
const ULTRA_RAF_THROTTLE = 8 // 120fps+ 双重RAF
const RECT_CACHE_TTL = 50 // 更短的缓存时间
const POSITION_SAVE_DEBOUNCE = 2000 // 2秒防抖，大幅减少API调用
const TRANSFORM_PRECISION = 1 // 像素精度，避免子像素渲染
const GPU_WARMUP_COUNT = 10 // GPU预热次数

export function useUltraPerformanceDrag(
  canvasContainer: Ref<HTMLElement | undefined>,
  taskPositions: Ref<{ [key: number]: { x: number; y: number } }>,
  viewport: Ref<{ x: number; y: number; scale: number }>,
  canvasSize: Ref<{ width: number; height: number }>,
  options: DragOptions = {}
) {
  // 拖拽状态
  const dragState = ref<DragState>({
    isDragging: false,
    task: null,
    startX: 0,
    startY: 0,
    offsetX: 0,
    offsetY: 0,
    element: null,
    ghost: null
  })

  // 超级缓存系统
  const rectCache = new Map<string, CachedRect>()
  const positionCache = new Map<number, { x: number; y: number }>()
  const transformCache = new Map<number, string>()
  const elementCache = new Map<number, HTMLElement>()
  
  // 双重RAF系统
  let primaryRafId: number | null = null
  let secondaryRafId: number | null = null
  let lastFrameTime = 0
  let frameCount = 0
  
  // 防抖和节流
  let savePositionTimer: number | null = null
  let lastUpdateTime = 0
  
  // GPU加速池
  const gpuElements = new Set<HTMLElement>()
  const transformBuffer = new Map<HTMLElement, { x: number; y: number; scale: number }>()
  
  // 性能监控
  const perfMetrics = {
    avgFrameTime: 0,
    fps: 0,
    lastUpdate: 0
  }

  // 超级缓存rect获取
  function getUltraCachedRect(key: string, element: HTMLElement): DOMRect {
    const cached = rectCache.get(key)
    const now = performance.now()
    
    if (cached && now - cached.timestamp < RECT_CACHE_TTL) {
      return cached.rect
    }
    
    const rect = element.getBoundingClientRect()
    rectCache.set(key, { rect, timestamp: now })
    return rect
  }

  // 预热GPU加速
  function warmupGPUAcceleration(element: HTMLElement) {
    if (gpuElements.has(element)) return
    
    // 强制GPU层创建
    element.style.willChange = 'transform'
    element.style.backfaceVisibility = 'hidden'
    element.style.perspective = '1000px'
    element.style.transformStyle = 'preserve-3d'
    element.style.contain = 'layout style paint'
    
    // 预热变换
    for (let i = 0; i < GPU_WARMUP_COUNT; i++) {
      element.style.transform = `translate3d(0,0,0) scale(1)`
    }
    
    gpuElements.add(element)
  }

  // 批量禁用GPU加速
  function cleanupGPUAcceleration(element: HTMLElement) {
    if (!gpuElements.has(element)) return
    
    // 延迟清理，避免闪烁
    setTimeout(() => {
      element.style.willChange = 'auto'
      element.style.backfaceVisibility = ''
      element.style.perspective = ''
      element.style.transformStyle = ''
      element.style.contain = ''
      gpuElements.delete(element)
    }, 300)
  }

  // 超高精度transform更新
  function ultraUpdateTransform(element: HTMLElement, x: number, y: number, scale = 1, force = false) {
    // 像素对齐，避免模糊
    const alignedX = Math.round(x * TRANSFORM_PRECISION) / TRANSFORM_PRECISION
    const alignedY = Math.round(y * TRANSFORM_PRECISION) / TRANSFORM_PRECISION
    const alignedScale = Math.round(scale * 1000) / 1000
    
    const transform = `translate3d(${alignedX}px, ${alignedY}px, 0) scale(${alignedScale})`
    const taskId = Number(element.dataset.taskId)
    
    // 更智能的缓存检查
    if (!force && transformCache.get(taskId) === transform) return false
    
    // 缓冲变换，批量应用
    transformBuffer.set(element, { x: alignedX, y: alignedY, scale: alignedScale })
    transformCache.set(taskId, transform)
    return true
  }

  // 批量应用变换
  function flushTransformBuffer() {
    if (transformBuffer.size === 0) return
    
    // 使用文档片段优化
    transformBuffer.forEach(({ x, y, scale }, element) => {
      element.style.transform = `translate3d(${x}px, ${y}px, 0) scale(${scale})`
    })
    
    transformBuffer.clear()
  }

  // 双重RAF超级拖拽处理
  function handleUltraDragMove(event: MouseEvent) {
    if (!dragState.value.isDragging || !dragState.value.task || !dragState.value.element) return
    
    const now = performance.now()
    const deltaTime = now - lastFrameTime
    
    // 🚨 修复：降低节流阈值，确保更高帧率
    if (deltaTime < 4) return // 250fps 目标
    
    event.preventDefault()
    
    // 取消之前的RAF
    if (primaryRafId) cancelAnimationFrame(primaryRafId)
    if (secondaryRafId) cancelAnimationFrame(secondaryRafId)
    
    // 🚨 修复：简化为单RAF，提高响应速度
    primaryRafId = requestAnimationFrame(() => {
      if (!dragState.value.isDragging || !dragState.value.task || !dragState.value.element) return
      
      const startCalc = performance.now()
      
      // 使用超级缓存的rect
      const rect = getUltraCachedRect('canvas', canvasContainer.value!)
      
      // 优化的位置计算
      const scale = viewport.value.scale
      const canvasMouseX = (event.clientX - rect.left - viewport.value.x) / scale
      const canvasMouseY = (event.clientY - rect.top - viewport.value.y) / scale
      
      const newX = canvasMouseX - dragState.value.offsetX
      const newY = canvasMouseY - dragState.value.offsetY
      
      // 快速边界检查
      const cardWidth = 240
      const cardHeight = 120
      const boundedX = Math.max(0, Math.min(canvasSize.value.width - cardWidth, newX))
      const boundedY = Math.max(0, Math.min(canvasSize.value.height - cardHeight, newY))
      
      // 🚨 修复：直接更新DOM，跳过缓存检查
      const transform = `translate3d(${boundedX}px, ${boundedY}px, 0) scale(1.02)`
      dragState.value.element.style.transform = transform
      
      // 缓存位置
      positionCache.set(dragState.value.task.id, { x: boundedX, y: boundedY })
      
      // 性能监控
      const calcTime = performance.now() - startCalc
      frameCount++
      perfMetrics.avgFrameTime = (perfMetrics.avgFrameTime * (frameCount - 1) + calcTime) / frameCount
      perfMetrics.fps = 1000 / deltaTime
      
      // 🚨 修复：实时输出性能数据
      if (frameCount % 60 === 0) { // 每60帧输出一次
        console.log(`拖拽性能: 平均帧时间 ${perfMetrics.avgFrameTime.toFixed(2)}ms, 平均FPS ${perfMetrics.fps.toFixed(1)}`)
      }
      
      lastFrameTime = now
    })
  }

  // 创建拖拽幽灵元素（可选优化）
  function createDragGhost(element: HTMLElement): HTMLElement {
    const ghost = element.cloneNode(true) as HTMLElement
    
    // 幽灵样式
    ghost.style.position = 'absolute'
    ghost.style.pointerEvents = 'none'
    ghost.style.opacity = '0.8'
    ghost.style.transform = element.style.transform
    ghost.style.zIndex = '1001'
    
    // 预热GPU
    warmupGPUAcceleration(ghost)
    
    document.body.appendChild(ghost)
    return ghost
  }

  // 超级开始拖拽
  function startUltraDrag(task: Task, event: MouseEvent) {
    if (event.button !== 0) return
    
    event.preventDefault()
    event.stopPropagation()
    
    console.log('🚀 开始拖拽任务:', task.title)
    
    // 使用缓存的元素查找
    let element = elementCache.get(task.id)
    if (!element) {
      element = document.querySelector(`[data-task-id="${task.id}"]`) as HTMLElement
      if (element) elementCache.set(task.id, element)
    }
    
    if (!element || !canvasContainer.value) return
    
    // 预缓存关键rect
    const canvasRect = getUltraCachedRect('canvas', canvasContainer.value)
    
    // 精确偏移计算
    const currentPos = taskPositions.value[task.id] || { x: 0, y: 0 }
    const scale = viewport.value.scale
    const canvasMouseX = (event.clientX - canvasRect.left - viewport.value.x) / scale
    const canvasMouseY = (event.clientY - canvasRect.top - viewport.value.y) / scale
    
    const offsetX = canvasMouseX - currentPos.x
    const offsetY = canvasMouseY - currentPos.y
    
    // 设置拖拽状态
    dragState.value = {
      isDragging: true,
      task,
      startX: event.clientX,
      startY: event.clientY,
      offsetX,
      offsetY,
      element,
      ghost: null
    }
    
    // 预热GPU加速
    warmupGPUAcceleration(element)
    
    // 优化拖拽样式
    element.style.transition = 'none'
    element.style.zIndex = '1000'
    element.style.willChange = 'transform'
    
    // 全局事件监听 - 高性能配置
    document.addEventListener('mousemove', handleUltraDragMove, { 
      passive: false,
      capture: true 
    })
    document.addEventListener('mouseup', stopUltraDrag, { 
      passive: false,
      capture: true,
      once: true
    })
    
    // 性能优化的全局样式
    document.body.style.userSelect = 'none'
    document.body.style.cursor = 'grabbing'
    
    // 初始化性能监控
    lastFrameTime = performance.now()
    frameCount = 0
    
    console.log('✅ 拖拽系统已启动，GPU加速已激活')
    
    // 回调
    if (options.onDragStart) {
      options.onDragStart(task)
    }
  }

  // 超级停止拖拽
  function stopUltraDrag(event: MouseEvent) {
    if (!dragState.value.isDragging || !dragState.value.task || !dragState.value.element) return
    
    event.preventDefault()
    
    // 立即取消所有RAF
    if (primaryRafId) {
      cancelAnimationFrame(primaryRafId)
      primaryRafId = null
    }
    if (secondaryRafId) {
      cancelAnimationFrame(secondaryRafId)
      secondaryRafId = null
    }
    
    const task = dragState.value.task
    const element = dragState.value.element
    const ghost = dragState.value.ghost
    
    // 获取最终位置
    const finalPosition = positionCache.get(task.id) || taskPositions.value[task.id]
    
    // 批量更新响应式数据
    if (finalPosition) {
      taskPositions.value[task.id] = finalPosition
      
      // 超长防抖，大幅减少API调用
      if (savePositionTimer) {
        clearTimeout(savePositionTimer)
      }
      
      savePositionTimer = window.setTimeout(() => {
        if (options.onPositionUpdate && finalPosition) {
          options.onPositionUpdate(task.id, finalPosition.x, finalPosition.y)
        }
      }, POSITION_SAVE_DEBOUNCE)
    }
    
    // 恢复元素样式
    element.style.transition = 'transform 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94)'
    element.style.zIndex = ''
    element.style.pointerEvents = ''
    
    // 最终位置设置
    if (finalPosition) {
      ultraUpdateTransform(element, finalPosition.x, finalPosition.y, 1, true)
      flushTransformBuffer()
    }
    
    // 清理幽灵元素
    if (ghost) {
      ghost.remove()
    }
    
    // 延迟清理GPU加速
    cleanupGPUAcceleration(element)
    
    // 恢复全局样式
    document.body.style.userSelect = ''
    document.body.style.cursor = ''
    document.body.style.pointerEvents = ''
    
    // 移除事件监听
    document.removeEventListener('mousemove', handleUltraDragMove, { capture: true } as any)
    document.removeEventListener('mouseup', stopUltraDrag, { capture: true } as any)
    
    // 清空状态
    dragState.value = {
      isDragging: false,
      task: null,
      startX: 0,
      startY: 0,
      offsetX: 0,
      offsetY: 0,
      element: null,
      ghost: null
    }
    
    // 性能报告
    console.log(`拖拽性能: 平均帧时间 ${perfMetrics.avgFrameTime.toFixed(2)}ms, 平均FPS ${perfMetrics.fps.toFixed(1)}`)
    
    // 回调
    if (options.onDragEnd && finalPosition) {
      options.onDragEnd(task, finalPosition)
    }
  }

  // 预热优化系统
  function ultraWarmup() {
    nextTick(() => {
      if (canvasContainer.value) {
        // 预缓存重要rect
        getUltraCachedRect('canvas', canvasContainer.value)
        
        // 预热所有任务元素
        Object.keys(taskPositions.value).forEach(taskIdStr => {
          const taskId = Number(taskIdStr)
          const element = document.querySelector(`[data-task-id="${taskId}"]`) as HTMLElement
          if (element) {
            elementCache.set(taskId, element)
            warmupGPUAcceleration(element)
          }
        })
        
        console.log('拖拽系统超级预热完成')
      }
    })
  }

  // 超级清理
  function ultraCleanup() {
    // 清理RAF
    if (primaryRafId) {
      cancelAnimationFrame(primaryRafId)
      primaryRafId = null
    }
    if (secondaryRafId) {
      cancelAnimationFrame(secondaryRafId)
      secondaryRafId = null
    }
    
    // 清理定时器
    if (savePositionTimer) {
      clearTimeout(savePositionTimer)
      savePositionTimer = null
    }
    
    // 批量清理GPU加速
    gpuElements.forEach(element => {
      cleanupGPUAcceleration(element)
    })
    
    // 清理所有缓存
    rectCache.clear()
    positionCache.clear()
    transformCache.clear()
    elementCache.clear()
    transformBuffer.clear()
    gpuElements.clear()
    
    // 移除事件监听
    document.removeEventListener('mousemove', handleUltraDragMove, { capture: true } as any)
    document.removeEventListener('mouseup', stopUltraDrag, { capture: true } as any)
    
    console.log('拖拽系统超级清理完成')
  }

  return {
    dragState,
    startDrag: startUltraDrag,
    cleanup: ultraCleanup,
    warmup: ultraWarmup,
    perfMetrics: ref(perfMetrics)
  }
} 