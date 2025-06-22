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
    task.title?.toLowerCase().includes(query) ||
    task.description?.toLowerCase().includes(query)
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
/* Modern Global Search with Enhanced Design */
.global-search {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 9999;
  animation: searchFadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes searchFadeIn {
  from {
    opacity: 0;
    backdrop-filter: blur(0px);
  }
  to {
    opacity: 1;
    backdrop-filter: blur(8px);
  }
}

.search-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.search-modal {
  position: absolute;
  top: 15%;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 600px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.15),
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  overflow: hidden;
  animation: searchModalSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  will-change: transform, opacity;
}

@keyframes searchModalSlideIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
}

/* Search Header */
.search-header {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
  padding: 20px;
}

.search-input-container {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 16px;
  padding: 0 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
}

.search-input-container:focus-within {
  border-color: rgba(102, 126, 234, 0.6);
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
  background: rgba(255, 255, 255, 0.95);
}

.search-icon {
  font-size: 18px;
  margin-right: 12px;
  color: rgba(102, 126, 234, 0.7);
  transition: all 0.3s ease;
}

.search-input-container:focus-within .search-icon {
  color: rgba(102, 126, 234, 1);
  transform: scale(1.1);
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 16px;
  padding: 16px 0;
  color: #1a202c;
  font-weight: 500;
  line-height: 1.2;
}

.search-input::placeholder {
  color: rgba(107, 114, 128, 0.8);
  font-weight: 400;
}

.close-button {
  background: none;
  border: none;
  font-size: 20px;
  color: rgba(107, 114, 128, 0.6);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
}

.close-button:hover {
  background: rgba(239, 68, 68, 0.1);
  color: rgba(239, 68, 68, 0.8);
  transform: scale(1.1);
}

/* Search Results */
.search-results {
  max-height: 400px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
}

.search-results::-webkit-scrollbar {
  width: 6px;
}

.search-results::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
}

.search-results::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 3px;
}

.search-results::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}

.results-header {
  padding: 16px 20px 8px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.4);
  background: rgba(248, 250, 252, 0.8);
}

.results-count {
  font-size: 14px;
  color: rgba(107, 114, 128, 0.8);
  font-weight: 500;
}

.results-list {
  padding: 8px 0;
}

.result-item {
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border-left: 4px solid transparent;
  background: transparent;
  position: relative;
  overflow: hidden;
}

.result-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 0;
  height: 100%;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: -1;
}

.result-item:hover::before,
.result-item.active::before {
  width: 100%;
}

.result-item:hover,
.result-item.active {
  background: rgba(102, 126, 234, 0.05);
  border-left-color: rgba(102, 126, 234, 0.6);
  transform: translateX(4px);
}

.result-item.active {
  border-left-color: rgba(102, 126, 234, 0.8);
  background: rgba(102, 126, 234, 0.08);
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a202c;
  line-height: 1.4;
  word-break: break-word;
}

.result-title :deep(mark) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
  color: rgba(102, 126, 234, 0.9);
  padding: 2px 4px;
  border-radius: 4px;
  font-weight: 700;
}

.result-description {
  font-size: 14px;
  color: rgba(107, 114, 128, 0.9);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-description :deep(mark) {
  background: rgba(251, 191, 36, 0.2);
  color: rgba(180, 83, 9, 0.9);
  padding: 1px 3px;
  border-radius: 3px;
  font-weight: 600;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.result-priority {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.result-priority.p0 { background: linear-gradient(135deg, #ef4444, #dc2626); }
.result-priority.p1 { background: linear-gradient(135deg, #f59e0b, #d97706); }
.result-priority.p2 { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.result-priority.p3 { background: linear-gradient(135deg, #10b981, #059669); }
.result-priority.p4 { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }

.result-module {
  background: rgba(102, 126, 234, 0.1);
  color: rgba(102, 126, 234, 0.8);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.result-date {
  font-size: 12px;
  color: rgba(107, 114, 128, 0.7);
  font-weight: 400;
}

/* Empty and Help States */
.search-empty,
.search-help {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  background: rgba(248, 250, 252, 0.5);
}

.empty-icon,
.help-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.7;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-8px);
  }
  60% {
    transform: translateY(-4px);
  }
}

.empty-text,
.help-text {
  font-size: 18px;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
  color: rgba(107, 114, 128, 0.8);
}

.help-shortcuts {
  display: flex;
  gap: 16px;
  margin-top: 20px;
  flex-wrap: wrap;
  justify-content: center;
}

.shortcut {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: rgba(107, 114, 128, 0.8);
}

.shortcut kbd {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(209, 213, 219, 0.8);
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 600;
  color: #374151;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  min-width: 24px;
  text-align: center;
}

/* Loading State */
.search-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: rgba(248, 250, 252, 0.5);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(102, 126, 234, 0.2);
  border-top: 3px solid rgba(102, 126, 234, 0.8);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 14px;
  color: rgba(107, 114, 128, 0.8);
  font-weight: 500;
}

/* Responsive Design */
@media (max-width: 768px) {
  .search-modal {
    top: 10%;
    width: 95%;
    max-width: none;
    margin: 0 auto;
  }
  
  .search-header {
    padding: 16px;
  }
  
  .search-input-container {
    padding: 0 16px;
  }
  
  .search-input {
    font-size: 16px;
    padding: 14px 0;
  }
  
  .result-item {
    padding: 14px 16px;
  }
  
  .help-shortcuts {
    gap: 12px;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .search-modal {
    background: rgba(17, 24, 39, 0.95);
    border: 1px solid rgba(55, 65, 81, 0.3);
  }
  
  .search-header {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
    border-bottom: 1px solid rgba(55, 65, 81, 0.6);
  }
  
  .search-input-container {
    background: rgba(31, 41, 55, 0.8);
    border: 2px solid rgba(102, 126, 234, 0.3);
  }
  
  .search-input {
    color: #f9fafb;
  }
  
  .search-input::placeholder {
    color: rgba(156, 163, 175, 0.8);
  }
  
  .search-results {
    background: rgba(17, 24, 39, 0.6);
  }
  
  .results-header {
    background: rgba(31, 41, 55, 0.8);
    border-bottom: 1px solid rgba(55, 65, 81, 0.4);
  }
  
  .result-title {
    color: #f9fafb;
  }
  
  .result-description {
    color: rgba(156, 163, 175, 0.9);
  }
  
  .empty-text,
  .help-text {
    color: #f9fafb;
  }
  
  .shortcut kbd {
    background: rgba(31, 41, 55, 0.9);
    border: 1px solid rgba(55, 65, 81, 0.8);
    color: #d1d5db;
  }
}
</style>