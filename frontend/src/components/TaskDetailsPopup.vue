<template>
  <Teleport to="body">
    <div 
      v-if="visible && task" 
      class="task-details-popup-overlay"
      @click="handleOverlayClick"
    >
      <div 
        class="task-details-popup"
        :style="popupStyle"
        @click.stop
      >
        <!-- Header -->
        <div class="popup-header">
          <h3>{{ task.title }}</h3>
          <div class="header-actions">
            <el-tag :type="urgencyType" size="small">P{{ task.urgency }}</el-tag>
            <el-button 
              type="text" 
              @click="closePopup"
              :icon="Close"
              size="small"
            />
          </div>
        </div>

        <!-- Content -->
        <div class="popup-content">
          <el-form label-position="top" size="small">
            <el-form-item label="标题">
              <el-input
                v-model="localTask.title"
                @blur="updateTask"
                placeholder="任务标题"
              />
            </el-form-item>

            <el-form-item label="描述">
              <el-input
                v-model="localTask.description"
                type="textarea"
                :rows="2"
                @blur="updateTask"
                placeholder="任务描述"
                :maxlength="200"
                show-word-limit
              />
            </el-form-item>

            <div class="form-row">
              <el-form-item label="优先级" class="form-item-half">
                <el-select v-model="localTask.urgency" @change="updateTask">
                  <el-option label="P0 - 紧急" :value="0" />
                  <el-option label="P1 - 高" :value="1" />
                  <el-option label="P2 - 中" :value="2" />
                  <el-option label="P3 - 低" :value="3" />
                  <el-option label="P4 - 待办" :value="4" />
                </el-select>
              </el-form-item>

              <el-form-item label="模块" class="form-item-half">
                <el-select
                  v-model="localTask.module_id"
                  @change="updateTask"
                  clearable
                  placeholder="选择模块"
                >
                  <el-option
                    v-for="module in modules"
                    :key="module.id"
                    :label="module.name"
                    :value="module.id"
                  />
                </el-select>
              </el-form-item>
            </div>

            <el-form-item label="父任务" v-if="availableParentTasks.length > 0">
              <el-select
                v-model="localTask.parent_id"
                @change="updateTask"
                clearable
                placeholder="选择父任务"
              >
                <el-option
                  v-for="parentTask in availableParentTasks.slice(0, 10)"
                  :key="parentTask.id"
                  :label="parentTask.title"
                  :value="parentTask.id"
                />
              </el-select>
            </el-form-item>
          </el-form>

          <!-- Metadata -->
          <div class="metadata-section">
            <h4>任务信息</h4>
            <div class="metadata-grid">
              <div class="metadata-item">
                <span class="label">创建时间:</span>
                <span class="value">{{ formatDate(task.created_at) }}</span>
              </div>
              <div class="metadata-item">
                <span class="label">更新时间:</span>
                <span class="value">{{ formatDate(task.updated_at) }}</span>
              </div>
              <div v-if="task.ocr_src" class="metadata-item">
                <span class="label">OCR 来源:</span>
                <span class="value">{{ task.ocr_src }}</span>
              </div>
            </div>
          </div>

          <!-- History -->
          <div class="history-section" v-if="taskHistory.length > 0 || historyLoading">
            <div class="section-header">
              <h4>变更历史</h4>
              <el-button
                size="small"
                @click="refreshHistory"
                :loading="historyLoading"
                text
              >
                刷新
              </el-button>
            </div>

            <div v-if="historyLoading" class="history-loading">
              <el-skeleton :rows="1" animated />
            </div>

            <div v-else class="history-list">
              <div
                v-for="entry in taskHistory.slice(0, 3)"
                :key="entry.id"
                class="history-item"
              >
                <div class="history-meta">
                  <span class="field">{{ entry.field }}</span>
                  <span class="time">{{ formatDate(entry.ts) }}</span>
                </div>
                <div class="history-change">
                  <span class="old-value">{{ entry.old_val || '(空)' }}</span>
                  <el-icon class="arrow"><Right /></el-icon>
                  <span class="new-value">{{ entry.new_val || '(空)' }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="popup-actions">
            <el-button
              type="danger"
              @click="deleteTask"
              :loading="deleteLoading"
              size="small"
            >
              删除任务
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElTag, ElButton, ElIcon, ElSkeleton, ElMessageBox } from 'element-plus'
import { Close, Right } from '@element-plus/icons-vue'
import { useTaskStore, type Task } from '@/stores/tasks'

interface Props {
  visible: boolean
  task: Task | null
  position: { x: number; y: number }
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:visible': [value: boolean]
  close: []
}>()

const taskStore = useTaskStore()

const localTask = ref<Partial<Task>>({})
const historyLoading = ref(false)
const deleteLoading = ref(false)

// Computed properties
const urgencyType = computed(() => {
  if (!props.task) return 'info'
  const urgency = props.task.urgency
  if (urgency === 0) return 'danger'   // P0 - Critical
  if (urgency === 1) return 'warning'  // P1 - High
  if (urgency === 2) return 'primary'  // P2 - Medium
  if (urgency === 3) return 'success'  // P3 - Low
  return 'info'  // P4 - Backlog
})

