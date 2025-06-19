import { onMounted, onUnmounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'

export interface KeyboardAction {
  shortcut: keyof ReturnType<typeof useSettingsStore>['shortcuts']
  action: () => void
  description: string
}

export function useKeyboard(actions: KeyboardAction[]) {
  const settingsStore = useSettingsStore()
  
  function handleKeydown(event: KeyboardEvent) {
    // 忽略在输入框中的快捷键
    const target = event.target as HTMLElement
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.contentEditable === 'true'
    ) {
      return
    }
    
    // 检查每个注册的快捷键
    for (const { shortcut, action } of actions) {
      const shortcutKey = settingsStore.shortcuts[shortcut]
      if (settingsStore.matchesShortcut(event, shortcutKey)) {
        event.preventDefault()
        event.stopPropagation()
        action()
        break
      }
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