<template>
  <div ref="canvasContainer" class="sticky-canvas">
    
    <!-- Task wrappers with drag and connection functionality -->
    <div
      v-for="task in tasks"
      :key="task.id"
      ref="taskElements"
      :class="['task-wrapper', { 'dragging': dragState.task?.id === task.id }]"
      :style="getTaskPosition(task)"
      :data-task-id="task.id"
      @mousedown="startDrag(task, $event)"
    >
      <TaskCard
        :task="task"
        :is-selected="selectedTask?.id === task.id"
        @select="selectTask"
        @openDetails="handleOpenDetails"
        @startConnection="handleStartConnection"
      />
    </div>

    <!-- Task connections -->
    <TaskConnections
      :connections="dependencies"
      :task-positions="taskPositions"
      :canvas-width="canvasSize.width"
      :canvas-height="canvasSize.height"
      :preview-connection="connectionPreview"
    />

    <!-- Canvas background grid -->
    <div class="canvas-grid"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import TaskCard from './TaskCard.vue'
import TaskConnections from './TaskConnections.vue'
import { type Task, type TaskDependency, useTaskStore } from '@/stores/tasks'
import { useSettingsStore } from '@/stores/settings'
import { autoArrange } from '@/utils/autoArrange'

interface Props {
  tasks: Task[]
  selectedTask?: Task | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  selectTask: [task: Task | null]
  openTaskDetails: [task: Task, position: { x: number, y: number }]
  autoArrangeComplete: []
}>()

// Add debug watching for tasks prop
watch(() => props.tasks, (newTasks, oldTasks) => {
  console.log('StickyCanvas: tasks prop changed:', newTasks)
  console.log('StickyCanvas: tasks length:', newTasks?.length || 0)
  console.log('StickyCanvas: old tasks length:', oldTasks?.length || 0)
  if (newTasks && newTasks.length > 0) {
    console.log('StickyCanvas: first task:', newTasks[0])
    console.log('StickyCanvas: task positions before init:', Object.keys(taskPositions.value).length)
    
    // Initialize positions for new tasks immediately
    nextTick(() => {
      initializeTaskPositions()
      console.log('StickyCanvas: task positions after init:', Object.keys(taskPositions.value).length)
    })
  }
}, { immediate: true })

const settingsStore = useSettingsStore()
const taskStore = useTaskStore()

const canvasContainer = ref<HTMLElement>()
const taskElements = ref<HTMLElement[]>([])

// Task positions (task_id -> {x, y}) - Fix Record type issue
const taskPositions = ref<{ [key: number]: { x: number; y: number } }>({})

// Connection state
const connectionPreview = ref<{
  fromTaskId: number
  toX: number
  toY: number
} | null>(null)

// Canvas size
const canvasSize = ref({ width: 1200, height: 800 })

// Dependencies from store
const dependencies = computed(() => taskStore.dependencies)

// Drag state
const dragState = ref<{
  isDragging: boolean
  task: Task | null
  startX: number
  startY: number
  offsetX: number
  offsetY: number
}>({
  isDragging: false,
  task: null,
  startX: 0,
  startY: 0,
  offsetX: 0,
  offsetY: 0
})

// Methods
function getTaskPosition(task: Task) {
  const position = taskPositions.value[task.id] || getDefaultPosition(task)
  const isDragging = dragState.value.task?.id === task.id
  
  return {
    position: 'absolute',
    left: `${position.x}px`,
    top: `${position.y}px`,
    zIndex: isDragging ? 1000 : 1,
    transform: isDragging ? 'translate3d(0, 0, 0) scale(1.02)' : 'translate3d(0, 0, 0)',
    willChange: isDragging ? 'transform' : 'auto'
  }
}

function getDefaultPosition(task: Task) {
  // Generate default positions based on module and urgency
  const moduleOffset = (task.module_id || 0) * 250
  const urgencyOffset = task.urgency * 60
  const randomOffset = Math.random() * 100
  
  const position = {
    x: 50 + moduleOffset + randomOffset,
    y: 50 + urgencyOffset + randomOffset
  }
  
  taskPositions.value[task.id] = position
  return position
}

function selectTask(task: Task) {
  emit('selectTask', task)
}

