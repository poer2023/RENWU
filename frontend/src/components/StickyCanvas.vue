<template>
  <div 
    ref="canvasContainer" 
    :class="['sticky-canvas', { 'dragging': dragState.isDragging, 'panning': panState.isPanning }]"
    @mousedown="handleCanvasMouseDown"
    @wheel="handleCanvasWheel"
    @contextmenu.prevent
  >
    <!-- Canvas content with transform -->
    <div 
      class="canvas-content" 
      :style="canvasContentStyle"
    >
      <!-- Canvas background grid -->
      <div class="canvas-grid"></div>
      
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

      <!-- Island Headers -->
      <div v-if="islandView" class="island-headers">
        <div
          v-for="(island, index) in islands"
          :key="island.id"
          :class="['island-header', { 'collapsed': island.collapsed }]"
          :style="getIslandHeaderStyle(island, index)"
          @click="toggleIsland(island)"
        >
          <div class="island-title">
            <span class="island-icon">🏝️</span>
            <span class="island-name">{{ island.name }}</span>
            <span class="island-count">({{ island.tasks.length }})</span>
          </div>
          <div v-if="island.keywords" class="island-keywords">
            <span v-for="keyword in island.keywords.slice(0, 3)" :key="keyword" class="keyword-tag">
              {{ keyword }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Mini Map -->
    <MiniMap
      :tasks="tasks"
      :task-positions="taskPositions"
      :canvas-width="canvasSize.width"
      :canvas-height="canvasSize.height"
      :viewport-x="-viewport.x / viewport.scale"
      :viewport-y="-viewport.y / viewport.scale"
      :viewport-width="viewportWidth"
      :viewport-height="viewportHeight"
      :selected-task-id="selectedTask?.id"
      @focus-task="focusOnTask"
      @move-viewport="handleViewportMove"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import TaskCard from './TaskCard.vue'
import TaskConnections from './TaskConnections.vue'
import MiniMap from './MiniMap.vue'
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

// Canvas size - 动态计算实际需要的边界
const canvasSize = ref({ width: 2000, height: 2000 })

// Canvas viewport state (for pan and zoom)
const viewport = ref({
  x: 0,        // 水平偏移
  y: 0,        // 垂直偏移
  scale: 1,    // 缩放比例
  minScale: 0.1,  // 最小缩放
  maxScale: 3     // 最大缩放
})

// Pan state for middle mouse button dragging
const panState = ref({
  isPanning: false,
  startX: 0,
  startY: 0,
  startViewportX: 0,
  startViewportY: 0
})

// Dependencies from store
const dependencies = computed(() => taskStore.dependencies)

// Computed viewport dimensions for minimap
const viewportWidth = computed(() => {
  if (!canvasContainer.value) return 1200 / viewport.value.scale
  return canvasContainer.value.getBoundingClientRect().width / viewport.value.scale
})

const viewportHeight = computed(() => {
  if (!canvasContainer.value) return 800 / viewport.value.scale
  return canvasContainer.value.getBoundingClientRect().height / viewport.value.scale
})

// Canvas content style with transform
const canvasContentStyle = computed(() => ({
  width: `${canvasSize.value.width}px`,
  height: `${canvasSize.value.height}px`,
  transform: `translate(${viewport.value.x}px, ${viewport.value.y}px) scale(${viewport.value.scale})`,
  transformOrigin: '0 0',
  position: 'relative'
}))

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
  
  // Add global mouse event listeners with optimized settings for smooth dragging
  document.addEventListener('mousemove', handleDrag, { passive: false, capture: true })
  document.addEventListener('mouseup', stopDrag, { passive: false, capture: true })
  
  // Add styles for better dragging experience
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'grabbing'
  document.body.style.pointerEvents = 'none' // Prevent interference from other elements
  
  // Enable GPU acceleration for the dragging task
  if (cardElement) {
    cardElement.style.willChange = 'transform'
    cardElement.style.transition = 'none'
  }
  
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
  
  // 在画布坐标系中计算鼠标位置
  const canvasMouseX = (event.clientX - canvasRect.left - viewport.value.x) / viewport.value.scale
  const canvasMouseY = (event.clientY - canvasRect.top - viewport.value.y) / viewport.value.scale
  
  // 用固定的偏移量计算新位置，保持鼠标相对于卡片的位置不变
  const canvasX = canvasMouseX - dragState.value.offsetX
  const canvasY = canvasMouseY - dragState.value.offsetY
  
  // 只约束到容器的实际可见范围内，确保卡片边界与可视区域一致
  const containerRect = canvasContainer.value?.getBoundingClientRect()
  if (!containerRect) return
  
  const viewportWidth = containerRect.width / viewport.value.scale
  const viewportHeight = containerRect.height / viewport.value.scale
  const viewportLeft = -viewport.value.x / viewport.value.scale
  const viewportTop = -viewport.value.y / viewport.value.scale
  
  const padding = 10
  const constrainedX = Math.max(viewportLeft + padding, Math.min(canvasX, viewportLeft + viewportWidth - cardDimensions.width - padding))
  const constrainedY = Math.max(viewportTop + padding, Math.min(canvasY, viewportTop + viewportHeight - cardDimensions.height - padding))
  
  // Update position immediately with requestAnimationFrame for smoother updates
  requestAnimationFrame(() => {
    taskPositions.value[dragState.value.task!.id] = {
      x: constrainedX,
      y: constrainedY
    }
  })
  
  // In island view, highlight target island
  if (islandView.value) {
    highlightTargetIsland(event.clientX, event.clientY)
  }
}

