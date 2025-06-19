<template>
  <div class="debug-task-list">
    <h3>Debug Task List (Total: {{ tasks.length }})</h3>
    <div v-if="tasks.length === 0" class="no-tasks">
      No tasks available
    </div>
    <div v-else>
      <div 
        v-for="task in tasks" 
        :key="task.id" 
        class="debug-task-item"
      >
        <div><strong>ID:</strong> {{ task.id }}</div>
        <div><strong>Title:</strong> {{ task.title }}</div>
        <div><strong>Description:</strong> {{ task.description || 'No description' }}</div>
        <div><strong>Urgency:</strong> P{{ task.urgency }}</div>
        <div><strong>Created:</strong> {{ task.created_at }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { type Task } from '@/stores/tasks'

interface Props {
  tasks: Task[]
}

defineProps<Props>()
</script>

<style scoped>
.debug-task-list {
  padding: 20px;
  background: #f0f0f0;
  border: 2px solid #ccc;
  border-radius: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.debug-task-item {
  background: white;
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.no-tasks {
  color: #999;
  font-style: italic;
  text-align: center;
  padding: 20px;
}
</style> 