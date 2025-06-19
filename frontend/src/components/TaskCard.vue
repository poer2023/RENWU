<template>
  <div 
    ref="cardRef"
    :data-task-id="task.id"
    :class="[
      'task-card',
      `urgency-${task.urgency}`,
      { 'selected': isSelected, 'editing': isEditing }
    ]"
    @click="handleClick"
    @dblclick="handleDoubleClick"
    :style="{ 
      borderColor: moduleColor,
      width: cardWidth + 'px',
      height: cardHeight + 'px'
    }"
  >
    <!-- Urgency indicator with color -->
    <div :class="['urgency-indicator', `urgency-badge-${task.urgency}`]">
      P{{ task.urgency }}
    </div>

    <!-- Resize handle -->
    <div 
      class="resize-handle"
      @mousedown="startResize"
    ></div>

    <!-- Title -->
    <div v-if="!isEditing" class="task-title">
      {{ task.title }}
    </div>
    <el-input
      v-else
      v-model="editTitle"
      ref="titleInput"
      @blur="saveEdit"
      @keydown.enter="saveEdit"
      @keydown.esc="cancelEdit"
      @input="handleTitleInput"
      class="edit-input"
      size="small"
    />

    <!-- Description -->
    <div v-if="task.description && !isEditing" class="task-description">
      {{ task.description }}
    </div>
    <el-input
      v-else-if="isEditing"
      v-model="editDescription"
      type="textarea"
      :rows="2"
      @blur="saveEdit"
      @keydown.esc="cancelEdit"
      @input="handleDescriptionInput"
      class="edit-textarea"
      size="small"
    />

    <!-- Module tag -->
    <div class="module-tag" :style="{ backgroundColor: moduleColor }">
      {{ moduleName }}
    </div>

    <!-- Connection points -->
    <div v-if="isSelected" class="connection-points">
      <div 
        class="connection-point connection-out"
        @mousedown.stop="startConnection"
        title="Drag to create dependency"
      ></div>
    </div>

    <!-- Actions -->
    <div class="task-actions" v-if="isSelected && !isEditing">
      <el-button size="small" @click.stop="startEditing" :icon="Edit" />
      <el-dropdown @command="handleDropdownCommand" trigger="click">
        <el-button size="small" title="子任务操作">
          🔧 <el-icon><arrow-down /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="generate-subtasks">
              <el-icon><magic-stick /></el-icon>
              智能拆分子任务
            </el-dropdown-item>
            <el-dropdown-item command="manage-subtasks" :disabled="!hasSubtasks">
              <el-icon><list /></el-icon>
              管理子任务 ({{ subtaskCount }})
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button size="small" type="danger" @click.stop="handleDelete" :icon="Delete" />
    </div>

    <!-- AI Assistant Prompt -->
    <AIAssistantPrompt
      :visible="showAIPrompt"
      :position="aiPromptPosition"
      :content="aiPromptContent"
      :context="aiPromptContext"
      @close="hideAIPrompt"
      @command="handleAICommand"
    />

    <!-- 子任务确认对话框 -->
    <SubtaskConfirmationDialog
      v-model:visible="showSubtaskDialog"
      :suggestions="subtaskSuggestions"
      :generation-data="generationData"
      :parent-task="task"
      @confirm="handleSubtaskConfirm"
      @reject="handleSubtaskReject"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { ElButton, ElInput, ElMessageBox, ElDropdown, ElDropdownMenu, ElDropdownItem, ElIcon, ElMessage } from 'element-plus'
import { Edit, Delete, ArrowDown, MagicStick, List } from '@element-plus/icons-vue'
import { useTaskStore, type Task } from '@/stores/tasks'
import AIAssistantPrompt from './AIAssistantPrompt.vue'
import SubtaskConfirmationDialog from './SubtaskConfirmationDialog.vue'

interface Props {
  task: Task
  isSelected?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSelected: false
})

const emit = defineEmits<{
  select: [task: Task]
  openDetails: [task: Task, position: { x: number, y: number }]
  update: [task: Task]
  delete: [taskId: number]
  startConnection: [fromTaskId: number, event: MouseEvent]
}>()

