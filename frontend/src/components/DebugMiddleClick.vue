<template>
  <div class="debug-overlay" v-if="showDebug">
    <div class="debug-panel">
      <h3>🔍 中键拖动调试面板</h3>
      <button @click="toggleDebug" class="close-btn">❌</button>
      
      <div class="debug-section">
        <h4>📊 事件统计</h4>
        <p>mousedown 事件: {{ stats.mousedown }}</p>
        <p>auxclick 事件: {{ stats.auxclick }}</p>
        <p>中键拖动开始: {{ stats.panStart }}</p>
        <p>拖动结束: {{ stats.panEnd }}</p>
      </div>
      
      <div class="debug-section">
        <h4>🎯 最后一次事件</h4>
        <p>按键: {{ lastEvent.button }}</p>
        <p>位置: ({{ lastEvent.x }}, {{ lastEvent.y }})</p>
        <p>目标: {{ lastEvent.target }}</p>
        <p>时间: {{ lastEvent.time }}</p>
      </div>
      
      <div class="debug-section">
        <h4>🔧 系统信息</h4>
        <p>浏览器: {{ browserInfo }}</p>
        <p>触摸设备: {{ isTouchDevice ? '是' : '否' }}</p>
        <p>auxclick支持: {{ supportsAuxClick ? '是' : '否' }}</p>
      </div>
      
      <div class="debug-section">
        <h4>📋 最近日志</h4>
        <div class="log-container">
          <div v-for="(log, index) in recentLogs" :key="index" 
               :class="['log-item', log.type]">
            [{{ log.time }}] {{ log.message }}
          </div>
        </div>
      </div>
      
      <div class="debug-section">
        <button @click="clearLogs" class="clear-btn">🗑️ 清除日志</button>
        <button @click="testMiddleClick" class="test-btn">🧪 测试中键</button>
      </div>
    </div>
  </div>
  
  <!-- 触发按钮 -->
  <div class="debug-trigger" @click="toggleDebug" v-if="!showDebug">
    🔍
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'

const showDebug = ref(false)

const stats = reactive({
  mousedown: 0,
  auxclick: 0,
  panStart: 0,
  panEnd: 0
})

const lastEvent = reactive({
  button: 0,
  x: 0,
  y: 0,
  target: '',
  time: ''
})

const recentLogs = ref<Array<{time: string, message: string, type: string}>>([])

const browserInfo = ref('')
const isTouchDevice = ref(false)
const supportsAuxClick = ref(false)

function addLog(message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') {
  const time = new Date().toLocaleTimeString()
  recentLogs.value.push({ time, message, type })
  
  // 保持最近20条日志
  if (recentLogs.value.length > 20) {
    recentLogs.value.shift()
  }
  
  console.log(`[DebugMiddleClick] ${message}`)
}

function toggleDebug() {
  showDebug.value = !showDebug.value
  if (showDebug.value) {
    addLog('调试面板已打开', 'info')
  }
}

function clearLogs() {
  recentLogs.value = []
  Object.keys(stats).forEach(key => {
    stats[key as keyof typeof stats] = 0
  })
  addLog('日志和统计已清除', 'info')
}

function testMiddleClick() {
  addLog('开始模拟中键测试...', 'info')
  
  // 模拟中键事件
  const canvas = document.querySelector('.sticky-canvas') as HTMLElement
  if (canvas) {
    const rect = canvas.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2
    
    const mouseEvent = new MouseEvent('mousedown', {
      button: 1,
      buttons: 4,
      clientX: centerX,
      clientY: centerY,
      bubbles: true,
      cancelable: true
    })
    
    addLog(`模拟中键事件: 位置=(${centerX}, ${centerY})`, 'info')
    canvas.dispatchEvent(mouseEvent)
    
    setTimeout(() => {
      const mouseUpEvent = new MouseEvent('mouseup', {
        button: 1,
        buttons: 0,
        clientX: centerX + 50,
        clientY: centerY + 50,
        bubbles: true,
        cancelable: true
      })
      canvas.dispatchEvent(mouseUpEvent)
      addLog('模拟中键测试完成', 'success')
    }, 500)
  } else {
    addLog('找不到画布元素', 'error')
  }
}

