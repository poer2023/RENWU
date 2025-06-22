<template>
  <div class="home-layout">
    <!-- Modern Canvas Layout - No Top Bar -->
    <div class="canvas-layout">
      <!-- Full Screen Canvas -->
      <main class="fullscreen-canvas">
        <!-- Risk Radar (Hidden by default, show on demand) -->
        <RiskRadar 
          v-if="showRiskRadar" 
          @view-task="handleViewRiskyTask" 
          style="position: absolute; top: 20px; right: 20px; z-index: 900;"
        />
        
        <!-- Main Canvas Component -->
        <StickyCanvas
          v-if="currentView === 'canvas' || currentView === 'island'"
          ref="stickyCanvasRef"
          :tasks="taskStore.tasks"
          :selected-task="selectedTask"
          :island-view="currentView === 'island'"
          :island-view-enabled="islandViewEnabled"
          :theme-islands="themeIslands"
          @select-task="handleTaskSelect"
          @open-task-details="handleOpenTaskDetails"
          @auto-arrange-complete="handleAutoArrangeComplete"
        />
        
        <!-- Timeline View Component -->
        <TimelineView
          v-if="currentView === 'timeline'"
          :tasks="taskStore.tasks"
          @task-click="handleTimelineTaskClick"
        />
        
        <!-- Empty state -->
        <div v-if="taskStore.tasks.length === 0" class="empty-state">
          <div class="empty-content">
            <div class="empty-icon">📁</div>
            <h2>欢迎使用 TaskWall</h2>
            <p>点击顶部洞察按钮，然后选择添加任务开始创建</p>
            <p class="shortcut-hint">或按 <kbd>Q</kbd> 快速添加</p>
          </div>
        </div>
        
      </main>
      
      <!-- Context Toolbar -->
      <ContextToolbar
        :visible="selectedTask && showContextToolbar"
        :position="contextToolbarPosition"
        @link-tasks="linkTasks"
        @generate-subtasks="generateSubtasksForSelected"
        @delete-task="deleteSelectedTask"
        @align-nodes="alignNodes"
      />
      
      
      <!-- Insight Drawer -->
      <InsightDrawer
        v-model:open="insightDrawerOpen"
        :workload-data="workloadData"
        :show-risk-radar="showRiskRadar"
        :show-debug-tab="advancedSettings.showDebugInfo"
        :current-view="currentView"
        :tasks="taskStore.tasks"
        @refresh-workload="refreshWorkloadAnalysis"
        @analyze-risks="analyzeRisks"
        @toggle-risk-radar="(value) => showRiskRadar = value"
        @open-settings="openSettings"
        @open-search="openGlobalSearch"
        @open-quick-add="openQuickAdd"
        @open-ai-assistant="openAIAssistant"
        @switch-view="switchView"
        @select-task="handleTaskSelect"
      >
        <template #debug-content>
          <DebugTaskList :tasks="taskStore.tasks" />
        </template>
      </InsightDrawer>
    </div>

    <!-- Task Details Popup -->
    <TaskDetailsPopup
      v-model:visible="detailsPopupVisible"
      :task="detailsTask"
      :position="popupPosition"
      @close="handleCloseDetails"
    />

    <!-- Quick Add Dialog -->
    <QuickAddDialog
      v-model="showQuickAdd"
      :modules="taskStore.modules"
      @created="handleQuickTaskCreated"
    />

    <!-- New Module Dialog -->
    <NewModuleDialog
      v-model="showNewModule"
      @created="handleModuleCreated"
    />

    <!-- Auto Arrange Dialog -->
    <AutoArrangeDialog
      v-model="showAutoArrangeDialog"
      @arrange="triggerAutoArrange"
    />

    <!-- Backup Dialog -->
    <BackupDialog v-model="showBackupDialog" />

    <!-- Settings Dialog -->
    <SettingsDialog v-model="showSettings" />

    <!-- Similar Tasks Dialog -->
    <SimilarTaskDialog
      v-model:visible="showSimilarTasksDialog"
      :new-task-title="taskOps.pendingTask.value?.title || ''"
      :new-task-description="taskOps.pendingTask.value?.description || ''"
      :similar-tasks="taskOps.similarTasksData.value?.similar_tasks || []"
      :suggestions="taskOps.similarTasksData.value?.suggestions || []"
      @cancel="handleSimilarTasksCancel"
      @ignore="handleSimilarTasksIgnore"
      @create="handleSimilarTasksCreate"
      @view-task="handleViewSimilarTask"
      @link-tasks="handleLinkSimilarTask"
    />

    <!-- Command Palette -->
    <CommandPalette
      :visible="showCommandPalette"
      @close="showCommandPalette = false"
      @select-task="handleCommandPaletteSelectTask"
      @select-module="handleCommandPaletteSelectModule"
      @execute-command="handleCommandPaletteExecuteCommand"
    />

    <!-- AI Parse Dialog -->
    <AIParseDialog v-model="showAIParseDialog" />
    
    <!-- AI Assistant Dialog -->
    <AIAssistantDialog v-model="showAIAssistantDialog" />
    
    <!-- Workload Analysis Dialog -->
    <WorkloadDialog v-model="showWorkloadDialog" />
    


    <!-- Export Dialog -->
    <ExportDialog
      v-model="showExportDialog"
      :modules="taskStore.modules"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElButton, ElInput, ElUpload, ElDialog, ElForm, ElFormItem, ElSelect, ElOption, ElTag, ElIcon, ElColorPicker, ElMessage, ElMessageBox, ElTabs, ElTabPane, ElRadioGroup, ElRadio, ElCheckbox, ElInputNumber, ElDropdown, ElDropdownMenu, ElDropdownItem, ElAlert } from 'element-plus'
import { Download, Setting, UploadFilled, Search, Menu, Grid, CollectionTag, Plus, Rank, Close, Lightning, MagicStick, Picture, Box, Check, CircleCheck, FolderOpened, Edit, Delete, ArrowDown } from '@element-plus/icons-vue'
import StickyCanvas from '@/components/StickyCanvas.vue'
import TaskDetailsPopup from '@/components/TaskDetailsPopup.vue'
import DebugTaskList from '@/components/DebugTaskList.vue'
import WorkloadSidebar from '@/components/WorkloadSidebar.vue'
import SimilarTaskDialog from '@/components/SimilarTaskDialog.vue'
import RiskRadar from '@/components/RiskRadar.vue'
import CommandPalette from '@/components/CommandPalette.vue'
import TimelineView from '@/components/TimelineView.vue'
import InsightDrawer from '@/components/InsightDrawer.vue'
import ContextToolbar from '@/components/ContextToolbar.vue'
import QuickAddDialog from '@/components/dialogs/QuickAddDialog.vue'
import NewModuleDialog from '@/components/dialogs/NewModuleDialog.vue'
import AutoArrangeDialog from '@/components/dialogs/AutoArrangeDialog.vue'
import BackupDialog from '@/components/dialogs/BackupDialog.vue'
import ExportDialog from '@/components/dialogs/ExportDialog.vue'
import SettingsDialog from '@/components/dialogs/SettingsDialog.vue'
import AIParseDialog from '@/components/dialogs/AIParseDialog.vue'
import AIAssistantDialog from '@/components/dialogs/AIAssistantDialog.vue'
import WorkloadDialog from '@/components/dialogs/WorkloadDialog.vue'
import { useTaskStore, type Task } from '@/stores/tasks'
import { useSettingsStore } from '@/stores/settings'
import { useKeyboard } from '@/composables/useKeyboard'
import { useDialogs } from '@/composables/dialogs/useDialogs'
import { useTaskOperations } from '@/composables/useTaskOperations'
import { useAIAnalysis } from '@/composables/useAIAnalysis'
import { useDataManagement } from '@/composables/useDataManagement'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'

