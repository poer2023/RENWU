<template>
  <div class="performance-optimizer">
    <!-- 性能监控显示（开发模式） -->
    <div v-if="showMetrics && isDevelopment" class="performance-metrics">
      <div class="metric">
        <span>FPS:</span>
        <span :class="{ 'warning': currentFPS < 30, 'critical': currentFPS < 15 }">
          {{ currentFPS.toFixed(1) }}
        </span>
      </div>
      <div class="metric">
        <span>渲染时间:</span>
        <span :class="{ 'warning': lastRenderTime > 16.67, 'critical': lastRenderTime > 33 }">
          {{ lastRenderTime.toFixed(2) }}ms
        </span>
      </div>
      <div class="metric">
        <span>可见任务:</span>
        <span>{{ visibleTaskCount }}/{{ totalTaskCount }}</span>
      </div>
      <div class="metric">
        <span>内存使用:</span>
        <span>{{ memoryUsage.toFixed(1) }}MB</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

interface Props {
  enabled?: boolean
  showMetrics?: boolean
  taskCount: number
  visibleTaskCount: number
  isRendering?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  enabled: true,
  showMetrics: false,
  isRendering: false
})

const emit = defineEmits<{
  performanceWarning: [type: string, value: number, threshold: number]
  performanceCritical: [type: string, value: number, threshold: number]
  optimizationSuggestion: [suggestion: string]
}>()

// 性能指标
const performanceMetrics = ref({
  lastRenderTime: 0,
  frameCount: 0,
  avgFrameTime: 0,
  fps: 60,
  memoryUsage: 0,
  lastUpdate: 0
})

// 计算属性
const isDevelopment = computed(() => import.meta.env.DEV)
const currentFPS = computed(() => performanceMetrics.value.fps)
const lastRenderTime = computed(() => performanceMetrics.value.lastRenderTime)
const totalTaskCount = computed(() => props.taskCount)
const memoryUsage = computed(() => performanceMetrics.value.memoryUsage)

// FPS 监控
let fpsCounter = 0
let fpsStartTime = performance.now()
let animationFrameId: number | null = null

// 内存监控
let memoryMonitorInterval: NodeJS.Timeout | null = null

// RAF 池管理
const rafPool = new Set<number>()

// 节流函数池
const throttledFunctions = new Map<string, (...args: any[]) => void>()

// 防抖函数池
const debouncedFunctions = new Map<string, (...args: any[]) => void>()

// 开始性能监控
function startPerformanceMonitoring() {
  if (!props.enabled) return

  // FPS 监控
  startFPSMonitoring()
  
  // 内存监控
  startMemoryMonitoring()
  
  // 渲染时间监控
  startRenderTimeMonitoring()
}

// FPS 监控
function startFPSMonitoring() {
  function updateFPS() {
    fpsCounter++
    const currentTime = performance.now()
    const elapsed = currentTime - fpsStartTime
    
    if (elapsed >= 1000) {
      const fps = (fpsCounter * 1000) / elapsed
      performanceMetrics.value.fps = fps
      
      // 检查性能警告
      if (fps < 15) {
        emit('performanceCritical', 'fps', fps, 15)
      } else if (fps < 30) {
        emit('performanceWarning', 'fps', fps, 30)
      }
      
      fpsCounter = 0
      fpsStartTime = currentTime
    }
    
    animationFrameId = requestAnimationFrame(updateFPS)
  }
  
  updateFPS()
}

// 内存监控
function startMemoryMonitoring() {
  if (!(performance as any).memory) return
  
  memoryMonitorInterval = setInterval(() => {
    const memory = (performance as any).memory
    if (memory) {
      const usedMB = memory.usedJSHeapSize / 1024 / 1024
      performanceMetrics.value.memoryUsage = usedMB
      
      // 检查内存使用警告
      if (usedMB > 100) {
        emit('performanceCritical', 'memory', usedMB, 100)
      } else if (usedMB > 50) {
        emit('performanceWarning', 'memory', usedMB, 50)
      }
    }
  }, 2000)
}

// 渲染时间监控
function startRenderTimeMonitoring() {
  // 这个方法将在渲染开始和结束时被调用
}