// 监听全局事件
function handleGlobalMouseDown(event: MouseEvent) {
  stats.mousedown++
  lastEvent.button = event.button
  lastEvent.x = event.clientX
  lastEvent.y = event.clientY
  lastEvent.target = (event.target as HTMLElement)?.className || 'unknown'
  lastEvent.time = new Date().toLocaleTimeString()
  
  if (event.button === 1) {
    addLog(`🎯 检测到中键按下: 位置=(${event.clientX}, ${event.clientY})`, 'warning')
  }
}

function handleGlobalAuxClick(event: MouseEvent) {
  stats.auxclick++
  if (event.button === 1) {
    addLog(`🎯 检测到auxclick事件: button=${event.button}`, 'info')
  }
}

// 监听控制台消息（如果可能）
const originalConsoleLog = console.log
console.log = function(...args) {
  const message = args.join(' ')
  
  if (message.includes('开始中键画布拖动')) {
    stats.panStart++
    addLog('✅ 中键拖动开始事件已触发', 'success')
  } else if (message.includes('超级画布拖动结束')) {
    stats.panEnd++
    addLog('✅ 中键拖动结束事件已触发', 'success')
  }
  
  originalConsoleLog.apply(console, args)
}

onMounted(() => {
  // 检测浏览器信息
  browserInfo.value = navigator.userAgent.includes('Chrome') ? 'Chrome' : 
                     navigator.userAgent.includes('Firefox') ? 'Firefox' : 
                     navigator.userAgent.includes('Safari') ? 'Safari' : '其他'
  
  isTouchDevice.value = navigator.maxTouchPoints > 0
  supportsAuxClick.value = 'onauxclick' in document.createElement('div')
  
  // 绑定全局事件监听
  document.addEventListener('mousedown', handleGlobalMouseDown, true)
  document.addEventListener('auxclick', handleGlobalAuxClick, true)
  
  addLog('调试组件已初始化', 'success')
  addLog(`浏览器: ${browserInfo.value}, 触摸设备: ${isTouchDevice.value}`, 'info')
})

onUnmounted(() => {
  // 恢复console.log
  console.log = originalConsoleLog
  
  // 移除事件监听
  document.removeEventListener('mousedown', handleGlobalMouseDown, true)
  document.removeEventListener('auxclick', handleGlobalAuxClick, true)
})
</script>

<style scoped>
.debug-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.8);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.debug-panel {
  background: white;
  border-radius: 10px;
  padding: 20px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: #ff6b6b;
  color: white;
  border: none;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  cursor: pointer;
  font-size: 12px;
}

.debug-section {
  margin-bottom: 15px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

.debug-section h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.debug-section p {
  margin: 5px 0;
  font-family: monospace;
  font-size: 12px;
}

.log-container {
  max-height: 150px;
  overflow-y: auto;
  background: #f8f9fa;
  padding: 5px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 11px;
}

.log-item {
  margin: 2px 0;
  padding: 2px 5px;
  border-radius: 2px;
}

.log-item.info {
  background: #e3f2fd;
  color: #1976d2;
}

.log-item.success {
  background: #e8f5e8;
  color: #2e7d32;
}

.log-item.warning {
  background: #fff3e0;
  color: #f57c00;
}

.log-item.error {
  background: #ffebee;
  color: #d32f2f;
}

.clear-btn, .test-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 10px;
  font-size: 12px;
}

.clear-btn:hover, .test-btn:hover {
  background: #0056b3;
}

.debug-trigger {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 50px;
  height: 50px;
  background: #007bff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 9999;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

.debug-trigger:hover {
  background: #0056b3;
  transform: scale(1.1);
}
</style>