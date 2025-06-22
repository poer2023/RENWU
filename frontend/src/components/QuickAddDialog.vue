<template>
  <el-dialog 
    v-model="visible" 
    title="快速添加任务" 
    width="500px"
    @close="handleClose"
  >
    <el-form>
      <el-form-item label="标题">
        <el-input 
          v-model="form.title" 
          placeholder="任务标题"
          @keyup.enter="handleSubmit"
        />
      </el-form-item>
      <el-form-item label="描述">
        <el-input 
          v-model="form.description" 
          type="textarea" 
          :rows="3"
          placeholder="任务描述"
        />
      </el-form-item>
      <el-form-item label="优先级">
        <el-select v-model="form.urgency" class="w-full">
          <el-option label="P0 - 紧急" :value="0" />
          <el-option label="P1 - 高" :value="1" />
          <el-option label="P2 - 中" :value="2" />
          <el-option label="P3 - 低" :value="3" />
          <el-option label="P4 - 待办" :value="4" />
        </el-select>
      </el-form-item>
      <el-form-item label="模块">
        <el-select v-model="form.module_id" class="w-full" clearable>
          <el-option
            v-for="module in modules"
            :key="module.id"
            :label="module.name"
            :value="module.id"
          />
        </el-select>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit">创建任务</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElDialog, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElButton } from 'element-plus'

interface Props {
  modelValue: boolean
  modules: any[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'submit': [task: any]
}>()

const visible = ref(props.modelValue)

const form = ref({
  title: '',
  description: '',
  urgency: 2,
  module_id: null as number | null
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
    title: '',
    description: '',
    urgency: 2,
    module_id: null
  }
  visible.value = false
}

function handleSubmit() {
  if (!form.value.title.trim()) {
    return
  }
  
  emit('submit', { ...form.value })
  handleClose()
}
</script>

<style scoped>
.w-full {
  width: 100%;
}
</style> 