const taskStore = useTaskStore()
const settingsStore = useSettingsStore()

// Composables
const taskOps = useTaskOperations()
const aiAnalysis = useAIAnalysis()
const dataManagement = useDataManagement()

// State
const selectedTask = ref<Task | null>(null)
const stickyCanvasRef = ref<InstanceType<typeof StickyCanvas>>()
const detailsTask = ref<Task | null>(null)
const detailsPopupVisible = ref(false)
const popupPosition = ref({ x: 0, y: 0 })
const showQuickAdd = ref(false)
const showNewModule = ref(false)
const showSettings = ref(false)
const quickText = ref('')
const taskInbox = ref<Partial<Task>[]>([])
const searchQuery = ref('')
const searchResults = ref<Task[]>([])
const searchInput = ref()
const showSimilarTasksDialog = ref(false)
const islandViewEnabled = ref(false)
const themeIslands = ref<any[]>([])
const islandViewLoading = ref(false)
const showCommandPalette = ref(false)
const showAIAssistantDialog = ref(false)
const showAIParseDialog = ref(false)
const showWorkloadDialog = ref(false)
const aiAssistantAction = ref('')
const aiAssistantContent = ref('')
const aiAssistantContext = ref('')
const aiAssistantResult = ref('')

// Modern UI State
const showContextToolbar = ref(false)
const contextToolbarPosition = ref({ top: '0px', left: '0px' })
const showAlignOptions = ref(false)
const timelineFilter = ref('all') // all, pending, completed
const selectedTasks = ref<number[]>([])
const insightDrawerOpen = ref(false)
const currentView = ref('canvas') // canvas, timeline, island
const showRiskRadar = ref(false)
const showBackupDialog = ref(false)
const showQuickTextDialog = ref(false)
const quickTextInput = ref('')
const showExportDialog = ref(false)
const exportFormat = ref('json')
const exportFilterModule = ref<number | null>(null)
const exportFilterPriority = ref<number | null>(null)


// AI Features settings
const aiFeatures = ref({
  textParsing: true,
  subtaskGeneration: true,
  similarityDetection: true,
  weeklyReports: true,
  riskAnalysis: true,
  themeIslands: true
})

// Export options
const exportOptions = ref({
  includeHistory: true,
  includeDependencies: true,
  includeModules: true
})

// Advanced settings
const advancedSettings = ref({
  enableAnimations: true,
  enableAutoLayout: true,
  enableKeyboardShortcuts: true,
  showDebugInfo: false,
  enableConsoleLogging: false,
  enableBetaFeatures: false
})

// 使用 dialogs composable
const dialogs = useDialogs()

const showAutoArrangeDialog = ref(false)

// Methods
function handleQuickTextKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    event.preventDefault()
    parseQuickText()
  }
}


function openSettings() {
  showSettings.value = true
}

function openGlobalSearch() {
  // 由于搜索功能已经集成到InsightDrawer中，这里不需要额外操作
  console.log('Search opened from top button')
}

function openQuickAdd() {
  showQuickAdd.value = true
}

function openAIAssistant() {
  showAIAssistantDialog.value = true
}


function handleOpenTaskDetails(task: Task, position: { x: number, y: number }) {
  detailsTask.value = task
  popupPosition.value = position
  detailsPopupVisible.value = true
}

function handleCloseDetails() {
  detailsPopupVisible.value = false
  detailsTask.value = null
}

async function parseQuickText() {
  if (!quickText.value.trim()) return
  
  try {
    const parsedTasks = await taskStore.parseTasksFromText(quickText.value)
    taskInbox.value = [...taskInbox.value, ...parsedTasks]
    quickText.value = ''
    ElMessage.success(`已解析 ${parsedTasks.length} 个任务`)
  } catch (error) {
    ElMessage.error('任务解析失败')
  }
}

async function handleImageUpload(file: any) {
  try {
    const text = await taskStore.extractTextFromImage(file.raw)
    quickText.value = text
    ElMessage.success('已从图片中提取文本')
  } catch (error) {
    ElMessage.error('从图片提取文本失败')
  }
}

async function createTaskFromInbox(task: Partial<Task>) {
  try {
    // Check for similar tasks before creating
    await checkSimilarTasksBeforeCreate(task)
  } catch (error) {
    ElMessage.error('创建任务失败')
  }
}

async function checkSimilarTasksBeforeCreate(task: Partial<Task>) {
  try {
    // Import the similarity detection function
    const { useSimilarityDetection } = await import('@/composables/useSimilarityDetection')
    const { findSimilarTasks: findSimilarTasksFn } = useSimilarityDetection()
    
    if (task.title) {
      const result = await findSimilarTasksFn(task.title, task.description || '')
      
      if (result.similar_tasks.length > 0) {
        // Show similar tasks dialog
        showSimilarTasksDialog.value = true
        taskOps.similarTasksData.value = result
        taskOps.pendingTask.value = task
        return
      }
    }
    
    // No similar tasks found, create directly
    await finalizeTaskCreation(task)
  } catch (error) {
    console.warn('Similarity check failed, creating task anyway:', error)
    await finalizeTaskCreation(task)
  }
}

async function finalizeTaskCreation(task: Partial<Task>) {
  await taskStore.createTask(task)
  
  // Remove from inbox if it was from inbox
  const index = taskInbox.value.indexOf(task)
  if (index > -1) {
    taskInbox.value.splice(index, 1)
  }
  
  // Force refresh tasks list
  await taskStore.fetchTasks()
  ElMessage.success('任务创建成功')
}

function removeFromInbox(index: number) {
  taskInbox.value.splice(index, 1)
}

async function createAllFromInbox() {
  try {
    for (const task of taskInbox.value) {
      await taskStore.createTask(task)
    }
    taskInbox.value = []
    ElMessage.success('所有任务已创建')
  } catch (error) {
    ElMessage.error('部分任务创建失败')
  }
}

// 处理快速添加任务创建
async function handleQuickTaskCreated(taskData: any) {
  try {
    // Check for similar tasks before creating
    await checkSimilarTasksBeforeCreate(taskData)
  } catch (error) {
    ElMessage.error('Failed to create task')
  }
}

// 处理模块创建
function handleModuleCreated(moduleData: { name: string; color: string }) {
  ElMessage.success('模块创建成功')
}

// Similar tasks dialog handlers
function handleSimilarTasksCancel() {
  showSimilarTasksDialog.value = false
  taskOps.pendingTask.value = null
  taskOps.similarTasksData.value = null
}

function handleSimilarTasksIgnore() {
  showSimilarTasksDialog.value = false
  if (taskOps.pendingTask.value) {
    finalizeTaskCreation(taskOps.pendingTask.value)
  }
  taskOps.pendingTask.value = null
  taskOps.similarTasksData.value = null
}

function handleSimilarTasksCreate() {
  showSimilarTasksDialog.value = false
  if (taskOps.pendingTask.value) {
    finalizeTaskCreation(taskOps.pendingTask.value)
  }
  taskOps.pendingTask.value = null
  taskOps.similarTasksData.value = null
}

function handleViewSimilarTask(task: any) {
  // Focus on the similar task in canvas
  const foundTask = taskStore.tasks.find(t => t.id === task.id)
  if (foundTask) {
    handleTaskSelect(foundTask)
    if (stickyCanvasRef.value) {
      stickyCanvasRef.value.focusOnTask(foundTask.id)
    }
  }
}