const taskStore = useTaskStore()

const cardRef = ref<HTMLElement>()
const isEditing = ref(false)
const editTitle = ref('')
const editDescription = ref('')
const titleInput = ref()

// Card size state
const cardWidth = ref(200)
const cardHeight = ref(120)
const isResizing = ref(false)

// AI Assistant state
const showAIPrompt = ref(false)
const aiPromptPosition = ref({ x: 0, y: 0 })
const aiPromptContent = ref('')
const aiPromptContext = ref('')
const aiPromptField = ref<'title' | 'description'>('title')

// 子任务相关状态
const showSubtaskDialog = ref(false)
const subtaskSuggestions = ref([])
const generationData = ref(null)
const isGeneratingSubtasks = ref(false)

// Computed properties
const moduleName = computed(() => taskStore.getModuleName(props.task.module_id))
const moduleColor = computed(() => taskStore.getModuleColor(props.task.module_id))

// 子任务相关计算属性
const hasSubtasks = computed(() => {
  return taskStore.tasks.some(task => task.parent_id === props.task.id)
})

const subtaskCount = computed(() => {
  return taskStore.tasks.filter(task => task.parent_id === props.task.id).length
})

// 判断是否应该自动触发子任务拆分（≥12个中文字符）
const shouldAutoTriggerSubtasks = computed(() => {
  const chineseCharCount = (props.task.title.match(/[\u4e00-\u9fa5]/g) || []).length
  return chineseCharCount >= 12
})

// 监听标题变化，自动触发子任务拆分
watch(() => props.task.title, (newTitle) => {
  if (shouldAutoTriggerSubtasks.value && !hasSubtasks.value) {
    // 延迟触发，避免在编辑过程中频繁触发
    setTimeout(() => {
      if (shouldAutoTriggerSubtasks.value && !hasSubtasks.value) {
        autoGenerateSubtasks()
      }
    }, 2000)
  }
})

// Methods
function handleClick() {
  emit('select', props.task)
}

function handleDoubleClick(event: MouseEvent) {
  event.stopPropagation()
  if (!cardRef.value) return
  
  const rect = cardRef.value.getBoundingClientRect()
  const position = {
    x: rect.left + rect.width / 2,
    y: rect.bottom + 10
  }
  
  emit('openDetails', props.task, position)
}

async function startEditing() {
  isEditing.value = true
  editTitle.value = props.task.title
  editDescription.value = props.task.description
  
  await nextTick()
  if (titleInput.value) {
    titleInput.value.focus()
  }
}

// Resize functionality
function startResize(event: MouseEvent) {
  event.preventDefault()
  event.stopPropagation()
  
  isResizing.value = true
  const startX = event.clientX
  const startY = event.clientY
  const startWidth = cardWidth.value
  const startHeight = cardHeight.value
  
  function handleMouseMove(e: MouseEvent) {
    const deltaX = e.clientX - startX
    const deltaY = e.clientY - startY
    
    cardWidth.value = Math.max(150, startWidth + deltaX)
    cardHeight.value = Math.max(80, startHeight + deltaY)
  }
  
  function handleMouseUp() {
    isResizing.value = false
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }
  
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

// Connection functionality
function startConnection(event: MouseEvent) {
  event.preventDefault()
  event.stopPropagation()
  emit('startConnection', props.task.id, event)
}

async function saveEdit() {
  if (!isEditing.value) return
  
  try {
    const updates: Partial<Task> = {}
    
    if (editTitle.value !== props.task.title) {
      updates.title = editTitle.value
    }
    
    if (editDescription.value !== props.task.description) {
      updates.description = editDescription.value
    }
    
    if (Object.keys(updates).length > 0) {
      await taskStore.updateTask(props.task.id, updates)
    }
    
    isEditing.value = false
  } catch (error) {
    console.error('Failed to update task:', error)
  }
}

function cancelEdit() {
  isEditing.value = false
  editTitle.value = props.task.title
  editDescription.value = props.task.description
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm(
      'Are you sure you want to delete this task?',
      'Delete Task',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
      }
    )
    
    await taskStore.deleteTask(props.task.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete task:', error)
    }
  }
}

