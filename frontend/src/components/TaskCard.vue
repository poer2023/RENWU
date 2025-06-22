<template>
  <div 
    ref="nodeRef"
    :data-task-id="task.id"
    :class="[
      'task-node',
      `priority-${task.urgency}`,
      { 'selected': isSelected, 'editing': isEditing, 'connecting': isConnecting, 'hovering': isHovering, 'resizing': isResizing }
    ]"
    @click.stop="handleClick"
    @dblclick.stop="handleDoubleClick"
    @mouseenter="isHovering = true"
    @mouseleave="isHovering = false"
    @keydown="handleKeyDown"
    tabindex="0"
    :style="{ 
      width: nodeWidth + 'px'
    }"
  >
    <!-- Priority Border Strip - Left Vertical -->
    <div class="priority-strip" :class="`priority-${task.urgency}`"></div>

    <!-- Connection Ports -->
    <ConnectionPorts
      :visible="isSelected || isConnecting"
      :is-active="isConnecting"
      @start-connection="startConnection"
    />

    <!-- 固定高度的标题区域 -->
    <div class="card-header-fixed" @click.stop="handleClick" @dblclick.stop="handleDoubleClick">
      <TaskCardHeader
        :title="task.title"
        :urgency="task.urgency"
        :is-editing="isEditing"
        @update:title="editTitle = $event"
        @save="saveEdit"
        @cancel="cancelEdit"
        @input="handleTitleInput"
        ref="titleInput"
      />
    </div>

    <!-- 可变高度的内容区域 -->
    <div 
      class="card-body-resizable" 
      :style="{ minHeight: contentHeight + 'px' }"
    >
      <TaskCardBody
        v-if="task.description || isEditing"
        :description="task.description"
        :is-editing="isEditing"
        @update:description="editDescription = $event"
        @save="saveEdit"
        @cancel="cancelEdit"
        @input="handleDescriptionInput"
      />
      
      <!-- 编辑模式下的额外字段 -->
      <div v-if="isEditing" class="editing-fields" @click.stop>
        <div class="field-row">
          <label>优先级:</label>
          <select v-model="editUrgency" class="urgency-select" @click.stop>
            <option value="0">🔴 紧急</option>
            <option value="1">🟡 重要</option>
            <option value="2">🔵 正常</option>
            <option value="3">🟢 低</option>
            <option value="4">🟣 可选</option>
          </select>
        </div>
        <div class="field-row">
          <label>估算工时:</label>
          <input 
            v-model.number="editEstimatedHours" 
            type="number" 
            min="0" 
            step="0.5"
            class="hours-input"
            placeholder="小时"
            @click.stop
          />
        </div>
      </div>
    </div>

    <!-- 固定高度的底部工具栏 -->
    <div class="card-footer-fixed" @click.stop="handleClick">
      <TaskCardFooter
        :module-id="task.module_id"
        :module-name="moduleName"
        :module-color="moduleColor"
        :created-at="task.created_at"
        :estimated-hours="task.estimated_hours"
        :show-actions="isSelected"
      >
        <template #actions>
          <div class="footer-actions" v-if="isSelected && !isEditing">
            <button
              @click="startEditing"
              class="action-btn edit-btn"
              title="编辑任务 (Enter/F2)"
            >
              ✏️
            </button>
            <button
              @click="generateSubtasks"
              class="action-btn subtask-btn"
              title="生成子任务 (Ctrl+G)"
              :disabled="generating"
            >
              {{ generating ? '⏳' : '🔧' }}
            </button>
            <button
              @click="handleQuickDelete"
              class="action-btn delete-btn"
              title="删除任务 (Ctrl+D)"
            >
              🗑️
            </button>
          </div>
          <div class="editing-actions" v-if="isEditing">
            <button @click="saveEdit" class="action-btn save-btn" title="保存 (Ctrl+S)">
              💾
            </button>
            <button @click="cancelEdit" class="action-btn cancel-btn" title="取消 (Esc)">
              ❌
            </button>
          </div>
        </template>
      </TaskCardFooter>
    </div>

    <!-- Resize Handles -->
    <div v-if="isSelected" class="resize-handles">
      <!-- 四个角的缩放手柄 -->
      <div class="resize-handle corner-nw" @mousedown="startResize($event, 'nw')" title="调整大小"></div>
      <div class="resize-handle corner-ne" @mousedown="startResize($event, 'ne')" title="调整大小"></div>
      <div class="resize-handle corner-sw" @mousedown="startResize($event, 'sw')" title="调整大小"></div>
      <div class="resize-handle corner-se" @mousedown="startResize($event, 'se')" title="调整大小"></div>
      
      <!-- 四个边的缩放手柄 -->
      <div class="resize-handle edge-n" @mousedown="startResize($event, 'n')" title="调整高度"></div>
      <div class="resize-handle edge-s" @mousedown="startResize($event, 's')" title="调整高度"></div>
      <div class="resize-handle edge-w" @mousedown="startResize($event, 'w')" title="调整宽度"></div>
      <div class="resize-handle edge-e" @mousedown="startResize($event, 'e')" title="调整宽度"></div>
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
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { ElInput, ElMessageBox, ElMessage } from 'element-plus'
import { useTaskStore, type Task } from '@/stores/tasks'
import AIAssistantPrompt from './AIAssistantPrompt.vue'
import ConnectionPorts from './task/ConnectionPorts.vue'
import TaskCardHeader from './task/TaskCardHeader.vue'
import TaskCardBody from './task/TaskCardBody.vue'
import TaskCardFooter from './task/TaskCardFooter.vue'

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
  getTaskPosition: [taskId: number]
  subtasksCreated: [data: { parentTask: Task, subtasks: Task[] }]
}>()

