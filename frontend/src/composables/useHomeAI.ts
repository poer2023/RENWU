import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTaskStore } from '@/stores/tasks'

export function useHomeAI() {
  const taskStore = useTaskStore()
  
  // AI Parse functionality
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
  
  // AI Assistant functionality
  async function executeAIAssistant(action: string, content: string, context: string) {
    try {
      const result = await taskStore.executeAIAssistant(action, content, context)
      ElMessage.success('AI功能执行成功！')
      return result
    } catch (error) {
      console.error('AI assistant failed:', error)
      ElMessage.error('AI功能执行失败')
      throw error
    }
  }
  
  // Risk Analysis functionality
  async function analyzeRisks() {
    try {
      const response = await fetch('/api/ai/risk-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      })
      
      const result = await response.json()
      
      if (result.success) {
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
    }
  }
  
  // Workload Analysis functionality
  async function fetchWorkloadAnalysis(date?: string) {
    try {
      const response = await fetch('/api/ai/v3/workload/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          date: date || new Date().toISOString().split('T')[0]
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      
      if (result.success) {
        // 验证数据结构并提供默认值
        return {
          success: true,
          total_hours: typeof result.total_hours === 'number' && isFinite(result.total_hours) ? result.total_hours : 0,
          workload_percentage: typeof result.workload_percentage === 'number' && isFinite(result.workload_percentage) ? result.workload_percentage : 0,
          capacity_hours: result.capacity_hours || 8,
          tasks_count: result.tasks_count || 0,
          tasks: result.tasks || [],
          conflict_level: result.conflict_level || 'green',
          analysis_date: result.analysis_date || new Date().toISOString().split('T')[0]
        }
      } else {
        throw new Error(result.error || 'Workload analysis failed')
      }
    } catch (error) {
      console.error('Workload analysis failed:', error)
      // 提供默认的工作负载数据，避免显示错误
      return {
        success: false,
        total_hours: 0,
        workload_percentage: 0,
        capacity_hours: 8,
        tasks_count: 0,
        tasks: [],
        conflict_level: 'green',
        analysis_date: new Date().toISOString().split('T')[0]
      }
    }
  }
  
  // Generate Subtasks functionality
  async function generateSubtasksForTask(task: any, count: number = 5) {
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
      
      ElMessage.success(
        `已为 "${task.title}" 生成 ${subtasks.length} 个子任务并建立依赖关系`
      )
      
      return createdSubtasks
    } catch (error) {
      console.error('Failed to generate subtasks:', error)
      ElMessage.error('生成子任务失败')
      throw error
    }
  }
  
  // Theme Islands functionality
  async function enableThemeIslands() {
    try {
      const response = await fetch('/ai/theme-islands', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      const result = await response.json()
      
      if (result.success && result.islands) {
        ElMessage.success(`已生成 ${result.islands.length} 个主题岛`)
        return result.islands
      } else {
        throw new Error(result.error || 'Theme islands generation failed')
      }
    } catch (error) {
      console.error('Theme islands failed:', error)
      ElMessage.error('主题岛生成失败')
      throw error
    }
  }
  
  return {
    parseTasksFromText,
    executeAIAssistant,
    analyzeRisks,
    fetchWorkloadAnalysis,
    generateSubtasksForTask,
    enableThemeIslands
  }
} 