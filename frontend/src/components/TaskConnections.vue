<template>
  <svg
    class="connections-overlay"
    :width="canvasWidth"
    :height="canvasHeight"
    style="position: absolute; top: 0; left: 0; pointer-events: none; z-index: 1;"
  >
    <!-- Existing connections -->
    <g v-for="connection in connections" :key="`${connection.from_task_id}-${connection.to_task_id}`">
      <path
        :d="getConnectionPath(connection)"
        stroke="#666"
        stroke-width="2"
        fill="none"
        stroke-dasharray="5,5"
        opacity="0.7"
      />
      <!-- Arrow head -->
      <polygon
        :points="getArrowHead(connection)"
        fill="#666"
        opacity="0.7"
      />
    </g>

    <!-- Preview connection while dragging -->
    <g v-if="previewConnection">
      <path
        :d="previewConnection.path"
        stroke="#007bff"
        stroke-width="2"
        fill="none"
        stroke-dasharray="2,2"
        opacity="0.8"
      />
      <polygon
        :points="previewConnection.arrowHead"
        fill="#007bff"
        opacity="0.8"
      />
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

// Constants for task card dimensions (should match TaskCard component)
const TASK_WIDTH = 200
const TASK_HEIGHT = 120

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
  const dx = x2 - x1
  const dy = y2 - y1
  
  // Control points for curved path
  const controlOffset = Math.abs(dx) * 0.3
  const cp1x = x1 + controlOffset
  const cp1y = y1
  const cp2x = x2 - controlOffset
  const cp2y = y2
  
  return `M ${x1} ${y1} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${x2} ${y2}`
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
const previewConnection = computed(() => {
  if (!props.previewConnection) return null
  
  const fromPos = props.taskPositions[props.previewConnection.fromTaskId]
  if (!fromPos) return null
  
  const fromX = fromPos.x + TASK_WIDTH
  const fromY = fromPos.y + TASK_HEIGHT / 2
  const toX = props.previewConnection.toX
  const toY = props.previewConnection.toY
  
  const path = createCurvedPath(fromX, fromY, toX, toY)
  
  // Arrow head at cursor position
  const arrowSize = 8
  const arrowHead = `${toX},${toY} ${toX-arrowSize},${toY-arrowSize/2} ${toX-arrowSize},${toY+arrowSize/2}`
  
  return { path, arrowHead }
})
</script>

<style scoped>
.connections-overlay {
  pointer-events: none;
}
</style>