<template>
  <div class="node-header">
    <div class="node-icon">
      <span class="task-icon">{{ taskIcon }}</span>
    </div>
    <div class="node-title-area">
      <h3 v-if="!isEditing" class="node-title">{{ title }}</h3>
      <el-input
        v-else
        v-model="editableTitle"
        ref="titleInput"
        @blur="handleBlur"
        @keydown.enter="handleSave"
        @keydown.esc="handleCancel"
        @input="handleInput"
        class="edit-input"
        size="small"
      />
      <div class="node-subtitle">
        <span class="priority-badge" :class="`priority-badge-${urgency}`">
          P{{ urgency }}
        </span>
        <span class="priority-name">{{ priorityName }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElInput } from 'element-plus'

interface Props {
  title: string
  urgency: number
  isEditing?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isEditing: false
})

const emit = defineEmits<{
  'update:title': [value: string]
  'save': []
  'cancel': []
  'input': [value: string]
}>()

const titleInput = ref<InstanceType<typeof ElInput>>()
const editableTitle = ref(props.title)

// Watch for external title changes
watch(() => props.title, (newTitle) => {
  editableTitle.value = newTitle
})

// Watch for editing state changes
watch(() => props.isEditing, async (isEditing) => {
  if (isEditing) {
    editableTitle.value = props.title
    await nextTick()
    titleInput.value?.focus()
  }
})

// Computed properties
const taskIcon = computed(() => {
  const icons = {
    0: '🚨', // Critical
    1: '⚡', // High
    2: '📝', // Medium
    3: '📋', // Low
    4: '💭'  // Backlog
  }
  return icons[props.urgency as keyof typeof icons] || '📝'
})

const priorityName = computed(() => {
  const names = {
    0: '紧急',
    1: '高',
    2: '中',
    3: '低',
    4: '待办'
  }
  return names[props.urgency as keyof typeof names] || '中'
})

// Event handlers
function handleInput(value: string) {
  emit('update:title', value)
  emit('input', value)
}

function handleSave() {
  emit('save')
}

function handleCancel() {
  editableTitle.value = props.title
  emit('cancel')
}

function handleBlur() {
  emit('save')
}

// Expose methods
defineExpose({
  focus: () => titleInput.value?.focus()
})
</script>

<style scoped>
/* Node Header */
.node-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 16px 12px 20px;
}

.node-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-elevated);
  border-radius: var(--radius-md);
  font-size: 16px;
  transition: all 0.3s ease;
}

.node-title-area {
  flex: 1;
  min-width: 0;
}

.node-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 4px 0;
  line-height: var(--line-height-tight);
  word-wrap: break-word;
}

.node-subtitle {
  display: flex;
  align-items: center;
  gap: 8px;
}

.priority-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: white;
}

.priority-badge.priority-badge-0 { background-color: var(--danger); }
.priority-badge.priority-badge-1 { background-color: var(--warning); }
.priority-badge.priority-badge-2 { background-color: var(--info); }
.priority-badge.priority-badge-3 { background-color: var(--success); }
.priority-badge.priority-badge-4 { background-color: var(--primary); }

.priority-name {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

/* Edit Input */
.edit-input {
  font-family: var(--font-family);
}

:deep(.el-input__wrapper) {
  background-color: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}

:deep(.el-input__inner) {
  color: var(--text-primary);
  font-size: var(--font-size-sm);
}

/* Hover effects */
:global(.task-node:hover) .node-icon {
  transform: scale(1.1);
  background-color: var(--primary-light);
}

:global(.task-node:hover) .node-title {
  color: var(--primary);
}
</style> 