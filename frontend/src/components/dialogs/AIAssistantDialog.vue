<template>
  <div v-if="visible" class="command-palette-overlay" @click="handleOverlayClick">
    <div class="command-palette ai-assistant-dialog" @click.stop>
      <!-- Header -->
      <div class="search-container">
        <div class="search-icon">🤖</div>
        <div class="view-title">AI 助手</div>
        <button @click="handleClose" class="close-button">✕</button>
      </div>
      
      <!-- Chat Content -->
      <div class="results-container">
        <div class="chat-container">
          <!-- Messages -->
          <div class="chat-messages" ref="chatContainer">
            <div v-for="(message, index) in messages" :key="index" :class="['message', message.role]">
              <div class="message-wrapper">
                <div class="message-avatar">
                  <span v-if="message.role === 'user'">👤</span>
                  <span v-else>🤖</span>
                </div>
                <div class="message-bubble">
                  <div class="message-header">
                    <span class="message-role">{{ message.role === 'user' ? '你' : 'AI 助手' }}</span>
                    <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                  </div>
                  <div class="message-content">
                    <div v-html="formatMessage(message.content)"></div>
                    <div v-if="message.suggestions && message.suggestions.length > 0" class="suggestions">
                      <div class="suggestions-label">建议操作：</div>
                      <div class="suggestion-buttons">
                        <button 
                          v-for="(suggestion, idx) in message.suggestions" 
                          :key="idx"
                          class="suggestion-btn"
                          @click="applySuggestion(suggestion)"
                        >
                          {{ suggestion.label }}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-if="thinking" class="message assistant thinking">
              <div class="message-wrapper">
                <div class="message-avatar">
                  <span>🤖</span>
                </div>
                <div class="message-bubble thinking-bubble">
                  <div class="message-header">
                    <span class="message-role">AI 助手</span>
                  </div>
                  <div class="message-content">
                    <div class="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    正在思考...
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Quick Actions -->
          <div class="quick-actions-section">
            <div class="section-header">
              <div class="search-icon">⚡</div>
              <span>快速操作</span>
            </div>
            <div class="quick-actions-grid">
              <button class="quick-action-btn" @click="askForHelp('分析当前任务')">
                <span class="action-icon">📊</span>
                <span class="action-label">分析当前任务</span>
              </button>
              <button class="quick-action-btn" @click="askForHelp('生成周报')">
                <span class="action-icon">📝</span>
                <span class="action-label">生成周报</span>
              </button>
              <button class="quick-action-btn" @click="askForHelp('优化任务安排')">
                <span class="action-icon">🎯</span>
                <span class="action-label">优化任务安排</span>
              </button>
              <button class="quick-action-btn" @click="askForHelp('识别风险')">
                <span class="action-icon">⚠️</span>
                <span class="action-label">识别风险</span>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Input Area -->
      <div class="chat-input-section">
        <div class="input-container">
          <textarea
            ref="inputRef"
            v-model="inputMessage"
            placeholder="输入你的问题或需求... (Ctrl+Enter 发送)"
            class="chat-input"
            rows="3"
            @keydown.ctrl.enter="sendMessage"
          ></textarea>
          <div class="input-actions">
            <button @click="clearChat" class="input-btn secondary">清空对话</button>
            <button @click="sendMessage" :disabled="!inputMessage.trim() || thinking" class="input-btn primary">
              {{ thinking ? '发送中...' : '发送' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useTaskStore } from '@/stores/tasks'

interface Props {
  modelValue: boolean
  context?: any
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  suggestions?: Array<{ label: string; action: string; data?: any }>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'apply-suggestion': [suggestion: any]
}>()

const taskStore = useTaskStore()

const visible = ref(props.modelValue)
const thinking = ref(false)
const inputMessage = ref('')
const messages = ref<Message[]>([
  {
    role: 'assistant',
    content: '你好！我是你的AI助手。我可以帮助你分析任务、生成报告、优化工作流程等。有什么我可以帮助你的吗？',
    timestamp: new Date()
  }
])

const chatContainer = ref<HTMLDivElement>()
const inputRef = ref<HTMLTextAreaElement>()

// Watch for external visibility changes
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal) {
    nextTick(() => {
      inputRef.value?.focus()
      scrollToBottom()
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

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

function formatMessage(content: string): string {
  // Simple markdown-like formatting
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}

async function sendMessage() {
  if (!inputMessage.value.trim() || thinking.value) return
  
  const userMessage: Message = {
    role: 'user',
    content: inputMessage.value,
    timestamp: new Date()
  }
  
  messages.value.push(userMessage)
  const input = inputMessage.value
  inputMessage.value = ''
  thinking.value = true
  
  scrollToBottom()
  
  try {
    // Simulate AI response
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000))
    
    const aiResponse = await generateAIResponse(input)
    messages.value.push(aiResponse)
    
  } catch (error) {
    console.error('AI response error:', error)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，我遇到了一些问题。请稍后再试。',
      timestamp: new Date()
    })
  } finally {
    thinking.value = false
    scrollToBottom()
  }
}

