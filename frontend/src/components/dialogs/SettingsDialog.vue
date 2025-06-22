<template>
  <div v-if="visible" class="command-palette-overlay" @click="handleOverlayClick">
    <div class="command-palette settings-dialog" @click.stop>
      <!-- Header -->
      <div class="search-container">
        <div class="search-icon">⚙️</div>
        <div class="view-title">应用设置</div>
        <button @click="handleClose" class="close-button">✕</button>
      </div>
      
      <!-- Settings Tabs -->
      <div class="settings-tabs">
        <div
          v-for="tab in settingsTabs"
          :key="tab.key"
          :class="['settings-tab', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          <div class="tab-icon">{{ tab.icon }}</div>
          <div class="tab-label">{{ tab.label }}</div>
        </div>
      </div>
      
      <!-- Settings Content -->
      <div class="results-container">
        <!-- 快捷键设置 -->
        <div v-if="activeTab === 'shortcuts'" class="settings-section">
          <div class="section-header">
            <div class="search-icon">⌨️</div>
            <span>快捷键设置</span>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">键盘布局</div>
            <div class="setting-control">
              <div class="radio-group">
                <label class="radio-item">
                  <input 
                    type="radio" 
                    :value="'windows'" 
                    v-model="settingsStore.keyboardLayout"
                    @change="settingsStore.setKeyboardLayout"
                  />
                  <span>Windows (Ctrl)</span>
                </label>
                <label class="radio-item">
                  <input 
                    type="radio" 
                    :value="'mac'" 
                    v-model="settingsStore.keyboardLayout"
                    @change="settingsStore.setKeyboardLayout"
                  />
                  <span>Mac (⌘)</span>
                </label>
              </div>
            </div>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">快捷键列表</div>
            <div class="shortcuts-list">
              <div v-for="(shortcut, key) in settingsStore.shortcuts" :key="key" class="shortcut-row">
                <span class="shortcut-name">{{ getShortcutName(key) }}</span>
                <kbd class="shortcut-key">{{ settingsStore.formatShortcut(shortcut) }}</kbd>
              </div>
            </div>
          </div>
        </div>
        
        <!-- AI设置 -->
        <div v-if="activeTab === 'ai'" class="settings-section">
          <div class="section-header">
            <div class="search-icon">🤖</div>
            <span>AI设置</span>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">Gemini API Key</div>
            <div class="setting-control">
              <input 
                v-model="settingsStore.geminiApiKey" 
                type="password" 
                placeholder="输入你的 Gemini API key 用于AI解析"
                class="setting-input"
              />
              <small class="setting-hint">用于从文本中AI智能解析任务</small>
            </div>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">AI功能启用</div>
            <div class="checkbox-group">
              <label class="checkbox-item">
                <input type="checkbox" v-model="localAiFeatures.textParsing" />
                <span class="checkbox-label">
                  <strong>智能文本解析</strong>
                  <small>从纯文本中自动识别和创建任务</small>
                </span>
              </label>
              
              <label class="checkbox-item">
                <input type="checkbox" v-model="localAiFeatures.subtaskGeneration" />
                <span class="checkbox-label">
                  <strong>子任务生成</strong>
                  <small>为复杂任务自动生成子任务</small>
                </span>
              </label>
              
              <label class="checkbox-item">
                <input type="checkbox" v-model="localAiFeatures.similarityDetection" />
                <span class="checkbox-label">
                  <strong>相似任务检测</strong>
                  <small>创建任务时检测已有的相似任务</small>
                </span>
              </label>
              
              <label class="checkbox-item">
                <input type="checkbox" v-model="localAiFeatures.weeklyReports" />
                <span class="checkbox-label">
                  <strong>周报生成</strong>
                  <small>自动生成工作周报</small>
                </span>
              </label>
              
              <label class="checkbox-item">
                <input type="checkbox" v-model="localAiFeatures.riskAnalysis" />
                <span class="checkbox-label">
                  <strong>风险分析</strong>
                  <small>分析任务风险并提供建议</small>
                </span>
              </label>
              
              <label class="checkbox-item">
                <input type="checkbox" v-model="localAiFeatures.themeIslands" />
                <span class="checkbox-label">
                  <strong>主题岛聚类</strong>
                  <small>基于主题自动分组相关任务</small>
                </span>
              </label>
            </div>
          </div>
        </div>
        
        <!-- 界面设置 -->
        <div v-if="activeTab === 'interface'" class="settings-section">
          <div class="section-header">
            <div class="search-icon">🎨</div>
            <span>界面设置</span>
          </div>
          
          <div class="checkbox-group">
            <label class="checkbox-item">
              <input type="checkbox" v-model="settingsStore.gridVisible" @change="settingsStore.toggleGrid" />
              <span class="checkbox-label">
                <strong>显示网格背景</strong>
                <small>在画布中显示网格辅助线</small>
              </span>
            </label>
            
            <label class="checkbox-item">
              <input type="checkbox" v-model="settingsStore.notifications" @change="settingsStore.toggleNotifications" />
              <span class="checkbox-label">
                <strong>启用通知</strong>
                <small>显示系统通知和提醒</small>
              </span>
            </label>
            
            <label class="checkbox-item">
              <input type="checkbox" v-model="settingsStore.autoSave" @change="settingsStore.toggleAutoSave" />
              <span class="checkbox-label">
                <strong>自动保存</strong>
                <small>自动保存更改的数据</small>
              </span>
            </label>
            
            <label class="checkbox-item">
              <input type="checkbox" v-model="settingsStore.autoBackup" @change="settingsStore.toggleAutoBackup" />
              <span class="checkbox-label">
                <strong>自动备份</strong>
                <small>定期备份应用数据</small>
              </span>
            </label>
          </div>
        </div>
        
        <!-- 数据管理 -->
        <div v-if="activeTab === 'data'" class="settings-section">
          <div class="section-header">
            <div class="search-icon">📊</div>
            <span>数据管理</span>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">导出选项</div>
            <div class="checkbox-group">
              <label class="checkbox-item">
                <input type="checkbox" v-model="localExportOptions.includeHistory" />
                <span class="checkbox-label">包含历史记录</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="localExportOptions.includeDependencies" />
                <span class="checkbox-label">包含任务依赖关系</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="localExportOptions.includeModules" />
                <span class="checkbox-label">包含模块信息</span>
              </label>
            </div>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">数据统计</div>
            <div class="data-stats">
              <div class="stat-row">
                <span class="stat-label">总任务数:</span>
                <span class="stat-value">{{ taskStore.tasks.length }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">模块数:</span>
                <span class="stat-value">{{ taskStore.modules.length }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">依赖关系:</span>
                <span class="stat-value">{{ taskStore.dependencies.length }}</span>
              </div>
            </div>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">操作</div>
            <div class="action-buttons">
              <button @click="$emit('export')" class="action-btn primary">
                📤 导出数据
              </button>
              <button @click="$emit('backup')" class="action-btn">
                💾 备份管理
              </button>
              <button @click="handleClearCache" class="action-btn warning">
                🗑️ 清除缓存
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Footer -->
      <div class="palette-footer">
        <div class="footer-actions">
          <button @click="handleClose" class="footer-btn">取消</button>
          <button @click="handleSave" class="footer-btn primary">保存设置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useTaskStore } from '@/stores/tasks'

interface Props {
  modelValue: boolean
  aiFeatures?: {
    textParsing: boolean
    subtaskGeneration: boolean
    similarityDetection: boolean
    weeklyReports: boolean
    riskAnalysis: boolean
    themeIslands: boolean
  }
  exportOptions?: {
    includeHistory: boolean
    includeDependencies: boolean
    includeModules: boolean
  }
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'export'): void
  (e: 'backup'): void
  (e: 'save', settings: any): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  aiFeatures: () => ({
    textParsing: false,
    subtaskGeneration: false,
    similarityDetection: false,
    weeklyReports: false,
    riskAnalysis: false,
    themeIslands: false
  }),
  exportOptions: () => ({
    includeHistory: true,
    includeDependencies: true,
    includeModules: true
  })
})

