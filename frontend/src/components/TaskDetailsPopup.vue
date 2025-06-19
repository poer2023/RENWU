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
  background: rgba(0, 0, 0, 0.3);
  z-index: 2000;
  backdrop-filter: blur(2px);
}

.task-details-popup {
  position: absolute;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  border: 1px solid #e4e7ed;
  animation: popupSlideIn 0.2s ease-out;
  display: flex;
  flex-direction: column;
}

@keyframes popupSlideIn {
  from {
    transform: translateY(-10px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
}

.popup-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.popup-content {
  padding: 16px;
  flex: 1;
  overflow-y: hidden;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-item-half {
  flex: 1;
}

.metadata-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.metadata-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.metadata-grid {
  display: grid;
  gap: 8px;
}

.metadata-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.metadata-item .label {
  color: #909399;
  font-weight: 500;
}

.metadata-item .value {
  color: #303133;
}

.history-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.history-loading {
  padding: 12px 0;
}

.no-history {
  text-align: center;
  color: #909399;
  font-size: 12px;
  padding: 20px;
  font-style: italic;
}

.history-list {
  max-height: none;
  overflow-y: hidden;
}

.history-item {
  padding: 8px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 6px;
  background: #fafafa;
  font-size: 12px;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.history-meta .field {
  font-weight: 600;
  color: #303133;
  text-transform: capitalize;
}

.history-meta .time {
  color: #909399;
  font-size: 11px;
}

.history-change {
  display: flex;
  align-items: center;
  gap: 6px;
}

.old-value {
  color: #f56c6c;
  text-decoration: line-through;
  max-width: 40%;
  word-break: break-word;
  font-size: 11px;
}

.new-value {
  color: #67c23a;
  max-width: 40%;
  word-break: break-word;
  font-size: 11px;
}

.arrow {
  color: #909399;
  font-size: 12px;
}

.popup-actions {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
  text-align: center;
}

/* Element Plus form overrides */
:deep(.el-form-item) {
  margin-bottom: 12px;
}

:deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 500;
}

:deep(.el-input__inner) {
  font-size: 12px;
}

:deep(.el-select) {
  width: 100%;
}
</style>