async function handleLinkSimilarTask(task: any) {
  // Create dependency relationship with the similar task
  if (taskOps.pendingTask.value) {
    try {
      // First create the new task
      const newTaskCreated = await taskStore.createTask(taskOps.pendingTask.value)
      
      // Then create dependency
      await taskStore.createDependency({
        from_task_id: task.id,
        to_task_id: newTaskCreated.id,
        dependency_type: 'relates'
      })
      
      showSimilarTasksDialog.value = false
      taskOps.pendingTask.value = null
      taskOps.similarTasksData.value = null
      
      // Remove from inbox if it was from inbox
      if (taskInbox.value.includes(taskOps.pendingTask.value)) {
        const index = taskInbox.value.indexOf(taskOps.pendingTask.value)
        if (index > -1) {
          taskInbox.value.splice(index, 1)
        }
      }
      
      // Force refresh tasks list
      await taskStore.fetchTasks()
      ElMessage.success('任务已创建并与相似任务建立关联')
    } catch (error) {
      console.error('Failed to link tasks:', error)
      ElMessage.error('建立关联失败')
    }
  }
}

function handleViewRiskyTask(task: any) {
  // Find the task in the store and focus on it
  const foundTask = taskStore.tasks.find(t => t.id === task.id)
  if (foundTask) {
    handleTaskSelect(foundTask)
    if (stickyCanvasRef.value) {
      stickyCanvasRef.value.focusOnTask(foundTask.id)
    }
    
    // Open task details popup
    const rect = { left: window.innerWidth / 2, bottom: window.innerHeight / 2 }
    const position = {
      x: rect.left,
      y: rect.bottom + 10
    }
    handleOpenTaskDetails(foundTask, position)
  }
}



async function saveSettings() {
  try {
    // Save additional settings to localStorage
    const additionalSettings = {
      aiFeatures: aiFeatures.value,
      exportOptions: exportOptions.value,
      advancedSettings: advancedSettings.value
    }
    localStorage.setItem('taskwall-additional-settings', JSON.stringify(additionalSettings))
    
    // Save settings to local storage
    settingsStore.saveSettings()
    
    // Save Gemini API key to backend if provided
    if (settingsStore.geminiApiKey && settingsStore.geminiApiKey.trim()) {
      await fetch('/api/settings/gemini_api_key', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          value: settingsStore.geminiApiKey
        })
      })
      console.log('Gemini API key saved to backend')
    }
    
    showSettings.value = false
    ElMessage.success('设置已保存')
  } catch (error) {
    console.error('Failed to save settings:', error)
    ElMessage.error('设置保存失败')
  }
}

function clearCache() {
  localStorage.removeItem('taskwall-settings')
  localStorage.removeItem('taskwall-additional-settings')
  ElMessage.success('缓存已清除，页面将在3秒后刷新')
  setTimeout(() => {
    window.location.reload()
  }, 3000)
}

function loadSettings() {
  settingsStore.loadSettings()
  
  // Load additional settings
  try {
    const saved = localStorage.getItem('taskwall-additional-settings')
    if (saved) {
      const settings = JSON.parse(saved)
      aiFeatures.value = { ...aiFeatures.value, ...settings.aiFeatures }
      exportOptions.value = { ...exportOptions.value, ...settings.exportOptions }
      advancedSettings.value = { ...advancedSettings.value, ...settings.advancedSettings }
    }
  } catch (error) {
    console.warn('Failed to load additional settings:', error)
  }
}

function triggerAutoArrange() {
  if (stickyCanvasRef.value) {
    stickyCanvasRef.value.triggerAutoArrange()
    showAutoArrangeDialog.value = false
  }
}

function handleAutoArrangeComplete() {
  ElMessage.success(`已完成${settingsStore.autoArrangeOptions.mode}排列`)
}

function getShortcutName(key: string): string {
  const names: { [key: string]: string } = {
    quickAdd: '快速添加',
    export: '导出',
    save: '保存',
    undo: '撤销',
    redo: '重做',
    selectAll: '全选',
    delete: '删除',
    duplicate: '复制',
    search: '搜索',
    zoomIn: '放大',
    zoomOut: '缩小',
    resetZoom: '重置缩放',
    autoArrange: '自动排列',
    toggleSidebar: '切换侧栏',
    newModule: '新建模块',
    settings: '设置'
  }
  return names[key] || key
}

// Search methods
function handleSearch(query: string) {
  if (!query.trim()) {
    searchResults.value = []
    return
  }

  const lowerQuery = query.toLowerCase()
  searchResults.value = taskStore.tasks.filter(task => 
    task.title?.toLowerCase().includes(lowerQuery) ||
    task.description?.toLowerCase().includes(lowerQuery)
  )
}

function selectFirstResult() {
  if (searchResults.value.length > 0) {
    const firstResult = searchResults.value[0]
    handleTaskSelect(firstResult)
    
    // Scroll to and highlight the task
    if (stickyCanvasRef.value) {
      stickyCanvasRef.value.focusOnTask(firstResult.id)
    }
    
    clearSearch()
  }
}

function clearSearch() {
  searchQuery.value = ''
  searchResults.value = []
}

function focusSearch() {
  if (searchInput.value) {
    searchInput.value.focus()
  }
}

// Command Palette handlers
function handleCommandPaletteSelectTask(task: Task) {
  handleTaskSelect(task)
  if (stickyCanvasRef.value) {
    stickyCanvasRef.value.focusOnTask(task.id)
  }
}

function handleCommandPaletteSelectModule(module: any) {
  // Filter tasks by module and focus on the first one
  const moduleTasks = taskStore.tasks.filter(task => task.module_id === module.id)
  if (moduleTasks.length > 0) {
    handleTaskSelect(moduleTasks[0])
    if (stickyCanvasRef.value) {
      stickyCanvasRef.value.focusOnTask(moduleTasks[0].id)
    }
  }
}

function handleCommandPaletteExecuteCommand(command: any) {
  switch (command.name) {
    case 'newTask':
      showQuickAdd.value = true
      break
    case 'newModule':
      showNewModule.value = true
      break
    case 'autoArrange':
      triggerAutoArrange()
      break
    case 'export':
      exportTasks()
      break
    case 'settings':
      showSettings.value = true
      break
    case 'toggleIsland':
      currentView.value = 'island'
      if (!islandViewEnabled.value) {
        toggleIslandView()
      }
      break
    case 'canvasView':
      currentView.value = 'canvas'
      if (islandViewEnabled.value) {
        islandViewEnabled.value = false
        themeIslands.value = []
        if (stickyCanvasRef.value) {
          stickyCanvasRef.value.exitIslandView()
        }
      }
      break
    case 'timelineView':
      currentView.value = 'timeline'
      if (islandViewEnabled.value) {
        islandViewEnabled.value = false
        themeIslands.value = []
        if (stickyCanvasRef.value) {
          stickyCanvasRef.value.exitIslandView()
        }
      }
      break
    case 'weeklyReport':
      generateWeeklyReport()
      break
    case 'riskAnalysis':
      analyzeRisks()
      break
    case 'workloadAnalysis':
      refreshWorkloadAnalysis()
      break
    case 'resetZoom':
      settingsStore.resetZoom()
      break
    case 'zoomIn':
      settingsStore.zoomIn()
      break
    case 'zoomOut':
      settingsStore.zoomOut()
      break
    case 'selectAll':
      selectAllTasks()
      break
    case 'toggleGrid':
      settingsStore.toggleGrid()
      break
    case 'toggleSidebar':
      settingsStore.toggleSidebar()
      break
    case 'backup':
      backupData()
      break
    case 'aiParse':
      showAIParseDialog.value = true
      break
    case 'search':
      showCommandPalette.value = true
      break
    case 'focusLatest':
      if (stickyCanvasRef.value) {
        stickyCanvasRef.value.focusOnLatestTask()
        ElMessage.success('已定位到最新任务')
      }
      break
    default:
      console.warn('Unknown command:', command.name)
  }
}

