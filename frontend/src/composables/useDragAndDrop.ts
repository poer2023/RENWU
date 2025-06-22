import { ref, Ref } from 'vue'
import { type Task } from '@/stores/tasks'
import { debounce } from 'lodash'

interface DragState {
  isDragging: boolean
  task: Task | null
  startX: number
  startY: number
  offsetX: number
  offsetY: number
}

interface DragOptions {
  onDragStart?: (task: Task) => void
  onDragEnd?: (task: Task, position: { x: number; y: number }) => void
  onPositionUpdate?: (taskId: number, x: number, y: number) => void
}

export function useDragAndDrop(
  canvasContainer: Ref<HTMLElement | undefined>,
  taskPositions: Ref<{ [key: number]: { x: number; y: number } }>,
  viewport: Ref<{ x: number; y: number; scale: number }>,
  canvasSize: Ref<{ width: number; height: number }>,
  options: DragOptions = {}
) {
  // Drag state
  const dragState = ref<DragState>({
    isDragging: false,
    task: null,
    startX: 0,
    startY: 0,
    offsetX: 0,
    offsetY: 0
  })

  // 拖动RAF ID管理
  const dragRafId = ref<number | null>(null)

  // Cache for better performance
  let canvasRect: DOMRect | null = null
  let cardDimensions = { width: 240, height: 120 }

  // 防抖的位置保存函数
  const debouncedSavePosition = debounce(async (taskId: number, x: number, y: number) => {
    if (options.onPositionUpdate) {
      options.onPositionUpdate(taskId, x, y)
    }
  }, 500)

  function startDrag(task: Task, event: MouseEvent) {
    if (event.button !== 0) return // Only left mouse button
    
    event.preventDefault()
    event.stopPropagation()
    
    const rect = canvasContainer.value?.getBoundingClientRect()
    if (!rect) return
    
    // Cache canvas rect and card dimensions for performance
    canvasRect = rect
    const cardElement = document.querySelector(`[data-task-id="${task.id}"]`) as HTMLElement
    if (cardElement) {
      cardDimensions = {
        width: cardElement.offsetWidth || 240,
        height: cardElement.offsetHeight || 120
      }
    }
    
    const currentPos = taskPositions.value[task.id] || { x: 0, y: 0 }
    
    // 计算鼠标相对于卡片的精确偏移量（考虑缩放和视口变换）
    const canvasMouseX = (event.clientX - rect.left - viewport.value.x) / viewport.value.scale
    const canvasMouseY = (event.clientY - rect.top - viewport.value.y) / viewport.value.scale
    
    const offsetX = canvasMouseX - currentPos.x
    const offsetY = canvasMouseY - currentPos.y
    
    dragState.value = {
      isDragging: true,
      task,
      startX: event.clientX,
      startY: event.clientY,
      offsetX,
      offsetY
    }
    
    // Add global mouse event listeners
    document.addEventListener('mousemove', handleDrag, { passive: false, capture: true })
    document.addEventListener('mouseup', stopDrag, { passive: false, capture: true })
    
    // Add styles for better dragging experience
    document.body.style.userSelect = 'none'
    document.body.style.cursor = 'grabbing'
    
    // Enable GPU acceleration for the dragging task
    if (cardElement) {
      cardElement.style.willChange = 'transform'
      cardElement.style.transition = 'none'
    }
    
    // Callback
    if (options.onDragStart) {
      options.onDragStart(task)
    }
  }

  function handleDrag(event: MouseEvent) {
    if (!dragState.value.isDragging || !dragState.value.task || !canvasRect) return
    
    event.preventDefault()
    
    // 使用 requestAnimationFrame 来优化拖动
    if (dragRafId.value) {
      cancelAnimationFrame(dragRafId.value)
    }
    
    dragRafId.value = requestAnimationFrame(() => {
      if (!dragState.value.isDragging || !dragState.value.task || !canvasRect) return
      
      // 重新获取最新的rect
      const rect = canvasContainer.value?.getBoundingClientRect()
      if (!rect) return
      
      // 计算新位置（考虑缩放和视口变换）
      const canvasMouseX = (event.clientX - rect.left - viewport.value.x) / viewport.value.scale
      const canvasMouseY = (event.clientY - rect.top - viewport.value.y) / viewport.value.scale
      
      const newX = canvasMouseX - dragState.value.offsetX
      const newY = canvasMouseY - dragState.value.offsetY
      
      // 限制在画布边界内
      const boundedX = Math.max(0, Math.min(canvasSize.value.width - cardDimensions.width, newX))
      const boundedY = Math.max(0, Math.min(canvasSize.value.height - cardDimensions.height, newY))
      
      // 更新任务位置
      taskPositions.value[dragState.value.task.id] = {
        x: boundedX,
        y: boundedY
      }
    })
  }

  function stopDrag(event: MouseEvent) {
    if (!dragState.value.isDragging || !dragState.value.task) return
    
    event.preventDefault()
    
    // 取消任何挂起的动画帧
    if (dragRafId.value) {
      cancelAnimationFrame(dragRafId.value)
      dragRafId.value = null
    }
    
    const task = dragState.value.task
    const finalPosition = taskPositions.value[task.id]
    
    if (finalPosition) {
      // 使用防抖保存位置
      debouncedSavePosition(task.id, finalPosition.x, finalPosition.y)
      
      // Callback
      if (options.onDragEnd) {
        options.onDragEnd(task, finalPosition)
      }
    }
    
    // 恢复正常的鼠标样式
    document.body.style.userSelect = 'auto'
    document.body.style.cursor = 'default'
    
    // 移除全局事件监听
    document.removeEventListener('mousemove', handleDrag, { capture: true } as any)
    document.removeEventListener('mouseup', stopDrag, { capture: true } as any)
    
    // 清理拖动状态
    dragState.value = {
      isDragging: false,
      task: null,
      startX: 0,
      startY: 0,
      offsetX: 0,
      offsetY: 0
    }
  }

  // Cleanup function
  function cleanup() {
    if (dragRafId.value) {
      cancelAnimationFrame(dragRafId.value)
      dragRafId.value = null
    }
    document.removeEventListener('mousemove', handleDrag, { capture: true } as any)
    document.removeEventListener('mouseup', stopDrag, { capture: true } as any)
  }

  return {
    dragState,
    startDrag,
    cleanup
  }
} 