const taskStore = useTaskStore()

const nodeRef = ref<HTMLElement>()
const isEditing = ref(false)
const isConnecting = ref(false)
const generating = ref(false)
const isHovering = ref(false)
const isResizing = ref(false)
const editTitle = ref('')
const editDescription = ref('')
const editUrgency = ref(0)
const editEstimatedHours = ref(0)
const titleInput = ref()

// Node size state
const nodeWidth = ref(240)
const nodeHeight = ref(120)
const contentHeight = ref(80)

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
function handleClick(event: MouseEvent) {
  // 🔧 修复: 检查点击目标，避免误触发
  const target = event.target as HTMLElement
  
  // 如果点击的是交互元素，不触发选择
  if (target.closest('.resize-handle, .connection-port, button, input, textarea, select')) {
    return
  }
  
  // 🔧 修复: 不要过度阻止事件传播，让统一拖拽系统能够正确处理
  // 只在必要时阻止传播
  if (target.closest('.editing-fields, .footer-actions')) {
    event.stopPropagation()
  }
  
  console.log('🎯 [TaskCard] 任务卡片被点击:', props.task.title)
  emit('select', props.task)
}

// 处理键盘快捷键
function handleKeyDown(event: KeyboardEvent) {
  if (!props.isSelected) return
  
  // 🔧 修复: 只在处理快捷键时阻止传播
  if (event.key === 'Delete' || event.key === 'Enter' || event.key === 'F2' || 
      ((event.ctrlKey || event.metaKey) && (event.key === 'd' || event.key === 'g'))) {
    event.stopPropagation()
  }
  
  // 只有在双按Delete键时才删除任务（防止误删）
  if (event.key === 'Delete' && event.detail === 2) {
    event.preventDefault()
    handleQuickDelete()
  }
  
  // Ctrl/Cmd + D 删除任务（需要组合键，更安全）
  if ((event.ctrlKey || event.metaKey) && event.key === 'd') {
    event.preventDefault()
    handleQuickDelete()
  }
  
  // Ctrl/Cmd + G 生成子任务
  if ((event.ctrlKey || event.metaKey) && event.key === 'g') {
    event.preventDefault()
    generateSubtasks()
  }
  
  // Enter键或F2键编辑任务
  if (event.key === 'Enter' || event.key === 'F2') {
    event.preventDefault()
    startEditing()
  }
}

