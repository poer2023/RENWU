<template>
  <div class="node-footer">
    <div class="node-meta">
      <span class="module-pill" v-if="moduleId" :style="moduleStyle">
        {{ moduleName }}
      </span>
      <div class="node-badges">
        <span class="time-badge" :title="formatFullDate(createdAt)">
          {{ formatRelativeTime(createdAt) }}
        </span>
        <span v-if="estimatedHours && estimatedHours > 0" class="hours-badge">
          {{ estimatedHours }}h
        </span>
      </div>
    </div>
    <div class="node-actions" v-if="showActions">
      <slot name="actions"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  moduleId?: number | null
  moduleName?: string
  moduleColor?: string
  createdAt: string
  estimatedHours?: number
  showActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showActions: false
})

// Computed module style
const moduleStyle = computed(() => {
  if (!props.moduleId || !props.moduleColor) return {}
  return {
    backgroundColor: props.moduleColor,
    color: 'rgba(0, 0, 0, 0.8)'
  }
})

// Utility functions
function formatRelativeTime(date: string): string {
  if (!date) return '未知时间'
  
  try {
    const now = new Date()
    const then = new Date(date)
    
    // Check if the date is valid
    if (isNaN(then.getTime())) {
      return '无效时间'
    }
    
    const diffMs = now.getTime() - then.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffMinutes = Math.floor(diffMs / (1000 * 60))

    if (diffDays > 0) return `${diffDays}天前`
    if (diffHours > 0) return `${diffHours}小时前`
    if (diffMinutes > 0) return `${diffMinutes}分钟前`
    return '刚刚'
  } catch (error) {
    console.error('Time formatting error:', error, 'date:', date)
    return '时间错误'
  }
}

function formatFullDate(date: string): string {
  if (!date) return '未知时间'
  
  try {
    const dateObj = new Date(date)
    if (isNaN(dateObj.getTime())) {
      return '无效时间'
    }
    return dateObj.toLocaleString('zh-CN')
  } catch (error) {
    console.error('Full date formatting error:', error, 'date:', date)
    return '时间错误'
  }
}
</script>

<style scoped>
/* Node Footer */
.node-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px 16px 20px;
  border-top: 1px solid var(--border-subtle);
  margin-top: 8px;
}

.node-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.module-pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  background-color: var(--bg-elevated);
  color: var(--text-secondary);
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: all 0.2s ease;
  border: 1px solid var(--border-subtle);
}

.node-badges {
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s ease;
}

.time-badge,
.hours-badge {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  padding: 1px 4px;
  border-radius: 3px;
  background-color: var(--bg-elevated);
  transition: all 0.2s ease;
}

/* Node Actions */
.node-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Hover effects */
:global(.task-node:hover) .module-pill {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
  border-color: var(--border-default);
}

:global(.task-node:hover) .node-badges {
  transform: translateX(2px);
}

:global(.task-node:hover) .time-badge,
:global(.task-node:hover) .hours-badge {
  background-color: var(--primary-light);
  color: var(--primary);
  transform: scale(1.05);
}
</style> 