async function generateWeeklyReport() {
  try {
    const response = await fetch('/api/ai/weekly-report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        // Use default dates (last 7 days)
      })
    })
    
    const result = await response.json()
    
    if (result.success) {
      // Create and download the report
      const blob = new Blob([result.report], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `weekly-report-${new Date().toISOString().split('T')[0]}.md`
      a.click()
      URL.revokeObjectURL(url)
      
      ElMessage.success('周报已生成并下载！')
    } else {
      throw new Error(result.error || 'Failed to generate report')
    }
  } catch (error) {
    console.error('Weekly report generation failed:', error)
    ElMessage.error('周报生成失败')
  }
}

async function toggleIslandView() {
  islandViewEnabled.value = !islandViewEnabled.value
  
  if (islandViewEnabled.value) {
    await loadThemeIslands()
  } else {
    themeIslands.value = []
    // Exit island view in canvas
    if (stickyCanvasRef.value) {
      stickyCanvasRef.value.exitIslandView()
    }
  }
}

async function loadThemeIslands() {
  islandViewLoading.value = true
  try {
    const response = await fetch('/api/ai/theme-islands', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        // Use all tasks by default
      })
    })
    
    const result = await response.json()
    
    if (result.success) {
      themeIslands.value = result.islands
      ElMessage.success(`发现 ${result.islands.length} 个主题岛`)
      
      // Apply island layout to canvas
      if (stickyCanvasRef.value) {
        stickyCanvasRef.value.applyIslandLayout(result.islands)
      }
    } else {
      throw new Error(result.error || 'Failed to create theme islands')
    }
  } catch (error) {
    console.error('Theme island creation failed:', error)
    ElMessage.error('主题岛创建失败')
  } finally {
    islandViewLoading.value = false
  }
}

async function exportTasks() {
  showExportDialog.value = true
}

async function executeExport() {
  try {
    let endpoint = '/api/export/json'
    let mimeType = 'application/json'
    let fileExtension = 'json'
    
    // Determine export format and endpoint
    switch (exportFormat.value) {
      case 'markdown':
        endpoint = '/api/export/markdown'
        mimeType = 'text/markdown'
        fileExtension = 'md'
        break
      case 'csv':
        endpoint = '/api/export/csv'
        mimeType = 'text/csv'
        fileExtension = 'csv'
        break
      case 'excel':
        endpoint = '/api/export/excel'
        mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        fileExtension = 'xlsx'
        break
      case 'pdf':
        endpoint = '/api/export/pdf'
        mimeType = 'application/pdf'
        fileExtension = 'pdf'
        break
      default: // JSON
        break
    }
    
    // Build query parameters based on export options
    const params = new URLSearchParams()
    if (!exportOptions.value.includeHistory) params.append('exclude_history', 'true')
    if (!exportOptions.value.includeDependencies) params.append('exclude_dependencies', 'true')
    if (!exportOptions.value.includeModules) params.append('exclude_modules', 'true')
    if (exportFilterModule.value) params.append('module_id', exportFilterModule.value.toString())
    if (exportFilterPriority.value !== null) params.append('priority', exportFilterPriority.value.toString())
    
    const fullEndpoint = params.toString() ? `${endpoint}?${params.toString()}` : endpoint
    
    const response = await fetch(fullEndpoint)
    
    if (!response.ok) {
      throw new Error(`Export failed with status ${response.status}`)
    }
    
    let blob: Blob
    let filename: string
    
    if (exportFormat.value === 'json') {
      const data = await response.json()
      blob = new Blob([JSON.stringify(data, null, 2)], { type: mimeType })
      filename = `taskwall-export-${new Date().toISOString().split('T')[0]}.${fileExtension}`
    } else if (exportFormat.value === 'markdown') {
      const result = await response.json()
      blob = new Blob([result.content], { type: mimeType })
      filename = result.filename || `taskwall-export-${new Date().toISOString().split('T')[0]}.${fileExtension}`
    } else {
      // For binary formats (Excel, PDF) or text formats (CSV)
      blob = await response.blob()
      filename = `taskwall-export-${new Date().toISOString().split('T')[0]}.${fileExtension}`
    }
    
    // Download file
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
    
    showExportDialog.value = false
    ElMessage.success(`任务已导出为${exportFormat.value.toUpperCase()}格式`)
  } catch (error) {
    console.error('Export failed:', error)
    ElMessage.error('导出失败')
  }
}

// Backup management functions


// Setup keyboard shortcuts
useKeyboard([
  {
    shortcut: 'quickAdd',
    action: () => { showQuickAdd.value = true },
    description: '打开快速添加对话框'
  },
  {
    shortcut: 'export',
    action: () => exportTasks(),
    description: '导出任务数据'
  },
  {
    shortcut: 'autoArrange',
    action: () => triggerAutoArrange(),
    description: '自动排列任务'
  },
  {
    shortcut: 'settings',
    action: () => { showSettings.value = true },
    description: '打开设置对话框'
  },
  {
    shortcut: 'newModule',
    action: () => { showNewModule.value = true },
    description: '创建新模块'
  },
  {
    shortcut: 'toggleSidebar',
    action: () => settingsStore.toggleSidebar(),
    description: '切换侧边栏显示'
  },
  {
    shortcut: 'search',
    action: () => focusSearch(),
    description: '全局搜索任务'
  },
  {
    shortcut: 'commandPalette',
    action: () => { showCommandPalette.value = true },
    description: 'Command Palette 全局搜索'
  }
])

onMounted(async () => {
  console.log('Home: Starting to fetch data...')
  
  await taskStore.fetchTasks()
  console.log('Home: Tasks fetched, count:', taskStore.tasks.length)
  console.log('Home: Tasks data:', taskStore.tasks)
  
  await taskStore.fetchModules()
  console.log('Home: Modules fetched, count:', taskStore.modules.length)
  
  await taskStore.fetchDependencies()
  loadSettings()
  
  // Auto-detect platform for keyboard shortcuts
  settingsStore.detectPlatform()
  
  // Create default module if none exist
  if (taskStore.modules.length === 0) {
    await taskStore.createModule({ name: '通用', color: '#FFE58F' })
  }
  
  console.log('Home: All data loaded, final tasks count:', taskStore.tasks.length)
  
  // Load initial workload analysis
  await refreshWorkloadAnalysis()
  
  // Setup keyboard shortcuts
  setupKeyboardShortcuts()
})


function triggerImageUpload() {
  // Create a hidden file input
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) {
      handleImageUpload({ raw: file })
    }
  }
  input.click()
}

// View Switcher Functions
function switchView() {
  const views = ['canvas', 'timeline', 'island']
  const currentIndex = views.indexOf(currentView.value)
  const nextIndex = (currentIndex + 1) % views.length
  currentView.value = views[nextIndex]
  
  // Execute view switching logic
  switch (currentView.value) {
    case 'canvas':
      // Default canvas view - exit island view if needed
      if (islandViewEnabled.value) {
        islandViewEnabled.value = false
        themeIslands.value = []
        if (stickyCanvasRef.value) {
          stickyCanvasRef.value.exitIslandView()
        }
      }
      break
    case 'timeline':
      // Timeline view is now implemented - exit island view if needed
      if (islandViewEnabled.value) {
        islandViewEnabled.value = false
        themeIslands.value = []
        if (stickyCanvasRef.value) {
          stickyCanvasRef.value.exitIslandView()
        }
      }
      break
    case 'island':
      // Switch to island view
      if (!islandViewEnabled.value) {
        toggleIslandView()
      }
      break
  }
}

function getCurrentViewIcon() {
  switch (currentView.value) {
    case 'canvas': return '🗺️'
    case 'timeline': return '📅'
    case 'island': return '🏝️'
    default: return '🗺️'
  }
}

function getViewSwitcherTitle() {
  switch (currentView.value) {
    case 'canvas': return '切换到时间线视图'
    case 'timeline': return '切换到主题岛视图'
    case 'island': return '切换到画布视图'
    default: return '切换视图'
  }
}

