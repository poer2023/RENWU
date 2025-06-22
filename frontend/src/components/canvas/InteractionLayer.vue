<template>
  <div 
    class="interaction-layer"
    @mousedown="handleCanvasMouseDown"
    @wheel="handleCanvasWheel"
    @contextmenu.prevent
  >
    <!-- 透明的交互层，覆盖整个画布 -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { type Task } from '@/stores/tasks'
import { debounce, throttle } from 'lodash'

interface Props {
  containerElement: HTMLElement | null
  canvasSize: { width: number; height: number }
  viewport: {
    x: number
    y: number
    scale: number
    minScale: number
    maxScale: number
  }
  dragState: {
    isDragging: boolean
    task: Task | null
    startX: number
    startY: number
    offsetX: number
    offsetY: number
  }
  panState: {
    isPanning: boolean
    startX: number
    startY: number
    startViewportX: number
    startViewportY: number
    maxX: number
    maxY: number
    minX: number
    minY: number
  }
  taskPositions: Record<number, { x: number; y: number }>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  selectTask: [task: Task | null]
  startDrag: [task: Task, event: MouseEvent]
  updateViewport: [viewport: { x: number; y: number; scale: number }]
  updateTaskPosition: [taskId: number, x: number, y: number]
  panStart: [event: MouseEvent]
  panMove: [event: MouseEvent]
  panEnd: []
}>()

// RAF管理
const wheelRafId = ref<number | null>(null)
const panRafId = ref<number | null>(null)
const dragRafId = ref<number | null>(null)

// 缓存的变换值
const cachedTransform = ref({
  x: 0,
  y: 0,
  scale: 1
})

// 画布内容元素引用
const canvasContentRef = ref<HTMLElement | null>(null)

// 优化的滚轮处理函数
function handleCanvasWheel(event: WheelEvent) {
  event.preventDefault()
  
  // 使用 RAF 优化滚轮事件处理
  if (wheelRafId.value) {
    cancelAnimationFrame(wheelRafId.value)
  }
  
  wheelRafId.value = requestAnimationFrame(() => {
    const rect = props.containerElement?.getBoundingClientRect()
    if (!rect) return
    
    // 获取鼠标在画布中的位置
    const mouseX = event.clientX - rect.left
    const mouseY = event.clientY - rect.top
    
    // 计算缩放前的世界坐标
    const worldX = (mouseX - props.viewport.x) / props.viewport.scale
    const worldY = (mouseY - props.viewport.y) / props.viewport.scale
    
    // 计算缩放因子（平滑缩放）
    const scaleFactor = event.deltaY > 0 ? 0.9 : 1.1
    const newScale = Math.max(
      props.viewport.minScale, 
      Math.min(props.viewport.maxScale, props.viewport.scale * scaleFactor)
    )
    
    // 如果缩放值没有变化，说明已达到边界
    if (newScale === props.viewport.scale) return
    
    // 计算新的视口位置，保持鼠标位置不变
    const newX = mouseX - worldX * newScale
    const newY = mouseY - worldY * newScale
    
    // 应用约束，防止画布飞出视野
    const maxX = rect.width * 0.5
    const maxY = rect.height * 0.5
    const minX = -(props.canvasSize.width * newScale - rect.width * 0.5)
    const minY = -(props.canvasSize.height * newScale - rect.height * 0.5)
    
    const constrainedViewport = {
      x: Math.max(minX, Math.min(maxX, newX)),
      y: Math.max(minY, Math.min(maxY, newY)),
      scale: newScale
    }
    
    emit('updateViewport', constrainedViewport)
  })
}

// 优化的鼠标按下处理函数
function handleCanvasMouseDown(event: MouseEvent) {
  // 只处理中键（滚轮按下）进行平移
  if (event.button === 1) {
    event.preventDefault()
    startPan(event)
  } else if (event.button === 0) {
    // 左键点击 - 检查是否点击在空白区域
    const target = event.target as HTMLElement
    const isCanvas = target.classList.contains('interaction-layer') || 
                    target.classList.contains('canvas-grid') || 
                    target.classList.contains('canvas-content')
    const isTaskOrChild = target.closest('.task-wrapper') !== null
    
    if (isCanvas && !isTaskOrChild) {
      // 只有点击空白区域才取消选择
      emit('selectTask', null)
    }
  }
}

