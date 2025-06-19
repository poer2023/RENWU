<template>
  <div class="risk-radar">
    <!-- Risk indicator button -->
    <div 
      class="risk-indicator" 
      :class="getRiskLevelClass()"
      @click="togglePopover"
      v-if="riskData"
    >
      <span class="risk-icon">⚠️</span>
      <span class="risk-count">{{ getTotalRiskyTasks() }}</span>
    </div>

    <!-- Risk popover -->
    <div 
      v-if="showPopover && riskData" 
      class="risk-popover"
      v-click-outside="closePopover"
    >
      <div class="popover-header">
        <h4>🎯 风险雷达</h4>
        <button class="close-btn" @click="closePopover">×</button>
      </div>

      <div class="risk-summary">
        <div class="summary-stats">
          <div class="stat-item high">
            <span class="stat-label">高风险</span>
            <span class="stat-value">{{ riskData.risk_summary.high_risk }}</span>
          </div>
          <div class="stat-item medium">
            <span class="stat-label">中风险</span>
            <span class="stat-value">{{ riskData.risk_summary.medium_risk }}</span>
          </div>
          <div class="stat-item low">
            <span class="stat-label">低风险</span>
            <span class="stat-value">{{ riskData.risk_summary.low_risk }}</span>
          </div>
        </div>
      </div>

      <div class="risky-tasks-list" v-if="riskData.risky_tasks.length > 0">
        <h5>风险任务</h5>
        <div class="task-list">
          <div 
            v-for="riskyTask in riskData.risky_tasks.slice(0, 5)" 
            :key="riskyTask.task.id"
            class="risky-task-item"
            :class="riskyTask.risk_level"
            @click="viewTask(riskyTask.task)"
          >
            <div class="task-info">
              <div class="task-title">{{ riskyTask.task.title }}</div>
              <div class="risk-badges">
                <span 
                  v-for="category in riskyTask.risk_categories" 
                  :key="category"
                  class="risk-badge"
                  :class="category"
                >
                  {{ getRiskCategoryLabel(category) }}
                </span>
                <span class="risk-score">{{ riskyTask.risk_score }}</span>
              </div>
            </div>
            <div class="task-actions">
              <el-button 
                size="small" 
                @click.stop="showRecommendations(riskyTask)"
                :icon="QuestionFilled"
              />
            </div>
          </div>
        </div>
        <div v-if="riskData.risky_tasks.length > 5" class="more-tasks">
          还有 {{ riskData.risky_tasks.length - 5 }} 个风险任务...
        </div>
      </div>

      <div class="suggestions" v-if="riskData.suggestions.length > 0">
        <h5>建议</h5>
        <ul class="suggestion-list">
          <li v-for="(suggestion, index) in riskData.suggestions.slice(0, 3)" :key="index">
            {{ suggestion }}
          </li>
        </ul>
      </div>

      <div class="popover-footer">
        <el-button size="small" @click="refreshAnalysis" :loading="loading">
          🔄 刷新
        </el-button>
        <el-button size="small" type="primary" @click="openDetailedView">
          查看详情
        </el-button>
      </div>
    </div>

    <!-- Loading indicator -->
    <div v-if="loading && !riskData" class="loading-indicator">
      <el-icon class="is-loading"><Loading /></el-icon>
    </div>

    <!-- Recommendations Dialog -->
    <el-dialog v-model="showRecommendationsDialog" title="风险建议" width="500px">
      <div v-if="selectedRiskyTask">
        <h4>{{ selectedRiskyTask.task.title }}</h4>
        <div class="task-risk-details">
          <p><strong>风险等级:</strong> 
            <span :class="`risk-level ${selectedRiskyTask.risk_level}`">
              {{ getRiskLevelLabel(selectedRiskyTask.risk_level) }}
            </span>
          </p>
          <p><strong>风险评分:</strong> {{ selectedRiskyTask.risk_score }}</p>
          <p><strong>风险类别:</strong> 
            <span 
              v-for="category in selectedRiskyTask.risk_categories" 
              :key="category"
              class="risk-category-tag"
            >
              {{ getRiskCategoryLabel(category) }}
            </span>
          </p>
        </div>
        
        <div class="recommendations-list">
          <h5>建议操作:</h5>
          <ul>
            <li v-for="recommendation in selectedRiskyTask.recommendations" :key="recommendation">
              {{ recommendation }}
            </li>
          </ul>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showRecommendationsDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElButton, ElDialog, ElIcon } from 'element-plus'
import { QuestionFilled, Loading } from '@element-plus/icons-vue'
import axios from 'axios'

interface RiskData {
  risk_summary: {
    total_tasks: number
    high_risk: number
    medium_risk: number
    low_risk: number
    risk_categories: Record<string, number>
  }
  risky_tasks: Array<{
    task: any
    risk_level: string
    risk_score: number
    risk_categories: string[]
    recommendations: string[]
  }>
  suggestions: string[]
  success: boolean
  error?: string
}

const emit = defineEmits<{
  'view-task': [task: any]
}>()

const riskData = ref<RiskData | null>(null)
const showPopover = ref(false)
const loading = ref(false)
const showRecommendationsDialog = ref(false)
const selectedRiskyTask = ref<any>(null)

const fetchRiskAnalysis = async () => {
  loading.value = true
  try {
    const response = await axios.post<RiskData>('/api/ai/risk-analysis', {})
    riskData.value = response.data
  } catch (error) {
    console.error('Risk analysis failed:', error)
  } finally {
    loading.value = false
  }
}

