<template>
  <div class="connection-layer">
    <!-- 连接线渲染组件 -->
    <TaskConnections
      :connections="connections"
      :task-positions="taskPositions"
      :task-dimensions="taskDimensions"
      :canvas-width="canvasSize.width"
      :canvas-height="canvasSize.height"
      :viewport="viewport"
      :preview-connection="previewConnection"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import TaskConnections from '../TaskConnections.vue'
import { type Task, type TaskDependency } from '@/stores/tasks'

interface Props {
  connections: TaskDependency[]
  taskPositions: Record<number, { x: number; y: number }>
  taskDimensions: Record<number, { width: number; height: number }>
  canvasSize: { width: number; height: number }
  viewport: {
    x: number
    y: number
    scale: number
  }
  containerElement: HTMLElement | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  connectionCreate: [fromTaskId: number, toTaskId: number]
  connectionStart: [fromTaskId: number, event: MouseEvent]
  connectionEnd: []
}>()

// 连接状态
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

// 连接预览
const previewConnection = ref<{
  fromTaskId: number
  toX: number
  toY: number
} | null>(null)

// 开始连接
function startConnection(fromTaskId: number, event: MouseEvent) {
  console.log('ConnectionLayer: startConnection called with task:', fromTaskId)
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
  
  emit('connectionStart', fromTaskId, event)
}

// 连接拖拽处理
function handleConnectionDrag(event: MouseEvent) {
  if (!connectionState.value.isConnecting) return
  updateConnectionPreview(event.clientX, event.clientY)
}

// 更新连接预览
function updateConnectionPreview(clientX: number, clientY: number) {
  if (!connectionState.value.fromTaskId || !props.containerElement) return
  
  const canvasRect = props.containerElement.getBoundingClientRect()
  
  // 精确计算考虑视口变换的鼠标位置
  const canvasMouseX = clientX - canvasRect.left
  const canvasMouseY = clientY - canvasRect.top
  
  previewConnection.value = {
    fromTaskId: connectionState.value.fromTaskId,
    toX: canvasMouseX,
    toY: canvasMouseY
  }
}

// 结束连接
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
      emit('connectionCreate', connectionState.value.fromTaskId!, toTaskId)
    }
  }
  
  // Reset connection state
  connectionState.value = {
    isConnecting: false,
    fromTaskId: null,
    startX: 0,
    startY: 0
  }
  previewConnection.value = null
  
  emit('connectionEnd')
}

// 进入连接模式
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
  if (props.containerElement) {
    props.containerElement.style.cursor = 'crosshair'
  }
  
  // Add click listener to all task elements for connection target
  document.addEventListener('click', handleConnectionTargetClick)
}

// 处理连接目标点击
function handleConnectionTargetClick(event: MouseEvent) {
  if (!connectionState.value.isConnecting) return
  
  const targetElement = event.target as HTMLElement
  const taskElement = targetElement.closest('[data-task-id]') as HTMLElement
  
  if (taskElement) {
    const toTaskId = parseInt(taskElement.dataset.taskId || '0')
    if (toTaskId && toTaskId !== connectionState.value.fromTaskId) {
      // Create dependency
      emit('connectionCreate', connectionState.value.fromTaskId!, toTaskId)
      exitConnectionMode()
    }
  } else {
    // Clicked outside tasks, exit connection mode
    exitConnectionMode()
  }
}

// 退出连接模式
function exitConnectionMode() {
  // Remove visual feedback
  const sourceElement = document.querySelector('.connection-source')
  if (sourceElement) {
    sourceElement.classList.remove('connection-source')
  }
  
  // Reset cursor
  if (props.containerElement) {
    props.containerElement.style.cursor = 'default'
  }
  
  // Reset connection state
  connectionState.value = {
    isConnecting: false,
    fromTaskId: null,
    startX: 0,
    startY: 0
  }
  previewConnection.value = null
  
  // Remove event listeners
  document.removeEventListener('click', handleConnectionTargetClick)
}

// 清理连接预览
function clearConnectionPreview() {
  previewConnection.value = null
}

// 暴露方法给父组件
defineExpose({
  startConnection,
  enterConnectionMode,
  exitConnectionMode,
  clearConnectionPreview,
  connectionState: computed(() => connectionState.value),
  previewConnection: computed(() => previewConnection.value)
})
</script>

<style scoped>
.connection-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
}

/* 连接源的视觉反馈 */
:global(.connection-source) {
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
  border-color: rgb(59, 130, 246);
}

/* 连接模式下的光标样式 */
:global(.canvas-container.connecting) {
  cursor: crosshair !important;
}
</style> 