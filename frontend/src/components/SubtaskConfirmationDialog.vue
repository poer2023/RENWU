<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="确认子任务"
    width="800px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    class="subtask-confirmation-dialog"
  >
    <div class="dialog-content">
      <!-- 父任务信息 -->
      <div class="parent-task-info">
        <h4>父任务: {{ parentTask?.title }}</h4>
        <p v-if="parentTask?.description" class="parent-description">
          {{ parentTask.description }}
        </p>
        <div class="priority-info">
          <span class="priority-label">父任务优先级: P{{ parentTask?.urgency || 2 }}</span>
          <span class="arrow">→</span>
          <span class="child-priority-label">子任务优先级: P{{ Math.min((parentTask?.urgency || 2) + 1, 4) }}</span>
        </div>
      </div>

      <!-- AI生成信息 -->
      <div class="ai-info">
        <div class="ai-meta">
          <span class="model-badge">{{ generationData?.model_used || 'Gemini Pro' }}</span>
          <span class="cost-info">成本: ${{ (generationData?.cost || 0).toFixed(4) }}</span>
          <span class="token-info">
            Token: {{ generationData?.tokens_in || 0 }}↗ / {{ generationData?.tokens_out || 0 }}↙
          </span>
        </div>
      </div>

      <!-- 子任务列表 -->
      <div class="subtasks-container">
        <h5>生成的子任务 ({{ editableSuggestions.length }}个)</h5>
        
        <div 
          class="subtasks-list"
          @drop="handleDrop"
          @dragover.prevent
          @dragenter.prevent
        >
          <TemporarySubtaskCard
            v-for="(suggestion, index) in editableSuggestions"
            :key="`suggestion-${index}`"
            :suggestion="suggestion"
            :index="index"
            @update="handleSubtaskUpdate"
            @delete="handleSubtaskDelete"
            @drag-start="handleDragStart"
            @drag-end="handleDragEnd"
          />
        </div>

        <!-- 空状态 -->
        <div v-if="editableSuggestions.length === 0" class="empty-state">
          <p>没有子任务建议</p>
          <el-button @click="$emit('update:visible', false)" size="small">
            关闭
          </el-button>
        </div>
      </div>

      <!-- 批量操作 -->
      <div v-if="editableSuggestions.length > 0" class="batch-actions">
        <el-button 
          @click="selectAll" 
          size="small"
          :disabled="allSelected"
        >
          全选
        </el-button>
        <el-button 
          @click="selectNone" 
          size="small"
          :disabled="noneSelected"
        >
          全不选
        </el-button>
        <el-button 
          @click="deleteSelected" 
          size="small" 
          type="danger"
          :disabled="noneSelected"
        >
          删除选中 ({{ selectedCount }})
        </el-button>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <div class="footer-info">
          <span class="selection-info">
            已选择 {{ selectedCount }} / {{ editableSuggestions.length }} 个子任务
          </span>
        </div>
        <div class="footer-actions">
          <el-button @click="handleReject" size="small">
            拒绝全部
          </el-button>
          <el-button 
            @click="handleConfirm" 
            type="primary" 
            size="small"
            :disabled="selectedCount === 0"
            :loading="isConfirming"
          >
            确认创建 ({{ selectedCount }})
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElDialog, ElButton, ElMessage } from 'element-plus'
import TemporarySubtaskCard from './TemporarySubtaskCard.vue'

interface SubtaskSuggestion {
  title: string
  description: string
  order: number
  urgency?: number
  selected?: boolean
}

interface GenerationData {
  model_used: string
  tokens_in: number
  tokens_out: number
  cost: number
  log_id: number
}

interface ParentTask {
  id: number
  title: string
  description?: string
  urgency?: number
}

interface Props {
  visible: boolean
  suggestions: SubtaskSuggestion[]
  generationData?: GenerationData
  parentTask?: ParentTask
}

const props = withDefaults(defineProps<Props>(), {
  suggestions: () => []
})

const emit = defineEmits<{
  'update:visible': [visible: boolean]
  confirm: [acceptedSuggestions: SubtaskSuggestion[], logId: number]
  reject: [logId: number]
}>()

// 本地状态
const editableSuggestions = ref<SubtaskSuggestion[]>([])
const isConfirming = ref(false)
const draggedIndex = ref<number | null>(null)

// 计算属性
const selectedCount = computed(() => 
  editableSuggestions.value.filter(s => s.selected).length
)

const allSelected = computed(() => 
  editableSuggestions.value.length > 0 && 
  editableSuggestions.value.every(s => s.selected)
)

const noneSelected = computed(() => 
  selectedCount.value === 0
)

// 监听props变化
watch(() => props.suggestions, (newSuggestions) => {
  // 计算子任务的默认优先级（比父任务低一级，但不超过4）
  const parentUrgency = props.parentTask?.urgency || 2
  const defaultChildUrgency = Math.min(parentUrgency + 1, 4)
  
  editableSuggestions.value = newSuggestions.map((suggestion, index) => ({
    ...suggestion,
    selected: true, // 默认全选
    order: index + 1,
    urgency: suggestion.urgency || defaultChildUrgency // 使用计算后的优先级
  }))
}, { immediate: true, deep: true })