function handleDoubleClick(event: MouseEvent) {
  // 🔧 修复: 检查双击目标
  const target = event.target as HTMLElement
  
  // 如果双击的是输入框或按钮，不触发编辑
  if (target.matches('input, textarea, select, button')) {
    return
  }
  
  // 🔧 修复: 只在需要时阻止事件传播
  event.preventDefault()
  event.stopPropagation()
  
  console.log('✏️ [TaskCard] 双击编辑任务:', props.task.title)
  
  // 双击进入内联编辑模式而不是弹窗
  if (!isEditing.value) {
    startEditing()
  }
}

async function startEditing() {
  console.log('📝 [TaskCard] 开始编辑模式:', props.task.title)
  isEditing.value = true
  editTitle.value = props.task.title
  editDescription.value = props.task.description
  editUrgency.value = props.task.urgency
  editEstimatedHours.value = props.task.estimated_hours || 0
  
  await nextTick()
  if (titleInput.value) {
    titleInput.value.focus()
  }
}

function startConnection(portPosition: 'top' | 'right' | 'bottom' | 'left', event?: MouseEvent) {
  if (!event) return
  
  // 🔧 修复: 确保连接事件不被统一拖拽系统拦截
  event.preventDefault()
  event.stopPropagation()
  event.stopImmediatePropagation()
  
  console.log('🔗 [TaskCard] 开始连接:', portPosition, 'task:', props.task.id)
  isConnecting.value = true
  
  emit('startConnection', props.task.id, event)
}

