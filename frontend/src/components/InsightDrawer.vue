<template>
  <div>
    <!-- Top Button Group -->
    <div class="top-button-group">
      <!-- Search Button -->
      <div class="top-button search-trigger" @click="openSearch">
        <div class="button-icon">🔍</div>
        <div class="button-label">搜索</div>
      </div>
      
      <!-- Quick Add Button -->
      <div class="top-button quick-add-trigger" @click="openQuickAdd">
        <div class="button-icon">➕</div>
        <div class="button-label">添加</div>
      </div>
      
      <!-- AI Assistant Button -->
      <div class="top-button ai-trigger" @click="openAI">
        <div class="button-icon">🤖</div>
        <div class="button-label">AI助手</div>
      </div>
      
      <!-- View Switcher Button -->
      <div class="top-button view-trigger" @click="toggleViewSwitcher">
        <div class="button-icon">{{ getCurrentViewIcon() }}</div>
        <div class="button-label">视图</div>
      </div>
      
      <!-- Insight Drawer Trigger -->
      <div class="top-button insight-trigger" @click="toggleDrawer">
        <div class="button-icon">📈</div>
        <div class="button-label">分析</div>
      </div>
      
      <!-- Settings Button -->
      <div class="top-button settings-trigger" @click="openSettings">
        <div class="button-icon">⚙️</div>
        <div class="button-label">设置</div>
      </div>
    </div>
    
    <!-- Search Modal -->
    <div v-if="searchOpen" class="command-palette-overlay" @click="handleSearchOverlayClick">
      <div class="command-palette search-modal" @click.stop>
        <div class="search-container">
          <div class="search-icon">🔍</div>
          <input
            ref="searchInput"
            v-model="searchQuery"
            @input="handleSearchInput"
            @keydown="handleSearchKeydown"
            class="search-input"
            placeholder="搜索任务、模块或内容..."
            autocomplete="off"
          />
          <div class="search-hint">
            <kbd>Esc</kbd> 关闭
          </div>
        </div>
        
        <div class="results-container" v-if="searchResults.length > 0">
          <div class="result-section">
            <div class="section-header">
              <div class="search-icon">📄</div>
              <span>搜索结果 ({{ searchResults.length }})</span>
            </div>
            <div
              v-for="(task, index) in searchResults.slice(0, 8)"
              :key="'search-' + task.id"
              :class="['result-item', { 'selected': searchSelectedIndex === index }]"
              @click="selectSearchResult(task)"
              @mouseenter="searchSelectedIndex = index"
            >
              <div class="item-icon task-priority" :class="`priority-${task.urgency}`">
                P{{ task.urgency }}
              </div>
              <div class="item-content">
                <div class="item-title">{{ task.title }}</div>
                <div class="item-description" v-if="task.description">
                  {{ task.description.slice(0, 60) }}{{ task.description.length > 60 ? '...' : '' }}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else-if="searchQuery.trim() && searchResults.length === 0" class="empty-state">
          <div class="empty-icon">🔍</div>
          <div class="empty-text">未找到 "{{ searchQuery }}" 的相关结果</div>
          <div class="empty-hint">试试搜索任务标题或描述</div>
        </div>
        
        <div class="palette-footer">
          <div class="footer-hints">
            <span class="hint-item"><kbd>↑↓</kbd> 导航</span>
            <span class="hint-item"><kbd>Enter</kbd> 选择</span>
            <span class="hint-item"><kbd>Esc</kbd> 关闭</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- View Switcher Modal -->
    <div v-if="viewSwitcherOpen" class="command-palette-overlay" @click="viewSwitcherOpen = false">
      <div class="command-palette view-switcher-modal" @click.stop>
        <div class="search-container">
          <div class="search-icon">🎨</div>
          <div class="view-title">选择视图模式</div>
        </div>
        
        <div class="results-container">
          <div class="result-section">
            <div
              v-for="(view, index) in viewOptions"
              :key="'view-' + view.key"
              :class="['result-item view-option', { 'selected': view.key === currentView }]"
              @click="switchToView(view.key)"
            >
              <div class="item-icon view-icon">{{ view.icon }}</div>
              <div class="item-content">
                <div class="item-title">{{ view.label }}</div>
                <div class="item-description">{{ view.description }}</div>
              </div>
              <div v-if="view.key === currentView" class="current-indicator">当前</div>
            </div>
          </div>
        </div>
        
        <div class="palette-footer">
          <div class="footer-hints">
            <span class="hint-item"><kbd>Esc</kbd> 关闭</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Insight Drawer -->
    <div 
      class="insight-drawer"
      :class="{ 'drawer-open': isOpen }"
    >
      <div class="drawer-header">
        <h3>分析</h3>
        <button class="drawer-close" @click="closeDrawer">×</button>
      </div>
      
      <div class="drawer-tabs">
        <div 
          class="drawer-tab"
          :class="{ active: activeTab === 'workload' }"
          @click="activeTab = 'workload'"
        >
          工作负载
        </div>
        <div 
          class="drawer-tab"
          :class="{ active: activeTab === 'risk' }"
          @click="activeTab = 'risk'"
        >
          风险
        </div>
        <div 
          class="drawer-tab"
          :class="{ active: activeTab === 'debug' }"
          @click="activeTab = 'debug'"
          v-if="showDebugTab"
        >
          调试
        </div>
      </div>
      
      <div class="drawer-content">
        <!-- Workload Tab -->
        <div v-if="activeTab === 'workload'" class="insight-content">
          <div v-if="workloadData" class="workload-summary">
            <div class="stat-item">
              <span class="stat-label">总工时:</span>
              <span class="stat-value">{{ workloadData.totalHours }}小时</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">负载率:</span>
              <span class="stat-value" :class="getWorkloadColor(workloadData.workloadPercentage)">
                {{ workloadData.workloadPercentage }}%
              </span>
            </div>
          </div>
          <button class="refresh-btn" @click="$emit('refresh-workload')">刷新分析</button>
        </div>
        
        <!-- Risk Tab -->
        <div v-if="activeTab === 'risk'" class="insight-content">
          <button class="analyze-btn" @click="$emit('analyze-risks')">分析风险</button>
          <div class="risk-toggle">
            <label>
                          <input 
              type="checkbox" 
              :checked="showRiskRadar" 
              @change="$emit('toggle-risk-radar', ($event.target as HTMLInputElement).checked)"
            />
              显示风险雷达
            </label>
          </div>
        </div>
        
        <!-- Debug Tab -->
        <div v-if="activeTab === 'debug' && showDebugTab" class="insight-content">
          <slot name="debug-content">
            <p>调试信息将在这里显示</p>
          </slot>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'

