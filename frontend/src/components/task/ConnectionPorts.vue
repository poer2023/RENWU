<template>
  <div class="connection-ports" :class="{ visible }" v-show="visible">
    <!-- 顶部连接点 -->
    <div 
      class="connection-port port-top" 
      @mousedown.stop="startConnection('top', $event)"
      :class="{ 'port-active': isActive }"
    >
      <div class="port-dot"></div>
    </div>
    
    <!-- 右侧连接点 -->
    <div 
      class="connection-port port-right" 
      @mousedown.stop="startConnection('right', $event)"
      :class="{ 'port-active': isActive }"
    >
      <div class="port-dot"></div>
    </div>
    
    <!-- 底部连接点 -->
    <div 
      class="connection-port port-bottom" 
      @mousedown.stop="startConnection('bottom', $event)"
      :class="{ 'port-active': isActive }"
    >
      <div class="port-dot"></div>
    </div>
    
    <!-- 左侧连接点 -->
    <div 
      class="connection-port port-left" 
      @mousedown.stop="startConnection('left', $event)"
      :class="{ 'port-active': isActive }"
    >
      <div class="port-dot"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch } from 'vue'

interface Props {
  visible?: boolean
  isActive?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  isActive: false
})

const emit = defineEmits<{
  'start-connection': [position: 'top' | 'right' | 'bottom' | 'left', event: MouseEvent]
}>()

// 监控 visible 属性变化
watch(() => props.visible, (newVal) => {
  console.log('ConnectionPorts: visible changed to', newVal)
}, { immediate: true })

function startConnection(position: 'top' | 'right' | 'bottom' | 'left', event: MouseEvent) {
  console.log('🔗 ConnectionPorts: startConnection called', position, event)
  console.log('🔗 ConnectionPorts: event target:', event.target)
  console.log('🔗 ConnectionPorts: event currentTarget:', event.currentTarget)
  
  // 确保阻止事件传播到统一拖动系统
  event.preventDefault()
  event.stopPropagation()
  event.stopImmediatePropagation()
  
  emit('start-connection', position, event)
}
</script>

<style scoped>
/* Connection Ports Container */
.connection-ports {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 100; /* 提高z-index确保在任务卡片之上 */
}

.connection-port {
  position: absolute;
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: auto;
  cursor: crosshair;
  z-index: 101; /* 确保连接点在最顶层 */
  /* 增加点击区域 */
  padding: 2px;
}

/* Show ports when parent is selected or connecting */
:global(.task-node.selected) .connection-port,
:global(.task-node.connecting) .connection-port,
.connection-ports.visible .connection-port {
  opacity: 1;
}

:global(.task-node:hover) .connection-port {
  opacity: 0.7;
}

/* Port positions */
.port-top {
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
}

.port-right {
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
}

.port-bottom {
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
}

.port-left {
  left: -6px;
  top: 50%;
  transform: translateY(-50%);
}

/* Port dot styling */
.port-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: var(--primary);
  border: 2px solid var(--card-bg);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.connection-port:hover .port-dot {
  transform: scale(1.3);
  background-color: var(--primary-hover);
  box-shadow: 0 0 12px var(--primary-light);
}

.connection-port.port-active .port-dot {
  background-color: var(--success);
  transform: scale(1.4);
  box-shadow: 0 0 16px var(--success-light);
  animation: connection-pulse 1.5s infinite;
}

@keyframes connection-pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1.4);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.6);
  }
}

/* Dark mode adjustments */
@media (prefers-color-scheme: dark) {
  .port-dot {
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .connection-port:hover .port-dot {
    box-shadow: 0 0 12px rgba(102, 126, 234, 0.6);
  }
  
  .connection-port.port-active .port-dot {
    box-shadow: 0 0 16px rgba(16, 185, 129, 0.6);
  }
}
</style> 