// AI Assistant methods
function handleTitleInput(value: string) {
  if (value.endsWith('/')) {
    showAIPromptFor('title', value.slice(0, -1))
  }
}

function handleDescriptionInput(value: string) {
  if (value.endsWith('/')) {
    showAIPromptFor('description', value.slice(0, -1))
  }
}

function showAIPromptFor(field: 'title' | 'description', content: string) {
  if (!cardRef.value) return
  
  const rect = cardRef.value.getBoundingClientRect()
  aiPromptPosition.value = {
    x: rect.right + 10,
    y: rect.top
  }
  
  aiPromptField.value = field
  aiPromptContent.value = content
  aiPromptContext.value = `Task: ${props.task.title}\nDescription: ${props.task.description}\nModule: ${moduleName.value}`
  showAIPrompt.value = true
}

function hideAIPrompt() {
  showAIPrompt.value = false
}

function handleAICommand(command: string, result: string) {
  if (aiPromptField.value === 'title') {
    editTitle.value = result
  } else if (aiPromptField.value === 'description') {
    editDescription.value = result
  }
  
  hideAIPrompt()
}

// 下拉菜单命令处理
function handleDropdownCommand(command: string) {
  if (command === 'generate-subtasks') {
    manualGenerateSubtasks()
  } else if (command === 'manage-subtasks') {
    // Logic to manage subtasks, e.g., open a dialog
    console.log('Managing subtasks for task:', props.task.id)
  }
}

async function handleSubtaskConfirm(subtasksToCreate: any[]) {
  console.log('Confirmed subtasks', subtasksToCreate)
  try {
    const createdTasks = []
    
    // 计算子任务的优先级（比父任务优先级低一级，但不超过4）
    const childUrgency = Math.min(props.task.urgency + 1, 4)
    
    // 逐个创建子任务
    for (const subtask of subtasksToCreate) {
      const newTask = await taskStore.createTask({
        title: subtask.title,
        description: subtask.description,
        urgency: childUrgency, // 使用计算后的优先级
        module_id: props.task.module_id,
        parent_id: props.task.id
      })
      createdTasks.push(newTask)
    }
    
    // 创建父子任务之间的依赖关系（连线）
    for (const childTask of createdTasks) {
      try {
        await taskStore.createDependency(props.task.id, childTask.id)
        console.log(`Created dependency: ${props.task.id} -> ${childTask.id}`)
      } catch (depError) {
        console.warn(`Failed to create dependency for task ${childTask.id}:`, depError)
      }
    }
    
    // 刷新依赖关系以显示连线
    await taskStore.fetchDependencies()
    
    ElMessage.success(`已创建 ${subtasksToCreate.length} 个子任务并建立连接关系`)
  } catch (error) {
    console.error('创建子任务失败:', error)
    ElMessage.error('创建子任务失败，请重试')
  }
  showSubtaskDialog.value = false
}

function handleSubtaskReject(reason: string) {
  console.log('Rejected subtasks, reason:', reason)
  showSubtaskDialog.value = false
}

// 自动触发子任务生成
async function autoGenerateSubtasks() {
  if (isGeneratingSubtasks.value) return
  
  try {
    isGeneratingSubtasks.value = true
    await generateSubtasksFromAPI()
  } catch (error) {
    console.error('自动生成子任务失败:', error)
  } finally {
    isGeneratingSubtasks.value = false
  }
}

// 手动触发子任务生成
async function manualGenerateSubtasks() {
  if (isGeneratingSubtasks.value) return
  
  try {
    isGeneratingSubtasks.value = true
    await generateSubtasksFromAPI()
    showSubtaskDialog.value = true
  } catch (error) {
    console.error('手动生成子任务失败:', error)
    ElMessage.error('生成子任务失败，请重试')
  } finally {
    isGeneratingSubtasks.value = false
  }
}

