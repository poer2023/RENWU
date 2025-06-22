import { onMounted, onUnmounted } from 'vue'

interface KeyboardActions {
  openCommandPalette?: () => void
  openQuickAdd?: () => void
  focusOnLatestTask?: () => void
  toggleInsightDrawer?: () => void
  switchToCanvasView?: () => void
  switchToTimelineView?: () => void
  switchToIslandView?: () => void
  quickDeleteTask?: () => void
  undoDelete?: () => void
  closeFab?: () => void
  closeCommandPalette?: () => void
  closeAlignOptions?: () => void
}

export function useKeyboardShortcuts(actions: KeyboardActions) {
  function handleKeyDown(e: KeyboardEvent) {
    // Command Palette - Ctrl/Cmd + K
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      actions.openCommandPalette?.()
      return
    }
    
    // Quick Add - Q key (when not in input)
    if (e.key === 'q' || e.key === 'Q') {
      if (!isInInputElement(e.target as HTMLElement)) {
        e.preventDefault()
        actions.openQuickAdd?.()
        return
      }
    }
    
    // Focus on latest task - Space key (when not in input)
    if (e.key === ' ' || e.key === 'Space') {
      if (!isInInputElement(e.target as HTMLElement)) {
        e.preventDefault()
        actions.focusOnLatestTask?.()
        return
      }
    }
    
    // Toggle Insight Drawer - Ctrl/Cmd + I
    if ((e.metaKey || e.ctrlKey) && e.key === 'i') {
      e.preventDefault()
      actions.toggleInsightDrawer?.()
      return
    }
    
    // View Switching - Ctrl/Cmd + 1/2/3
    if ((e.metaKey || e.ctrlKey) && ['1', '2', '3'].includes(e.key)) {
      e.preventDefault()
      const viewActions = [
        actions.switchToCanvasView,
        actions.switchToTimelineView,
        actions.switchToIslandView
      ]
      const actionIndex = parseInt(e.key) - 1
      viewActions[actionIndex]?.()
      return
    }
    
    // Quick Delete - Shift + Delete (when not in input)
    if (e.shiftKey && e.key === 'Delete') {
      if (!isInInputElement(e.target as HTMLElement)) {
        e.preventDefault()
        actions.quickDeleteTask?.()
        return
      }
    }
    
    // Undo Delete - Ctrl/Cmd + Z (when not in input)
    if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
      if (!isInInputElement(e.target as HTMLElement)) {
        e.preventDefault()
        actions.undoDelete?.()
        return
      }
    }
    
    // ESC to close things
    if (e.key === 'Escape') {
      actions.closeFab?.()
      actions.closeCommandPalette?.()
      actions.closeAlignOptions?.()
      return
    }
  }
  
  function isInInputElement(target: HTMLElement | null): boolean {
    if (!target) return false
    
    const tagName = target.tagName.toUpperCase()
    const isContentEditable = target.contentEditable === 'true'
    
    return (
      tagName === 'INPUT' ||
      tagName === 'TEXTAREA' ||
      tagName === 'SELECT' ||
      isContentEditable
    )
  }
  
  function setupKeyboardShortcuts() {
    document.addEventListener('keydown', handleKeyDown)
  }
  
  function cleanupKeyboardShortcuts() {
    document.removeEventListener('keydown', handleKeyDown)
  }
  
  onMounted(() => {
    setupKeyboardShortcuts()
  })
  
  onUnmounted(() => {
    cleanupKeyboardShortcuts()
  })
  
  return {
    setupKeyboardShortcuts,
    cleanupKeyboardShortcuts
  }
}

// Helper function to get shortcut description
export function getShortcutDescription(key: string): string {
  const shortcuts: Record<string, string> = {
    'cmd+k': '打开命令面板',
    'ctrl+k': '打开命令面板',
    'q': '快速添加任务',
    'space': '定位到最新任务',
    'cmd+i': '切换洞察面板',
    'ctrl+i': '切换洞察面板',
    'cmd+1': '切换到画布视图',
    'ctrl+1': '切换到画布视图',
    'cmd+2': '切换到时间线视图',
    'ctrl+2': '切换到时间线视图',
    'cmd+3': '切换到岛屿视图',
    'ctrl+3': '切换到岛屿视图',
    'shift+delete': '快速删除任务',
    'cmd+z': '撤回删除',
    'ctrl+z': '撤回删除',
    'esc': '关闭浮层'
  }
  
  return shortcuts[key.toLowerCase()] || '未知快捷键'
} 