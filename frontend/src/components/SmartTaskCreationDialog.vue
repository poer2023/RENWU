<template>
  <el-dialog
    v-model="visible"
    title="🤖 智能任务创建"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="true"
    @close="handleClose"
    class="smart-task-dialog"
  >
    <!-- Header with mode switch -->
    <div class="dialog-header">
      <div class="header-title">
        <span class="title-icon">✨</span>
        <span class="title-text">TaskWall AI v3.0 智能助手</span>
      </div>
      <div class="creation-modes">
        <el-radio-group v-model="creationMode" size="small">
          <el-radio-button value="single">单个任务</el-radio-button>
          <el-radio-button value="batch">批量创建</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- Single Task Mode -->
    <div v-if="creationMode === 'single'" class="single-mode">
      <div class="input-section">
        <el-input
          v-model="naturalLanguageInput"
          type="textarea"
          :rows="4"
          placeholder="用自然语言描述你的任务，比如：&#10;'明天下午3点开会讨论项目进度，高优先级'&#10;'这周完成用户登录功能的开发和测试'&#10;'写一份产品需求文档，预计需要4小时'"
          class="nl-input"
          @keydown.ctrl.enter="parseTask"
        />
        <div class="input-controls">
          <div class="controls-left">
            <el-checkbox v-model="enableSmartAnalysis">
              开启智能分析
            </el-checkbox>
            <el-tooltip content="智能分析将提供分类建议、优先级评估、相似任务检测等功能">
              <el-icon class="help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
          <div class="controls-right">
            <el-button 
              type="primary" 
              @click="parseTask"
              :loading="loading"
              :disabled="!naturalLanguageInput.trim()"
            >
              <el-icon><MagicStick /></el-icon>
              {{ loading ? '解析中...' : '智能解析' }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- Parse Results -->
      <div v-if="parseResult" class="parse-results">
        <div class="result-header">
          <span class="result-title">🎯 解析结果</span>
          <el-tag :type="getConfidenceType(parseResult.confidence)" size="small">
            置信度: {{ Math.round(parseResult.confidence * 100) }}%
          </el-tag>
        </div>

        <!-- Task Preview -->
        <div class="task-preview">
          <el-form :model="taskForm" label-width="80px" label-position="left">
            <el-form-item label="标题">
              <el-input v-model="taskForm.title" placeholder="任务标题" />
            </el-form-item>
            
            <el-form-item label="描述">
              <el-input 
                v-model="taskForm.description" 
                type="textarea" 
                :rows="2" 
                placeholder="任务描述（可选）" 
              />
            </el-form-item>
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="优先级">
                  <el-select v-model="taskForm.urgency" style="width: 100%">
                    <el-option v-for="(name, value) in priorityOptions" :key="value" :label="name" :value="parseInt(value)" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="分类">
                  <el-input v-model="taskForm.category" placeholder="自动分类" readonly />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="预估工时">
                  <el-input-number 
                    v-model="taskForm.estimated_hours" 
                    :min="0" 
                    :max="100" 
                    :step="0.5"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="截止时间">
                  <el-date-picker 
                    v-model="taskForm.due_date" 
                    type="datetime" 
                    placeholder="选择截止时间"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <!-- AI Enhancements -->
        <div v-if="aiEnhancements.length > 0" class="ai-enhancements">
          <div class="enhancement-header">
            <el-icon><MagicStick /></el-icon>
            <span>AI 增强建议</span>
          </div>
          <div class="enhancement-list">
            <div v-for="enhancement in aiEnhancements" :key="enhancement.type" class="enhancement-item">
              <el-tag :type="enhancement.tagType" size="small">{{ enhancement.label }}</el-tag>
              <span class="enhancement-content">{{ enhancement.content }}</span>
              <el-button 
                v-if="enhancement.actionable" 
                size="small" 
                text 
                @click="applyEnhancement(enhancement)"
              >
                应用
              </el-button>
            </div>
          </div>
        </div>

        <!-- Similar Tasks Warning -->
        <div v-if="parseResult.similar_tasks && parseResult.similar_tasks.length > 0" class="similar-tasks-warning">
          <el-alert
            :title="`发现 ${parseResult.similar_tasks.length} 个相似任务`"
            type="warning"
            :closable="false"
            show-icon
          >
            <template #default>
              <div class="similar-tasks-list">
                <div v-for="task in parseResult.similar_tasks.slice(0, 3)" :key="task.task_id" class="similar-task">
                  <span class="task-title">{{ task.task_title }}</span>
                  <el-tag size="small">{{ Math.round(task.similarity_score * 100) }}% 相似</el-tag>
                </div>
              </div>
              <el-button size="small" text @click="showSimilarTasksDetail = true">
                查看详情
              </el-button>
            </template>
          </el-alert>
        </div>
      </div>
    </div>

    <!-- Batch Mode -->
    <div v-else-if="creationMode === 'batch'" class="batch-mode">
      <div class="batch-input-section">
        <div class="batch-header">
          <span class="batch-title">📝 批量任务创建</span>
          <span class="batch-hint">每行输入一个任务</span>
        </div>
        <el-input
          v-model="batchInput"
          type="textarea"
          :rows="8"
          placeholder="每行输入一个任务，例如：&#10;修复登录页面bug&#10;设计新的用户界面&#10;测试支付功能，高优先级&#10;编写API文档，预计2小时&#10;明天开会讨论项目进度"
          class="batch-textarea"
        />
        <div class="batch-controls">
          <div class="batch-info">
            <span class="task-count">{{ batchTaskCount }} 个任务</span>
          </div>
          <el-button 
            type="primary" 
            @click="processBatch"
            :loading="loading"
            :disabled="batchTaskCount === 0"
          >
            <el-icon><MagicStick /></el-icon>
            {{ loading ? '处理中...' : '批量处理' }}
          </el-button>
        </div>
      </div>

      <!-- Batch Results -->
      <div v-if="batchResults.length > 0" class="batch-results">
        <div class="result-header">
          <span class="result-title">🎯 批量处理结果</span>
          <el-tag size="small">{{ batchResults.length }} 个任务</el-tag>
        </div>
        
        <div class="batch-task-list">
          <div 
            v-for="(result, index) in batchResults" 
            :key="index"
            class="batch-task-item"
          >
            <div class="task-index">{{ index + 1 }}</div>
            <div class="task-content">
              <div class="task-title">{{ result.suggested_task.title }}</div>
              <div class="task-meta">
                <el-tag size="small" :type="getPriorityType(result.suggested_task.priority)">
                  {{ getPriorityName(result.suggested_task.priority) }}
                </el-tag>
                <span v-if="result.suggested_task.category" class="category">
                  {{ result.suggested_task.category }}
                </span>
                <span class="confidence">{{ Math.round(result.confidence * 100) }}%</span>
              </div>
            </div>
            <div class="task-actions">
              <el-button size="small" @click="editBatchTask(index)">编辑</el-button>
              <el-button size="small" type="danger" @click="removeBatchTask(index)">移除</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dialog Footer -->
    <template #footer>
      <div class="dialog-footer">
        <div class="footer-left">
          <el-button @click="handleClose">取消</el-button>
          <el-button v-if="creationMode === 'single' && parseResult" @click="analyzeTask">
            <el-icon><Search /></el-icon>
            深度分析
          </el-button>
        </div>
        <div class="footer-right">
          <el-button 
            v-if="creationMode === 'single'" 
            type="primary" 
            @click="createSingleTask"
            :disabled="!canCreateSingle"
          >
            <el-icon><Plus /></el-icon>
            创建任务
          </el-button>
          <el-button 
            v-else-if="creationMode === 'batch'" 
            type="primary" 
            @click="createBatchTasks"
            :disabled="batchResults.length === 0"
          >
            <el-icon><Plus /></el-icon>
            创建所有任务 ({{ batchResults.length }})
          </el-button>
        </div>
      </div>
    </template>

    <!-- Similar Tasks Detail Dialog -->
    <el-dialog
      v-model="showSimilarTasksDetail"
      title="相似任务详情"
      width="500px"
      append-to-body
    >
      <div v-if="parseResult?.similar_tasks" class="similar-tasks-detail">
        <div v-for="task in parseResult.similar_tasks" :key="task.task_id" class="similar-task-detail">
          <div class="task-header">
            <span class="task-title">{{ task.task_title }}</span>
            <el-tag :type="getSimilarityType(task.similarity_score)">
              {{ Math.round(task.similarity_score * 100) }}% 相似
            </el-tag>
          </div>
          <div class="similarity-type">类型: {{ task.similarity_type }}</div>
          <div v-if="task.reasoning && task.reasoning.length > 0" class="reasoning">
            <div class="reasoning-title">相似原因:</div>
            <ul class="reasoning-list">
              <li v-for="reason in task.reasoning.slice(0, 3)" :key="reason">{{ reason }}</li>
            </ul>
          </div>
        </div>
      </div>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElDialog, ElInput, ElButton, ElRadioGroup, ElRadioButton, ElCheckbox, ElForm, ElFormItem, ElSelect, ElOption, ElInputNumber, ElDatePicker, ElRow, ElCol, ElTag, ElAlert, ElIcon, ElTooltip, ElMessage } from 'element-plus'
