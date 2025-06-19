import { onMounted, onUnmounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'

export interface KeyboardAction {
  shortcut: keyof ReturnType<typeof useSettingsStore>['shortcuts']
  action: () => void
  description: string
}

export interface KeyboardCallbacks {
  onQuickAdd?: () => void
  onExport?: () => void
  onSearch?: () => void
  onGlobalSearch?: () => void
}

export function useKeyboard(callbacks: KeyboardCallbacks) {
  const settingsStore = useSettingsStore()
  
  function handleKeydown(event: KeyboardEvent) {
    // 忽略在输入框中的快捷键（除了全局搜索）
    const target = event.target as HTMLElement
    const isInputElement = target.tagName === 'INPUT' || 
                          target.tagName === 'TEXTAREA' || 
                          target.contentEditable === 'true'
    
    // 全局搜索快捷键（Shift + Cmd/Ctrl + K）不受输入框影响
    if (event.shiftKey && (event.metaKey || event.ctrlKey) && event.key === 'k') {
      event.preventDefault()
      callbacks.onGlobalSearch?.()
      return
    }
    
    if (isInputElement) {
      return
    }
    
    // 其他快捷键
    if ((event.metaKey || event.ctrlKey) && event.key === 'p') {
      event.preventDefault()
      callbacks.onQuickAdd?.()
    } else if ((event.metaKey || event.ctrlKey) && event.key === 'e') {
      event.preventDefault()
      callbacks.onExport?.()
    } else if ((event.metaKey || event.ctrlKey) && event.key === 'f') {
      event.preventDefault()
      callbacks.onSearch?.()
    }
  }
  
  onMounted(() => {
    document.addEventListener('keydown', handleKeydown)
  })
  
  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown)
  })
  
  return {
    formatShortcut: settingsStore.formatShortcut
  }
}