const togglePopover = () => {
  showPopover.value = !showPopover.value
}

const closePopover = () => {
  showPopover.value = false
}

const getTotalRiskyTasks = (): number => {
  if (!riskData.value) return 0
  return riskData.value.risk_summary.high_risk + riskData.value.risk_summary.medium_risk
}

const getRiskLevelClass = (): string => {
  if (!riskData.value) return 'low'
  
  const highRisk = riskData.value.risk_summary.high_risk
  const mediumRisk = riskData.value.risk_summary.medium_risk
  
  if (highRisk > 0) return 'high'
  if (mediumRisk > 2) return 'medium'
  return 'low'
}

const getRiskLevelLabel = (level: string): string => {
  const labels: Record<string, string> = {
    high: '高风险',
    medium: '中风险',
    low: '低风险'
  }
  return labels[level] || level
}

const getRiskCategoryLabel = (category: string): string => {
  const labels: Record<string, string> = {
    delay: '延期',
    blocked: '阻塞',
    external_dependency: '外部依赖',
    complexity: '复杂',
    emotional_stress: '压力',
    stale: '过期'
  }
  return labels[category] || category
}

const viewTask = (task: any) => {
  emit('view-task', task)
  closePopover()
}

const showRecommendations = (riskyTask: any) => {
  selectedRiskyTask.value = riskyTask
  showRecommendationsDialog.value = true
}

const refreshAnalysis = () => {
  fetchRiskAnalysis()
}

const openDetailedView = () => {
  // TODO: Implement detailed risk view
  closePopover()
}

// Click outside directive
const vClickOutside = {
  mounted(el: any, binding: any) {
    el.clickOutsideEvent = (event: Event) => {
      if (!(el === event.target || el.contains(event.target))) {
        binding.value()
      }
    }
    document.addEventListener('click', el.clickOutsideEvent)
  },
  unmounted(el: any) {
    document.removeEventListener('click', el.clickOutsideEvent)
  }
}

onMounted(() => {
  fetchRiskAnalysis()
})
</script>

<style scoped>
.risk-radar {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
}

.risk-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: white;
  border: 2px solid;
}

.risk-indicator.high {
  border-color: #ff4d4f;
  background: #fff1f0;
}

.risk-indicator.medium {
  border-color: #fa8c16;
  background: #fff7e6;
}

.risk-indicator.low {
  border-color: #52c41a;
  background: #f6ffed;
}

.risk-indicator:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.risk-icon {
  font-size: 16px;
}

.risk-count {
  font-weight: bold;
  font-size: 14px;
}

.risk-popover {
  position: absolute;
  top: 50px;
  right: 0;
  width: 360px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border: 1px solid #eee;
  max-height: 500px;
  overflow-y: auto;
}

.popover-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.popover-header h4 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 24px;
  height: 24px;
  border-radius: 4px;
}

.close-btn:hover {
  background: #f0f0f0;
}

.risk-summary {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.summary-stats {
  display: flex;
  gap: 12px;
}

.stat-item {
  flex: 1;
  text-align: center;
  padding: 8px;
  border-radius: 6px;
}

.stat-item.high {
  background: #fff1f0;
  color: #ff4d4f;
}

.stat-item.medium {
  background: #fff7e6;
  color: #fa8c16;
}

.stat-item.low {
  background: #f6ffed;
  color: #52c41a;
}

.stat-label {
  display: block;
  font-size: 12px;
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-size: 18px;
  font-weight: bold;
}

.risky-tasks-list {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.risky-tasks-list h5,
.suggestions h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #333;
}

.risky-task-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-left: 3px solid;
}

.risky-task-item.high {
  background: #fff1f0;
  border-left-color: #ff4d4f;
}

.risky-task-item.medium {
  background: #fff7e6;
  border-left-color: #fa8c16;
}

.risky-task-item.low {
  background: #f6ffed;
  border-left-color: #52c41a;
}

.risky-task-item:hover {
  opacity: 0.8;
}

.task-info {
  flex: 1;
}

.task-title {
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 6px;
  line-height: 1.3;
}

.risk-badges {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  align-items: center;
}

.risk-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
  background: #f0f0f0;
  color: #666;
}

.risk-score {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
  background: #1890ff;
  color: white;
  font-weight: bold;
}

.task-actions {
  margin-left: 8px;
}

.more-tasks {
  text-align: center;
  color: #999;
  font-size: 12px;
  padding: 8px;
}

.suggestions {
  padding: 16px;
  background: #fafafa;
}

.suggestion-list {
  margin: 0;
  padding-left: 16px;
}

.suggestion-list li {
  margin-bottom: 6px;
  font-size: 12px;
  line-height: 1.4;
  color: #666;
}

.popover-footer {
  padding: 16px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  border-top: 1px solid #f0f0f0;
}

.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Recommendations Dialog */
.task-risk-details {
  margin-bottom: 20px;
}

.risk-level {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.risk-level.high {
  background: #ff4d4f;
  color: white;
}

.risk-level.medium {
  background: #fa8c16;
  color: white;
}

.risk-level.low {
  background: #52c41a;
  color: white;
}

.risk-category-tag {
  display: inline-block;
  margin-right: 6px;
  padding: 2px 6px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 12px;
}

.recommendations-list ul {
  margin: 0;
  padding-left: 20px;
}

.recommendations-list li {
  margin-bottom: 8px;
  line-height: 1.4;
}
</style>