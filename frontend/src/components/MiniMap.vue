<template>
  <div class="mini-map" v-if="visible">
    <div class="mini-map-header">
      <span class="mini-map-title">导航</span>
      <button @click="toggleVisibility" class="mini-map-toggle">
        <span class="toggle-icon">{{ visible ? '−' : '+' }}</span>
      </button>
    </div>
    <div class="mini-map-viewport" ref="viewport">
      <!-- Canvas representation -->
      <div 
        class="mini-map-canvas"
        :style="{ 
          width: canvasWidth + 'px', 
          height: canvasHeight + 'px',
          transform: `scale(${scale})`
        }"
      >
        <!-- Task nodes in minimap -->
        <div
          v-for="task in tasks"
          :key="task.id"
          :class="['mini-node', { 'mini-selected': selectedTaskId === task.id }]"
          :style="getMiniNodeStyle(task)"
          @click="focusOnTask(task.id)"
        >
          <div class="mini-node-dot" :class="`priority-${task.urgency}`"></div>
        </div>
      </div>
      
      <!-- Current viewport indicator -->
      <div 
        class="viewport-indicator"
        :style="getViewportIndicatorStyle()"
        @mousedown="startViewportDrag"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { Task } from '@/stores/tasks'

interface Props {
  tasks: Task[]
  taskPositions: { [key: number]: { x: number; y: number } }
  canvasWidth: number
  canvasHeight: number
  viewportX?: number
  viewportY?: number
  viewportWidth?: number
  viewportHeight?: number
  selectedTaskId?: number | null
}

const props = withDefaults(defineProps<Props>(), {
  viewportX: 0,
  viewportY: 0,
  viewportWidth: 1200,
  viewportHeight: 800,
  selectedTaskId: null
})

const emit = defineEmits<{
  focusTask: [taskId: number]
  moveViewport: [x: number, y: number]
}>()

const visible = ref(true)
const viewport = ref<HTMLElement>()

// Mini-map dimensions
const MINIMAP_WIDTH = 160
const MINIMAP_HEIGHT = 120

// Calculate scale to fit canvas in minimap
const scale = computed(() => {
  const scaleX = MINIMAP_WIDTH / props.canvasWidth
  const scaleY = MINIMAP_HEIGHT / props.canvasHeight
  // 确保整个画布能在minimap中显示，为6000x6000画布调整缩放
  return Math.min(scaleX, scaleY) // 移除最大值限制，让它自动适应新的画布尺寸
})

const canvasWidth = computed(() => props.canvasWidth * scale.value)
const canvasHeight = computed(() => props.canvasHeight * scale.value)

function getMiniNodeStyle(task: Task) {
  const position = props.taskPositions[task.id]
  if (!position) return { display: 'none' }
  
  return {
    left: `${position.x * scale.value}px`,
    top: `${position.y * scale.value}px`,
  }
}

function getViewportIndicatorStyle() {
  const x = props.viewportX * scale.value
  const y = props.viewportY * scale.value
  const width = Math.min(props.viewportWidth * scale.value, canvasWidth.value)
  const height = Math.min(props.viewportHeight * scale.value, canvasHeight.value)
  
  return {
    left: `${Math.max(0, x)}px`,
    top: `${Math.max(0, y)}px`,
    width: `${width}px`,
    height: `${height}px`,
  }
}

function toggleVisibility() {
  visible.value = !visible.value
}

function focusOnTask(taskId: number) {
  emit('focusTask', taskId)
}

// Viewport dragging
let isDragging = false

function startViewportDrag(event: MouseEvent) {
  event.preventDefault()
  isDragging = true
  
  document.addEventListener('mousemove', handleViewportDrag)
  document.addEventListener('mouseup', stopViewportDrag)
}

function handleViewportDrag(event: MouseEvent) {
  if (!isDragging || !viewport.value) return
  
  const rect = viewport.value.getBoundingClientRect()
  const x = (event.clientX - rect.left) / scale.value
  const y = (event.clientY - rect.top) / scale.value
  
  emit('moveViewport', x, y)
}

function stopViewportDrag() {
  isDragging = false
  document.removeEventListener('mousemove', handleViewportDrag)
  document.removeEventListener('mouseup', stopViewportDrag)
}

// Handle clicking on minimap to move viewport
function handleMinimapClick(event: MouseEvent) {
  if (!viewport.value || isDragging) return
  
  const rect = viewport.value.getBoundingClientRect()
  const x = (event.clientX - rect.left) / scale.value
  const y = (event.clientY - rect.top) / scale.value
  
  emit('moveViewport', x - props.viewportWidth / 2, y - props.viewportHeight / 2)
}

onMounted(() => {
  if (viewport.value) {
    viewport.value.addEventListener('click', handleMinimapClick)
  }
})
</script>

<style scoped>
.mini-map {
  position: fixed;
  bottom: 20px;
  right: 200px;
  width: 180px;
  background: var(--panel-bg);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(8px);
  z-index: 1000;
  overflow: hidden;
  transition: all 0.3s ease;
}

.mini-map:hover {
  box-shadow: var(--shadow-xl);
  border-color: var(--primary);
}

.mini-map-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border-subtle);
}

.mini-map-title {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
}

.mini-map-toggle {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
  transition: all 0.2s ease;
}

.mini-map-toggle:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.toggle-icon {
  font-size: 12px;
  font-weight: bold;
}

.mini-map-viewport {
  position: relative;
  width: 160px;
  height: 120px;
  overflow: hidden;
  cursor: pointer;
  background: var(--bg-base);
  /* 添加网格背景，显示画布范围 */
  background-image: 
    linear-gradient(rgba(0, 0, 0, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 0, 0, 0.05) 1px, transparent 1px);
  background-size: 10px 10px;
}

.mini-map-canvas {
  position: relative;
  transform-origin: top left;
  /* 添加边框显示画布边界 */
  border: 1px dashed rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.02);
}

.mini-node {
  position: absolute;
  width: 8px;
  height: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mini-node:hover {
  transform: scale(1.5);
  z-index: 10;
}

.mini-node.mini-selected {
  transform: scale(1.3);
  z-index: 10;
}

.mini-node-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  border: 1px solid var(--card-bg);
  transition: all 0.2s ease;
}

.mini-node-dot.priority-0 { background-color: var(--danger); }
.mini-node-dot.priority-1 { background-color: var(--warning); }
.mini-node-dot.priority-2 { background-color: var(--info); }
.mini-node-dot.priority-3 { background-color: var(--success); }
.mini-node-dot.priority-4 { background-color: var(--primary); }

.mini-node:hover .mini-node-dot {
  border-width: 2px;
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.3);
}

.viewport-indicator {
  position: absolute;
  border: 2px solid var(--primary);
  background: rgba(37, 99, 235, 0.1);
  cursor: move;
  min-width: 10px;
  min-height: 10px;
  pointer-events: auto;
  transition: all 0.1s ease;
}

.viewport-indicator:hover {
  border-color: var(--primary-hover);
  background: rgba(37, 99, 235, 0.2);
}

.viewport-indicator:active {
  border-color: var(--primary-hover);
  background: rgba(37, 99, 235, 0.3);
}

/* Animation for showing/hiding */
.mini-map.hidden {
  transform: translateX(100%);
  opacity: 0;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .mini-map {
    bottom: 10px;
    right: 100px;  /* 在移动设备上也要避免与FAB重叠 */
    width: 140px;
  }
  
  .mini-map-viewport {
    width: 120px;
    height: 90px;
  }
}
</style>