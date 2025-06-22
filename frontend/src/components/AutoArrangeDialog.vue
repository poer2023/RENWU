<template>
  <el-dialog 
    v-model="visible" 
    title="自动排列" 
    width="600px"
    @close="handleClose"
  >
    <el-form label-position="top">
      <el-form-item label="排列模式">
        <el-select v-model="form.mode" class="w-full">
          <el-option
            v-for="mode in arrangeModes"
            :key="mode.value"
            :label="`${mode.icon} ${mode.label}`"
            :value="mode.value"
          >
            <div>
              <span style="font-size: 16px; margin-right: 8px;">{{ mode.icon }}</span>
              <strong>{{ mode.label }}</strong>
              <div style="font-size: 12px; color: #999; margin-top: 2px;">
                {{ mode.description }}
              </div>
            </div>
          </el-option>
        </el-select>
      </el-form-item>

      <div class="form-row">
        <el-form-item label="间距" class="form-item-half">
          <el-input-number
            v-model="form.spacing"
            :min="5"
            :max="100"
            :step="5"
            class="w-full"
          />
        </el-form-item>
        
        <el-form-item label="边距" class="form-item-half">
          <el-input-number
            v-model="form.padding"
            :min="10"
            :max="200"
            :step="10"
            class="w-full"
          />
        </el-form-item>
      </div>

      <el-form-item v-if="form.mode === 'grid'" label="列数">
        <el-input-number
          v-model="form.columns"
          :min="1"
          :max="10"
          class="w-full"
        />
      </el-form-item>

      <el-form-item>
        <el-checkbox v-model="form.animated">
          使用动画过渡
        </el-checkbox>
      </el-form-item>

      <el-form-item>
        <el-checkbox v-model="form.groupByModule">
          按模块分组
        </el-checkbox>
      </el-form-item>

      <el-form-item>
        <el-checkbox v-model="form.sortByPriority">
          按优先级排序
        </el-checkbox>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleArrange">立即排列</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElDialog, ElForm, ElFormItem, ElSelect, ElOption, ElButton, ElInputNumber, ElCheckbox } from 'element-plus'

interface ArrangeMode {
  value: string
  label: string
  icon: string
  description: string
}

interface Props {
  modelValue: boolean
  options: any
  arrangeModes: ArrangeMode[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'update:options': [options: any]
  'arrange': []
}>()

const visible = ref(props.modelValue)

const form = ref({
  mode: props.options?.mode || 'grid',
  spacing: props.options?.spacing || 20,
  padding: props.options?.padding || 50,
  columns: props.options?.columns || 4,
  animated: props.options?.animated !== false,
  groupByModule: props.options?.groupByModule || false,
  sortByPriority: props.options?.sortByPriority || false
})

// Watch for external changes
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

// Watch for internal changes
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// Watch form changes to update parent options
watch(form, (newVal) => {
  emit('update:options', { ...newVal })
}, { deep: true })

function handleClose() {
  visible.value = false
}

function handleArrange() {
  emit('arrange')
  visible.value = false
}
</script>

<style scoped>
.w-full {
  width: 100%;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-item-half {
  flex: 1;
}
</style> 