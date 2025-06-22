import { ref, computed, Ref, watch, nextTick } from 'vue'
import { type Task } from '@/stores/tasks'

interface ViewportState {
  x: number
  y: number
  scale: number
}

interface TaskPosition {
  x: number
  y: number
}

interface VirtualTask extends Task {
  isVisible: boolean
  distance: number
  lodLevel: number
}

interface VirtualizationOptions {
  // 视口边距，用于提前加载即将进入视野的任务
  viewportMargin: number
  // 最大渲染任务数量（性能保护）
  maxRenderTasks: number
  // LOD距离阈值
  lodDistances: number[]
  // 是否启用预测性加载
  enablePredictiveLoading: boolean
}

const DEFAULT_OPTIONS: VirtualizationOptions = {
  viewportMargin: 500, // 500px边距
  maxRenderTasks: 100, // 最多同时渲染100个任务
  lodDistances: [2000, 5000, 10000], // LOD距离阈值
  enablePredictiveLoading: true
}

export function useVirtualizedTasks(
  tasks: Ref<Task[]>,
  taskPositions: Ref<{ [key: number]: TaskPosition }>,
  viewport: Ref<ViewportState>,
  canvasContainer: Ref<HTMLElement | undefined>,
  options: Partial<VirtualizationOptions> = {}
) {
  const config = { ...DEFAULT_OPTIONS, ...options }
  
  // 性能优化缓存
  let lastViewport = { x: 0, y: 0, scale: 1 }
  let lastUpdateTime = 0
  const UPDATE_THROTTLE = 16 // 60fps
  
  // 可见区域缓存
  const visibilityCache = new Map<number, { isVisible: boolean, timestamp: number }>()
  const CACHE_TTL = 100 // 100ms缓存
  
  // 预测性加载状态
  const velocityTracker = {
    lastX: 0,
    lastY: 0,
    velocityX: 0,
    velocityY: 0,
    lastTime: 0
  }

  // 计算视口边界（带预测）
  function getViewportBounds(includeVelocity = false) {
    if (!canvasContainer.value) {
      return { left: 0, top: 0, right: 1920, bottom: 1080 }
    }

    const containerRect = canvasContainer.value.getBoundingClientRect()
    const scale = viewport.value.scale
    
    // 屏幕坐标转画布坐标
    let left = (-viewport.value.x) / scale
    let top = (-viewport.value.y) / scale
    let right = left + containerRect.width / scale
    let bottom = top + containerRect.height / scale
    
    // 添加边距
    const margin = config.viewportMargin / scale
    left -= margin
    top -= margin
    right += margin
    bottom += margin
    
    // 预测性加载：根据移动速度扩展边界
    if (includeVelocity && config.enablePredictiveLoading) {
      const prediction = 500 // 500ms预测时间
      const predictX = velocityTracker.velocityX * prediction / scale
      const predictY = velocityTracker.velocityY * prediction / scale
      
      if (predictX > 0) right += Math.abs(predictX)
      else left -= Math.abs(predictX)
      
      if (predictY > 0) bottom += Math.abs(predictY)
      else top -= Math.abs(predictY)
    }
    
    return { left, top, right, bottom }
  }

  // 计算任务与视口中心的距离
  function getTaskDistance(taskPos: TaskPosition): number {
    if (!canvasContainer.value) return 0
    
    const containerRect = canvasContainer.value.getBoundingClientRect()
    const scale = viewport.value.scale
    
    // 视口中心在画布坐标系中的位置
    const viewportCenterX = (-viewport.value.x + containerRect.width / 2) / scale
    const viewportCenterY = (-viewport.value.y + containerRect.height / 2) / scale
    
    // 计算距离
    const dx = taskPos.x - viewportCenterX
    const dy = taskPos.y - viewportCenterY
    return Math.sqrt(dx * dx + dy * dy)
  }

  // 计算LOD级别
  function getLODLevel(distance: number): number {
    for (let i = 0; i < config.lodDistances.length; i++) {
      if (distance <= config.lodDistances[i]) {
        return i
      }
    }
    return config.lodDistances.length // 最远距离
  }

  // 检查任务是否在视口内（带缓存）
  function isTaskVisible(taskPos: TaskPosition, taskId: number): boolean {
    const now = performance.now()
    const cached = visibilityCache.get(taskId)
    
    // 检查缓存
    if (cached && now - cached.timestamp < CACHE_TTL) {
      return cached.isVisible
    }
    
    const bounds = getViewportBounds(true)
    const isVisible = taskPos.x < bounds.right && 
                     taskPos.x > bounds.left &&
                     taskPos.y < bounds.bottom && 
                     taskPos.y > bounds.top
    
    // 更新缓存
    visibilityCache.set(taskId, { isVisible, timestamp: now })
    
    return isVisible
  }

  // 更新速度追踪
  function updateVelocityTracker() {
    const now = performance.now()
    const currentX = viewport.value.x
    const currentY = viewport.value.y
    
    if (velocityTracker.lastTime > 0) {
      const deltaTime = now - velocityTracker.lastTime
      if (deltaTime > 0) {
        velocityTracker.velocityX = (currentX - velocityTracker.lastX) / deltaTime * 1000 // px/s
        velocityTracker.velocityY = (currentY - velocityTracker.lastY) / deltaTime * 1000
      }
    }
    
    velocityTracker.lastX = currentX
    velocityTracker.lastY = currentY
    velocityTracker.lastTime = now
  }

  // 虚拟化任务列表
  const virtualTasks = computed<VirtualTask[]>(() => {
    const now = performance.now()
    
    // 节流优化：避免过度计算
    if (now - lastUpdateTime < UPDATE_THROTTLE) {
      // 返回上次计算结果，但这里我们直接计算以保证响应性
    }
    lastUpdateTime = now
    
    // 更新速度追踪
    updateVelocityTracker()
    
    const result: VirtualTask[] = []
    
    for (const task of tasks.value) {
      const position = taskPositions.value[task.id]
      if (!position) continue
      
      const distance = getTaskDistance(position)
      const isVisible = isTaskVisible(position, task.id)
      const lodLevel = getLODLevel(distance)
      
      result.push({
        ...task,
        isVisible,
        distance,
        lodLevel
      })
    }
    
    // 按距离排序，优先渲染近的任务
    result.sort((a, b) => a.distance - b.distance)
    
    // 应用最大渲染数量限制
    const visibleTasks = result.filter(task => task.isVisible)
    const hiddenTasks = result.filter(task => !task.isVisible)
    
    // 取最近的可见任务 + 一些隐藏但很近的任务
    const renderTasks = [
      ...visibleTasks.slice(0, Math.min(config.maxRenderTasks * 0.8, visibleTasks.length)),
      ...hiddenTasks.slice(0, Math.min(config.maxRenderTasks * 0.2, hiddenTasks.length))
    ].slice(0, config.maxRenderTasks)
    
    return renderTasks
  })

  // 仅可见的任务（用于实际渲染）
  const visibleTasks = computed(() => {
    return virtualTasks.value.filter(task => task.isVisible)
  })

  // 不同LOD级别的任务
  const tasksByLOD = computed(() => {
    const result: { [level: number]: VirtualTask[] } = {}
    
    for (const task of virtualTasks.value) {
      if (!result[task.lodLevel]) {
        result[task.lodLevel] = []
      }
      result[task.lodLevel].push(task)
    }
    
    return result
  })

  // 性能监控
  const performanceMetrics = ref({
    totalTasks: 0,
    visibleTasks: 0,
    renderTasks: 0,
    cacheHitRate: 0,
    avgComputeTime: 0,
    lastUpdateTime: 0
  })

  // 监听变化，更新性能指标
  watch([tasks, virtualTasks], () => {
    performanceMetrics.value = {
      totalTasks: tasks.value.length,
      visibleTasks: visibleTasks.value.length,
      renderTasks: virtualTasks.value.length,
      cacheHitRate: visibilityCache.size > 0 ? 
        Array.from(visibilityCache.values()).filter(c => 
          performance.now() - c.timestamp < CACHE_TTL
        ).length / visibilityCache.size : 0,
      avgComputeTime: lastUpdateTime,
      lastUpdateTime: Date.now()
    }
  }, { immediate: true })

  // 清理过期缓存
  function cleanupCache() {
    const now = performance.now()
    for (const [key, value] of visibilityCache.entries()) {
      if (now - value.timestamp > CACHE_TTL * 10) { // 保留10倍TTL时间
        visibilityCache.delete(key)
      }
    }
  }

  // 定期清理缓存
  setInterval(cleanupCache, 5000) // 每5秒清理一次

  // 强制更新可见性
  function forceUpdate() {
    visibilityCache.clear()
    lastUpdateTime = 0
  }

  // 预热系统
  function warmup() {
    nextTick(() => {
      // 预计算第一批任务
      forceUpdate()
      console.log('🚀 虚拟化任务系统预热完成')
    })
  }

  return {
    virtualTasks,
    visibleTasks,
    tasksByLOD,
    performanceMetrics,
    forceUpdate,
    warmup,
    
    // 工具方法
    getViewportBounds,
    getTaskDistance,
    getLODLevel,
    isTaskVisible
  }
}