// Workload Data
const workloadData = computed(() => {
  if (!aiAnalysis.workloadAnalysis.value) return null
  
  const percentage = aiAnalysis.workloadAnalysis.value?.workload_percentage
  const hours = aiAnalysis.workloadAnalysis.value?.total_hours
  
  return {
    totalHours: typeof hours === 'number' && isFinite(hours) ? Math.round(hours * 10) / 10 : 0,
    workloadPercentage: typeof percentage === 'number' && isFinite(percentage) ? Math.round(percentage) : 0,
    tasksCount: aiAnalysis.workloadAnalysis.value?.tasks_count || 0,
    analysisDate: aiAnalysis.workloadAnalysis.value?.analysis_date || new Date().toISOString().split('T')[0]
  }
})

function getTimelineEmptyMessage() {
  switch (timelineFilter.value) {
    case 'pending': return '暂无进行中的任务'
    case 'completed': return '暂无已完成的任务'
    default: return '暂无任务'
  }
}

function formatTimelineDate(dateStr: string) {
  if (!dateStr) return '未知时间'
  
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    return '今天 ' + date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } else if (days === 1) {
    return '昨天 ' + date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } else if (days <= 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }
}

function getTimelineItemClass(task: any) {
  const classes = ['timeline-item']
  
  if (task.status === 'completed') {
    classes.push('completed')
  } else if (task.urgency <= 1) {
    classes.push('high-priority')
  }
  
  return classes
}

function handleTimelineTaskClick(task: any) {
  selectedTask.value = task
  handleOpenTaskDetails(task)
}

function getTaskColor(task: any) {
  if (task.status === 'completed') return '#52c41a'
  
  switch (task.urgency) {
    case 0: return '#ff4d4f' // P0 Critical - Red
    case 1: return '#fa8c16' // P1 High - Orange  
    case 2: return '#1890ff' // P2 Medium - Blue
    case 3: return '#52c41a' // P3 Low - Green
    case 4: return '#8c8c8c' // P4 Backlog - Gray
    default: return '#1890ff'
  }
}

function getPriorityClass(urgency: number) {
  switch (urgency) {
    case 0: return 'priority-critical'
    case 1: return 'priority-high'
    case 2: return 'priority-medium'
    case 3: return 'priority-low'
    case 4: return 'priority-backlog'
    default: return 'priority-medium'
  }
}

function getPriorityText(urgency: number) {
  switch (urgency) {
    case 0: return 'P0'
    case 1: return 'P1'
    case 2: return 'P2'
    case 3: return 'P3'
    case 4: return 'P4'
    default: return 'P2'
  }
}

function getStatusText(status: string) {
  switch (status) {
    case 'pending': return '待处理'
    case 'in_progress': return '进行中'
    case 'completed': return '已完成'
    case 'cancelled': return '已取消'
    default: return '未知'
  }
}

function getModuleName(moduleId: number) {
  const module = taskStore.modules.find(m => m.id === moduleId)
  return module ? module.name : '未分类'
}

// Context Toolbar Functions
function updateContextToolbar() {
  if (!selectedTask.value) {
    showContextToolbar.value = false
    return
  }
  
  // Position the toolbar above the selected task
  // This would need integration with StickyCanvas to get actual position
  showContextToolbar.value = true
  contextToolbarPosition.value = {
    top: '100px', // TODO: Calculate based on task position
    left: '200px'
  }
}

function linkTasks() {
  if (!selectedTask.value) {
    ElMessage.warning('请先选择一个任务')
    return
  }
  
  // Enter connection mode
  ElMessage.info('连线模式已激活，点击另一个任务创建依赖关系')
  
  // Trigger connection mode in StickyCanvas
  if (stickyCanvasRef.value) {
    stickyCanvasRef.value.enterConnectionMode(selectedTask.value.id)
  }
}

function alignNodes(direction: string) {
  ElMessage.info(`${direction}对齐功能开发中...`)
  showAlignOptions.value = false
  // TODO: Implement node alignment
}

// Quick Text Functions
async function parseQuickTextInput() {
  if (!quickTextInput.value.trim()) return
  
  try {
    const parsedTasks = await taskStore.parseTasksFromText(quickTextInput.value)
    
    // Add to inbox for review
    taskInbox.value = [...taskInbox.value, ...parsedTasks]
    
    // Clear input and close dialog
    quickTextInput.value = ''
    showQuickTextDialog.value = false
    
    ElMessage.success(`已解析 ${parsedTasks.length} 个任务到收件箱`)
    
    // Show inbox in a notification or mini-panel
    showInboxNotification(parsedTasks)
  } catch (error) {
    ElMessage.error('文本解析失败')
  }
}

function showInboxNotification(tasks: any[]) {
  // Show a temporary notification with parsed tasks
  ElMessage({
    message: `解析完成！点击右下角 + 按钮查看收件箱中的 ${tasks.length} 个任务`,
    type: 'success',
    duration: 5000,
    showClose: true
  })
}

// Insight Drawer Functions
function toggleInsightDrawer() {
  insightDrawerOpen.value = !insightDrawerOpen.value
}

// Additional Command Functions
function selectAllTasks() {
  // Select all visible tasks
  const visibleTasks = taskStore.tasks
  selectedTasks.value = visibleTasks.map(task => task.id)
  ElMessage.success(`已选择 ${visibleTasks.length} 个任务`)
}

async function backupData() {
  try {
    const response = await fetch('/api/backup', { method: 'POST' })
    if (response.ok) {
      ElMessage.success('数据备份成功')
    } else {
      throw new Error('备份失败')
    }
  } catch (error) {
    ElMessage.error('数据备份失败')
    console.error('Backup error:', error)
  }
}

// Watch for selected task changes
function handleTaskSelect(task: Task | null) {
  selectedTask.value = task
  taskStore.selectTask(task)
  updateContextToolbar()
}

// Global Keyboard Shortcuts
function setupKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Command Palette
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      showCommandPalette.value = true
    }
    
    // Quick Add
    if (e.key === 'q' || e.key === 'Q') {
      if (!e.target || (e.target as HTMLElement).tagName !== 'INPUT') {
        e.preventDefault()
        showQuickAdd.value = true
      }
    }
    
    // 空格键定位到最新任务
    if (e.key === ' ' || e.key === 'Space') {
      // 检查是否在输入框中
      const target = e.target as HTMLElement
      if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA' && !target.contentEditable) {
        e.preventDefault()
        if (stickyCanvasRef.value) {
          stickyCanvasRef.value.focusOnLatestTask()
          ElMessage.success('已定位到最新任务')
        }
      }
    }
    
    // Toggle Insight Drawer
    if ((e.metaKey || e.ctrlKey) && e.key === 'i') {
      e.preventDefault()
      toggleInsightDrawer()
    }
    
    // View Switching
    if ((e.metaKey || e.ctrlKey) && ['1', '2', '3'].includes(e.key)) {
      e.preventDefault()
      const views = ['canvas', 'timeline', 'island']
      currentView.value = views[parseInt(e.key) - 1]
    }
    
    // Global Quick Delete - 只有在明确的删除模式下才启用
    // Shift + Delete 进入删除模式
    if (e.shiftKey && e.key === 'Delete' && selectedTask.value) {
      const target = e.target as HTMLElement
      if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA' && !target.contentEditable) {
        e.preventDefault()
        quickDeleteSelectedTask()
      }
    }
    
    // Global Undo - Ctrl/Cmd + Z 撤回删除
    if ((e.metaKey || e.ctrlKey) && e.key === 'z' && taskStore.canUndo()) {
      const target = e.target as HTMLElement
      if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA' && !target.contentEditable) {
        e.preventDefault()
        handleUndoDelete()
      }
    }
    
    // ESC to close things
    if (e.key === 'Escape') {
      showAlignOptions.value = false
      showCommandPalette.value = false
    }
  })
}