import { Plus, MagicStick, Search, QuestionFilled } from '@element-plus/icons-vue'
import { useAIAssistantV3 } from '@/composables/useAIAssistantV3'

interface Props {
  visible: boolean
  position?: { x: number, y: number }
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:visible': [value: boolean]
  'task-created': [task: any]
  'tasks-created': [tasks: any[]]
}>()

const { 
  loading, 
  parseNaturalLanguage, 
  processBatch: processBatchAPI, 
  analyzeTask: analyzeTaskAPI 
} = useAIAssistantV3()

// Dialog state
const visible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// Creation modes
const creationMode = ref('single')

// Single task mode state
const naturalLanguageInput = ref('')
const enableSmartAnalysis = ref(true)
const parseResult = ref<any>(null)
const taskForm = ref({
  title: '',
  description: '',
  urgency: 2,
  category: '',
  estimated_hours: 0,
  due_date: null as Date | null
})

// Batch mode state
const batchInput = ref('')
const batchResults = ref<any[]>([])

// UI state
const showSimilarTasksDetail = ref(false)

// Priority options
const priorityOptions = {
  0: '🚨 紧急',
  1: '⚡ 高',
  2: '📝 中',
  3: '📋 低',
  4: '💭 待办'
}

// Computed properties
const batchTaskCount = computed(() => {
  return batchInput.value.split('\n').filter(line => line.trim()).length
})

