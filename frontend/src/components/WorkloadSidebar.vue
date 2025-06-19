<template>
  <div class="workload-sidebar">
    <div class="sidebar-header">
      <h3>📊 Daily Workload</h3>
      <el-date-picker
        v-model="selectedDate"
        type="date"
        placeholder="Select date"
        size="small"
        @change="fetchWorkload"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
      />
    </div>

    <div class="workload-summary" v-if="workload">
      <div class="capacity-bar">
        <div class="capacity-label">
          <span>{{ workload.total_hours.toFixed(1) }}h / {{ workload.capacity_hours }}h</span>
          <span :class="['conflict-indicator', workload.conflict_level]">
            {{ workload.workload_percentage.toFixed(0) }}%
          </span>
        </div>
        <div class="capacity-progress">
          <div
            class="capacity-fill"
            :class="workload.conflict_level"
            :style="{ width: Math.min(workload.workload_percentage, 100) + '%' }"
          ></div>
        </div>
      </div>

      <div class="conflict-status">
        <div v-if="workload.conflict_level === 'green'" class="status-message green">
          ✅ Workload is manageable
        </div>
        <div v-else-if="workload.conflict_level === 'yellow'" class="status-message yellow">
          ⚠️ High workload - monitor progress
        </div>
        <div v-else class="status-message red">
          🚨 Overloaded - reschedule tasks
        </div>
      </div>
    </div>

    <div class="task-breakdown" v-if="workload && workload.tasks.length > 0">
      <h4>Today's Tasks</h4>
      <div class="task-list">
        <div
          v-for="task in workload.tasks"
          :key="task.id"
          class="workload-task"
          :class="getTaskConflictClass(task)"
        >
          <div class="task-info">
            <div class="task-title">{{ task.title }}</div>
            <div class="task-meta">
              <span class="task-hours">{{ task.estimated_hours }}h</span>
              <span :class="['task-priority', `priority-${task.urgency}`]">
                P{{ task.urgency }}
              </span>
            </div>
          </div>
          <div class="task-actions">
            <el-button size="small" @click="adjustHours(task)">⏱️</el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="empty-state" v-else-if="workload && workload.tasks.length === 0">
      <p>No tasks scheduled for this date</p>
    </div>

    <div class="loading-state" v-if="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>Analyzing workload...</span>
    </div>

    <!-- Hours Adjustment Dialog -->
    <el-dialog v-model="showHoursDialog" title="Adjust Estimated Hours" width="400px">
      <el-form v-if="selectedTask">
        <el-form-item label="Task">
          <div>{{ selectedTask.title }}</div>
        </el-form-item>
        <el-form-item label="Estimated Hours">
          <el-input-number
            v-model="newHours"
            :min="0.5"
            :max="24"
            :step="0.5"
            :precision="1"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showHoursDialog = false">Cancel</el-button>
        <el-button type="primary" @click="saveHours">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElDatePicker, ElButton, ElDialog, ElForm, ElFormItem, ElInputNumber, ElIcon, ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import axios from 'axios'
import { useTaskStore } from '@/stores/tasks'

interface WorkloadData {
  total_hours: number
  capacity_hours: number
  workload_percentage: number
  conflict_level: 'green' | 'yellow' | 'red'
  tasks: Array<{
    id: number
    title: string
    description: string
    urgency: number
    estimated_hours: number
    due_date?: string
  }>
  success: boolean
  error?: string
}

const taskStore = useTaskStore()

const selectedDate = ref(new Date().toISOString().split('T')[0])
const workload = ref<WorkloadData | null>(null)
const loading = ref(false)
const showHoursDialog = ref(false)
const selectedTask = ref<any>(null)
const newHours = ref(0)

const fetchWorkload = async () => {
  loading.value = true
  try {
    const response = await axios.post<WorkloadData>('/api/workload/analyze', {
      date: selectedDate.value
    })
    
    workload.value = response.data
  } catch (error) {
    console.error('Failed to fetch workload:', error)
    ElMessage.error('Failed to analyze workload')
  } finally {
    loading.value = false
  }
}

const getTaskConflictClass = (task: any) => {
  if (task.urgency <= 1 && task.estimated_hours >= 6) {
    return 'high-conflict'
  } else if (task.estimated_hours >= 4) {
    return 'medium-conflict'
  }
  return 'low-conflict'
}

const adjustHours = (task: any) => {
  selectedTask.value = task
  newHours.value = task.estimated_hours
  showHoursDialog.value = true
}

const saveHours = async () => {
  if (!selectedTask.value) return
  
  try {
    await taskStore.updateTask(selectedTask.value.id, {
      estimated_hours: newHours.value
    })
    
    showHoursDialog.value = false
    selectedTask.value = null
    
    // Refresh workload analysis
    await fetchWorkload()
    
    ElMessage.success('Hours updated successfully')
  } catch (error) {
    console.error('Failed to update hours:', error)
    ElMessage.error('Failed to update hours')
  }
}

onMounted(() => {
  fetchWorkload()
})

// Watch for task store changes and refresh workload
watch(() => taskStore.tasks.length, () => {
  fetchWorkload()
})
</script>

<style scoped>
.workload-sidebar {
  width: 300px;
  background: white;
  border-left: 1px solid #eee;
  padding: 16px;
  overflow-y: auto;
  height: 100%;
}

.sidebar-header {
  margin-bottom: 20px;
}

.sidebar-header h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.workload-summary {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.capacity-bar {
  margin-bottom: 12px;
}

.capacity-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
}

.conflict-indicator {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.conflict-indicator.green {
  background: #f6ffed;
  color: #52c41a;
}

.conflict-indicator.yellow {
  background: #feffe6;
  color: #fadb14;
}

.conflict-indicator.red {
  background: #fff1f0;
  color: #ff4d4f;
}

.capacity-progress {
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.capacity-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.capacity-fill.green {
  background: #52c41a;
}

.capacity-fill.yellow {
  background: #fadb14;
}

.capacity-fill.red {
  background: #ff4d4f;
}

.conflict-status {
  margin-top: 12px;
}

.status-message {
  font-size: 12px;
  padding: 8px;
  border-radius: 4px;
  text-align: center;
}

.status-message.green {
  background: #f6ffed;
  color: #52c41a;
}

.status-message.yellow {
  background: #feffe6;
  color: #d48806;
}

.status-message.red {
  background: #fff1f0;
  color: #ff4d4f;
}

.task-breakdown h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.task-list {
  max-height: 400px;
  overflow-y: auto;
}

.workload-task {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
  background: white;
}

.workload-task.high-conflict {
  border-color: #ff4d4f;
  background: #fff1f0;
}

.workload-task.medium-conflict {
  border-color: #fadb14;
  background: #feffe6;
}

.workload-task.low-conflict {
  border-color: #52c41a;
  background: #f6ffed;
}

.task-info {
  flex: 1;
}

.task-title {
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 4px;
  line-height: 1.3;
}

.task-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.task-hours {
  font-size: 11px;
  color: #666;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 8px;
}

.task-priority {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
  font-weight: bold;
}

.priority-0 { background: #ff4d4f; color: white; }
.priority-1 { background: #fa8c16; color: white; }
.priority-2 { background: #fadb14; color: #000; }
.priority-3 { background: #52c41a; color: white; }
.priority-4 { background: #1890ff; color: white; }

.task-actions {
  margin-left: 8px;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 40px 20px;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #666;
}
</style>