// AI Assistant functions
async function executeAIAssistantDialog() {
  try {
    const result = await taskStore.executeAIAssistant(
      aiAssistantAction.value,
      aiAssistantContent.value,
      aiAssistantContext.value
    )
    aiAssistantResult.value = result
    ElMessage.success('AI功能执行成功！')
  } catch (error) {
    console.error('AI assistant failed:', error)
    ElMessage.error('AI功能执行失败')
  }
}

function copyAIResult() {
  navigator.clipboard.writeText(aiAssistantResult.value).then(() => {
    ElMessage.success('结果已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// Risk analysis function
async function analyzeRisks() {
  try {
    const response = await fetch('/api/ai/risk-analysis', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        // Use all tasks by default
      })
    })
    
    const result = await response.json()
    
    if (result.success) {
      // Show risk analysis results
      const riskMessage = `风险分析完成！\n\n高风险任务: ${result.risky_tasks.length} 个\n\n建议:\n${result.suggestions.join('\n')}`
      await ElMessageBox.alert(riskMessage, '风险分析结果', {
        confirmButtonText: '确定',
        type: 'warning'
      })
    } else {
      throw new Error(result.error || 'Risk analysis failed')
    }
  } catch (error) {
    console.error('Risk analysis failed:', error)
    ElMessage.error('风险分析失败')
  }
}

// Workload analysis functions
async function showWorkloadAnalysis() {
  try {
    await refreshWorkloadAnalysis()
    showWorkloadDialog.value = true
  } catch (error) {
    ElMessage.error('工作量分析加载失败')
  }
}

async function refreshWorkloadAnalysis() {
  try {
          const response = await fetch('/api/ai/v3/workload/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        date: new Date().toISOString().split('T')[0]
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const result = await response.json()
    
    if (result.success) {
      // Use the aiAnalysis composable for workload analysis
      await aiAnalysis.refreshWorkloadAnalysis()
    } else {
      throw new Error(result.error || 'Workload analysis failed')
    }
  } catch (error) {
    console.error('Workload analysis failed:', error)
    // 提供默认的工作负载数据，避免显示错误
    // 使用aiAnalysis composable管理工作负载数据
    // aiAnalysis会自动处理错误状态
    ElMessage.error('工作量分析失败，显示默认数据')
  }
}

function getWorkloadColor(percentage: number): string {
  // 确保percentage是有效数字
  const safePercentage = typeof percentage === 'number' && isFinite(percentage) ? percentage : 0
  if (safePercentage <= 70) return 'workload-green'
  if (safePercentage <= 90) return 'workload-yellow'
  return 'workload-red'
}

function getWorkloadMessage(level: string): string {
  switch (level) {
    case 'green': return '工作量正常，时间安排合理'
    case 'yellow': return '工作量较高，建议优化任务安排'
    case 'red': return '工作量过载，存在时间冲突风险'
    default: return '工作量分析'
  }
}

function getWorkloadAlertType(level: string): string {
  switch (level) {
    case 'green': return 'success'
    case 'yellow': return 'warning'
    case 'red': return 'error'
    default: return 'info'
  }
}

// Additional functions for new UI
function toggleLeftDrawer() {
  leftDrawerVisible.value = !leftDrawerVisible.value
}

function handleModuleClick(module: any) {
  // Filter tasks by module and focus on the first one
  const moduleTasks = taskStore.tasks.filter(task => task.module_id === module.id)
  if (moduleTasks.length > 0) {
    handleTaskSelect(moduleTasks[0])
    if (stickyCanvasRef.value) {
      stickyCanvasRef.value.focusOnTask(moduleTasks[0].id)
    }
  }
}

function editSelectedTask() {
  if (selectedTask.value) {
    // Open task details popup for editing
    const rect = { left: window.innerWidth / 2, bottom: window.innerHeight / 2 }
    const position = {
      x: rect.left,
      y: rect.bottom + 10
    }
    handleOpenTaskDetails(selectedTask.value, position)
  }
}

async function generateSubtasksForSelected() {
  if (selectedTask.value) {
    try {
      const subtasks = await taskStore.generateTaskSubtasks(
        selectedTask.value.title,
        selectedTask.value.description,
        5
      )
      
      const createdSubtasks = []
      
      // Create all subtasks first
      for (const subtask of subtasks) {
        const createdTask = await taskStore.createTask({
          ...subtask,
          parent_id: selectedTask.value.id,
          module_id: selectedTask.value.module_id
        })
        createdSubtasks.push(createdTask)
      }
      
      // Create dependencies: parent -> first subtask, and chain subtasks
      if (createdSubtasks.length > 0) {
        // Parent depends on first subtask
        await taskStore.createDependency({
          from_task_id: selectedTask.value.id,
          to_task_id: createdSubtasks[0].id,
          dependency_type: 'subtask'
        })
        
        // Chain subtasks (each depends on the previous one)
        for (let i = 1; i < createdSubtasks.length; i++) {
          await taskStore.createDependency({
            from_task_id: createdSubtasks[i - 1].id,
            to_task_id: createdSubtasks[i].id,
            dependency_type: 'subtask'
          })
        }
      }
      
      await taskStore.fetchTasks()
      await taskStore.fetchDependencies()
      
      ElMessage.success(
        `已为 "${selectedTask.value.title}" 生成 ${subtasks.length} 个子任务并建立依赖关系`
      )
    } catch (error) {
      console.error('Failed to generate subtasks:', error)
      ElMessage.error('生成子任务失败')
    }
  }
}

async function deleteSelectedTask() {
  if (selectedTask.value) {
    try {
      await ElMessageBox.confirm(
        '确定要删除这个任务吗？',
        '删除任务',
        {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
      
      await taskStore.deleteTask(selectedTask.value.id)
      handleTaskSelect(null)
      ElMessage.success('任务已删除')
    } catch (error) {
      if (error !== 'cancel') {
        console.error('Failed to delete task:', error)
        ElMessage.error('删除任务失败')
      }
    }
  }
}

// 快捷删除选中任务 - 无确认
async function quickDeleteSelectedTask() {
  if (selectedTask.value) {
    try {
      console.log('Quick deleting task:', selectedTask.value.id)
      await taskStore.deleteTask(selectedTask.value.id)
      handleTaskSelect(null)
      showUndoDeleteMessage()
    } catch (error) {
      console.error('Failed to delete task:', error)
      ElMessage.error('删除任务失败')
    }
  }
}

// 显示撤回删除消息
function showUndoDeleteMessage() {
  ElMessage({
    type: 'success',
    duration: 5000,
    showClose: true,
    dangerouslyUseHTMLString: true,
    message: `
      <div style="display: flex; align-items: center; justify-content: space-between; width: 200px;">
        <span>任务已删除</span>
        <button 
          onclick="window.handleUndoDelete()"
          style="margin-left: 12px; padding: 4px 8px; background: #409EFF; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;"
        >
          撤回 (Ctrl+Z)
        </button>
      </div>
    `
  })
}

// 处理撤回删除
async function handleUndoDelete() {
  try {
    const recreatedTask = await taskStore.undoDeleteTask()
    ElMessage.success(`任务 "${recreatedTask.title}" 已恢复`)
    // 选中恢复的任务
    handleTaskSelect(recreatedTask)
  } catch (error) {
    console.error('Failed to undo delete:', error)
    ElMessage.error('撤回失败')
  }
}

// 将撤回函数暴露到全局，供消息中的按钮调用
if (typeof window !== 'undefined') {
  (window as any).handleUndoDelete = handleUndoDelete
}

function getPriorityName(urgency: number): string {
  const names = {
    0: '紧急',
    1: '高',
    2: '中',
    3: '低',
    4: '待办'
  }
  return names[urgency as keyof typeof names] || '中'
}

function formatFullDate(date: string): string {
  return new Date(date).toLocaleString('zh-CN')
}

// Export helper functions
function getFilteredTaskCount(): number {
  let filteredTasks = taskStore.tasks
  
  if (exportFilterModule.value) {
    filteredTasks = filteredTasks.filter(task => task.module_id === exportFilterModule.value)
  }
  
  if (exportFilterPriority.value !== null) {
    filteredTasks = filteredTasks.filter(task => task.urgency === exportFilterPriority.value)
  }
  
  return filteredTasks.length
}

function getEstimatedFileSize(): string {
  const taskCount = getFilteredTaskCount()
  let estimatedSize = 0
  
  // Base task data size estimation
  estimatedSize += taskCount * 500 // ~500 bytes per task
  
  if (exportOptions.value.includeHistory) {
    estimatedSize += taskCount * 200 // ~200 bytes per history record
  }
  
  if (exportOptions.value.includeDependencies) {
    estimatedSize += taskStore.dependencies.length * 100 // ~100 bytes per dependency
  }
  
  if (exportOptions.value.includeModules) {
    estimatedSize += taskStore.modules.length * 150 // ~150 bytes per module
  }
  
  // Format size estimation based on export format
  switch (exportFormat.value) {
    case 'json':
      estimatedSize *= 1.2 // JSON formatting overhead
      break
    case 'markdown':
      estimatedSize *= 1.5 // Markdown formatting
      break
    case 'csv':
      estimatedSize *= 0.8 // CSV is more compact
      break
    case 'excel':
      estimatedSize *= 2.0 // Excel has more overhead
      break
    case 'pdf':
      estimatedSize *= 3.0 // PDF has significant overhead
      break
  }
  
  // Convert to human readable format
  if (estimatedSize < 1024) {
    return `${Math.round(estimatedSize)} B`
  } else if (estimatedSize < 1024 * 1024) {
    return `${Math.round(estimatedSize / 1024)} KB`
  } else {
    return `${Math.round(estimatedSize / (1024 * 1024))} MB`
  }
}
</script>

<style scoped>
.home-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-base);
  color: var(--text-primary);
  overflow: hidden;
}

.canvas-layout {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.fullscreen-canvas {
  flex: 1;
  position: relative;
  overflow: hidden;
  width: 100%;
  height: 100%;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-default);
  box-shadow: var(--shadow-sm);
  z-index: 100;
  backdrop-filter: blur(8px);
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.top-bar-center {
  display: flex;
  align-items: center;
}

.app-title {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  font-family: var(--font-family);
}

.top-bar-right {
  display: flex;
  gap: 8px;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.capture-panel {
  width: 280px;
  background: var(--bg-surface);
  border-right: 1px solid var(--border-default);
  padding: 16px;
  overflow-y: auto;
}

.panel-section {
  margin-bottom: 24px;
}

.panel-section h3 {
  margin: 0 0 12px 0;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  font-family: var(--font-family);
}

.w-full {
  width: 100%;
}

.mt-2 {
  margin-top: 8px;
}

.inbox-tasks {
  max-height: 200px;
  overflow-y: auto;
}

.inbox-task {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  margin-bottom: 8px;
  background: var(--bg-elevated);
  transition: all 0.2s ease;
}

.inbox-task:hover {
  box-shadow: var(--shadow-sm);
  border-color: var(--border-default);
}

.task-info {
  flex: 1;
}

.task-info strong {
  font-size: 12px;
  display: block;
  margin-bottom: 4px;
}

.task-info p {
  font-size: 11px;
  color: var(--text-secondary);
  margin: 0 0 4px 0;
}

.task-actions {
  display: flex;
  gap: 4px;
}

.module-list {
  margin-bottom: 8px;
}

.module-item {
  padding: 6px 10px;
  border-radius: 12px;
  font-size: var(--font-size-xs);
  margin-bottom: 4px;
  color: var(--text-primary);
  border: 1px solid var(--border-subtle);
  transition: all 0.2s ease;
  cursor: pointer;
}

.module-item:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.canvas-area {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.empty-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: var(--text-muted);
}

.empty-state h2 {
  margin: 0 0 8px 0;
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-secondary);
}

.empty-state p {
  margin: 0;
  font-size: var(--font-size-sm);
}

/* Element Plus customizations */
:deep(.el-upload-dragger) {
  width: 100%;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

:deep(.el-upload__text) {
  font-size: 12px;
}

:deep(.el-button--small) {
  font-size: 12px;
}

/* Shortcuts list */
.shortcuts-list {
  max-height: 300px;
  overflow-y: auto;
}

.shortcut-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-subtle);
}

.shortcut-name {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

/* Form row for side-by-side inputs */
.form-row {
  display: flex;
  gap: 16px;
}

.form-item-half {
  flex: 1;
}

/* Auto arrange mode options */
:deep(.el-select-dropdown__item) {
  height: auto !important;
  padding: 12px 20px !important;
  white-space: normal !important;
}

/* Modern TopBar Styles */
.modern-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 24px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-default);
  box-shadow: var(--shadow-sm);
  z-index: 100;
  backdrop-filter: blur(8px);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.drawer-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.drawer-toggle:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.app-brand {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.brand-title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  line-height: 1;
}

.brand-subtitle {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  line-height: 1;
}

.topbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
  max-width: 480px;
  margin: 0 40px;
}

.global-search {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px 16px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s ease;
  gap: 12px;
}

.global-search:hover {
  border-color: var(--border-default);
  box-shadow: var(--shadow-sm);
}

.search-icon {
  color: var(--text-muted);
  font-size: 16px;
  flex-shrink: 0;
}

.search-placeholder {
  flex: 1;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

.search-shortcut {
  display: flex;
  align-items: center;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.view-tabs {
  display: flex;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: 4px;
  gap: 2px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: none;
  border-radius: calc(var(--radius-md) - 2px);
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  background: var(--bg-base);
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--primary);
  color: white;
  box-shadow: var(--shadow-sm);
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--border-default);
  color: var(--text-primary);
  transform: translateY(-1px);
}

.action-btn.primary {
  background: var(--primary);
  color: white;
}

.action-btn.primary:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
}

