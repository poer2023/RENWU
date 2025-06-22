<template>
  <div class="ai-assistant-v3" v-if="visible" :style="{ left: position.x + 'px', top: position.y + 'px' }">
    <!-- Header -->
    <div class="assistant-header">
      <div class="header-left">
        <span class="ai-icon">🤖</span>
        <span class="assistant-title">TaskWall AI v3.0</span>
      </div>
      <button class="close-btn" @click="$emit('close')">×</button>
    </div>
    
    <!-- Mode Tabs -->
    <div class="mode-tabs">
      <button
        v-for="mode in modes"
        :key="mode.id"
        class="mode-tab"
        :class="{ active: activeMode === mode.id }"
        @click="activeMode = mode.id"
      >
        <span class="mode-icon">{{ mode.icon }}</span>
        <span class="mode-label">{{ mode.label }}</span>
      </button>
    </div>
    
    <!-- Content Area -->
    <div class="assistant-content">
      <!-- Natural Language Input Mode -->
      <div v-if="activeMode === 'parse'" class="mode-content">
        <div class="input-section">
          <textarea
            v-model="naturalLanguageInput"
            placeholder="用自然语言描述你的任务，比如：'明天下午3点开会讨论项目进度，高优先级'"
            class="nl-input"
            rows="3"
            @keydown.ctrl.enter="parseNaturalLanguage"
          ></textarea>
          <div class="input-controls">
            <label class="checkbox-label">
              <input type="checkbox" v-model="fullAnalysis" />
              完整分析
            </label>
            <button 
              class="parse-btn"
              @click="parseNaturalLanguage"
              :disabled="!naturalLanguageInput.trim() || loading"
            >
              <span v-if="loading" class="loading-spinner"></span>
              {{ loading ? '解析中...' : '解析任务' }}
            </button>
          </div>
        </div>
        
        <!-- Parse Results -->
        <div v-if="parseResult" class="parse-results">
          <div class="result-header">
            <span class="result-title">解析结果</span>
            <span class="confidence-badge" :class="getConfidenceClass(parseResult.confidence)">
              {{ Math.round(parseResult.confidence * 100) }}%
            </span>
          </div>
          
          <div class="suggested-task">
            <div class="field-group">
              <label>标题</label>
              <div class="field-value">{{ parseResult.suggested_task.title }}</div>
            </div>
            
            <div class="field-group" v-if="parseResult.suggested_task.description">
              <label>描述</label>
              <div class="field-value">{{ parseResult.suggested_task.description }}</div>
            </div>
            
            <div class="field-row">
              <div class="field-group">
                <label>优先级</label>
                <div class="field-value">{{ getPriorityText(parseResult.suggested_task.priority) }}</div>
              </div>
              
              <div class="field-group" v-if="parseResult.suggested_task.category">
                <label>分类</label>
                <div class="field-value">{{ parseResult.suggested_task.category }}</div>
              </div>
            </div>
            
            <div class="field-row" v-if="parseResult.suggested_task.estimated_hours || parseResult.suggested_task.deadline">
              <div class="field-group" v-if="parseResult.suggested_task.estimated_hours">
                <label>预估工时</label>
                <div class="field-value">{{ parseResult.suggested_task.estimated_hours }} 小时</div>
              </div>
              
              <div class="field-group" v-if="parseResult.suggested_task.deadline">
                <label>截止时间</label>
                <div class="field-value">{{ formatDate(parseResult.suggested_task.deadline) }}</div>
              </div>
            </div>
            
            <div class="field-group" v-if="parseResult.suggested_task.tags && parseResult.suggested_task.tags.length">
              <label>标签</label>
              <div class="tags-container">
                <span 
                  v-for="tag in parseResult.suggested_task.tags" 
                  :key="tag" 
                  class="tag"
                >{{ tag }}</span>
              </div>
            </div>
          </div>
          
          <!-- Similar Tasks -->
          <div v-if="parseResult.similar_tasks && parseResult.similar_tasks.length" class="similar-tasks">
            <div class="section-title">相似任务</div>
            <div class="similar-task-list">
              <div 
                v-for="task in parseResult.similar_tasks.slice(0, 3)" 
                :key="task.task_id"
                class="similar-task-item"
              >
                <div class="task-title">{{ task.task_title }}</div>
                <div class="similarity-score">相似度: {{ Math.round(task.similarity_score * 100) }}%</div>
              </div>
            </div>
          </div>
          
          <!-- Actions -->
          <div class="result-actions">
            <button class="create-task-btn" @click="createTaskFromResult">
              创建任务
            </button>
            <button class="analyze-more-btn" @click="analyzeTask" v-if="parseResult">
              深度分析
            </button>
          </div>
        </div>
      </div>
      
      <!-- Task Analysis Mode -->
      <div v-if="activeMode === 'analyze'" class="mode-content">
        <div class="analysis-section">
          <div class="section-title">任务分析</div>
          <p class="section-desc">对现有任务进行全面的AI分析，包括分类、优先级、相似度等</p>
          
          <button 
            class="analyze-current-btn"
            @click="analyzeCurrentTask"
            :disabled="!props.taskData || loading"
          >
            <span v-if="loading" class="loading-spinner"></span>
            {{ loading ? '分析中...' : '分析当前任务' }}
          </button>
        </div>
        
        <!-- Analysis Results -->
        <div v-if="analysisResult" class="analysis-results">
          <div class="result-header">
            <span class="result-title">分析结果</span>
            <span class="confidence-badge" :class="getConfidenceClass(analysisResult.overall_confidence)">
              {{ Math.round(analysisResult.overall_confidence * 100) }}%
            </span>
          </div>
          
          <!-- Classification -->
          <div v-if="analysisResult.classification_result" class="analysis-item">
            <div class="analysis-label">🏷️ 分类结果</div>
            <div class="analysis-content">
              <div>
                <strong>主分类:</strong> {{ analysisResult.classification_result.data.category }}
              </div>
              <div v-if="analysisResult.classification_result.data.subcategory">
                <strong>子分类:</strong> {{ analysisResult.classification_result.data.subcategory }}
              </div>
              <div>
                <strong>置信度:</strong> {{ Math.round(analysisResult.classification_result.confidence * 100) }}%
              </div>
            </div>
          </div>
          
          <!-- Priority -->
          <div v-if="analysisResult.priority_result" class="analysis-item">
            <div class="analysis-label">🎯 优先级评估</div>
            <div class="analysis-content">
              <div>
                <strong>建议优先级:</strong> {{ getPriorityText(analysisResult.priority_result.data.priority_level) }}
              </div>
              <div>
                <strong>紧急度:</strong> {{ Math.round(analysisResult.priority_result.data.urgency_score * 100) }}%
              </div>
              <div>
                <strong>重要度:</strong> {{ Math.round(analysisResult.priority_result.data.importance_score * 100) }}%
              </div>
            </div>
          </div>
          
          <!-- Similar Tasks -->
          <div v-if="analysisResult.similarity_result" class="analysis-item">
            <div class="analysis-label">🔍 相似任务</div>
            <div class="analysis-content">
              <div v-if="analysisResult.similarity_result.data.length === 0">
                没有发现相似任务
              </div>
              <div v-else>
                找到 {{ analysisResult.similarity_result.data.length }} 个相似任务
              </div>
            </div>
          </div>
          
          <!-- Recommendations -->
          <div v-if="analysisResult.recommendations && analysisResult.recommendations.length" class="recommendations">
            <div class="section-title">💡 AI建议</div>
            <ul class="recommendation-list">
              <li v-for="rec in analysisResult.recommendations" :key="rec" class="recommendation-item">
                {{ rec }}
              </li>
            </ul>
          </div>
        </div>
      </div>
      
      <!-- Batch Processing Mode -->
      <div v-if="activeMode === 'batch'" class="mode-content">
        <div class="batch-section">
          <div class="section-title">批量处理</div>
          <p class="section-desc">一次性解析多个任务，每行一个任务</p>
          
          <textarea
            v-model="batchInput"
            placeholder="每行输入一个任务，例如：&#10;修复登录页面bug&#10;设计新的用户界面&#10;测试支付功能"
            class="batch-input"
            rows="6"
          ></textarea>
          
          <button 
            class="batch-process-btn"
            @click="processBatch"
            :disabled="!batchInput.trim() || loading"
          >
            <span v-if="loading" class="loading-spinner"></span>
            {{ loading ? '处理中...' : '批量处理' }}
          </button>
        </div>
        
        <!-- Batch Results -->
        <div v-if="batchResults && batchResults.length" class="batch-results">
          <div class="result-header">
            <span class="result-title">批量处理结果</span>
            <span class="count-badge">{{ batchResults.length }} 个任务</span>
          </div>
          
          <div class="batch-result-list">
            <div 
              v-for="(result, index) in batchResults" 
              :key="index"
              class="batch-result-item"
            >
              <div class="result-index">{{ index + 1 }}</div>
              <div class="result-content">
                <div class="task-title">{{ result.suggested_task.title }}</div>
                <div class="task-meta">
                  <span>{{ getPriorityText(result.suggested_task.priority) }}</span>
                  <span v-if="result.suggested_task.category">{{ result.suggested_task.category }}</span>
                  <span class="confidence">{{ Math.round(result.confidence * 100) }}%</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="batch-actions">
            <button class="create-all-btn" @click="createAllTasks">
              创建所有任务
            </button>
          </div>
        </div>
      </div>
      
      <!-- Insights Mode -->
      <div v-if="activeMode === 'insights'" class="mode-content">
        <div class="insights-section">
          <div class="section-title">AI洞察</div>
          <p class="section-desc">获取基于AI分析的工作负载和任务模式洞察</p>
          
          <div class="insights-controls">
            <select v-model="insightsTimeFrame" class="time-frame-select">
              <option value="today">今天</option>
              <option value="this_week">本周</option>
              <option value="this_month">本月</option>
            </select>
            
            <button 
              class="get-insights-btn"
              @click="getInsights"
              :disabled="loading"
            >
              <span v-if="loading" class="loading-spinner"></span>
              {{ loading ? '分析中...' : '获取洞察' }}
            </button>
          </div>
        </div>
        
        <!-- Insights Results -->
        <div v-if="insightsResult" class="insights-results">
          <div class="result-header">
            <span class="result-title">AI洞察报告</span>
            <span class="time-badge">{{ getTimeFrameText(insightsTimeFrame) }}</span>
          </div>
          
          <!-- Workload -->
          <div v-if="insightsResult.insights.workload" class="insight-item">
            <div class="insight-label">📊 工作负载</div>
            <div class="insight-content">
              <div class="workload-metrics">
                <div class="metric">
                  <span class="metric-label">任务数量:</span>
                  <span class="metric-value">{{ insightsResult.insights.workload.task_count }}</span>
                </div>
                <div class="metric">
                  <span class="metric-label">利用率:</span>
                  <span class="metric-value">{{ Math.round(insightsResult.insights.workload.utilization_rate * 100) }}%</span>
                </div>
                <div class="metric">
                  <span class="metric-label">负载级别:</span>
                  <span class="metric-value workload-level" :class="insightsResult.insights.workload.workload_level">
                    {{ getWorkloadLevelText(insightsResult.insights.workload.workload_level) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Recommendations -->
          <div v-if="insightsResult.recommendations && insightsResult.recommendations.length" class="insight-item">
            <div class="insight-label">💡 智能建议</div>
            <div class="insight-content">
              <ul class="recommendation-list">
                <li v-for="rec in insightsResult.recommendations" :key="rec" class="recommendation-item">
                  {{ rec }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAIAssistantV3 } from '@/composables/useAIAssistantV3'

interface Position {
  x: number
  y: number
}

interface Props {
  visible: boolean
  position: Position
  content?: string
  taskData?: any
  context?: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  taskCreated: [task: any]
  taskUpdated: [task: any]
}>()

const {
  loading,
  parseNaturalLanguage: parseNL,
  analyzeTask: analyzeTaskAPI,
  processBatch: processBatchAPI,
  getInsights: getInsightsAPI
} = useAIAssistantV3()

// State
const activeMode = ref('parse')
const naturalLanguageInput = ref('')
const fullAnalysis = ref(true)
const parseResult = ref<any>(null)
const analysisResult = ref<any>(null)
const batchInput = ref('')
const batchResults = ref<any[]>([])
const insightsTimeFrame = ref('this_week')
const insightsResult = ref<any>(null)

// Modes configuration
const modes = [
  { id: 'parse', label: '智能解析', icon: '🧠' },
  { id: 'analyze', label: '任务分析', icon: '🔍' },
  { id: 'batch', label: '批量处理', icon: '📝' },
  { id: 'insights', label: 'AI洞察', icon: '📊' }
]

// Methods
const parseNaturalLanguage = async () => {
  if (!naturalLanguageInput.value.trim()) return
  
  try {
    const result = await parseNL(naturalLanguageInput.value, props.context || {}, fullAnalysis.value)
    parseResult.value = result
  } catch (error) {
    console.error('Parse failed:', error)
  }
}

const analyzeCurrentTask = async () => {
  if (!props.taskData) return
  
  try {
    const result = await analyzeTaskAPI(props.taskData, props.context || {})
    analysisResult.value = result
  } catch (error) {
    console.error('Analysis failed:', error)
  }
}

const analyzeTask = async () => {
  if (!parseResult.value) return
  
  try {
    const result = await analyzeTaskAPI(parseResult.value.suggested_task, props.context || {})
    analysisResult.value = result
    activeMode.value = 'analyze'
  } catch (error) {
    console.error('Analysis failed:', error)
  }
}

const processBatch = async () => {
  if (!batchInput.value.trim()) return
  
  const lines = batchInput.value.split('\n').filter(line => line.trim())
  
  try {
    const results = await processBatchAPI(lines, props.context || {})
    batchResults.value = results.results
  } catch (error) {
    console.error('Batch processing failed:', error)
  }
}

const getInsights = async () => {
  try {
    const result = await getInsightsAPI('default', insightsTimeFrame.value)
    insightsResult.value = result
  } catch (error) {
    console.error('Insights failed:', error)
  }
}

const createTaskFromResult = () => {
  if (parseResult.value) {
    emit('taskCreated', parseResult.value.suggested_task)
    emit('close')
  }
}

const createAllTasks = () => {
  if (batchResults.value && batchResults.value.length) {
    batchResults.value.forEach(result => {
      emit('taskCreated', result.suggested_task)
    })
    emit('close')
  }
}

// Utility functions
const getConfidenceClass = (confidence: number) => {
  if (confidence >= 0.8) return 'high'
  if (confidence >= 0.6) return 'medium'
  return 'low'
}

const getPriorityText = (priority: number) => {
  const priorityTexts = ['紧急', '高', '中', '低', '待办']
  return priorityTexts[priority] || '中'
}

const getWorkloadLevelText = (level: string) => {
  const levelTexts = {
    'underutilized': '未充分利用',
    'optimal': '最优',
    'high': '高负载',
    'overloaded': '过载',
    'critical': '临界'
  }
  return levelTexts[level] || level
}

const getTimeFrameText = (timeFrame: string) => {
  const texts = {
    'today': '今天',
    'this_week': '本周',
    'this_month': '本月'
  }
  return texts[timeFrame] || timeFrame
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
/* Modern AI Assistant V3 - Enhanced Design */
.ai-assistant-v3 {
  position: fixed;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 20px;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.15),
    0 8px 32px rgba(102, 126, 234, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 0.8);
  width: 500px;
  max-height: 640px;
  z-index: 10000;
  font-size: 14px;
  overflow: hidden;
  animation: assistantSlideIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes assistantSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Enhanced Assistant Header */
.assistant-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.95) 0%, rgba(118, 75, 162, 0.95) 100%);
  color: white;
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
}

