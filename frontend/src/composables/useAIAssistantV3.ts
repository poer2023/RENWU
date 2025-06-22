import { ref } from 'vue'
import axios from 'axios'

export interface AIParseResult {
  suggested_task: {
    title: string
    description?: string
    priority: number
    category?: string
    tags?: string[]
    deadline?: string
    estimated_hours?: number
    ai_generated?: boolean
    ai_confidence?: number
  }
  confidence: number
  reasoning: string[]
  ai_enhancements: any
  similar_tasks: Array<{
    task_id: number
    task_title: string
    similarity_score: number
    similarity_type: string
    reasoning: string[]
  }>
}

export interface AIAnalysisResult {
  classification_result?: {
    success: boolean
    data: {
      category: string
      subcategory?: string
      confidence: number
      alternatives: Array<{
        category: string
        confidence: number
      }>
    }
    confidence: number
  }
  similarity_result?: {
    success: boolean
    data: Array<{
      task_id: number
      task_title: string
      similarity_score: number
      similarity_type: string
    }>
    confidence: number
  }
  priority_result?: {
    success: boolean
    data: {
      priority_level: number
      priority_name: string
      confidence: number
      urgency_score: number
      importance_score: number
      factors: any
    }
    confidence: number
  }
  dependency_result?: any
  workload_result?: any
  overall_confidence: number
  processing_time: number
  recommendations: string[]
}

export interface AIBatchResult {
  results: Array<{
    suggested_task: any
    confidence: number
    reasoning: string[]
    ai_enhancements: any
    similar_tasks: any[]
  }>
}

export interface AIInsightsResult {
  insights: {
    workload?: {
      total_hours: number
      available_hours: number
      utilization_rate: number
      workload_level: string
      task_count: number
      high_priority_count: number
      overdue_count: number
      avg_task_complexity: number
      stress_indicators: string[]
      recommendations: string[]
    }
    priorities?: {
      priority_distribution: Record<number, number>
      total_tasks: number
      high_urgency_tasks: any[]
      high_importance_tasks: any[]
      overdue_tasks: any[]
      recommendations: string[]
    }
    potential_duplicates?: number
    vector_database?: {
      available: boolean
      total_vectors: number
      tasks_with_vectors: number
      vector_coverage: number
    }
    recommendations?: string[]
  }
  task_count: number
  recommendations: string[]
}

export const useAIAssistantV3 = () => {
  const loading = ref(false)
  const error = ref<string | null>(null)

  const parseNaturalLanguage = async (
    text: string,
    context: any = {},
    fullAnalysis: boolean = true
  ): Promise<AIParseResult> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/ai/v3/parse-task', {
        text,
        context,
        full_analysis: fullAnalysis
      })

      if (response.data.success) {
        return response.data
      } else {
        throw new Error(response.data.error || 'Task parsing failed')
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const analyzeTask = async (
    taskData: any,
    context: any = {}
  ): Promise<AIAnalysisResult> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/ai/v3/analyze-task', {
        task_data: taskData,
        context
      })

      if (response.data.success) {
        return response.data
      } else {
        throw new Error(response.data.error || 'Task analysis failed')
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const processBatch = async (
    taskInputs: string[],
    context: any = {}
  ): Promise<AIBatchResult> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/ai/v3/batch-process', {
        task_inputs: taskInputs,
        context
      })

      if (response.data.success) {
        return response.data
      } else {
        throw new Error(response.data.error || 'Batch processing failed')
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const optimizeTasks = async (
    tasks: any[],
    context: any = {}
  ): Promise<any> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/ai/v3/optimize-tasks', {
        tasks,
        context
      })

      if (response.data.success) {
        return response.data
      } else {
        throw new Error(response.data.error || 'Task optimization failed')
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const getInsights = async (
    userId: string = 'default',
    timeFrame: string = 'this_week'
  ): Promise<AIInsightsResult> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`/api/ai/v3/insights?user_id=${userId}&time_frame=${timeFrame}`)

      if (response.data.success) {
        return response.data
      } else {
        throw new Error(response.data.error || 'Insights retrieval failed')
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const getServiceStatus = async (): Promise<any> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get('/api/ai/v3/status')
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // Individual AI service methods
  const classifyTask = async (
    taskContent: string,
    userContext: any = {}
  ): Promise<any> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/ai/v3/classification/classify', {
        task_content: taskContent,
        user_context: userContext
      })
      return response.data.result
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const findSimilarTasks = async (
    taskContent: string,
    threshold: number = 0.7,
    maxResults: number = 5
  ): Promise<any> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/ai/v3/similarity/find', {
        task_content: taskContent,
        threshold,
        max_results: maxResults
      })
      return response.data.result
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const assessPriority = async (
    taskData: any,
    context: any = {}
  ): Promise<any> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/ai/v3/priority/assess', {
        task_data: taskData,
        context
      })
      return response.data.result
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const detectDependencies = async (
    tasks: any[],
    context: any = {}
  ): Promise<any> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/ai/v3/dependency/detect', {
        tasks,
        context
      })
      return response.data.result
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const analyzeWorkload = async (
    tasks: any[],
    timeFrame: string = 'this_week',
    context: any = {}
  ): Promise<any> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/ai/v3/workload/analyze', {
        tasks,
        time_frame: timeFrame,
        context
      })
      return response.data.result
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const getVectorDBStats = async (): Promise<any> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get('/api/ai/v3/vector-db/stats')
      return response.data.stats
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateAllVectors = async (force: boolean = false): Promise<any> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/ai/v3/vector-db/update-all', {
        force
      })
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const submitFeedback = async (
    operationType: string,
    inputData: any,
    aiResult: any,
    userCorrection?: any,
    feedbackType: string = 'accept'
  ): Promise<any> => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/ai/v3/feedback', {
        operation_type: operationType,
        input_data: inputData,
        ai_result: aiResult,
        user_correction: userCorrection,
        feedback_type: feedbackType
      })
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    parseNaturalLanguage,
    analyzeTask,
    processBatch,
    optimizeTasks,
    getInsights,
    getServiceStatus,
    // Individual services
    classifyTask,
    findSimilarTasks,
    assessPriority,
    detectDependencies,
    analyzeWorkload,
    // Vector DB management
    getVectorDBStats,
    updateAllVectors,
    // Feedback
    submitFeedback
  }
}