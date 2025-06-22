<template>
  <svg 
    :width="canvasWidth" 
    :height="canvasHeight"
    class="task-connections-lazy"
    style="position: absolute; top: 0; left: 0; pointer-events: none; z-index: 5;"
  >
    <!-- 只渲染可见的连线 -->
    <g v-for="connection in visibleConnections" :key="`${connection.from_task_id}-${connection.to_task_id}`">
      <!-- LOD 0-1: 完整连线 (近距离) -->
      <path
        v-if="connection.lodLevel <= 1"
        :d="connection.path"
        :class="['connection-path', `priority-${connection.priority}`, { 'animated': connection.animated }]"
        :stroke="connection.color"
        :stroke-width="connection.strokeWidth"
        stroke-dasharray="none"
        fill="none"
        style="pointer-events: stroke;"
        @dblclick="$emit('connectionDoubleClick', connection.original)"
      />
      
      <!-- LOD 2: 简化连线 (中距离) -->
      <line
        v-else-if="connection.lodLevel === 2"
        :x1="connection.fromX"
        :y1="connection.fromY"
        :x2="connection.toX"
        :y2="connection.toY"
        :stroke="connection.color"
        :stroke-width="Math.max(1, connection.strokeWidth * 0.5)"
        stroke-opacity="0.7"
        style="pointer-events: stroke;"
        @dblclick="$emit('connectionDoubleClick', connection.original)"
      />
      
      <!-- LOD 3+: 点状连线 (远距离) -->
      <line
        v-else
        :x1="connection.fromX"
        :y1="connection.fromY"
        :x2="connection.toX"
        :y2="connection.toY"
        :stroke="connection.color"
        stroke-width="1"
        stroke-opacity="0.4"
        stroke-dasharray="5,5"
        style="pointer-events: none;"
      />
    </g>

    <!-- 预览连线 (总是完整渲染) -->
    <path
      v-if="previewConnection"
      :d="getConnectionPath(previewConnection.from, previewConnection.to)"
      class="connection-preview"
      stroke="#667eea"
      stroke-width="3"
      stroke-dasharray="8,4"
      fill="none"
      opacity="0.8"
    >
      <animate
        attributeName="stroke-dashoffset"
        values="0;12;0"
        dur="1s"
        repeatCount="indefinite"
      />
    </path>
  </svg>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface TaskDependency {
  id?: number
  from_task_id: number
  to_task_id: number
  dependency_type: string
}

interface TaskPosition {
  x: number
  y: number
}

interface TaskDimension {
  width: number
  height: number
}

interface ViewportState {
  x: number
  y: number
  scale: number
}

interface ConnectionWithLOD {
  original: TaskDependency
  fromX: number
  fromY: number
  toX: number
  toY: number
  path: string
  color: string
  strokeWidth: number
  priority: number
  lodLevel: number
  distance: number
  animated: boolean
}

interface Props {
  connections: TaskDependency[]
  taskPositions: { [key: number]: TaskPosition }
  taskDimensions: { [key: number]: TaskDimension }
  canvasWidth: number
  canvasHeight: number
  viewport: ViewportState
  previewConnection?: { from: TaskPosition; to: TaskPosition } | null
  // 性能配置
  maxRenderConnections?: number
  viewportMargin?: number
  lodDistances?: number[]
}

const props = withDefaults(defineProps<Props>(), {
  maxRenderConnections: 200,
  viewportMargin: 1000,
  lodDistances: () => [1500, 3000, 6000]
})

const emit = defineEmits<{
  connectionDoubleClick: [connection: TaskDependency]
}>()

// 连线颜色配置
const connectionColors = {
  blocks: '#ef4444',      // 红色 - 阻塞
  subtask: '#10b981',     // 绿色 - 子任务
  related: '#6366f1',     // 紫色 - 相关
  default: '#64748b'      // 灰色 - 默认
}

// 计算视口边界
function getViewportBounds() {
  const scale = props.viewport.scale
  const margin = props.viewportMargin / scale
  
  const left = (-props.viewport.x) / scale - margin
  const top = (-props.viewport.y) / scale - margin
  const right = left + (window.innerWidth || 1920) / scale + margin * 2
  const bottom = top + (window.innerHeight || 1080) / scale + margin * 2
  
  return { left, top, right, bottom }
}

// 检查连线是否在视口内
function isConnectionVisible(fromPos: TaskPosition, toPos: TaskPosition): boolean {
  const bounds = getViewportBounds()
  
  // 连线的边界框
  const lineLeft = Math.min(fromPos.x, toPos.x)
  const lineTop = Math.min(fromPos.y, toPos.y)
  const lineRight = Math.max(fromPos.x, toPos.x)
  const lineBottom = Math.max(fromPos.y, toPos.y)
  
  // 检查是否与视口相交
  return !(lineRight < bounds.left || 
           lineLeft > bounds.right || 
           lineBottom < bounds.top || 
           lineTop > bounds.bottom)
}

// 计算连线与视口中心的距离
function getConnectionDistance(fromPos: TaskPosition, toPos: TaskPosition): number {
  // 连线中点
  const centerX = (fromPos.x + toPos.x) / 2
  const centerY = (fromPos.y + toPos.y) / 2
  
  // 视口中心
  const scale = props.viewport.scale
  const viewportCenterX = (-props.viewport.x + (window.innerWidth || 1920) / 2) / scale
  const viewportCenterY = (-props.viewport.y + (window.innerHeight || 1080) / 2) / scale
  
  const dx = centerX - viewportCenterX
  const dy = centerY - viewportCenterY
  return Math.sqrt(dx * dx + dy * dy)
}

