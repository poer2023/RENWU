<template>
  <el-dialog 
    v-model="visible" 
    title="AI智能解析" 
    width="600px"
    @close="handleClose"
  >
    <el-form>
      <el-form-item label="要解析的文本">
        <el-input 
          v-model="text" 
          type="textarea" 
          :rows="8"
          placeholder="粘贴要解析的文本，AI将自动识别并创建任务..."
          @keydown.ctrl.enter="handleParse"
          @keydown.meta.enter="handleParse"
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button 
        type="primary" 
        @click="handleParse" 
        :loading="loading"
        :disabled="!text.trim()"
      >
        解析任务
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElDialog, ElForm, ElFormItem, ElInput, ElButton } from 'element-plus'

interface Props {
  modelValue: boolean
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'parse': [text: string]
}>()

const visible = ref(props.modelValue)
const text = ref('')

// Watch for external changes
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

// Watch for internal changes
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

function handleClose() {
  text.value = ''
  visible.value = false
}

function handleParse() {
  if (!text.value.trim()) return
  emit('parse', text.value)
}

// Expose method to clear text after successful parse
function clearText() {
  text.value = ''
}

defineExpose({
  clearText
})
</script> 