// 子任务操作
function handleSubtaskUpdate(index: number, updatedSuggestion: SubtaskSuggestion) {
  if (index >= 0 && index < editableSuggestions.value.length) {
    editableSuggestions.value[index] = {
      ...updatedSuggestion,
      selected: editableSuggestions.value[index].selected
    }
  }
}

function handleSubtaskDelete(index: number) {
  editableSuggestions.value.splice(index, 1)
  // 重新排序
  editableSuggestions.value.forEach((suggestion, idx) => {
    suggestion.order = idx + 1
  })
}

// 拖拽排序
function handleDragStart(index: number) {
  draggedIndex.value = index
}

function handleDragEnd() {
  draggedIndex.value = null
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  
  if (draggedIndex.value === null) return
  
  const dropIndex = findDropIndex(event.clientY)
  if (dropIndex !== -1 && dropIndex !== draggedIndex.value) {
    const draggedItem = editableSuggestions.value[draggedIndex.value]
    editableSuggestions.value.splice(draggedIndex.value, 1)
    editableSuggestions.value.splice(dropIndex, 0, draggedItem)
    
    // 重新排序
    editableSuggestions.value.forEach((suggestion, index) => {
      suggestion.order = index + 1
    })
  }
  
  draggedIndex.value = null
}

function findDropIndex(clientY: number): number {
  const subtaskElements = document.querySelectorAll('.temp-subtask-card')
  for (let i = 0; i < subtaskElements.length; i++) {
    const rect = subtaskElements[i].getBoundingClientRect()
    if (clientY < rect.top + rect.height / 2) {
      return i
    }
  }
  return subtaskElements.length
}

// 批量操作
function selectAll() {
  editableSuggestions.value.forEach(suggestion => {
    suggestion.selected = true
  })
}

function selectNone() {
  editableSuggestions.value.forEach(suggestion => {
    suggestion.selected = false
  })
}

function deleteSelected() {
  editableSuggestions.value = editableSuggestions.value.filter(s => !s.selected)
  // 重新排序
  editableSuggestions.value.forEach((suggestion, index) => {
    suggestion.order = index + 1
  })
}

// 确认/拒绝操作
async function handleConfirm() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请至少选择一个子任务')
    return
  }

  isConfirming.value = true
  
  try {
    const acceptedSuggestions = editableSuggestions.value
      .filter(s => s.selected)
      .map(s => ({
        title: s.title,
        description: s.description,
        order: s.order,
        urgency: s.urgency || 2
      }))

    emit('confirm', acceptedSuggestions, props.generationData?.log_id || 0)
  } catch (error) {
    console.error('确认子任务失败:', error)
    ElMessage.error('确认子任务失败')
  } finally {
    isConfirming.value = false
  }
}

function handleReject() {
  emit('reject', props.generationData?.log_id || 0)
}
</script>

<style scoped>
.subtask-confirmation-dialog :deep(.el-dialog) {
  border-radius: 12px;
}

.subtask-confirmation-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px 12px 0 0;
  padding: 16px 20px;
}

.subtask-confirmation-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
}

.subtask-confirmation-dialog :deep(.el-dialog__close) {
  color: white;
}

.dialog-content {
  max-height: 70vh;
  overflow-y: auto;
  padding: 0 4px;
}

/* 父任务信息 */
.parent-task-info {
  background: #f8f9fa;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  border-left: 4px solid #1890ff;
}

.parent-task-info h4 {
  margin: 0 0 8px 0;
  color: #1890ff;
  font-weight: 600;
}

.parent-description {
  margin: 0 0 8px 0;
  color: #666;
  font-size: 13px;
  line-height: 1.4;
}

.priority-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 500;
}

.priority-label {
  color: #1890ff;
  background: rgba(24, 144, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.arrow {
  color: #666;
}

.child-priority-label {
  color: #52c41a;
  background: rgba(82, 196, 26, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

/* AI信息 */
.ai-info {
  margin-bottom: 16px;
}

.ai-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 12px;
}

.model-badge {
  background: linear-gradient(45deg, #4CAF50, #45a049);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.cost-info {
  color: #fa8c16;
  font-weight: 500;
}

.token-info {
  color: #666;
}

/* 子任务容器 */
.subtasks-container h5 {
  margin: 0 0 12px 0;
  color: #333;
  font-weight: 600;
}

.subtasks-list {
  min-height: 100px;
  padding: 8px;
  border: 2px dashed transparent;
  border-radius: 8px;
  transition: border-color 0.2s;
}

.subtasks-list:hover {
  border-color: #e0e0e0;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.empty-state p {
  margin: 0 0 16px 0;
  font-size: 14px;
}

/* 批量操作 */
.batch-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fafafa;
  border-radius: 0 0 12px 12px;
  margin: 0 -20px -20px -20px;
}

.footer-info {
  color: #666;
  font-size: 13px;
}

.selection-info {
  font-weight: 500;
}

.footer-actions {
  display: flex;
  gap: 8px;
}

/* 响应式 */
@media (max-width: 768px) {
  .subtask-confirmation-dialog :deep(.el-dialog) {
    width: 95% !important;
    margin: 10px auto;
  }
  
  .dialog-content {
    max-height: 60vh;
  }
  
  .dialog-footer {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .footer-actions {
    justify-content: center;
  }
}
</style>