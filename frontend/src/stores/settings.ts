import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type KeyboardLayout = 'windows' | 'mac'
export type AutoArrangeMode = 'grid' | 'priority' | 'module' | 'timeline' | 'compact' | 'radial' | 'cluster'

export interface KeyboardShortcuts {
  quickAdd: string
  export: string
  save: string
  undo: string
  redo: string
  selectAll: string
  delete: string
  duplicate: string
  search: string
  zoomIn: string
  zoomOut: string
  resetZoom: string
  autoArrange: string
  toggleSidebar: string
  newModule: string
  settings: string
}

export interface AutoArrangeOptions {
  mode: AutoArrangeMode
  spacing: number
  padding: number
  columns?: number
  animated: boolean
  groupByModule: boolean
  sortByPriority: boolean
}

const DEFAULT_SHORTCUTS: Record<KeyboardLayout, KeyboardShortcuts> = {
  windows: {
    quickAdd: 'Ctrl+P',
    export: 'Ctrl+E',
    save: 'Ctrl+S',
    undo: 'Ctrl+Z',
    redo: 'Ctrl+Y',
    selectAll: 'Ctrl+A',
    delete: 'Delete',
    duplicate: 'Ctrl+D',
    search: 'Ctrl+F',
    zoomIn: 'Ctrl+=',
    zoomOut: 'Ctrl+-',
    resetZoom: 'Ctrl+0',
    autoArrange: 'Ctrl+L',
    toggleSidebar: 'Ctrl+B',
    newModule: 'Ctrl+M',
    settings: 'Ctrl+,'
  },
  mac: {
    quickAdd: '⌘P',
    export: '⌘E',
    save: '⌘S',
    undo: '⌘Z',
    redo: '⌘⇧Z',
    selectAll: '⌘A',
    delete: 'Delete',
    duplicate: '⌘D',
    search: '⌘F',
    zoomIn: '⌘=',
    zoomOut: '⌘-',
    resetZoom: '⌘0',
    autoArrange: '⌘L',
    toggleSidebar: '⌘B',
    newModule: '⌘M',
    settings: '⌘,'
  }
}

const DEFAULT_AUTO_ARRANGE: AutoArrangeOptions = {
  mode: 'grid',
  spacing: 20,
  padding: 50,
  columns: 4,
  animated: true,
  groupByModule: false,
  sortByPriority: true
}

