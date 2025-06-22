import { ref, Ref, nextTick, watch } from 'vue'
import { type Task } from '@/stores/tasks'
import { debounce } from 'lodash'

interface TaskPositionsOptions {
  onPositionChange?: (taskId: number, x: number, y: number) => void
  onBoundsUpdate?: (bounds: { width: number; height: number }) => void
}

export function useTaskPositions(
  tasks: Ref<Task[]>,
  options: TaskPositionsOptions = {}
) {
  // Task positions (task_id -> {x, y})
  const taskPositions = ref<{ [key: number]: { x: number; y: number } }>({})
  
  // Task dimensions cache
  const taskDimensions = ref<{ [key: number]: { width: number; height: number } }>({})
  
  // 性能优化标志
  const isInitializing = ref(false)
  const initializationPromise = ref<Promise<void> | null>(null)
  
  // 防抖处理
  let initializationTimeout: NodeJS.Timeout | null = null
  
  // 默认任务尺寸
  const DEFAULT_TASK_WIDTH = 240
  const DEFAULT_TASK_HEIGHT = 120

  // 获取任务的默认位置
  function getDefaultPosition(task: any) {
    // 如果任务已经有位置，使用它
    if (task.position_x !== undefined && task.position_y !== undefined) {
      return { 
        x: Math.max(0, task.position_x), 
        y: Math.max(0, task.position_y) 
      }
    }
    
    // 否则计算一个合理的默认位置
    const index = tasks.value.findIndex(t => t.id === task.id)
    const row = Math.floor(index / 4)
    const col = index % 4
    
    // 确保位置在视口内，使用更小的间距
    return {
      x: Math.max(50, 100 + col * 350), // 从左边留出50px，卡片间距350px
      y: Math.max(50, 100 + row * 250)  // 从上边留出50px，卡片间距250px
    }
  }

  // 初始化任务位置
  async function initializeTaskPositions() {
    // 防抖处理
    if (initializationTimeout) {
      clearTimeout(initializationTimeout)
    }
    
    return new Promise<void>((resolve) => {
      initializationTimeout = setTimeout(async () => {
        // 防止重复初始化
        if (isInitializing.value) {
          if (initializationPromise.value) {
            await initializationPromise.value
          }
          resolve()
          return
        }
        
        isInitializing.value = true
        
        initializationPromise.value = new Promise<void>((innerResolve) => {
          // 批量初始化位置
          const newPositions: { [key: number]: { x: number; y: number } } = {}
          let hasNewPositions = false
          
          tasks.value.forEach(task => {
            if (!taskPositions.value[task.id]) {
              // 如果任务有保存的位置，使用保存的位置（但需要验证边界）
              if (task.position_x !== undefined && task.position_y !== undefined) {
                const CANVAS_WIDTH = 6000
                const CANVAS_HEIGHT = 6000
                const taskWidth = DEFAULT_TASK_WIDTH
                const taskHeight = DEFAULT_TASK_HEIGHT
                
                // 约束保存的位置到画布边界内
                const constrainedX = Math.max(0, Math.min(task.position_x, CANVAS_WIDTH - taskWidth))
                const constrainedY = Math.max(0, Math.min(task.position_y, CANVAS_HEIGHT - taskHeight))
                
                newPositions[task.id] = {
                  x: constrainedX,
                  y: constrainedY
                }
              } else {
                // 否则生成默认位置
                newPositions[task.id] = getDefaultPosition(task)
              }
              hasNewPositions = true
            }
          })
          
          // 批量更新位置
          if (hasNewPositions) {
            Object.assign(taskPositions.value, newPositions)
          }
          
          // 更新画布边界
          requestAnimationFrame(() => {
            nextTick(() => {
              updateCanvasBounds()
              updateTaskDimensions()
              isInitializing.value = false
              innerResolve()
              resolve()
            })
          })
        })
        
        await initializationPromise.value
      }, 50) // 50ms防抖延迟
    })
  }

  // 更新任务尺寸缓存
  function updateTaskDimensions() {
    tasks.value.forEach(task => {
      const element = document.querySelector(`[data-task-id="${task.id}"]`) as HTMLElement
      if (element) {
        const rect = element.getBoundingClientRect()
        taskDimensions.value[task.id] = {
          width: element.offsetWidth || rect.width || DEFAULT_TASK_WIDTH,
          height: element.offsetHeight || rect.height || DEFAULT_TASK_HEIGHT
        }
      } else {
        // 使用默认尺寸
        taskDimensions.value[task.id] = { 
          width: DEFAULT_TASK_WIDTH, 
          height: DEFAULT_TASK_HEIGHT 
        }
      }
    })
  }

  // 优化的画布边界更新函数
  function updateCanvasBounds() {
    if (tasks.value.length === 0) return
    
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
    
    for (const task of tasks.value) {
      const pos = taskPositions.value[task.id]
      if (pos) {
        const taskWidth = taskDimensions.value[task.id]?.width || DEFAULT_TASK_WIDTH
        const taskHeight = taskDimensions.value[task.id]?.height || DEFAULT_TASK_HEIGHT
        
        minX = Math.min(minX, pos.x)
        minY = Math.min(minY, pos.y)
        maxX = Math.max(maxX, pos.x + taskWidth)
        maxY = Math.max(maxY, pos.y + taskHeight)
      }
    }
    
    if (minX !== Infinity) {
      const padding = 200
      const bounds = {
        width: Math.max(6000, maxX + padding),
        height: Math.max(6000, maxY + padding)
      }
      
      if (options.onBoundsUpdate) {
        options.onBoundsUpdate(bounds)
      }
    }
  }

  // 设置任务位置（带边界约束）
  function setTaskPosition(taskId: number, x: number, y: number, enforceCanvasBounds: boolean = true) {
    let constrainedX = x
    let constrainedY = y
    
    if (enforceCanvasBounds) {
      // 画布边界约束（基于当前网格系统的6000x6000画布）
      const CANVAS_WIDTH = 6000
      const CANVAS_HEIGHT = 6000
      const taskWidth = taskDimensions.value[taskId]?.width || DEFAULT_TASK_WIDTH
      const taskHeight = taskDimensions.value[taskId]?.height || DEFAULT_TASK_HEIGHT
      
      // 约束到画布边界内，确保任务卡片完全在画布内
      constrainedX = Math.max(0, Math.min(x, CANVAS_WIDTH - taskWidth))
      constrainedY = Math.max(0, Math.min(y, CANVAS_HEIGHT - taskHeight))
      
      console.log(`[Canvas Bounds] Task ${taskId}: (${x}, ${y}) -> (${constrainedX}, ${constrainedY})`)
    }
    
    taskPositions.value[taskId] = { x: constrainedX, y: constrainedY }
    
    if (options.onPositionChange) {
      options.onPositionChange(taskId, constrainedX, constrainedY)
    }
    
    // 更新画布边界
    debouncedUpdateBounds()
  }

  // 获取任务位置
  function getTaskPosition(taskId: number) {
    return taskPositions.value[taskId] || null
  }

  // 批量设置任务位置（带边界约束）
  function setTaskPositions(positions: { [key: number]: { x: number; y: number } }, enforceCanvasBounds: boolean = true) {
    const CANVAS_WIDTH = 6000
    const CANVAS_HEIGHT = 6000
    
    const constrainedPositions: { [key: number]: { x: number; y: number } } = {}
    
    Object.entries(positions).forEach(([taskIdStr, pos]) => {
      const taskId = parseInt(taskIdStr)
      let { x, y } = pos
      
      if (enforceCanvasBounds) {
        const taskWidth = taskDimensions.value[taskId]?.width || DEFAULT_TASK_WIDTH
        const taskHeight = taskDimensions.value[taskId]?.height || DEFAULT_TASK_HEIGHT
        
        // 约束到画布边界内
        x = Math.max(0, Math.min(x, CANVAS_WIDTH - taskWidth))
        y = Math.max(0, Math.min(y, CANVAS_HEIGHT - taskHeight))
      }
      
      constrainedPositions[taskId] = { x, y }
    })
    
    Object.assign(taskPositions.value, constrainedPositions)
    updateCanvasBounds()
  }

  // 防抖的边界更新
  const debouncedUpdateBounds = debounce(updateCanvasBounds, 300)

  // 设置ResizeObserver来监听尺寸变化
  function setupDimensionObserver() {
    if (!window.ResizeObserver) return null
    
    const resizeObserver = new ResizeObserver((entries) => {
      entries.forEach(entry => {
        const element = entry.target as HTMLElement
        const taskId = parseInt(element.dataset.taskId || '0')
        if (taskId) {
          taskDimensions.value[taskId] = {
            width: entry.contentRect.width,
            height: entry.contentRect.height
          }
        }
      })
    })
    
    // 监听所有任务元素
    nextTick(() => {
      tasks.value.forEach(task => {
        const element = document.querySelector(`[data-task-id="${task.id}"]`) as HTMLElement
        if (element) {
          resizeObserver.observe(element)
        }
      })
    })
    
    return resizeObserver
  }

  // 监听任务变化
  watch(tasks, async (newTasks) => {
    if (newTasks && newTasks.length > 0) {
      await nextTick()
      if (!isInitializing.value) {
        await initializeTaskPositions()
      }
    }
  }, { immediate: true })

  return {
    taskPositions,
    taskDimensions,
    initializeTaskPositions,
    updateTaskDimensions,
    updateCanvasBounds,
    setTaskPosition,
    getTaskPosition,
    setTaskPositions,
    setupDimensionObserver,
    getDefaultPosition
  }
} 