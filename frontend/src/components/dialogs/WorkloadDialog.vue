<template>
  <el-dialog
    v-model="visible"
    title="工作量分析"
    width="90%"
    @close="handleClose"
  >
    <div class="workload-content">
      <div class="workload-header">
        <el-select v-model="selectedUserId" placeholder="选择用户" @change="handleUserChange">
          <el-option
            v-for="user in users"
            :key="user.id"
            :label="user.name"
            :value="user.id"
          />
        </el-select>
        
        <el-select v-model="selectedPeriod" placeholder="选择时间段" @change="fetchWorkloadData">
          <el-option label="本周" value="week" />
          <el-option label="本月" value="month" />
          <el-option label="本季度" value="quarter" />
          <el-option label="自定义" value="custom" />
        </el-select>
        
        <el-date-picker
          v-if="selectedPeriod === 'custom'"
          v-model="customDateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @change="fetchWorkloadData"
        />
      </div>
      
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading">
          <Loading />
        </el-icon>
        <p>正在分析工作量...</p>
      </div>
      
      <div v-else-if="workloadData" class="workload-body">
        <div class="workload-summary">
          <el-card>
            <h3>工作量概览</h3>
            <div class="summary-stats">
              <div class="stat-item">
                <span class="stat-label">总任务数</span>
                <span class="stat-value">{{ workloadData.summary.total_tasks }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">已完成</span>
                <span class="stat-value">{{ workloadData.summary.completed_tasks }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">进行中</span>
                <span class="stat-value">{{ workloadData.summary.in_progress_tasks }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">未开始</span>
                <span class="stat-value">{{ workloadData.summary.pending_tasks }}</span>
              </div>
            </div>
          </el-card>
        </div>
        
        <div class="workload-charts">
          <el-card>
            <h3>任务分布</h3>
            <div class="chart-container">
              <canvas ref="taskDistributionChart"></canvas>
            </div>
          </el-card>
          
          <el-card>
            <h3>工作趋势</h3>
            <div class="chart-container">
              <canvas ref="workTrendChart"></canvas>
            </div>
          </el-card>
        </div>
        
        <div class="workload-details">
          <el-card>
            <h3>任务详情</h3>
            <el-table :data="workloadData.tasks" style="width: 100%">
              <el-table-column prop="title" label="任务名称" />
              <el-table-column prop="status" label="状态">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)">
                    {{ getStatusLabel(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="priority" label="优先级">
                <template #default="{ row }">
                  <el-tag :type="getPriorityType(row.priority)">
                    {{ getPriorityLabel(row.priority) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="创建时间" />
              <el-table-column prop="updated_at" label="更新时间" />
            </el-table>
          </el-card>
        </div>
        
        <div v-if="workloadData.insights" class="workload-insights">
          <el-card>
            <h3>AI 洞察</h3>
            <div class="insights-content">
              <div v-for="(insight, index) in workloadData.insights" :key="index" class="insight-item">
                <el-icon>
                  <InfoFilled />
                </el-icon>
                <span>{{ insight }}</span>
              </div>
            </div>
          </el-card>
        </div>
      </div>
      
      <div v-else class="no-data">
        <el-empty description="暂无工作量数据" />
      </div>
    </div>
    
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
      <el-button type="primary" @click="handleExport">导出报告</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { ElDialog, ElSelect, ElOption, ElDatePicker, ElCard, ElTable, ElTableColumn, ElTag, ElButton, ElIcon, ElEmpty, ElMessage } from 'element-plus'
import { Loading, InfoFilled } from '@element-plus/icons-vue'
import Chart from 'chart.js/auto'

interface Props {
  modelValue: boolean
  userId?: string
}

interface WorkloadData {
  summary: {
    total_tasks: number
    completed_tasks: number
    in_progress_tasks: number
    pending_tasks: number
  }
  tasks: Array<{
    id: string
    title: string
    status: string
    priority: number
    created_at: string
    updated_at: string
  }>
  insights?: string[]
  distribution?: { [key: string]: number }
  trend?: Array<{ date: string; count: number }>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const visible = ref(props.modelValue)
const loading = ref(false)
const selectedUserId = ref(props.userId || '')
const selectedPeriod = ref('week')
const customDateRange = ref<[Date, Date] | null>(null)
const workloadData = ref<WorkloadData | null>(null)
const users = ref([
  { id: 'user1', name: '用户1' },
  { id: 'user2', name: '用户2' },
  { id: 'user3', name: '用户3' }
])

// Chart refs
const taskDistributionChart = ref<HTMLCanvasElement>()
const workTrendChart = ref<HTMLCanvasElement>()
let distributionChartInstance: Chart | null = null
let trendChartInstance: Chart | null = null

// Watch for external visibility changes
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal) {
    fetchWorkloadData()
  }
})

// Watch for internal visibility changes
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

onMounted(() => {
  if (visible.value) {
    fetchWorkloadData()
  }
})

async function fetchWorkloadData() {
  if (!selectedUserId.value) return
  
  loading.value = true
  try {
    const params = new URLSearchParams({
      user_id: selectedUserId.value,
      period: selectedPeriod.value
    })
    
    if (selectedPeriod.value === 'custom' && customDateRange.value) {
      params.append('start_date', customDateRange.value[0].toISOString())
      params.append('end_date', customDateRange.value[1].toISOString())
    }
    
    const response = await fetch(`/api/ai/v3/workload?${params}`)
    if (!response.ok) throw new Error('Failed to fetch workload data')
    
    workloadData.value = await response.json()
    
    // Update charts after data is loaded
    await nextTick()
    updateCharts()
  } catch (error) {
    console.error('Error fetching workload data:', error)
    ElMessage.error('获取工作量数据失败')
  } finally {
    loading.value = false
  }
}

function updateCharts() {
  if (!workloadData.value) return
  
  // Update task distribution chart
  if (taskDistributionChart.value) {
    if (distributionChartInstance) {
      distributionChartInstance.destroy()
    }
    
    const ctx = taskDistributionChart.value.getContext('2d')
    if (ctx) {
      distributionChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['已完成', '进行中', '未开始'],
          datasets: [{
            data: [
              workloadData.value.summary.completed_tasks,
              workloadData.value.summary.in_progress_tasks,
              workloadData.value.summary.pending_tasks
            ],
            backgroundColor: ['#67C23A', '#E6A23C', '#909399']
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false
        }
      })
    }
  }
  
  // Update work trend chart
  if (workTrendChart.value && workloadData.value.trend) {
    if (trendChartInstance) {
      trendChartInstance.destroy()
    }
    
    const ctx = workTrendChart.value.getContext('2d')
    if (ctx) {
      trendChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: workloadData.value.trend.map(item => item.date),
          datasets: [{
            label: '任务数量',
            data: workloadData.value.trend.map(item => item.count),
            borderColor: '#409EFF',
            tension: 0.1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false
        }
      })
    }
  }
}

function handleUserChange() {
  fetchWorkloadData()
}

function handleClose() {
  visible.value = false
}

async function handleExport() {
  try {
    const params = new URLSearchParams({
      user_id: selectedUserId.value,
      period: selectedPeriod.value,
      format: 'pdf'
    })
    
    const response = await fetch(`/api/ai/v3/workload/export?${params}`)
    if (!response.ok) throw new Error('Failed to export report')
    
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `workload-report-${new Date().toISOString().split('T')[0]}.pdf`
    a.click()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('报告导出成功')
  } catch (error) {
    console.error('Error exporting report:', error)
    ElMessage.error('报告导出失败')
  }
}

function getStatusType(status: string) {
  const types: { [key: string]: string } = {
    'completed': 'success',
    'in_progress': 'warning',
    'pending': 'info',
    'cancelled': 'danger'
  }
  return types[status] || 'info'
}

function getStatusLabel(status: string) {
  const labels: { [key: string]: string } = {
    'completed': '已完成',
    'in_progress': '进行中',
    'pending': '未开始',
    'cancelled': '已取消'
  }
  return labels[status] || status
}

function getPriorityType(priority: number) {
  if (priority >= 4) return 'danger'
  if (priority >= 3) return 'warning'
  return 'info'
}

function getPriorityLabel(priority: number) {
  const labels: { [key: string]: string } = {
    '5': '紧急',
    '4': '高',
    '3': '中',
    '2': '低',
    '1': '很低'
  }
  return labels[priority.toString()] || '未设置'
}
</script>

<style scoped>
.workload-content {
  min-height: 500px;
}

.workload-header {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.loading-container .el-icon {
  font-size: 48px;
  color: #409EFF;
  margin-bottom: 16px;
}

.workload-body {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.workload-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.chart-container {
  height: 300px;
  padding: 16px;
}

.workload-insights {
  margin-top: 24px;
}

.insights-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.insight-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background-color: #f0f9ff;
  border-radius: 4px;
}

.insight-item .el-icon {
  color: #409EFF;
  margin-top: 2px;
}

.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}
</style> 