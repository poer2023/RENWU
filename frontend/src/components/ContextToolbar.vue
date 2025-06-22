<template>
  <div 
    v-if="visible" 
    class="context-toolbar"
    :style="position"
  >
    <div class="toolbar-button" @click="$emit('link-tasks')" title="创建依赖">
      🔗
    </div>
    <div class="toolbar-button" @click="showAlignOptions = !showAlignOptions" title="对齐">
      〢
    </div>
    <div class="toolbar-button" @click="$emit('generate-subtasks')" title="AI子任务">
      🧩
    </div>
    <div class="toolbar-button delete" @click="$emit('delete-task')" title="删除">
      🗑
    </div>
    
    <!-- Align Options Dropdown -->
    <div v-if="showAlignOptions" class="align-dropdown">
      <div class="align-option" @click="handleAlign('left')">左对齐</div>
      <div class="align-option" @click="handleAlign('center')">居中</div>
      <div class="align-option" @click="handleAlign('right')">右对齐</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  visible?: boolean
  position?: {
    top: string
    left: string
  }
}

interface Emits {
  (e: 'link-tasks'): void
  (e: 'generate-subtasks'): void
  (e: 'delete-task'): void
  (e: 'align-nodes', direction: string): void
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  position: () => ({ top: '0px', left: '0px' })
})

const emit = defineEmits<Emits>()

const showAlignOptions = ref(false)

function handleAlign(direction: string) {
  emit('align-nodes', direction)
  showAlignOptions.value = false
}

// Expose methods
defineExpose({
  hideAlignOptions: () => { showAlignOptions.value = false }
})
</script>

<style scoped>
.context-toolbar {
  position: fixed;
  display: flex;
  gap: 8px;
  padding: 8px;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: 999;
  backdrop-filter: blur(8px);
}

.toolbar-button {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: transparent;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 16px;
  position: relative;
}

.toolbar-button:hover {
  background: var(--bg-elevated);
  transform: translateY(-1px);
}

.toolbar-button.delete:hover {
  background: var(--danger);
  color: white;
}

.align-dropdown {
  position: absolute;
  top: 44px;
  left: 0;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  min-width: 120px;
}

.align-option {
  padding: 8px 12px;
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: background 0.2s ease;
}

.align-option:hover {
  background: var(--bg-elevated);
}

/* Responsive Design */
@media (max-width: 768px) {
  .context-toolbar {
    flex-direction: column;
  }
  
  .toolbar-button {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }
  
  .align-dropdown {
    top: 0;
    left: 40px;
  }
}
</style> 