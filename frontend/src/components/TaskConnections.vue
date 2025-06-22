<template>
  <svg
    ref="svgElement"
    class="connections-overlay"
    :width="canvasWidth"
    :height="canvasHeight"
    style="position: absolute; top: 0; left: 0; pointer-events: none; z-index: 1;"
    :viewBox="`0 0 ${canvasWidth} ${canvasHeight}`"
    preserveAspectRatio="xMidYMid meet"
  >
    <!-- SVG Definitions -->
    <defs>
      <!-- Arrow marker -->
      <marker
        id="arrowhead"
        markerWidth="10"
        markerHeight="7"
        refX="9"
        refY="3.5"
        orient="auto"
      >
        <polygon
          points="0 0, 10 3.5, 0 7"
          fill="var(--primary)"
        />
      </marker>
      
      <!-- Glow filter -->
      <filter id="glow">
        <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
        <feMerge>
          <feMergeNode in="coloredBlur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>

    <!-- Connection shadows (for depth) -->
    <g class="connection-shadows">
      <path
        v-for="connection in connections"
        :key="`shadow-${connection.from_task_id}-${connection.to_task_id}`"
        :d="getConnectionPath(connection)"
        stroke="rgba(0,0,0,0.1)"
        stroke-width="4"
        fill="none"
        transform="translate(2,2)"
      />
    </g>

    <!-- Main connections -->
    <g v-for="connection in connections" :key="`${connection.from_task_id}-${connection.to_task_id}`" class="connection-group">
      <!-- 连线主体 -->
      <path
        :d="getConnectionPath(connection)"
        :stroke="getConnectionColor(connection)"
        stroke-width="2"
        fill="none"
        :class="['connection-line', getConnectionClass(connection)]"
        marker-end="url(#arrowhead)"
        style="pointer-events: stroke; cursor: pointer;"
        @click="handleConnectionClick(connection)"
        @dblclick="handleConnectionDoubleClick(connection)"
        @mouseenter="handleConnectionHover(connection, true)"
        @mouseleave="handleConnectionHover(connection, false)"
      />
    </g>

    <!-- Preview connection while dragging -->
    <g v-if="previewConnection" class="preview-connection">
      <path
        :d="previewConnectionPath"
        stroke="var(--primary)"
        stroke-width="2"
        fill="none"
        stroke-dasharray="4,4"
        opacity="0.8"
        class="preview-line"
      >
        <animate
          attributeName="stroke-dashoffset"
          values="0;8"
          dur="0.5s"
          repeatCount="indefinite"
        />
      </path>
    </g>

    <!-- Connection flow animation dots -->
    <g v-for="connection in animatedConnections" :key="`flow-${connection.from_task_id}-${connection.to_task_id}`">
      <circle
        r="3"
        fill="var(--primary)"
        opacity="0.8"
      >
        <animateMotion
          :dur="getFlowDuration(connection) + 's'"
          repeatCount="indefinite"
        >
          <mpath :href="`#path-${connection.from_task_id}-${connection.to_task_id}`"/>
        </animateMotion>
      </circle>
    </g>
  </svg>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import type { TaskDependency } from '@/stores/tasks'

// 防抖工具函数
function debounce<T extends (...args: any[]) => any>(func: T, wait: number): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

interface Props {
  connections: TaskDependency[]
  taskPositions: { [key: number]: { x: number; y: number } }
  taskDimensions: { [key: number]: { width: number; height: number } }
  canvasWidth: number
  canvasHeight: number
  viewport: { x: number; y: number; scale: number }
  previewConnection?: {
    fromTaskId: number
    toX: number
    toY: number
  } | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  connectionClick: [connection: TaskDependency]
  connectionHover: [connection: TaskDependency, isHover: boolean]
  connectionDoubleClick: [connection: TaskDependency]
}>()

const svgElement = ref<SVGElement>()

// 默认任务尺寸常量，用作备选值
const DEFAULT_TASK_WIDTH = 240
const DEFAULT_TASK_HEIGHT = 120

// 坐标缓存，提高性能
const coordinateCache = ref<Map<string, { fromX: number; fromY: number; toX: number; toY: number }>>(new Map())
// 路径缓存，避免重复计算
const pathCache = ref<Map<string, string>>(new Map())

