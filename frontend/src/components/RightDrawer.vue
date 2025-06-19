<template>
  <el-drawer
    v-model="visible"
    title="Task Properties"
    direction="rtl"
    :size="350"
    :with-header="true"
  >
    <div v-if="task" class="drawer-content">
      <!-- Task Header -->
      <div class="task-header">
        <h3>{{ task.title }}</h3>
        <el-tag :type="urgencyType" size="small">P{{ task.urgency }}</el-tag>
      </div>

      <!-- Task Properties -->
      <el-form label-position="top" class="properties-form">
        <el-form-item label="Title">
          <el-input
            v-model="localTask.title"
            @blur="updateTask"
            placeholder="Task title"
          />
        </el-form-item>

        <el-form-item label="Description">
          <el-input
            v-model="localTask.description"
            type="textarea"
            :rows="3"
            @blur="updateTask"
            placeholder="Task description"
          />
        </el-form-item>

        <el-form-item label="Priority">
          <el-select v-model="localTask.urgency" @change="updateTask" class="w-full">
            <el-option label="P0 - Critical" :value="0" />
            <el-option label="P1 - High" :value="1" />
            <el-option label="P2 - Medium" :value="2" />
            <el-option label="P3 - Low" :value="3" />
            <el-option label="P4 - Backlog" :value="4" />
          </el-select>
        </el-form-item>

        <el-form-item label="Module">
          <el-select
            v-model="localTask.module_id"
            @change="updateTask"
            class="w-full"
            clearable
            placeholder="Select module"
          >
            <el-option
              v-for="module in modules"
              :key="module.id"
              :label="module.name"
              :value="module.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="Parent Task">
          <el-select
            v-model="localTask.parent_id"
            @change="updateTask"
            class="w-full"
            clearable
            placeholder="Select parent task"
          >
            <el-option
              v-for="parentTask in availableParentTasks"
              :key="parentTask.id"
              :label="parentTask.title"
              :value="parentTask.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <!-- Task Metadata -->
      <div class="metadata">
        <el-divider content-position="left">Metadata</el-divider>
        <div class="metadata-item">
          <span class="label">Created:</span>
          <span class="value">{{ formatDate(task.created_at) }}</span>
        </div>
        <div class="metadata-item">
          <span class="label">Updated:</span>
          <span class="value">{{ formatDate(task.updated_at) }}</span>
        </div>
        <div v-if="task.ocr_src" class="metadata-item">
          <span class="label">OCR Source:</span>
          <span class="value">{{ task.ocr_src }}</span>
        </div>
      </div>

      <!-- History Section -->
      <div class="history-section">
        <el-divider content-position="left">
          <span>History</span>
          <el-button
            size="small"
            @click="refreshHistory"
            :loading="historyLoading"
            style="margin-left: 8px"
          >
            Refresh
          </el-button>
        </el-divider>

        <div v-if="historyLoading" class="history-loading">
          <el-skeleton :rows="3" animated />
        </div>

        <div v-else-if="taskHistory.length === 0" class="no-history">
          No changes recorded yet
        </div>

        <div v-else class="history-list">
          <div
            v-for="entry in taskHistory"
            :key="entry.id"
            class="history-item"
          >
            <div class="history-header">
              <span class="field">{{ entry.field }}</span>
              <span class="timestamp">{{ formatDate(entry.ts) }}</span>
            </div>
            <div class="history-change">
              <span class="old-value">{{ entry.old_val || '(empty)' }}</span>
              <el-icon class="arrow"><Right /></el-icon>
              <span class="new-value">{{ entry.new_val || '(empty)' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="actions">
        <el-divider />
        <el-button
          type="danger"
          @click="deleteTask"
          :loading="deleteLoading"
          class="w-full"
        >
          Delete Task
        </el-button>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElDrawer, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElTag, ElDivider, ElButton, ElIcon, ElSkeleton, ElMessageBox } from 'element-plus'
import { Right } from '@element-plus/icons-vue'
import { useTaskStore, type Task } from '@/stores/tasks'

interface Props {
  visible: boolean
  task: Task | null
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
const visible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

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
  // Exclude self and its descendants to prevent circular references
  return taskStore.tasks.filter(t => 
    t.id !== props.task!.id && 
    t.parent_id !== props.task!.id
  )
})

// Watchers
watch(() => props.task, (newTask) => {
  if (newTask) {
    localTask.value = { ...newTask }
  }
}, { immediate: true })

// Methods
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
      // Revert local changes on error
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
      'Are you sure you want to delete this task? This action cannot be undone.',
      'Delete Task',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
      }
    )
    
    deleteLoading.value = true
    await taskStore.deleteTask(props.task.id)
    emit('close')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete task:', error)
    }
  } finally {
    deleteLoading.value = false
  }
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleString()
}
</script>

<style scoped>
.drawer-content {
  padding: 0 8px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.task-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.properties-form {
  margin-bottom: 20px;
}

.w-full {
  width: 100%;
}

.metadata {
  margin-bottom: 20px;
}

.metadata-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.metadata-item .label {
  font-weight: 500;
  color: #666;
}

.metadata-item .value {
  color: #333;
  font-size: 14px;
}

.history-section {
  margin-bottom: 20px;
}

.history-loading {
  padding: 16px;
}

.no-history {
  text-align: center;
  color: #999;
  padding: 20px;
  font-style: italic;
}

.history-list {
  max-height: 300px;
  overflow-y: auto;
}

.history-item {
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 6px;
  margin-bottom: 8px;
  background: #fafafa;
}

.history-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.history-header .field {
  font-weight: 600;
  color: #333;
  text-transform: capitalize;
}

.history-header .timestamp {
  font-size: 12px;
  color: #666;
}

.history-change {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.old-value {
  color: #f56c6c;
  text-decoration: line-through;
  max-width: 40%;
  word-break: break-word;
}

.new-value {
  color: #67c23a;
  max-width: 40%;
  word-break: break-word;
}

.arrow {
  color: #999;
}

.actions {
  margin-top: 20px;
}

/* Element Plus drawer content scrolling */
:deep(.el-drawer__body) {
  padding: 20px;
  overflow-y: auto;
}
</style>