<template>
  <el-dialog
    v-model="visible"
    title="备份管理"
    width="600px"
    @close="handleClose"
  >
    <el-tabs>
      <el-tab-pane label="手动备份" name="manual">
        <el-form label-position="top">
          <el-form-item label="备份状态">
            <div class="backup-status">
              <el-alert
                v-if="backupStatus"
                :title="backupStatus"
                type="info"
                :closable="false"
                style="margin-bottom: 16px;"
              />
              <el-button 
                @click="createManualBackup" 
                type="primary" 
                :loading="loading"
                style="width: 100%;"
              >
                立即创建备份
              </el-button>
            </div>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      
      <el-tab-pane label="备份历史" name="history">
        <div class="backup-history">
          <el-button @click="loadBackupHistory" size="small" style="margin-bottom: 16px;">
            刷新历史
          </el-button>
          <div v-if="backupHistory.length === 0" class="empty-history">
            <p>暂无备份历史</p>
          </div>
          <div v-else class="history-list">
            <div 
              v-for="backup in backupHistory" 
              :key="backup.filename"
              class="history-item"
            >
              <div class="backup-info">
                <strong>{{ backup.filename }}</strong>
                <p class="backup-date">{{ backup.created_at || '未知日期' }}</p>
              </div>
              <div class="backup-actions">
                <el-button size="small" @click="downloadBackup(backup.filename)">
                  下载
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="自动备份" name="auto">
        <el-form label-position="top">
          <el-form-item label="自动备份设置">
            <el-checkbox v-model="settingsStore.autoBackup" @change="settingsStore.toggleAutoBackup">
              启用自动备份
            </el-checkbox>
            <small style="display: block; margin-top: 8px; color: var(--text-muted);">
              自动备份将在后台定期执行
            </small>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
    
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElDialog, ElTabs, ElTabPane, ElForm, ElFormItem, ElButton, ElAlert, ElCheckbox, ElMessage } from 'element-plus'
import { useSettingsStore } from '@/stores/settings'
import { useTaskStore } from '@/stores/tasks'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const settingsStore = useSettingsStore()
const taskStore = useTaskStore()

const visible = ref(props.modelValue)
const loading = ref(false)
const backupStatus = ref('')
const backupHistory = ref<any[]>([])

// Watch for external visibility changes
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal) {
    loadBackupHistory()
  }
})

// Watch for internal visibility changes
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

function handleClose() {
  visible.value = false
}

async function createManualBackup() {
  loading.value = true
  backupStatus.value = '正在创建备份...'
  
  try {
    const response = await fetch('/api/backup/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      backupStatus.value = `备份成功：${data.filename}`
      ElMessage.success('备份创建成功')
      await loadBackupHistory()
    } else {
      throw new Error('备份创建失败')
    }
  } catch (error) {
    console.error('Backup failed:', error)
    backupStatus.value = '备份失败'
    ElMessage.error('备份创建失败')
  } finally {
    loading.value = false
  }
}

async function loadBackupHistory() {
  try {
    const response = await fetch('/api/backup/list')
    if (response.ok) {
      backupHistory.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to load backup history:', error)
  }
}

async function downloadBackup(filename: string) {
  try {
    const response = await fetch(`/api/backup/download/${filename}`)
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      ElMessage.success('备份下载成功')
    } else {
      throw new Error('下载失败')
    }
  } catch (error) {
    console.error('Download failed:', error)
    ElMessage.error('备份下载失败')
  }
}
</script>

<style scoped>
.backup-status {
  width: 100%;
}

.backup-history {
  max-height: 400px;
  overflow-y: auto;
}

.empty-history {
  text-align: center;
  padding: 40px;
  color: #999;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.backup-info strong {
  display: block;
  margin-bottom: 4px;
}

.backup-date {
  font-size: 12px;
  color: #666;
  margin: 0;
}
</style> 