// 防抖清除缓存 - 优化连线流畅度
const debouncedClearCache = debounce(() => {
  coordinateCache.value.clear()
  pathCache.value.clear()
}, 16) // 降低到16ms，约60fps

// 监听属性变化，清除缓存
watch(() => [props.taskPositions, props.taskDimensions, props.viewport], () => {
  debouncedClearCache()
}, { deep: true, flush: 'post' })

// 性能监控 (非响应式，避免递归更新)
let performanceMetrics = {
  pathCalculationTime: 0,
  cacheHitRate: 0,
  totalCalculations: 0,
  cacheHits: 0
}

// 重置性能指标
function resetPerformanceMetrics() {
  performanceMetrics = {
    pathCalculationTime: 0,
    cacheHitRate: 0,
    totalCalculations: 0,
    cacheHits: 0
  }
}

// 更新缓存命中率
function updateCacheHitRate() {
  performanceMetrics.cacheHitRate = performanceMetrics.totalCalculations > 0 
    ? (performanceMetrics.cacheHits / performanceMetrics.totalCalculations) * 100 
    : 0
}

// Animation state - 进一步优化性能
const animatedConnections = computed(() => {
  // 只动画化可见的连接，提高性能
  const visibleConnections = props.connections.filter(conn => {
    const fromPos = props.taskPositions[conn.from_task_id]
    const toPos = props.taskPositions[conn.to_task_id]
    
    // 检查连接是否在视口范围内
    if (!fromPos || !toPos) return false
    
    const minX = Math.min(fromPos.x, toPos.x)
    const maxX = Math.max(fromPos.x, toPos.x)
    const minY = Math.min(fromPos.y, toPos.y)
    const maxY = Math.max(fromPos.y, toPos.y)
    
    // 简单的视口裁剪检查
    const margin = 100
    return !(maxX < -margin || minX > props.canvasWidth + margin ||
             maxY < -margin || minY > props.canvasHeight + margin)
  })
  
  // 限制同时动画的连接数量
  return visibleConnections.filter(conn => shouldAnimateConnection(conn)).slice(0, 3)
})

// 获取任务的实际尺寸
function getTaskDimensions(taskId: number): { width: number; height: number } {
  return props.taskDimensions[taskId] || { width: DEFAULT_TASK_WIDTH, height: DEFAULT_TASK_HEIGHT }
}

// Calculate connection paths with caching
function getConnectionPath(connection: TaskDependency): string {
  try {
    const startTime = performance.now()
    performanceMetrics.totalCalculations++
    
    // 生成缓存键，基于任务ID和位置信息
    const fromPos = props.taskPositions[connection.from_task_id]
    const toPos = props.taskPositions[connection.to_task_id]
    const fromDim = props.taskDimensions[connection.from_task_id]
    const toDim = props.taskDimensions[connection.to_task_id]
    
    // Safety check for required positions
    if (!fromPos || !toPos) {
      console.warn('Missing task positions for connection:', connection)
      return ''
    }
    
    const cacheKey = `${connection.from_task_id}-${connection.to_task_id}-${fromPos?.x || 0}-${fromPos?.y || 0}-${toPos?.x || 0}-${toPos?.y || 0}-${fromDim?.width || 240}-${fromDim?.height || 120}-${toDim?.width || 240}-${toDim?.height || 120}`
    
    // 检查路径缓存
    if (pathCache.value.has(cacheKey)) {
      performanceMetrics.cacheHits++
      updateCacheHitRate()
      return pathCache.value.get(cacheKey)!
    }
    
    // 获取实际的任务尺寸
    const fromDimensions = getTaskDimensions(connection.from_task_id)
    const toDimensions = getTaskDimensions(connection.to_task_id)
    
    // 使用智能连接点计算
    const connectionPoints = getBestConnectionPoints(
      fromPos.x, fromPos.y, 
      toPos.x, toPos.y,
      fromDimensions, toDimensions
    )
    
    const path = createBezierPath(
      connectionPoints.fromX, connectionPoints.fromY,
      connectionPoints.toX, connectionPoints.toY
    )
    
    // 缓存路径
    pathCache.value.set(cacheKey, path)
    
    // 更新性能指标
    const endTime = performance.now()
    performanceMetrics.pathCalculationTime += endTime - startTime
    updateCacheHitRate()
    
    return path
  } catch (error) {
    console.error('Error calculating connection path:', error)
    return ''
  }
}

