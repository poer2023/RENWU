<template>
  <div class="home-layout">
    <!-- Top Bar -->
    <header class="top-bar">
      <div class="top-bar-left">
        <h1 class="app-title">TaskWall</h1>
        <el-button @click="showQuickAdd = true" type="primary" size="small">
          ⌘P Quick Add
        </el-button>
      </div>
      
      <div class="top-bar-center">
        <el-input
          v-model="searchQuery"
          placeholder="Search tasks... (⇧⌘K)"
          clearable
          size="small"
          style="width: 300px;"
          @input="handleSearch"
          @keydown.enter="selectFirstResult"
          @keydown.escape="clearSearch"
          @focus="showGlobalSearch = true"
          ref="searchInput"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      
      <div class="top-bar-right">
        <el-button @click="showAutoArrangeDialog = true" size="small">
          🎯 自动排列
        </el-button>
        <el-button @click="generateWeeklyReport" size="small">
          📊 Weekly Report
        </el-button>
        <el-button @click="settingsStore.toggleWorkloadSidebar" size="small">
          📈 Workload
        </el-button>
        <el-button 
          @click="toggleIslandView" 
          size="small"
          :loading="islandViewLoading"
          :type="islandViewEnabled ? 'primary' : 'default'"
        >
          🏝️ 主题岛
        </el-button>
        <el-button @click="exportTasks" size="small" :icon="Download">
          Export
        </el-button>
        <el-button @click="showSettings = true" size="small" :icon="Setting">
          Settings
        </el-button>
      </div>
    </header>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Left Sidebar - Capture Panel -->
      <aside class="capture-panel">
        <div class="panel-section">
          <h3>Quick Add</h3>
          <el-input
            v-model="quickText"
            type="textarea"
            :rows="3"
            placeholder="Paste text or describe tasks..."
            @keydown.meta.enter="parseQuickText"
          />
          <el-button 
            @click="parseQuickText" 
            type="primary" 
            :loading="taskStore.loading"
            class="w-full mt-2"
          >
            Parse with AI
          </el-button>
        </div>

        <div class="panel-section">
          <h3>Image Upload</h3>
          <el-upload
            ref="upload"
            :auto-upload="false"
            :on-change="handleImageUpload"
            accept="image/*"
            :show-file-list="false"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              Drop image here or <em>click to upload</em>
            </div>
          </el-upload>
        </div>

        <div class="panel-section" v-if="taskInbox.length > 0">
          <h3>Inbox ({{ taskInbox.length }})</h3>
          <div class="inbox-tasks">
            <div 
              v-for="(task, index) in taskInbox"
              :key="index"
              class="inbox-task"
            >
              <div class="task-info">
                <strong>{{ task.title }}</strong>
                <p v-if="task.description">{{ task.description }}</p>
                <el-tag size="small">P{{ task.urgency }}</el-tag>
              </div>
              <div class="task-actions">
                <el-button size="small" @click="createTaskFromInbox(task)">
                  Add
                </el-button>
                <el-button size="small" @click="removeFromInbox(index)">
                  ×
                </el-button>
              </div>
            </div>
          </div>
          <el-button 
            @click="createAllFromInbox" 
            type="success" 
            size="small"
            class="w-full mt-2"
          >
            Create All
          </el-button>
        </div>

        <div class="panel-section">
          <h3>Modules</h3>
          <div class="module-list">
            <div 
              v-for="module in taskStore.modules"
              :key="module.id"
              class="module-item"
              :style="{ backgroundColor: module.color }"
            >
              {{ module.name }}
            </div>
          </div>
          <el-button @click="showNewModule = true" size="small" class="w-full">
            + Add Module
          </el-button>
        </div>
      </aside>

      <!-- Center Canvas -->
      <main class="canvas-area">
        <!-- Add debug component temporarily -->
        <DebugTaskList :tasks="taskStore.tasks" style="position: absolute; top: 10px; right: 10px; width: 400px; z-index: 1000;" />
        
        <!-- Risk Radar -->
        <RiskRadar @view-task="handleViewRiskyTask" />
        
        <StickyCanvas
          ref="stickyCanvasRef"
          :tasks="taskStore.tasks"
          :selected-task="selectedTask"
          @select-task="handleTaskSelect"
          @open-task-details="handleOpenTaskDetails"
          @auto-arrange-complete="handleAutoArrangeComplete"
        />
        
        <!-- Empty state -->
        <div v-if="taskStore.tasks.length === 0" class="empty-state">
          <h2>Welcome to TaskWall</h2>
          <p>Start by adding some tasks using the Quick Add panel or upload an image</p>
        </div>
      </main>

      <!-- Right Sidebar - Workload Analysis -->
      <WorkloadSidebar v-if="settingsStore.showWorkloadSidebar" />
    </div>

    <!-- Task Details Popup -->
    <TaskDetailsPopup
      v-model:visible="detailsPopupVisible"
      :task="detailsTask"
      :position="popupPosition"
      @close="handleCloseDetails"
    />

    <!-- Quick Add Dialog -->
    <el-dialog v-model="showQuickAdd" title="Quick Add Task" width="500px">
      <el-form>
        <el-form-item label="Title">
          <el-input v-model="newTask.title" placeholder="Task title" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input 
            v-model="newTask.description" 
            type="textarea" 
            :rows="3"
            placeholder="Task description"
          />
        </el-form-item>
        <el-form-item label="Priority">
          <el-select v-model="newTask.urgency" class="w-full">
            <el-option label="P0 - Critical" :value="0" />
            <el-option label="P1 - High" :value="1" />
            <el-option label="P2 - Medium" :value="2" />
            <el-option label="P3 - Low" :value="3" />
            <el-option label="P4 - Backlog" :value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="Module">
          <el-select v-model="newTask.module_id" class="w-full" clearable>
            <el-option
              v-for="module in taskStore.modules"
              :key="module.id"
              :label="module.name"
              :value="module.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showQuickAdd = false">Cancel</el-button>
        <el-button type="primary" @click="createQuickTask">Create Task</el-button>
      </template>
    </el-dialog>

    <!-- New Module Dialog -->
    <el-dialog v-model="showNewModule" title="New Module" width="400px">
      <el-form>
        <el-form-item label="Name">
          <el-input v-model="newModule.name" placeholder="Module name" />
        </el-form-item>
        <el-form-item label="Color">
          <el-color-picker v-model="newModule.color" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showNewModule = false">Cancel</el-button>
        <el-button type="primary" @click="createModule">Create Module</el-button>
      </template>
    </el-dialog>

    <!-- Auto Arrange Dialog -->
    <el-dialog v-model="showAutoArrangeDialog" title="自动排列" width="600px">
      <el-form label-position="top">
        <el-form-item label="排列模式">
          <el-select v-model="settingsStore.autoArrangeOptions.mode" class="w-full">
            <el-option
              v-for="mode in settingsStore.autoArrangeModes"
              :key="mode.value"
              :label="`${mode.icon} ${mode.label}`"
              :value="mode.value"
            >
              <div>
                <span style="font-size: 16px; margin-right: 8px;">{{ mode.icon }}</span>
                <strong>{{ mode.label }}</strong>
                <div style="font-size: 12px; color: #999; margin-top: 2px;">
                  {{ mode.description }}
                </div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <div class="form-row">
          <el-form-item label="间距" class="form-item-half">
            <el-input-number
              v-model="settingsStore.autoArrangeOptions.spacing"
              :min="5"
              :max="100"
              :step="5"
              class="w-full"
            />
          </el-form-item>
          
          <el-form-item label="边距" class="form-item-half">
            <el-input-number
              v-model="settingsStore.autoArrangeOptions.padding"
              :min="10"
              :max="200"
              :step="10"
              class="w-full"
            />
          </el-form-item>
        </div>

        <el-form-item v-if="settingsStore.autoArrangeOptions.mode === 'grid'" label="列数">
          <el-input-number
            v-model="settingsStore.autoArrangeOptions.columns"
            :min="1"
            :max="10"
            class="w-full"
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="settingsStore.autoArrangeOptions.animated">
            使用动画过渡
          </el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="settingsStore.autoArrangeOptions.groupByModule">
            按模块分组
          </el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="settingsStore.autoArrangeOptions.sortByPriority">
            按优先级排序
          </el-checkbox>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAutoArrangeDialog = false">取消</el-button>
        <el-button type="primary" @click="triggerAutoArrange">立即排列</el-button>
      </template>
    </el-dialog>

    <!-- Global Search Modal -->
    <GlobalSearch 
      :visible="showGlobalSearch"
      @close="showGlobalSearch = false"
    />

    <!-- Similar Tasks Dialog -->
    <SimilarTaskDialog
      v-model:visible="showSimilarTasksDialog"
      :new-task-title="pendingTask?.title || ''"
      :new-task-description="pendingTask?.description || ''"
      :similar-tasks="similarTasksData?.similar_tasks || []"
      :suggestions="similarTasksData?.suggestions || []"
      @cancel="handleSimilarTaskCancel"
      @ignore="handleSimilarTaskIgnore"
      @create="handleSimilarTaskCreate"
      @view-task="handleViewSimilarTask"
      @link-tasks="handleLinkSimilarTask"
    />

    <!-- Settings Dialog -->
    <el-dialog v-model="showSettings" title="设置" width="600px">
      <el-tabs>
        <el-tab-pane label="快捷键" name="shortcuts">
          <el-form label-position="top">
            <el-form-item label="键盘布局">
              <el-radio-group v-model="settingsStore.keyboardLayout" @change="settingsStore.setKeyboardLayout">
                <el-radio value="windows">Windows (Ctrl)</el-radio>
                <el-radio value="mac">Mac (⌘)</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="快捷键列表">
              <div class="shortcuts-list">
                <div v-for="(shortcut, key) in settingsStore.shortcuts" :key="key" class="shortcut-item">
                  <span class="shortcut-name">{{ getShortcutName(key) }}</span>
                  <el-tag size="small">{{ settingsStore.formatShortcut(shortcut) }}</el-tag>
                </div>
              </div>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="AI设置" name="ai">
          <el-form label-position="top">
            <el-form-item label="Gemini API Key">
              <el-input 
                v-model="settingsStore.geminiApiKey" 
                type="password" 
                placeholder="输入你的 Gemini API key 用于AI解析"
              />
              <small>用于从文本中AI智能解析任务</small>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="界面" name="interface">
          <el-form label-position="top">
            <el-form-item>
              <el-checkbox v-model="settingsStore.gridVisible" @change="settingsStore.toggleGrid">
                显示网格背景
              </el-checkbox>
            </el-form-item>
            
            <el-form-item>
              <el-checkbox v-model="settingsStore.notifications" @change="settingsStore.toggleNotifications">
                启用通知
              </el-checkbox>
            </el-form-item>
            
            <el-form-item>
              <el-checkbox v-model="settingsStore.autoSave" @change="settingsStore.toggleAutoSave">
                自动保存
              </el-checkbox>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      
      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </template>
    </el-dialog>


  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElButton, ElInput, ElUpload, ElDialog, ElForm, ElFormItem, ElSelect, ElOption, ElTag, ElIcon, ElColorPicker, ElMessage, ElMessageBox, ElTabs, ElTabPane, ElRadioGroup, ElRadio, ElCheckbox, ElInputNumber } from 'element-plus'
