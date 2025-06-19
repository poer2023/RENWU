import { ref } from 'vue'
import axios from 'axios'

export interface AIAssistantCommand {
  id: string
  label: string
  icon: string
  description: string
}

export const useAIAssistant = () => {
  const loading = ref(false)
  const error = ref<string | null>(null)

  const commands: AIAssistantCommand[] = [
    {
      id: 'rewrite',
      label: 'Rewrite',
      icon: '✏️',
      description: 'Rewrite text to be clearer and more concise'
    },
    {
      id: 'add-emoji',
      label: 'Add Emoji',
      icon: '😊',
      description: 'Add appropriate emojis to make text more engaging'
    },
    {
      id: 'summarize',
      label: 'Summarize',
      icon: '📝',
      description: 'Create a concise summary of the text'
    },
    {
      id: 'make-subtasks',
      label: 'Make Subtasks',
      icon: '📋',
      description: 'Break down into smaller, actionable subtasks'
    }
  ]

  const executeCommand = async (
    command: string,
    content: string,
    context?: string
  ): Promise<string> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/ai/assistant', {
        command,
        content,
        context
      })

      if (response.data.success) {
        return response.data.result
      } else {
        throw new Error(response.data.error || 'Command failed')
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const generateSubtasks = async (
    parentTitle: string,
    parentDescription: string,
    maxSubtasks: number = 5
  ): Promise<any[]> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/ai/subtasks', {
        parent_task_title: parentTitle,
        parent_task_description: parentDescription,
        max_subtasks: maxSubtasks
      })

      if (response.data.success) {
        return response.data.subtasks
      } else {
        throw new Error(response.data.error || 'Subtask generation failed')
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    commands,
    loading,
    error,
    executeCommand,
    generateSubtasks
  }
}