/* Modern Left Drawer */
.left-drawer {
  width: 320px;
  background: var(--bg-surface);
  border-right: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px 24px;
  border-bottom: 1px solid var(--border-subtle);
}

.drawer-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.drawer-content {
  flex: 1;
  padding: 0 24px 24px 24px;
  overflow-y: auto;
}

.drawer-section {
  margin-bottom: 32px;
}

.drawer-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.section-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: var(--primary);
  color: white;
  border-radius: 10px;
  font-size: 11px;
  font-weight: var(--font-weight-medium);
  margin-left: auto;
}

.section-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn-full {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: var(--font-size-sm);
}

/* Right Drawer */
.right-drawer {
  width: 300px;
  background: var(--bg-surface);
  border-left: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.task-preview {
  padding: 20px;
  border-bottom: 1px solid var(--border-subtle);
}

.task-priority {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  color: white;
  margin-bottom: 12px;
}

.task-priority.priority-0 { background: var(--danger); }
.task-priority.priority-1 { background: var(--warning); }
.task-priority.priority-2 { background: #FADB14; color: #000; }
.task-priority.priority-3 { background: var(--success); }
.task-priority.priority-4 { background: var(--primary); }

.task-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 8px 0;
  line-height: var(--line-height-tight);
}

.task-description {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: var(--line-height-normal);
  margin: 0;
}

.task-properties {
  padding: 20px;
  border-bottom: 1px solid var(--border-subtle);
}

.property-group {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.property-group:last-child {
  margin-bottom: 0;
}

.property-label {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  font-weight: var(--font-weight-medium);
}

.property-value {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.priority-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: white;
}

.priority-badge.priority-badge-0 { background: var(--danger); }
.priority-badge.priority-badge-1 { background: var(--warning); }
.priority-badge.priority-badge-2 { background: #FADB14; color: #000; }
.priority-badge.priority-badge-3 { background: var(--success); }
.priority-badge.priority-badge-4 { background: var(--primary); }

.module-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: rgba(0, 0, 0, 0.8);
}

.text-secondary {
  color: var(--text-secondary) !important;
}

.task-actions-panel {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Top bar is now visible and functional */

/* Backup Dialog Styles */
.backup-status {
  padding: 16px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
}

.backup-history {
  max-height: 300px;
  overflow-y: auto;
}

.empty-history {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  transition: all 0.2s ease;
}

.history-item:hover {
  box-shadow: var(--shadow-sm);
  border-color: var(--border-default);
}

.backup-info {
  flex: 1;
}

.backup-info strong {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  display: block;
  margin-bottom: 4px;
}

.backup-date {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  margin: 0;
}

.backup-actions {
  display: flex;
  gap: 8px;
}

/* Enhanced Settings Styles */
.ai-features-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-features-list .el-checkbox {
  margin-bottom: 4px;
}

.ai-features-list small {
  display: block;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  margin-left: 24px;
  margin-bottom: 8px;
}

.export-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.data-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.stat-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--primary);
}

.data-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.experimental-features small {
  display: block;
  color: var(--warning);
  font-size: var(--font-size-xs);
  margin-top: 4px;
  margin-left: 24px;
}

/* Workload Analysis Styles */
.workload-analysis {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.workload-summary {
  display: flex;
  justify-content: space-around;
  padding: 16px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.summary-item .label {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.summary-item .value {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
}

.workload-green {
  color: var(--success) !important;
}

.workload-yellow {
  color: var(--warning) !important;
}

.workload-red {
  color: var(--danger) !important;
}

.task-breakdown h4 {
  margin: 0 0 12px 0;
  font-size: var(--font-size-base);
  color: var(--text-primary);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
}

.task-title {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.task-hours {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  font-weight: var(--font-weight-medium);
}

/* Enhanced Export Dialog Styles */
.export-filters {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.export-content-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.export-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.preview-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--primary);
}

/* Modern UI Components */

/* Empty State */
.empty-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 1;
}

.empty-content {
  padding: 40px;
  border-radius: var(--radius-xl);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-lg);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-state h2 {
  margin: 0 0 8px 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.empty-state p {
  margin: 0 0 8px 0;
  font-size: var(--font-size-base);
  color: var(--text-secondary);
}

.shortcut-hint {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.shortcut-hint kbd {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: 2px 6px;
  font-family: monospace;
  font-weight: var(--font-weight-medium);
}


/* Context Toolbar */
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

/* Insight Drawer */
.insight-trigger {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 999;
  backdrop-filter: blur(8px);
}

.insight-trigger:hover {
  transform: translateX(-50%) translateY(-2px);
  box-shadow: var(--shadow-md);
}

.insight-icon {
  font-size: 16px;
}

.insight-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.insight-drawer {
  position: fixed;
  top: 0;
  left: 50%;
  transform: translateX(-50%) translateY(-100%);
  width: 480px;
  max-width: 90vw;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-top: none;
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
  box-shadow: var(--shadow-xl);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 998;
  backdrop-filter: blur(8px);
}

.insight-drawer.drawer-open {
  transform: translateX(-50%) translateY(0);
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-subtle);
}

.drawer-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.drawer-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.drawer-close:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
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
  max-height: 400px;
  overflow-y: auto;
}

.insight-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.refresh-btn, .analyze-btn {
  padding: 8px 16px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--font-size-sm);
  transition: all 0.2s ease;
}

.refresh-btn:hover, .analyze-btn:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
}

.risk-toggle label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  cursor: pointer;
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
  
  .context-toolbar {
    flex-direction: column;
  }
}