// 🔧 修复5: 增强缩放功能的事件处理
function startResize(event: MouseEvent, direction: string = 'se') {
  // 强制阻止所有事件传播，确保缩放功能不被拦截
  event.preventDefault()
  event.stopPropagation()
  event.stopImmediatePropagation()
  
  console.log('📏 [TaskCard] 开始缩放:', direction, props.task.title)
  
  // 设置resize状态，禁用不必要的CSS动画
  isResizing.value = true
  
  const startX = event.clientX
  const startY = event.clientY
  const startWidth = nodeWidth.value
  const startHeight = nodeHeight.value
  const minWidth = 200
  const minHeight = 100
  const headerHeight = 60
  const footerHeight = 40
  
  // 性能优化变量
  let rafId: number | null = null
  let lastFrameTime = 0
  const FRAME_THROTTLE = 8 // 120fps for ultra smooth resize
  let pendingUpdate = false
  
  // 缓存计算结果
  let cachedNewWidth = startWidth
  let cachedNewHeight = startHeight
  let cachedContentHeight = Math.max(40, startHeight - headerHeight - footerHeight)
  
  function handleMouseMove(e: MouseEvent) {
    // 🔧 修复6: 确保拖拽期间事件不被其他系统拦截
    e.preventDefault()
    e.stopPropagation()
    
    const now = performance.now()
    
    // 节流：限制计算频率
    if (now - lastFrameTime < FRAME_THROTTLE && !pendingUpdate) {
      return
    }
    
    const deltaX = e.clientX - startX
    const deltaY = e.clientY - startY
    
    let newWidth = startWidth
    let newHeight = startHeight
    
    // 根据方向计算新的尺寸 - 优化计算
    switch (direction) {
      case 'se': 
        newWidth = startWidth + deltaX
        newHeight = startHeight + deltaY
        break
      case 'sw': 
        newWidth = startWidth - deltaX
        newHeight = startHeight + deltaY
        break
      case 'ne': 
        newWidth = startWidth + deltaX
        newHeight = startHeight - deltaY
        break
      case 'nw': 
        newWidth = startWidth - deltaX
        newHeight = startHeight - deltaY
        break
      case 'n': 
        newHeight = startHeight - deltaY
        break
      case 's': 
        newHeight = startHeight + deltaY
        break
      case 'w': 
        newWidth = startWidth - deltaX
        break
      case 'e': 
        newWidth = startWidth + deltaX
        break
    }
    
    // 应用约束并缓存
    cachedNewWidth = Math.max(minWidth, newWidth)
    cachedNewHeight = Math.max(minHeight, newHeight)
    cachedContentHeight = Math.max(40, cachedNewHeight - headerHeight - footerHeight)
    
    // 标记需要更新
    pendingUpdate = true
    
    // 取消之前的 RAF
    if (rafId) {
      cancelAnimationFrame(rafId)
    }
    
    // 使用 RAF 批量更新 DOM
    rafId = requestAnimationFrame(() => {
      if (pendingUpdate) {
        // 批量更新，减少 DOM 操作
        nodeWidth.value = cachedNewWidth
        nodeHeight.value = cachedNewHeight  
        contentHeight.value = cachedContentHeight
        
        pendingUpdate = false
        lastFrameTime = performance.now()
      }
    })
  }
  
  function handleMouseUp(e: MouseEvent) {
    // 🔧 修复7: 确保缩放结束时事件不被拦截
    e.preventDefault()
    e.stopPropagation()
    
    console.log('📏 [TaskCard] 缩放结束:', direction, 'new size:', cachedNewWidth, 'x', cachedNewHeight)
    
    // 清理
    if (rafId) {
      cancelAnimationFrame(rafId)
      rafId = null
    }
    
    // 确保最终状态正确
    nodeWidth.value = cachedNewWidth
    nodeHeight.value = cachedNewHeight
    contentHeight.value = cachedContentHeight
    
    // 重新启用CSS动画
    setTimeout(() => {
      isResizing.value = false
    }, 100) // 延迟一帧确保resize完成
    
    document.removeEventListener('mousemove', handleMouseMove, { capture: true } as any)
    document.removeEventListener('mouseup', handleMouseUp, { capture: true } as any)
  }
  
  // 🔧 修复8: 使用捕获模式确保事件优先级
  document.addEventListener('mousemove', handleMouseMove, { capture: true })
  document.addEventListener('mouseup', handleMouseUp, { capture: true })
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
    
    if (editUrgency.value !== props.task.urgency) {
      updates.urgency = editUrgency.value
    }
    
    if (editEstimatedHours.value !== (props.task.estimated_hours || 0)) {
      updates.estimated_hours = editEstimatedHours.value
    }
    
    if (Object.keys(updates).length > 0) {
      await taskStore.updateTask(props.task.id, updates)
    }
    
    isEditing.value = false
  } catch (error) {
    console.error('Failed to update task:', error)
    // Reset editing state even if update fails
    isEditing.value = false
  }
}

function cancelEdit() {
  isEditing.value = false
  editTitle.value = props.task.title
  editDescription.value = props.task.description
  editUrgency.value = props.task.urgency
  editEstimatedHours.value = props.task.estimated_hours || 0
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
    
    await deleteTask()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete task:', error)
    }
  }
}

// 快捷删除函数 - 不需要确认，但会显示撤回选项
async function handleQuickDelete() {
  try {
    await deleteTask()
    showUndoMessage()
  } catch (error) {
    console.error('Failed to delete task:', error)
    ElMessage.error('删除任务失败')
  }
}