function handleOpenDetails(task: Task, position: { x: number, y: number }) {
  emit('openTaskDetails', task, position)
}

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
      width: cardElement.offsetWidth,
      height: cardElement.offsetHeight
    }
  }
  
  const currentPos = taskPositions.value[task.id] || getDefaultPosition(task)
  
  dragState.value = {
    isDragging: true,
    task,
    startX: event.clientX,
    startY: event.clientY,
    offsetX: event.clientX - rect.left - currentPos.x,
    offsetY: event.clientY - rect.top - currentPos.y
  }
  
  // Add global mouse event listeners with passive: false for better performance
  document.addEventListener('mousemove', handleDrag, { passive: false })
  document.addEventListener('mouseup', stopDrag, { passive: false })
  
  // Add styles for better dragging experience
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'grabbing'
  
  // Select the task being dragged
  selectTask(task)
}

// Cache for better performance
let canvasRect: DOMRect | null = null
let cardDimensions = { width: 200, height: 120 }

function handleDrag(event: MouseEvent) {
  if (!dragState.value.isDragging || !dragState.value.task) return
  
  event.preventDefault()
  
  // Calculate position immediately without RAF for better responsiveness
  if (!canvasRect) {
    canvasRect = canvasContainer.value?.getBoundingClientRect() || null
  }
  
  if (!canvasRect) return
  
  const newX = event.clientX - canvasRect.left - dragState.value.offsetX
  const newY = event.clientY - canvasRect.top - dragState.value.offsetY
  
  // Constrain to canvas bounds with some padding
  const padding = 10
  const constrainedX = Math.max(padding, Math.min(newX, canvasRect.width - cardDimensions.width - padding))
  const constrainedY = Math.max(padding, Math.min(newY, canvasRect.height - cardDimensions.height - padding))
  
  // Update position immediately
  taskPositions.value[dragState.value.task!.id] = {
    x: constrainedX,
    y: constrainedY
  }
}

function stopDrag() {
  if (!dragState.value.isDragging) return
  
  // Clear cached values
  canvasRect = null
  
  // Remove global mouse event listeners
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', stopDrag)
  
  // Restore default styles
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
  
  dragState.value = {
    isDragging: false,
    task: null,
    startX: 0,
    startY: 0,
    offsetX: 0,
    offsetY: 0
  }
}

// Connection handling
const connectionState = ref<{
  isConnecting: boolean
  fromTaskId: number | null
  startX: number
  startY: number
}>({
  isConnecting: false,
  fromTaskId: null,
  startX: 0,
  startY: 0
})

function handleStartConnection(fromTaskId: number, event: MouseEvent) {
  event.preventDefault()
  event.stopPropagation()
  
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
}

function handleConnectionDrag(event: MouseEvent) {
  if (!connectionState.value.isConnecting) return
  updateConnectionPreview(event.clientX, event.clientY)
}

function updateConnectionPreview(clientX: number, clientY: number) {
  if (!connectionState.value.fromTaskId || !canvasContainer.value) return
  
  const canvasRect = canvasContainer.value.getBoundingClientRect()
  connectionPreview.value = {
    fromTaskId: connectionState.value.fromTaskId,
    toX: clientX - canvasRect.left,
    toY: clientY - canvasRect.top
  }
}

function handleConnectionEnd(event: MouseEvent) {
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
      createTaskDependency(connectionState.value.fromTaskId!, toTaskId)
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
}

async function createTaskDependency(fromTaskId: number, toTaskId: number) {
  try {
    await taskStore.createDependency(fromTaskId, toTaskId)
  } catch (error) {
    console.error('Failed to create dependency:', error)
  }
}

// Initialize positions for new tasks
function initializeTaskPositions() {
  props.tasks.forEach(task => {
    if (!taskPositions.value[task.id]) {
      getDefaultPosition(task)
    }
  })
}

// Canvas click handler (deselect task)
function handleCanvasClick(event: MouseEvent) {
  // Only deselect if clicking on the canvas itself, not on a task
  if (event.target === canvasContainer.value) {
    emit('selectTask', null)
  }
}

