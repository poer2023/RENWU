<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="🔍 发现相似任务"
    width="600px"
    :close-on-click-modal="false"
  >
    <div class="similar-tasks-content">
      <div class="dialog-header">
        <p class="description">
          系统检测到以下任务与您要创建的任务相似，请选择操作：
        </p>
        <div class="new-task-preview">
          <strong>新任务：</strong>{{ newTaskTitle }}
          <div v-if="newTaskDescription" class="task-desc">
            {{ newTaskDescription }}
          </div>
        </div>
      </div>

      <div class="similar-tasks-list" v-if="similarTasks.length > 0">
        <h4>相似任务 ({{ similarTasks.length }})</h4>
        <div 
          v-for="similar in similarTasks" 
          :key="similar.task.id"
          class="similar-task-item"
        >
          <div class="task-info">
            <div class="task-header">
              <span class="task-title">{{ similar.task.title }}</span>
              <div class="similarity-badges">
                <el-tag 
                  :color="getMatchTypeColor(similar.match_type)" 
                  size="small"
                  effect="dark"
                >
                  {{ getMatchTypeLabel(similar.match_type) }}
                </el-tag>
                <el-tag size="small" type="info">
                  {{ getSimilarityPercentage(similar.similarity_score) }}
                </el-tag>
              </div>
            </div>
            <div v-if="similar.task.description" class="task-description">
              {{ similar.task.description }}
            </div>
            <div class="task-meta">
              <span class="priority">P{{ similar.task.urgency }}</span>
              <span class="date">{{ formatDate(similar.task.created_at) }}</span>
            </div>
          </div>
          <div class="task-actions">
            <el-button 
              size="small" 
              @click="viewTask(similar.task)"
              :icon="View"
            >
              查看
            </el-button>
            <el-button 
              size="small" 
              type="primary"
              @click="linkTasks(similar.task)"
              :icon="Link"
            >
              关联
            </el-button>
          </div>
        </div>
      </div>

      <div class="suggestions" v-if="suggestions.length > 0">
        <h4>建议操作</h4>
        <ul class="suggestion-list">
          <li v-for="(suggestion, index) in suggestions" :key="index">
            {{ suggestion }}
          </li>
        </ul>
      </div>

      <div class="no-similar" v-if="similarTasks.length === 0">
        <el-empty 
          description="未发现相似任务"
          :image-size="60"
        />
      </div>
    </div>

    <template #footer>
      <div class="dialog-actions">
        <el-button @click="handleCancel">取消创建</el-button>
        <el-button @click="handleIgnore">忽略相似，继续创建</el-button>
        <el-button 
          type="primary" 
          @click="handleCreateAnyway"
          :disabled="similarTasks.length === 0"
        >
          创建新任务
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElDialog, ElButton, ElTag, ElEmpty } from 'element-plus'
import { View, Link } from '@element-plus/icons-vue'
import { useSimilarityDetection, type SimilarTask } from '@/composables/useSimilarityDetection'

interface Props {
  visible: boolean
  newTaskTitle: string
  newTaskDescription?: string
  similarTasks: SimilarTask[]
  suggestions: string[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'cancel': []
  'ignore': []
  'create': []
  'view-task': [task: any]
  'link-tasks': [task: any]
}>()

const { getMatchTypeLabel, getMatchTypeColor, getSimilarityPercentage } = useSimilarityDetection()

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const viewTask = (task: any) => {
  emit('view-task', task)
}

const linkTasks = (task: any) => {
  emit('link-tasks', task)
}

const handleCancel = () => {
  emit('update:visible', false)
  emit('cancel')
}

const handleIgnore = () => {
  emit('update:visible', false)
  emit('ignore')
}

const handleCreateAnyway = () => {
  emit('update:visible', false)
  emit('create')
}
</script>

<style scoped>
.similar-tasks-content {
  max-height: 500px;
  overflow-y: auto;
}

.dialog-header {
  margin-bottom: 20px;
}

.description {
  color: #666;
  margin-bottom: 12px;
  line-height: 1.5;
}

.new-task-preview {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.task-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.similar-tasks-list h4,
.suggestions h4 {
  margin: 20px 0 12px 0;
  font-size: 14px;
  color: #333;
}

.similar-task-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #eee;
  border-radius: 8px;
  background: #fafafa;
  transition: border-color 0.2s;
}

.similar-task-item:hover {
  border-color: #409eff;
}

.task-info {
  flex: 1;
  margin-right: 12px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-title {
  font-weight: 600;
  color: #333;
  flex: 1;
  margin-right: 12px;
}

.similarity-badges {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.task-description {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
  line-height: 1.4;
}

.task-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #999;
}

.priority {
  padding: 2px 6px;
  background: #f0f0f0;
  border-radius: 4px;
  font-weight: 500;
}

.task-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.suggestions {
  margin-top: 20px;
  padding: 16px;
  background: #fff7e6;
  border-radius: 6px;
  border: 1px solid #ffd666;
}

.suggestion-list {
  margin: 0;
  padding-left: 20px;
}

.suggestion-list li {
  margin-bottom: 8px;
  color: #d48806;
  line-height: 1.4;
}

.no-similar {
  text-align: center;
  padding: 40px 20px;
}

.dialog-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* Element Plus tag customization */
:deep(.el-tag--dark) {
  border: none;
}
</style>