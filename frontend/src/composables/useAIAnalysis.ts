import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface WorkloadAnalysis {
  success: boolean
  total_hours: number
  workload_percentage: number
  tasks_count: number
  analysis_date: string
}

export function useAIAnalysis() {
  const workloadAnalysis = ref<WorkloadAnalysis | null>(null)
  const isAnalyzing = ref(false)

  // Risk analysis
  async function analyzeRisks() {
    try {
      isAnalyzing.value = true
      const response = await fetch('/api/ai/risk-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          // Use all tasks by default
        })
      })
      
      const result = await response.json()
      
      if (result.success) {
        // Show risk analysis results
        const riskMessage = `风险分析完成！\n\n高风险任务: ${result.risky_tasks.length} 个\n\n建议:\n${result.suggestions.join('\n')}`
        await ElMessageBox.alert(riskMessage, '风险分析结果', {
          confirmButtonText: '确定',
          type: 'warning'
        })
        return result
      } else {
        throw new Error(result.error || 'Risk analysis failed')
      }
    } catch (error) {
      console.error('Risk analysis failed:', error)
      ElMessage.error('风险分析失败')
      throw error
    } finally {
      isAnalyzing.value = false
    }
  }

  // Workload analysis
  async function refreshWorkloadAnalysis() {
    try {
      isAnalyzing.value = true
      const response = await fetch('/api/ai/v3/workload/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          date: new Date().toISOString().split('T')[0]
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      
      if (result.success) {
        // 验证数据结构并提供默认值
        workloadAnalysis.value = {
          success: true,
          total_hours: typeof result.total_hours === 'number' && isFinite(result.total_hours) ? result.total_hours : 0,
          workload_percentage: typeof result.workload_percentage === 'number' && isFinite(result.workload_percentage) ? result.workload_percentage : 0,
          tasks_count: result.tasks_count || 0,
          analysis_date: result.analysis_date || new Date().toISOString().split('T')[0]
        }
        return workloadAnalysis.value
      } else {
        throw new Error(result.error || 'Workload analysis failed')
      }
    } catch (error) {
      console.error('Workload analysis failed:', error)
      // 提供默认的工作负载数据，避免显示错误
      workloadAnalysis.value = {
        success: false,
        total_hours: 0,
        workload_percentage: 0,
        tasks_count: 0,
        analysis_date: new Date().toISOString().split('T')[0]
      }
      ElMessage.error('工作量分析失败，显示默认数据')
      return workloadAnalysis.value
    } finally {
      isAnalyzing.value = false
    }
  }

  // AI Assistant functions
  async function executeAIAssistant(action: string, content: string, context: string) {
    try {
      const response = await fetch('/api/ai/assistant', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action,
          content,
          context
        })
      })
      
      const result = await response.json()
      
      if (result.success) {
        ElMessage.success('AI功能执行成功！')
        return result.data
      } else {
        throw new Error(result.error || 'AI assistant failed')
      }
    } catch (error) {
      console.error('AI assistant failed:', error)
      ElMessage.error('AI功能执行失败')
      throw error
    }
  }

  // Workload level helpers
  function getWorkloadColor(percentage: number): string {
    const safePercentage = typeof percentage === 'number' && isFinite(percentage) ? percentage : 0
    if (safePercentage <= 70) return 'workload-green'
    if (safePercentage <= 90) return 'workload-yellow'
    return 'workload-red'
  }

  function getWorkloadMessage(level: string): string {
    switch (level) {
      case 'green': return '工作量正常，时间安排合理'
      case 'yellow': return '工作量较高，建议优化任务安排'
      case 'red': return '工作量过载，存在时间冲突风险'
      default: return '工作量分析'
    }
  }

  function getWorkloadAlertType(level: string): string {
    switch (level) {
      case 'green': return 'success'
      case 'yellow': return 'warning'
      case 'red': return 'error'
      default: return 'info'
    }
  }

  return {
    // State
    workloadAnalysis,
    isAnalyzing,
    
    // Methods
    analyzeRisks,
    refreshWorkloadAnalysis,
    executeAIAssistant,
    getWorkloadColor,
    getWorkloadMessage,
    getWorkloadAlertType
  }
} 