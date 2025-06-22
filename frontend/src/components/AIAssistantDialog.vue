<template>
  <el-dialog 
    v-model="visible" 
    title="AI助手" 
    width="500px"
    @close="handleClose"
  >
    <el-form label-position="top">
      <el-form-item label="选择功能">
        <el-select v-model="form.action" placeholder="选择AI功能" style="width: 100%;">
          <el-option label="重写文本" value="rewrite" />
          <el-option label="添加表情" value="add-emoji" />
          <el-option label="总结内容" value="summarize" />
          <el-option label="创建子任务" value="make-subtasks" />
        </el-select>
      </el-form-item>
      <el-form-item label="输入内容">
        <el-input 
          v-model="form.content" 
          type="textarea" 
          :rows="4"
          placeholder="输入需要处理的文本..."
        />
      </el-form-item>
      <el-form-item label="上下文（可选）">
        <el-input 
          v-model="form.context" 
          type="textarea" 
          :rows="2"
          placeholder="提供额外的上下文信息..."
        />
      </el-form-item>
      <el-form-item v-if="result" label="结果">
        <el-input 
          v-model="result" 
          type="textarea" 
          :rows="6"
          readonly
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
      <el-button 
        type="primary" 
        @click="handleExecute" 
        :loading="loading"
        :disabled="!form.action || !form.content"
      >
        执行AI功能
      </el-button>
      <el-button 
        v-if="result" 
        @click="copyResult" 
        type="success"
      >
        复制结果
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElDialog, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElButton, ElMessage } from 'element-plus'

interface Props {
  modelValue: boolean
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'execute': [data: { action: string; content: string; context: string }]
}>()

const visible = ref(props.modelValue)
const result = ref('')

const form = ref({
  action: '',
  content: '',
  context: ''
})

// Watch for external changes
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

// Watch for internal changes
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

function handleClose() {
  // Reset form
  form.value = {
    action: '',
    content: '',
    context: ''
  }
  result.value = ''
  visible.value = false
}

async function handleExecute() {
  emit('execute', { ...form.value })
}

function copyResult() {
  navigator.clipboard.writeText(result.value).then(() => {
    ElMessage.success('结果已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// Expose method to set result
function setResult(text: string) {
  result.value = text
}

defineExpose({
  setResult
})
</script> 