// 计算LOD级别
function getLODLevel(distance: number): number {
  for (let i = 0; i < props.lodDistances.length; i++) {
    if (distance <= props.lodDistances[i]) {
      return i
    }
  }
  return props.lodDistances.length
}

// 获取任务中心位置
function getTaskCenter(taskId: number): TaskPosition {
  const pos = props.taskPositions[taskId]
  const dim = props.taskDimensions[taskId]
  
  if (!pos) return { x: 0, y: 0 }
  
  return {
    x: pos.x + (dim?.width || 240) / 2,
    y: pos.y + (dim?.height || 120) / 2
  }
}

// 生成连线路径
function getConnectionPath(from: TaskPosition, to: TaskPosition): string {
  const dx = to.x - from.x
  const dy = to.y - from.y
  const distance = Math.sqrt(dx * dx + dy * dy)
  
  // 控制点距离（曲线弯曲程度）
  const controlDistance = Math.min(distance * 0.5, 200)
  
  // 控制点（让连线有轻微的曲线）
  const midX = (from.x + to.x) / 2
  const midY = (from.y + to.y) / 2
  
  // 垂直方向的偏移
  const offsetX = -dy / distance * controlDistance * 0.3
  const offsetY = dx / distance * controlDistance * 0.3
  
  const cp1x = from.x + dx * 0.3 + offsetX
  const cp1y = from.y + dy * 0.3 + offsetY
  const cp2x = to.x - dx * 0.3 + offsetX
  const cp2y = to.y - dy * 0.3 + offsetY
  
  return `M ${from.x} ${from.y} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${to.x} ${to.y}`
}

// 获取连线优先级（用于颜色和粗细）
function getConnectionPriority(connection: TaskDependency): number {
  switch (connection.dependency_type) {
    case 'blocks': return 3     // 最高优先级
    case 'subtask': return 2    // 高优先级
    case 'related': return 1    // 中优先级
    default: return 0           // 默认优先级
  }
}

// 计算可见连线（带LOD）
const visibleConnections = computed<ConnectionWithLOD[]>(() => {
  const results: ConnectionWithLOD[] = []
  
  for (const connection of props.connections) {
    const fromPos = getTaskCenter(connection.from_task_id)
    const toPos = getTaskCenter(connection.to_task_id)
    
    // 检查可见性
    if (!isConnectionVisible(fromPos, toPos)) continue
    
    const distance = getConnectionDistance(fromPos, toPos)
    const lodLevel = getLODLevel(distance)
    const priority = getConnectionPriority(connection)
    
    // 根据LOD级别决定样式
    let strokeWidth = 2
    let animated = false
    
    switch (lodLevel) {
      case 0: // 近距离 - 完整效果
        strokeWidth = priority >= 2 ? 3 : 2
        animated = priority >= 3
        break
      case 1: // 中距离 - 简化效果  
        strokeWidth = priority >= 2 ? 2.5 : 1.5
        animated = false
        break
      case 2: // 远距离 - 最简效果
        strokeWidth = 1
        animated = false
        break
      default: // 极远距离 - 点线
        strokeWidth = 1
        animated = false
    }
    
    const color = connectionColors[connection.dependency_type as keyof typeof connectionColors] || connectionColors.default
    
    results.push({
      original: connection,
      fromX: fromPos.x,
      fromY: fromPos.y,
      toX: toPos.x,
      toY: toPos.y,
      path: getConnectionPath(fromPos, toPos),
      color,
      strokeWidth,
      priority,
      lodLevel,
      distance,
      animated
    })
  }
  
  // 按距离排序，优先渲染近的连线
  results.sort((a, b) => a.distance - b.distance)
  
  // 应用最大渲染数量限制
  return results.slice(0, props.maxRenderConnections)
})

// 性能监控
const performanceMetrics = computed(() => ({
  totalConnections: props.connections.length,
  visibleConnections: visibleConnections.value.length,
  renderRatio: props.connections.length > 0 ? 
    (visibleConnections.value.length / props.connections.length * 100).toFixed(1) : '0'
}))

// 暴露性能指标（可选）
defineExpose({
  performanceMetrics
})
</script>

<style scoped>
.task-connections-lazy {
  will-change: auto;
  contain: layout;
}

.connection-path {
  transition: stroke-width 0.3s ease, opacity 0.3s ease;
  cursor: pointer;
}

.connection-path:hover {
  stroke-width: 4 !important;
  opacity: 0.9;
}

.connection-path.priority-3 {
  filter: drop-shadow(0 0 4px rgba(239, 68, 68, 0.4));
}

.connection-path.priority-2 {
  filter: drop-shadow(0 0 2px rgba(16, 185, 129, 0.3));
}

.connection-path.animated {
  stroke-dasharray: 8,4;
  animation: connection-flow 2s linear infinite;
}

@keyframes connection-flow {
  from {
    stroke-dashoffset: 0;
  }
  to {
    stroke-dashoffset: 12;
  }
}

.connection-preview {
  will-change: stroke-dashoffset;
}

/* 性能优化：远距离连线不使用复杂样式 */
.connection-path[stroke-width="1"] {
  filter: none;
  animation: none;
  transition: none;
}
</style>