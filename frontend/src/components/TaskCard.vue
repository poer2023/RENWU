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
      <el-button size="small" @click.stop="generateSubtasks" title="Generate Subtasks">🔧</el-button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { ElButton, ElInput, ElMessageBox } from 'element-plus'
import { Edit, Delete } from '@element-plus/icons-vue'
import { useTaskStore, type Task } from '@/stores/tasks'
import AIAssistantPrompt from './AIAssistantPrompt.vue'

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

// Computed properties
const moduleName = computed(() => taskStore.getModuleName(props.task.module_id))
const moduleColor = computed(() => taskStore.getModuleColor(props.task.module_id))

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

async function generateSubtasks() {
  try {
    const subtasks = await taskStore.generateTaskSubtasks(
      props.task.title,
      props.task.description,
      5
    )
    
    // Create each subtask
    for (const subtask of subtasks) {
      await taskStore.createTask({
        ...subtask,
        parent_id: props.task.id,
        module_id: props.task.module_id
      })
    }
    
    // Refresh tasks to show new subtasks
    await taskStore.fetchTasks()
    
    emit('update', props.task) // Notify parent to refresh
  } catch (error) {
    console.error('Failed to generate subtasks:', error)
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