interface WorkloadData {
  totalHours: number
  workloadPercentage: number
  tasksCount?: number
  analysisDate?: string
}

interface Props {
  open?: boolean
  workloadData?: WorkloadData | null
  showRiskRadar?: boolean
  showDebugTab?: boolean
  currentView?: string
  tasks?: any[]
}

interface Emits {
  (e: 'update:open', value: boolean): void
  (e: 'refresh-workload'): void
  (e: 'analyze-risks'): void
  (e: 'toggle-risk-radar', value: boolean): void
  (e: 'open-settings'): void
  (e: 'open-search'): void
  (e: 'open-quick-add'): void
  (e: 'open-ai-assistant'): void
  (e: 'switch-view', view: string): void
  (e: 'select-task', task: any): void
}

const props = withDefaults(defineProps<Props>(), {
  open: false,
  workloadData: null,
  showRiskRadar: false,
  showDebugTab: false,
  currentView: 'canvas',
  tasks: () => []
})

const emit = defineEmits<Emits>()

const activeTab = ref('workload')

// New state for additional modals
const searchOpen = ref(false)
const searchQuery = ref('')
const searchResults = ref<any[]>([])
const searchSelectedIndex = ref(0)
const searchInput = ref<HTMLInputElement>()

const viewSwitcherOpen = ref(false)

// View options
const viewOptions = ref([
  {
    key: 'canvas',
    label: '画布视图',
    icon: '🎨',
    description: '自由拖拽和排列任务'
  },
  {
    key: 'timeline',
    label: '时间线视图',
    icon: '📅',
    description: '按时间顺序查看任务'
  },
  {
    key: 'island',
    label: '主题岛视图',
    icon: '🏝️',
    description: '按主题分组显示任务'
  }
])

const isOpen = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

function toggleDrawer() {
  isOpen.value = !isOpen.value
}

function closeDrawer() {
  isOpen.value = false
}

function getWorkloadColor(percentage: number): string {
  const safePercentage = typeof percentage === 'number' && isFinite(percentage) ? percentage : 0
  if (safePercentage <= 70) return 'workload-green'
  if (safePercentage <= 90) return 'workload-yellow'
  return 'workload-red'
}

function openSettings() {
  emit('open-settings')
}

// New function handlers
function openSearch() {
  searchOpen.value = true
  searchQuery.value = ''
  searchResults.value = []
  searchSelectedIndex.value = 0
  nextTick(() => {
    searchInput.value?.focus()
  })
}

function openQuickAdd() {
  emit('open-quick-add')
}

function openAI() {
  emit('open-ai-assistant')
}

function toggleViewSwitcher() {
  viewSwitcherOpen.value = !viewSwitcherOpen.value
}

function getCurrentViewIcon() {
  const view = viewOptions.value.find(v => v.key === props.currentView)
  return view?.icon || '🎨'
}

