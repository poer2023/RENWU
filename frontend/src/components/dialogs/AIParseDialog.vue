<template>
  <el-dialog
    v-model="visible"
    title="AI智能解析"
    width="60%"
    @close="handleClose"
  >
    <div class="ai-parse-container">
      <el-form label-position="top">
        <el-form-item label="输入文本内容">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="10"
            placeholder="粘贴或输入文本内容，AI将自动解析并创建任务..."
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="parseText" :loading="parsing">
            <el-icon v-if="!parsing">
              <MagicStick />
            </el-icon>
            {{ parsing ? '解析中...' : '开始解析' }}
          </el-button>
          <el-button @click="clearText" :disabled="parsing">清空</el-button>
        </el-form-item>
      </el-form>
      
      <div v-if="parsedTasks.length > 0" class="parsed-results">
        <el-divider />
        <h3>解析结果</h3>
        <div class="task-preview-list">
          <div v-for="(task, index) in parsedTasks" :key="index" class="task-preview">
            <el-card>
              <div class="task-header">
                <el-checkbox v-model="task.selected" />
                <h4>{{ task.title }}</h4>
              </div>
              <div class="task-details">
                <el-tag v-if="task.priority" :type="getPriorityType(task.priority)" size="small">
                  {{ getPriorityLabel(task.priority) }}
                </el-tag>
                <el-tag v-if="task.module" type="info" size="small">
                  {{ task.module }}
                </el-tag>
                <span v-if="task.dueDate" class="due-date">
                  <el-icon><Calendar /></el-icon>
                  {{ formatDate(task.dueDate) }}
                </span>
              </div>
              <p v-if="task.description" class="task-description">{{ task.description }}</p>
              <div v-if="task.subtasks && task.subtasks.length > 0" class="subtasks">
                <h5>子任务：</h5>
                <ul>
                  <li v-for="(subtask, subIndex) in task.subtasks" :key="subIndex">
                    {{ subtask }}
                  </li>
                </ul>
              </div>
            </el-card>
          </div>
        </div>
      </div>
      
      <div v-if="parseError" class="parse-error">
        <el-alert
          title="解析失败"
          :description="parseError"
          type="error"
          show-icon
          closable
          @close="parseError = ''"
        />
      </div>
    </div>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button 
        type="primary" 
        @click="createSelectedTasks" 
        :disabled="!hasSelectedTasks"
      >
        创建选中的任务 ({{ selectedTaskCount }})
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElDialog, ElForm, ElFormItem, ElInput, ElButton, ElIcon, ElDivider, ElCard, ElCheckbox, ElTag, ElAlert, ElMessage } from 'element-plus'
import { MagicStick, Calendar } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/tasks'

interface Props {
  modelValue: boolean
}

interface ParsedTask {
  title: string
  description?: string
  priority?: number
  module?: string
  dueDate?: string
  subtasks?: string[]
  selected: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'tasks-created': [tasks: ParsedTask[]]
}>()

const taskStore = useTaskStore()

const visible = ref(props.modelValue)
const inputText = ref('')
const parsing = ref(false)
const parsedTasks = ref<ParsedTask[]>([])
const parseError = ref('')

// Watch for external visibility changes
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

// Watch for internal visibility changes
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

const hasSelectedTasks = computed(() => {
  return parsedTasks.value.some(task => task.selected)
})

const selectedTaskCount = computed(() => {
  return parsedTasks.value.filter(task => task.selected).length
})

async function parseText() {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入要解析的文本')
    return
  }
  
  parsing.value = true
  parseError.value = ''
  
  try {
    const response = await fetch('/api/ai/v3/parse', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: inputText.value
      })
    })
    
    if (!response.ok) {
      throw new Error('解析请求失败')
    }
    
    const result = await response.json()
    
    if (result.tasks && result.tasks.length > 0) {
      parsedTasks.value = result.tasks.map((task: any) => ({
        ...task,
        selected: true
      }))
      ElMessage.success(`成功解析出 ${result.tasks.length} 个任务`)
    } else {
      ElMessage.warning('未能从文本中解析出任务')
    }
  } catch (error) {
    console.error('Parse error:', error)
    parseError.value = error instanceof Error ? error.message : '解析失败，请重试'
    ElMessage.error('解析失败')
  } finally {
    parsing.value = false
  }
}

function clearText() {
  inputText.value = ''
  parsedTasks.value = []
  parseError.value = ''
}

async function createSelectedTasks() {
  const selectedTasks = parsedTasks.value.filter(task => task.selected)
  
  if (selectedTasks.length === 0) {
    ElMessage.warning('请至少选择一个任务')
    return
  }
  
  try {
    // Create tasks one by one
    for (const task of selectedTasks) {
      const newTask = {
        title: task.title,
        description: task.description || '',
        priority: task.priority || 3,
        status: 'pending',
        module_id: task.module ? await getOrCreateModule(task.module) : null,
        due_date: task.dueDate || null,
        position_x: Math.random() * 800 + 100,
        position_y: Math.random() * 600 + 100
      }
      
      const createdTask = await taskStore.createTask(newTask)
      
      // Create subtasks if any
      if (task.subtasks && task.subtasks.length > 0) {
        for (const subtaskTitle of task.subtasks) {
          await taskStore.createTask({
            title: subtaskTitle,
            description: '',
            priority: 3,
            status: 'pending',
            parent_id: createdTask.id,
            position_x: createdTask.position_x + Math.random() * 100 - 50,
            position_y: createdTask.position_y + Math.random() * 100 + 50
          })
        }
      }
    }
    
    ElMessage.success(`成功创建 ${selectedTasks.length} 个任务`)
    emit('tasks-created', selectedTasks)
    handleClose()
  } catch (error) {
    console.error('Error creating tasks:', error)
    ElMessage.error('创建任务失败')
  }
}

async function getOrCreateModule(moduleName: string): Promise<string | null> {
  // Check if module already exists
  const existingModule = taskStore.modules.find(m => m.name === moduleName)
  if (existingModule) {
    return existingModule.id
  }
  
  // Create new module
  try {
    const newModule = await taskStore.createModule({
      name: moduleName,
      color: getRandomColor()
    })
    return newModule.id
  } catch (error) {
    console.error('Error creating module:', error)
    return null
  }
}

function getRandomColor(): string {
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#B88230', '#5CB87A', '#6F7AD3']
  return colors[Math.floor(Math.random() * colors.length)]
}

function handleClose() {
  visible.value = false
  // Reset state
  inputText.value = ''
  parsedTasks.value = []
  parseError.value = ''
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

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.ai-parse-container {
  min-height: 400px;
}

.parsed-results {
  margin-top: 20px;
}

.task-preview-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
  padding: 4px;
}

.task-preview .el-card {
  cursor: pointer;
  transition: all 0.3s;
}

.task-preview .el-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.task-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.task-header h4 {
  margin: 0;
  flex: 1;
}

.task-details {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.due-date {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
  font-size: 14px;
}

.task-description {
  color: #666;
  margin: 8px 0;
  font-size: 14px;
  line-height: 1.5;
}

.subtasks {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.subtasks h5 {
  margin: 0 0 8px 0;
  color: #666;
  font-size: 14px;
}

.subtasks ul {
  margin: 0;
  padding-left: 20px;
}

.subtasks li {
  color: #666;
  font-size: 14px;
  line-height: 1.8;
}

.parse-error {
  margin-top: 20px;
}
</style> 