const modules = computed(() => taskStore.modules)
const taskHistory = computed(() => taskStore.taskHistory)

const availableParentTasks = computed(() => {
  if (!props.task) return []
  return taskStore.tasks.filter(t => 
    t.id !== props.task!.id && 
    t.parent_id !== props.task!.id
  )
})

const popupStyle = computed(() => {
  if (!props.position) return {}
  
  const maxWidth = 380
  const estimatedHeight = calculateEstimatedHeight()
  const maxHeight = Math.min(estimatedHeight + 50, window.innerHeight - 100)
  
  // Calculate position to keep popup within viewport
  let x = props.position.x - maxWidth / 2
  let y = props.position.y
  
  // Adjust x to stay within viewport
  if (x < 20) x = 20
  if (x + maxWidth > window.innerWidth - 20) {
    x = window.innerWidth - maxWidth - 20
  }
  
  // Adjust y to stay within viewport
  if (y + maxHeight > window.innerHeight - 20) {
    y = props.position.y - maxHeight - 20
  }
  
  return {
    left: `${x}px`,
    top: `${y}px`,
    width: `${maxWidth}px`,
    height: `${maxHeight}px`
  }
})

function calculateEstimatedHeight() {
  if (!props.task) return 400
  
  let height = 100 // header
  height += 120 // title + description form items
  height += 60 // priority + module row
  
  if (availableParentTasks.value.length > 0) {
    height += 50 // parent task field
  }
  
  height += 80 // metadata section
  
  if (taskHistory.value.length > 0) {
    height += 50 + (taskHistory.value.slice(0, 3).length * 35) // history section
  }
  
  height += 60 // actions
  
  return height
}

// Watchers
watch(() => props.task, (newTask) => {
  if (newTask) {
    localTask.value = { ...newTask }
  }
}, { immediate: true })

// Methods
function closePopup() {
  emit('update:visible', false)
  emit('close')
}

function handleOverlayClick() {
  closePopup()
}

async function updateTask() {
  if (!props.task) return
  
  const updates: Partial<Task> = {}
  
  if (localTask.value.title !== props.task.title) {
    updates.title = localTask.value.title || ''
  }
  
  if (localTask.value.description !== props.task.description) {
    updates.description = localTask.value.description || ''
  }
  
  if (localTask.value.urgency !== props.task.urgency) {
    updates.urgency = localTask.value.urgency || 2
  }
  
  if (localTask.value.module_id !== props.task.module_id) {
    updates.module_id = localTask.value.module_id || null
  }
  
  if (localTask.value.parent_id !== props.task.parent_id) {
    updates.parent_id = localTask.value.parent_id || null
  }
  
  if (Object.keys(updates).length > 0) {
    try {
      await taskStore.updateTask(props.task.id, updates)
    } catch (error) {
      console.error('Failed to update task:', error)
      localTask.value = { ...props.task }
    }
  }
}

async function refreshHistory() {
  if (!props.task) return
  
  historyLoading.value = true
  try {
    await taskStore.fetchTaskHistory(props.task.id)
  } catch (error) {
    console.error('Failed to fetch history:', error)
  } finally {
    historyLoading.value = false
  }
}

async function deleteTask() {
  if (!props.task) return
  
  try {
    await ElMessageBox.confirm(
      '确定要删除这个任务吗？此操作无法撤销。',
      '删除任务',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    deleteLoading.value = true
    await taskStore.deleteTask(props.task.id)
    closePopup()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete task:', error)
    }
  } finally {
    deleteLoading.value = false
  }
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleString('zh-CN')
}

// Load history when popup opens
watch(() => props.visible, (visible) => {
  if (visible && props.task) {
    refreshHistory()
  }
})
</script>

<style scoped>
.task-details-popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(12px);
  z-index: 1000;
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

/* Enhanced Task Details Popup */
.task-details-popup {
  position: absolute;
  width: 400px;
  min-height: 300px;
  max-height: 80vh;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 20px;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.15),
    0 8px 32px rgba(102, 126, 234, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: popupSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes popupSlideIn {
  from {
    transform: translateY(-20px) scale(0.95);
    opacity: 0;
  }
  to {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

/* Enhanced Popup Header */
.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  position: relative;
}

.popup-header::before {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 20%;
  width: 60%;
  height: 2px;
  background: linear-gradient(90deg, rgba(102, 126, 234, 0.8), rgba(118, 75, 162, 0.8));
  border-radius: 1px;
}

.popup-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #1a202c;
  letter-spacing: -0.025em;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-actions .el-tag {
  border-radius: 8px;
  font-weight: 600;
  padding: 6px 12px;
}

.header-actions .el-button {
  border-radius: 10px;
  transition: all 0.3s ease;
}

.header-actions .el-button:hover {
  background: rgba(102, 126, 234, 0.1);
  transform: scale(1.1);
}

/* Enhanced Popup Content */
.popup-content {
  padding: 20px 24px;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%);
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-item-half {
  flex: 1;
}

/* Enhanced Metadata Section */
.metadata-section {
  margin-top: 24px;
  padding: 20px;
  border-top: 2px solid rgba(102, 126, 234, 0.1);
  background: rgba(255, 255, 255, 0.7);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}

.metadata-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 700;
  color: rgba(102, 126, 234, 0.9);
  display: flex;
  align-items: center;
  gap: 8px;
}

.metadata-section h4::before {
  content: '📊';
  font-size: 14px;
}

.metadata-grid {
  display: grid;
  gap: 12px;
}

.metadata-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  padding: 10px 16px;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 10px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  transition: all 0.3s ease;
}