/* Timeline View Styles */
.timeline-view {
  width: 100%;
  height: 100vh;
  overflow-y: auto;
  padding: 20px;
  background: var(--background);
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.timeline-header h2 {
  margin: 0;
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.timeline-controls {
  display: flex;
  gap: 8px;
}

.timeline-container {
  position: relative;
  max-width: 800px;
  margin: 0 auto;
}

.timeline-line {
  position: absolute;
  left: 20px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--border);
  z-index: 1;
}

.timeline-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  text-align: center;
  color: var(--text-muted);
}

.timeline-empty .empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.timeline-empty .empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.timeline-empty h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--text-secondary);
}

.timeline-empty p {
  margin: 0;
  font-size: var(--font-size-sm);
}

.timeline-item {
  position: relative;
  margin-bottom: 24px;
  padding-left: 56px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.timeline-item:hover {
  transform: translateX(4px);
}

.timeline-item.completed {
  opacity: 0.8;
}

.timeline-item.high-priority .timeline-dot {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(255, 77, 79, 0.4); }
  70% { box-shadow: 0 0 0 6px rgba(255, 77, 79, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 77, 79, 0); }
}

.timeline-dot {
  position: absolute;
  left: 11px;
  top: 8px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--primary);
  border: 3px solid var(--background);
  z-index: 2;
  transition: all 0.2s ease;
}

.timeline-item:hover .timeline-dot {
  transform: scale(1.2);
}

.timeline-content {
  background: var(--surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--border-radius-lg);
  padding: 16px;
  transition: all 0.2s ease;
}

.timeline-item:hover .timeline-content {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.timeline-date {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  margin-bottom: 8px;
}

.timeline-task {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.task-header h4 {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  flex: 1;
  line-height: 1.4;
}

.task-badges {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.priority-badge,
.status-badge {
  font-size: var(--font-size-xs);
  padding: 2px 6px;
  border-radius: var(--border-radius-sm);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.priority-badge.priority-critical {
  background: rgba(255, 77, 79, 0.1);
  color: #ff4d4f;
}

.priority-badge.priority-high {
  background: rgba(250, 140, 22, 0.1);
  color: #fa8c16;
}

.priority-badge.priority-medium {
  background: rgba(24, 144, 255, 0.1);
  color: #1890ff;
}

.priority-badge.priority-low {
  background: rgba(82, 196, 26, 0.1);
  color: #52c41a;
}

.priority-badge.priority-backlog {
  background: rgba(140, 140, 140, 0.1);
  color: #8c8c8c;
}

.status-badge.pending {
  background: rgba(250, 140, 22, 0.1);
  color: #fa8c16;
}

.status-badge.in_progress {
  background: rgba(24, 144, 255, 0.1);
  color: #1890ff;
}

.status-badge.completed {
  background: rgba(82, 196, 26, 0.1);
  color: #52c41a;
}

.status-badge.cancelled {
  background: rgba(140, 140, 140, 0.1);
  color: #8c8c8c;
}

.task-description {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

.task-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.module-tag {
  background: var(--surface-secondary);
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
  font-weight: var(--font-weight-medium);
}

.task-id {
  opacity: 0.6;
}

/* Dark mode support for timeline */
@media (prefers-color-scheme: dark) {
  .timeline-line {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .timeline-dot {
    border-color: var(--background);
  }
  
  .timeline-content {
    background: rgba(255, 255, 255, 0.03);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .timeline-item:hover .timeline-content {
    background: rgba(255, 255, 255, 0.05);
    border-color: var(--primary);
  }
}

/* Responsive timeline */
@media (max-width: 768px) {
  .timeline-view {
    padding: 16px;
  }
  
  .timeline-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .timeline-item {
    padding-left: 40px;
  }
  
  .timeline-line {
    left: 15px;
  }
  
  .timeline-dot {
    left: 6px;
    width: 16px;
    height: 16px;
  }
  
  .task-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .task-badges {
    align-self: flex-end;
  }
}
</style>