// 显示撤回消息
function showUndoMessage() {
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

// 实际的删除操作
async function deleteTask() {
  console.log('Deleting task:', props.task.id)
  await taskStore.deleteTask(props.task.id)
  console.log('Task deleted successfully')
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
    
    console.log('开始生成子任务...', {
      parentTitle: props.task.title,
      parentDescription: props.task.description,
      parentId: props.task.id
    })
    
    // 添加更详细的请求信息
    console.log('正在调用 taskStore.generateTaskSubtasks...')
    
    const subtasks = await taskStore.generateTaskSubtasks(
      props.task.title,
      props.task.description,
      5
    )
    
    console.log('收到AI生成的子任务:', subtasks)
    
    if (!subtasks || subtasks.length === 0) {
      console.warn('AI未生成任何子任务')
      ElMessage.warning('AI未生成任何子任务，请检查任务描述是否清晰')
      return
    }
    
    // 获取父任务的当前位置
    const baseX = (props.task.position_x || 0) + 300 // 在父任务右侧
    const baseY = (props.task.position_y || 0) - (subtasks.length * 60) // 向上偏移
    
    const createdSubtasks = []
    
    // 创建每个子任务
    for (let i = 0; i < subtasks.length; i++) {
      const subtask = subtasks[i]
      const taskData = {
        ...subtask,
        parent_id: props.task.id,
        module_id: props.task.module_id,
        position_x: baseX,
        position_y: baseY + (i * 140), // 垂直排列
        estimated_hours: subtask.estimated_hours || 1
      }
      
      console.log('创建子任务:', taskData)
      
      try {
        const newTask = await taskStore.createTask(taskData)
        createdSubtasks.push(newTask)
        console.log('子任务创建成功:', newTask)
        
        // 创建从父任务到子任务的依赖连线
        try {
          await taskStore.createDependency({
            from_task_id: props.task.id,
            to_task_id: newTask.id,
            dependency_type: 'subtask'
          })
          console.log('创建依赖连线成功:', props.task.id, '->', newTask.id)
        } catch (depError) {
          console.error('创建依赖连线失败:', depError)
        }
      } catch (taskError) {
        console.error('创建子任务失败:', taskError)
      }
    }
    
    // 刷新任务列表和依赖关系
    await Promise.all([
      taskStore.fetchTasks(),
      taskStore.fetchDependencies()
    ])
    
    emit('update', props.task)
    emit('subtasksCreated', { parentTask: props.task, subtasks: createdSubtasks })
    
    console.log(`子任务生成完成！创建了 ${createdSubtasks.length} 个子任务`)
    ElMessage.success(`成功生成并创建了 ${createdSubtasks.length} 个子任务`)
    
  } catch (error: unknown) {
    console.error('生成子任务失败:', error)
    console.error('Error details:', {
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
      response: (error as any).response?.data || (error as any).response || error
    })
    
    // 显示详细的错误提示
    const errorMessage = error instanceof Error ? error.message : String(error)
    const detailedMessage = (error as any).response?.data?.detail || (error as any).response?.data?.error || errorMessage
    
    ElMessage.error(`生成子任务失败: ${detailedMessage}`)
  } finally {
    generating.value = false
  }
}

// 连接结束事件处理
function handleConnectionEnd() {
  console.log('TaskCard: 收到连接结束事件，重置连接状态')
  isConnecting.value = false
}

// 生命周期钩子 - 键盘事件管理
onMounted(() => {
  // 添加全局键盘事件监听
  document.addEventListener('keydown', handleKeyDown)
  // 监听连接结束事件
  document.addEventListener('connection-ended', handleConnectionEnd)
})

onUnmounted(() => {
  // 清理键盘事件监听
  document.removeEventListener('keydown', handleKeyDown)
  // 清理连接结束事件监听
  document.removeEventListener('connection-ended', handleConnectionEnd)
})

// 监听选中状态变化，确保键盘事件只在选中时生效
watch(() => props.isSelected, (newValue) => {
  if (newValue) {
    // 任务被选中时，确保可以接收键盘事件
    nextTick(() => {
      nodeRef.value?.focus()
    })
  }
})