// 优化的渲染函数
function optimizedRender(renderFn: () => void) {
  if (!props.enabled) {
    renderFn()
    return
  }
  
  const startTime = performance.now()
  
  renderFn()
  
  const endTime = performance.now()
  const renderTime = endTime - startTime
  
  performanceMetrics.value.lastRenderTime = renderTime
  performanceMetrics.value.frameCount++
  
  // 计算平均帧时间
  performanceMetrics.value.avgFrameTime = 
    (performanceMetrics.value.avgFrameTime * (performanceMetrics.value.frameCount - 1) + renderTime) / 
    performanceMetrics.value.frameCount
  
  // 性能警告
  if (renderTime > 33) { // 超过30fps
    emit('performanceCritical', 'renderTime', renderTime, 33)
  } else if (renderTime > 16.67) { // 超过60fps
    emit('performanceWarning', 'renderTime', renderTime, 16.67)
  }
}

// 管理 RAF 的函数
function managedRequestAnimationFrame(callback: FrameRequestCallback): number {
  const id = requestAnimationFrame(callback)
  rafPool.add(id)
  return id
}

function managedCancelAnimationFrame(id: number) {
  cancelAnimationFrame(id)
  rafPool.delete(id)
}

// 清理所有 RAF
function cleanupAllRAF() {
  rafPool.forEach(id => cancelAnimationFrame(id))
  rafPool.clear()
}

// 创建节流函数
function createThrottledFunction<T extends (...args: any[]) => void>(
  key: string,
  fn: T,
  delay: number
): T {
  if (throttledFunctions.has(key)) {
    return throttledFunctions.get(key) as T
  }
  
  let lastCall = 0
  const throttled = ((...args: any[]) => {
    const now = Date.now()
    if (now - lastCall >= delay) {
      lastCall = now
      fn(...args)
    }
  }) as T
  
  throttledFunctions.set(key, throttled)
  return throttled
}

// 创建防抖函数
function createDebouncedFunction<T extends (...args: any[]) => void>(
  key: string,
  fn: T,
  delay: number
): T {
  if (debouncedFunctions.has(key)) {
    return debouncedFunctions.get(key) as T
  }
  
  let timeoutId: NodeJS.Timeout | null = null
  const debounced = ((...args: any[]) => {
    if (timeoutId) clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }) as T
  
  debouncedFunctions.set(key, debounced)
  return debounced
}

// 虚拟化建议
function checkVirtualizationNeed() {
  if (props.taskCount > 100 && props.visibleTaskCount / props.taskCount > 0.8) {
    emit('optimizationSuggestion', '建议启用任务虚拟化以提高性能')
  }
}

// 内存清理建议
function checkMemoryCleanup() {
  if (performanceMetrics.value.memoryUsage > 80) {
    emit('optimizationSuggestion', '内存使用过高，建议清理不必要的缓存')
  }
}

// 监听任务数量变化
watch(() => props.taskCount, () => {
  checkVirtualizationNeed()
})

// 监听内存使用
watch(() => performanceMetrics.value.memoryUsage, () => {
  checkMemoryCleanup()
})

// 停止性能监控
function stopPerformanceMonitoring() {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
  
  if (memoryMonitorInterval) {
    clearInterval(memoryMonitorInterval)
    memoryMonitorInterval = null
  }
  
  cleanupAllRAF()
  throttledFunctions.clear()
  debouncedFunctions.clear()
}

// 生命周期
onMounted(() => {
  if (props.enabled) {
    startPerformanceMonitoring()
  }
})

onUnmounted(() => {
  stopPerformanceMonitoring()
})

// 监听启用状态
watch(() => props.enabled, (enabled) => {
  if (enabled) {
    startPerformanceMonitoring()
  } else {
    stopPerformanceMonitoring()
  }
})

// 暴露方法给父组件
defineExpose({
  optimizedRender,
  managedRequestAnimationFrame,
  managedCancelAnimationFrame,
  createThrottledFunction,
  createDebouncedFunction,
  cleanupAllRAF,
  performanceMetrics: computed(() => performanceMetrics.value)
})
</script>

<style scoped>
.performance-optimizer {
  position: relative;
}

.performance-metrics {
  position: fixed;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 10px;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  z-index: 9999;
  min-width: 200px;
}

.metric {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.metric:last-child {
  margin-bottom: 0;
}

.metric span:first-child {
  color: #888;
}

.metric span:last-child {
  color: #0f0;
  font-weight: bold;
}

.metric span.warning {
  color: #ff0 !important;
}

.metric span.critical {
  color: #f00 !important;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
}
</style> 