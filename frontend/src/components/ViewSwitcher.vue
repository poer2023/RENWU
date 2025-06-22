<template>
  <div class="view-switcher">
    <div class="view-tabs">
      <div 
        v-for="view in views"
        :key="view.key"
        class="view-tab"
        :class="{ active: currentView === view.key }"
        @click="switchView(view.key)"
        :title="view.description"
      >
        <div class="view-icon">{{ view.icon }}</div>
        <div class="view-label">{{ view.label }}</div>
      </div>
    </div>
    
    <div class="view-actions">
      <el-button
        v-if="currentView === 'island'"
        :loading="islandLoading"
        @click="$emit('reload-islands')"
        size="small"
        type="primary"
      >
        {{ islandLoading ? '加载中...' : '重新生成岛屿' }}
      </el-button>
      
      <el-button
        v-if="currentView === 'timeline'"
        @click="$emit('filter-timeline')"
        size="small"
      >
        筛选
      </el-button>
      
      <el-button
        v-if="currentView === 'canvas'"
        @click="$emit('auto-arrange')"
        size="small"
      >
        自动排列
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface ViewConfig {
  key: string
  label: string
  icon: string
  description: string
}

interface Props {
  currentView: string
  islandLoading?: boolean
}

interface Emits {
  (e: 'update:current-view', value: string): void
  (e: 'reload-islands'): void
  (e: 'filter-timeline'): void
  (e: 'auto-arrange'): void
}

const props = withDefaults(defineProps<Props>(), {
  islandLoading: false
})

const emit = defineEmits<Emits>()

const views = computed<ViewConfig[]>(() => [
  {
    key: 'canvas',
    label: '画布视图',
    icon: '🎨',
    description: '自由拖拽的任务画布'
  },
  {
    key: 'timeline',
    label: '时间线',
    icon: '📅',
    description: '按时间排序的任务列表'
  },
  {
    key: 'island',
    label: '主题岛',
    icon: '🏝️',
    description: 'AI生成的主题聚类视图'
  }
])

function switchView(viewKey: string) {
  emit('update:current-view', viewKey)
}
</script>

<style scoped>
.view-switcher {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-light);
}

.view-tabs {
  display: flex;
  gap: var(--spacing-xs);
}

.view-tab {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-base);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.view-tab:hover {
  background-color: var(--bg-tertiary);
}

.view-tab.active {
  background-color: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.view-icon {
  font-size: var(--font-size-lg);
}

.view-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  white-space: nowrap;
}

.view-actions {
  display: flex;
  gap: var(--spacing-sm);
}

@media (max-width: 768px) {
  .view-switcher {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .view-label {
    display: none;
  }
  
  .view-tab {
    padding: var(--spacing-sm);
  }
  
  .view-actions {
    width: 100%;
    justify-content: center;
  }
}
</style> 