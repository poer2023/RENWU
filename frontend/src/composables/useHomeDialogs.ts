import { ref } from 'vue'

export interface DialogState {
  showQuickAdd: boolean
  showNewModule: boolean
  showSettings: boolean
  showBackupDialog: boolean
  showAutoArrangeDialog: boolean
  showSimilarTasksDialog: boolean
  showCommandPalette: boolean
  showAIAssistantDialog: boolean
  showAIParseDialog: boolean
  showWorkloadDialog: boolean
  showQuickTextDialog: boolean
  showExportDialog: boolean
}

export function useHomeDialogs() {
  // Dialog visibility states
  const showQuickAdd = ref(false)
  const showNewModule = ref(false)
  const showSettings = ref(false)
  const showBackupDialog = ref(false)
  const showAutoArrangeDialog = ref(false)
  const showSimilarTasksDialog = ref(false)
  const showCommandPalette = ref(false)
  const showAIAssistantDialog = ref(false)
  const showAIParseDialog = ref(false)
  const showWorkloadDialog = ref(false)
  const showQuickTextDialog = ref(false)
  const showExportDialog = ref(false)
  
  // Dialog data states
  const similarTasksData = ref<any>(null)
  const pendingTask = ref<Partial<any> | null>(null)
  const workloadAnalysis = ref<any>(null)
  
  // AI Assistant states
  const aiAssistantAction = ref('')
  const aiAssistantContent = ref('')
  const aiAssistantContext = ref('')
  const aiAssistantResult = ref('')
  
  // Export states
  const exportFormat = ref('json')
  const exportFilterModule = ref<number | null>(null)
  const exportFilterPriority = ref<number | null>(null)
  const exportOptions = ref({
    includeHistory: true,
    includeDependencies: true,
    includeModules: true
  })
  
  // Quick text input
  const quickTextInput = ref('')
  
  // Methods to open/close dialogs
  const openDialog = (dialogName: keyof DialogState) => {
    const dialogRefs = {
      showQuickAdd,
      showNewModule,
      showSettings,
      showBackupDialog,
      showAutoArrangeDialog,
      showSimilarTasksDialog,
      showCommandPalette,
      showAIAssistantDialog,
      showAIParseDialog,
      showWorkloadDialog,
      showQuickTextDialog,
      showExportDialog
    }
    
    if (dialogRefs[dialogName]) {
      dialogRefs[dialogName].value = true
    }
  }
  
  const closeDialog = (dialogName: keyof DialogState) => {
    const dialogRefs = {
      showQuickAdd,
      showNewModule,
      showSettings,
      showBackupDialog,
      showAutoArrangeDialog,
      showSimilarTasksDialog,
      showCommandPalette,
      showAIAssistantDialog,
      showAIParseDialog,
      showWorkloadDialog,
      showQuickTextDialog,
      showExportDialog
    }
    
    if (dialogRefs[dialogName]) {
      dialogRefs[dialogName].value = false
    }
  }
  
  const closeAllDialogs = () => {
    showQuickAdd.value = false
    showNewModule.value = false
    showSettings.value = false
    showBackupDialog.value = false
    showAutoArrangeDialog.value = false
    showSimilarTasksDialog.value = false
    showCommandPalette.value = false
    showAIAssistantDialog.value = false
    showAIParseDialog.value = false
    showWorkloadDialog.value = false
    showQuickTextDialog.value = false
    showExportDialog.value = false
  }
  
  return {
    // Dialog visibility refs
    showQuickAdd,
    showNewModule,
    showSettings,
    showBackupDialog,
    showAutoArrangeDialog,
    showSimilarTasksDialog,
    showCommandPalette,
    showAIAssistantDialog,
    showAIParseDialog,
    showWorkloadDialog,
    showQuickTextDialog,
    showExportDialog,
    
    // Dialog data refs
    similarTasksData,
    pendingTask,
    workloadAnalysis,
    
    // AI Assistant refs
    aiAssistantAction,
    aiAssistantContent,
    aiAssistantContext,
    aiAssistantResult,
    
    // Export refs
    exportFormat,
    exportFilterModule,
    exportFilterPriority,
    exportOptions,
    
    // Quick text
    quickTextInput,
    
    // Methods
    openDialog,
    closeDialog,
    closeAllDialogs
  }
} 