const emit = defineEmits<Emits>()

const settingsStore = useSettingsStore()
const taskStore = useTaskStore()

const visible = ref(props.modelValue)
const activeTab = ref('shortcuts')

const settingsTabs = ref([
  { key: 'shortcuts', label: '快捷键', icon: '⌨️' },
  { key: 'ai', label: 'AI设置', icon: '🤖' },
  { key: 'interface', label: '界面', icon: '🎨' },
  { key: 'data', label: '数据管理', icon: '📊' }
])

const localAiFeatures = reactive({ ...props.aiFeatures })
const localExportOptions = reactive({ ...props.exportOptions })

watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

function handleOverlayClick() {
  handleClose()
}

function handleClose() {
  visible.value = false
}

function handleSave() {
  const settings = {
    aiFeatures: localAiFeatures,
    exportOptions: localExportOptions
  }
  emit('save', settings)
  settingsStore.saveSettings()
  visible.value = false
}

function handleClearCache() {
  localStorage.clear()
  // 显示成功消息
  console.log('Cache cleared successfully')
}

function getShortcutName(key: string): string {
  const names: Record<string, string> = {
    commandPalette: '命令面板',
    quickAdd: '快速添加',
    search: '搜索',
    save: '保存',
    undo: '撤销',
    redo: '重做',
    delete: '删除',
    selectAll: '全选',
    copy: '复制',
    paste: '粘贴',
    newModule: '新建模块',
    export: '导出',
    import: '导入',
    toggleGrid: '切换网格',
    toggleSidebar: '切换侧边栏',
    zoomIn: '放大',
    zoomOut: '缩小',
    resetZoom: '重置缩放',
    autoArrange: '自动排列',
    settings: '设置'
  }
  return names[key] || key
}
</script>