const canCreateSingle = computed(() => {
  return taskForm.value.title.trim().length > 0
})

const aiEnhancements = computed(() => {
  if (!parseResult.value?.ai_enhancements) return []
  
  const enhancements = []
  
  // Classification enhancement
  if (parseResult.value.ai_enhancements.classification?.data?.category) {
    enhancements.push({
      type: 'classification',
      label: '分类建议',
      content: parseResult.value.ai_enhancements.classification.data.category,
      tagType: 'primary',
      actionable: true
    })
  }
  
  // Priority enhancement
  if (parseResult.value.ai_enhancements.priority?.data?.priority_level !== undefined) {
    const priorityLevel = parseResult.value.ai_enhancements.priority.data.priority_level
    enhancements.push({
      type: 'priority',
      label: '优先级建议',
      content: `建议设置为 ${getPriorityName(priorityLevel)}`,
      tagType: 'warning',
      actionable: true,
      value: priorityLevel
    })
  }
  
  return enhancements
})

// Methods
const parseTask = async () => {
  if (!naturalLanguageInput.value.trim()) return
  
  try {
    const result = await parseNaturalLanguage(
      naturalLanguageInput.value,
      {},
      enableSmartAnalysis.value
    )
    
    parseResult.value = result
    
    // Populate form with parsed data
    taskForm.value = {
      title: result.suggested_task.title || '',
      description: result.suggested_task.description || '',
      urgency: result.suggested_task.priority ?? 2,
      category: result.suggested_task.category || '',
      estimated_hours: result.suggested_task.estimated_hours || 0,
      due_date: result.suggested_task.deadline ? new Date(result.suggested_task.deadline) : null
    }
    
  } catch (error) {
    console.error('Parse failed:', error)
    ElMessage.error('任务解析失败，请重试')
  }
}

const processBatch = async () => {
  const lines = batchInput.value.split('\n').filter(line => line.trim())
  if (lines.length === 0) return
  
  try {
    const result = await processBatchAPI(lines, {})
    batchResults.value = result.results
  } catch (error) {
    console.error('Batch processing failed:', error)
    ElMessage.error('批量处理失败，请重试')
  }
}

const analyzeTask = async () => {
  if (!parseResult.value) return
  
  try {
    // This would open a detailed analysis dialog
    ElMessage.info('深度分析功能即将推出')
  } catch (error) {
    console.error('Analysis failed:', error)
  }
}

const createSingleTask = () => {
  const task = {
    ...taskForm.value,
    ai_generated: true,
    ai_confidence: parseResult.value?.confidence || 0
  }
  
  emit('task-created', task)
  handleClose()
}

const createBatchTasks = () => {
  const tasks = batchResults.value.map(result => ({
    title: result.suggested_task.title,
    description: result.suggested_task.description || '',
    urgency: result.suggested_task.priority ?? 2,
    category: result.suggested_task.category || '',
    estimated_hours: result.suggested_task.estimated_hours || 0,
    due_date: result.suggested_task.deadline ? new Date(result.suggested_task.deadline) : null,
    ai_generated: true,
    ai_confidence: result.confidence
  }))
  
  emit('tasks-created', tasks)
  handleClose()
}

