<template>
  <div class="timeline-view">
    <div class="timeline-header">
      <h2>📅 时间线视图</h2>
      <div class="timeline-controls">
        <el-button-group>
          <el-button 
            :type="timelineFilter === 'all' ? 'primary' : ''"
            @click="timelineFilter = 'all'"
            size="small"
          >
            全部
          </el-button>
          <el-button 
            :type="timelineFilter === 'pending' ? 'primary' : ''"
            @click="timelineFilter = 'pending'"
            size="small"
          >
            进行中
          </el-button>
          <el-button 
            :type="timelineFilter === 'completed' ? 'primary' : ''"
            @click="timelineFilter = 'completed'"
            size="small"
          >
            已完成
          </el-button>
        </el-button-group>
      </div>
    </div>
    
    <div class="timeline-container">
      <div class="timeline-line"></div>
      
      <div v-if="filteredTimelineTasks.length === 0" class="timeline-empty">
        <div class="empty-content">
          <div class="empty-icon">📅</div>
          <h3>暂无任务</h3>
          <p>{{ timelineFilter === 'all' ? '还没有任务' : getTimelineEmptyMessage() }}</p>
        </div>
      </div>
      
      <div 
        v-for="(task, index) in filteredTimelineTasks" 
        :key="task.id"
        class="timeline-item"
        :class="getTimelineItemClass(task)"
        @click="handleTimelineTaskClick(task)"
      >
        <div class="timeline-dot" :style="{ backgroundColor: getTaskColor(task) }"></div>
        <div class="timeline-content">
          <div class="timeline-date">
            {{ formatTimelineDate(task.created_at || task.updated_at) }}
          </div>
          <div class="timeline-task">
            <div class="task-header">
              <h4>{{ task.title }}</h4>
              <div class="task-badges">
                <span class="priority-badge" :class="getPriorityClass(task.urgency)">
                  {{ getPriorityText(task.urgency) }}
                </span>
                <span v-if="task.status" class="status-badge" :class="task.status">
                  {{ getStatusText(task.status) }}
                </span>
              </div>
            </div>
            <p v-if="task.description" class="task-description">
              {{ task.description }}
            </p>
            <div class="task-meta">
              <span v-if="task.module_id" class="module-tag">
                {{ getModuleName(task.module_id) }}
              </span>
              <span class="task-id">#{{ task.id }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElButton } from 'element-plus'
import { useTaskStore, type Task } from '@/stores/tasks'

interface Props {
  tasks: Task[]
}

interface Emits {
  (e: 'task-click', task: Task): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const taskStore = useTaskStore()
const timelineFilter = ref('all')

const filteredTimelineTasks = computed(() => {
  let filtered = [...props.tasks].sort((a, b) => {
    const dateA = new Date(a.created_at || a.updated_at || 0).getTime()
    const dateB = new Date(b.created_at || b.updated_at || 0).getTime()
    return dateB - dateA
  })

  switch (timelineFilter.value) {
    case 'pending':
      return filtered.filter(task => task.status !== 'completed')
    case 'completed':
      return filtered.filter(task => task.status === 'completed')
    default:
      return filtered
  }
})

function getTimelineEmptyMessage() {
  switch (timelineFilter.value) {
    case 'pending':
      return '没有进行中的任务'
    case 'completed':
      return '没有已完成的任务'
    default:
      return '还没有任务'
  }
}

function formatTimelineDate(dateStr: string) {
  if (!dateStr) return ''
  
  const date = new Date(dateStr)
  const now = new Date()
  const diffInMs = now.getTime() - date.getTime()
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))
  
  if (diffInDays === 0) {
    return '今天 ' + date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  } else if (diffInDays === 1) {
    return '昨天'
  } else if (diffInDays < 7) {
    return `${diffInDays}天前`
  } else {
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric'
    })
  }
}

function getTimelineItemClass(task: any) {
  const classes = []
  if (task.status === 'completed') {
    classes.push('completed')
  }
  if (task.urgency <= 1) {
    classes.push('high-priority')
  }
  return classes
}

function handleTimelineTaskClick(task: any) {
  emit('task-click', task)
}

function getTaskColor(task: any) {
  const colors = {
    0: '#ff4d4f', // 紧急 - 红色
    1: '#fa8c16', // 高 - 橙色
    2: '#1890ff', // 中 - 蓝色
    3: '#52c41a', // 低 - 绿色
    4: '#8c8c8c'  // 待办 - 灰色
  }
  return colors[task.urgency as keyof typeof colors] || '#1890ff'
}

