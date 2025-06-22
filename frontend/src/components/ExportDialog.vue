<template>
  <el-dialog 
    v-model="visible" 
    title="导出数据" 
    width="600px"
    @close="handleClose"
  >
    <el-form label-position="top">
      <el-form-item label="导出格式">
        <el-select v-model="form.format" style="width: 100%;">
          <el-option label="JSON - 结构化数据" value="json" />
          <el-option label="Markdown - 文档格式" value="markdown" />
          <el-option label="CSV - 表格数据" value="csv" />
          <el-option label="Excel - 电子表格" value="excel" />
          <el-option label="PDF - 报告文档" value="pdf" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="筛选条件">
        <div class="export-filters">
          <el-select 
            v-model="form.filterModule" 
            placeholder="按模块筛选（可选）"
            clearable
            style="width: 48%;"
          >
            <el-option
              v-for="module in modules"
              :key="module.id"
              :label="module.name"
              :value="module.id"
            />
          </el-select>
          
          <el-select 
            v-model="form.filterPriority" 
            placeholder="按优先级筛选（可选）"
            clearable
            style="width: 48%;"
          >
            <el-option label="P0 - 紧急" :value="0" />
            <el-option label="P1 - 高" :value="1" />
            <el-option label="P2 - 中" :value="2" />
            <el-option label="P3 - 低" :value="3" />
            <el-option label="P4 - 待办" :value="4" />
          </el-select>
        </div>
      </el-form-item>
      
      <el-form-item label="包含内容">
        <div class="export-content-options">
          <el-checkbox v-model="form.includeHistory">
            历史记录
          </el-checkbox>
          <el-checkbox v-model="form.includeDependencies">
            任务依赖关系
          </el-checkbox>
          <el-checkbox v-model="form.includeModules">
            模块信息
          </el-checkbox>
        </div>
      </el-form-item>
      
      <el-form-item label="预览信息">
        <div class="export-preview">
          <div class="preview-item">
            <span class="preview-label">将导出任务数:</span>
            <span class="preview-value">{{ filteredTaskCount }}</span>
          </div>
          <div class="preview-item">
            <span class="preview-label">预计文件大小:</span>
            <span class="preview-value">{{ estimatedFileSize }}</span>
          </div>
        </div>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button 
        type="primary" 
        @click="handleExport" 
        :loading="loading"
      >
        导出文件
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElDialog, ElForm, ElFormItem, ElSelect, ElOption, ElButton, ElCheckbox } from 'element-plus'
import { type Task } from '@/stores/tasks'

interface Props {
  modelValue: boolean
  tasks: Task[]
  modules: any[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'export': [options: any]
}>()

const visible = ref(props.modelValue)

const form = ref({
  format: 'json',
  filterModule: null as number | null,
  filterPriority: null as number | null,
  includeHistory: true,
  includeDependencies: true,
  includeModules: true
})

// Watch for external changes
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

// Watch for internal changes
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// Computed
const filteredTaskCount = computed(() => {
  let count = props.tasks.length
  
  if (form.value.filterModule !== null) {
    count = props.tasks.filter(t => t.module_id === form.value.filterModule).length
  }
  
  if (form.value.filterPriority !== null) {
    count = props.tasks.filter(t => t.urgency === form.value.filterPriority).length
  }
  
  return count
})

const estimatedFileSize = computed(() => {
  const baseSize = filteredTaskCount.value * 500 // ~500 bytes per task
  const multiplier = form.value.format === 'pdf' ? 3 : 
                    form.value.format === 'excel' ? 2 : 1
  const totalBytes = baseSize * multiplier
  
  if (totalBytes < 1024) return `${totalBytes} B`
  if (totalBytes < 1024 * 1024) return `${(totalBytes / 1024).toFixed(1)} KB`
  return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`
})

// Methods
function handleClose() {
  visible.value = false
}

function handleExport() {
  emit('export', { ...form.value })
}
</script>

<style scoped>
.export-filters {
  display: flex;
  gap: 16px;
}

.export-content-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.export-preview {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 16px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-item:last-child {
  margin-bottom: 0;
}

.preview-label {
  font-size: 14px;
  color: var(--text-muted);
}

.preview-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}
</style> 