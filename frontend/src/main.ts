import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import './styles/index.css'

import App from './App.vue'
import Home from './pages/Home.vue'
import { setupGlobalErrorHandlers } from './utils/errorHandler'
import { accessibilityManager, srOnlyStyles } from './utils/accessibility'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home,
    },
  ],
})

const app = createApp(App)

// Register Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// Setup global error handlers
setupGlobalErrorHandlers()

// Add Vue error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue Error:', err, info)
  // Prevent error from bubbling up
  return false
}

// Handle unhandled promise rejections specifically for Vue
app.config.warnHandler = (msg, vm, trace) => {
  console.warn('Vue Warning:', msg, trace)
}

// Initialize accessibility features
accessibilityManager.init()

// Add accessibility styles
const styleSheet = document.createElement('style')
styleSheet.textContent = srOnlyStyles
document.head.appendChild(styleSheet)

app.mount('#app')