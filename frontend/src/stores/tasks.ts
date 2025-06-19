import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export interface Task {
  id: number
  title: string
  description: string
  urgency: number
  module_id?: number
  parent_id?: number
  created_at: string
  updated_at: string
  ocr_src?: string
}

export interface Module {
  id: number
  name: string
  color: string
}

export interface History {
  id: number
  task_id: number
  field: string
  old_val: string
  new_val: string
  ts: string
}

export interface TaskDependency {
  id: number
  from_task_id: number
  to_task_id: number
  created_at: string
}

const API_BASE = '/api'

export const useTaskStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const modules = ref<Module[]>([])
  const dependencies = ref<TaskDependency[]>([])
  const selectedTask = ref<Task | null>(null)
  const taskHistory = ref<History[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed properties
  const tasksByModule = computed(() => {
    const grouped: Record<number, Task[]> = {}
    tasks.value.forEach(task => {
      const moduleId = task.module_id || 0
      if (!grouped[moduleId]) {
        grouped[moduleId] = []
      }
      grouped[moduleId].push(task)
    })
    return grouped
  })

  const rootTasks = computed(() => {
    return tasks.value.filter(task => !task.parent_id)
  })

  // Actions
  async function fetchTasks() {
    loading.value = true
    try {
      console.log('Fetching tasks from:', `${API_BASE}/tasks/`)
      const response = await axios.get<Task[]>(`${API_BASE}/tasks/`)
      console.log('Tasks fetched successfully:', response.data)
      console.log('Number of tasks:', response.data.length)
      
      tasks.value = response.data
      error.value = null
    } catch (err: any) {
      error.value = 'Failed to fetch tasks'
      console.error('Error fetching tasks:', err)
      console.error('Error response:', err.response?.data)
      console.error('Error status:', err.response?.status)
      console.error('Error config:', err.config?.url)
    } finally {
      loading.value = false
    }
  }

  async function fetchModules() {
    try {
      const response = await axios.get<Module[]>(`${API_BASE}/modules/`)
      modules.value = response.data
    } catch (err) {
      console.error('Error fetching modules:', err)
    }
  }

  async function createTask(taskData: Partial<Task>) {
    loading.value = true
    try {
      console.log('Creating task:', taskData)
      const response = await axios.post<Task>(`${API_BASE}/tasks/`, taskData)
      console.log('Task created successfully:', response.data)
      
      // Add the new task to the local tasks array
      tasks.value.push(response.data)
      
      // Force refresh tasks from server to ensure consistency
      await fetchTasks()
      
      error.value = null
      return response.data
    } catch (err: any) {
      error.value = 'Failed to create task'
      console.error('Error creating task:', err)
      console.error('Error response:', err.response?.data)
      console.error('Error status:', err.response?.status)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateTask(taskId: number, updates: Partial<Task>) {
    loading.value = true
    try {
      const response = await axios.patch<Task>(`${API_BASE}/tasks/${taskId}`, updates)
      const index = tasks.value.findIndex(t => t.id === taskId)
      if (index !== -1) {
        tasks.value[index] = response.data
      }
      if (selectedTask.value?.id === taskId) {
        selectedTask.value = response.data
      }
      error.value = null
      return response.data
    } catch (err) {
      error.value = 'Failed to update task'
      console.error('Error updating task:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteTask(taskId: number) {
    loading.value = true
    try {
      await axios.delete(`${API_BASE}/tasks/${taskId}`)
      tasks.value = tasks.value.filter(t => t.id !== taskId)
      if (selectedTask.value?.id === taskId) {
        selectedTask.value = null
      }
      error.value = null
    } catch (err) {
      error.value = 'Failed to delete task'
      console.error('Error deleting task:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createModule(moduleData: Partial<Module>) {
    try {
      const response = await axios.post<Module>(`${API_BASE}/modules/`, moduleData)
      modules.value.push(response.data)
      return response.data
    } catch (err) {
      console.error('Error creating module:', err)
      throw err
    }
  }

  async function fetchTaskHistory(taskId: number) {
    try {
      const response = await axios.get<History[]>(`${API_BASE}/tasks/${taskId}/history`)
      taskHistory.value = response.data
    } catch (err) {
      console.error('Error fetching task history:', err)
    }
  }

  async function parseTasksFromText(prompt: string) {
    loading.value = true
    try {
      const response = await axios.post(`${API_BASE}/ai/parse`, { prompt })
      return response.data.tasks
    } catch (err) {
      error.value = 'Failed to parse tasks'
      console.error('Error parsing tasks:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function extractTextFromImage(file: File) {
    loading.value = true
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await axios.post(`${API_BASE}/ocr/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data.text
    } catch (err) {
      error.value = 'Failed to extract text from image'
      console.error('Error extracting text:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function executeAIAssistant(command: string, content: string, context?: string) {
    loading.value = true
    try {
      const response = await axios.post(`${API_BASE}/ai/assistant`, {
        command,
        content,
        context
      })
      return response.data.result
    } catch (err) {
      error.value = 'AI assistant failed'
      console.error('Error with AI assistant:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function generateTaskSubtasks(parentTitle: string, parentDescription: string, maxSubtasks: number = 5) {
    loading.value = true
    try {
      const response = await axios.post(`${API_BASE}/ai/subtasks`, {
        parent_task_title: parentTitle,
        parent_task_description: parentDescription,
        max_subtasks: maxSubtasks
      })
      return response.data.subtasks
    } catch (err) {
      error.value = 'Subtask generation failed'
      console.error('Error generating subtasks:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function selectTask(task: Task | null) {
    selectedTask.value = task
    if (task) {
      fetchTaskHistory(task.id)
    } else {
      taskHistory.value = []
    }
  }

  function getModuleName(moduleId?: number) {
    if (!moduleId) return 'General'
    const module = modules.value.find(m => m.id === moduleId)
    return module?.name || 'Unknown'
  }

  function getModuleColor(moduleId?: number) {
    if (!moduleId) return '#FFE58F'
    const module = modules.value.find(m => m.id === moduleId)
    return module?.color || '#FFE58F'
  }

  // Dependency management functions
  async function fetchDependencies() {
    try {
      const response = await axios.get<TaskDependency[]>(`${API_BASE}/dependencies/`)
      dependencies.value = response.data
      error.value = null
    } catch (err) {
      error.value = 'Failed to fetch dependencies'
      console.error('Error fetching dependencies:', err)
      throw err
    }
  }

  async function createDependency(fromTaskId: number, toTaskId: number) {
    try {
      const response = await axios.post<TaskDependency>(`${API_BASE}/dependencies/`, {
        from_task_id: fromTaskId,
        to_task_id: toTaskId
      })
      dependencies.value.push(response.data)
      error.value = null
      return response.data
    } catch (err) {
      error.value = 'Failed to create dependency'
      console.error('Error creating dependency:', err)
      throw err
    }
  }

  async function deleteDependency(fromTaskId: number, toTaskId: number) {
    try {
      await axios.delete(`${API_BASE}/dependencies/${fromTaskId}/${toTaskId}`)
      dependencies.value = dependencies.value.filter(
        d => !(d.from_task_id === fromTaskId && d.to_task_id === toTaskId)
      )
      error.value = null
    } catch (err) {
      error.value = 'Failed to delete dependency'
      console.error('Error deleting dependency:', err)
      throw err
    }
  }

  function getTaskDependencies(taskId: number) {
    return {
      incoming: dependencies.value.filter(d => d.to_task_id === taskId),
      outgoing: dependencies.value.filter(d => d.from_task_id === taskId)
    }
  }

  return {
    // State
    tasks,
    modules,
    dependencies,
    selectedTask,
    taskHistory,
    loading,
    error,
    
    // Computed
    tasksByModule,
    rootTasks,
    
    // Actions
    fetchTasks,
    fetchModules,
    createTask,
    updateTask,
    deleteTask,
    createModule,
    fetchTaskHistory,
    parseTasksFromText,
    extractTextFromImage,
    selectTask,
    getModuleName,
    getModuleColor,
    
    // Dependency actions
    fetchDependencies,
    createDependency,
    deleteDependency,
    getTaskDependencies,
    
    // AI actions
    executeAIAssistant,
    generateTaskSubtasks
  }
})