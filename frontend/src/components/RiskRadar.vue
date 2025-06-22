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
/* Modern Risk Radar Component */
.risk-radar {
  position: relative;
  z-index: 1000;
}

/* Enhanced Risk Indicator Button */
.risk-indicator {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid #e0e0e0;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  user-select: none;
  min-width: 80px;
  justify-content: center;
}

.risk-indicator.high {
  border-color: #ff4d4f;
  background: rgba(255, 240, 240, 0.95);
  color: #cf1322;
}

.risk-indicator.medium {
  border-color: #fa8c16;
  background: rgba(255, 247, 230, 0.95);
  color: #d46b08;
}

.risk-indicator.low {
  border-color: #52c41a;
  background: rgba(246, 255, 237, 0.95);
  color: #389e0d;
}

.risk-indicator:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  border-width: 3px;
}

.risk-indicator:active {
  transform: translateY(-1px) scale(1.02);
}

.risk-icon {
  font-size: 18px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.risk-count {
  font-weight: 700;
  font-size: 16px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* Enhanced Risk Popover */
.risk-popover {
  position: absolute;
  top: 55px;
  right: 0;
  width: 420px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  max-height: 550px;
  overflow: hidden;
  backdrop-filter: blur(20px);
  animation: popoverSlideIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 1001;
}

@keyframes popoverSlideIn {
  0% {
    opacity: 0;
    transform: translateY(-10px) scale(0.95);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.popover-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 16px 16px 0 0;
}

.popover-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: white;
  padding: 6px;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

/* Enhanced Summary Section */
.risk-summary {
  padding: 24px;
  background: rgba(248, 250, 252, 0.8);
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px 12px;
  border-radius: 12px;
  transition: all 0.3s;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.stat-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  transition: all 0.3s;
}

.stat-item.high {
  background: linear-gradient(135deg, #fff1f0 0%, #ffece8 100%);
  color: #cf1322;
  border: 2px solid rgba(255, 77, 79, 0.2);
}

.stat-item.high::before {
  background: linear-gradient(90deg, #ff4d4f, #cf1322);
}

.stat-item.medium {
  background: linear-gradient(135deg, #fff7e6 0%, #ffefd3 100%);
  color: #d46b08;
  border: 2px solid rgba(250, 140, 22, 0.2);
}

.stat-item.medium::before {
  background: linear-gradient(90deg, #fa8c16, #d46b08);
}

.stat-item.low {
  background: linear-gradient(135deg, #f6ffed 0%, #eaffd1 100%);
  color: #389e0d;
  border: 2px solid rgba(82, 196, 26, 0.2);
}

.stat-item.low::before {
  background: linear-gradient(90deg, #52c41a, #389e0d);
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.stat-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 8px;
  opacity: 0.8;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* Enhanced Risky Tasks List */
.risky-tasks-list {
  padding: 24px;
  max-height: 250px;
  overflow-y: auto;
}

.risky-tasks-list::-webkit-scrollbar {
  width: 6px;
}

.risky-tasks-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.risky-tasks-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.risky-tasks-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.risky-tasks-list h5,
.suggestions h5 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a202c;
  display: flex;
  align-items: center;
  gap: 8px;
}

.risky-tasks-list h5::before {
  content: '⚠️';
  font-size: 18px;
}

.risky-task-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  margin-bottom: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}

.risky-task-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  transition: all 0.3s;
}

.risky-task-item.high {
  background: linear-gradient(135deg, rgba(255, 241, 240, 0.8) 0%, rgba(255, 236, 232, 0.8) 100%);
}

.risky-task-item.high::before {
  background: linear-gradient(180deg, #ff4d4f, #cf1322);
}

.risky-task-item.medium {
  background: linear-gradient(135deg, rgba(255, 247, 230, 0.8) 0%, rgba(255, 239, 211, 0.8) 100%);
}

.risky-task-item.medium::before {
  background: linear-gradient(180deg, #fa8c16, #d46b08);
}

.risky-task-item.low {
  background: linear-gradient(135deg, rgba(246, 255, 237, 0.8) 0%, rgba(234, 255, 209, 0.8) 100%);
}

.risky-task-item.low::before {
  background: linear-gradient(180deg, #52c41a, #389e0d);
}

.risky-task-item:hover {
  transform: translateX(6px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  border-color: rgba(102, 126, 234, 0.3);
}

.risky-task-item:hover::before {
  width: 6px;
}

.task-info {
  flex: 1;
}

.task-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  line-height: 1.4;
  color: #1a202c;
}

.risk-badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  align-items: center;
}

.risk-badge {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 12px;
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  font-weight: 500;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.risk-score {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 12px;
  background: linear-gradient(45deg, #667eea, #764ba2);
  color: white;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
}

.task-actions {
  margin-left: 12px;
  display: flex;
  align-items: center;
}

.more-tasks {
  text-align: center;
  color: #718096;
  font-size: 13px;
  padding: 12px;
  font-style: italic;
}

/* Enhanced Suggestions Section */
.suggestions {
  padding: 24px;
  background: linear-gradient(135deg, rgba(250, 250, 250, 0.8) 0%, rgba(245, 245, 245, 0.8) 100%);
  border-radius: 0 0 16px 16px;
}

.suggestions h5::before {
  content: '💡';
  font-size: 18px;
}

.suggestion-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.suggestion-list li {
  margin-bottom: 12px;
  font-size: 13px;
  line-height: 1.5;
  color: #4a5568;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  border-left: 3px solid #667eea;
  position: relative;
}

.suggestion-list li::before {
  content: '→';
  position: absolute;
  left: -8px;
  top: 50%;
  transform: translateY(-50%);
  background: #667eea;
  color: white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}

/* Enhanced Footer */
.popover-footer {
  padding: 20px 24px;
  display: flex;
  gap: 12px;
  justify-content: space-between;
  align-items: center;
  background: rgba(248, 250, 252, 0.8);
  border-radius: 0 0 16px 16px;
}

.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 25px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

/* Enhanced Recommendations Dialog */
.task-risk-details {
  margin-bottom: 24px;
  padding: 20px;
  background: rgba(248, 250, 252, 0.5);
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.risk-level {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.risk-level.high {
  background: linear-gradient(45deg, #ff4d4f, #cf1322);
  color: white;
  box-shadow: 0 2px 4px rgba(255, 77, 79, 0.3);
}

.risk-level.medium {
  background: linear-gradient(45deg, #fa8c16, #d46b08);
  color: white;
  box-shadow: 0 2px 4px rgba(250, 140, 22, 0.3);
}

.risk-level.low {
  background: linear-gradient(45deg, #52c41a, #389e0d);
  color: white;
  box-shadow: 0 2px 4px rgba(82, 196, 26, 0.3);
}

.risk-category-tag {
  display: inline-block;
  padding: 4px 8px;
  margin: 2px 4px 2px 0;
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.recommendations-list {
  margin-top: 20px;
}

.recommendations-list h5 {
  color: #1a202c;
  font-weight: 600;
  margin-bottom: 12px;
}

.recommendations-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.recommendations-list li {
  padding: 12px 16px;
  margin-bottom: 8px;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 8px;
  border-left: 3px solid #667eea;
  font-size: 14px;
  line-height: 1.5;
  color: #4a5568;
}

/* Element Plus Component Overrides */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.el-button:hover) {
  transform: translateY(-1px);
}

:deep(.el-button--small) {
  padding: 8px 12px;
  font-size: 12px;
}

:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}

:deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 24px;
}

:deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
}

:deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 18px;
}

/* Responsive Design */
@media (max-width: 768px) {
  .risk-popover {
    width: 320px;
    right: -20px;
  }
  
  .summary-stats {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .risky-task-item {
    flex-direction: column;
    gap: 12px;
  }
  
  .task-actions {
    margin-left: 0;
    align-self: flex-end;
  }
}
</style>