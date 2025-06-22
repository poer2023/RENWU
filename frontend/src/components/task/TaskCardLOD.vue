<template>
  <div 
    :class="['task-card-lod', `lod-${lodLevel}`, { 'selected': isSelected }]"
    :style="cardStyle"
    @click="$emit('select', task)"
    @dblclick="$emit('openDetails', task, { x: 0, y: 0 })"
  >
    <!-- LOD 0: 完整详细视图 (距离最近) -->
    <TaskCard
      v-if="lodLevel === 0"
      :task="task"
      :is-selected="isSelected"
      @select="$emit('select', $event)"
      @openDetails="$emit('openDetails', $event, { x: 0, y: 0 })"
      @startConnection="$emit('startConnection', $event)"
      @getTaskPosition="$emit('getTaskPosition', $event)"
      @subtasksCreated="$emit('subtasksCreated', $event)"
    />
    
    <!-- LOD 1: 简化视图 (中等距离) -->
    <div v-else-if="lodLevel === 1" class="lod-simplified">
      <div class="task-header">
        <div class="task-icon">{{ getTaskIcon(task.urgency) }}</div>
        <div class="task-title">{{ task.title }}</div>
      </div>
      <div class="task-module" :style="{ backgroundColor: moduleColor }">
        {{ moduleName }}
      </div>
    </div>
    
    <!-- LOD 2: 最小视图 (远距离) -->
    <div v-else-if="lodLevel === 2" class="lod-minimal">
      <div class="task-dot" :class="`priority-${task.urgency}`">
        {{ getTaskIcon(task.urgency) }}
      </div>
    </div>
    
    <!-- LOD 3+: 点状视图 (极远距离) -->
    <div v-else class="lod-dot">
      <div class="task-point" :class="`priority-${task.urgency}`"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTaskStore, type Task } from '@/stores/tasks'
import TaskCard from '../TaskCard.vue'

interface Props {
  task: Task
  lodLevel: number
  distance: number
  isSelected?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSelected: false
})

const emit = defineEmits<{
  select: [task: Task]
  openDetails: [task: Task, position: { x: number, y: number }]
  startConnection: [fromTaskId: number, event: MouseEvent]
  getTaskPosition: [taskId: number]
  subtasksCreated: [data: { parentTask: Task, subtasks: Task[] }]
}>()

const taskStore = useTaskStore()

// 计算模块信息
const moduleName = computed(() => taskStore.getModuleName(props.task.module_id))
const moduleColor = computed(() => taskStore.getModuleColor(props.task.module_id))

// 获取任务图标
function getTaskIcon(urgency: number): string {
  const icons = {
    0: '🚨', // 紧急
    1: '⚡', // 重要
    2: '📝', // 正常
    3: '📋', // 低
    4: '💭'  // 可选
  }
  return icons[urgency as keyof typeof icons] || '📝'
}

// 根据LOD级别和距离动态计算样式
const cardStyle = computed(() => {
  const baseSize = 240 // 基础尺寸
  let scale = 1
  let opacity = 1
  
  switch (props.lodLevel) {
    case 0: // 完整视图
      scale = 1
      opacity = 1
      break
    case 1: // 简化视图
      scale = 0.8
      opacity = 0.95
      break
    case 2: // 最小视图
      scale = 0.5
      opacity = 0.8
      break
    default: // 点状视图
      scale = 0.3
      opacity = 0.6
      break
  }
  
  // 距离衰减
  const maxDistance = 10000
  const distanceFactor = Math.max(0.3, 1 - (props.distance / maxDistance))
  opacity *= distanceFactor
  
  return {
    transform: `scale(${scale})`,
    opacity,
    transformOrigin: 'center center',
    transition: props.lodLevel <= 1 ? 'all 0.3s ease' : 'none' // 远距离时禁用动画
  }
})
</script>

<style scoped>
.task-card-lod {
  position: relative;
  will-change: transform, opacity;
  contain: layout;
  backface-visibility: hidden;
}

/* LOD 1: 简化视图 */
.lod-simplified {
  width: 200px;
  height: 80px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s ease;
}

.lod-simplified:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.task-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.task-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.task-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.task-module {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 6px;
  color: white;
  text-align: center;
  font-weight: 500;
}

/* LOD 2: 最小视图 */
.lod-minimal {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.task-dot {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.task-dot:hover {
  transform: scale(1.1);
}

.task-dot.priority-0 { background: linear-gradient(135deg, #ff4d4f, #cf1322); }
.task-dot.priority-1 { background: linear-gradient(135deg, #fa8c16, #d46b08); }
.task-dot.priority-2 { background: linear-gradient(135deg, #1890ff, #096dd9); }
.task-dot.priority-3 { background: linear-gradient(135deg, #52c41a, #389e0d); }
.task-dot.priority-4 { background: linear-gradient(135deg, #722ed1, #531dab); }

/* LOD 3+: 点状视图 */
.lod-dot {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.task-point {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  cursor: pointer;
  transition: none; /* 禁用动画提升性能 */
}

.task-point.priority-0 { background: #ff4d4f; }
.task-point.priority-1 { background: #fa8c16; }
.task-point.priority-2 { background: #1890ff; }
.task-point.priority-3 { background: #52c41a; }
.task-point.priority-4 { background: #722ed1; }

/* 选中状态 */
.task-card-lod.selected {
  z-index: 10;
}

.task-card-lod.selected .lod-simplified {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3);
}

.task-card-lod.selected .task-dot {
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.5);
}

.task-card-lod.selected .task-point {
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.5);
  transform: scale(1.5);
}

/* 性能优化：远距离时移除复杂样式 */
.lod-3, .lod-4, .lod-5 {
  animation: none;
  transition: none;
  will-change: auto;
}
</style>