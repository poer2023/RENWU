<template>
  <div 
    ref="nodeRef"
    :data-task-id="task.id"
    :class="[
      'task-node',
      `priority-${task.urgency}`,
      { 'selected': isSelected, 'editing': isEditing, 'connecting': isConnecting, 'hovering': isHovering }
    ]"
    @click="handleClick"
    @dblclick="handleDoubleClick"
    @mouseenter="isHovering = true"
    @mouseleave="isHovering = false"
    :style="{ 
      width: nodeWidth + 'px',
      minHeight: nodeHeight + 'px'
    }"
  >
    <!-- Priority Border Strip - Left Vertical -->
    <div class="priority-strip" :class="`priority-${task.urgency}`"></div>

    <!-- Node Ports - Enhanced Design -->
    <div class="node-port input-port" @mousedown.stop="(e) => startConnection('input', e)" v-show="isSelected || isConnecting">
      <div class="port-dot input-dot" :class="{ 'port-active': isConnecting }">
        <div class="port-inner"></div>
      </div>
      <div class="port-label">输入</div>
    </div>
    <div class="node-port output-port" @mousedown.stop="(e) => startConnection('output', e)" v-show="isSelected || isConnecting">
      <div class="port-dot output-dot" :class="{ 'port-active': isConnecting }">
        <div class="port-inner"></div>
      </div>
      <div class="port-label">输出</div>
    </div>

    <!-- Node Header -->
    <div class="node-header">
      <div class="node-icon">
        <span class="task-icon">{{ getTaskIcon(task) }}</span>
      </div>
      <div class="node-title-area">
        <h3 v-if="!isEditing" class="node-title">{{ task.title }}</h3>
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
        <div class="node-subtitle">
          <span class="priority-badge" :class="`priority-badge-${task.urgency}`">
            P{{ task.urgency }}
          </span>
          <span class="priority-name">{{ getPriorityName(task.urgency) }}</span>
        </div>
      </div>
    </div>

    <!-- Node Body -->
    <div class="node-body" v-if="task.description || isEditing">
      <p v-if="!isEditing && task.description" class="node-description">{{ task.description }}</p>
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
        placeholder="添加描述..."
      />
    </div>

    <!-- Node Footer -->
    <div class="node-footer">
      <div class="node-meta">
        <span class="module-pill" v-if="task.module_id" :style="getModuleStyle(task.module_id)">
          {{ getModuleName(task.module_id) }}
        </span>
        <div class="node-badges">
          <span class="time-badge" :title="formatFullDate(task.created_at)">
            {{ formatRelativeTime(task.created_at) }}
          </span>
          <span v-if="task.estimated_hours > 0" class="hours-badge">
            {{ task.estimated_hours }}h
          </span>
        </div>
      </div>
      <div class="node-actions" v-if="isSelected && !isEditing">
        <button @click.stop="startEditing" class="node-action-btn" title="编辑">
          <span class="action-icon">✏️</span>
        </button>
        <button 
          @click.stop="generateSubtasks" 
          class="node-action-btn"
          title="生成子任务"
          :disabled="generating"
        >
          <span v-if="generating" class="action-icon loading">⏳</span>
          <span v-else class="action-icon">🤖</span>
        </button>
        <button @click.stop="handleDelete" class="node-action-btn danger" title="删除任务">
          <span class="action-icon">🗑️</span>
        </button>
      </div>
    </div>

    <!-- Resize Handle -->
    <div class="resize-handle" @mousedown="startResize" v-if="isSelected"></div>

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
import { ElInput, ElMessageBox } from 'element-plus'
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

const nodeRef = ref<HTMLElement>()
const isEditing = ref(false)
const isConnecting = ref(false)
const generating = ref(false)
const isHovering = ref(false)
const editTitle = ref('')
const editDescription = ref('')
const titleInput = ref()

// Node size state
const nodeWidth = ref(240)
const nodeHeight = ref(120)

// AI Assistant state
const showAIPrompt = ref(false)
const aiPromptPosition = ref({ x: 0, y: 0 })
const aiPromptContent = ref('')
const aiPromptContext = ref('')
const aiPromptField = ref<'title' | 'description'>('title')

// Computed properties
const moduleName = computed(() => taskStore.getModuleName(props.task.module_id))
const moduleColor = computed(() => taskStore.getModuleColor(props.task.module_id))