<style scoped>
/* Command Palette Style Overlays */
.command-palette-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(12px);
  z-index: 2000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 10vh;
  animation: overlayFadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes overlayFadeIn {
  from {
    opacity: 0;
    backdrop-filter: blur(0px);
  }
  to {
    opacity: 1;
    backdrop-filter: blur(12px);
  }
}

/* Enhanced Main Palette Container */
.command-palette.settings-dialog {
  width: 640px;
  max-width: 90vw;
  max-height: 80vh;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 20px;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.15),
    0 8px 32px rgba(102, 126, 234, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 0.8);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: paletteSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes paletteSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Header */
.search-container {
  position: relative;
  display: flex;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%);
}

.search-icon {
  color: rgba(102, 126, 234, 0.7);
  font-size: 20px;
  margin-right: 16px;
  flex-shrink: 0;
}

.view-title {
  flex: 1;
  font-size: 16px;
  color: #1a202c;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.5;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  font-size: 18px;
  color: rgba(102, 126, 234, 0.6);
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.close-button:hover {
  background: rgba(102, 126, 234, 0.1);
  color: rgba(102, 126, 234, 0.9);
}

/* Settings Tabs */
.settings-tabs {
  display: flex;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
  background: rgba(248, 250, 252, 0.8);
}

.settings-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 3px solid transparent;
}

.settings-tab:hover {
  background: rgba(102, 126, 234, 0.05);
}

.settings-tab.active {
  background: rgba(102, 126, 234, 0.1);
  border-bottom-color: rgba(102, 126, 234, 0.6);
}

.tab-icon {
  font-size: 16px;
}

.tab-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.settings-tab.active .tab-label {
  color: rgba(102, 126, 234, 0.9);
  font-weight: 600;
}

/* Settings Content */
.results-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%);
}

.settings-section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  font-size: 14px;
  font-weight: 700;
  color: rgba(102, 126, 234, 0.8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.setting-item {
  margin-bottom: 24px;
}

.setting-label {
  font-size: 15px;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 12px;
}

.setting-control {
  margin-top: 8px;
}

.setting-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.8);
  transition: all 0.3s ease;
}

.setting-input:focus {
  outline: none;
  border-color: rgba(102, 126, 234, 0.5);
  background: rgba(255, 255, 255, 1);
}

.setting-hint {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
}

/* Radio and Checkbox Groups */
.radio-group, .checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.radio-item, .checkbox-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  padding: 12px;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.radio-item:hover, .checkbox-item:hover {
  background: rgba(102, 126, 234, 0.05);
}

.radio-item input[type="radio"], 
.checkbox-item input[type="checkbox"] {
  margin: 0;
  width: 16px;
  height: 16px;
  accent-color: rgba(102, 126, 234, 0.8);
}

.checkbox-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.checkbox-label strong {
  font-size: 14px;
  color: #1a202c;
}

.checkbox-label small {
  font-size: 12px;
  color: #64748b;
}

/* Shortcuts List */
.shortcuts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shortcut-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 12px;
}

.shortcut-name {
  font-size: 14px;
  color: #374151;
}

.shortcut-key {
  background: rgba(102, 126, 234, 0.1);
  color: rgba(102, 126, 234, 0.8);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

/* Data Stats */
.data-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 12px;
}

.stat-label {
  font-size: 14px;
  color: #374151;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: rgba(102, 126, 234, 0.8);
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 12px 20px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.8);
  color: #374151;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn:hover {
  background: rgba(102, 126, 234, 0.05);
  border-color: rgba(102, 126, 234, 0.4);
}

.action-btn.primary {
  background: rgba(102, 126, 234, 0.1);
  color: rgba(102, 126, 234, 0.9);
  border-color: rgba(102, 126, 234, 0.3);
}

.action-btn.warning {
  background: rgba(245, 158, 11, 0.1);
  color: rgba(245, 158, 11, 0.9);
  border-color: rgba(245, 158, 11, 0.3);
}

/* Footer */
.palette-footer {
  padding: 20px 24px;
  border-top: 2px solid rgba(102, 126, 234, 0.1);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%);
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.footer-btn {
  padding: 12px 24px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.8);
  color: #374151;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.footer-btn:hover {
  background: rgba(102, 126, 234, 0.05);
  border-color: rgba(102, 126, 234, 0.4);
}

.footer-btn.primary {
  background: rgba(102, 126, 234, 0.8);
  color: white;
  border-color: rgba(102, 126, 234, 0.8);
}

.footer-btn.primary:hover {
  background: rgba(102, 126, 234, 1);
  border-color: rgba(102, 126, 234, 1);
}

/* Responsive Design */
@media (max-width: 768px) {
  .command-palette.settings-dialog {
    width: 95vw;
    max-height: 85vh;
  }
  
  .settings-tabs {
    flex-wrap: wrap;
  }
  
  .settings-tab {
    min-width: 50%;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .footer-actions {
    flex-direction: column;
  }
}
</style>