// Preview connection for dragging - 使用固定连接点
const previewConnectionPath = computed(() => {
  if (!props.previewConnection) return ''
  
  const fromPos = props.taskPositions[props.previewConnection.fromTaskId]
  if (!fromPos) return ''
  
  // 获取源任务的实际尺寸
  const fromDimensions = getTaskDimensions(props.previewConnection.fromTaskId)
  
  // 将鼠标坐标转换为画布坐标系
  const mouseX = (props.previewConnection.toX - props.viewport.x) / props.viewport.scale
  const mouseY = (props.previewConnection.toY - props.viewport.y) / props.viewport.scale
  
  // 获取源任务的所有连接点
  const fromPorts = getCardConnectionPoints(fromPos.x, fromPos.y, fromDimensions)
  
  // 找到距离鼠标最近的连接点
  let closestDistance = Infinity
  let bestFromPort = fromPorts.right // 默认使用右侧连接点
  
  const portKeys = ['top', 'right', 'bottom', 'left'] as const
  for (const key of portKeys) {
    const port = fromPorts[key]
    const distance = Math.sqrt(
      Math.pow(mouseX - port.x, 2) + 
      Math.pow(mouseY - port.y, 2)
    )
    
    if (distance < closestDistance) {
      closestDistance = distance
      bestFromPort = port
    }
  }
  
  return createBezierPath(bestFromPort.x, bestFromPort.y, mouseX, mouseY)
})

// 获取任务卡片的四个边界连接点（顶部、右侧、底部、左侧中点）
function getCardConnectionPoints(x: number, y: number, dimensions: { width: number; height: number }) {
  const centerX = x + dimensions.width / 2
  const centerY = y + dimensions.height / 2
  
  return {
    top: { x: centerX, y: y },                              // 顶部中点
    right: { x: x + dimensions.width, y: centerY },         // 右侧中点
    bottom: { x: centerX, y: y + dimensions.height },       // 底部中点
    left: { x: x, y: centerY }                              // 左侧中点
  }
}

// 计算两点间最短距离并选择最佳连接点组合
function getBestConnectionPoints(x1: number, y1: number, x2: number, y2: number, fromDimensions: { width: number; height: number }, toDimensions: { width: number; height: number }) {
  const fromPorts = getCardConnectionPoints(x1, y1, fromDimensions)
  const toPorts = getCardConnectionPoints(x2, y2, toDimensions)
  
  let minDistance = Infinity
  let bestConnection = { fromX: 0, fromY: 0, toX: 0, toY: 0 }
  
  // 遍历所有连接点组合，找到最短距离
  const fromKeys = ['top', 'right', 'bottom', 'left'] as const
  const toKeys = ['top', 'right', 'bottom', 'left'] as const
  
  for (const fromKey of fromKeys) {
    for (const toKey of toKeys) {
      const fromPort = fromPorts[fromKey]
      const toPort = toPorts[toKey]
      
      // 避免同侧连接（例如两个右侧连接点相连）
      if (shouldAvoidConnection(fromKey, toKey)) continue
      
      const distance = Math.sqrt(
        Math.pow(toPort.x - fromPort.x, 2) + 
        Math.pow(toPort.y - fromPort.y, 2)
      )
      
      if (distance < minDistance) {
        minDistance = distance
        bestConnection = {
          fromX: fromPort.x,
          fromY: fromPort.y,
          toX: toPort.x,
          toY: toPort.y
        }
      }
    }
  }
  
  return bestConnection
}

// 避免不合理的连接组合
function shouldAvoidConnection(fromPort: string, toPort: string): boolean {
  // 避免对向连接点相连（比如左连左，右连右）会产生重叠
  const conflicts = [
    ['left', 'right'],
    ['right', 'left'],
    ['top', 'bottom'], 
    ['bottom', 'top']
  ]
  
  // 允许适当的对向连接，但要确保有最小距离
  return false
}