// Utility functions
function getTaskIcon(task: Task): string {
  const icons = {
    0: '🚨', // Critical
    1: '⚡', // High
    2: '📝', // Medium
    3: '📋', // Low
    4: '💭'  // Backlog
  }
  return icons[task.urgency as keyof typeof icons] || '📝'
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

function getModuleStyle(moduleId: number | null) {
  if (!moduleId) return {}
  return {
    backgroundColor: moduleColor.value,
    color: 'rgba(0, 0, 0, 0.8)'
  }
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

function formatFullDate(date: string): string {
  return new Date(date).toLocaleString('zh-CN')
}

// Event handlers
function handleClick() {
  emit('select', props.task)
}

function handleDoubleClick(event: MouseEvent) {
  event.stopPropagation()
  if (!nodeRef.value) return
  
  const rect = nodeRef.value.getBoundingClientRect()
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

function startConnection(type: 'input' | 'output', event?: MouseEvent) {
  if (!event) return
  
  console.log('StartConnection called:', type, 'task:', props.task.id)
  isConnecting.value = true
  
  // 输出端口才能开始连线（从输出连到输入）
  if (type === 'output') {
    console.log('Emitting startConnection event:', props.task.id)
    emit('startConnection', props.task.id, event)
  }
}

// Resize functionality
function startResize(event: MouseEvent) {
  event.preventDefault()
  event.stopPropagation()
  
  const startX = event.clientX
  const startY = event.clientY
  const startWidth = nodeWidth.value
  const startHeight = nodeHeight.value
  
  function handleMouseMove(e: MouseEvent) {
    const deltaX = e.clientX - startX
    const deltaY = e.clientY - startY
    
    nodeWidth.value = Math.max(200, startWidth + deltaX)
    nodeHeight.value = Math.max(100, startHeight + deltaY)
  }
  
  function handleMouseUp() {
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }
  
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
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
      '确定要删除这个任务吗？',
      '删除任务',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
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
  if (!nodeRef.value) return
  
  const rect = nodeRef.value.getBoundingClientRect()
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
    generating.value = true
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
    emit('update', props.task)
  } catch (error) {
    console.error('Failed to generate subtasks:', error)
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
/* Task Node - n8n/Dify Style */
.task-node {
  position: relative;
  background-color: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  cursor: pointer;
  user-select: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: var(--font-family);
  overflow: hidden;
  min-width: 200px;
  max-width: 400px;
  backdrop-filter: blur(8px);
  will-change: transform, box-shadow;
}

.task-node:hover {
  box-shadow: var(--shadow-xl), 0 0 20px rgba(59, 130, 246, 0.15);
  transform: translateY(-4px) scale(1.02);
  border-color: var(--primary-light);
  background-color: var(--card-hover);
}

.task-node:hover .priority-strip {
  height: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.task-node:hover .node-icon {
  transform: scale(1.1);
  background-color: var(--primary-light);
}

.task-node:hover .node-title {
  color: var(--primary);
}

.task-node.selected {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-light), var(--shadow-xl);
  transform: translateY(-2px);
  z-index: 10;
}

.task-node.selected .priority-strip {
  animation: priority-glow 2s infinite alternate;
}

@keyframes priority-glow {
  from {
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.2);
  }
  to {
    box-shadow: 0 0 16px rgba(59, 130, 246, 0.4);
  }
}

.task-node.connecting {
  border-color: var(--info);
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
}

/* Priority Border Strip - Left Vertical */
.priority-strip {
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  border-radius: var(--radius-lg) 0 0 var(--radius-lg);
}

.priority-strip.priority-0 { background-color: var(--danger); }
.priority-strip.priority-1 { background-color: var(--warning); }
.priority-strip.priority-2 { background-color: var(--info); }
.priority-strip.priority-3 { background-color: var(--success); }
.priority-strip.priority-4 { background-color: var(--primary); }

/* Node Ports */
.node-port {
  position: absolute;
  display: flex;
  align-items: center;
  opacity: 0;
  transition: opacity 0.2s ease;
  z-index: 10;
}

.task-node.selected .node-port,
.task-node.connecting .node-port {
  opacity: 1;
}

.task-node:hover .node-port {
  opacity: 0.6;
}

.task-node.connecting {
  box-shadow: 0 0 0 2px var(--info), var(--shadow-lg);
}

.input-port {
  left: -8px;
  top: 50%;
  transform: translateY(-50%);
  flex-direction: row;
}

.output-port {
  right: -8px;
  top: 50%;
  transform: translateY(-50%);
  flex-direction: row-reverse;
}

.port-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background-color: var(--border-default);
  border: 2px solid var(--card-bg);
  cursor: crosshair;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.port-inner {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--text-muted);
  transition: all 0.2s ease;
}

.input-dot {
  background-color: var(--success);
}

.output-dot {
  background-color: var(--primary);
}

.port-dot:hover {
  transform: scale(1.2);
  box-shadow: 0 0 8px rgba(37, 99, 235, 0.3);
}

.input-dot:hover {
  background-color: var(--success);
  box-shadow: 0 0 8px rgba(52, 211, 153, 0.4);
}

.input-dot:hover .port-inner {
  background-color: var(--card-bg);
  transform: scale(1.2);
}

.output-dot:hover {
  background-color: var(--primary);
  box-shadow: 0 0 8px rgba(37, 99, 235, 0.4);
}

.output-dot:hover .port-inner {
  background-color: var(--card-bg);
  transform: scale(1.2);
}

.port-dot.port-active {
  background-color: var(--primary-hover);
  transform: scale(1.2);
  box-shadow: 0 0 16px var(--primary-light);
  animation: port-pulse 1.5s infinite;
}

@keyframes port-pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1.2);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.4);
  }
}

