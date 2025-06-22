import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useTaskStore } from '@/stores/tasks'

export function useDataManagement() {
  const taskStore = useTaskStore()
  
  // Export state
  const exportFormat = ref('json')
  const exportFilterModule = ref<number | null>(null)
  const exportFilterPriority = ref<number | null>(null)
  const exportOptions = ref({
    includeHistory: true,
    includeDependencies: true,
    includeModules: true
  })

  // Backup state
  const isBackupInProgress = ref(false)

  // Export helpers
  const filteredTaskCount = computed(() => {
    let filteredTasks = taskStore.tasks
    
    if (exportFilterModule.value) {
      filteredTasks = filteredTasks.filter(task => task.module_id === exportFilterModule.value)
    }
    
    if (exportFilterPriority.value !== null) {
      filteredTasks = filteredTasks.filter(task => task.urgency === exportFilterPriority.value)
    }
    
    return filteredTasks.length
  })

  const estimatedFileSize = computed(() => {
    const taskCount = filteredTaskCount.value
    let estimatedSize = 0
    
    // Base task data size estimation
    estimatedSize += taskCount * 500 // ~500 bytes per task
    
    if (exportOptions.value.includeHistory) {
      estimatedSize += taskCount * 200 // ~200 bytes per history record
    }
    
    if (exportOptions.value.includeDependencies) {
      estimatedSize += taskStore.dependencies.length * 100 // ~100 bytes per dependency
    }
    
    if (exportOptions.value.includeModules) {
      estimatedSize += taskStore.modules.length * 150 // ~150 bytes per module
    }
    
    // Format size estimation based on export format
    switch (exportFormat.value) {
      case 'json':
        estimatedSize *= 1.2 // JSON formatting overhead
        break
      case 'markdown':
        estimatedSize *= 1.5 // Markdown formatting
        break
      case 'csv':
        estimatedSize *= 0.8 // CSV is more compact
        break
      case 'excel':
        estimatedSize *= 2.0 // Excel has more overhead
        break
      case 'pdf':
        estimatedSize *= 3.0 // PDF has significant overhead
        break
    }
    
    // Convert to human readable format
    if (estimatedSize < 1024) {
      return `${Math.round(estimatedSize)} B`
    } else if (estimatedSize < 1024 * 1024) {
      return `${Math.round(estimatedSize / 1024)} KB`
    } else {
      return `${Math.round(estimatedSize / (1024 * 1024))} MB`
    }
  })

  // Export functions
  async function exportData() {
    try {
      const exportData = {
        format: exportFormat.value,
        filters: {
          module_id: exportFilterModule.value,
          priority: exportFilterPriority.value
        },
        options: exportOptions.value,
        timestamp: new Date().toISOString()
      }

      const endpoint = exportFormat.value === 'markdown' ? '/api/export/markdown' : '/api/export/json'
      const response = await fetch(endpoint, {
        method: 'GET'
      })

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`)
      }

      // Handle file download
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `taskwall_export_${new Date().toISOString().split('T')[0]}.${exportFormat.value}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      ElMessage.success(`数据导出成功 (${exportFormat.value.toUpperCase()})`)
    } catch (error) {
      console.error('Export failed:', error)
      ElMessage.error('数据导出失败')
    }
  }

  // Backup functions
  async function createBackup() {
    try {
      isBackupInProgress.value = true
      const response = await fetch('/api/backup/create', { 
        method: 'POST'
      })
      
      if (response.ok) {
        const result = await response.json()
        ElMessage.success(`数据备份成功: ${result.filename}`)
        return result
      } else {
        throw new Error('备份失败')
      }
    } catch (error) {
      ElMessage.error('数据备份失败')
      console.error('Backup error:', error)
      throw error
    } finally {
      isBackupInProgress.value = false
    }
  }

  async function restoreFromBackup(backupFile: File) {
    try {
      // TODO: 后端暂无restore API，功能待实现
      ElMessage.warning('恢复功能暂未实现')
      throw new Error('恢复功能暂未实现')
    } catch (error) {
      ElMessage.error('数据恢复失败')
      console.error('Restore error:', error)
      throw error
    }
  }

  // Clear cache
  async function clearCache() {
    try {
      // 清理本地缓存
      if ('caches' in window) {
        const cacheNames = await caches.keys()
        await Promise.all(cacheNames.map(name => caches.delete(name)))
      }
      
      // 刷新数据
      await taskStore.fetchTasks()
      await taskStore.fetchModules() 
      await taskStore.fetchDependencies()
      
      ElMessage.success('缓存已清理')
    } catch (error) {
      ElMessage.error('清理缓存失败')
      console.error('Clear cache error:', error)
    }
  }

  // Data validation
  function validateExportSettings() {
    if (!exportFormat.value) {
      ElMessage.warning('请选择导出格式')
      return false
    }
    
    if (filteredTaskCount.value === 0) {
      ElMessage.warning('没有找到符合条件的任务')
      return false
    }
    
    return true
  }

  // Format helpers
  function getPriorityName(urgency: number): string {
    const names = {
      0: '紧急',
      1: '高',
      2: '中',
      3: '低',
      4: '待办'
    }
    return names[urgency as keyof typeof names] || '中'
  }

  function formatFullDate(date: string): string {
    return new Date(date).toLocaleString('zh-CN')
  }

  return {
    // State
    exportFormat,
    exportFilterModule,
    exportFilterPriority,
    exportOptions,
    isBackupInProgress,
    
    // Computed
    filteredTaskCount,
    estimatedFileSize,
    
    // Methods
    exportData,
    createBackup,
    restoreFromBackup,
    clearCache,
    validateExportSettings,
    getPriorityName,
    formatFullDate
  }
} 