// 优化的Bezier曲线计算 - 更流畅的连线
function createBezierPath(x1: number, y1: number, x2: number, y2: number): string {
  const dx = x2 - x1
  const dy = y2 - y1
  const distance = Math.sqrt(dx * dx + dy * dy)
  
  // 根据连线类型和距离动态调整控制点
  const minControlDistance = 40
  const maxControlDistance = 120
  const baseControlDistance = Math.min(Math.max(distance * 0.3, minControlDistance), maxControlDistance)
  
  let cp1x, cp1y, cp2x, cp2y
  
  // 判断连接方向并设置控制点
  const isHorizontalDominant = Math.abs(dx) > Math.abs(dy)
  
  if (isHorizontalDominant) {
    // 水平主导连线 - 使用水平控制点
    const horizontalOffset = baseControlDistance * Math.sign(dx)
    cp1x = x1 + horizontalOffset
    cp1y = y1
    cp2x = x2 - horizontalOffset
    cp2y = y2
    
    // 如果起点和终点在垂直方向上差距较大，增加垂直偏移以产生更自然的弧度
    if (Math.abs(dy) > 60) {
      const verticalBias = dy * 0.2
      cp1y = y1 + verticalBias
      cp2y = y2 - verticalBias
    }
  } else {
    // 垂直主导连线 - 使用垂直控制点
    const verticalOffset = baseControlDistance * Math.sign(dy)
    cp1x = x1
    cp1y = y1 + verticalOffset
    cp2x = x2
    cp2y = y2 - verticalOffset
    
    // 如果起点和终点在水平方向上差距较大，增加水平偏移
    if (Math.abs(dx) > 60) {
      const horizontalBias = dx * 0.2
      cp1x = x1 + horizontalBias
      cp2x = x2 - horizontalBias
    }
  }
  
  // 短距离连线优化 - 减少弯曲度，让连线更直接
  if (distance < 80) {
    const factor = distance / 80
    cp1x = x1 + (cp1x - x1) * factor
    cp1y = y1 + (cp1y - y1) * factor
    cp2x = x2 + (cp2x - x2) * factor
    cp2y = y2 + (cp2y - y2) * factor
  }
  
  // 避免控制点过度偏移
  const maxOffset = distance * 0.6
  cp1x = Math.max(Math.min(cp1x, x1 + maxOffset), x1 - maxOffset)
  cp1y = Math.max(Math.min(cp1y, y1 + maxOffset), y1 - maxOffset)
  cp2x = Math.max(Math.min(cp2x, x2 + maxOffset), x2 - maxOffset)
  cp2y = Math.max(Math.min(cp2y, y2 + maxOffset), y2 - maxOffset)
  
  return `M ${x1.toFixed(1)} ${y1.toFixed(1)} C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${x2.toFixed(1)} ${y2.toFixed(1)}`
}

// Connection styling
function getConnectionColor(connection: TaskDependency): string {
  return 'var(--primary)'
}

function getConnectionClass(connection: TaskDependency): string {
  return 'dependency'
}

// Animation helpers
function shouldAnimateConnection(connection: TaskDependency): boolean {
  // 只为重要的连接添加动画，减少性能消耗
  return Math.random() > 0.7
}

function getFlowDuration(connection: TaskDependency): number {
  // 根据连接长度调整动画速度
  const fromPos = props.taskPositions[connection.from_task_id]
  const toPos = props.taskPositions[connection.to_task_id]
  
  if (!fromPos || !toPos) return 3
  
  const distance = Math.sqrt(
    Math.pow(toPos.x - fromPos.x, 2) + Math.pow(toPos.y - fromPos.y, 2)
  )
  
  // 距离越长，动画越慢
  return Math.max(2, Math.min(6, distance / 100))
}

// Event handlers
function handleConnectionClick(connection: TaskDependency) {
  emit('connectionClick', connection)
}

function handleConnectionHover(connection: TaskDependency, isHover: boolean) {
  emit('connectionHover', connection, isHover)
}

function handleConnectionDoubleClick(connection: TaskDependency) {
  emit('connectionDoubleClick', connection)
}

