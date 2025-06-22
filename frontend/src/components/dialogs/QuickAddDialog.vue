<template>
  <div v-if="visible" class="command-palette-overlay" @click="handleOverlayClick">
    <div class="command-palette quick-add-dialog" @click.stop>
      <!-- Header -->
      <div class="search-container">
        <div class="search-icon">➕</div>
        <div class="view-title">快速添加任务</div>
        <div class="creation-mode-toggle">
          <button 
            :class="['mode-btn', { active: creationMode === 'manual' }]"
            @click="creationMode = 'manual'"
          >
            ✏️ 手动创建
          </button>
          <button 
            :class="['mode-btn', { active: creationMode === 'ai' }]"
            @click="creationMode = 'ai'"
          >
            🤖 AI 智能创建
          </button>
        </div>
        <button @click="handleClose" class="close-button">✕</button>
      </div>
      
      <!-- Form Content -->
      <div class="results-container">
        <!-- Manual Creation Form -->
        <div v-if="creationMode === 'manual'" class="form-section">
          <div class="form-item">
            <div class="form-label">
              <span class="label-text">任务标题</span>
              <span class="label-required">*</span>
            </div>
            <input
              ref="titleInput"
              v-model="formData.title"
              placeholder="请输入任务标题"
              class="form-input"
              @keydown.enter="handleSubmit"
            />
          </div>
          
          <div class="form-item">
            <div class="form-label">
              <span class="label-text">任务描述</span>
            </div>
            <textarea
              v-model="formData.description"
              placeholder="请输入任务描述（可选）"
              class="form-textarea"
              rows="3"
            ></textarea>
          </div>
          
          <div class="form-row">
            <div class="form-item half">
              <div class="form-label">
                <span class="label-text">优先级</span>
              </div>
              <div class="priority-selector">
                <div
                  v-for="priority in priorityOptions"
                  :key="priority.value"
                  :class="['priority-option', `priority-${priority.value}`, { active: formData.urgency === priority.value }]"
                  @click="formData.urgency = priority.value"
                >
                  <div class="priority-badge">P{{ priority.value }}</div>
                  <div class="priority-label">{{ priority.label }}</div>
                </div>
              </div>
            </div>
            
            <div class="form-item half">
              <div class="form-label">
                <span class="label-text">模块</span>
              </div>
              <div class="module-selector">
                <div
                  :class="['module-option', { active: formData.module_id === null }]"
                  @click="formData.module_id = null"
                >
                  <div class="module-color" style="background: #94a3b8;"></div>
                  <div class="module-name">无模块</div>
                </div>
                <div
                  v-for="module in modules"
                  :key="module.id"
                  :class="['module-option', { active: formData.module_id === module.id }]"
                  @click="formData.module_id = module.id"
                >
                  <div class="module-color" :style="{ background: module.color }"></div>
                  <div class="module-name">{{ module.name }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- AI Creation Form -->
        <div v-if="creationMode === 'ai'" class="ai-form-section">
          <div class="ai-intro">
            <div class="ai-intro-icon">🤖</div>
            <div class="ai-intro-text">
              <h3>AI 智能任务创建</h3>
              <p>描述你的想法，AI 会帮你自动创建和分解任务</p>
            </div>
          </div>
          
          <div class="form-item">
            <div class="form-label">
              <span class="label-text">任务描述</span>
              <span class="label-required">*</span>
            </div>
            <textarea
              ref="aiInput"
              v-model="aiFormData.description"
              placeholder="例如：准备下周的产品发布会，包括演示文稿、邀请嘉宾、场地安排等..."
              class="ai-textarea"
              rows="4"
            ></textarea>
            <div class="ai-hint">
              💡 提示：描述得越详细，AI 生成的任务就越准确
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-item half">
              <div class="form-label">
                <span class="label-text">默认优先级</span>
              </div>
              <div class="priority-selector">
                <div
                  v-for="priority in priorityOptions"
                  :key="priority.value"
                  :class="['priority-option', `priority-${priority.value}`, { active: aiFormData.defaultPriority === priority.value }]"
                  @click="aiFormData.defaultPriority = priority.value"
                >
                  <div class="priority-badge">P{{ priority.value }}</div>
                  <div class="priority-label">{{ priority.label }}</div>
                </div>
              </div>
            </div>
            
            <div class="form-item half">
              <div class="form-label">
                <span class="label-text">模块</span>
              </div>
              <div class="module-selector">
                <div
                  :class="['module-option', { active: aiFormData.module_id === null }]"
                  @click="aiFormData.module_id = null"
                >
                  <div class="module-color" style="background: #94a3b8;"></div>
                  <div class="module-name">无模块</div>
                </div>
                <div
                  v-for="module in modules"
                  :key="module.id"
                  :class="['module-option', { active: aiFormData.module_id === module.id }]"
                  @click="aiFormData.module_id = module.id"
                >
                  <div class="module-color" :style="{ background: module.color }"></div>
                  <div class="module-name">{{ module.name }}</div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="ai-options">
            <div class="form-label">
              <span class="label-text">AI 创建选项</span>
            </div>
            <div class="checkbox-group">
              <label class="checkbox-item">
                <input type="checkbox" v-model="aiFormData.generateSubtasks" />
                <span class="checkbox-label">
                  <strong>自动分解子任务</strong>
                  <small>将复杂任务分解为多个子任务</small>
                </span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="aiFormData.detectSimilar" />
                <span class="checkbox-label">
                  <strong>检测相似任务</strong>
                  <small>检查是否有类似的现有任务</small>
                </span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="aiFormData.suggestDependencies" />
                <span class="checkbox-label">
                  <strong>建议依赖关系</strong>
                  <small>分析任务间的逻辑依赖关系</small>
                </span>
              </label>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Footer -->
      <div class="palette-footer">
        <div class="footer-actions">
          <button @click="handleClose" class="footer-btn">取消</button>
          <button 
            @click="handleSubmit" 
            :disabled="!canSubmit || loading"
            class="footer-btn primary"
          >
            {{ getSubmitButtonText() }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { useTaskStore, type Module } from '@/stores/tasks'

interface Props {
  modelValue: boolean
  modules?: Module[]
}

const props = withDefaults(defineProps<Props>(), {
  modules: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'created': [task: any]
}>()

const taskStore = useTaskStore()

const visible = ref(props.modelValue)
const loading = ref(false)
const titleInput = ref<HTMLInputElement>()
const aiInput = ref<HTMLTextAreaElement>()
const creationMode = ref<'manual' | 'ai'>('manual')

// Form data
const formData = ref({
  title: '',
  description: '',
  urgency: 2,
  module_id: null as number | null
})

// AI Form data
const aiFormData = ref({
  description: '',
  defaultPriority: 2,
  module_id: null as number | null,
  generateSubtasks: true,
  detectSimilar: true,
  suggestDependencies: false
})

const priorityOptions = ref([
  { value: 1, label: '高优先级' },
  { value: 2, label: '中优先级' },
  { value: 3, label: '低优先级' }
])

// Watch for external visibility changes
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal) {
    // Reset forms when opening
    formData.value = {
      title: '',
      description: '',
      urgency: 2,
      module_id: null
    }
    aiFormData.value = {
      description: '',
      defaultPriority: 2,
      module_id: null,
      generateSubtasks: true,
      detectSimilar: true,
      suggestDependencies: false
    }
    creationMode.value = 'manual'
    // Focus on appropriate input
    nextTick(() => {
      if (creationMode.value === 'manual') {
        titleInput.value?.focus()
      } else {
        aiInput.value?.focus()
      }
    })
  }
})

