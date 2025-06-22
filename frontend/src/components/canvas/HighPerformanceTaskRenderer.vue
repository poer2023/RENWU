<template>
  <div class="task-renderer" ref="rendererContainer">
    <!-- 虚拟化的任务容器 -->
    <div
      v-for="task in visibleTasks"
      :key="task.id"
      :ref="(el) => setTaskRef(el as HTMLElement, task.id)"
      :class="['task-wrapper', { 
        'dragging': isDragging(task.id),
        'gpu-accelerated': gpuAcceleratedTasks.has(task.id)
      }]"
      :style="getTaskStyle(task)"
      :data-task-id="task.id"
      @mousedown="handleTaskMouseDown(task, $event)"
    >
      <TaskCard
        :task="task"
        :is-selected="selectedTask?.id === task.id"
        @select="$emit('selectTask', task)"
        @openDetails="(task, position) => $emit('openDetails', task, position)"
        @startConnection="(taskId, event) => $emit('startConnection', taskId, event)"
        @getTaskPosition="getTaskPositionData"
        @subtasksCreated="$emit('subtasksCreated', $event)"
      />
    </div>
    
    <!-- 性能指示器 (开发模式) -->
    <div v-if="showPerformanceStats" class="performance-stats">
      <div>Visible: {{ visibleTasks.length }}/{{ totalTasks }}</div>
      <div>FPS: {{ fps }}</div>
      <div>GPU: {{ gpuAcceleratedTasks.size }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import TaskCard from '../TaskCard.vue'
import { type Task } from '@/stores/tasks'

interface Props {
  tasks: Task[]
  selectedTask?: Task | null
  taskPositions: Record<number, { x: number; y: number }>
  taskDimensions: Record<number, { width: number; height: number }>
  dragState: {
    isDragging: boolean
    task: Task | null
  }
  viewport: {
    x: number
    y: number
    scale: number
  }
  canvasSize: { width: number; height: number }
  containerElement: HTMLElement | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  selectTask: [task: Task]
  openDetails: [task: Task, position: { x: number; y: number }]
  startConnection: [taskId: number, event: MouseEvent]
  subtasksCreated: [data: { parentTask: Task; subtasks: Task[] }]
  taskMouseDown: [task: Task, event: MouseEvent]
  updateTaskDimensions: [taskId: number, dimensions: { width: number; height: number }]
}>()

// 性能相关变量
const rendererContainer = ref<HTMLElement>()
const taskElements = new Map<number, HTMLElement>()
const gpuAcceleratedTasks = new Set<number>()
const transformCache = new Map<number, string>()
const showPerformanceStats = ref(process.env.NODE_ENV === 'development')

// 性能监控
const fps = ref(60)
let frameCount = 0
let lastFpsUpdate = Date.now()

// 虚拟化相关
let visibleBounds = { left: 0, top: 0, right: 0, bottom: 0 }
let lastBoundsUpdate = 0
const BOUNDS_UPDATE_INTERVAL = 100 // 100ms更新一次边界
const TASK_MARGIN = 300 // 可见区域边距
const VIRTUALIZATION_THRESHOLD = 100 // 超过100个任务启用虚拟化

// 批量更新队列
const updateQueue = new Set<number>()
let batchUpdateScheduled = false

// 获取总任务数
const totalTasks = computed(() => props.tasks.length)

// 智能虚拟化 - 只在任务数量多时启用
const useVirtualization = computed(() => props.tasks.length > VIRTUALIZATION_THRESHOLD)

// 计算可见任务
const visibleTasks = computed(() => {
  if (!useVirtualization.value) {
    return props.tasks
  }

  // 在拖拽时减少计算频率
  if (props.dragState.isDragging) {
    const now = Date.now()
    if (now - lastBoundsUpdate < BOUNDS_UPDATE_INTERVAL * 2) {
      return cachedVisibleTasks.value
    }
  }

  updateVisibleBounds()
  
  return props.tasks.filter(task => {
    const pos = props.taskPositions[task.id]
    if (!pos) return true
    
    const dimensions = props.taskDimensions[task.id] || { width: 240, height: 120 }
    
    return !(pos.x + dimensions.width < visibleBounds.left || 
             pos.x > visibleBounds.right || 
             pos.y + dimensions.height < visibleBounds.top || 
             pos.y > visibleBounds.bottom)
  })
})

// 缓存可见任务
const cachedVisibleTasks = ref<Task[]>([])

// 更新可见边界
function updateVisibleBounds() {
  if (!props.containerElement) return
  
  const now = Date.now()
  if (now - lastBoundsUpdate < BOUNDS_UPDATE_INTERVAL) return
  
  const rect = props.containerElement.getBoundingClientRect()
  const scale = props.viewport.scale
  
  visibleBounds = {
    left: (-props.viewport.x) / scale - TASK_MARGIN,
    top: (-props.viewport.y) / scale - TASK_MARGIN,
    right: (-props.viewport.x + rect.width) / scale + TASK_MARGIN,
    bottom: (-props.viewport.y + rect.height) / scale + TASK_MARGIN
  }
  
  lastBoundsUpdate = now
  cachedVisibleTasks.value = visibleTasks.value
}

// 设置任务元素引用
function setTaskRef(el: HTMLElement | null, taskId: number) {
  if (el) {
    taskElements.set(taskId, el)
    // 启用GPU加速
    enableGPUAcceleration(el, taskId)
  } else {
    taskElements.delete(taskId)
    gpuAcceleratedTasks.delete(taskId)
  }
}

// 启用GPU加速
function enableGPUAcceleration(element: HTMLElement, taskId: number) {
  if (gpuAcceleratedTasks.has(taskId)) return
  
  element.style.willChange = 'transform'
  element.style.backfaceVisibility = 'hidden'
  element.style.transform = element.style.transform || 'translate3d(0,0,0)'
  
  gpuAcceleratedTasks.add(taskId)
}

// 禁用GPU加速
function disableGPUAcceleration(element: HTMLElement, taskId: number) {
  element.style.willChange = 'auto'
  element.style.backfaceVisibility = ''
  
  gpuAcceleratedTasks.delete(taskId)
}

// 检查任务是否正在拖拽
function isDragging(taskId: number): boolean {
  return props.dragState.isDragging && props.dragState.task?.id === taskId
}

// 获取任务样式
function getTaskStyle(task: Task) {
  const position = props.taskPositions[task.id] || getDefaultPosition(task)
  const dragging = isDragging(task.id)
  
  // 基础样式
  const baseStyle = {
    position: 'absolute' as const,
    left: '0px',
    top: '0px',
    zIndex: dragging ? 1000 : 1
  }
  
  // 计算transform
  const scale = dragging ? 1.02 : 1
  const transform = `translate3d(${position.x}px, ${position.y}px, 0) scale(${scale})`
  
  // 检查是否需要更新
  const cachedTransform = transformCache.get(task.id)
  if (cachedTransform !== transform) {
    transformCache.set(task.id, transform)
  }
  
  return {
    ...baseStyle,
    transform,
    transition: dragging ? 'none' : 'transform 0.2s ease'
  }
}

// 生成默认位置
function getDefaultPosition(task: Task) {
  const moduleOffset = (task.module_id || 0) * 250
  const urgencyOffset = task.urgency * 60
  const randomOffset = Math.random() * 100
  
  return {
    x: 50 + moduleOffset + randomOffset,
    y: 50 + urgencyOffset + randomOffset
  }
}

// 获取任务位置数据
function getTaskPositionData(taskId: number) {
  return props.taskPositions[taskId] || { x: 0, y: 0 }
}

// 处理任务鼠标按下
function handleTaskMouseDown(task: Task, event: MouseEvent) {
  emit('taskMouseDown', task, event)
}

// 批量更新任务尺寸
function scheduleTaskDimensionsUpdate(taskId?: number) {
  if (taskId) {
    updateQueue.add(taskId)
  } else {
    props.tasks.forEach(task => updateQueue.add(task.id))
  }
  
  if (!batchUpdateScheduled) {
    batchUpdateScheduled = true
    nextTick(() => {
      processBatchUpdate()
      batchUpdateScheduled = false
    })
  }
}

// 处理批量更新
function processBatchUpdate() {
  const updates: Array<{ taskId: number; dimensions: { width: number; height: number } }> = []
  
  updateQueue.forEach(taskId => {
    const element = taskElements.get(taskId)
    if (element) {
      const rect = element.getBoundingClientRect()
      if (rect.width > 0 && rect.height > 0) {
        updates.push({
          taskId,
          dimensions: { width: rect.width, height: rect.height }
        })
      }
    }
  })
  
  // 批量发送更新
  updates.forEach(({ taskId, dimensions }) => {
    emit('updateTaskDimensions', taskId, dimensions)
  })
  
  updateQueue.clear()
}

// 性能监控
function updateFPS() {
  frameCount++
  const now = Date.now()
  if (now - lastFpsUpdate > 1000) {
    fps.value = Math.round((frameCount * 1000) / (now - lastFpsUpdate))
    frameCount = 0
    lastFpsUpdate = now
  }
  
  requestAnimationFrame(updateFPS)
}

// 监听任务变化
watch(() => props.tasks.length, () => {
  scheduleTaskDimensionsUpdate()
})

// 监听视口变化，更新可见边界
watch(() => [props.viewport.x, props.viewport.y, props.viewport.scale], () => {
  if (useVirtualization.value) {
    updateVisibleBounds()
  }
}, { flush: 'post' })

// 组件挂载
onMounted(() => {
  nextTick(() => {
    scheduleTaskDimensionsUpdate()
    if (showPerformanceStats.value) {
      updateFPS()
    }
  })
})

// 组件卸载
onUnmounted(() => {
  // 清理GPU加速
  taskElements.forEach((element, taskId) => {
    disableGPUAcceleration(element, taskId)
  })
  
  taskElements.clear()
  gpuAcceleratedTasks.clear()
  transformCache.clear()
  updateQueue.clear()
})

// 暴露方法
defineExpose({
  scheduleTaskDimensionsUpdate,
  updateVisibleBounds,
  taskElements: () => taskElements
})
</script>

<style scoped>
.task-renderer {
  position: relative;
  width: 100%;
  height: 100%;
  contain: layout style paint;
}

.task-wrapper {
  will-change: auto;
  backface-visibility: hidden;
  contain: layout style;
}

.task-wrapper.dragging {
  will-change: transform;
  z-index: 1000;
}

.task-wrapper.gpu-accelerated {
  transform: translate3d(0, 0, 0); /* 触发硬件加速 */
}

.performance-stats {
  position: fixed;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  z-index: 10000;
  pointer-events: none;
}

.performance-stats div {
  margin: 2px 0;
}
</style> 