async function generateAIResponse(input: string): Promise<Message> {
  // This is a simplified mock AI response
  // In a real implementation, this would call your AI service
  
  const responses = {
    '分析当前任务': {
      content: `根据当前的 ${taskStore.tasks.length} 个任务分析：

**任务概况：**
- 总任务数：${taskStore.tasks.length}
- 高优先级任务：${taskStore.tasks.filter(t => t.urgency === 1).length}个
- 已完成任务：${taskStore.tasks.filter(t => t.completed).length}个

**建议：**
1. 优先处理高优先级任务
2. 合理分配时间和资源
3. 定期回顾进度`,
      suggestions: [
        { label: '自动排列任务', action: 'auto-arrange' },
        { label: '生成详细报告', action: 'generate-report' }
      ]
    },
    '生成周报': {
      content: `**本周工作总结：**

📊 **任务完成情况：**
- 本周完成任务：${taskStore.tasks.filter(t => t.completed).length}个
- 进行中任务：${taskStore.tasks.filter(t => !t.completed).length}个

⭐ **重点成果：**
- 高优先级任务处理
- 工作流程优化

📈 **下周计划：**
- 继续推进重要项目
- 优化任务管理效率`,
      suggestions: [
        { label: '导出周报', action: 'export-report' },
        { label: '设置下周目标', action: 'set-goals' }
      ]
    }
  }
  
  // Simple keyword matching
  for (const [keyword, response] of Object.entries(responses)) {
    if (input.includes(keyword)) {
      return {
        role: 'assistant',
        content: response.content,
        timestamp: new Date(),
        suggestions: response.suggestions
      }
    }
  }
  
  // Default response
  return {
    role: 'assistant',
    content: `我理解你的问题："${input}"。让我为你提供一些建议：

1. 你可以尝试使用更具体的关键词
2. 我可以帮你分析任务、生成报告、优化流程
3. 有任何疑问都可以随时问我`,
    timestamp: new Date(),
    suggestions: [
      { label: '查看帮助', action: 'show-help' },
      { label: '任务分析', action: 'analyze-tasks' }
    ]
  }
}

function askForHelp(query: string) {
  inputMessage.value = query
  sendMessage()
}

function applySuggestion(suggestion: any) {
  emit('apply-suggestion', suggestion)
  
  // Add confirmation message
  messages.value.push({
    role: 'assistant',
    content: `已执行建议操作：${suggestion.label}`,
    timestamp: new Date()
  })
  
  scrollToBottom()
}

function clearChat() {
  messages.value = [
    {
      role: 'assistant',
      content: '对话已清空。有什么新的问题需要帮助吗？',
      timestamp: new Date()
    }
  ]
  scrollToBottom()
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
  padding-top: 5vh;
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
.command-palette.ai-assistant-dialog {
  width: 700px;
  max-width: 90vw;
  max-height: 85vh;
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

/* Chat Content */
.results-container {
  flex: 1;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%);
}

.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  flex-direction: column;
}

.message-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.message.user .message-wrapper {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  border: 2px solid rgba(102, 126, 234, 0.2);
}

.message.user .message-avatar {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%);
  border-color: rgba(34, 197, 94, 0.2);
}

.message-bubble {
  max-width: 70%;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.message.user .message-bubble {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border-color: rgba(102, 126, 234, 0.3);
}

.thinking-bubble {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(251, 191, 36, 0.1) 100%);
  border-color: rgba(245, 158, 11, 0.3);
}

.message-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.message-role {
  font-size: 13px;
  font-weight: 600;
  color: rgba(102, 126, 234, 0.8);
}

.message.user .message-role {
  color: rgba(34, 197, 94, 0.8);
}

.message-time {
  font-size: 11px;
  color: #64748b;
}

.message-content {
  font-size: 14px;
  line-height: 1.5;
  color: #374151;
}

.suggestions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(102, 126, 234, 0.1);
}

.suggestions-label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 8px;
}

.suggestion-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.suggestion-btn {
  padding: 6px 12px;
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 8px;
  color: rgba(102, 126, 234, 0.8);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.suggestion-btn:hover {
  background: rgba(102, 126, 234, 0.2);
  border-color: rgba(102, 126, 234, 0.3);
}

/* Typing Indicator */
.typing-indicator {
  display: inline-flex;
  gap: 3px;
  margin-right: 8px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(102, 126, 234, 0.6);
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

/* Quick Actions */
.quick-actions-section {
  padding: 16px 24px;
  border-top: 1px solid rgba(102, 126, 234, 0.1);
  background: rgba(248, 250, 252, 0.8);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 700;
  color: rgba(102, 126, 234, 0.8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 8px;
}

.quick-action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 13px;
}

.quick-action-btn:hover {
  background: rgba(102, 126, 234, 0.05);
  border-color: rgba(102, 126, 234, 0.3);
  transform: translateY(-1px);
}

.action-icon {
  font-size: 16px;
}

.action-label {
  font-weight: 500;
  color: #374151;
}

/* Input Section */
.chat-input-section {
  padding: 20px 24px;
  border-top: 2px solid rgba(102, 126, 234, 0.1);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%);
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.8);
  transition: all 0.3s ease;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  resize: vertical;
  min-height: 80px;
}

.chat-input:focus {
  outline: none;
  border-color: rgba(102, 126, 234, 0.5);
  background: rgba(255, 255, 255, 1);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.input-btn {
  padding: 10px 20px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.8);
  color: #374151;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.input-btn:hover {
  background: rgba(102, 126, 234, 0.05);
  border-color: rgba(102, 126, 234, 0.4);
}

.input-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-btn.primary {
  background: rgba(102, 126, 234, 0.8);
  color: white;
  border-color: rgba(102, 126, 234, 0.8);
}

.input-btn.primary:hover:not(:disabled) {
  background: rgba(102, 126, 234, 1);
  border-color: rgba(102, 126, 234, 1);
}

/* Scrollbar Styling */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: rgba(102, 126, 234, 0.05);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}

/* Responsive Design */
@media (max-width: 768px) {
  .command-palette.ai-assistant-dialog {
    width: 95vw;
    max-height: 90vh;
  }
  
  .message-bubble {
    max-width: 85%;
  }
  
  .quick-actions-grid {
    grid-template-columns: 1fr;
  }
  
  .input-actions {
    flex-direction: column;
  }
}
</style>