onMounted(() => {
  if (canvasContainer.value) {
    canvasContainer.value.addEventListener('click', handleCanvasClick)
    updateCanvasSize()
  }
  
  // Initialize positions for any existing tasks
  nextTick(() => {
    initializeTaskPositions()
  })
})

// Update canvas size based on container
function updateCanvasSize() {
  if (canvasContainer.value) {
    const rect = canvasContainer.value.getBoundingClientRect()
    canvasSize.value = {
      width: Math.max(1200, rect.width),
      height: Math.max(800, rect.height)
    }
  }
}

// Re-initialize positions when tasks change
function updateTaskPositions() {
  nextTick(() => {
    initializeTaskPositions()
  })
}

// Auto arrange functionality
function getTaskSizes(): Map<number, { width: number; height: number }> {
  const sizes = new Map()
  
  props.tasks.forEach(task => {
    const element = document.querySelector(`[data-task-id="${task.id}"]`) as HTMLElement
    if (element) {
      sizes.set(task.id, {
        width: element.offsetWidth || 200,
        height: element.offsetHeight || 120
      })
    } else {
      sizes.set(task.id, { width: 200, height: 120 })
    }
  })
  
  return sizes
}

function triggerAutoArrange() {
  if (!canvasContainer.value || props.tasks.length === 0) return
  
  const containerRect = canvasContainer.value.getBoundingClientRect()
  const taskSizes = getTaskSizes()
  
  const newPositions = autoArrange(
    props.tasks,
    containerRect.width,
    containerRect.height,
    settingsStore.autoArrangeOptions,
    taskSizes
  )
  
  if (settingsStore.autoArrangeOptions.animated) {
    // 动画过渡到新位置
    animateToPositions(newPositions)
  } else {
    // 直接设置新位置
    taskPositions.value = newPositions
  }
  
  emit('autoArrangeComplete')
}

function animateToPositions(newPositions: { [key: number]: { x: number; y: number } }) {
  const duration = 500 // 动画持续时间
  const startTime = performance.now()
  const startPositions = { ...taskPositions.value }
  
  function animate(currentTime: number) {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    
    // 使用easeInOutCubic缓动函数
    const easeProgress = progress < 0.5
      ? 4 * progress * progress * progress
      : 1 - Math.pow(-2 * progress + 2, 3) / 2
    
    // 插值计算当前位置
    Object.keys(newPositions).forEach(taskIdStr => {
      const taskId = parseInt(taskIdStr)
      const startPos = startPositions[taskId] || { x: 0, y: 0 }
      const endPos = newPositions[taskId]
      
      taskPositions.value[taskId] = {
        x: startPos.x + (endPos.x - startPos.x) * easeProgress,
        y: startPos.y + (endPos.y - startPos.y) * easeProgress
      }
    })
    
    if (progress < 1) {
      requestAnimationFrame(animate)
    }
  }
  
  requestAnimationFrame(animate)
}

// Expose auto arrange function
defineExpose({
  triggerAutoArrange
})

// Note: Watch for tasks is already handled above in the debug section
</script>

<style scoped>
.sticky-canvas {
  position: relative;
  width: 100%;
  height: 100%;
  background: #f8f9fa;
  overflow: hidden;
  cursor: grab;
}

.sticky-canvas:active {
  cursor: grabbing;
}

.canvas-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0.1;
  background-image: 
    linear-gradient(rgba(0,0,0,0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,0.1) 1px, transparent 1px);
  background-size: 20px 20px;
  pointer-events: none;
  z-index: 0;
}


.task-wrapper:active {
  cursor: grabbing;
}

.task-wrapper:hover {
  z-index: 10;
}

/* Smooth transitions when not dragging */
.task-wrapper:not(.dragging) {
  transition: left 0.2s ease, top 0.2s ease;
}

/* Hardware acceleration for dragging */
.task-wrapper.dragging {
  will-change: transform;
  transition: none;
  transform: translate3d(0, 0, 0) !important;
}

/* Optimize all task wrappers */
.task-wrapper {
  position: absolute;
  cursor: grab;
  user-select: none;
  z-index: 1;
  contain: layout;
  transform: translate3d(0, 0, 0);
}

/* Prevent text selection during drag */
.sticky-canvas * {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}
</style>