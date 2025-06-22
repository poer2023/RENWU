import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTaskStore, type Task } from '@/stores/tasks'

export function useTaskOperations() {
  const taskStore = useTaskStore()
  const pendingTask = ref<Partial<Task> | null>(null)
  const similarTasksData = ref<any>(null)

  // Task creation and management
  async function generateSubtasks(task: Task, count: number = 5) {
    try {
      const subtasks = await taskStore.generateTaskSubtasks(
        task.title,
        task.description,
        count
      )
      
      const createdSubtasks = []
      
      // Create all subtasks first
      for (const subtask of subtasks) {
        const createdTask = await taskStore.createTask({
          ...subtask,
          parent_id: task.id,
          module_id: task.module_id
        })
        createdSubtasks.push(createdTask)
      }
      
      // Create dependencies: parent -> first subtask, and chain subtasks
      if (createdSubtasks.length > 0) {
        // Parent depends on first subtask
        await taskStore.createDependency({
          from_task_id: task.id,
          to_task_id: createdSubtasks[0].id,
          dependency_type: 'subtask'
        })
        
        // Chain subtasks (each depends on the previous one)
        for (let i = 1; i < createdSubtasks.length; i++) {
          await taskStore.createDependency({
            from_task_id: createdSubtasks[i - 1].id,
            to_task_id: createdSubtasks[i].id,
            dependency_type: 'subtask'
          })
        }
      }
      
      await taskStore.fetchTasks()
      await taskStore.fetchDependencies()
      
      ElMessage.success(`已为 "${task.title}" 生成 ${subtasks.length} 个子任务并建立依赖关系`)
    } catch (error) {
      console.error('Failed to generate subtasks:', error)
      ElMessage.error('生成子任务失败')
    }
  }

  async function deleteTask(taskId: number) {
    try {
      await ElMessageBox.confirm(
        '确定要删除这个任务吗？',
        '删除任务',
        {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
      
      await taskStore.deleteTask(taskId)
      ElMessage.success('任务已删除')
      return true
    } catch (error) {
      if (error !== 'cancel') {
        console.error('Failed to delete task:', error)
        ElMessage.error('删除任务失败')
      }
      return false
    }
  }

  async function quickDeleteTask(taskId: number) {
    try {
      console.log('Quick deleting task:', taskId)
      await taskStore.deleteTask(taskId)
      showUndoDeleteMessage()
      return true
    } catch (error) {
      console.error('Failed to delete task:', error)
      ElMessage.error('删除任务失败')
      return false
    }
  }

  function showUndoDeleteMessage() {
    ElMessage({
      type: 'success',
      duration: 5000,
      showClose: true,
      dangerouslyUseHTMLString: true,
      message: `
        <div style="display: flex; align-items: center; justify-content: space-between; width: 200px;">
          <span>任务已删除</span>
          <button 
            onclick="window.handleUndoDelete()"
            style="margin-left: 12px; padding: 4px 8px; background: #409EFF; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;"
          >
            撤回 (Ctrl+Z)
          </button>
        </div>
      `
    })
  }

  async function undoDelete() {
    try {
      const recreatedTask = await taskStore.undoDeleteTask()
      ElMessage.success(`任务 "${recreatedTask.title}" 已恢复`)
      return recreatedTask
    } catch (error) {
      console.error('Failed to undo delete:', error)
      ElMessage.error('撤回失败')
      return null
    }
  }

  // Text parsing
  async function parseTasksFromText(text: string) {
    try {
      const parsedTasks = await taskStore.parseTasksFromText(text)
      ElMessage.success(`已解析 ${parsedTasks.length} 个任务`)
      return parsedTasks
    } catch (error) {
      ElMessage.error('文本解析失败')
      throw error
    }
  }

  // Image upload and OCR
  async function handleImageUpload(file: File) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('/api/ocr', {
        method: 'POST',
        body: formData
      })
      
      const result = await response.json()
      
      if (result.success) {
        const extractedText = result.text
        const parsedTasks = await parseTasksFromText(extractedText)
        return parsedTasks
      } else {
        throw new Error(result.error || 'OCR处理失败')
      }
    } catch (error) {
      console.error('Image upload failed:', error)
      ElMessage.error('图片处理失败')
      throw error
    }
  }

  // Task similarity detection
  async function checkSimilarTasks(newTask: Partial<Task>) {
    try {
      const response = await fetch('/api/ai/similar-tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: newTask.title,
          description: newTask.description
        })
      })
      
      const result = await response.json()
      
      if (result.success && result.similar_tasks.length > 0) {
        similarTasksData.value = result
        pendingTask.value = newTask
        return true // Has similar tasks
      }
      
      return false // No similar tasks
    } catch (error) {
      console.error('Similar tasks check failed:', error)
      return false
    }
  }

  // Expose global undo function
  if (typeof window !== 'undefined') {
    (window as any).handleUndoDelete = undoDelete
  }

  return {
    // State
    pendingTask,
    similarTasksData,
    
    // Methods
    generateSubtasks,
    deleteTask,
    quickDeleteTask,
    undoDelete,
    parseTasksFromText,
    handleImageUpload,
    checkSimilarTasks
  }
} 