// Watch for internal visibility changes
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

function handleOverlayClick() {
  handleClose()
}

function handleClose() {
  visible.value = false
}

// Computed properties
const canSubmit = computed(() => {
  if (creationMode.value === 'manual') {
    return formData.value.title.trim().length > 0
  } else {
    return aiFormData.value.description.trim().length > 0
  }
})

function getSubmitButtonText() {
  if (loading.value) {
    return creationMode.value === 'manual' ? '创建中...' : 'AI 分析中...'
  }
  return creationMode.value === 'manual' ? '创建任务' : 'AI 智能创建'
}

async function handleSubmit() {
  if (!canSubmit.value || loading.value) return
  
  loading.value = true
  
  try {
    if (creationMode.value === 'manual') {
      await handleManualSubmit()
    } else {
      await handleAISubmit()
    }
  } catch (error) {
    console.error('Failed to create task:', error)
  } finally {
    loading.value = false
  }
}

async function handleManualSubmit() {
  const newTask = {
    ...formData.value,
    id: Date.now(),
    x: Math.random() * 400 + 100,
    y: Math.random() * 400 + 100,
    completed: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
  
  await taskStore.addTask(newTask)
  emit('created', newTask)
  visible.value = false
  
  // Reset form
  formData.value = {
    title: '',
    description: '',
    urgency: 2,
    module_id: null
  }
}

async function handleAISubmit() {
  // Simulate AI processing
  await new Promise(resolve => setTimeout(resolve, 1500))
  
  const aiResponse = await generateAITasks(aiFormData.value.description)
  
  // Create tasks from AI response
  const createdTasks = []
  for (const taskData of aiResponse.tasks) {
    const newTask = {
      ...taskData,
      id: Date.now() + Math.random(),
      urgency: aiFormData.value.defaultPriority,
      module_id: aiFormData.value.module_id,
      x: Math.random() * 400 + 100,
      y: Math.random() * 400 + 100,
      completed: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    
    await taskStore.addTask(newTask)
    createdTasks.push(newTask)
  }
  
  emit('created', { tasks: createdTasks, aiResponse })
  visible.value = false
  
  // Reset AI form
  aiFormData.value = {
    description: '',
    defaultPriority: 2,
    module_id: null,
    generateSubtasks: true,
    detectSimilar: true,
    suggestDependencies: false
  }
}

async function generateAITasks(description: string) {
  // Mock AI task generation - in real implementation, this would call your AI service
  const mockTasks = [
    {
      title: description.split('，')[0] || description.substring(0, 20),
      description: `AI 解析：${description}`
    }
  ]
  
  // Add subtasks if enabled
  if (aiFormData.value.generateSubtasks) {
    mockTasks.push(
      {
        title: '准备工作',
        description: '收集相关资料和信息'
      },
      {
        title: '执行阶段',
        description: '按计划执行主要任务'
      },
      {
        title: '总结回顾',
        description: '整理成果并总结经验'
      }
    )
  }
  
  return {
    tasks: mockTasks,
    similar: aiFormData.value.detectSimilar ? [] : undefined,
    dependencies: aiFormData.value.suggestDependencies ? [] : undefined
  }
}
</script>

<style scoped>
/* Command Palette Style Overlays */
.command-palette-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(12px);
  z-index: 2000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  animation: overlayFadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes overlayFadeIn {
  from {
    opacity: 0;
    backdrop-filter: blur(0px);
  }
  to {
    opacity: 1;
    backdrop-filter: blur(12px);
  }
}

/* Enhanced Main Palette Container */
.command-palette.quick-add-dialog {
  width: 560px;
  max-width: 90vw;
  max-height: 80vh;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 20px;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.15),
    0 8px 32px rgba(102, 126, 234, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 0.8);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: paletteSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes paletteSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Header */
.search-container {
  position: relative;
  display: flex;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%);
  gap: 16px;
}

/* Creation Mode Toggle */
.creation-mode-toggle {
  display: flex;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 12px;
  padding: 4px;
  gap: 2px;
}

.mode-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.mode-btn:hover {
  background: rgba(102, 126, 234, 0.1);
  color: rgba(102, 126, 234, 0.8);
}

.mode-btn.active {
  background: rgba(102, 126, 234, 0.8);
  color: white;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
}

.search-icon {
  color: rgba(102, 126, 234, 0.7);
  font-size: 20px;
  margin-right: 16px;
  flex-shrink: 0;
}

.view-title {
  flex: 1;
  font-size: 16px;
  color: #1a202c;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.5;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  font-size: 18px;
  color: rgba(102, 126, 234, 0.6);
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.close-button:hover {
  background: rgba(102, 126, 234, 0.1);
  color: rgba(102, 126, 234, 0.9);
}

/* Form Content */
.results-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%);
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item.half {
  flex: 1;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 4px;
}

.label-text {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.label-required {
  color: #ef4444;
  font-weight: 700;
}

.form-input, .form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.8);
  transition: all 0.3s ease;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: rgba(102, 126, 234, 0.5);
  background: rgba(255, 255, 255, 1);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

/* Priority Selector */
.priority-selector {
  display: flex;
  gap: 8px;
}

.priority-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
}