.metadata-item:hover {
  background: rgba(102, 126, 234, 0.1);
  transform: translateX(4px);
}

.metadata-item .label {
  color: rgba(102, 126, 234, 0.8);
  font-weight: 600;
}

.metadata-item .value {
  color: #1a202c;
  font-weight: 500;
}

/* Enhanced History Section */
.history-section {
  margin-top: 24px;
  padding: 20px;
  border-top: 2px solid rgba(102, 126, 234, 0.1);
  background: rgba(255, 255, 255, 0.7);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: rgba(102, 126, 234, 0.9);
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-header h4::before {
  content: '📝';
  font-size: 14px;
}

.section-header .el-button {
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.section-header .el-button:hover {
  background: rgba(102, 126, 234, 0.1);
  color: rgba(102, 126, 234, 0.9);
}

.history-loading {
  padding: 16px 0;
}

.no-history {
  text-align: center;
  color: rgba(102, 126, 234, 0.6);
  font-size: 14px;
  padding: 24px;
  font-style: italic;
  font-weight: 500;
}

.history-list {
  max-height: none;
  overflow-y: hidden;
}

.history-item {
  padding: 12px 16px;
  border: 2px solid rgba(102, 126, 234, 0.1);
  border-radius: 12px;
  margin-bottom: 10px;
  background: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.history-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
  transition: left 0.6s ease;
}

.history-item:hover {
  border-color: rgba(102, 126, 234, 0.3);
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.history-item:hover::before {
  left: 100%;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.history-meta .field {
  font-weight: 700;
  color: rgba(102, 126, 234, 0.9);
  text-transform: capitalize;
  background: rgba(102, 126, 234, 0.1);
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
}

.history-meta .time {
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
}

.history-change {
  display: flex;
  align-items: center;
  gap: 8px;
}

.old-value {
  color: #ef4444;
  text-decoration: line-through;
  max-width: 40%;
  word-break: break-word;
  font-size: 12px;
  font-weight: 500;
  background: rgba(239, 68, 68, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
}

.new-value {
  color: #10b981;
  max-width: 40%;
  word-break: break-word;
  font-size: 12px;
  font-weight: 500;
  background: rgba(16, 185, 129, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
}

.arrow {
  color: rgba(102, 126, 234, 0.6);
  font-size: 14px;
  font-weight: 600;
}

/* Enhanced Popup Actions */
.popup-actions {
  margin-top: 24px;
  padding: 20px 0 0;
  border-top: 2px solid rgba(102, 126, 234, 0.1);
  text-align: center;
}

.popup-actions .el-button {
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.popup-actions .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
}

/* Enhanced Element Plus form overrides */
:deep(.el-form-item) {
  margin-bottom: 16px;
}

:deep(.el-form-item__label) {
  font-size: 14px;
  font-weight: 600;
  color: rgba(102, 126, 234, 0.8);
  margin-bottom: 8px;
}

:deep(.el-input) {
  border-radius: 10px;
}

:deep(.el-input__wrapper) {
  border-radius: 10px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

:deep(.el-input__wrapper:hover) {
  border-color: rgba(102, 126, 234, 0.4);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: rgba(102, 126, 234, 0.6);
  box-shadow: 
    0 4px 16px rgba(102, 126, 234, 0.2),
    0 0 0 3px rgba(102, 126, 234, 0.1);
}

:deep(.el-input__inner) {
  font-size: 14px;
  font-weight: 500;
  color: #1a202c;
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-select .el-input__wrapper) {
  border-radius: 10px;
}

:deep(.el-textarea) {
  border-radius: 10px;
}

:deep(.el-textarea__inner) {
  border-radius: 10px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  font-size: 14px;
  font-weight: 500;
  color: #1a202c;
}

:deep(.el-textarea__inner:hover) {
  border-color: rgba(102, 126, 234, 0.4);
}

:deep(.el-textarea__inner:focus) {
  border-color: rgba(102, 126, 234, 0.6);
  box-shadow: 
    0 4px 16px rgba(102, 126, 234, 0.2),
    0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Scrollbar Styling */
.popup-content::-webkit-scrollbar {
  width: 6px;
}

.popup-content::-webkit-scrollbar-track {
  background: rgba(102, 126, 234, 0.05);
  border-radius: 3px;
}

.popup-content::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 3px;
}

.popup-content::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}
</style>