export const useSettingsStore = defineStore('settings', () => {
  // UI状态
  const showWorkloadSidebar = ref(false)
  const islandViewEnabled = ref(false)
  // State
  const keyboardLayout = ref<KeyboardLayout>('windows')
  const autoArrangeOptions = ref<AutoArrangeOptions>({ ...DEFAULT_AUTO_ARRANGE })
  const geminiApiKey = ref('')
  const sidebarVisible = ref(true)
  const zoomLevel = ref(1)
  const darkMode = ref(false)
  const notifications = ref(true)
  const autoSave = ref(true)
  const gridVisible = ref(true)

  // Computed
  const shortcuts = computed(() => DEFAULT_SHORTCUTS[keyboardLayout.value])
  
  const isMac = computed(() => keyboardLayout.value === 'mac')
  
  const modifierKey = computed(() => isMac.value ? '⌘' : 'Ctrl')

  // Auto-arrange mode descriptions
  const autoArrangeModes = computed(() => [
    {
      value: 'grid',
      label: '网格排列',
      description: '按网格整齐排列所有任务',
      icon: '⊞'
    },
    {
      value: 'priority',
      label: '优先级排列',
      description: '按优先级从高到低排列',
      icon: '⚡'
    },
    {
      value: 'module',
      label: '模块分组',
      description: '按模块分组排列',
      icon: '📁'
    },
    {
      value: 'timeline',
      label: '时间线排列',
      description: '按创建时间排列',
      icon: '📅'
    },
    {
      value: 'compact',
      label: '紧凑排列',
      description: '最小化空白空间',
      icon: '📦'
    },
    {
      value: 'radial',
      label: '径向排列',
      description: '以中心点辐射排列',
      icon: '🎯'
    },
    {
      value: 'cluster',
      label: '聚类排列',
      description: '相关任务聚集排列',
      icon: '🔗'
    }
  ])

  // Actions
  function setKeyboardLayout(layout: KeyboardLayout) {
    keyboardLayout.value = layout
    saveSettings()
  }

  function updateAutoArrangeOptions(options: Partial<AutoArrangeOptions>) {
    autoArrangeOptions.value = { ...autoArrangeOptions.value, ...options }
    saveSettings()
  }

  function setGeminiApiKey(key: string) {
    geminiApiKey.value = key
    saveSettings()
  }

  function toggleSidebar() {
    sidebarVisible.value = !sidebarVisible.value
    saveSettings()
  }

  function setZoomLevel(level: number) {
    zoomLevel.value = Math.max(0.5, Math.min(2, level))
    saveSettings()
  }

  function zoomIn() {
    setZoomLevel(zoomLevel.value + 0.1)
  }

  function zoomOut() {
    setZoomLevel(zoomLevel.value - 0.1)
  }

  function resetZoom() {
    setZoomLevel(1)
  }

  function toggleDarkMode() {
    darkMode.value = !darkMode.value
    saveSettings()
  }

  function toggleNotifications() {
    notifications.value = !notifications.value
    saveSettings()
  }

  function toggleAutoSave() {
    autoSave.value = !autoSave.value
    saveSettings()
  }

  function toggleGrid() {
    gridVisible.value = !gridVisible.value
    saveSettings()
  }

  function toggleWorkloadSidebar() {
    showWorkloadSidebar.value = !showWorkloadSidebar.value
    saveSettings()
  }

  function toggleIslandView() {
    islandViewEnabled.value = !islandViewEnabled.value
    saveSettings()
  }

  // Save settings to localStorage
  function saveSettings() {
    const settings = {
      keyboardLayout: keyboardLayout.value,
      autoArrangeOptions: autoArrangeOptions.value,
      geminiApiKey: geminiApiKey.value,
      sidebarVisible: sidebarVisible.value,
      zoomLevel: zoomLevel.value,
      darkMode: darkMode.value,
      notifications: notifications.value,
      autoSave: autoSave.value,
      gridVisible: gridVisible.value,
      showWorkloadSidebar: showWorkloadSidebar.value
    }
    localStorage.setItem('taskwall-settings', JSON.stringify(settings))
  }

  // Load settings from localStorage
  function loadSettings() {
    try {
      const saved = localStorage.getItem('taskwall-settings')
      if (saved) {
        const settings = JSON.parse(saved)
        keyboardLayout.value = settings.keyboardLayout || 'windows'
        autoArrangeOptions.value = { ...DEFAULT_AUTO_ARRANGE, ...settings.autoArrangeOptions }
        geminiApiKey.value = settings.geminiApiKey || ''
        sidebarVisible.value = settings.sidebarVisible !== undefined ? settings.sidebarVisible : true
        zoomLevel.value = settings.zoomLevel || 1
        darkMode.value = settings.darkMode || false
        notifications.value = settings.notifications !== undefined ? settings.notifications : true
        autoSave.value = settings.autoSave !== undefined ? settings.autoSave : true
        gridVisible.value = settings.gridVisible !== undefined ? settings.gridVisible : true
        showWorkloadSidebar.value = settings.showWorkloadSidebar !== undefined ? settings.showWorkloadSidebar : true
      }
    } catch (error) {
      console.warn('Failed to load settings:', error)
    }
  }

  // Detect platform automatically
  function detectPlatform() {
    const platform = navigator.platform.toLowerCase()
    const isMacPlatform = platform.includes('mac') || platform.includes('darwin')
    setKeyboardLayout(isMacPlatform ? 'mac' : 'windows')
  }

  // Keyboard shortcut helper
  function formatShortcut(shortcut: string): string {
    if (isMac.value) {
      return shortcut
        .replace('Ctrl', '⌘')
        .replace('Alt', '⌥')
        .replace('Shift', '⇧')
    }
    return shortcut
  }

  // Check if key combination matches shortcut
  function matchesShortcut(event: KeyboardEvent, shortcut: string): boolean {
    const parts = shortcut.toLowerCase().split('+')
    const key = parts[parts.length - 1]
    const modifiers = parts.slice(0, -1)

    // Check key
    if (event.key.toLowerCase() !== key && event.code.toLowerCase() !== key.replace(/[^a-z0-9]/g, '')) {
      return false
    }

    // Check modifiers
    const hasCtrl = modifiers.includes('ctrl') || modifiers.includes('⌘')
    const hasAlt = modifiers.includes('alt') || modifiers.includes('⌥')
    const hasShift = modifiers.includes('shift') || modifiers.includes('⇧')

    return (
      (hasCtrl ? (event.ctrlKey || event.metaKey) : !event.ctrlKey && !event.metaKey) &&
      (hasAlt ? event.altKey : !event.altKey) &&
      (hasShift ? event.shiftKey : !event.shiftKey)
    )
  }

  return {
    // State
    keyboardLayout,
    autoArrangeOptions,
    geminiApiKey,
    sidebarVisible,
    zoomLevel,
    darkMode,
    notifications,
    autoSave,
    gridVisible,
    showWorkloadSidebar,
    islandViewEnabled,

    // Computed
    shortcuts,
    isMac,
    modifierKey,
    autoArrangeModes,

    // Actions
    setKeyboardLayout,
    updateAutoArrangeOptions,
    setGeminiApiKey,
    toggleSidebar,
    setZoomLevel,
    zoomIn,
    zoomOut,
    resetZoom,
    toggleDarkMode,
    toggleNotifications,
    toggleAutoSave,
    toggleGrid,
    toggleWorkloadSidebar,
    toggleIslandView,
    saveSettings,
    loadSettings,
    detectPlatform,
    formatShortcut,
    matchesShortcut
  }
})