// 监听节点高度变化，动态计算内容区域高度
watch(() => nodeHeight.value, (newHeight) => {
  const headerHeight = 60
  const footerHeight = 40
  contentHeight.value = Math.max(40, newHeight - headerHeight - footerHeight)
}, { immediate: true })
</script>

<style scoped>
/* Modern Task Node - 高性能设计 */
.task-node {
  position: relative;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  user-select: none;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;
  min-width: 220px;
  max-width: 420px;
  backdrop-filter: blur(20px);
  /* 高性能优化 */
  will-change: width, height;
  contain: layout style paint;
  transform: translateZ(0); /* 强制GPU加速 */
  backface-visibility: hidden;
  perspective: 1000px;
  border-bottom: 3px solid transparent;
  /* 减少transition复杂度 - 只在非resize时生效 */
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
  /* 确保是可点击的 */
  pointer-events: auto;
  z-index: 1;
  /* 🔧 修复: 严格控制任务卡片的边界 */
  width: 240px; /* 默认宽度 */
  height: auto; /* 自适应高度 */
  min-height: 120px; /* 最小高度 */
  max-height: 600px; /* 最大高度，防止异常扩展 */
  /* 🔧 修复: 确保任务卡片不会意外覆盖其他元素 */
  isolation: isolate; /* 创建新的层叠上下文 */
  box-sizing: border-box;
}

/* 禁用resize时的hover效果，避免冲突 */
.task-node:hover:not(.resizing) {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15), 0 4px 20px rgba(102, 126, 234, 0.2);
  transform: translateZ(0) translateY(-2px); /* 减少transform复杂度 */
  border-color: rgba(102, 126, 234, 0.4);
  background: rgba(255, 255, 255, 0.98);
  border-bottom-color: rgba(102, 126, 234, 0.6);
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
  border-color: rgba(102, 126, 234, 0.8);
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.2), 0 8px 32px rgba(0, 0, 0, 0.15);
  transform: translateY(-6px) scale(1.02);
  z-index: 10;
  border-bottom-color: #667eea;
  background: rgba(255, 255, 255, 0.98);
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

/* 高性能编辑模式动画 */
.task-node.editing {
  border-color: rgba(34, 197, 94, 0.8);
  background: rgba(255, 255, 255, 0.98);
  border-bottom-color: #22c55e;
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.3);
  will-change: transform;
}

.task-node.editing::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, transparent, rgba(34, 197, 94, 0.1), transparent);
  border-radius: 18px;
  z-index: -1;
  animation: editing-shimmer 2s infinite ease-in-out;
  opacity: 0.6;
}

@keyframes editing-shimmer {
  0%, 100% { transform: translateX(-100%); }
  50% { transform: translateX(100%); }
}

/* 编辑模式下隐藏缩放手柄 */
.task-node.editing .resize-handles {
  display: none;
}

/* Enhanced Priority Border Strip */
.priority-strip {
  position: absolute;
  top: 0;
  left: 0;
  width: 5px;
  height: 100%;
  border-radius: 16px 0 0 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0.8;
}