function stopDrag(event?: MouseEvent) {
  if (!dragState.value.isDragging) return
  
  const draggedTask = dragState.value.task
  
  // 动态扩展画布边界以容纳新位置的任务
  if (draggedTask) {
    const position = taskPositions.value[draggedTask.id]
    if (position) {
      const newCanvasWidth = Math.max(canvasSize.value.width, position.x + cardDimensions.width + 200)
      const newCanvasHeight = Math.max(canvasSize.value.height, position.y + cardDimensions.height + 200)
      canvasSize.value = { width: newCanvasWidth, height: newCanvasHeight }
    }
  }
  
  // Handle island view task reassignment
  if (islandView.value && draggedTask && event) {
    const targetIsland = findTargetIsland(event.clientX, event.clientY)
    if (targetIsland) {
      handleTaskIslandChange(draggedTask, targetIsland)
    }
  }
  
  // Clear cached values
  canvasRect = null
  
  // Remove global mouse event listeners
  document.removeEventListener('mousemove', handleDrag, { capture: true } as any)
  document.removeEventListener('mouseup', stopDrag, { capture: true } as any)
  
  // Restore default styles
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
  document.body.style.pointerEvents = ''
  
  // Clean up GPU acceleration
  if (draggedTask) {
    const cardElement = document.querySelector(`[data-task-id="${draggedTask.id}"]`) as HTMLElement
    if (cardElement) {
      cardElement.style.willChange = 'auto'
      cardElement.style.transition = ''
    }
  }
  
  // Clear island highlights
  if (islandView.value) {
    clearIslandHighlights()
  }
  
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
  console.log('StickyCanvas: handleStartConnection called with task:', fromTaskId)
  event.preventDefault()
  event.stopPropagation()
  
  connectionState.value = {
    isConnecting: true,
    fromTaskId,
    startX: event.clientX,
    startY: event.clientY
  }
  
  console.log('Connection state set:', connectionState.value)
  
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
  
  // Update canvas size after initializing positions
  nextTick(() => {
    updateCanvasSize()
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
  }
  
  // Initialize positions for any existing tasks
  nextTick(() => {
    initializeTaskPositions()
    updateCanvasSize()
  })
})