.port-label {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  margin: 0 8px;
  padding: 2px 6px;
  background-color: var(--bg-elevated);
  border-radius: 4px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.node-port:hover .port-label {
  opacity: 1;
}

/* Node Header */
.node-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 16px 12px 20px; /* Add left padding for vertical strip */
}

.node-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-elevated);
  border-radius: var(--radius-md);
  font-size: 16px;
}

.node-title-area {
  flex: 1;
  min-width: 0;
}

.node-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 4px 0;
  line-height: var(--line-height-tight);
  word-wrap: break-word;
}

.node-subtitle {
  display: flex;
  align-items: center;
  gap: 8px;
}

.priority-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: white;
}

.priority-badge.priority-badge-0 { background-color: var(--danger); }
.priority-badge.priority-badge-1 { background-color: var(--warning); }
.priority-badge.priority-badge-2 { background-color: var(--info); }
.priority-badge.priority-badge-3 { background-color: var(--success); }
.priority-badge.priority-badge-4 { background-color: var(--primary); }

.priority-name {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

/* Node Body */
.node-body {
  padding: 0 16px 8px 20px; /* Add left padding for vertical strip */
}

.node-description {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: var(--line-height-normal);
  margin: 0;
  word-wrap: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Node Footer */
.node-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px 16px 20px; /* Add left padding for vertical strip */
  border-top: 1px solid var(--border-subtle);
  margin-top: 8px;
}

.node-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.module-pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  background-color: var(--bg-elevated);
  color: var(--text-secondary);
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: all 0.2s ease;
  border: 1px solid var(--border-subtle);
}

.task-node:hover .module-pill {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
  border-color: var(--border-default);
}

.node-badges {
  display: flex;
  align-items: center;
  gap: 4px;
}

.time-badge,
.hours-badge {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  padding: 1px 4px;
  border-radius: 3px;
  background-color: var(--bg-elevated);
}

/* Node Actions */
.node-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.node-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background-color: transparent;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--text-secondary);
  position: relative;
  overflow: hidden;
}

.node-action-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: var(--primary-light);
  border-radius: 50%;
  transition: all 0.3s ease;
  transform: translate(-50%, -50%);
  z-index: -1;
}

.node-action-btn:hover {
  background-color: var(--bg-elevated);
  transform: scale(1.15) translateY(-1px);
  box-shadow: var(--shadow-sm);
  color: var(--primary);
}

.node-action-btn:hover::before {
  width: 100%;
  height: 100%;
}

.node-action-btn:active {
  transform: scale(1.05);
  transition: all 0.1s ease;
}

.node-action-btn.danger:hover {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--danger);
}

.node-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-icon {
  font-size: 12px;
}

.action-icon.loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Resize Handle */
.resize-handle {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 20px;
  height: 20px;
  cursor: se-resize;
  opacity: 0;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, transparent 40%, var(--primary-light) 50%, var(--primary) 100%);
  border-radius: var(--radius-sm) 0 var(--radius-lg) 0;
}

.resize-handle::before {
  content: '';
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-bottom: 6px solid var(--text-muted);
}

.task-node:hover .resize-handle {
  opacity: 0.7;
  transform: scale(1.1);
}

.resize-handle:hover {
  opacity: 1;
  transform: scale(1.2);
  box-shadow: var(--shadow-sm);
}

/* Priority Strip Animations */
.priority-strip {
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.priority-strip::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s ease;
}

.task-node:hover .priority-strip::after {
  left: 100%;
}

/* Micro Interactions */
.node-badges {
  transition: all 0.2s ease;
}

.task-node:hover .node-badges {
  transform: translateX(2px);
}

.time-badge,
.hours-badge {
  transition: all 0.2s ease;
}

.task-node:hover .time-badge,
.task-node:hover .hours-badge {
  background-color: var(--primary-light);
  color: var(--primary);
  transform: scale(1.05);
}

/* Loading States */
.action-icon.loading {
  animation: spin 1s linear infinite;
}

/* Edit Inputs */
.edit-input,
.edit-textarea {
  font-family: var(--font-family);
}

:deep(.el-input__wrapper) {
  background-color: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}

:deep(.el-input__inner) {
  color: var(--text-primary);
  font-size: var(--font-size-sm);
}

:deep(.el-textarea__inner) {
  background-color: var(--bg-elevated);
  border: 1px solid var(--border-default);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  border-radius: var(--radius-md);
}
</style>