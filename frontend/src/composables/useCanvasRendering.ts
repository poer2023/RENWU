import { ref, computed, nextTick, readonly, type Ref } from 'vue'
import { throttle } from 'lodash'
import type { Task } from '@/stores/tasks'

interface RenderingOptions {
  taskCardWidth?: number
  taskCardHeight?: number
  visibilityMargin?: number
  performanceMode?: boolean
}

interface PerformanceMetrics {
  lastRenderTime: number
  frameCount: number
  avgFrameTime: number
  droppedFrames: number
}

interface ViewportBounds {
  left: number
  top: number
  right: number
  bottom: number
  lastUpdate: number
}

export function useCanvasRendering(
  tasks: Readonly<Ref<Task[]>>,
  viewport: Readonly<Ref<{ x: number; y: number; scale: number }>>,
  canvasContainer: Ref<HTMLElement | undefined>,
  options: RenderingOptions = {}
) {
  // Default options
  const {
    taskCardWidth = 240,
    taskCardHeight = 120,
    visibilityMargin = 300,
    performanceMode = true
  } = options

  // Performance metrics
  const performanceMetrics = ref<PerformanceMetrics>({
    lastRenderTime: 0,
    frameCount: 0,
    avgFrameTime: 0,
    droppedFrames: 0
  })

  // Visible bounds cache
  const visibleBounds = ref<ViewportBounds>({
    left: 0,
    top: 0,
    right: 0,
    bottom: 0,
    lastUpdate: 0
  })

  // Cached visible tasks
  let cachedVisibleTasks: Task[] = []
  let lastVisibleTasksUpdate = 0
  const isPanning = ref(false)

  // Calculate visible bounds
  function calculateVisibleBounds() {
    if (!canvasContainer.value) return null

    const container = canvasContainer.value
    const rect = container.getBoundingClientRect()
    
    const currentX = viewport.value.x
    const currentY = viewport.value.y
    const currentScale = viewport.value.scale
    
    return {
      left: (-currentX) / currentScale - visibilityMargin,
      top: (-currentY) / currentScale - visibilityMargin,
      right: (-currentX) / currentScale + (rect.width / currentScale) + visibilityMargin,
      bottom: (-currentY) / currentScale + (rect.height / currentScale) + visibilityMargin
    }
  }

  // Check if task is visible in current viewport
  function isTaskVisible(task: Task, taskPositions: Record<number, { x: number; y: number }>) {
    const bounds = calculateVisibleBounds()
    if (!bounds) return true

    const pos = taskPositions[task.id]
    if (!pos) return true

    // Quick boundary check
    return !(pos.x + taskCardWidth < bounds.left || 
             pos.x > bounds.right || 
             pos.y + taskCardHeight < bounds.top || 
             pos.y > bounds.bottom)
  }

  // Virtualized rendering - only render visible tasks
  function getVisibleTasks(taskPositions: Record<number, { x: number; y: number }>) {
    // If tasks are few, render all
    if (tasks.value.length < 50 && !performanceMode) {
      return tasks.value
    }
    
    // Use cache during panning to reduce calculations
    const now = Date.now()
    if (isPanning.value && now - lastVisibleTasksUpdate < 100) {
      return cachedVisibleTasks
    }

    // Update visible bounds cache
    const bounds = calculateVisibleBounds()
    if (!bounds) return tasks.value

    // Filter visible tasks
    cachedVisibleTasks = tasks.value.filter(task => 
      isTaskVisible(task, taskPositions)
    )
    
    lastVisibleTasksUpdate = now
    return cachedVisibleTasks
  }

  // Performance monitoring
  function measureRenderPerformance<T>(fn: () => T): T {
    const startTime = performance.now()
    const result = fn()
    
    nextTick(() => {
      const endTime = performance.now()
      const renderTime = endTime - startTime
      
      performanceMetrics.value.lastRenderTime = renderTime
      performanceMetrics.value.frameCount++
      
      // Calculate average frame time
      const prevAvg = performanceMetrics.value.avgFrameTime
      const frameCount = performanceMetrics.value.frameCount
      performanceMetrics.value.avgFrameTime = 
        (prevAvg * (frameCount - 1) + renderTime) / frameCount
      
      // Track dropped frames (over 16.67ms = under 60fps)
      if (renderTime > 16.67) {
        performanceMetrics.value.droppedFrames++
        if (process.env.NODE_ENV === 'development') {
          console.warn(`Canvas render time: ${renderTime.toFixed(2)}ms (over 16.67ms threshold)`)
        }
      }
    })
    
    return result
  }

  // Optimized render function
  function optimizedRender() {
    return measureRenderPerformance(() => {
      // Trigger re-render logic here
      return true
    })
  }

  // Throttled viewport update for performance
  const throttledViewportUpdate = throttle(() => {
    if (!isPanning.value) {
      optimizedRender()
    }
  }, 16) // 60fps

  // Lightweight pan update for smooth panning
  const lightweightPanUpdate = throttle(() => {
    // Lightweight update during panning
    visibleBounds.value.lastUpdate = Date.now()
  }, 8) // 120fps for smoother panning

  // Task position styling
  function getTaskPositionStyle(
    task: Task, 
    taskPositions: Record<number, { x: number; y: number }>,
    isDragging = false
  ) {
    const position = taskPositions[task.id] || { x: 0, y: 0 }
    
    if (isDragging) {
      return {
        position: 'absolute' as const,
        left: '0px',
        top: '0px',
        transform: `translate3d(${position.x}px, ${position.y}px, 0) scale(1.02)`,
        zIndex: 1000,
        willChange: 'transform' as const
      }
    }
    
    return {
      position: 'absolute' as const,
      left: '0px',
      top: '0px',
      transform: `translate3d(${position.x}px, ${position.y}px, 0)`,
      zIndex: 1,
      willChange: 'auto' as const
    }
  }

  // Batch DOM updates
  function batchDOMUpdates(updates: (() => void)[]) {
    return new Promise<void>((resolve) => {
      requestAnimationFrame(() => {
        updates.forEach(update => update())
        nextTick(resolve)
      })
    })
  }

  // GPU acceleration helpers
  function enableGPUAcceleration(element: HTMLElement) {
    element.style.willChange = 'transform'
    element.style.transform = element.style.transform || 'translate3d(0,0,0)'
  }

  function disableGPUAcceleration(element: HTMLElement) {
    element.style.willChange = 'auto'
  }

  // Level of Detail (LOD) rendering
  const currentLOD = computed(() => {
    const scale = viewport.value.scale
    if (scale < 0.3) return 'low'
    if (scale < 0.7) return 'medium'
    return 'high'
  })

  function shouldRenderTaskDetails(task: Task): boolean {
    return currentLOD.value !== 'low'
  }

  function shouldRenderTaskConnections(): boolean {
    return currentLOD.value === 'high'
  }

  // Memory management
  function cleanupCache() {
    cachedVisibleTasks = []
    lastVisibleTasksUpdate = 0
    visibleBounds.value.lastUpdate = 0
  }

  // Performance analysis
  function getPerformanceReport() {
    const metrics = performanceMetrics.value
    const frameRate = metrics.frameCount > 0 ? 1000 / metrics.avgFrameTime : 0
    const droppedFrameRate = metrics.frameCount > 0 ? 
      (metrics.droppedFrames / metrics.frameCount) * 100 : 0

    return {
      ...metrics,
      frameRate: Math.round(frameRate),
      droppedFrameRate: Math.round(droppedFrameRate * 100) / 100,
      memoryUsage: (performance as any).memory ? {
        used: Math.round((performance as any).memory.usedJSHeapSize / 1024 / 1024),
        total: Math.round((performance as any).memory.totalJSHeapSize / 1024 / 1024)
      } : null
    }
  }

  return {
    // State
    performanceMetrics: readonly(performanceMetrics),
    visibleBounds: readonly(visibleBounds),
    currentLOD,
    isPanning,

    // Methods
    getVisibleTasks,
    isTaskVisible,
    getTaskPositionStyle,
    optimizedRender,
    measureRenderPerformance,
    throttledViewportUpdate,
    lightweightPanUpdate,
    batchDOMUpdates,
    enableGPUAcceleration,
    disableGPUAcceleration,
    shouldRenderTaskDetails,
    shouldRenderTaskConnections,
    cleanupCache,
    getPerformanceReport,
    calculateVisibleBounds
  }
} 