import { Download, Setting, UploadFilled, Search } from '@element-plus/icons-vue'
import StickyCanvas from '@/components/StickyCanvas.vue'
import TaskDetailsPopup from '@/components/TaskDetailsPopup.vue'
import DebugTaskList from '@/components/DebugTaskList.vue'
import WorkloadSidebar from '@/components/WorkloadSidebar.vue'
import SimilarTaskDialog from '@/components/SimilarTaskDialog.vue'
import RiskRadar from '@/components/RiskRadar.vue'
import GlobalSearch from '@/components/GlobalSearch.vue'
import { useTaskStore, type Task } from '@/stores/tasks'
import { useSettingsStore } from '@/stores/settings'
import { useKeyboard } from '@/composables/useKeyboard'
import { useSimilarityDetection } from '@/composables/useSimilarityDetection'

const taskStore = useTaskStore()
const settingsStore = useSettingsStore()
const { findSimilarTasks } = useSimilarityDetection()

// 键盘快捷键
useKeyboard({
  onQuickAdd: () => showQuickAdd.value = true,
  onExport: exportTasks,
  onSearch: focusSearch,
  onGlobalSearch: () => showGlobalSearch.value = true
})

// State
const selectedTask = ref<Task | null>(null)
const stickyCanvasRef = ref<InstanceType<typeof StickyCanvas>>()
const detailsTask = ref<Task | null>(null)
const detailsPopupVisible = ref(false)
const popupPosition = ref({ x: 0, y: 0 })
const showQuickAdd = ref(false)
const showNewModule = ref(false)
const showSettings = ref(false)
const showAutoArrangeDialog = ref(false)
const quickText = ref('')
const taskInbox = ref<Partial<Task>[]>([])
const searchQuery = ref('')
const searchResults = ref<Task[]>([])
const searchInput = ref()
const showGlobalSearch = ref(false)
const showSimilarTasksDialog = ref(false)
const similarTasksData = ref<any>(null)
const pendingTask = ref<Partial<Task> | null>(null)
const islandViewEnabled = ref(false)
const themeIslands = ref<any[]>([])
const islandViewLoading = ref(false)