// 调用API生成子任务
async function generateSubtasksFromAPI() {
  const response = await fetch('/api/ai/subtasks/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      parent_task_id: props.task.id,
      parent_task_title: props.task.title,
      parent_task_description: props.task.description,
      max_subtasks: 5,
      auto_accept: false
    })
  })

  if (!response.ok) {
    throw new Error(`API请求失败: ${response.status}`)
  }

  const data = await response.json()
  
  if (!data.success) {
    throw new Error(data.error || '生成子任务失败')
  }

  subtaskSuggestions.value = data.suggestions
  generationData.value = {
    model_used: data.model_used,
    tokens_in: data.tokens_in,
    tokens_out: data.tokens_out,
    cost: data.cost,
    log_id: data.log_id
  }
}
</script>

<style scoped>
.task-card {
  position: relative;
  min-width: 150px;
  min-height: 80px;
  padding: 12px;
  border-radius: 8px;
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  user-select: none;
  transition: box-shadow 0.15s ease, transform 0.15s ease;
  font-size: 12px;
  background: #ffffff;
  overflow: hidden;
  contain: layout style;
  transform: translate3d(0, 0, 0);
}

.task-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translate3d(0, -1px, 0);
}

.task-card.selected {
  border-color: #409EFF !important;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.task-card.editing {
  box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.3);
}

/* Urgency color backgrounds - lighter for better readability */
.urgency-0 { background: #fff1f0; border-left: 4px solid #ff4d4f; } /* P0 - Critical - Red */
.urgency-1 { background: #fff7e6; border-left: 4px solid #fa8c16; } /* P1 - High - Orange */
.urgency-2 { background: #feffe6; border-left: 4px solid #fadb14; } /* P2 - Medium - Yellow */
.urgency-3 { background: #f6ffed; border-left: 4px solid #52c41a; } /* P3 - Low - Green */
.urgency-4 { background: #f0f5ff; border-left: 4px solid #1890ff; } /* P4 - Backlog - Blue */

.urgency-indicator {
  position: absolute;
  top: 6px;
  right: 6px;
  padding: 2px 6px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: bold;
  color: white;
  z-index: 10;
}

/* Urgency badge colors */
.urgency-badge-0 { background: #ff4d4f; } /* Critical - Red */
.urgency-badge-1 { background: #fa8c16; } /* High - Orange */
.urgency-badge-2 { background: #fadb14; color: #000; } /* Medium - Yellow */
.urgency-badge-3 { background: #52c41a; } /* Low - Green */
.urgency-badge-4 { background: #1890ff; } /* Backlog - Blue */

/* Resize handle */
.resize-handle {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 12px;
  height: 12px;
  background: linear-gradient(-45deg, transparent 30%, #ccc 30%, #ccc 40%, transparent 40%, transparent 60%, #ccc 60%, #ccc 70%, transparent 70%);
  cursor: se-resize;
  opacity: 0;
  transition: opacity 0.2s;
}

.task-card:hover .resize-handle {
  opacity: 0.6;
}

.resize-handle:hover {
  opacity: 1 !important;
}

.task-title {
  font-weight: 600;
  margin-bottom: 6px;
  line-height: 1.3;
  word-wrap: break-word;
}

.task-description {
  color: #666;
  margin-bottom: 8px;
  line-height: 1.4;
  word-wrap: break-word;
}

.module-tag {
  position: absolute;
  bottom: 4px;
  left: 4px;
  color: rgba(0, 0, 0, 0.7);
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 500;
}

.task-actions {
  position: absolute;
  top: 4px;
  left: 4px;
  display: flex;
  gap: 4px;
}

.edit-input {
  margin-bottom: 8px;
}

.edit-textarea {
  margin-bottom: 8px;
}

/* Element Plus overrides for smaller buttons */
:deep(.el-button--small) {
  padding: 4px 6px;
  font-size: 10px;
}

/* Connection points */
.connection-points {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.connection-point {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #409EFF;
  border: 2px solid #fff;
  pointer-events: auto;
  cursor: crosshair;
  opacity: 0;
  transition: opacity 0.2s;
  z-index: 15;
}

.connection-point:hover {
  opacity: 1;
  transform: scale(1.2);
}

.task-card.selected .connection-point {
  opacity: 0.7;
}

.connection-out {
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
}
</style>