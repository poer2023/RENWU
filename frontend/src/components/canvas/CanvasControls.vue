<template>
  <div class="canvas-controls">
    <!-- Zoom Controls -->
    <div class="zoom-controls" v-if="showZoomControls">
      <button 
        class="zoom-btn"
        @click="$emit('zoom-in')"
        title="放大 (Ctrl/Cmd +)"
      >
        <el-icon><ZoomIn /></el-icon>
      </button>
      <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
      <button 
        class="zoom-btn"
        @click="$emit('zoom-out')"
        title="缩小 (Ctrl/Cmd -)"
      >
        <el-icon><ZoomOut /></el-icon>
      </button>
      <button 
        class="zoom-btn"
        @click="$emit('reset-zoom')"
        title="重置缩放 (Ctrl/Cmd 0)"
      >
        <el-icon><FullScreen /></el-icon>
      </button>
    </div>
    
    <!-- View Mode Toggle -->
    <div class="view-controls" v-if="showViewControls">
      <button 
        class="view-btn"
        :class="{ active: isIslandView }"
        @click="$emit('toggle-island-view')"
        title="切换岛屿视图"
      >
        <el-icon><Grid /></el-icon>
        <span>岛屿视图</span>
      </button>
      <button 
        class="view-btn"
        @click="$emit('auto-arrange')"
        title="自动排列 (Ctrl/Cmd L)"
      >
        <el-icon><Rank /></el-icon>
        <span>自动排列</span>
      </button>
    </div>
    
    <!-- Performance Indicator -->
    <div class="performance-indicator" v-if="showPerformance && performanceData">
      <span class="fps-counter" :class="fpsClass">
        {{ Math.round(performanceData.fps) }} FPS
      </span>
      <span class="task-count">
        {{ performanceData.taskCount }} 任务
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElIcon } from 'element-plus'
import { ZoomIn, ZoomOut, FullScreen, Grid, Rank } from '@element-plus/icons-vue'

interface Props {
  zoomLevel?: number
  isIslandView?: boolean
  showZoomControls?: boolean
  showViewControls?: boolean
  showPerformance?: boolean
  performanceData?: {
    fps: number
    taskCount: number
  }
}

const props = withDefaults(defineProps<Props>(), {
  zoomLevel: 1,
  isIslandView: false,
  showZoomControls: true,
  showViewControls: true,
  showPerformance: false
})

defineEmits<{
  'open-smart-creation': []
  'zoom-in': []
  'zoom-out': []
  'reset-zoom': []
  'toggle-island-view': []
  'auto-arrange': []
}>()

const fpsClass = computed(() => {
  if (!props.performanceData) return ''
  const fps = props.performanceData.fps
  if (fps >= 50) return 'good'
  if (fps >= 30) return 'warning'
  return 'bad'
})
</script>

<style scoped>
.canvas-controls {
  position: relative;
  pointer-events: none;
}

.canvas-controls > * {
  pointer-events: auto;
}

/* Enhanced Smart Task Creation FAB */
.smart-creation-fab-container {
  position: fixed;
  bottom: 32px;
  right: 32px;
  z-index: 1000;
}

.smart-creation-fab {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 50px;
  box-shadow: 
    0 8px 32px rgba(102, 126, 234, 0.4),
    0 4px 16px rgba(102, 126, 234, 0.2);
  cursor: pointer;
  font-size: 16px;
  font-weight: 700;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform: translateY(0);
  backdrop-filter: blur(20px);
  min-width: 160px;
  justify-content: center;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.smart-creation-fab:hover {
  transform: translateY(-6px) scale(1.05);
  box-shadow: 
    0 16px 48px rgba(102, 126, 234, 0.6),
    0 8px 24px rgba(102, 126, 234, 0.3);
  background: linear-gradient(135deg, #5a6fd8 0%, #6b5b95 100%);
  border-color: rgba(255, 255, 255, 0.3);
}

.smart-creation-fab:active {
  transform: translateY(-3px) scale(1.02);
  transition: all 0.2s ease;
}

.fab-icon {
  font-size: 20px;
  animation: fabIconBounce 2s ease-in-out infinite;
}

@keyframes fabIconBounce {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  25% {
    transform: translateY(-2px) rotate(-5deg);
  }
  75% {
    transform: translateY(-1px) rotate(5deg);
  }
}

.fab-label {
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  font-size: 14px;
}

/* Zoom Controls */
.zoom-controls {
  position: fixed;
  bottom: 32px;
  left: 32px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.95);
  padding: 8px 16px;
  border-radius: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  z-index: 100;
}

.zoom-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: #667eea;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.zoom-btn:hover {
  background: rgba(102, 126, 234, 0.1);
  transform: scale(1.1);
}

.zoom-btn:active {
  transform: scale(0.95);
}

.zoom-level {
  font-size: 14px;
  font-weight: 600;
  color: #4a5568;
  min-width: 50px;
  text-align: center;
}

/* View Controls */
.view-controls {
  position: fixed;
  top: 80px;
  right: 32px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 100;
}

.view-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid transparent;
  border-radius: 12px;
  color: #4a5568;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

.view-btn:hover {
  background: white;
  border-color: #667eea;
  color: #667eea;
  transform: translateX(-4px);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
}

.view-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

/* Performance Indicator */
.performance-indicator {
  position: fixed;
  top: 32px;
  left: 32px;
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(255, 255, 255, 0.95);
  padding: 8px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  font-size: 12px;
  font-weight: 600;
  z-index: 100;
}

.fps-counter {
  padding: 4px 8px;
  border-radius: 4px;
}

.fps-counter.good {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.fps-counter.warning {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
}

.fps-counter.bad {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.task-count {
  color: #6b7280;
}

/* Responsive Design */
@media (max-width: 768px) {
  .smart-creation-fab {
    padding: 14px 18px;
    font-size: 14px;
    min-width: 130px;
    bottom: 20px;
    right: 20px;
  }
  
  .fab-icon {
    font-size: 18px;
  }
  
  .fab-label {
    font-size: 12px;
  }
  
  .zoom-controls {
    bottom: 20px;
    left: 20px;
    padding: 6px 12px;
  }
  
  .zoom-btn {
    width: 32px;
    height: 32px;
  }
  
  .view-controls {
    top: 60px;
    right: 20px;
  }
  
  .view-btn {
    padding: 8px 16px;
    font-size: 12px;
  }
  
  .performance-indicator {
    top: 20px;
    left: 20px;
    padding: 6px 12px;
    font-size: 11px;
  }
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
  .zoom-controls,
  .view-btn,
  .performance-indicator {
    background: rgba(31, 41, 55, 0.95);
    color: #f9fafb;
  }
  
  .zoom-btn {
    color: #a5b4fc;
  }
  
  .zoom-btn:hover {
    background: rgba(102, 126, 234, 0.2);
  }
  
  .zoom-level {
    color: #d1d5db;
  }
  
  .view-btn:hover {
    background: rgba(31, 41, 55, 0.98);
    border-color: #a5b4fc;
    color: #a5b4fc;
  }
  
  .view-btn.active {
    background: #667eea;
  }
  
  .task-count {
    color: #9ca3af;
  }
}

/* Accessibility */
.smart-creation-fab:focus,
.zoom-btn:focus,
.view-btn:focus {
  outline: 3px solid rgba(102, 126, 234, 0.6);
  outline-offset: 2px;
}
</style> 