function getPriorityClass(urgency: number) {
  const classes = {
    0: 'priority-critical',
    1: 'priority-high',
    2: 'priority-medium',
    3: 'priority-low',
    4: 'priority-backlog'
  }
  return classes[urgency as keyof typeof classes] || 'priority-medium'
}

function getPriorityText(urgency: number) {
  const texts = {
    0: '紧急',
    1: '高',
    2: '中',
    3: '低',
    4: '待办'
  }
  return texts[urgency as keyof typeof texts] || '中'
}

function getStatusText(status: string) {
  const texts = {
    pending: '待办',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status as keyof typeof texts] || status
}

function getModuleName(moduleId: number) {
  const module = taskStore.modules.find(m => m.id === moduleId)
  return module?.name || `模块${moduleId}`
}
</script>

<style scoped>
.timeline-view {
  width: 100%;
  height: 100vh;
  overflow-y: auto;
  padding: 20px;
  background: var(--background);
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.timeline-header h2 {
  margin: 0;
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.timeline-controls {
  display: flex;
  gap: 8px;
}

.timeline-container {
  position: relative;
  max-width: 800px;
  margin: 0 auto;
}

.timeline-line {
  position: absolute;
  left: 20px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--border);
  z-index: 1;
}

.timeline-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  text-align: center;
  color: var(--text-muted);
}

.timeline-empty .empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.timeline-empty .empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.timeline-empty h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--text-secondary);
}

.timeline-empty p {
  margin: 0;
  font-size: var(--font-size-sm);
}

.timeline-item {
  position: relative;
  margin-bottom: 24px;
  padding-left: 56px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.timeline-item:hover {
  transform: translateX(4px);
}

.timeline-item.completed {
  opacity: 0.8;
}

.timeline-item.high-priority .timeline-dot {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(255, 77, 79, 0.4); }
  70% { box-shadow: 0 0 0 6px rgba(255, 77, 79, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 77, 79, 0); }
}

.timeline-dot {
  position: absolute;
  left: 11px;
  top: 8px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--primary);
  border: 3px solid var(--background);
  z-index: 2;
  transition: all 0.2s ease;
}

.timeline-item:hover .timeline-dot {
  transform: scale(1.2);
}

.timeline-content {
  background: var(--surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--border-radius-lg);
  padding: 16px;
  transition: all 0.2s ease;
}

.timeline-item:hover .timeline-content {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.timeline-date {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  margin-bottom: 8px;
}

.timeline-task {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.task-header h4 {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  flex: 1;
  line-height: 1.4;
}

.task-badges {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.priority-badge,
.status-badge {
  font-size: var(--font-size-xs);
  padding: 2px 6px;
  border-radius: var(--border-radius-sm);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.priority-badge.priority-critical {
  background: rgba(255, 77, 79, 0.1);
  color: #ff4d4f;
}

.priority-badge.priority-high {
  background: rgba(250, 140, 22, 0.1);
  color: #fa8c16;
}

.priority-badge.priority-medium {
  background: rgba(24, 144, 255, 0.1);
  color: #1890ff;
}

.priority-badge.priority-low {
  background: rgba(82, 196, 26, 0.1);
  color: #52c41a;
}

.priority-badge.priority-backlog {
  background: rgba(140, 140, 140, 0.1);
  color: #8c8c8c;
}

.status-badge.pending {
  background: rgba(250, 140, 22, 0.1);
  color: #fa8c16;
}

.status-badge.in_progress {
  background: rgba(24, 144, 255, 0.1);
  color: #1890ff;
}

.status-badge.completed {
  background: rgba(82, 196, 26, 0.1);
  color: #52c41a;
}

.status-badge.cancelled {
  background: rgba(140, 140, 140, 0.1);
  color: #8c8c8c;
}

.task-description {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

.task-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.module-tag {
  background: var(--surface-secondary);
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
  font-weight: var(--font-weight-medium);
}

.task-id {
  opacity: 0.6;
}

/* Dark mode support for timeline */
@media (prefers-color-scheme: dark) {
  .timeline-line {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .timeline-dot {
    border-color: var(--background);
  }
  
  .timeline-content {
    background: rgba(255, 255, 255, 0.03);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .timeline-item:hover .timeline-content {
    background: rgba(255, 255, 255, 0.05);
    border-color: var(--primary);
  }
}

/* Responsive timeline */
@media (max-width: 768px) {
  .timeline-view {
    padding: 16px;
  }
  
  .timeline-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .timeline-item {
    padding-left: 40px;
  }
  
  .timeline-line {
    left: 15px;
  }
  
  .timeline-dot {
    left: 6px;
    width: 16px;
    height: 16px;
  }
  
  .task-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .task-badges {
    align-self: flex-end;
  }
}
</style> 