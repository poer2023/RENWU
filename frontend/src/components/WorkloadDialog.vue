<template>
  <el-dialog 
    v-model="visible" 
    title="工作量分析" 
    width="600px"
    @close="handleClose"
  >
    <div v-if="analysis" class="workload-analysis">
      <div class="workload-summary">
        <div class="summary-item">
          <span class="label">总工时:</span>
          <span class="value">{{ safeTotalHours }}小时</span>
        </div>
        <div class="summary-item">
          <span class="label">日容量:</span>
          <span class="value">{{ analysis.capacity_hours || 8 }}小时</span>
        </div>
        <div class="summary-item">
          <span class="label">负载率:</span>
          <span class="value" :class="getWorkloadColor(safeWorkloadPercentage)">
            {{ safeWorkloadPercentage }}%
          </span>
        </div>
      </div>
      
      <el-alert 
        :title="getWorkloadMessage(analysis.conflict_level)"
        :type="getWorkloadAlertType(analysis.conflict_level)"
        :closable="false"
        style="margin: 16px 0;"
      />
      
      <div v-if="analysis.tasks && analysis.tasks.length > 0" class="task-breakdown">
        <h4>任务分解:</h4>
        <div class="task-list">
          <div 
            v-for="task in analysis.tasks" 
            :key="task.id"
            class="task-item"
          >
            <span class="task-title">{{ task.title }}</span>
            <span class="task-hours">{{ task.estimated_hours }}小时</span>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else class="empty-analysis">
      <p>暂无工作量分析数据</p>
    </div>
    
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
      <el-button @click="$emit('refresh')" :loading="loading">
        刷新分析
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElDialog, ElButton, ElAlert } from 'element-plus'

interface Props {
  modelValue: boolean
  analysis?: any
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'refresh': []
}>()

const visible = ref(props.modelValue)

// Watch for external changes
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

// Watch for internal changes
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// Computed
const safeTotalHours = computed(() => {
  const hours = props.analysis?.total_hours
  return typeof hours === 'number' && isFinite(hours) ? hours : 0
})

const safeWorkloadPercentage = computed(() => {
  const percentage = props.analysis?.workload_percentage
  const value = typeof percentage === 'number' && isFinite(percentage) ? percentage : 0
  return Math.round(value)
})

// Methods
function handleClose() {
  visible.value = false
}

function getWorkloadColor(percentage: number): string {
  if (percentage <= 70) return 'workload-green'
  if (percentage <= 90) return 'workload-yellow'
  return 'workload-red'
}

function getWorkloadMessage(level: string): string {
  switch (level) {
    case 'green': return '工作量正常，时间安排合理'
    case 'yellow': return '工作量较高，建议优化任务安排'
    case 'red': return '工作量过载，存在时间冲突风险'
    default: return '工作量分析'
  }
}

function getWorkloadAlertType(level: string): 'success' | 'warning' | 'error' | 'info' {
  switch (level) {
    case 'green': return 'success'
    case 'yellow': return 'warning'
    case 'red': return 'error'
    default: return 'info'
  }
}
</script>

<style scoped>
.workload-analysis {
  padding: 20px 0;
}

.workload-summary {
  display: flex;
  justify-content: space-between;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: 8px;
  margin-bottom: 16px;
}

.summary-item {
  text-align: center;
}

.label {
  display: block;
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.value {
  display: block;
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.workload-green { color: #52c41a !important; }
.workload-yellow { color: #faad14 !important; }
.workload-red { color: #ff4d4f !important; }

.task-breakdown {
  margin-top: 24px;
}

.task-breakdown h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

.task-list {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 16px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.task-item:last-child {
  border-bottom: none;
}

.task-title {
  font-size: 14px;
  color: var(--text-primary);
}

.task-hours {
  font-size: 14px;
  color: var(--text-muted);
  font-weight: 500;
}

.empty-analysis {
  padding: 40px;
  text-align: center;
  color: var(--text-muted);
}
</style> 