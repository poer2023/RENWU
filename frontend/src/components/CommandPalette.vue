<template>
  <div v-if="visible" class="command-palette-overlay" @click="handleOverlayClick">
    <div class="command-palette" @click.stop>
      <div class="search-container">
        <el-icon class="search-icon"><Search /></el-icon>
        <input
          ref="searchInput"
          v-model="query"
          @input="handleSearch"
          @keydown="handleKeydown"
          class="search-input"
          placeholder="搜索任务、模块或命令..."
          autocomplete="off"
        />
        <div class="search-hint">
          <kbd>{{ settingsStore.shortcuts.commandPalette }}</kbd> 搜索
        </div>
      </div>

      <div class="results-container" v-if="hasResults">
        <!-- Quick Actions -->
        <div v-if="filteredCommands.length > 0" class="result-section">
          <div class="section-header">
            <el-icon><Lightning /></el-icon>
            <span>快速操作</span>
          </div>
          <div
            v-for="(command, index) in filteredCommands"
            :key="'command-' + index"
            :class="['result-item', { 'selected': selectedIndex === getCommandIndex(index) }]"
            @click="executeCommand(command)"
            @mouseenter="selectedIndex = getCommandIndex(index)"
          >
            <div class="item-icon">{{ command.icon }}</div>
            <div class="item-content">
              <div class="item-title">{{ command.name }}</div>
              <div class="item-description">{{ command.description }}</div>
            </div>
            <div class="item-shortcut" v-if="command.shortcut">
              <kbd>{{ command.shortcut }}</kbd>
            </div>
          </div>
        </div>

        <!-- Tasks -->
        <div v-if="filteredTasks.length > 0" class="result-section">
          <div class="section-header">
            <el-icon><Document /></el-icon>
            <span>任务 ({{ filteredTasks.length }})</span>
          </div>
          <div
            v-for="(task, index) in filteredTasks.slice(0, 8)"
            :key="'task-' + task.id"
            :class="['result-item', { 'selected': selectedIndex === getTaskIndex(index) }]"
            @click="selectTask(task)"
            @mouseenter="selectedIndex = getTaskIndex(index)"
          >
            <div class="item-icon task-priority" :class="`priority-${task.urgency}`">
              P{{ task.urgency }}
            </div>
            <div class="item-content">
              <div class="item-title">{{ task.title }}</div>
              <div class="item-description" v-if="task.description">
                {{ task.description.slice(0, 60) }}{{ task.description.length > 60 ? '...' : '' }}
              </div>
              <div class="item-meta">
                <span v-if="task.module_id" class="module-badge" :style="getModuleStyle(task.module_id)">
                  {{ getModuleName(task.module_id) }}
                </span>
                <span class="time-badge">{{ formatRelativeTime(task.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Modules -->
        <div v-if="filteredModules.length > 0" class="result-section">
          <div class="section-header">
            <el-icon><Grid /></el-icon>
            <span>模块 ({{ filteredModules.length }})</span>
          </div>
          <div
            v-for="(module, index) in filteredModules"
            :key="'module-' + module.id"
            :class="['result-item', { 'selected': selectedIndex === getModuleIndex(index) }]"
            @click="selectModule(module)"
            @mouseenter="selectedIndex = getModuleIndex(index)"
          >
            <div class="item-icon module-color" :style="{ backgroundColor: module.color }"></div>
            <div class="item-content">
              <div class="item-title">{{ module.name }}</div>
              <div class="item-description">
                {{ getModuleTaskCount(module.id) }} 个任务
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="query.trim() && !hasResults" class="empty-state">
        <el-icon class="empty-icon"><Search /></el-icon>
        <div class="empty-text">未找到 "{{ query }}" 的相关结果</div>
        <div class="empty-hint">试试搜索任务标题、描述或模块名称</div>
      </div>

      <!-- Default State -->
      <div v-else class="default-state">
        <div class="recent-section">
          <div class="section-header">
            <el-icon><Clock /></el-icon>
            <span>最近的任务</span>
          </div>
          <div
            v-for="(task, index) in recentTasks.slice(0, 5)"
            :key="'recent-' + task.id"
            :class="['result-item', { 'selected': selectedIndex === index }]"
            @click="selectTask(task)"
            @mouseenter="selectedIndex = index"
          >
            <div class="item-icon task-priority" :class="`priority-${task.urgency}`">
              P{{ task.urgency }}
            </div>
            <div class="item-content">
              <div class="item-title">{{ task.title }}</div>
              <div class="item-meta">
                <span class="time-badge">{{ formatRelativeTime(task.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="palette-footer">
        <div class="footer-hints">
          <span class="hint-item"><kbd>↑↓</kbd> 导航</span>
          <span class="hint-item"><kbd>Enter</kbd> 选择</span>
          <span class="hint-item"><kbd>Esc</kbd> 关闭</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ElIcon } from 'element-plus'
import { Search, Lightning, Document, Grid, Clock } from '@element-plus/icons-vue'
import { useTaskStore, type Task, type Module } from '@/stores/tasks'
import { useSettingsStore } from '@/stores/settings'

interface Props {
  visible: boolean
}

interface Command {
  name: string
  description: string
  icon: string
  action: () => void
  shortcut?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  selectTask: [task: Task]
  selectModule: [module: Module]
  executeCommand: [command: Command]
}>()

const taskStore = useTaskStore()
const settingsStore = useSettingsStore()

const searchInput = ref<HTMLInputElement>()
const query = ref('')
const selectedIndex = ref(0)

// Commands definition
const commands = ref<Command[]>([
  {
    name: '新建任务',
    description: '快速创建新任务',
    icon: '➕',
    action: () => emit('executeCommand', { name: 'newTask' } as Command),
    shortcut: settingsStore.shortcuts.quickAdd
  },
  {
    name: '新建模块',
    description: '创建新的任务模块',
    icon: '📁',
    action: () => emit('executeCommand', { name: 'newModule' } as Command),
    shortcut: settingsStore.shortcuts.newModule
  },
  {
    name: '自动排列',
    description: '自动排列所有任务',
    icon: '🎯',
    action: () => emit('executeCommand', { name: 'autoArrange' } as Command),
    shortcut: settingsStore.shortcuts.autoArrange
  },
  {
    name: '导出任务',
    description: '导出任务数据',
    icon: '📤',
    action: () => emit('executeCommand', { name: 'export' } as Command),
    shortcut: settingsStore.shortcuts.export
  },
  {
    name: '设置',
    description: '打开应用设置',
    icon: '⚙️',
    action: () => emit('executeCommand', { name: 'settings' } as Command),
    shortcut: settingsStore.shortcuts.settings
  },
  {
    name: '主题岛视图',
    description: '切换主题岛视图',
    icon: '🏝️',
    action: () => emit('executeCommand', { name: 'toggleIsland' } as Command)
  },
  {
    name: '画布视图',
    description: '切换到画布视图',
    icon: '🎨',
    action: () => emit('executeCommand', { name: 'canvasView' } as Command)
  },
  {
    name: '时间线视图',
    description: '切换到时间线视图',
    icon: '📅',
    action: () => emit('executeCommand', { name: 'timelineView' } as Command)
  },
  {
    name: '周报生成',
    description: '生成工作周报',
    icon: '📊',
    action: () => emit('executeCommand', { name: 'weeklyReport' } as Command)
  },
  {
    name: '风险分析',
    description: '分析任务风险',
    icon: '⚠️',
    action: () => emit('executeCommand', { name: 'riskAnalysis' } as Command)
  },
  {
    name: '工作负载分析',
    description: '分析当前工作负载',
    icon: '📈',
    action: () => emit('executeCommand', { name: 'workloadAnalysis' } as Command)
  },
  {
    name: '缩放重置',
    description: '重置画布缩放',
    icon: '🔍',
    action: () => emit('executeCommand', { name: 'resetZoom' } as Command),
    shortcut: settingsStore.shortcuts.resetZoom
  },
  {
    name: '放大',
    description: '放大画布',
    icon: '🔍',
    action: () => emit('executeCommand', { name: 'zoomIn' } as Command),
    shortcut: settingsStore.shortcuts.zoomIn
  },
  {
    name: '缩小',
    description: '缩小画布',
    icon: '🔍',
    action: () => emit('executeCommand', { name: 'zoomOut' } as Command),
    shortcut: settingsStore.shortcuts.zoomOut
  },
  {
    name: '全选',
    description: '选择所有任务',
    icon: '☑️',
    action: () => emit('executeCommand', { name: 'selectAll' } as Command),
    shortcut: settingsStore.shortcuts.selectAll
  },
  {
    name: '切换网格',
    description: '显示/隐藏网格背景',
    icon: '⊞',
    action: () => emit('executeCommand', { name: 'toggleGrid' } as Command)
  },
  {
    name: '切换侧边栏',
    description: '显示/隐藏侧边栏',
    icon: '⋮',
    action: () => emit('executeCommand', { name: 'toggleSidebar' } as Command),
    shortcut: settingsStore.shortcuts.toggleSidebar
  },
  {
    name: '数据备份',
    description: '备份所有数据',
    icon: '💾',
    action: () => emit('executeCommand', { name: 'backup' } as Command)
  },
  {
    name: 'AI解析',
    description: '从文本智能解析任务',
    icon: '🤖',
    action: () => emit('executeCommand', { name: 'aiParse' } as Command)
  },
  {
    name: '搜索',
    description: '搜索任务和内容',
    icon: '🔍',
    action: () => emit('executeCommand', { name: 'search' } as Command),
    shortcut: settingsStore.shortcuts.search
  },
  {
    name: '定位最新任务',
    description: '快速定位到最新创建的任务',
    icon: '🎯',
    action: () => emit('executeCommand', { name: 'focusLatest' } as Command),
    shortcut: 'Space'
  }
])

// Computed properties
const filteredCommands = computed(() => {
  if (!query.value.trim()) return []
  const q = query.value.toLowerCase()
  return commands.value.filter(cmd => 
    cmd.name.toLowerCase().includes(q) || 
    cmd.description.toLowerCase().includes(q)
  )
})

const filteredTasks = computed(() => {
  if (!query.value.trim()) return []
  const q = query.value.toLowerCase()
  return taskStore.tasks.filter(task => 
    task.title.toLowerCase().includes(q) || 
    task.description.toLowerCase().includes(q)
  ).slice(0, 20)
})

const filteredModules = computed(() => {
  if (!query.value.trim()) return []
  const q = query.value.toLowerCase()
  return taskStore.modules.filter(module => 
    module.name.toLowerCase().includes(q)
  )
})

const recentTasks = computed(() => {
  return [...taskStore.tasks]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 10)
})

const hasResults = computed(() => {
  return filteredCommands.value.length > 0 || 
         filteredTasks.value.length > 0 || 
         filteredModules.value.length > 0
})

const totalResults = computed(() => {
  return filteredCommands.value.length + 
         Math.min(filteredTasks.value.length, 8) + 
         filteredModules.value.length
})

// Helper functions for index calculation
function getCommandIndex(index: number): number {
  return index
}

function getTaskIndex(index: number): number {
  return filteredCommands.value.length + index
}

function getModuleIndex(index: number): number {
  return filteredCommands.value.length + Math.min(filteredTasks.value.length, 8) + index
}

// Event handlers
function handleSearch() {
  selectedIndex.value = 0
}

function handleKeydown(event: KeyboardEvent) {
  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      if (query.value.trim()) {
        selectedIndex.value = Math.min(selectedIndex.value + 1, totalResults.value - 1)
      } else {
        selectedIndex.value = Math.min(selectedIndex.value + 1, recentTasks.value.length - 1)
      }
      break
      
    case 'ArrowUp':
      event.preventDefault()
      selectedIndex.value = Math.max(selectedIndex.value - 1, 0)
      break
      
    case 'Enter':
      event.preventDefault()
      executeSelected()
      break
      
    case 'Escape':
      event.preventDefault()
      emit('close')
      break
  }
}

function executeSelected() {
  const commandsLength = filteredCommands.value.length
  const tasksLength = Math.min(filteredTasks.value.length, 8)
  
  if (query.value.trim()) {
    if (selectedIndex.value < commandsLength) {
      executeCommand(filteredCommands.value[selectedIndex.value])
    } else if (selectedIndex.value < commandsLength + tasksLength) {
      const taskIndex = selectedIndex.value - commandsLength
      selectTask(filteredTasks.value[taskIndex])
    } else {
      const moduleIndex = selectedIndex.value - commandsLength - tasksLength
      selectModule(filteredModules.value[moduleIndex])
    }
  } else {
    // Default state - recent tasks
    if (selectedIndex.value < recentTasks.value.length) {
      selectTask(recentTasks.value[selectedIndex.value])
    }
  }
}

function executeCommand(command: Command) {
  command.action()
  emit('close')
}

function selectTask(task: Task) {
  emit('selectTask', task)
  emit('close')
}

function selectModule(module: Module) {
  emit('selectModule', module)
  emit('close')
}

function handleOverlayClick() {
  emit('close')
}

// Utility functions
function getModuleName(moduleId: number): string {
  const module = taskStore.modules.find(m => m.id === moduleId)
  return module?.name || '未分类'
}

function getModuleStyle(moduleId: number) {
  const module = taskStore.modules.find(m => m.id === moduleId)
  return module ? { backgroundColor: module.color } : {}
}

function getModuleTaskCount(moduleId: number): number {
  return taskStore.tasks.filter(task => task.module_id === moduleId).length
}

function formatRelativeTime(date: string): string {
  const now = new Date()
  const then = new Date(date)
  const diffMs = now.getTime() - then.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffMinutes = Math.floor(diffMs / (1000 * 60))

  if (diffDays > 0) return `${diffDays}天前`
  if (diffHours > 0) return `${diffHours}小时前`
  if (diffMinutes > 0) return `${diffMinutes}分钟前`
  return '刚刚'
}

// Focus management
watch(() => props.visible, (visible) => {
  if (visible) {
    nextTick(() => {
      searchInput.value?.focus()
      selectedIndex.value = 0
      query.value = ''
    })
  }
})

// Global shortcut handling
function handleGlobalKeydown(event: KeyboardEvent) {
  // Check if matches command palette shortcut
  if (settingsStore.matchesShortcut(event, settingsStore.shortcuts.commandPalette)) {
    event.preventDefault()
    if (!props.visible) {
      // Emit open event to parent
      emit('close') // This will toggle the state in parent
    }
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<style scoped>
/* Modern Command Palette - Enhanced Design */
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

.section-header .el-icon {
  font-size: 16px;
  color: rgba(102, 126, 234, 0.6);
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
  margin-bottom: 6px;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.item-shortcut {
  margin-left: 12px;
}

.item-shortcut kbd {
  background: rgba(102, 126, 234, 0.1);
  color: rgba(102, 126, 234, 0.8);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid rgba(102, 126, 234, 0.2);
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

.module-color {
  border-radius: 50%;
  width: 32px;
  height: 32px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.module-badge {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  color: rgba(102, 126, 234, 0.9);
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.time-badge {
  color: #64748b;
  font-weight: 500;
}

/* Enhanced Empty and Default States */
.empty-state,
.default-state {
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

.recent-section {
  text-align: left;
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

/* Scrollbar Styling */
.results-container::-webkit-scrollbar {
  width: 6px;
}

.results-container::-webkit-scrollbar-track {
  background: rgba(102, 126, 234, 0.05);
  border-radius: 3px;
}

.results-container::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 3px;
}

.results-container::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}
</style>