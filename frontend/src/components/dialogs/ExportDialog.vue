<template>
  <el-dialog
    v-model="visible"
    title="导出数据"
    width="600px"
    @close="handleClose"
  >
    <el-form label-position="top">
      <el-form-item label="导出格式">
        <el-radio-group v-model="exportFormat">
          <el-radio value="json">JSON</el-radio>
          <el-radio value="csv">CSV</el-radio>
          <el-radio value="markdown">Markdown</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="过滤条件">
        <div class="filter-options">
          <el-select 
            :model-value="filterModule || undefined"
            @update:model-value="(val) => filterModule = val === undefined ? null : val"
            placeholder="选择模块" 
            clearable
            style="width: 200px; margin-right: 16px;"
          >
            <el-option
              v-for="module in modules"
              :key="module.id"
              :label="module.name"
              :value="module.id"
            />
          </el-select>

          <el-select 
            :model-value="filterPriority ?? undefined"
            @update:model-value="(val) => filterPriority = val === undefined ? null : val"
            placeholder="选择优先级" 
            clearable
            style="width: 200px;"
          >
            <el-option label="P0 - 紧急" :value="0" />
            <el-option label="P1 - 高" :value="1" />
            <el-option label="P2 - 中" :value="2" />
            <el-option label="P3 - 低" :value="3" />
            <el-option label="P4 - 待办" :value="4" />
          </el-select>
        </div>
      </el-form-item>

      <el-form-item label="导出选项">
        <el-checkbox v-model="options.includeHistory">
          包含历史记录
        </el-checkbox>
        <el-checkbox v-model="options.includeDependencies">
          包含任务依赖关系
        </el-checkbox>
        <el-checkbox v-model="options.includeModules">
          包含模块信息
        </el-checkbox>
      </el-form-item>

      <el-form-item label="预览">
        <div class="export-preview">
          <p>将导出 {{ previewCount }} 个任务</p>
          <p v-if="filterModule">筛选模块：{{ getModuleName(filterModule) }}</p>
          <p v-if="filterPriority !== null">筛选优先级：P{{ filterPriority }}</p>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleExport" :loading="loading">
        导出
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElDialog, ElForm, ElFormItem, ElRadioGroup, ElRadio, ElSelect, ElOption, ElCheckbox, ElButton, ElMessage } from 'element-plus'
import { useTaskStore, type Module } from '@/stores/tasks'

interface Props {
  modelValue: boolean
  modules?: Module[]
}

const props = withDefaults(defineProps<Props>(), {
  modules: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const taskStore = useTaskStore()

const visible = ref(props.modelValue)
const loading = ref(false)

// Export settings
const exportFormat = ref('json')
const filterModule = ref<number | null>(null)
const filterPriority = ref<number | null>(null)

const options = ref({
  includeHistory: true,
  includeDependencies: true,
  includeModules: true
})

// Watch for external visibility changes
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

// Watch for internal visibility changes
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// Computed preview count
const previewCount = computed(() => {
  let tasks = taskStore.tasks
  
  if (filterModule.value !== null) {
    tasks = tasks.filter(t => t.module_id === filterModule.value)
  }
  
  if (filterPriority.value !== null) {
    tasks = tasks.filter(t => t.urgency === filterPriority.value)
  }
  
  return tasks.length
})

function getModuleName(moduleId: number): string {
  const module = props.modules.find(m => m.id === moduleId)
  return module?.name || '未知模块'
}

function handleClose() {
  visible.value = false
}

async function handleExport() {
  loading.value = true
  
  try {
    const params = new URLSearchParams({
      format: exportFormat.value,
      includeHistory: options.value.includeHistory.toString(),
      includeDependencies: options.value.includeDependencies.toString(),
      includeModules: options.value.includeModules.toString()
    })
    
    if (filterModule.value !== null) {
      params.append('module_id', filterModule.value.toString())
    }
    
    if (filterPriority.value !== null) {
      params.append('priority', filterPriority.value.toString())
    }
    
    const endpoint = exportFormat.value === 'markdown' ? '/api/export/markdown' : '/api/export/json'
    const response = await fetch(endpoint)
    
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      
      // Set filename based on format
      const timestamp = new Date().toISOString().split('T')[0]
      const extension = exportFormat.value === 'markdown' ? 'md' : exportFormat.value
      a.download = `taskwall_export_${timestamp}.${extension}`
      
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      ElMessage.success('数据导出成功')
      handleClose()
    } else {
      throw new Error('导出失败')
    }
  } catch (error) {
    console.error('Export failed:', error)
    ElMessage.error('数据导出失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.filter-options {
  display: flex;
  align-items: center;
}

.export-preview {
  padding: 16px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.export-preview p {
  margin: 4px 0;
  color: #666;
}

.export-preview p:first-child {
  font-weight: bold;
  color: #333;
}
</style> 