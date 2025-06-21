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
/* Command Palette Overlay */
.command-palette-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
  z-index: 2000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
}

/* Main Palette Container */
.command-palette {
  width: 480px;
  max-width: 90vw;
  max-height: 70vh;
  background: var(--card-bg);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Search Container */
.search-container {
  position: relative;
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-subtle);
}

.search-icon {
  color: var(--text-muted);
  font-size: 18px;
  margin-right: 12px;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: var(--font-size-base);
  color: var(--text-primary);
  font-family: var(--font-family);
  line-height: 1.5;
}

.search-input::placeholder {
  color: var(--text-muted);
}

.search-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  margin-left: 12px;
}

/* Results Container */
.results-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  max-height: 400px;
}

/* Result Sections */
.result-section {
  margin-bottom: 16px;
}

.result-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px 4px 20px;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Result Items */
.result-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.15s ease;
  border-left: 3px solid transparent;
}

.result-item:hover,
.result-item.selected {
  background: var(--bg-elevated);
  border-left-color: var(--primary);
}

.result-item.selected {
  background: var(--primary-light);
}

.item-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
  font-size: 16px;
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
}

.task-priority {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  color: white;
}

.task-priority.priority-0 { background: var(--danger); }
.task-priority.priority-1 { background: var(--warning); }
.task-priority.priority-2 { background: #FADB14; color: #000; }
.task-priority.priority-3 { background: var(--success); }
.task-priority.priority-4 { background: var(--primary); }

.module-color {
  border-radius: 50%;
  border: 2px solid var(--border-default);
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  margin-bottom: 2px;
  line-height: var(--line-height-tight);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-description {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  line-height: var(--line-height-normal);
  margin-bottom: 4px;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.module-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: var(--font-weight-medium);
  color: rgba(0, 0, 0, 0.8);
}

.time-badge {
  font-size: 10px;
  color: var(--text-muted);
  padding: 2px 4px;
  background: var(--bg-elevated);
  border-radius: 4px;
}

.item-shortcut {
  margin-left: 12px;
  flex-shrink: 0;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 32px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.empty-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.empty-hint {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

/* Default State */
.default-state {
  padding: 8px 0;
}

.recent-section {
  margin-bottom: 0;
}

/* Footer */
.palette-footer {
  padding: 12px 20px;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-surface);
}

.footer-hints {
  display: flex;
  gap: 16px;
  align-items: center;
}

.hint-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

/* Keyboard Shortcuts */
kbd {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: 4px;
  font-size: 10px;
  font-family: var(--font-family);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  line-height: 1;
  min-height: 18px;
}

/* Scrollbar styling */
.results-container::-webkit-scrollbar {
  width: 6px;
}

.results-container::-webkit-scrollbar-track {
  background: transparent;
}

.results-container::-webkit-scrollbar-thumb {
  background: var(--border-default);
  border-radius: 3px;
}

.results-container::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>