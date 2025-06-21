<template>
  <svg
    class="connections-overlay"
    :width="canvasWidth"
    :height="canvasHeight"
    style="position: absolute; top: 0; left: 0; pointer-events: none; z-index: 1;"
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
      <path
        :d="getConnectionPath(connection)"
        :stroke="getConnectionColor(connection)"
        stroke-width="2"
        fill="none"
        :class="['connection-line', getConnectionClass(connection)]"
        marker-end="url(#arrowhead)"
        @click="handleConnectionClick(connection)"
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
import { ref, computed, watch } from 'vue'
import type { TaskDependency } from '@/stores/tasks'

interface Props {
  connections: TaskDependency[]
  taskPositions: { [key: number]: { x: number; y: number } }
  canvasWidth: number
  canvasHeight: number
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
}>()

// Constants for task card dimensions (should match TaskCard component)
const TASK_WIDTH = 240
const TASK_HEIGHT = 120

// Animation state
const animatedConnections = computed(() => {
  // Only animate active connections, not all of them for performance
  return props.connections.filter(conn => shouldAnimateConnection(conn)).slice(0, 5)
})

// Calculate connection paths
function getConnectionPath(connection: TaskDependency): string {
  const fromPos = props.taskPositions[connection.from_task_id]
  const toPos = props.taskPositions[connection.to_task_id]
  
  if (!fromPos || !toPos) return ''
  
  // Calculate connection points (from center-right to center-left)
  const fromX = fromPos.x + TASK_WIDTH
  const fromY = fromPos.y + TASK_HEIGHT / 2
  const toX = toPos.x
  const toY = toPos.y + TASK_HEIGHT / 2
  
  return createCurvedPath(fromX, fromY, toX, toY)
}

function createCurvedPath(x1: number, y1: number, x2: number, y2: number): string {
  return createBezierPath(x1, y1, x2, y2)
}

function getArrowHead(connection: TaskDependency): string {
  const toPos = props.taskPositions[connection.to_task_id]
  if (!toPos) return ''
  
  const x = toPos.x
  const y = toPos.y + TASK_HEIGHT / 2
  
  // Arrow pointing right (towards the task)
  const arrowSize = 8
  return `${x},${y} ${x-arrowSize},${y-arrowSize/2} ${x-arrowSize},${y+arrowSize/2}`
}

// Preview connection for dragging
const previewConnectionPath = computed(() => {
  if (!props.previewConnection) return ''
  
  const fromPos = props.taskPositions[props.previewConnection.fromTaskId]
  if (!fromPos) return ''
  
  const fromX = fromPos.x + TASK_WIDTH
  const fromY = fromPos.y + TASK_HEIGHT / 2
  const toX = props.previewConnection.toX
  const toY = props.previewConnection.toY
  
  return createBezierPath(fromX, fromY, toX, toY)
})

// Enhanced bezier curve calculation
function createBezierPath(x1: number, y1: number, x2: number, y2: number): string {
  const dx = x2 - x1
  const dy = y2 - y1
  
  // Dynamic control points based on distance and direction
  const distance = Math.sqrt(dx * dx + dy * dy)
  const controlDistance = Math.min(distance * 0.5, 100)
  
  let cp1x = x1 + controlDistance
  let cp1y = y1
  let cp2x = x2 - controlDistance
  let cp2y = y2
  
  // Adjust for vertical connections
  if (Math.abs(dy) > Math.abs(dx)) {
    cp1x = x1 + Math.sign(dx) * 20
    cp1y = y1 + dy * 0.3
    cp2x = x2 - Math.sign(dx) * 20
    cp2y = y2 - dy * 0.3
  }
  
  return `M ${x1} ${y1} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${x2} ${y2}`
}

// Connection styling
function getConnectionColor(connection: TaskDependency): string {
  // You can add logic here based on connection type or status
  return 'var(--primary)'
}

function getConnectionClass(connection: TaskDependency): string {
  // Add classes based on connection properties
  return 'dependency'
}

// Animation helpers
function shouldAnimateConnection(connection: TaskDependency): boolean {
  // Only animate active/important connections
  return true // For now, animate all connections
}

function getFlowDuration(connection: TaskDependency): number {
  // Vary animation speed based on connection properties
  return 2 + Math.random() * 2 // 2-4 seconds
}

// Event handlers
function handleConnectionClick(connection: TaskDependency) {
  emit('connectionClick', connection)
}

function handleConnectionHover(connection: TaskDependency, isHover: boolean) {
  emit('connectionHover', connection, isHover)
}
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

/* Connection Lines */
.connection-line {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.connection-line:hover {
  opacity: 1;
  stroke-width: 3;
  filter: drop-shadow(0 0 8px rgba(37, 99, 235, 0.3));
}

/* Connection Shadows */
.connection-shadows {
  opacity: 0.8;
}

/* Preview Connection */
.preview-connection {
  pointer-events: none;
}

.preview-line {
  stroke-linecap: round;
  stroke-linejoin: round;
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