// 性能监控和调试工具
function logPerformanceMetrics() {
  console.log('TaskConnections Performance Metrics:', {
    avgCalculationTime: performanceMetrics.pathCalculationTime / Math.max(performanceMetrics.totalCalculations, 1),
    cacheHitRate: `${performanceMetrics.cacheHitRate.toFixed(2)}%`,
    totalCalculations: performanceMetrics.totalCalculations,
    cacheSize: pathCache.value.size,
    coordinateCacheSize: coordinateCache.value.size
  })
}

// 暴露调试方法
if (import.meta.env.DEV) {
  (window as any).taskConnectionsDebug = {
    getPerformanceMetrics: () => performanceMetrics,
    clearCache: () => {
      coordinateCache.value.clear()
      pathCache.value.clear()
    },
    logMetrics: logPerformanceMetrics,
    resetMetrics: resetPerformanceMetrics
  }
}

// 定期输出性能指标（仅在开发模式）
let performanceLogInterval: NodeJS.Timeout | null = null

onMounted(() => {
  if (import.meta.env.DEV) {
    performanceLogInterval = setInterval(logPerformanceMetrics, 10000) // 每10秒输出一次
  }
})

onUnmounted(() => {
  if (performanceLogInterval) {
    clearInterval(performanceLogInterval)
  }
})
</script>

<style scoped>
.connections-overlay {
  pointer-events: none;
  z-index: 1;
}

/* Connection Groups */
.connection-group {
  pointer-events: all;
  cursor: pointer;
}

/* Connection Lines - 优化流畅度 */
.connection-line {
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  opacity: 0.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2;
  fill: none;
  /* vector-effect: non-scaling-stroke; removed for consistent rendering */
}

.connection-line:hover,
.connection-line.connection-hovered {
  opacity: 1;
  stroke-width: 3;
  filter: drop-shadow(0 0 12px rgba(37, 99, 235, 0.4));
  transform: translateZ(0); /* 开启硬件加速 */
}

/* Connection Shadows */
.connection-shadows {
  opacity: 0.8;
}

/* Preview Connection - 增强流畅度 */
.preview-connection {
  pointer-events: none;
}

.preview-line {
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2;
  fill: none;
  /* vector-effect: non-scaling-stroke; removed for consistent rendering */
  will-change: d; /* 优化路径变化的性能 */
}

/* Different connection states */
.connection-line.dependency {
  stroke: var(--primary);
}

.connection-line.blocked {
  stroke: var(--danger);
  stroke-dasharray: 6,4;
  opacity: 0.8;
}

.connection-line.completed {
  stroke: var(--success);
  opacity: 0.5;
}

.connection-line.warning {
  stroke: var(--warning);
  opacity: 0.8;
}

/* Hover effects for different types */
.connection-line.dependency:hover {
  stroke: var(--primary-hover);
  filter: drop-shadow(0 0 12px rgba(37, 99, 235, 0.4));
}

.connection-line.blocked:hover {
  stroke: var(--danger);
  filter: drop-shadow(0 0 12px rgba(248, 113, 113, 0.4));
}

.connection-line.completed:hover {
  stroke: var(--success);
  filter: drop-shadow(0 0 12px rgba(52, 211, 153, 0.4));
}

/* Flow animation dots */
.flow-dot {
  filter: drop-shadow(0 0 4px rgba(37, 99, 235, 0.5));
}

/* SVG Markers */
marker polygon {
  transition: fill 0.2s ease;
}

.connection-group:hover marker polygon {
  fill: var(--primary-hover);
}

/* Animation keyframes */
@keyframes connection-draw {
  from {
    stroke-dasharray: 1000;
    stroke-dashoffset: 1000;
  }
  to {
    stroke-dasharray: 1000;
    stroke-dashoffset: 0;
  }
}

@keyframes pulse-glow {
  0%, 100% {
    filter: drop-shadow(0 0 4px rgba(37, 99, 235, 0.3));
  }
  50% {
    filter: drop-shadow(0 0 12px rgba(37, 99, 235, 0.6));
  }
}

/* Apply animations */
.connection-line.new {
  animation: connection-draw 0.8s ease-out;
}

.connection-line.active {
  animation: pulse-glow 2s ease-in-out infinite;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .connection-line {
    stroke-width: 1.5;
  }
  
  .connection-line:hover {
    stroke-width: 2.5;
  }
}
</style>