// 平滑的平移开始函数
function startPan(event: MouseEvent) {
  const rect = props.containerElement?.getBoundingClientRect()
  if (!rect) return
  
  // 预计算边界约束以提高性能
  const maxX = rect.width * 0.5
  const maxY = rect.height * 0.5
  const minX = -(props.canvasSize.width * props.viewport.scale - rect.width * 0.5)
  const minY = -(props.canvasSize.height * props.viewport.scale - rect.height * 0.5)
  
  // 同步当前的viewport到缓存
  cachedTransform.value.x = props.viewport.x
  cachedTransform.value.y = props.viewport.y
  cachedTransform.value.scale = props.viewport.scale
  
  const panData = {
    isPanning: true,
    startX: event.clientX,
    startY: event.clientY,
    startViewportX: props.viewport.x,
    startViewportY: props.viewport.y,
    maxX,
    maxY,
    minX,
    minY
  }
  
  // 设置鼠标样式
  document.body.style.cursor = 'grabbing'
  
  // 获取canvas content元素的引用
  const contentElement = props.containerElement?.querySelector('.canvas-content') as HTMLElement
  if (contentElement) {
    canvasContentRef.value = contentElement
    // 启用硬件加速
    contentElement.style.willChange = 'transform'
    contentElement.style.transform = `translate3d(${cachedTransform.value.x}px, ${cachedTransform.value.y}px, 0) scale(${cachedTransform.value.scale})`
  }
  
  // 添加全局事件监听，使用 passive: false 以便阻止默认行为
  document.addEventListener('mousemove', handlePan, { passive: false })
  document.addEventListener('mouseup', stopPan, { passive: false })
  document.addEventListener('mouseleave', stopPan, { passive: false })
  
  // 防止选择文本
  document.body.style.userSelect = 'none'
  
  emit('panStart', event)
}

// 高性能的平移处理函数
function handlePan(event: MouseEvent) {
  if (!props.panState.isPanning || !canvasContentRef.value) return
  
  event.preventDefault() // 防止页面滚动
  
  // 直接计算位移，不使用RAF
  const deltaX = event.clientX - props.panState.startX
  const deltaY = event.clientY - props.panState.startY
  
  const newX = props.panState.startViewportX + deltaX
  const newY = props.panState.startViewportY + deltaY
  
  // 使用预计算的边界约束
  const constrainedX = Math.max(props.panState.minX, Math.min(props.panState.maxX, newX))
  const constrainedY = Math.max(props.panState.minY, Math.min(props.panState.maxY, newY))
  
  // 更新缓存的transform值
  cachedTransform.value.x = constrainedX
  cachedTransform.value.y = constrainedY
  
  // 直接操作DOM，绕过Vue的响应式系统
  canvasContentRef.value.style.transform = `translate3d(${constrainedX}px, ${constrainedY}px, 0) scale(${cachedTransform.value.scale})`
  
  emit('panMove', event)
}

// 停止平移函数
function stopPan() {
  if (panRafId.value) {
    cancelAnimationFrame(panRafId.value)
    panRafId.value = null
  }
  
  // 同步缓存的值回到响应式数据
  emit('updateViewport', {
    x: cachedTransform.value.x,
    y: cachedTransform.value.y,
    scale: cachedTransform.value.scale
  })
  
  // 清理样式
  document.body.style.cursor = 'default'
  document.body.style.userSelect = 'auto'
  
  // 移除事件监听
  document.removeEventListener('mousemove', handlePan, { passive: false } as any)
  document.removeEventListener('mouseup', stopPan, { passive: false } as any)
  document.removeEventListener('mouseleave', stopPan, { passive: false } as any)
  
  // 禁用硬件加速
  if (canvasContentRef.value) {
    canvasContentRef.value.style.willChange = 'auto'
  }
  
  emit('panEnd')
}