// Update canvas size based on container and task positions
function updateCanvasSize() {
  if (!canvasContainer.value) return
  
  const containerRect = canvasContainer.value.getBoundingClientRect()
  let maxX = containerRect.width
  let maxY = containerRect.height
  
  // 计算所有任务的边界
  Object.values(taskPositions.value).forEach(position => {
    maxX = Math.max(maxX, position.x + cardDimensions.width + 100)
    maxY = Math.max(maxY, position.y + cardDimensions.height + 100)
  })
  
  canvasSize.value = {
    width: Math.max(containerRect.width * 2, maxX),
    height: Math.max(containerRect.height * 2, maxY)
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

// Island layout functionality
const islandView = ref(false)
const islands = ref<any[]>([])

function applyIslandLayout(islandData: any[]) {
  console.log('Applying island layout:', islandData)
  islandView.value = true
  islands.value = islandData
  
  // Calculate island positions and layout
  arrangeTasksInIslands()
}

function arrangeTasksInIslands() {
  if (!canvasContainer.value || islands.value.length === 0) return
  
  const containerRect = canvasContainer.value.getBoundingClientRect()
  const containerWidth = containerRect.width
  const containerHeight = containerRect.height
  
  // Calculate grid layout for islands
  const islandsCount = islands.value.length
  const cols = Math.ceil(Math.sqrt(islandsCount))
  const rows = Math.ceil(islandsCount / cols)
  
  const islandWidth = containerWidth / cols
  const islandHeight = containerHeight / rows
  const padding = 20
  
  islands.value.forEach((island, index) => {
    const row = Math.floor(index / cols)
    const col = index % cols
    
    const islandX = col * islandWidth + padding
    const islandY = row * islandHeight + padding
    const availableWidth = islandWidth - 2 * padding
    const availableHeight = islandHeight - 2 * padding
    
    // Arrange tasks within this island
    arrangeTasksInIsland(island.tasks, islandX, islandY, availableWidth, availableHeight)
  })
}

function arrangeTasksInIsland(tasks: any[], startX: number, startY: number, width: number, height: number) {
  if (!tasks || tasks.length === 0) return
  
  const taskWidth = 200
  const taskHeight = 120
  const spacing = 10
  
  const cols = Math.floor(width / (taskWidth + spacing))
  
  tasks.forEach((task, index) => {
    const row = Math.floor(index / cols)
    const col = index % cols
    
    const x = startX + col * (taskWidth + spacing)
    const y = startY + row * (taskHeight + spacing) + 30 // Reserve space for island header
    
    taskPositions.value[task.id] = { x, y }
  })
}

function focusOnTask(taskId: number) {
  // Find the task and center the view on it
  const task = props.tasks.find(t => t.id === taskId)
  if (task && taskPositions.value[taskId]) {
    const position = taskPositions.value[taskId]
    
    // 计算容器中心点
    if (canvasContainer.value) {
      const containerRect = canvasContainer.value.getBoundingClientRect()
      const centerX = containerRect.width / 2
      const centerY = containerRect.height / 2
      
      // 将任务定位到画布中心
      viewport.value.x = centerX - (position.x * viewport.value.scale) - 100 // 100是任务卡片宽度的一半
      viewport.value.y = centerY - (position.y * viewport.value.scale) - 60  // 60是任务卡片高度的一半
    }
    
    // 添加高亮效果
    const element = document.querySelector(`[data-task-id="${taskId}"]`) as HTMLElement
    if (element) {
      // 添加临时高亮效果
      element.style.boxShadow = '0 0 20px #2563eb, 0 0 40px rgba(37, 99, 235, 0.5)'
      element.style.transform = 'translateY(-4px) scale(1.05)'
      element.style.transition = 'all 0.3s ease'
      
      setTimeout(() => {
        element.style.boxShadow = ''
        element.style.transform = ''
        element.style.transition = ''
      }, 2000)
    }
  }
}

// 添加新函数：定位到最新任务
function focusOnLatestTask() {
  if (props.tasks.length === 0) return
  
  // 找到最新创建的任务（按创建时间排序）
  const latestTask = props.tasks.reduce((latest, current) => {
    const latestTime = new Date(latest.created_at).getTime()
    const currentTime = new Date(current.created_at).getTime()
    return currentTime > latestTime ? current : latest
  })
  
  focusOnTask(latestTask.id)
}

function exitIslandView() {
  islandView.value = false
  islands.value = []
  // Return to normal layout
  initializeTaskPositions()
}

function getIslandHeaderStyle(island: any, index: number) {
  if (!canvasContainer.value) return {}
  
  const containerRect = canvasContainer.value.getBoundingClientRect()
  const containerWidth = containerRect.width
  const containerHeight = containerRect.height
  
  const islandsCount = islands.value.length
  const cols = Math.ceil(Math.sqrt(islandsCount))
  const rows = Math.ceil(islandsCount / cols)
  
  const islandWidth = containerWidth / cols
  const islandHeight = containerHeight / rows
  const padding = 20
  
  const row = Math.floor(index / cols)
  const col = index % cols
  
  const islandX = col * islandWidth + padding
  const islandY = row * islandHeight + padding
  
  return {
    position: 'absolute',
    left: `${islandX}px`,
    top: `${islandY}px`,
    width: `${islandWidth - 2 * padding}px`,
    backgroundColor: island.color,
    borderColor: island.color
  }
}

function toggleIsland(island: any) {
  island.collapsed = !island.collapsed
  
  // Hide/show tasks in this island
  island.tasks.forEach((task: any) => {
    const element = document.querySelector(`[data-task-id="${task.id}"]`) as HTMLElement
    if (element) {
      if (island.collapsed) {
        element.style.display = 'none'
      } else {
        element.style.display = 'block'
      }
    }
  })
}

function highlightTargetIsland(clientX: number, clientY: number) {
  const targetIsland = findTargetIsland(clientX, clientY)
  
  // Clear previous highlights
  clearIslandHighlights()
  
  // Highlight target island
  if (targetIsland) {
    const islandIndex = islands.value.findIndex(island => island.id === targetIsland.id)
    if (islandIndex !== -1) {
      const headerElement = document.querySelector(`.island-header:nth-child(${islandIndex + 1})`) as HTMLElement
      if (headerElement) {
        headerElement.style.opacity = '1'
        headerElement.style.transform = 'translateY(-2px) scale(1.05)'
        headerElement.style.boxShadow = '0 8px 20px rgba(0, 0, 0, 0.3)'
      }
    }
  }
}

function findTargetIsland(clientX: number, clientY: number) {
  if (!canvasContainer.value) return null
  
  const containerRect = canvasContainer.value.getBoundingClientRect()
  const relativeX = clientX - containerRect.left
  const relativeY = clientY - containerRect.top
  
  const containerWidth = containerRect.width
  const containerHeight = containerRect.height
  
  const islandsCount = islands.value.length
  const cols = Math.ceil(Math.sqrt(islandsCount))
  const rows = Math.ceil(islandsCount / cols)
  
  const islandWidth = containerWidth / cols
  const islandHeight = containerHeight / rows
  const padding = 20
  
  for (let index = 0; index < islands.value.length; index++) {
    const row = Math.floor(index / cols)
    const col = index % cols
    
    const islandX = col * islandWidth + padding
    const islandY = row * islandHeight + padding
    const islandRight = islandX + islandWidth - 2 * padding
    const islandBottom = islandY + islandHeight - 2 * padding
    
    if (relativeX >= islandX && relativeX <= islandRight &&
        relativeY >= islandY && relativeY <= islandBottom) {
      return islands.value[index]
    }
  }
  
  return null
}

function clearIslandHighlights() {
  const headers = document.querySelectorAll('.island-header')
  headers.forEach(header => {
    const element = header as HTMLElement
    element.style.opacity = ''
    element.style.transform = ''
    element.style.boxShadow = ''
  })
}

async function handleTaskIslandChange(task: any, targetIsland: any) {
  try {
    // Call backend API to update task island
    const response = await fetch(`/api/tasks/${task.id}/island?island_id=${targetIsland.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      // Update local island data
      // Remove task from old island
      islands.value.forEach(island => {
        island.tasks = island.tasks.filter((t: any) => t.id !== task.id)
      })
      
      // Add task to new island
      targetIsland.tasks.push(task)
      
      console.log(`Task ${task.title} moved to island ${targetIsland.name}`)
    } else {
      console.error('Failed to update task island')
    }
  } catch (error) {
    console.error('Error updating task island:', error)
  }
}

function handleViewportMove(x: number, y: number) {
  // Update viewport position for infinite canvas
  viewport.value.x = -x * viewport.value.scale
  viewport.value.y = -y * viewport.value.scale
}

// Connection mode functions
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
}

function handleConnectionTargetClick(event: MouseEvent) {
  if (!connectionState.value.isConnecting) return
  
  const targetElement = event.target as HTMLElement
  const taskElement = targetElement.closest('[data-task-id]') as HTMLElement
  
  if (taskElement) {
    const toTaskId = parseInt(taskElement.dataset.taskId || '0')
    if (toTaskId && toTaskId !== connectionState.value.fromTaskId) {
      // Create dependency
      createTaskDependency(connectionState.value.fromTaskId!, toTaskId)
      exitConnectionMode()
    }
  } else {
    // Clicked outside tasks, exit connection mode
    exitConnectionMode()
  }
}

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
}

// Canvas pan and zoom functions
function handleCanvasMouseDown(event: MouseEvent) {
  // Only handle middle mouse button (button 1) for panning
  if (event.button === 1) {
    event.preventDefault()
    startPanning(event)
  }
}

function startPanning(event: MouseEvent) {
  panState.value = {
    isPanning: true,
    startX: event.clientX,
    startY: event.clientY,
    startViewportX: viewport.value.x,
    startViewportY: viewport.value.y
  }
  
  document.addEventListener('mousemove', handlePanDrag)
  document.addEventListener('mouseup', handlePanEnd)
  
  // Change cursor
  if (canvasContainer.value) {
    canvasContainer.value.style.cursor = 'grabbing'
  }
}

function handlePanDrag(event: MouseEvent) {
  if (!panState.value.isPanning) return
  
  const deltaX = event.clientX - panState.value.startX
  const deltaY = event.clientY - panState.value.startY
  
  viewport.value.x = panState.value.startViewportX + deltaX
  viewport.value.y = panState.value.startViewportY + deltaY
}

function handlePanEnd() {
  panState.value.isPanning = false
  
  document.removeEventListener('mousemove', handlePanDrag)
  document.removeEventListener('mouseup', handlePanEnd)
  
  // Reset cursor
  if (canvasContainer.value) {
    canvasContainer.value.style.cursor = 'grab'
  }
}

function handleCanvasWheel(event: WheelEvent) {
  // Only zoom with Ctrl key pressed
  if (!event.ctrlKey) return
  
  event.preventDefault()
  
  // 使用比例缩放而不是固定步长，确保一致的缩放体验
  const scaleFactor = 1.05  // 每次缩放5%
  const direction = event.deltaY > 0 ? -1 : 1  // 滚轮方向
  
  // 计算新的缩放比例
  const newScale = direction > 0 
    ? Math.min(viewport.value.maxScale, viewport.value.scale * scaleFactor)
    : Math.max(viewport.value.minScale, viewport.value.scale / scaleFactor)
  
  if (newScale !== viewport.value.scale) {
    // Get mouse position relative to canvas
    const rect = canvasContainer.value?.getBoundingClientRect()
    if (!rect) return
    
    const mouseX = event.clientX - rect.left
    const mouseY = event.clientY - rect.top
    
    // Calculate zoom point in canvas space
    const canvasX = (mouseX - viewport.value.x) / viewport.value.scale
    const canvasY = (mouseY - viewport.value.y) / viewport.value.scale
    
    // Update scale
    viewport.value.scale = newScale
    
    // Adjust position to zoom towards mouse cursor
    viewport.value.x = mouseX - canvasX * viewport.value.scale
    viewport.value.y = mouseY - canvasY * viewport.value.scale
  }
}

// Center viewport on canvas
function centerViewport() {
  if (!canvasContainer.value) return
  
  const containerRect = canvasContainer.value.getBoundingClientRect()
  viewport.value.x = (containerRect.width - canvasSize.value.width * viewport.value.scale) / 2
  viewport.value.y = (containerRect.height - canvasSize.value.height * viewport.value.scale) / 2
}

// Reset zoom to 100%
function resetZoom() {
  viewport.value.scale = 1
  centerViewport()
}

// Initialize viewport on mount
onMounted(() => {
  centerViewport()
})

// Expose functions
defineExpose({
  triggerAutoArrange,
  applyIslandLayout,
  focusOnTask,
  focusOnLatestTask,
  exitIslandView,
  enterConnectionMode,
  centerViewport,
  resetZoom
})

// Note: Watch for tasks is already handled above in the debug section
</script>

<style scoped>
.sticky-canvas {
  position: relative;
  width: 100%;
  height: 100%;
  background: var(--bg-base);
  overflow: hidden;
  cursor: grab;
  color: var(--text-primary);
  user-select: none; /* Prevent text selection during pan */
}

.sticky-canvas.panning {
  cursor: grabbing;
}

.sticky-canvas:active {
  cursor: grabbing;
}

.canvas-content {
  position: relative;
  pointer-events: none; /* Allow clicks to pass through to child elements */
}

.canvas-content > * {
  pointer-events: auto; /* Restore pointer events for child elements */
}

.canvas-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0.08;
  background-image: 
    linear-gradient(var(--grid-line, var(--border-subtle)) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid-line, var(--border-subtle)) 1px, transparent 1px);
  background-size: 50px 50px;
  background-position: 0 0;
  pointer-events: none;
  z-index: 0;
  transition: opacity 0.3s ease;
}

.sticky-canvas:hover .canvas-grid {
  opacity: 0.15;
}

/* Enhanced grid for drag operations */
.sticky-canvas.dragging .canvas-grid {
  opacity: 0.25;
  background-image: 
    linear-gradient(var(--primary) 1px, transparent 1px),
    linear-gradient(90deg, var(--primary) 1px, transparent 1px);
}

/* Grid dots for modern feel */
.canvas-grid::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: radial-gradient(circle, var(--text-muted) 1px, transparent 1px);
  background-size: 32px 32px;
  opacity: 0.1;
}


.task-wrapper:active {
  cursor: grabbing;
}

.task-wrapper:hover:not(.dragging) {
  z-index: 10;
  filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.15));
  transform: translate3d(0, -2px, 0) scale(1.01);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Smooth transitions when not dragging */
.task-wrapper:not(.dragging) {
  transition: left 0.15s cubic-bezier(0.4, 0, 0.2, 1), top 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Hardware acceleration for dragging */
.task-wrapper.dragging {
  will-change: transform, left, top;
  transition: none;
  transform: translate3d(0, 0, 0) scale(1.02) !important;
  z-index: 1001;
  filter: drop-shadow(0 12px 24px rgba(0, 0, 0, 0.25));
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

/* Optimize all task wrappers */
.task-wrapper {
  position: absolute;
  cursor: grab;
  user-select: none;
  z-index: 1;
  contain: layout style paint;
  transform: translate3d(0, 0, 0);
  animation: fadeIn 0.4s ease-out;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translate3d(0, 20px, 0) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0) scale(1);
  }
}

/* Prevent text selection during drag */
.sticky-canvas * {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

/* Island Headers */
.island-headers {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 5;
}

.island-header {
  background: var(--card-bg);
  border: 2px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  box-shadow: var(--shadow-md);
  cursor: pointer;
  pointer-events: auto;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(8px);
  max-height: 80px;
  overflow: hidden;
  color: var(--text-primary);
  animation: slideInFromTop 0.5s ease-out;
}

@keyframes slideInFromTop {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.island-header:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: var(--shadow-xl), 0 0 20px var(--primary-light);
  border-color: var(--primary);
  background: var(--card-hover);
}

.island-header:active {
  transform: translateY(-2px) scale(1.01);
  transition: all 0.1s ease;
}

.island-header.collapsed {
  opacity: 0.7;
}

.island-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.island-icon {
  font-size: 16px;
}

.island-name {
  color: var(--text-primary);
  font-weight: var(--font-weight-semibold);
}

.island-count {
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-normal);
}

.island-keywords {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.keyword-tag {
  background: var(--bg-elevated);
  color: var(--text-secondary);
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: var(--font-weight-normal);
  border: 1px solid var(--border-subtle);
  transition: all 0.2s ease;
  animation: fadeIn 0.3s ease-out;
}

.island-header:hover .keyword-tag {
  background: var(--primary-light);
  color: var(--primary);
  transform: translateY(-1px);
  border-color: var(--primary);
}

/* Connection Mode Styles */
:deep(.connection-source) {
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3), 0 0 20px rgba(37, 99, 235, 0.2);
  border: 2px solid var(--primary);
  animation: connection-pulse 1.5s ease-in-out infinite;
}

@keyframes connection-pulse {
  0%, 100% {
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3), 0 0 20px rgba(37, 99, 235, 0.2);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(37, 99, 235, 0.4), 0 0 30px rgba(37, 99, 235, 0.3);
  }
}

.canvas-container.connection-mode {
  cursor: crosshair !important;
}

:deep(.task-card):hover.connection-target {
  border: 2px solid var(--success);
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.2);
}
</style>