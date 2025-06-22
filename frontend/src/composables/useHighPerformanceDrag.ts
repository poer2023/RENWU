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

// 性能优化常量
const RECT_CACHE_TTL = 100 // 缓存100ms
const RAF_THROTTLE = 16 // 60fps
const POSITION_SAVE_DEBOUNCE = 300

export function useHighPerformanceDrag(
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
    element: null
  })

  // 性能优化缓存
  const rectCache = new Map<string, CachedRect>()
  const positionCache = new Map<number, { x: number; y: number }>()
  const transformCache = new Map<number, string>()
  
  // RAF 管理
  let dragRafId: number | null = null
  let lastRafTime = 0
  
  // 防抖定时器
  let savePositionTimer: number | null = null
  
  // GPU 加速元素池
  const gpuElements = new Set<HTMLElement>()

  // 获取缓存的rect
  function getCachedRect(key: string, element: HTMLElement): DOMRect {
    const cached = rectCache.get(key)
    const now = Date.now()
    
    if (cached && now - cached.timestamp < RECT_CACHE_TTL) {
      return cached.rect
    }
    
    const rect = element.getBoundingClientRect()
    rectCache.set(key, { rect, timestamp: now })
    return rect
  }

  // 启用GPU加速
  function enableGPUAcceleration(element: HTMLElement) {
    if (gpuElements.has(element)) return
    
    element.style.willChange = 'transform'
    element.style.backfaceVisibility = 'hidden'
    element.style.perspective = '1000px'
    element.style.transform = element.style.transform || 'translate3d(0,0,0)'
    
    gpuElements.add(element)
  }

  // 禁用GPU加速
  function disableGPUAcceleration(element: HTMLElement) {
    if (!gpuElements.has(element)) return
    
    element.style.willChange = 'auto'
    element.style.backfaceVisibility = ''
    element.style.perspective = ''
    
    gpuElements.delete(element)
  }

  // 高性能transform更新
  function updateTransform(element: HTMLElement, x: number, y: number, scale = 1, force = false) {
    const transform = `translate3d(${x}px, ${y}px, 0) scale(${scale})`
    const taskId = Number(element.dataset.taskId)
    
    // 检查是否需要更新
    if (!force && transformCache.get(taskId) === transform) return
    
    element.style.transform = transform
    transformCache.set(taskId, transform)
  }

  // 批量更新位置
  function batchUpdatePositions(updates: Array<{ element: HTMLElement; x: number; y: number; scale?: number }>) {
    // 使用DocumentFragment减少重绘
    requestAnimationFrame(() => {
      updates.forEach(({ element, x, y, scale = 1 }) => {
        updateTransform(element, x, y, scale)
      })
    })
  }

  // 高性能拖拽处理
  function handleDragMove(event: MouseEvent) {
    if (!dragState.value.isDragging || !dragState.value.task || !dragState.value.element) return
    
    const now = performance.now()
    if (now - lastRafTime < RAF_THROTTLE) return
    
    event.preventDefault()
    
    if (dragRafId) {
      cancelAnimationFrame(dragRafId)
    }
    
    dragRafId = requestAnimationFrame(() => {
      if (!dragState.value.isDragging || !dragState.value.task || !dragState.value.element) return
      
      // 使用缓存的rect
      const rect = getCachedRect('canvas', canvasContainer.value!)
      
      // 计算新位置
      const canvasMouseX = (event.clientX - rect.left - viewport.value.x) / viewport.value.scale
      const canvasMouseY = (event.clientY - rect.top - viewport.value.y) / viewport.value.scale
      
      const newX = canvasMouseX - dragState.value.offsetX
      const newY = canvasMouseY - dragState.value.offsetY
      
      // 边界约束（快速计算）
      const cardWidth = 240
      const cardHeight = 120
      const boundedX = Math.max(0, Math.min(canvasSize.value.width - cardWidth, newX))
      const boundedY = Math.max(0, Math.min(canvasSize.value.height - cardHeight, newY))
      
      // 直接更新DOM，避免Vue响应式开销
      updateTransform(dragState.value.element, boundedX, boundedY, 1.02)
      
      // 缓存位置
      positionCache.set(dragState.value.task.id, { x: boundedX, y: boundedY })
      
      lastRafTime = now
    })
  }

  // 开始拖拽
  function startDrag(task: Task, event: MouseEvent) {
    if (event.button !== 0) return
    
    event.preventDefault()
    event.stopPropagation()
    
    const element = document.querySelector(`[data-task-id="${task.id}"]`) as HTMLElement
    if (!element || !canvasContainer.value) return
    
    // 预缓存重要的rect
    const canvasRect = getCachedRect('canvas', canvasContainer.value)
    
    // 计算精确偏移
    const currentPos = taskPositions.value[task.id] || { x: 0, y: 0 }
    const canvasMouseX = (event.clientX - canvasRect.left - viewport.value.x) / viewport.value.scale
    const canvasMouseY = (event.clientY - canvasRect.top - viewport.value.y) / viewport.value.scale
    
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
      element
    }
    
    // 启用GPU加速
    enableGPUAcceleration(element)
    
    // 设置拖拽样式
    element.style.transition = 'none'
    element.style.zIndex = '1000'
    
    // 全局事件监听 - 使用passive优化
    document.addEventListener('mousemove', handleDragMove, { 
      passive: false, 
      capture: true 
    })
    document.addEventListener('mouseup', stopDrag, { 
      passive: true, 
      capture: true 
    })
    
    // 防止选择和设置光标
    document.body.style.userSelect = 'none'
    document.body.style.cursor = 'grabbing'
    
    // 回调
    if (options.onDragStart) {
      options.onDragStart(task)
    }
  }

  // 停止拖拽
  function stopDrag(event: MouseEvent) {
    if (!dragState.value.isDragging || !dragState.value.task || !dragState.value.element) return
    
    event.preventDefault()
    
    // 取消RAF
    if (dragRafId) {
      cancelAnimationFrame(dragRafId)
      dragRafId = null
    }
    
    const task = dragState.value.task
    const element = dragState.value.element
    
    // 获取最终位置
    const finalPosition = positionCache.get(task.id) || taskPositions.value[task.id]
    
    // 更新响应式数据（批量）
    if (finalPosition) {
      taskPositions.value[task.id] = finalPosition
      
      // 防抖保存位置
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
    element.style.transition = ''
    element.style.zIndex = ''
    updateTransform(element, finalPosition?.x || 0, finalPosition?.y || 0, 1, true)
    
    // 延迟禁用GPU加速，避免动画卡顿
    setTimeout(() => {
      disableGPUAcceleration(element)
    }, 200)
    
    // 恢复全局样式
    document.body.style.userSelect = ''
    document.body.style.cursor = ''
    
    // 移除事件监听
    document.removeEventListener('mousemove', handleDragMove, { capture: true } as any)
    document.removeEventListener('mouseup', stopDrag, { capture: true } as any)
    
    // 清空状态
    dragState.value = {
      isDragging: false,
      task: null,
      startX: 0,
      startY: 0,
      offsetX: 0,
      offsetY: 0,
      element: null
    }
    
    // 回调
    if (options.onDragEnd && finalPosition) {
      options.onDragEnd(task, finalPosition)
    }
  }

  // 清理函数
  function cleanup() {
    // 清理RAF
    if (dragRafId) {
      cancelAnimationFrame(dragRafId)
      dragRafId = null
    }
    
    // 清理定时器
    if (savePositionTimer) {
      clearTimeout(savePositionTimer)
      savePositionTimer = null
    }
    
    // 清理GPU加速
    gpuElements.forEach(element => {
      disableGPUAcceleration(element)
    })
    gpuElements.clear()
    
    // 清理缓存
    rectCache.clear()
    positionCache.clear()
    transformCache.clear()
    
    // 移除事件监听
    document.removeEventListener('mousemove', handleDragMove, { capture: true } as any)
    document.removeEventListener('mouseup', stopDrag, { capture: true } as any)
  }

  // 预热优化 - 预创建必要的样式
  function warmup() {
    nextTick(() => {
      if (canvasContainer.value) {
        getCachedRect('canvas', canvasContainer.value)
      }
    })
  }

  return {
    dragState,
    startDrag,
    cleanup,
    warmup,
    enableGPUAcceleration,
    disableGPUAcceleration,
    batchUpdatePositions
  }
} 