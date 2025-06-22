<template>
  <div class="priority-strip" :class="`priority-${priority}`"></div>
</template>

<script setup lang="ts">
interface Props {
  priority: number
}

defineProps<Props>()
</script>

<style scoped>
/* Enhanced Priority Border Strip */
.priority-strip {
  position: absolute;
  top: 0;
  left: 0;
  width: 5px;
  height: 100%;
  border-radius: 16px 0 0 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0.8;
  overflow: hidden;
}

/* Priority color gradients */
.priority-strip.priority-0 { 
  background: linear-gradient(180deg, #ff4d4f 0%, #cf1322 100%);
  box-shadow: inset 2px 0 4px rgba(207, 19, 34, 0.3);
}

.priority-strip.priority-1 { 
  background: linear-gradient(180deg, #fa8c16 0%, #d46b08 100%);
  box-shadow: inset 2px 0 4px rgba(212, 107, 8, 0.3);
}

.priority-strip.priority-2 { 
  background: linear-gradient(180deg, #1890ff 0%, #096dd9 100%);
  box-shadow: inset 2px 0 4px rgba(9, 109, 217, 0.3);
}

.priority-strip.priority-3 { 
  background: linear-gradient(180deg, #52c41a 0%, #389e0d 100%);
  box-shadow: inset 2px 0 4px rgba(56, 158, 13, 0.3);
}

.priority-strip.priority-4 { 
  background: linear-gradient(180deg, #722ed1 0%, #531dab 100%);
  box-shadow: inset 2px 0 4px rgba(83, 29, 171, 0.3);
}

/* Hover effect */
:global(.task-node:hover) .priority-strip {
  height: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

/* Selected state animation */
:global(.task-node.selected) .priority-strip {
  animation: priority-glow 2s infinite alternate;
}

@keyframes priority-glow {
  from {
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.2);
  }
  to {
    box-shadow: 0 0 16px rgba(59, 130, 246, 0.4);
  }
}

/* Shine effect */
.priority-strip::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s ease;
}

:global(.task-node:hover) .priority-strip::after {
  left: 100%;
}

/* Dark mode adjustments */
@media (prefers-color-scheme: dark) {
  .priority-strip {
    opacity: 0.9;
  }
  
  .priority-strip.priority-0 { 
    box-shadow: inset 2px 0 4px rgba(207, 19, 34, 0.4);
  }
  
  .priority-strip.priority-1 { 
    box-shadow: inset 2px 0 4px rgba(212, 107, 8, 0.4);
  }
  
  .priority-strip.priority-2 { 
    box-shadow: inset 2px 0 4px rgba(9, 109, 217, 0.4);
  }
  
  .priority-strip.priority-3 { 
    box-shadow: inset 2px 0 4px rgba(56, 158, 13, 0.4);
  }
  
  .priority-strip.priority-4 { 
    box-shadow: inset 2px 0 4px rgba(83, 29, 171, 0.4);
  }
}
</style> 