import { ref, Ref } from 'vue'
import { type TaskDependency } from '@/stores/tasks'

interface ConnectionState {
  isConnecting: boolean
  fromTaskId: number | null
  startX: number
  startY: number
}

interface ConnectionPreview {
  fromTaskId: number
  toX: number
  toY: number
}

interface ConnectionOptions {
  onConnectionCreate?: (fromTaskId: number, toTaskId: number) => Promise<void>
  onConnectionStart?: (fromTaskId: number) => void
  onConnectionEnd?: () => void
}

export function useConnections(
  canvasContainer: Ref<HTMLElement | undefined>,
  viewport: Ref<{ x: number; y: number; scale: number }>,
  options: ConnectionOptions = {}
) {
  // Connection state
  const connectionState = ref<ConnectionState>({
    isConnecting: false,
    fromTaskId: null,
    startX: 0,
    startY: 0
  })

  // Connection preview
  const connectionPreview = ref<ConnectionPreview | null>(null)

  // Start connection
  function startConnection(fromTaskId: number, event: MouseEvent) {
    console.log('useConnections: startConnection called with task:', fromTaskId)
    if (event.cancelable) {
      event.preventDefault()
      event.stopPropagation()
    }
    
    connectionState.value = {
      isConnecting: true,
      fromTaskId,
      startX: event.clientX,
      startY: event.clientY
    }
    
    // Start tracking mouse movement for preview
    document.addEventListener('mousemove', handleConnectionDrag)
    document.addEventListener('mouseup', handleConnectionEnd)
    
    // Show preview connection
    updateConnectionPreview(event.clientX, event.clientY)
    
    // Callback
    if (options.onConnectionStart) {
      options.onConnectionStart(fromTaskId)
    }
  }

  // Handle connection drag
  function handleConnectionDrag(event: MouseEvent) {
    if (!connectionState.value.isConnecting) return
    updateConnectionPreview(event.clientX, event.clientY)
  }

  // Update connection preview
  function updateConnectionPreview(clientX: number, clientY: number) {
    if (!connectionState.value.fromTaskId || !canvasContainer.value) return
    
    const canvasRect = canvasContainer.value.getBoundingClientRect()
    
    // 精确计算考虑视口变换的鼠标位置
    const canvasMouseX = clientX - canvasRect.left
    const canvasMouseY = clientY - canvasRect.top
    
    connectionPreview.value = {
      fromTaskId: connectionState.value.fromTaskId,
      toX: canvasMouseX,
      toY: canvasMouseY
    }
  }

  // Handle connection end
  async function handleConnectionEnd(event: MouseEvent) {
    if (!connectionState.value.isConnecting) return
    
    // Clean up event listeners
    document.removeEventListener('mousemove', handleConnectionDrag)
    document.removeEventListener('mouseup', handleConnectionEnd)
    
    // Find target task
    const targetElement = document.elementFromPoint(event.clientX, event.clientY)
    const taskElement = targetElement?.closest('[data-task-id]') as HTMLElement
    
    if (taskElement) {
      const toTaskId = parseInt(taskElement.dataset.taskId || '0')
      if (toTaskId && toTaskId !== connectionState.value.fromTaskId) {
        // Create dependency
        if (options.onConnectionCreate) {
          await options.onConnectionCreate(connectionState.value.fromTaskId!, toTaskId)
        }
      }
    }
    
    // Reset connection state
    connectionState.value = {
      isConnecting: false,
      fromTaskId: null,
      startX: 0,
      startY: 0
    }
    connectionPreview.value = null
    
    // Callback
    if (options.onConnectionEnd) {
      options.onConnectionEnd()
    }
  }

  // Enter connection mode
  function enterConnectionMode(fromTaskId: number) {
    connectionState.value = {
      isConnecting: true,
      fromTaskId,
      startX: 0,
      startY: 0
    }
    
    // Add visual feedback
    const fromElement = document.querySelector(`[data-task-id="${fromTaskId}"]`)
    if (fromElement) {
      fromElement.classList.add('connection-source')
    }
    
    // Add cursor style to canvas
    if (canvasContainer.value) {
      canvasContainer.value.style.cursor = 'crosshair'
    }
    
    // Add click listener to all task elements for connection target
    document.addEventListener('click', handleConnectionTargetClick)
    
    // Callback
    if (options.onConnectionStart) {
      options.onConnectionStart(fromTaskId)
    }
  }

  // Handle connection target click
  async function handleConnectionTargetClick(event: MouseEvent) {
    if (!connectionState.value.isConnecting) return
    
    const targetElement = event.target as HTMLElement
    const taskElement = targetElement.closest('[data-task-id]') as HTMLElement
    
    if (taskElement) {
      const toTaskId = parseInt(taskElement.dataset.taskId || '0')
      if (toTaskId && toTaskId !== connectionState.value.fromTaskId) {
        // Create dependency
        if (options.onConnectionCreate) {
          await options.onConnectionCreate(connectionState.value.fromTaskId!, toTaskId)
        }
        exitConnectionMode()
      }
    } else {
      // Clicked outside tasks, exit connection mode
      exitConnectionMode()
    }
  }

  // Exit connection mode
  function exitConnectionMode() {
    // Remove visual feedback
    const sourceElement = document.querySelector('.connection-source')
    if (sourceElement) {
      sourceElement.classList.remove('connection-source')
    }
    
    // Reset cursor
    if (canvasContainer.value) {
      canvasContainer.value.style.cursor = 'default'
    }
    
    // Reset connection state
    connectionState.value = {
      isConnecting: false,
      fromTaskId: null,
      startX: 0,
      startY: 0
    }
    connectionPreview.value = null
    
    // Remove event listeners
    document.removeEventListener('click', handleConnectionTargetClick)
    
    // Callback
    if (options.onConnectionEnd) {
      options.onConnectionEnd()
    }
  }

  // Cleanup
  function cleanup() {
    document.removeEventListener('mousemove', handleConnectionDrag)
    document.removeEventListener('mouseup', handleConnectionEnd)
    document.removeEventListener('click', handleConnectionTargetClick)
  }

  return {
    connectionState,
    connectionPreview,
    startConnection,
    enterConnectionMode,
    exitConnectionMode,
    cleanup
  }
} 