.priority-strip.priority-0 { 
  background: linear-gradient(180deg, #ff4d4f 0%, #cf1322 100%);
  box-shadow: inset 2px 0 4px rgba(207, 19, 34, 0.3);
}
.priority-strip.priority-1 { 
  background: linear-gradient(180deg, #fa8c16 0%, #d46b08 100%);
  box-shadow: inset 2px 0 4px rgba(212, 107, 8, 0.3);
}
.priority-strip.priority-2 { 
  background: linear-gradient(180deg, #1890ff 0%, #096dd9 100%);
  box-shadow: inset 2px 0 4px rgba(9, 109, 217, 0.3);
}
.priority-strip.priority-3 { 
  background: linear-gradient(180deg, #52c41a 0%, #389e0d 100%);
  box-shadow: inset 2px 0 4px rgba(56, 158, 13, 0.3);
}
.priority-strip.priority-4 { 
  background: linear-gradient(180deg, #722ed1 0%, #531dab 100%);
  box-shadow: inset 2px 0 4px rgba(83, 29, 171, 0.3);
}

/* 四个边界连接点样式 */
.connection-ports {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10;
}

.connection-port {
  position: absolute;
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: auto;
  cursor: crosshair;
}

.task-node.selected .connection-port,
.task-node.connecting .connection-port {
  opacity: 1;
}

.task-node:hover .connection-port {
  opacity: 0.7;
}

.task-node.connecting {
  box-shadow: 0 0 0 2px var(--primary), var(--shadow-lg);
}

/* 顶部连接点 */
.port-top {
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
}

/* 右侧连接点 */
.port-right {
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
}

/* 底部连接点 */
.port-bottom {
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
}

/* 左侧连接点 */
.port-left {
  left: -6px;
  top: 50%;
  transform: translateY(-50%);
}

.port-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: var(--primary);
  border: 2px solid var(--card-bg);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.connection-port:hover .port-dot {
  transform: scale(1.3);
  background-color: var(--primary-hover);
  box-shadow: 0 0 12px var(--primary-light);
}

.connection-port.port-active .port-dot {
  background-color: var(--success);
  transform: scale(1.4);
  box-shadow: 0 0 16px var(--success-light);
  animation: connection-pulse 1.5s infinite;
}

@keyframes connection-pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1.4);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.6);
  }
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

/* Enhanced Resize Handles */
.resize-handles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 20; /* 提高 z-index */
}

.resize-handle {
  position: absolute;
  opacity: 0;
  transition: all 0.2s ease;
  background: rgba(102, 126, 234, 0.8);
  border: 2px solid rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  pointer-events: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  z-index: 21; /* 确保在最上层 */
}

.task-node:hover .resize-handle,
.task-node.selected .resize-handle {
  opacity: 0.8;
}

.resize-handle:hover {
  opacity: 1;
  transform: scale(1.3);
  background: rgba(102, 126, 234, 1);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  z-index: 22; /* hover 时更高的 z-index */
}

/* 角落缩放手柄 */
.corner-nw { top: -6px; left: -6px; width: 12px; height: 12px; cursor: nw-resize; }
.corner-ne { top: -6px; right: -6px; width: 12px; height: 12px; cursor: ne-resize; }
.corner-sw { bottom: -6px; left: -6px; width: 12px; height: 12px; cursor: sw-resize; }
.corner-se { bottom: -6px; right: -6px; width: 12px; height: 12px; cursor: se-resize; }

/* 边缘缩放手柄 */
.edge-n { top: -4px; left: 50%; transform: translateX(-50%); width: 20px; height: 8px; cursor: n-resize; border-radius: 4px; }
.edge-s { bottom: -4px; left: 50%; transform: translateX(-50%); width: 20px; height: 8px; cursor: s-resize; border-radius: 4px; }
.edge-w { left: -4px; top: 50%; transform: translateY(-50%); width: 8px; height: 20px; cursor: w-resize; border-radius: 4px; }
.edge-e { right: -4px; top: 50%; transform: translateY(-50%); width: 8px; height: 20px; cursor: e-resize; border-radius: 4px; }

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

/* 快捷删除函数 - 不需要确认，但会显示撤回选项 */

.task-node:hover .node-actions-area {
  opacity: 1;
  visibility: visible;
}

/* Footer Actions */
.footer-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: var(--radius-sm);
  background-color: var(--bg-elevated);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 12px;
}