.assistant-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  backdrop-filter: blur(10px);
  z-index: -1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-icon {
  font-size: 20px;
}

.assistant-title {
  font-weight: 600;
  font-size: 16px;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 18px;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.mode-tabs {
  display: flex;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.mode-tab {
  flex: 1;
  padding: 12px 8px;
  border: none;
  background: none;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
  font-size: 12px;
}

.mode-tab:hover {
  background: #e9ecef;
}

.mode-tab.active {
  background: white;
  border-bottom: 2px solid #667eea;
  color: #667eea;
}

.mode-icon {
  font-size: 16px;
}

.mode-label {
  font-size: 11px;
  font-weight: 500;
}

.assistant-content {
  max-height: 480px;
  overflow-y: auto;
}

.mode-content {
  padding: 20px;
}

/* Natural Language Input Mode */
.input-section {
  margin-bottom: 20px;
}

/* Enhanced Natural Language Input */
.nl-input {
  width: 100%;
  padding: 16px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  resize: vertical;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.nl-input:focus {
  outline: none;
  border-color: rgba(102, 126, 234, 0.6);
  box-shadow: 
    0 4px 16px rgba(102, 126, 234, 0.15),
    0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
}

/* Enhanced Parse Button */
.parse-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 
    0 4px 12px rgba(102, 126, 234, 0.3),
    0 2px 6px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.parse-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.6s ease;
}

.parse-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #5a6fd8 0%, #6b4d95 100%);
  transform: translateY(-2px);
  box-shadow: 
    0 6px 20px rgba(102, 126, 234, 0.4),
    0 3px 8px rgba(0, 0, 0, 0.15);
}

.parse-btn:hover:not(:disabled)::before {
  left: 100%;
}

.parse-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

/* Results */
.parse-results, .analysis-results, .batch-results, .insights-results {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.result-title {
  font-weight: 600;
}

.confidence-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.confidence-badge.high {
  background: #d4edda;
  color: #155724;
}

.confidence-badge.medium {
  background: #fff3cd;
  color: #856404;
}

.confidence-badge.low {
  background: #f8d7da;
  color: #721c24;
}

.suggested-task {
  padding: 16px;
}

.field-group {
  margin-bottom: 12px;
}

.field-row {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
}

.field-row .field-group {
  flex: 1;
  margin-bottom: 0;
}

.field-group label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
  font-weight: 500;
}

.field-value {
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 13px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  padding: 4px 8px;
  background: #e3f2fd;
  color: #1565c0;
  border-radius: 12px;
  font-size: 12px;
}

/* Similar Tasks */
.similar-tasks {
  padding: 16px;
  border-top: 1px solid #e9ecef;
}

.section-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: #333;
}