const applyEnhancement = (enhancement: any) => {
  switch (enhancement.type) {
    case 'classification':
      taskForm.value.category = enhancement.content
      break
    case 'priority':
      taskForm.value.urgency = enhancement.value
      break
  }
}

const editBatchTask = (index: number) => {
  // Switch to single mode and populate with batch task data
  const result = batchResults.value[index]
  creationMode.value = 'single'
  naturalLanguageInput.value = '' // Clear input since we're editing
  parseResult.value = result
  taskForm.value = {
    title: result.suggested_task.title || '',
    description: result.suggested_task.description || '',
    urgency: result.suggested_task.priority ?? 2,
    category: result.suggested_task.category || '',
    estimated_hours: result.suggested_task.estimated_hours || 0,
    due_date: result.suggested_task.deadline ? new Date(result.suggested_task.deadline) : null
  }
  // Remove from batch
  batchResults.value.splice(index, 1)
}

const removeBatchTask = (index: number) => {
  batchResults.value.splice(index, 1)
}

const handleClose = () => {
  // Reset state
  naturalLanguageInput.value = ''
  batchInput.value = ''
  parseResult.value = null
  batchResults.value = []
  taskForm.value = {
    title: '',
    description: '',
    urgency: 2,
    category: '',
    estimated_hours: 0,
    due_date: null
  }
  showSimilarTasksDetail.value = false
  creationMode.value = 'single'
  
  visible.value = false
}

// Utility functions
const getConfidenceType = (confidence: number) => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'warning'
  return 'danger'
}

const getPriorityType = (priority: number) => {
  const types = ['danger', 'warning', 'primary', 'info', 'success']
  return types[priority] || 'primary'
}

const getPriorityName = (priority: number) => {
  const names = ['紧急', '高', '中', '低', '待办']
  return names[priority] || '中'
}

const getSimilarityType = (score: number) => {
  if (score >= 0.8) return 'danger'
  if (score >= 0.6) return 'warning'
  return 'primary'
}
</script>

<style scoped>
.smart-task-dialog :deep(.el-dialog__body) {
  padding: 0 20px 20px;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 20px;
}

.title-text {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* Single Mode Styles */
.input-section {
  margin-bottom: 20px;
}

.nl-input {
  margin-bottom: 12px;
}

.input-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.controls-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.help-icon {
  color: #909399;
  cursor: pointer;
}

.parse-results {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.result-title {
  font-weight: 600;
  color: #303133;
}

.task-preview {
  padding: 20px;
}

.ai-enhancements {
  padding: 16px;
  background: #fafbfc;
  border-top: 1px solid #ebeef5;
}

.enhancement-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  font-weight: 600;
  color: #303133;
}

.enhancement-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.enhancement-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.enhancement-content {
  flex: 1;
  font-size: 14px;
}

.similar-tasks-warning {
  padding: 16px;
  border-top: 1px solid #ebeef5;
}

.similar-tasks-list {
  margin: 8px 0;
}

.similar-task {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.task-title {
  font-size: 14px;
  color: #303133;
}

/* Batch Mode Styles */
.batch-input-section {
  margin-bottom: 20px;
}

.batch-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.batch-title {
  font-weight: 600;
  color: #303133;
}

.batch-hint {
  font-size: 12px;
  color: #909399;
}

.batch-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.task-count {
  font-size: 14px;
  color: #606266;
}

.batch-results {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}

.batch-task-list {
  max-height: 300px;
  overflow-y: auto;
}

.batch-task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #f5f7fa;
}

.batch-task-item:last-child {
  border-bottom: none;
}

.task-index {
  width: 24px;
  height: 24px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.task-content {
  flex: 1;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 12px;
}

.category {
  color: #909399;
}

.confidence {
  color: #67c23a;
  font-weight: 500;
}

.task-actions {
  display: flex;
  gap: 8px;
}

/* Dialog Footer */
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-left, .footer-right {
  display: flex;
  gap: 12px;
}

/* Similar Tasks Detail */
.similar-tasks-detail {
  max-height: 400px;
  overflow-y: auto;
}

.similar-task-detail {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 12px;
}

.similar-task-detail:last-child {
  margin-bottom: 0;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.similarity-type {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.reasoning-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}

.reasoning-list {
  margin: 0;
  padding-left: 16px;
  font-size: 12px;
  color: #606266;
}

.reasoning-list li {
  margin-bottom: 2px;
}
</style>