.action-btn:hover {
  background-color: var(--primary-light);
  color: var(--primary);
  transform: scale(1.1);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.edit-btn:hover {
  background-color: var(--warning-light);
  color: var(--warning);
}

.delete-btn:hover {
  background-color: var(--danger-light);
  color: var(--danger);
}

.subtask-btn:hover {
  background-color: var(--success-light);
  color: var(--success);
}

/* New Three-Section Layout */
.card-header-fixed {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 12px 16px 8px 20px;
  border-bottom: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(8px);
  border-radius: 16px 16px 0 0;
  position: relative;
  z-index: 2; /* 确保头部在上层 */
  pointer-events: auto; /* 确保可以接收事件 */
  cursor: pointer; /* 显示为可点击 */
}

.card-body-resizable {
  padding: 12px 16px;
  overflow-y: auto;
  overflow-x: hidden; /* 防止水平溢出 */
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(4px);
  border-left: 5px solid transparent;
  transition: all 0.2s ease;
  position: relative;
  z-index: 1; /* 低于头部和底部 */
  cursor: pointer; /* 显示为可点击 */
  /* 🔧 修复: 防止内容溢出和意外扩展 */
  max-height: 400px; /* 设置最大高度 */
  contain: layout; /* 只包含布局，防止影响其他元素 */
  /* 🔧 修复: 确保元素不会意外扩展到其他区域 */
  width: 100%;
  box-sizing: border-box;
  /* 🔧 修复: 防止元素超出父容器边界 */
  max-width: 100%;
  /* 🔧 关键修复: 禁用指针事件，防止拦截其他任务的点击 */
  pointer-events: none;
}

/* 🔧 修复: 为需要交互的子元素恢复指针事件 */
.card-body-resizable input,
.card-body-resizable textarea,
.card-body-resizable select,
.card-body-resizable button,
.card-body-resizable .editing-fields,
.card-body-resizable .task-description,
.card-body-resizable [contenteditable="true"] {
  pointer-events: auto;
}

.card-footer-fixed {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px 8px 20px;
  border-top: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(8px);
  border-radius: 0 0 16px 16px;
  position: relative;
  z-index: 2; /* 确保底部在上层 */
  pointer-events: auto; /* 确保可以接收事件 */
}

/* Editing Fields Styling */
.editing-fields {
  margin-top: 12px;
  padding: 12px;
  background: rgba(34, 197, 94, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.field-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.field-row:last-child {
  margin-bottom: 0;
}

.field-row label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  min-width: 60px;
  flex-shrink: 0;
}

.urgency-select {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid var(--border-default);
  border-radius: 4px;
  background: var(--bg-elevated);
  font-size: 12px;
  color: var(--text-primary);
  cursor: pointer;
}

.urgency-select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.hours-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid var(--border-default);
  border-radius: 4px;
  background: var(--bg-elevated);
  font-size: 12px;
  color: var(--text-primary);
  width: 80px;
}

.hours-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

/* Editing Actions */
.editing-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.save-btn:hover {
  background-color: var(--success-light);
  color: var(--success);
}

.cancel-btn:hover {
  background-color: var(--danger-light);
  color: var(--danger);
}

/* Enhanced content area styling when editing */
.card-body-resizable:has(.editing-fields) {
  background: rgba(34, 197, 94, 0.02);
  border-left-color: rgba(34, 197, 94, 0.3);
}

/* Resize性能优化样式 */
.task-node.resizing {
  /* 禁用所有transition和animation，最大化性能 */
  transition: none !important;
  animation: none !important;
  will-change: width, height;
  pointer-events: none; /* 禁用鼠标事件避免冲突 */
}

.task-node.resizing * {
  /* 禁用子元素的transition */
  transition: none !important;
  animation: none !important;
}

.task-node.resizing .resize-handle {
  /* resize时保持handle可见 */
  pointer-events: auto;
  opacity: 1;
}

/* 优化backdrop-filter在resize时的性能 */
.task-node.resizing {
  backdrop-filter: none; /* 临时禁用backdrop-filter提升性能 */
}

/* 为GPU优化的层叠上下文 */
.task-node.resizing {
  transform: translateZ(0) scale3d(1, 1, 1);
  will-change: width, height, transform;
}
</style>