const newTask = ref({
  title: '',
  description: '',
  urgency: 2,
  module_id: undefined
})

const newModule = ref({
  name: '',
  color: '#FFE58F'
})

// Methods
function handleTaskSelect(task: Task | null) {
  selectedTask.value = task
  taskStore.selectTask(task)
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
    ElMessage.success(`Parsed ${parsedTasks.length} tasks`)
  } catch (error) {
    ElMessage.error('Failed to parse tasks')
  }
}

async function handleImageUpload(file: any) {
  try {
    const text = await taskStore.extractTextFromImage(file.raw)
    quickText.value = text
    ElMessage.success('Text extracted from image')
  } catch (error) {
    ElMessage.error('Failed to extract text from image')
  }
}

async function createTaskFromInbox(task: Partial<Task>) {
  try {
    // Check for similar tasks before creating
    await checkSimilarTasksBeforeCreate(task)
  } catch (error) {
    ElMessage.error('Failed to create task')
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
        similarTasksData.value = result
        pendingTask.value = task
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
    ElMessage.success('All tasks created')
  } catch (error) {
    ElMessage.error('Failed to create some tasks')
  }
}

async function createQuickTask() {
  try {
    // Check for similar tasks before creating
    await checkSimilarTasksBeforeCreate(newTask.value)
    newTask.value = {
      title: '',
      description: '',
      urgency: 2,
      module_id: undefined
    }
    showQuickAdd.value = false
  } catch (error) {
    ElMessage.error('Failed to create task')
  }
}

