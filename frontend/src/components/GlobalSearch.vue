<template>
  <div class="global-search" v-if="visible">
    <div class="search-overlay" @click="close"></div>
    <div class="search-modal">
      <div class="search-header">
        <div class="search-input-container">
          <span class="search-icon">🔍</span>
          <input
            ref="searchInput"
            v-model="searchQuery"
            @input="onSearchInput"
            @keydown="handleKeydown"
            type="text"
            placeholder="Search tasks... (type to search)"
            class="search-input"
          />
          <button @click="close" class="close-button">✕</button>
        </div>
      </div>
      
      <div class="search-results" v-if="searchResults.length > 0">
        <div class="results-header">
          <span class="results-count">{{ searchResults.length }} results</span>
        </div>
        
        <div class="results-list">
          <div
            v-for="(task, index) in searchResults"
            :key="task.id"
            :class="['result-item', { active: selectedIndex === index }]"
            @click="selectResult(task)"
            @mouseenter="selectedIndex = index"
          >
            <div class="result-content">
              <div class="result-title" v-html="highlightText(task.title)"></div>
              <div class="result-description" v-if="task.description" v-html="highlightText(task.description)"></div>
              <div class="result-meta">
                <span class="result-priority" :class="getPriorityClass(task.urgency)">
                  P{{ task.urgency }}
                </span>
                <span class="result-module" v-if="task.module_id">
                  {{ getModuleName(task.module_id) }}
                </span>
                <span class="result-date">
                  {{ formatDate(task.updated_at) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="search-empty" v-else-if="searchQuery.trim() && !loading">
        <div class="empty-icon">📭</div>
        <div class="empty-text">No tasks found for "{{ searchQuery }}"</div>
        <div class="empty-hint">Try different keywords or check spelling</div>
      </div>
      
      <div class="search-help" v-else-if="!searchQuery.trim()">
        <div class="help-icon">💡</div>
        <div class="help-text">Start typing to search tasks</div>
        <div class="help-shortcuts">
          <div class="shortcut">
            <kbd>↑</kbd><kbd>↓</kbd> Navigate
          </div>
          <div class="shortcut">
            <kbd>Enter</kbd> Select
          </div>
          <div class="shortcut">
            <kbd>Esc</kbd> Close
          </div>
        </div>
      </div>
      
      <div class="search-loading" v-if="loading">
        <div class="loading-spinner"></div>
        <div class="loading-text">Searching...</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useTaskStore, type Task } from '@/stores/tasks'

interface Props {
  visible: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const taskStore = useTaskStore()
const searchInput = ref<HTMLInputElement>()
const searchQuery = ref('')
const selectedIndex = ref(0)
const loading = ref(false)

const searchResults = computed(() => {
  if (!searchQuery.value.trim()) return []
  
  const query = searchQuery.value.toLowerCase()
  return taskStore.tasks.filter(task => 
    task.title.toLowerCase().includes(query) ||
    task.description.toLowerCase().includes(query)
  )
})

const onSearchInput = () => {
  selectedIndex.value = 0
  taskStore.updateSearchQuery(searchQuery.value)
}

const highlightText = (text: string) => {
  if (!searchQuery.value.trim()) return text
  
  const query = searchQuery.value.trim()
  const regex = new RegExp(`(${query})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

const getPriorityClass = (urgency: number) => {
  const classes = ['p0', 'p1', 'p2', 'p3', 'p4']
  return classes[urgency] || 'p2'
}

const getModuleName = (moduleId: number) => {
  return taskStore.getModuleName(moduleId)
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  return date.toLocaleDateString()
}

const selectResult = (task: Task) => {
  taskStore.jumpToTask(task.id)
  close()
}

const handleKeydown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'ArrowUp':
      event.preventDefault()
      selectedIndex.value = Math.max(0, selectedIndex.value - 1)
      break
    case 'ArrowDown':
      event.preventDefault()
      selectedIndex.value = Math.min(searchResults.value.length - 1, selectedIndex.value + 1)
      break
    case 'Enter':
      event.preventDefault()
      if (searchResults.value[selectedIndex.value]) {
        selectResult(searchResults.value[selectedIndex.value])
      }
      break
    case 'Escape':
      event.preventDefault()
      close()
      break
  }
}

const close = () => {
  searchQuery.value = ''
  selectedIndex.value = 0
  taskStore.updateSearchQuery('')
  emit('close')
}

// Focus input when component becomes visible
onMounted(() => {
  if (props.visible) {
    nextTick(() => {
      searchInput.value?.focus()
    })
  }
})

// Focus input when visibility changes
const focusInput = () => {
  if (props.visible) {
    nextTick(() => {
      searchInput.value?.focus()
    })
  }
}

// Watch for visibility changes
const observer = new MutationObserver(() => {
  if (props.visible) {
    focusInput()
  }
})

onMounted(() => {
  observer.observe(document.body, { childList: true, subtree: true })
})

onUnmounted(() => {
  observer.disconnect()
})
</script>

<style scoped>
.global-search {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 10vh;
}

.search-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.search-modal {
  position: relative;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  animation: searchModalIn 0.2s ease-out;
}

@keyframes searchModalIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.search-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.search-input-container {
  display: flex;
  align-items: center;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px 16px;
}

.search-icon {
  font-size: 18px;
  margin-right: 12px;
  color: #666;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 16px;
  outline: none;
  color: #333;
}

.search-input::placeholder {
  color: #999;
}

.close-button {
  background: none;
  border: none;
  font-size: 16px;
  color: #666;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  margin-left: 8px;
}

.close-button:hover {
  background: #e9ecef;
}

.search-results {
  max-height: 50vh;
  overflow-y: auto;
}

.results-header {
  padding: 12px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #f0f0f0;
}

.results-count {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.results-list {
  padding: 8px 0;
}

.result-item {
  padding: 12px 20px;
  cursor: pointer;
  border-bottom: 1px solid #f8f9fa;
  transition: background-color 0.2s;
}

.result-item:hover,
.result-item.active {
  background: #f0f7ff;
}

.result-item:last-child {
  border-bottom: none;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-title {
  font-weight: 500;
  color: #333;
  line-height: 1.4;
}

.result-description {
  font-size: 14px;
  color: #666;
  line-height: 1.4;
  margin-top: 2px;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 6px;
  font-size: 12px;
}

.result-priority {
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
  color: white;
}

.result-priority.p0 { background: #ff4d4f; }
.result-priority.p1 { background: #fa8c16; }
.result-priority.p2 { background: #fadb14; color: #333; }
.result-priority.p3 { background: #52c41a; }
.result-priority.p4 { background: #1890ff; }

.result-module {
  color: #666;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
}

.result-date {
  color: #999;
}

.search-empty,
.search-help {
  padding: 40px 20px;
  text-align: center;
  color: #666;
}

.empty-icon,
.help-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text,
.help-text {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
  color: #999;
}

.help-shortcuts {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
}

.shortcut {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
}

kbd {
  background: #f0f0f0;
  border: 1px solid #ccc;
  border-radius: 3px;
  padding: 2px 6px;
  font-size: 11px;
  font-family: monospace;
}

.search-loading {
  padding: 40px 20px;
  text-align: center;
  color: #666;
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

.loading-text {
  font-size: 14px;
}

:deep(mark) {
  background: #fff3cd;
  color: #856404;
  padding: 1px 2px;
  border-radius: 2px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>