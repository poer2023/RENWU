<template>
  <div class="task-renderer">
    <!-- Task wrappers with drag and connection functionality -->
    <div
      v-for="task in visibleTasks"
      :key="task.id"
      ref="taskElements"
      :class="['task-wrapper', { 'dragging': isDragging(task.id) }]"
      :style="getTaskPosition(task)"
      :data-task-id="task.id"
      @mousedown="$emit('taskMouseDown', task, $event)"
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
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
    startX: number
    startY: number
    offsetX: number
    offsetY: number
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
}>()

const taskElements = ref<HTMLElement[]>([])

// 缓存可见区域计算结果
const visibleBounds = ref({
  left: 0,
  top: 0,
  right: 0,
  bottom: 0,
  lastUpdate: 0
})

// 添加一个缓存的可见任务列表
let cachedVisibleTasks: Task[] = []
let lastVisibleTasksUpdate = 0

// 虚拟化渲染 - 只渲染可见区域的任务
const visibleTasks = computed(() => {
  // 如果任务少，直接返回所有任务
  if (props.tasks.length < 50) {
    return props.tasks
  }
  
  // 平移时使用缓存，减少计算
  const now = Date.now()
  if (props.dragState.isDragging && now - lastVisibleTasksUpdate < 100) {
    return cachedVisibleTasks
  }
  
  // 更新可见边界
  if (!props.containerElement) {
    return props.tasks
  }
  
  const rect = props.containerElement.getBoundingClientRect()
  
  // 计算可见区域（考虑缩放和平移）
  const visibleLeft = (-props.viewport.x) / props.viewport.scale - 300 // 增加边距
  const visibleTop = (-props.viewport.y) / props.viewport.scale - 300
  const visibleRight = visibleLeft + (rect.width / props.viewport.scale) + 600
  const visibleBottom = visibleTop + (rect.height / props.viewport.scale) + 600
  
  // 过滤可见任务
  cachedVisibleTasks = props.tasks.filter(task => {
    const pos = props.taskPositions[task.id]
    if (!pos) return true
    
    const taskWidth = props.taskDimensions[task.id]?.width || 240
    const taskHeight = props.taskDimensions[task.id]?.height || 120
    
    // 快速边界检查
    return !(pos.x + taskWidth < visibleLeft || 
             pos.x > visibleRight || 
             pos.y + taskHeight < visibleTop || 
             pos.y > visibleBottom)
  })
  
  lastVisibleTasksUpdate = now
  return cachedVisibleTasks
})

// 检查任务是否正在拖拽
function isDragging(taskId: number): boolean {
  return props.dragState.isDragging && props.dragState.task?.id === taskId
}

// 获取任务位置样式
function getTaskPosition(task: Task) {
  const position = props.taskPositions[task.id] || getDefaultPosition(task)
  const dragging = isDragging(task.id)
  
  // 拖动时使用内联样式，非拖动时使用CSS transform
  if (dragging) {
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

// 更新任务尺寸缓存
function updateTaskDimensions() {
  nextTick(() => {
    props.tasks.forEach(task => {
      const element = document.querySelector(`[data-task-id="${task.id}"]`) as HTMLElement
      if (element) {
        const rect = element.getBoundingClientRect()
        // 这里需要通过emit通知父组件更新尺寸
        // 或者通过props传入更新函数
      }
    })
  })
}

// 监听任务变化，更新尺寸
watch(() => props.tasks.length, () => {
  updateTaskDimensions()
})

// 暴露方法给父组件
defineExpose({
  updateTaskDimensions,
  taskElements
})
</script>

<style scoped>
.task-renderer {
  position: relative;
  width: 100%;
  height: 100%;
}

.task-wrapper {
  transition: transform 0.2s ease;
}

.task-wrapper.dragging {
  transition: none;
  z-index: 1000;
}
</style> 