.priority-option:hover {
  background: rgba(102, 126, 234, 0.05);
  border-color: rgba(102, 126, 234, 0.3);
}

.priority-option.active {
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.4);
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.priority-badge {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  color: white;
}

.priority-1 .priority-badge {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.priority-2 .priority-badge {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.priority-3 .priority-badge {
  background: linear-gradient(135deg, #10b981, #059669);
}

.priority-label {
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  text-align: center;
}

/* Module Selector */
.module-selector {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 120px;
  overflow-y: auto;
}

.module-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
}

.module-option:hover {
  background: rgba(102, 126, 234, 0.05);
  border-color: rgba(102, 126, 234, 0.3);
}

.module-option.active {
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.4);
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.module-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  flex-shrink: 0;
}

.module-name {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Footer */
.palette-footer {
  padding: 20px 24px;
  border-top: 2px solid rgba(102, 126, 234, 0.1);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%);
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.footer-btn {
  padding: 12px 24px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.8);
  color: #374151;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.footer-btn:hover {
  background: rgba(102, 126, 234, 0.05);
  border-color: rgba(102, 126, 234, 0.4);
}

.footer-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.footer-btn.primary {
  background: rgba(102, 126, 234, 0.8);
  color: white;
  border-color: rgba(102, 126, 234, 0.8);
}

.footer-btn.primary:hover:not(:disabled) {
  background: rgba(102, 126, 234, 1);
  border-color: rgba(102, 126, 234, 1);
}

/* Scrollbar Styling */
.module-selector::-webkit-scrollbar {
  width: 4px;
}

.module-selector::-webkit-scrollbar-track {
  background: rgba(102, 126, 234, 0.05);
  border-radius: 2px;
}

.module-selector::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 2px;
}