// Similar tasks dialog handlers
function handleSimilarTaskCancel() {
  showSimilarTasksDialog.value = false
  pendingTask.value = null
  similarTasksData.value = null
}

function handleSimilarTaskIgnore() {
  showSimilarTasksDialog.value = false
  if (pendingTask.value) {
    finalizeTaskCreation(pendingTask.value)
  }
  pendingTask.value = null
  similarTasksData.value = null
}

function handleSimilarTaskCreate() {
  showSimilarTasksDialog.value = false
  if (pendingTask.value) {
    finalizeTaskCreation(pendingTask.value)
  }
  pendingTask.value = null
  similarTasksData.value = null
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
  if (pendingTask.value) {
    try {
      // First create the new task
      const newTaskCreated = await taskStore.createTask(pendingTask.value)
      
      // Then create dependency
      await taskStore.createDependency(task.id, newTaskCreated.id)
      
      showSimilarTasksDialog.value = false
      pendingTask.value = null
      similarTasksData.value = null
      
      // Remove from inbox if it was from inbox
      if (taskInbox.value.includes(pendingTask.value)) {
        const index = taskInbox.value.indexOf(pendingTask.value)
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

async function createModule() {
  try {
    await taskStore.createModule(newModule.value)
    newModule.value = {
      name: '',
      color: '#FFE58F'
    }
    showNewModule.value = false
    ElMessage.success('Module created')
  } catch (error) {
    ElMessage.error('Failed to create module')
  }
}

function saveSettings() {
  settingsStore.saveSettings()
  showSettings.value = false
  ElMessage.success('Settings saved')
}

function loadSettings() {
  settingsStore.loadSettings()
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
    task.title.toLowerCase().includes(lowerQuery) ||
    task.description.toLowerCase().includes(lowerQuery)
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
      
      ElMessage.success('Weekly report generated and downloaded!')
    } else {
      throw new Error(result.error || 'Failed to generate report')
    }
  } catch (error) {
    console.error('Weekly report generation failed:', error)
    ElMessage.error('Failed to generate weekly report')
  }
}

async function toggleIslandView() {
  islandViewEnabled.value = !islandViewEnabled.value
  
  if (islandViewEnabled.value) {
    await loadThemeIslands()
  } else {
    themeIslands.value = []
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
  try {
    // Show export options dialog
    await ElMessageBox({
      title: 'Export Format',
      message: 'Choose export format:',
      showCancelButton: true,
      confirmButtonText: 'JSON',
      cancelButtonText: 'Markdown',
      distinguishCancelAndClose: true
    }).then(async () => {
      // Export as JSON
      const response = await fetch('/api/export/json')
      const data = await response.json()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `taskwall-export-${new Date().toISOString().split('T')[0]}.json`
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('Tasks exported as JSON')
    }).catch(async (action) => {
      if (action === 'cancel') {
        // Export as Markdown
        const response = await fetch('/api/export/markdown')
        const result = await response.json()
        const blob = new Blob([result.content], { type: 'text/markdown' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = result.filename
        a.click()
        URL.revokeObjectURL(url)
        ElMessage.success('Tasks exported as Markdown')
      }
    })
  } catch (error) {
    console.error('Export failed:', error)
    ElMessage.error('Export failed')
  }
}



// Keyboard shortcuts are handled by useKeyboard composable above

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
    await taskStore.createModule({ name: 'General', color: '#FFE58F' })
  }
  
  console.log('Home: All data loaded, final tasks count:', taskStore.tasks.length)
})
</script>

<style scoped>
.home-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid #eee;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
  z-index: 100;
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
  font-size: 20px;
  font-weight: 600;
  color: #333;
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
  background: white;
  border-right: 1px solid #eee;
  padding: 16px;
  overflow-y: auto;
}

.panel-section {
  margin-bottom: 24px;
}

.panel-section h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
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
  border: 1px solid #eee;
  border-radius: 4px;
  margin-bottom: 8px;
  background: #fafafa;
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
  color: #666;
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
  font-size: 12px;
  margin-bottom: 4px;
  color: rgba(0,0,0,0.7);
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
  color: #999;
}

.empty-state h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
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
  border-bottom: 1px solid #f0f0f0;
}

.shortcut-name {
  font-size: 14px;
  color: #606266;
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
</style>