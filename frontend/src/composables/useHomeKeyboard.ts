import { Ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useTaskStore } from '@/stores/tasks'

interface KeyboardOptions {
  showCommandPalette: Ref<boolean>
  showQuickAdd: Ref<boolean>
  currentView: Ref<string>
  fabExpanded: Ref<boolean>
  showAlignOptions: Ref<boolean>
  selectedTask: Ref<any>
  stickyCanvasRef: Ref<any>
  insightDrawerOpen: Ref<boolean>
  onDeleteTask: () => void
  onUndoDelete: () => void
}

export function useHomeKeyboard(options: KeyboardOptions) {
  const taskStore = useTaskStore()
  
  const handleKeyDown = (e: KeyboardEvent) => {
    const target = e.target as HTMLElement
    const isInputElement = target.tagName === 'INPUT' || 
                          target.tagName === 'TEXTAREA' || 
                          target.contentEditable === 'true'
    
    // Command Palette - Ctrl/Cmd + K
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      options.showCommandPalette.value = true
      return
    }
    
    // Quick Add - Q
    if ((e.key === 'q' || e.key === 'Q') && !isInputElement) {
      e.preventDefault()
      options.showQuickAdd.value = true
      return
    }
    
    // Focus on latest task - Space
    if ((e.key === ' ' || e.key === 'Space') && !isInputElement) {
      e.preventDefault()
      if (options.stickyCanvasRef.value) {
        options.stickyCanvasRef.value.focusOnLatestTask()
        ElMessage.success('已定位到最新任务')
      }
      return
    }
    
    // Toggle Insight Drawer - Ctrl/Cmd + I
    if ((e.metaKey || e.ctrlKey) && e.key === 'i') {
      e.preventDefault()
      options.insightDrawerOpen.value = !options.insightDrawerOpen.value
      return
    }
    
    // View Switching - Ctrl/Cmd + 1/2/3
    if ((e.metaKey || e.ctrlKey) && ['1', '2', '3'].includes(e.key)) {
      e.preventDefault()
      const views = ['canvas', 'timeline', 'island']
      options.currentView.value = views[parseInt(e.key) - 1]
      return
    }
    
    // Quick Delete - Shift + Delete
    if (e.shiftKey && e.key === 'Delete' && options.selectedTask.value && !isInputElement) {
      e.preventDefault()
      options.onDeleteTask()
      return
    }
    
    // Undo - Ctrl/Cmd + Z
    if ((e.metaKey || e.ctrlKey) && e.key === 'z' && taskStore.canUndo() && !isInputElement) {
      e.preventDefault()
      options.onUndoDelete()
      return
    }
    
    // ESC to close things
    if (e.key === 'Escape') {
      options.fabExpanded.value = false
      options.showAlignOptions.value = false
      options.showCommandPalette.value = false
      return
    }
  }
  
  onMounted(() => {
    document.addEventListener('keydown', handleKeyDown)
  })
  
  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown)
  })
  
  return {
    // 可以返回一些方法供外部使用
  }
} 