.similar-task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 8px;
}

.task-title {
  font-size: 13px;
}

.similarity-score {
  font-size: 12px;
  color: #666;
}

/* Actions */
.result-actions {
  padding: 16px;
  border-top: 1px solid #e9ecef;
  display: flex;
  gap: 12px;
}

.create-task-btn, .analyze-more-btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid #ddd;
  cursor: pointer;
  font-size: 13px;
}

.create-task-btn {
  background: #28a745;
  color: white;
  border-color: #28a745;
}

.analyze-more-btn {
  background: white;
  color: #667eea;
  border-color: #667eea;
}

/* Analysis Mode */
.analysis-section {
  text-align: center;
  margin-bottom: 20px;
}

.section-desc {
  color: #666;
  font-size: 13px;
  margin: 8px 0 16px;
}

.analyze-current-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
}

.analysis-item {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.analysis-item:last-child {
  border-bottom: none;
}

.analysis-label {
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.analysis-content {
  font-size: 13px;
  line-height: 1.5;
}

/* Batch Mode */
.batch-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: vertical;
  font-family: monospace;
  font-size: 13px;
  margin-bottom: 12px;
}

.batch-process-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  width: 100%;
}

.batch-result-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.result-index {
  width: 24px;
  height: 24px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.result-content {
  flex: 1;
}

.task-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.confidence {
  font-weight: 500;
}

.batch-actions {
  padding: 16px;
  border-top: 1px solid #e9ecef;
}

.create-all-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  width: 100%;
}

/* Insights Mode */
.insights-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.time-frame-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.get-insights-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
}

.insight-item {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.insight-label {
  font-weight: 600;
  margin-bottom: 12px;
  color: #333;
}

.workload-metrics {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.metric-label {
  color: #666;
}

.metric-value {
  font-weight: 500;
}

.workload-level.optimal {
  color: #28a745;
}

.workload-level.high {
  color: #ffc107;
}

.workload-level.overloaded {
  color: #dc3545;
}

.recommendation-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.recommendation-item {
  padding: 8px 0;
  font-size: 13px;
  line-height: 1.4;
  border-bottom: 1px solid #f8f9fa;
}

.recommendation-item:before {
  content: "💡 ";
  margin-right: 6px;
}

/* Loading Spinner */
.loading-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.count-badge, .time-badge {
  padding: 4px 8px;
  background: #e3f2fd;
  color: #1565c0;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
</style>