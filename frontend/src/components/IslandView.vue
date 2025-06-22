<template>
  <div v-if="enabled && islands.length > 0" class="island-headers">
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
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { type Task } from '@/stores/tasks'

interface Island {
  id: string
  name: string
  tasks: Task[]
  keywords?: string[]
  collapsed?: boolean
  color?: string
}

interface Props {
  enabled: boolean
  islands: Island[]
  containerWidth?: number
  containerHeight?: number
  taskPositions: { [key: number]: { x: number; y: number } }
}

const props = defineProps<Props>()

const emit = defineEmits<{
  toggleIsland: [island: Island]
  arrangeTasksInIslands: []
}>()

// 获取岛屿头部样式
function getIslandHeaderStyle(island: Island, index: number) {
  if (!props.containerWidth || !props.containerHeight) return {}
  
  const islandsCount = props.islands.length
  const cols = Math.ceil(Math.sqrt(islandsCount))
  const rows = Math.ceil(islandsCount / cols)
  
  const islandWidth = props.containerWidth / cols
  const islandHeight = props.containerHeight / rows
  const padding = 20
  
  const row = Math.floor(index / cols)
  const col = index % cols
  
  const islandX = col * islandWidth + padding
  const islandY = row * islandHeight + padding
  
  return {
    position: 'absolute' as const,
    left: `${islandX}px`,
    top: `${islandY}px`,
    width: `${islandWidth - 2 * padding}px`,
    backgroundColor: island.color,
    borderColor: island.color
  }
}

// 切换岛屿折叠状态
function toggleIsland(island: Island) {
  island.collapsed = !island.collapsed
  
  // 隐藏/显示该岛屿中的任务
  island.tasks.forEach((task: Task) => {
    const element = document.querySelector(`[data-task-id="${task.id}"]`) as HTMLElement
    if (element) {
      if (island.collapsed) {
        element.style.display = 'none'
      } else {
        element.style.display = 'block'
      }
    }
  })
  
  emit('toggleIsland', island)
}

// 排列岛屿中的任务
function arrangeTasksInIslands() {
  if (!props.containerWidth || !props.containerHeight || props.islands.length === 0) return
  
  const islandsCount = props.islands.length
  const cols = Math.ceil(Math.sqrt(islandsCount))
  const rows = Math.ceil(islandsCount / cols)
  
  const islandWidth = props.containerWidth / cols
  const islandHeight = props.containerHeight / rows
  const padding = 20
  
  // 批量计算所有位置
  const newPositions: { [key: number]: { x: number; y: number } } = {}
  
  props.islands.forEach((island, index) => {
    const row = Math.floor(index / cols)
    const col = index % cols
    
    const islandX = col * islandWidth + padding
    const islandY = row * islandHeight + padding
    const availableWidth = islandWidth - 2 * padding
    const availableHeight = islandHeight - 2 * padding
    
    // 排列该岛屿中的任务
    arrangeTasksInIsland(island.tasks, islandX, islandY, availableWidth, availableHeight, newPositions)
  })
  
  // 触发事件，让父组件更新任务位置
  emit('arrangeTasksInIslands')
  
  return newPositions
}

// 在单个岛屿中排列任务
function arrangeTasksInIsland(
  tasks: Task[], 
  startX: number, 
  startY: number, 
  width: number, 
  height: number, 
  newPositions: { [key: number]: { x: number; y: number } }
) {
  if (!tasks || tasks.length === 0) return
  
  const taskWidth = 200
  const taskHeight = 120
  const spacing = 10
  
  const cols = Math.floor(width / (taskWidth + spacing))
  
  tasks.forEach((task, index) => {
    const row = Math.floor(index / cols)
    const col = index % cols
    
    const x = startX + col * (taskWidth + spacing)
    const y = startY + row * (taskHeight + spacing) + 30 // 为岛屿标题预留空间
    
    newPositions[task.id] = { x, y }
  })
}

