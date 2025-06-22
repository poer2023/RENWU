<template>
  <div class="workload-sidebar">
    <div class="sidebar-header">
      <h3>📊 Daily Workload</h3>
      <el-date-picker
        v-model="selectedDate"
        type="date"
        placeholder="选择日期"
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
          ✅ 工作负荷可管理
        </div>
        <div v-else-if="workload.conflict_level === 'yellow'" class="status-message yellow">
          ⚠️ 高工作负荷 - 监控进度
        </div>
        <div v-else class="status-message red">
          🚨 工作超负荷 - 重新安排任务
        </div>
      </div>
    </div>

    <div class="task-breakdown" v-if="workload && workload.tasks.length > 0">
      <h4>今日任务</h4>
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
      <p>此日期没有安排任务</p>
    </div>

    <div class="loading-state" v-if="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>分析工作负荷中...</span>
    </div>

    <!-- Hours Adjustment Dialog -->
    <el-dialog v-model="showHoursDialog" title="调整预估时长" width="400px">
      <el-form v-if="selectedTask">
        <el-form-item label="任务">
          <div>{{ selectedTask.title }}</div>
        </el-form-item>
        <el-form-item label="预估时长">
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
        <el-button @click="showHoursDialog = false">取消</el-button>
        <el-button type="primary" @click="saveHours">保存</el-button>
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
    ElMessage.error('分析工作负荷失败')
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
    
    ElMessage.success('时长更新成功')
  } catch (error) {
    console.error('Failed to update hours:', error)
    ElMessage.error('更新时长失败')
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
/* Modern Workload Sidebar - Enhanced Design */
.workload-sidebar {
  width: 320px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%);
  border-left: 1px solid rgba(226, 232, 240, 0.8);
  padding: 24px;
  overflow-y: auto;
  height: 100%;
  backdrop-filter: blur(20px);
  border-left: 3px solid rgba(102, 126, 234, 0.3);
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.05);
}

/* Enhanced Sidebar Header */
.sidebar-header {
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
  position: relative;
}

.sidebar-header::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, rgba(102, 126, 234, 0.8), rgba(118, 75, 162, 0.8));
  border-radius: 1px;
}

.sidebar-header h3 {
  margin: 0 0 16px 0;
  font-size: 20px;
  font-weight: 700;
  color: #1a202c;
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: -0.025em;
}

/* Enhanced Workload Summary */
.workload-summary {
  margin-bottom: 32px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.08),
    0 4px 16px rgba(102, 126, 234, 0.05);
  backdrop-filter: blur(20px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: summarySlideIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes summarySlideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.workload-summary:hover {
  border-color: rgba(102, 126, 234, 0.3);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.12),
    0 6px 20px rgba(102, 126, 234, 0.1);
  transform: translateY(-2px);
}

/* Enhanced Capacity Bar */
.capacity-bar {
  margin-bottom: 16px;
}

.capacity-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #1a202c;
}

.conflict-indicator {
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.5px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: indicatorPulse 2s ease-in-out infinite;
}

@keyframes indicatorPulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.conflict-indicator.green {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.15));
  color: rgba(16, 185, 129, 0.9);
  border: 1px solid rgba(16, 185, 129, 0.3);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
}

.conflict-indicator.yellow {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.15));
  color: rgba(180, 83, 9, 0.9);
  border: 1px solid rgba(245, 158, 11, 0.3);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.2);
}

.conflict-indicator.red {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.15));
  color: rgba(239, 68, 68, 0.9);
  border: 1px solid rgba(239, 68, 68, 0.3);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.2);
}

.capacity-progress {
  height: 12px;
  background: rgba(241, 245, 249, 0.8);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.6);
  position: relative;
}

.capacity-progress::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 50%, transparent 100%);
  animation: progressShimmer 2s ease-in-out infinite;
}

@keyframes progressShimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.capacity-fill {
  height: 100%;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.capacity-fill::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.4) 50%, transparent 100%);
  animation: fillShimmer 3s ease-in-out infinite;
}

@keyframes fillShimmer {
  0%, 100% {
    transform: translateX(-100%);
  }
  50% {
    transform: translateX(100%);
  }
}

.capacity-fill.green {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.3);
}

.capacity-fill.yellow {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.3);
}

.capacity-fill.red {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.3);
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