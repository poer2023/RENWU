<template>
  <div class="ai-assistant-prompt" v-if="visible" :style="{ left: position.x + 'px', top: position.y + 'px' }">
    <div class="prompt-header">
      <span class="prompt-title">AI Assistant</span>
      <button class="close-btn" @click="$emit('close')">×</button>
    </div>
    
    <div class="command-list">
      <div
        v-for="(command, index) in commands"
        :key="command.id"
        class="command-item"
        :class="{ active: selectedIndex === index }"
        @click="selectCommand(command)"
        @mouseenter="selectedIndex = index"
      >
        <span class="command-icon">{{ command.icon }}</span>
        <div class="command-info">
          <div class="command-label">{{ command.label }}</div>
          <div class="command-description">{{ command.description }}</div>
        </div>
      </div>
    </div>
    
    <div class="prompt-footer" v-if="loading">
      <div class="loading-indicator">
        <span class="loading-spinner"></span>
        Processing...
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useAIAssistant, type AIAssistantCommand } from '@/composables/useAIAssistant'

interface Position {
  x: number
  y: number
}

interface Props {
  visible: boolean
  position: Position
  content: string
  context?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  command: [command: string, result: string]
}>()

const { commands, loading, executeCommand } = useAIAssistant()
const selectedIndex = ref(0)

const selectCommand = async (command: AIAssistantCommand) => {
  try {
    const result = await executeCommand(command.id, props.content, props.context)
    emit('command', command.id, result)
  } catch (error) {
    console.error('AI command failed:', error)
  }
}

const handleKeydown = (event: KeyboardEvent) => {
  if (!props.visible) return

  switch (event.key) {
    case 'ArrowUp':
      event.preventDefault()
      selectedIndex.value = Math.max(0, selectedIndex.value - 1)
      break
    case 'ArrowDown':
      event.preventDefault()
      selectedIndex.value = Math.min(commands.length - 1, selectedIndex.value + 1)
      break
    case 'Enter':
      event.preventDefault()
      selectCommand(commands[selectedIndex.value])
      break
    case 'Escape':
      event.preventDefault()
      emit('close')
      break
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.ai-assistant-prompt {
  position: fixed;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  min-width: 300px;
  max-width: 400px;
  z-index: 10000;
  font-size: 14px;
}

.prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.prompt-title {
  font-weight: 600;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: #f0f0f0;
}

.command-list {
  max-height: 300px;
  overflow-y: auto;
}

.command-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f8f9fa;
  transition: background-color 0.2s;
}

.command-item:hover,
.command-item.active {
  background: #f0f7ff;
}

.command-item:last-child {
  border-bottom: none;
}

.command-icon {
  font-size: 16px;
  margin-right: 12px;
  flex-shrink: 0;
}

.command-info {
  flex: 1;
}

.command-label {
  font-weight: 500;
  color: #333;
  margin-bottom: 2px;
}

.command-description {
  font-size: 12px;
  color: #666;
  line-height: 1.3;
}

.prompt-footer {
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
  background: #f8f9fa;
  border-radius: 0 0 8px 8px;
}

.loading-indicator {
  display: flex;
  align-items: center;
  color: #666;
  font-size: 12px;
}

.loading-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>