// 查找任务所在的岛屿
function findTargetIsland(clientX: number, clientY: number) {
  if (!props.containerWidth || !props.containerHeight || props.islands.length === 0) return null
  
  // 这里需要获取容器的实际位置，可能需要从父组件传入
  const relativeX = clientX
  const relativeY = clientY
  
  const islandsCount = props.islands.length
  const cols = Math.ceil(Math.sqrt(islandsCount))
  const rows = Math.ceil(islandsCount / cols)
  
  const islandWidth = props.containerWidth / cols
  const islandHeight = props.containerHeight / rows
  const padding = 20
  
  for (let index = 0; index < props.islands.length; index++) {
    const row = Math.floor(index / cols)
    const col = index % cols
    
    const islandX = col * islandWidth + padding
    const islandY = row * islandHeight + padding
    const islandRight = islandX + islandWidth - 2 * padding
    const islandBottom = islandY + islandHeight - 2 * padding
    
    if (relativeX >= islandX && relativeX <= islandRight &&
        relativeY >= islandY && relativeY <= islandBottom) {
      return props.islands[index]
    }
  }
  
  return null
}

// 暴露方法给父组件
defineExpose({
  arrangeTasksInIslands,
  findTargetIsland
})
</script>

<style scoped>
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
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid rgba(102, 126, 234, 0.3);
  border-radius: 16px;
  padding: 16px 20px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 4px 16px rgba(102, 126, 234, 0.1);
  cursor: pointer;
  pointer-events: auto;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  backdrop-filter: blur(20px);
  max-height: 120px;
  overflow: hidden;
  color: #1a202c;
  animation: islandSlideIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  border-bottom: 4px solid rgba(102, 126, 234, 0.6);
}

@keyframes islandSlideIn {
  from {
    opacity: 0;
    transform: translateY(-30px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.island-header:hover {
  transform: translateY(-6px) scale(1.03);
  box-shadow: 
    0 16px 48px rgba(0, 0, 0, 0.15), 
    0 8px 24px rgba(102, 126, 234, 0.2);
  border-color: rgba(102, 126, 234, 0.6);
  background: rgba(255, 255, 255, 0.98);
  border-bottom-color: rgba(102, 126, 234, 0.8);
}

.island-header:active {
  transform: translateY(-3px) scale(1.01);
  transition: all 0.2s ease;
}

.island-header.collapsed {
  opacity: 0.6;
  transform: scale(0.95);
  filter: grayscale(0.3);
}

.island-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 16px;
  margin-bottom: 8px;
  color: #1a202c;
}

.island-icon {
  font-size: 20px;
  animation: islandIconFloat 3s ease-in-out infinite;
}

@keyframes islandIconFloat {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-2px);
  }
}

.island-name {
  color: #1a202c;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.island-count {
  color: rgba(107, 114, 128, 0.8);
  font-size: 14px;
  font-weight: 500;
  background: rgba(102, 126, 234, 0.1);
  padding: 2px 8px;
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.island-keywords {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  max-height: 60px;
  overflow: hidden;
}

.keyword-tag {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  color: rgba(102, 126, 234, 0.8);
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid rgba(102, 126, 234, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: keywordFadeIn 0.4s ease-out;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

@keyframes keywordFadeIn {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.8);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.island-header:hover .keyword-tag {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
  color: rgba(102, 126, 234, 1);
  transform: translateY(-2px) scale(1.05);
  border-color: rgba(102, 126, 234, 0.4);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
  .island-header {
    background: rgba(31, 41, 55, 0.95);
    border: 2px solid rgba(102, 126, 234, 0.4);
    color: #f9fafb;
  }
  
  .island-header:hover {
    background: rgba(31, 41, 55, 0.98);
    border-color: rgba(102, 126, 234, 0.6);
  }
  
  .island-name {
    color: #f9fafb;
  }
  
  .island-count {
    color: rgba(156, 163, 175, 0.8);
    background: rgba(102, 126, 234, 0.2);
    border: 1px solid rgba(102, 126, 234, 0.3);
  }
  
  .keyword-tag {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
    color: rgba(102, 126, 234, 0.9);
    border: 1px solid rgba(102, 126, 234, 0.3);
  }
}
</style> 