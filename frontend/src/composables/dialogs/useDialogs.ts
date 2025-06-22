import { ref, reactive } from 'vue'

// Dialog visibility states
export function useDialogs() {
  // Basic dialogs
  const quickAddDialogVisible = ref(false)
  const newModuleDialogVisible = ref(false)
  const autoArrangeDialogVisible = ref(false)
  const backupDialogVisible = ref(false)
  const exportDialogVisible = ref(false)
  
  // Advanced dialogs
  const settingsDialogVisible = ref(false)
  const workloadDialogVisible = ref(false)
  const aiParseDialogVisible = ref(false)
  const aiAssistantDialogVisible = ref(false)
  
  // Dialog data/props
  const dialogProps = reactive({
    quickAdd: {
      moduleId: null as string | null
    },
    autoArrange: {
      selectedModuleId: null as string | null,
      arrangeOptions: {
        spacing: 200,
        algorithm: 'force' as 'grid' | 'force' | 'hierarchical',
        groupByModule: true,
        animationDuration: 500
      }
    },
    backup: {
      backups: [] as any[],
      loading: false
    },
    export: {
      exportOptions: {
        format: 'json' as 'json' | 'csv' | 'markdown',
        includeCompleted: true,
        includeArchived: false,
        includeDependencies: true,
        includeHistory: false,
        dateRange: null as [Date, Date] | null,
        selectedModules: [] as string[]
      }
    },
    settings: {
      aiFeatures: {
        textParsing: true,
        subtaskGeneration: true,
        similarityDetection: true,
        weeklyReports: true,
        riskAnalysis: true,
        themeIslands: true
      },
      exportOptions: {
        includeHistory: true,
        includeDependencies: true,
        includeModules: true
      },
      advancedSettings: {
        enableAnimations: true,
        enableAutoLayout: true,
        enableKeyboardShortcuts: true,
        showDebugInfo: false,
        enableConsoleLogging: false,
        enableBetaFeatures: false
      }
    },
    workload: {
      userId: null as string | null
    },
    aiAssistant: {
      context: null as any
    }
  })
  
  // Dialog control functions
  const showQuickAddDialog = (moduleId?: string) => {
    dialogProps.quickAdd.moduleId = moduleId || null
    quickAddDialogVisible.value = true
  }
  
  const showNewModuleDialog = () => {
    newModuleDialogVisible.value = true
  }
  
  const showAutoArrangeDialog = (moduleId?: string) => {
    dialogProps.autoArrange.selectedModuleId = moduleId || null
    autoArrangeDialogVisible.value = true
  }
  
  const showBackupDialog = () => {
    backupDialogVisible.value = true
  }
  
  const showExportDialog = () => {
    exportDialogVisible.value = true
  }
  
  const showSettingsDialog = () => {
    settingsDialogVisible.value = true
  }
  
  const showWorkloadDialog = (userId?: string) => {
    dialogProps.workload.userId = userId || null
    workloadDialogVisible.value = true
  }
  
  const showAIParseDialog = () => {
    aiParseDialogVisible.value = true
  }
  
  const showAIAssistantDialog = (context?: any) => {
    dialogProps.aiAssistant.context = context || null
    aiAssistantDialogVisible.value = true
  }
  
  // Close all dialogs
  const closeAllDialogs = () => {
    quickAddDialogVisible.value = false
    newModuleDialogVisible.value = false
    autoArrangeDialogVisible.value = false
    backupDialogVisible.value = false
    exportDialogVisible.value = false
    settingsDialogVisible.value = false
    workloadDialogVisible.value = false
    aiParseDialogVisible.value = false
    aiAssistantDialogVisible.value = false
  }
  
  return {
    // Visibility states
    quickAddDialogVisible,
    newModuleDialogVisible,
    autoArrangeDialogVisible,
    backupDialogVisible,
    exportDialogVisible,
    settingsDialogVisible,
    workloadDialogVisible,
    aiParseDialogVisible,
    aiAssistantDialogVisible,
    
    // Dialog props
    dialogProps,
    
    // Control functions
    showQuickAddDialog,
    showNewModuleDialog,
    showAutoArrangeDialog,
    showBackupDialog,
    showExportDialog,
    showSettingsDialog,
    showWorkloadDialog,
    showAIParseDialog,
    showAIAssistantDialog,
    closeAllDialogs
  }
} 