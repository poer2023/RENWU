<template>
  <div class="canvas-grid" :style="gridStyle">
    <!-- Canvas boundary indicator -->
    <div class="canvas-boundary" :style="boundaryStyle"></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  size?: number
  color?: string
  opacity?: number
  showDots?: boolean
  canvasWidth?: number
  canvasHeight?: number
  showBoundary?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 40,
  color: 'rgba(102, 126, 234, 0.1)',
  opacity: 0.4,
  showDots: true,
  canvasWidth: 6000,
  canvasHeight: 6000,
  showBoundary: true
})

const gridStyle = computed(() => ({
  opacity: props.opacity,
  backgroundSize: `${props.size}px ${props.size}px`,
  backgroundImage: `
    linear-gradient(${props.color} 1px, transparent 1px),
    linear-gradient(90deg, ${props.color} 1px, transparent 1px)
  `.trim()
}))

const boundaryStyle = computed(() => ({
  width: `${props.canvasWidth}px`,
  height: `${props.canvasHeight}px`,
  display: props.showBoundary ? 'block' : 'none'
}))
</script>

<style scoped>
/* Modern Canvas Grid */
.canvas-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  background-position: 0 0, 0 0;
  contain: layout style paint;
}

/* Enhanced grid dots for modern feel */
.canvas-grid::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: radial-gradient(circle, rgba(102, 126, 234, 0.15) 1px, transparent 1px);
  background-size: 40px 40px;
  opacity: 0.6;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .canvas-grid {
    background-image: 
      linear-gradient(rgba(102, 126, 234, 0.2) 1px, transparent 1px),
      linear-gradient(90deg, rgba(102, 126, 234, 0.2) 1px, transparent 1px);
  }
  
  .canvas-grid::after {
    background-image: radial-gradient(circle, rgba(102, 126, 234, 0.3) 1px, transparent 1px);
  }
  
  .canvas-boundary {
    border: 2px solid rgba(102, 126, 234, 0.4);
    background: rgba(102, 126, 234, 0.05);
  }
}

/* Canvas boundary indicator */
.canvas-boundary {
  position: absolute;
  top: 0;
  left: 0;
  border: 2px solid rgba(102, 126, 234, 0.2);
  background: rgba(102, 126, 234, 0.02);
  box-shadow: 
    inset 0 0 20px rgba(102, 126, 234, 0.1),
    0 0 10px rgba(102, 126, 234, 0.1);
  pointer-events: none;
  z-index: 1;
  border-radius: 8px;
}
</style> 