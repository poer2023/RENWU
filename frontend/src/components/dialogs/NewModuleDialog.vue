<template>
  <el-dialog
    v-model="visible"
    title="新建模块"
    width="400px"
    @close="handleClose"
  >
    <el-form>
      <el-form-item label="名称">
        <el-input
          v-model="formData.name"
          placeholder="模块名称"
          @keydown.enter="handleSubmit"
        />
      </el-form-item>
      <el-form-item label="颜色">
        <el-color-picker v-model="formData.color" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">
        创建模块
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElDialog, ElForm, ElFormItem, ElInput, ElColorPicker, ElButton, ElMessage } from 'element-plus'
import { useTaskStore } from '@/stores/tasks'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'created': [module: { name: string; color: string }]
}>()

const taskStore = useTaskStore()

const visible = ref(props.modelValue)
const loading = ref(false)

// Form data
const formData = ref({
  name: '',
  color: '#409EFF' // Default color
})

// Watch for external visibility changes
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

// Watch for internal visibility changes
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// Reset form when dialog opens
watch(visible, (newVal) => {
  if (newVal) {
    resetForm()
  }
})

function resetForm() {
  formData.value = {
    name: '',
    color: '#409EFF'
  }
}

function handleClose() {
  visible.value = false
}

async function handleSubmit() {
  if (!formData.value.name.trim()) {
    ElMessage.warning('请输入模块名称')
    return
  }

  loading.value = true
  try {
    await taskStore.createModule({
      name: formData.value.name.trim(),
      color: formData.value.color
    })
    
    ElMessage.success('模块创建成功')
    
    // Emit the created module
    emit('created', {
      name: formData.value.name.trim(),
      color: formData.value.color
    })
    
    handleClose()
  } catch (error) {
    console.error('Failed to create module:', error)
    ElMessage.error('创建模块失败')
  } finally {
    loading.value = false
  }
}
</script> 