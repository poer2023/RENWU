<template>
  <div 
    :class="[
      'temp-subtask-card',
      `urgency-${suggestion.urgency}`,
      { 'dragging': isDragging }
    ]"
    :style="{ 
      opacity: 0.4,
      border: '2px dashed #ccc',
      position: 'relative'
    }"
    draggable="true"
    @dragstart="handleDragStart"
    @dragend="handleDragEnd"
  >
    <!-- 临时标识 -->
    <div class="temp-indicator">
      <span class="temp-badge">待确认</span>
    </div>

    <!-- 拖拽排序句柄 -->
    <div class="drag-handle" title="拖拽排序">
      ⋮⋮
    </div>

    <!-- 标题编辑 -->
    <div class="subtask-title-section">
      <el-input
        v-model="localTitle"
        @input="handleTitleChange"
        placeholder="子任务标题..."
        size="small"
        class="title-input"
      />
    </div>

    <!-- 描述编辑 -->
    <div class="subtask-description-section">
      <el-input
        v-model="localDescription"
        @input="handleDescriptionChange"
        type="textarea"
        :rows="2"
        placeholder="子任务描述..."
        size="small"
        class="description-input"
      />
    </div>

    <!-- 优先级选择 -->
    <div class="urgency-section">
      <el-select 
        v-model="localUrgency" 
        @change="handleUrgencyChange"
        size="small"
        class="urgency-select"
      >
        <el-option label="P0 - 紧急" :value="0" />
        <el-option label="P1 - 高优先级" :value="1" />
        <el-option label="P2 - 中优先级" :value="2" />
        <el-option label="P3 - 低优先级" :value="3" />
        <el-option label="P4 - 待处理" :value="4" />
      </el-select>
    </div>

    <!-- 操作按钮 -->
    <div class="temp-actions">
      <el-button 
        size="small" 
        type="danger" 
        @click="handleDelete"
        :icon="Delete"
        title="删除此子任务"
      />
    </div>

    <!-- 排序指示器 -->
    <div class="order-indicator">
      {{ suggestion.order }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElInput, ElSelect, ElOption, ElButton } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'

interface SubtaskSuggestion {
  title: string
  description: string
  order: number
  urgency?: number
}

interface Props {
  suggestion: SubtaskSuggestion
  index: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  update: [index: number, suggestion: SubtaskSuggestion]
  delete: [index: number]
  dragStart: [index: number]
  dragEnd: [index: number]
}>()

// 本地状态
const localTitle = ref(props.suggestion.title)
const localDescription = ref(props.suggestion.description)
const localUrgency = ref(props.suggestion.urgency || 2)
const isDragging = ref(false)

// 监听props变化同步本地状态
watch(() => props.suggestion, (newSuggestion) => {
  localTitle.value = newSuggestion.title
  localDescription.value = newSuggestion.description
  localUrgency.value = newSuggestion.urgency || 2
}, { deep: true })

// 事件处理
function handleTitleChange() {
  emitUpdate()
}

function handleDescriptionChange() {
  emitUpdate()
}

function handleUrgencyChange() {
  emitUpdate()
}

function emitUpdate() {
  const updatedSuggestion: SubtaskSuggestion = {
    title: localTitle.value,
    description: localDescription.value,
    order: props.suggestion.order,
    urgency: localUrgency.value
  }
  emit('update', props.index, updatedSuggestion)
}

function handleDelete() {
  emit('delete', props.index)
}

function handleDragStart(event: DragEvent) {
  isDragging.value = true
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', props.index.toString())
  }
  emit('dragStart', props.index)
}

function handleDragEnd() {
  isDragging.value = false
  emit('dragEnd', props.index)
}
</script>

<style scoped>
.temp-subtask-card {
  position: relative;
  min-width: 200px;
  min-height: 120px;
  padding: 12px;
  margin: 8px 0;
  border-radius: 8px;
  background: #ffffff;
  cursor: default;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.temp-subtask-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.temp-subtask-card.dragging {
  transform: rotate(2deg);
  opacity: 0.8 !important;
  z-index: 1000;
}

/* 临时标识 */
.temp-indicator {
  position: absolute;
  top: -8px;
  left: 8px;
  z-index: 10;
}

.temp-badge {
  background: linear-gradient(45deg, #ff9800, #f57c00);
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: bold;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* 拖拽句柄 */
.drag-handle {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 16px;
  height: 16px;
  cursor: grab;
  color: #999;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.drag-handle:hover {
  background: #f0f0f0;
  color: #666;
}

.drag-handle:active {
  cursor: grabbing;
}

/* 内容区域 */
.subtask-title-section {
  margin-bottom: 8px;
}

.subtask-description-section {
  margin-bottom: 8px;
}

.urgency-section {
  margin-bottom: 8px;
}

/* 输入框样式 */
.title-input :deep(.el-input__inner) {
  font-weight: 600;
  font-size: 13px;
}

.description-input :deep(.el-textarea__inner) {
  font-size: 12px;
  color: #666;
}

.urgency-select {
  width: 140px;
}

/* 操作按钮 */
.temp-actions {
  position: absolute;
  bottom: 4px;
  right: 4px;
}

/* 排序指示器 */
.order-indicator {
  position: absolute;
  bottom: 4px;
  left: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #1890ff;
  color: white;
  font-size: 11px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.8;
}

/* 优先级背景色 */
.urgency-0 { 
  background: rgba(255, 77, 79, 0.08);
  border-color: #ff4d4f;
}
.urgency-1 { 
  background: rgba(250, 140, 22, 0.08);
  border-color: #fa8c16;
}
.urgency-2 { 
  background: rgba(250, 219, 20, 0.08);
  border-color: #fadb14;
}
.urgency-3 { 
  background: rgba(82, 196, 26, 0.08);
  border-color: #52c41a;
}
.urgency-4 { 
  background: rgba(24, 144, 255, 0.08);
  border-color: #1890ff;
}

/* Element Plus 样式覆盖 */
:deep(.el-button--small) {
  padding: 4px 6px;
  font-size: 10px;
}

:deep(.el-input--small .el-input__inner) {
  height: 28px;
  line-height: 28px;
}

:deep(.el-select--small .el-input__inner) {
  height: 28px;
  line-height: 28px;
}
</style>