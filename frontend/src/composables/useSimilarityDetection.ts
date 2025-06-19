import { ref } from 'vue'
import axios from 'axios'

export interface SimilarTask {
  task: {
    id: number
    title: string
    description: string
    urgency: number
    module_id?: number
    created_at: string
    updated_at: string
  }
  similarity_score: number
  match_type: string
}

export interface SimilarityResult {
  similar_tasks: SimilarTask[]
  suggestions: string[]
  success: boolean
  error?: string
}

export const useSimilarityDetection = () => {
  const loading = ref(false)
  const error = ref<string | null>(null)

  const findSimilarTasks = async (
    title: string,
    description: string = '',
    threshold: number = 0.85
  ): Promise<SimilarityResult> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post<SimilarityResult>('/api/ai/similar-tasks', {
        task_title: title,
        task_description: description,
        similarity_threshold: threshold
      })

      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const getMatchTypeLabel = (matchType: string): string => {
    const labels: { [key: string]: string } = {
      exact_title: '标题完全匹配',
      near_duplicate: '几乎重复',
      very_similar: '高度相似',
      similar: '相似',
      related: '相关'
    }
    return labels[matchType] || matchType
  }

  const getMatchTypeColor = (matchType: string): string => {
    const colors: { [key: string]: string } = {
      exact_title: '#ff4d4f',
      near_duplicate: '#fa8c16', 
      very_similar: '#fadb14',
      similar: '#52c41a',
      related: '#1890ff'
    }
    return colors[matchType] || '#666'
  }

  const getSimilarityPercentage = (score: number): string => {
    return `${Math.round(score * 100)}%`
  }

  return {
    loading,
    error,
    findSimilarTasks,
    getMatchTypeLabel,
    getMatchTypeColor,
    getSimilarityPercentage
  }
}