.module-selector::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}

/* AI Form Section */
.ai-form-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.ai-intro {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  border: 2px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
}

.ai-intro-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.ai-intro-text h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a202c;
}

.ai-intro-text p {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.4;
}

.ai-textarea {
  width: 100%;
  padding: 16px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.8);
  transition: all 0.3s ease;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  resize: vertical;
  min-height: 100px;
  line-height: 1.5;
}

.ai-textarea:focus {
  outline: none;
  border-color: rgba(102, 126, 234, 0.5);
  background: rgba(255, 255, 255, 1);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.ai-hint {
  font-size: 12px;
  color: #64748b;
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(245, 158, 11, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(245, 158, 11, 0.1);
}

.ai-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkbox-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  padding: 12px;
  border-radius: 12px;
  transition: all 0.3s ease;
  border: 2px solid rgba(102, 126, 234, 0.1);
}

.checkbox-item:hover {
  background: rgba(102, 126, 234, 0.05);
  border-color: rgba(102, 126, 234, 0.2);
}

.checkbox-item input[type="checkbox"] {
  margin: 0;
  width: 16px;
  height: 16px;
  accent-color: rgba(102, 126, 234, 0.8);
  cursor: pointer;
}

.checkbox-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.checkbox-label strong {
  font-size: 14px;
  color: #1a202c;
  font-weight: 600;
}

.checkbox-label small {
  font-size: 12px;
  color: #64748b;
  line-height: 1.3;
}

/* Responsive Design */
@media (max-width: 768px) {
  .command-palette.quick-add-dialog {
    width: 95vw;
    max-height: 85vh;
  }
  
  .creation-mode-toggle {
    flex-direction: column;
    width: 100%;
  }
  
  .mode-btn {
    width: 100%;
    text-align: center;
  }
  
  .form-row {
    flex-direction: column;
    gap: 16px;
  }
  
  .priority-selector {
    flex-direction: column;
  }
  
  .footer-actions {
    flex-direction: column;
  }
  
  .ai-intro {
    flex-direction: column;
    text-align: center;
  }
}
</style>