function switchToView(viewKey: string) {
  emit('switch-view', viewKey)
  viewSwitcherOpen.value = false
}

// Search functionality
function handleSearchInput() {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  
  const query = searchQuery.value.toLowerCase()
  searchResults.value = props.tasks.filter(task => 
    task.title.toLowerCase().includes(query) || 
    (task.description && task.description.toLowerCase().includes(query))
  )
  searchSelectedIndex.value = 0
}

function handleSearchKeydown(event: KeyboardEvent) {
  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      searchSelectedIndex.value = Math.min(searchSelectedIndex.value + 1, searchResults.value.length - 1)
      break
    case 'ArrowUp':
      event.preventDefault()
      searchSelectedIndex.value = Math.max(searchSelectedIndex.value - 1, 0)
      break
    case 'Enter':
      event.preventDefault()
      if (searchResults.value[searchSelectedIndex.value]) {
        selectSearchResult(searchResults.value[searchSelectedIndex.value])
      }
      break
    case 'Escape':
      event.preventDefault()
      searchOpen.value = false
      break
  }
}

function selectSearchResult(task: any) {
  emit('select-task', task)
  searchOpen.value = false
}

function handleSearchOverlayClick() {
  searchOpen.value = false
}

// Expose methods
defineExpose({
  toggleDrawer,
  closeDrawer
})
</script>

<style scoped>
/* Top Button Group Container */
.top-button-group {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 6px;
  z-index: 999;
  max-width: 90vw;
  overflow-x: auto;
  padding: 0 16px;
}

/* Shared Top Button Styles */
.top-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 20px;
  box-shadow: 
    0 8px 32px rgba(102, 126, 234, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Button Hover Effects */
.top-button:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 12px 40px rgba(102, 126, 234, 0.15),
    0 4px 16px rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.3);
}

/* Specific Button Styling */
.settings-trigger:hover {
  border-color: rgba(118, 75, 162, 0.3);
  box-shadow: 
    0 12px 40px rgba(118, 75, 162, 0.15),
    0 4px 16px rgba(118, 75, 162, 0.1);
}

.search-trigger:hover {
  border-color: rgba(59, 130, 246, 0.3);
  box-shadow: 
    0 12px 40px rgba(59, 130, 246, 0.15),
    0 4px 16px rgba(59, 130, 246, 0.1);
}

.quick-add-trigger:hover {
  border-color: rgba(34, 197, 94, 0.3);
  box-shadow: 
    0 12px 40px rgba(34, 197, 94, 0.15),
    0 4px 16px rgba(34, 197, 94, 0.1);
}

.ai-trigger:hover {
  border-color: rgba(168, 85, 247, 0.3);
  box-shadow: 
    0 12px 40px rgba(168, 85, 247, 0.15),
    0 4px 16px rgba(168, 85, 247, 0.1);
}

.view-trigger:hover {
  border-color: rgba(245, 158, 11, 0.3);
  box-shadow: 
    0 12px 40px rgba(245, 158, 11, 0.15),
    0 4px 16px rgba(245, 158, 11, 0.1);
}

/* Button Icon and Label Styles */
.button-icon {
  font-size: 16px;
}

.button-label {
  font-size: 14px;
  font-weight: 600;
  color: #1a202c;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.insight-drawer {
  position: fixed;
  top: 0;
  left: 50%;
  transform: translateX(-50%) translateY(-100%);
  width: 520px;
  max-width: 90vw;
  max-height: 70vh;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-top: none;
  border-radius: 0 0 20px 20px;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.15),
    0 8px 32px rgba(102, 126, 234, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 0.8);
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 1000;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.insight-drawer.drawer-open {
  transform: translateX(-50%) translateY(0);
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%);
}

.drawer-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a202c;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.drawer-close {
  background: none;
  border: none;
  font-size: 20px;
  color: rgba(102, 126, 234, 0.6);
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drawer-close:hover {
  background: rgba(102, 126, 234, 0.1);
  color: rgba(102, 126, 234, 0.9);
}

.drawer-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-subtle);
}

.drawer-tab {
  flex: 1;
  padding: 12px 16px;
  text-align: center;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 2px solid transparent;
}

.drawer-tab:hover {
  color: var(--text-primary);
  background: var(--bg-elevated);
}

.drawer-tab.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
  background: var(--primary-light);
}

.drawer-content {
  padding: 20px;
  max-height: calc(70vh - 120px);
  overflow-y: auto;
}

.insight-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.workload-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.stat-value {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
}

.stat-value.workload-green {
  color: var(--success);
}

.stat-value.workload-yellow {
  color: var(--warning);
}

.stat-value.workload-red {
  color: var(--danger);
}

