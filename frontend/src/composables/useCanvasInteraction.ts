import { ref, readonly, type Ref } from 'vue'
import type { Task } from '@/stores/tasks'

interface InteractionState {
  isMouseDown: boolean
  isDragging: boolean
  isPanning: boolean
  isConnecting: boolean
  lastMousePosition: { x: number; y: number }
  interactionStartTime: number
  dragThreshold: number
}

interface InteractionOptions {
  dragThreshold?: number
  longPressDelay?: number
  doubleClickDelay?: number
  enableTouch?: boolean
  enableKeyboard?: boolean
}

interface MouseEventData {
  clientX: number
  clientY: number
  button: number
  shiftKey: boolean
  ctrlKey: boolean
  altKey: boolean
  metaKey: boolean
}

interface TouchEventData {
  touches: Array<{ clientX: number; clientY: number }>
  targetTouches: Array<{ clientX: number; clientY: number }>
  changedTouches: Array<{ clientX: number; clientY: number }>
}

export function useCanvasInteraction(
  canvasContainer: Ref<HTMLElement | undefined>,
  viewport: Ref<{ x: number; y: number; scale: number }>,
  options: InteractionOptions = {}
) {
  const {
    dragThreshold = 5,
    longPressDelay = 500,
    doubleClickDelay = 300,
    enableTouch = true,
    enableKeyboard = true
  } = options

  // Interaction state
  const interactionState = ref<InteractionState>({
    isMouseDown: false,
    isDragging: false,
    isPanning: false,
    isConnecting: false,
    lastMousePosition: { x: 0, y: 0 },
    interactionStartTime: 0,
    dragThreshold
  })

  // Event handlers registry
  const eventHandlers = ref<{
    onTaskDragStart?: (task: Task, event: MouseEventData) => void
    onTaskDrag?: (task: Task, event: MouseEventData) => void
    onTaskDragEnd?: (task: Task, event: MouseEventData) => void
    onCanvasPanStart?: (event: MouseEventData) => void
    onCanvasPan?: (event: MouseEventData) => void
    onCanvasPanEnd?: (event: MouseEventData) => void
    onTaskClick?: (task: Task, event: MouseEventData) => void
    onTaskDoubleClick?: (task: Task, event: MouseEventData) => void
    onTaskRightClick?: (task: Task, event: MouseEventData) => void
    onCanvasClick?: (event: MouseEventData) => void
    onConnectionStart?: (task: Task, event: MouseEventData) => void
    onConnectionDrag?: (event: MouseEventData) => void
    onConnectionEnd?: (targetTask: Task | null, event: MouseEventData) => void
  }>({})

  // Touch state for mobile
  const touchState = ref<{
    lastTouchTime: number
    touchCount: number
    initialDistance: number
    initialScale: number
    isPinching: boolean
  }>({
    lastTouchTime: 0,
    touchCount: 0,
    initialDistance: 0,
    initialScale: 1,
    isPinching: false
  })

  // Convert screen coordinates to canvas coordinates
  function screenToCanvas(screenX: number, screenY: number) {
    if (!canvasContainer.value) return { x: screenX, y: screenY }
    
    const rect = canvasContainer.value.getBoundingClientRect()
    const canvasX = (screenX - rect.left - viewport.value.x) / viewport.value.scale
    const canvasY = (screenY - rect.top - viewport.value.y) / viewport.value.scale
    
    return { x: canvasX, y: canvasY }
  }

  // Convert canvas coordinates to screen coordinates
  function canvasToScreen(canvasX: number, canvasY: number) {
    if (!canvasContainer.value) return { x: canvasX, y: canvasY }
    
    const rect = canvasContainer.value.getBoundingClientRect()
    const screenX = canvasX * viewport.value.scale + viewport.value.x + rect.left
    const screenY = canvasY * viewport.value.scale + viewport.value.y + rect.top
    
    return { x: screenX, y: screenY }
  }

  // Check if movement exceeds drag threshold
  function exceedsDragThreshold(startX: number, startY: number, currentX: number, currentY: number): boolean {
    const deltaX = Math.abs(currentX - startX)
    const deltaY = Math.abs(currentY - startY)
    return Math.sqrt(deltaX * deltaX + deltaY * deltaY) > dragThreshold
  }

  // Get task element at position
  function getTaskAtPosition(x: number, y: number): { task: Task; element: HTMLElement } | null {
    const elements = document.elementsFromPoint(x, y)
    
    for (const element of elements) {
      const taskElement = element.closest('[data-task-id]') as HTMLElement
      if (taskElement) {
        const taskId = parseInt(taskElement.dataset.taskId || '0')
        const task = getTaskById(taskId)
        if (task) {
          return { task, element: taskElement }
        }
      }
    }
    
    return null
  }

  // Get task by ID (this should be provided by the parent component)
  let getTaskById: (id: number) => Task | null = () => null

  // Mouse event handlers
  function handleMouseDown(event: MouseEvent) {
    if (!canvasContainer.value) return

    const eventData: MouseEventData = {
      clientX: event.clientX,
      clientY: event.clientY,
      button: event.button,
      shiftKey: event.shiftKey,
      ctrlKey: event.ctrlKey,
      altKey: event.altKey,
      metaKey: event.metaKey
    }

    interactionState.value.isMouseDown = true
    interactionState.value.lastMousePosition = { x: event.clientX, y: event.clientY }
    interactionState.value.interactionStartTime = Date.now()

    // Check if clicking on a task
    const taskAtPosition = getTaskAtPosition(event.clientX, event.clientY)
    
    if (taskAtPosition) {
      // Handle task interaction
      if (event.shiftKey) {
        // Start connection mode
        interactionState.value.isConnecting = true
        eventHandlers.value.onConnectionStart?.(taskAtPosition.task, eventData)
      } else {
        // Start potential drag
        eventHandlers.value.onTaskDragStart?.(taskAtPosition.task, eventData)
      }
    } else {
      // Start canvas panning
      interactionState.value.isPanning = true
      eventHandlers.value.onCanvasPanStart?.(eventData)
    }

    // Add global event listeners
    document.addEventListener('mousemove', handleMouseMove, { passive: false })
    document.addEventListener('mouseup', handleMouseUp, { passive: false })
  }

  function handleMouseMove(event: MouseEvent) {
    if (!interactionState.value.isMouseDown) return

    const eventData: MouseEventData = {
      clientX: event.clientX,
      clientY: event.clientY,
      button: event.button,
      shiftKey: event.shiftKey,
      ctrlKey: event.ctrlKey,
      altKey: event.altKey,
      metaKey: event.metaKey
    }

    const { x: startX, y: startY } = interactionState.value.lastMousePosition
    
    // Check if drag threshold is exceeded
    if (!interactionState.value.isDragging && 
        exceedsDragThreshold(startX, startY, event.clientX, event.clientY)) {
      interactionState.value.isDragging = true
    }

    if (interactionState.value.isConnecting) {
      eventHandlers.value.onConnectionDrag?.(eventData)
    } else if (interactionState.value.isPanning) {
      eventHandlers.value.onCanvasPan?.(eventData)
    } else if (interactionState.value.isDragging) {
      // Find the task being dragged
      const taskAtPosition = getTaskAtPosition(startX, startY)
      if (taskAtPosition) {
        eventHandlers.value.onTaskDrag?.(taskAtPosition.task, eventData)
      }
    }
  }

  function handleMouseUp(event: MouseEvent) {
    const eventData: MouseEventData = {
      clientX: event.clientX,
      clientY: event.clientY,
      button: event.button,
      shiftKey: event.shiftKey,
      ctrlKey: event.ctrlKey,
      altKey: event.altKey,
      metaKey: event.metaKey
    }

    const { x: startX, y: startY } = interactionState.value.lastMousePosition
    const isClick = !exceedsDragThreshold(startX, startY, event.clientX, event.clientY)
    
    if (interactionState.value.isConnecting) {
      const targetTask = getTaskAtPosition(event.clientX, event.clientY)
      eventHandlers.value.onConnectionEnd?.(targetTask?.task || null, eventData)
    } else if (interactionState.value.isPanning) {
      eventHandlers.value.onCanvasPanEnd?.(eventData)
    } else if (interactionState.value.isDragging) {
      const taskAtPosition = getTaskAtPosition(startX, startY)
      if (taskAtPosition) {
        eventHandlers.value.onTaskDragEnd?.(taskAtPosition.task, eventData)
      }
    } else if (isClick) {
      // Handle click events
      const taskAtPosition = getTaskAtPosition(event.clientX, event.clientY)
      if (taskAtPosition) {
        if (event.button === 2) {
          eventHandlers.value.onTaskRightClick?.(taskAtPosition.task, eventData)
        } else {
          eventHandlers.value.onTaskClick?.(taskAtPosition.task, eventData)
        }
      } else {
        eventHandlers.value.onCanvasClick?.(eventData)
      }
    }

    // Reset state
    interactionState.value.isMouseDown = false
    interactionState.value.isDragging = false
    interactionState.value.isPanning = false
    interactionState.value.isConnecting = false

    // Remove global event listeners
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }

  // Touch event handlers for mobile support
  function handleTouchStart(event: TouchEvent) {
    if (!enableTouch) return

    touchState.value.touchCount = event.touches.length
    touchState.value.lastTouchTime = Date.now()

    if (event.touches.length === 1) {
      // Single touch - treat as mouse down
      const touch = event.touches[0]
      handleMouseDown({
        clientX: touch.clientX,
        clientY: touch.clientY,
        button: 0,
        shiftKey: false,
        ctrlKey: false,
        altKey: false,
        metaKey: false,
        preventDefault: () => event.preventDefault(),
        stopPropagation: () => event.stopPropagation()
      } as MouseEvent)
    } else if (event.touches.length === 2) {
      // Two touches - start pinch zoom
      const touch1 = event.touches[0]
      const touch2 = event.touches[1]
      const distance = Math.sqrt(
        Math.pow(touch2.clientX - touch1.clientX, 2) + 
        Math.pow(touch2.clientY - touch1.clientY, 2)
      )
      
      touchState.value.initialDistance = distance
      touchState.value.initialScale = viewport.value.scale
      touchState.value.isPinching = true
    }
  }

  function handleTouchMove(event: TouchEvent) {
    if (!enableTouch) return

    if (touchState.value.isPinching && event.touches.length === 2) {
      // Handle pinch zoom
      const touch1 = event.touches[0]
      const touch2 = event.touches[1]
      const distance = Math.sqrt(
        Math.pow(touch2.clientX - touch1.clientX, 2) + 
        Math.pow(touch2.clientY - touch1.clientY, 2)
      )
      
      const scale = (distance / touchState.value.initialDistance) * touchState.value.initialScale
      // Apply scale change through viewport
      viewport.value.scale = Math.max(0.1, Math.min(3, scale))
    } else if (event.touches.length === 1) {
      // Single touch - treat as mouse move
      const touch = event.touches[0]
      handleMouseMove({
        clientX: touch.clientX,
        clientY: touch.clientY,
        button: 0,
        shiftKey: false,
        ctrlKey: false,
        altKey: false,
        metaKey: false,
        preventDefault: () => event.preventDefault(),
        stopPropagation: () => event.stopPropagation()
      } as MouseEvent)
    }
  }

  function handleTouchEnd(event: TouchEvent) {
    if (!enableTouch) return

    if (touchState.value.isPinching) {
      touchState.value.isPinching = false
    }

    if (event.touches.length === 0) {
      // All touches ended - treat as mouse up
      const touch = event.changedTouches[0]
      handleMouseUp({
        clientX: touch.clientX,
        clientY: touch.clientY,
        button: 0,
        shiftKey: false,
        ctrlKey: false,
        altKey: false,
        metaKey: false,
        preventDefault: () => event.preventDefault(),
        stopPropagation: () => event.stopPropagation()
      } as MouseEvent)
    }

    touchState.value.touchCount = event.touches.length
  }

  // Keyboard event handlers
  function handleKeyDown(event: KeyboardEvent) {
    if (!enableKeyboard) return

    // Handle keyboard shortcuts
    switch (event.key) {
      case 'Escape':
        if (interactionState.value.isConnecting) {
          interactionState.value.isConnecting = false
          eventHandlers.value.onConnectionEnd?.(null, {
            clientX: 0,
            clientY: 0,
            button: 0,
            shiftKey: false,
            ctrlKey: false,
            altKey: false,
            metaKey: false
          })
        }
        break
    }
  }

  // Setup event listeners
  function setupEventListeners() {
    if (!canvasContainer.value) return

    const container = canvasContainer.value

    // Mouse events
    container.addEventListener('mousedown', handleMouseDown)
    container.addEventListener('contextmenu', (e) => e.preventDefault())

    // Touch events
    if (enableTouch) {
      container.addEventListener('touchstart', handleTouchStart, { passive: false })
      container.addEventListener('touchmove', handleTouchMove, { passive: false })
      container.addEventListener('touchend', handleTouchEnd, { passive: false })
    }

    // Keyboard events
    if (enableKeyboard) {
      document.addEventListener('keydown', handleKeyDown)
    }
  }

  // Cleanup event listeners
  function cleanupEventListeners() {
    if (!canvasContainer.value) return

    const container = canvasContainer.value

    container.removeEventListener('mousedown', handleMouseDown)
    container.removeEventListener('touchstart', handleTouchStart)
    container.removeEventListener('touchmove', handleTouchMove)
    container.removeEventListener('touchend', handleTouchEnd)
    document.removeEventListener('keydown', handleKeyDown)
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }

  // Register event handlers
  function registerEventHandlers(handlers: typeof eventHandlers.value) {
    eventHandlers.value = { ...eventHandlers.value, ...handlers }
  }

  // Set task getter function
  function setTaskGetter(taskGetter: (id: number) => Task | null) {
    getTaskById = taskGetter
  }

  return {
    // State
    interactionState: readonly(interactionState),
    touchState: readonly(touchState),

    // Methods
    screenToCanvas,
    canvasToScreen,
    getTaskAtPosition,
    setupEventListeners,
    cleanupEventListeners,
    registerEventHandlers,
    setTaskGetter,
    
    // Event handlers
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    handleKeyDown
  }
} 