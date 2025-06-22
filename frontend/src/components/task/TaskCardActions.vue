<template>
  <div class="node-actions">
    <button @click.stop="$emit('edit')" class="node-action-btn" title="编辑">
      <span class="action-icon">✏️</span>
    </button>
    <button 
      @click.stop="$emit('generate-subtasks')" 
      class="node-action-btn"
      title="生成子任务"
      :disabled="generating"
    >
      <span v-if="generating" class="action-icon loading">⏳</span>
      <span v-else class="action-icon">🤖</span>
    </button>
    <button @click.stop="$emit('delete')" class="node-action-btn danger" title="删除任务">
      <span class="action-icon">🗑️</span>
    </button>
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
interface Props {
  generating?: boolean
}

withDefaults(defineProps<Props>(), {
  generating: false
})

defineEmits<{
  'edit': []
  'generate-subtasks': []
  'delete': []
}>()
</script>

<style scoped>
/* Node Actions */
.node-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.node-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background-color: transparent;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--text-secondary);
  position: relative;
  overflow: hidden;
}

.node-action-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: var(--primary-light);
  border-radius: 50%;
  transition: all 0.3s ease;
  transform: translate(-50%, -50%);
  z-index: -1;
}

.node-action-btn:hover {
  background-color: var(--bg-elevated);
  transform: scale(1.15) translateY(-1px);
  box-shadow: var(--shadow-sm);
  color: var(--primary);
}

.node-action-btn:hover::before {
  width: 100%;
  height: 100%;
}

.node-action-btn:active {
  transform: scale(1.05);
  transition: all 0.1s ease;
}

.node-action-btn.danger:hover {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--danger);
}

.node-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.node-action-btn:disabled:hover {
  transform: none;
  background-color: transparent;
  box-shadow: none;
}

.action-icon {
  font-size: 12px;
}

.action-icon.loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style> 