// 拖拽相关函数
function startDrag(task: Task, event: MouseEvent) {
  if (event.button !== 0) return // Only left mouse button
  
  event.preventDefault()
  event.stopPropagation()
  
  const rect = props.containerElement?.getBoundingClientRect()
  if (!rect) return
  
  // Cache canvas rect and card dimensions for performance
  const cardElement = document.querySelector(`[data-task-id="${task.id}"]`) as HTMLElement
  const cardDimensions = cardElement ? {
    width: cardElement.offsetWidth || 240,
    height: cardElement.offsetHeight || 120
  } : { width: 240, height: 120 }
  
  const currentPos = props.taskPositions[task.id] || getDefaultPosition(task)
  
  // 计算鼠标相对于卡片的精确偏移量（考虑缩放和视口变换）
  const canvasMouseX = (event.clientX - rect.left - props.viewport.x) / props.viewport.scale
  const canvasMouseY = (event.clientY - rect.top - props.viewport.y) / props.viewport.scale
  
  const offsetX = canvasMouseX - currentPos.x
  const offsetY = canvasMouseY - currentPos.y
  
  const dragData = {
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
  
  // Enable GPU acceleration for the dragging task
  if (cardElement) {
    cardElement.style.willChange = 'transform'
    cardElement.style.transition = 'none'
  }
  
  emit('startDrag', task, event)
}

// 优化的拖动处理函数
function handleDrag(event: MouseEvent) {
  if (!props.dragState.isDragging || !props.dragState.task) return
  
  event.preventDefault()
  
  // 使用 requestAnimationFrame 来优化拖动，避免过于频繁的更新
  if (dragRafId.value) {
    cancelAnimationFrame(dragRafId.value)
  }
  
  dragRafId.value = requestAnimationFrame(() => {
    if (!props.dragState.isDragging || !props.dragState.task) return
    
    // 重新获取最新的rect，以防画布移动
    const rect = props.containerElement?.getBoundingClientRect()
    if (!rect) return
    
    // 计算新位置（考虑缩放和视口变换）
    const canvasMouseX = (event.clientX - rect.left - props.viewport.x) / props.viewport.scale
    const canvasMouseY = (event.clientY - rect.top - props.viewport.y) / props.viewport.scale
    
    const newX = canvasMouseX - props.dragState.offsetX
    const newY = canvasMouseY - props.dragState.offsetY
    
    // 限制在画布边界内
    const cardDimensions = { width: 240, height: 120 } // 可以从props传入
    const boundedX = Math.max(0, Math.min(props.canvasSize.width - cardDimensions.width, newX))
    const boundedY = Math.max(0, Math.min(props.canvasSize.height - cardDimensions.height, newY))
    
    // 更新任务位置
    emit('updateTaskPosition', props.dragState.task.id, boundedX, boundedY)
  })
}

// 优化的停止拖动函数
function stopDrag(event: MouseEvent) {
  if (!props.dragState.isDragging || !props.dragState.task) return
  
  event.preventDefault()
  
  // 取消任何挂起的动画帧
  if (dragRafId.value) {
    cancelAnimationFrame(dragRafId.value)
    dragRafId.value = null
  }
  
  // 恢复正常的鼠标样式
  document.body.style.userSelect = 'auto'
  document.body.style.cursor = 'default'
  
  // 移除全局事件监听
  document.removeEventListener('mousemove', handleDrag, { capture: true } as any)
  document.removeEventListener('mouseup', stopDrag, { capture: true } as any)
  
  // 清理拖动元素的样式
  const cardElement = document.querySelector(`[data-task-id="${props.dragState.task.id}"]`) as HTMLElement
  if (cardElement) {
    cardElement.style.willChange = 'auto'
    cardElement.style.transition = ''
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

// 防抖的位置保存函数
const debouncedSavePosition = debounce(async (taskId: number, x: number, y: number) => {
  emit('updateTaskPosition', taskId, x, y)
}, 500)

// 暴露方法给父组件
defineExpose({
  startDrag,
  stopDrag: () => stopDrag(new MouseEvent('mouseup'))
})
</script>

<style scoped>
.interaction-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: auto;
  cursor: default;
}

.interaction-layer:active {
  cursor: grabbing;
}
</style> 