.refresh-btn, .analyze-btn {
  padding: 12px 20px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.refresh-btn:hover, .analyze-btn:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.risk-toggle label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  cursor: pointer;
}

.risk-toggle input[type="checkbox"] {
  margin: 0;
}

/* Responsive Design */
@media (max-width: 1280px) {
  .insight-drawer.drawer-open {
    width: 80vw;
  }
}

@media (max-width: 768px) {
  .insight-drawer {
    width: 100vw;
    border-radius: 0;
  }
  
  .insight-trigger {
    padding: 6px 12px;
  }
}

/* Command Palette Style Overlays */
.command-palette-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(12px);
  z-index: 2000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  animation: overlayFadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes overlayFadeIn {
  from {
    opacity: 0;
    backdrop-filter: blur(0px);
  }
  to {
    opacity: 1;
    backdrop-filter: blur(12px);
  }
}

/* Enhanced Main Palette Container */
.command-palette {
  width: 520px;
  max-width: 90vw;
  max-height: 70vh;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 20px;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.15),
    0 8px 32px rgba(102, 126, 234, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 0.8);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: paletteSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes paletteSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Enhanced Search Container */
.search-container {
  position: relative;
  display: flex;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%);
}

.search-icon {
  color: rgba(102, 126, 234, 0.7);
  font-size: 20px;
  margin-right: 16px;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 16px;
  color: #1a202c;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.5;
  font-weight: 500;
}

.search-input::placeholder {
  color: rgba(102, 126, 234, 0.5);
  font-weight: 400;
}

.search-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(102, 126, 234, 0.6);
  font-size: 13px;
  margin-left: 16px;
  font-weight: 500;
}

.search-hint kbd {
  background: rgba(102, 126, 234, 0.1);
  color: rgba(102, 126, 234, 0.8);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.view-title {
  flex: 1;
  font-size: 16px;
  color: #1a202c;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.5;
  font-weight: 600;
}

/* Enhanced Results Container */
.results-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  max-height: 400px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%);
}

/* Enhanced Result Sections */
.result-section {
  margin-bottom: 20px;
}

.result-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 24px 12px;
  font-size: 13px;
  font-weight: 700;
  color: rgba(102, 126, 234, 0.8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Enhanced Result Items */
.result-item {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  margin: 0 8px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.result-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
  transition: left 0.6s ease;
}

.result-item:hover {
  background: rgba(102, 126, 234, 0.08);
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.result-item:hover::before {
  left: 100%;
}

.result-item.selected {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  border: 2px solid rgba(102, 126, 234, 0.3);
  transform: translateX(6px);
  box-shadow: 
    0 6px 20px rgba(102, 126, 234, 0.2),
    0 2px 8px rgba(0, 0, 0, 0.1);
}

.item-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  margin-right: 16px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border: 1px solid rgba(102, 126, 234, 0.2);
  transition: all 0.3s ease;
}

.result-item:hover .item-icon,
.result-item.selected .item-icon {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  border-color: rgba(102, 126, 234, 0.4);
  transform: scale(1.05);
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 4px;
  line-height: 1.3;
}

.item-description {
  font-size: 13px;
  color: #64748b;
  line-height: 1.4;
}

/* Enhanced Badges */
.task-priority {
  color: white;
  font-size: 12px;
  font-weight: 700;
  border-radius: 8px;
  width: 32px;
  height: 32px;
}

.priority-1 {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.priority-2 {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.priority-3 {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.view-icon {
  font-size: 24px;
  background: none !important;
  border: none !important;
  width: auto !important;
  height: auto !important;
}

.current-indicator {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  color: rgba(102, 126, 234, 0.9);
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

/* Enhanced Empty States */
.empty-state {
  padding: 40px 24px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  color: rgba(102, 126, 234, 0.4);
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
  color: #64748b;
}

/* Enhanced Footer */
.palette-footer {
  padding: 16px 24px;
  border-top: 2px solid rgba(102, 126, 234, 0.1);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%);
}

.footer-hints {
  display: flex;
  justify-content: center;
  gap: 20px;
  color: rgba(102, 126, 234, 0.7);
  font-size: 13px;
  font-weight: 500;
}

.hint-item kbd {
  background: rgba(102, 126, 234, 0.1);
  color: rgba(102, 126, 234, 0.8);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid rgba(102, 126, 234, 0.2);
  margin-right: 4px;
}

/* Responsive Design */
@media (max-width: 768px) {
  .top-button-group {
    gap: 4px;
    padding: 0 8px;
  }
  
  .top-button {
    padding: 6px 10px;
    min-width: 0;
  }
  
  .button-label {
    font-size: 12px;
  }
  
  .command-palette {
    width: 95vw;
    margin: 0 16px;
  }
}
</style> 