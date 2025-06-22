<template>
  <div class="task-card-body" @click.stop="handleClick">
    <div v-if="isEditing" class="edit-mode">
      <ElInput
        v-model="localDescription"
        type="textarea"
        :rows="3"
        placeholder="添加任务描述..."
        @blur="handleBlur"
        @keydown.enter.ctrl="$emit('save')"
        @keydown.esc="$emit('cancel')"
        @click.stop
      />
    </div>
    <div v-else-if="description" class="view-mode">
      <p class="task-description">{{ description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElInput } from 'element-plus'

interface Props {
  description: string
  isEditing: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:description': [value: string]
  save: []
  cancel: []
  input: [value: string]
}>()

const localDescription = ref(props.description)

watch(() => props.description, (newVal) => {
  localDescription.value = newVal
})

watch(localDescription, (newVal) => {
  emit('update:description', newVal)
  emit('input', newVal)
})

function handleClick(event: MouseEvent) {
  // 不阻止事件冒泡，让父元素处理点击
  // event.stopPropagation() // 移除这行
}

function handleBlur() {
  // 可以在这里添加自动保存逻辑
}
</script>

<style scoped>
.task-card-body {
  flex: 1;
  min-height: 0;
  padding: 8px 0;
  /* 确保不会拦截点击事件 */
  pointer-events: none;
}

.task-card-body > * {
  /* 子元素恢复点击事件 */
  pointer-events: auto;
}

.task-description {
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-secondary);
  margin: 0;
  word-wrap: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  /* 文本不可选中，避免影响拖拽 */
  user-select: none;
  /* 但是确保可以接收点击事件 */
  pointer-events: auto;
}

.edit-mode {
  width: 100%;
}

:deep(.el-textarea__inner) {
  font-size: 13px;
  line-height: 1.5;
  resize: vertical;
  min-height: 60px !important;
}
</style> 