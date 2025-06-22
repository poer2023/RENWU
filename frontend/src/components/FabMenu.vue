<template>
  <div class="fab-container">
    <!-- Main FAB -->
    <div 
      class="fab-main" 
      :class="{ 'fab-expanded': fabExpanded }"
      @click="toggleFab"
    >
      <div class="fab-icon">
        <span v-if="!fabExpanded">+</span>
        <span v-else>×</span>
      </div>
    </div>
    
    <!-- Sub FABs -->
    <transition-group name="fab-sub" tag="div" class="fab-sub-container">
      <div 
        v-if="fabExpanded"
        v-for="(action, index) in fabActions"
        :key="action.key"
        class="fab-sub"
        :style="getFabSubPosition(index)"
        @click="executeFabAction(action)"
        :title="action.title"
      >
        <div class="fab-sub-icon">{{ action.icon }}</div>
        <div class="fab-sub-label">{{ action.label }}</div>
      </div>
    </transition-group>
    
    <!-- View Switcher FAB -->
    <div 
      class="fab-view-switcher" 
      @click="switchView"
      :title="getViewSwitcherTitle()"
    >
      <div class="fab-icon">{{ getCurrentViewIcon() }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface FabAction {
  key: string
  icon: string
  label: string
  title: string
  action: () => void
}

interface Props {
  currentView?: string
}

interface Emits {
  (e: 'action', actionKey: string): void
  (e: 'view-switch'): void
}

const props = withDefaults(defineProps<Props>(), {
  currentView: 'canvas'
})

const emit = defineEmits<Emits>()

const fabExpanded = ref(false)

// FAB Actions Configuration - Simplified since main actions moved to top
const fabActions = ref<FabAction[]>([
  {
    key: 'upload-image',
    icon: '📷',
    label: '上传图片',
    title: '上传图片进行OCR识别',
    action: () => emit('action', 'upload-image')
  },
  {
    key: 'quick-note',
    icon: '✏️',
    label: '快速笔记',
    title: '快速文本输入',
    action: () => emit('action', 'quick-note')
  }
])

function toggleFab() {
  fabExpanded.value = !fabExpanded.value
}

function executeFabAction(action: FabAction) {
  fabExpanded.value = false
  action.action()
}

function getFabSubPosition(index: number) {
  const radius = 80
  const angle = (index * 45) - 90 // Start from top and go clockwise
  const x = Math.cos(angle * Math.PI / 180) * radius
  const y = Math.sin(angle * Math.PI / 180) * radius
  
  return {
    transform: `translate(${x}px, ${y}px)`,
    transitionDelay: `${index * 50}ms`
  }
}

function switchView() {
  emit('view-switch')
}

function getCurrentViewIcon() {
  switch (props.currentView) {
    case 'canvas':
      return '🎨'
    case 'timeline':
      return '📅'
    case 'island':
      return '🏝️'
    default:
      return '🎨'
  }
}

function getViewSwitcherTitle() {
  switch (props.currentView) {
    case 'canvas':
      return '切换到时间线视图'
    case 'timeline':
      return '切换到岛屿视图'
    case 'island':
      return '切换到画布视图'
    default:
      return '切换视图'
  }
}

// Expose methods if needed
defineExpose({
  toggleFab,
  closeFab: () => { fabExpanded.value = false }
})
</script>

<style scoped>
.fab-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
}

.fab-main {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  box-shadow: var(--shadow-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1002;
  position: relative;
}

.fab-main:hover {
  transform: scale(1.05);
  box-shadow: var(--shadow-xl);
}

.fab-main.fab-expanded {
  background: var(--danger);
  transform: rotate(45deg);
}

.fab-icon {
  font-size: 24px;
  font-weight: bold;
  transition: transform 0.2s ease;
}

.fab-sub-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 56px;
  height: 56px;
}

.fab-sub {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: center;
  backdrop-filter: blur(8px);
}

.fab-sub:hover {
  transform: scale(1.1);
  background: var(--bg-elevated);
  box-shadow: var(--shadow-lg);
}

.fab-sub-icon {
  font-size: 16px;
  margin-bottom: 2px;
}

.fab-sub-label {
  font-size: 8px;
  font-weight: var(--font-weight-medium);
  color: var(--text-muted);
  text-align: center;
  line-height: 1;
  max-width: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fab-view-switcher {
  position: absolute;
  top: -76px;
  left: 4px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  box-shadow: var(--shadow-md);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 1001;
}

.fab-view-switcher:hover {
  transform: scale(1.05);
  background: var(--bg-elevated);
}

/* FAB Transitions */
.fab-sub-enter-active,
.fab-sub-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.fab-sub-enter-from,
.fab-sub-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

/* Responsive Design */
@media (max-width: 1280px) {
  .fab-container {
    bottom: 16px;
    right: 16px;
  }
}

@media (max-width: 768px) {
  .fab-main {
    width: 48px;
    height: 48px;
  }
  
  .fab-sub {
    width: 40px;
    height: 40px;
  }
  
  .fab-sub-icon {
    font-size: 14px;
  }
  
  .fab-sub-label {
    font-size: 7px;
  }
}
</style> 