# Dialog Components 对话框组件

这个目录包含了从 `Home.vue` 中拆分出来的所有对话框组件。

## 🎯 拆分目标

将原本在 `Home.vue` 中的所有对话框拆分成独立的组件，以：
- 减少 `Home.vue` 的代码量（原本 4253 行）
- 提高代码的可维护性
- 增强组件的可复用性
- 更好的关注点分离

## 📦 已完成的组件

### ✅ QuickAddDialog.vue
- **功能**：快速添加任务
- **Props**：
  - `v-model` - 控制对话框显示/隐藏
  - `modules` - 可选模块列表
- **Events**：
  - `created` - 任务创建时触发，返回任务数据

### ✅ NewModuleDialog.vue
- **功能**：创建新模块
- **Props**：
  - `v-model` - 控制对话框显示/隐藏
- **Events**：
  - `created` - 模块创建成功时触发

### ✅ AutoArrangeDialog.vue
- **功能**：自动排列任务卡片
- **Props**：
  - `v-model` - 控制对话框显示/隐藏
- **Events**：
  - `arrange` - 点击排列按钮时触发

### ✅ BackupDialog.vue
- **功能**：备份管理（手动备份、查看历史、自动备份设置）
- **Props**：
  - `v-model` - 控制对话框显示/隐藏
- **特点**：
  - 包含完整的备份逻辑
  - 支持手动备份、历史查看和下载
  - 集成自动备份设置

### ✅ ExportDialog.vue
- **功能**：导出任务数据
- **Props**：
  - `v-model` - 控制对话框显示/隐藏
  - `modules` - 模块列表
- **特点**：
  - 支持多种导出格式（JSON、CSV、Markdown）
  - 可按模块和优先级筛选
  - 实时预览导出任务数量

## 📋 待完成的组件

- [ ] SettingsDialog.vue - 应用设置对话框
- [ ] ExportDialog.vue - 数据导出对话框
- [ ] WorkloadDialog.vue - 工作负载分析对话框
- [ ] AIParseDialog.vue - AI文本解析对话框
- [ ] AIAssistantDialog.vue - AI助手对话框

## 🔧 使用方式

### 1. 导入组件
```vue
import QuickAddDialog from '@/components/dialogs/QuickAddDialog.vue'
```

### 2. 在模板中使用
```vue
<QuickAddDialog
  v-model="showQuickAdd"
  :modules="taskStore.modules"
  @created="handleTaskCreated"
/>
```

### 3. 使用 composable 管理状态
```vue
import { useDialogs } from '@/composables/dialogs/useDialogs'

const dialogs = useDialogs()

// 打开对话框
dialogs.openQuickAdd()

// 关闭对话框
dialogs.closeQuickAdd()
```

## 📊 拆分效果

- 原始 `Home.vue`：4253 行
- 预计拆分后：~2500 行（减少约 40%）
- 每个对话框组件：100-300 行

## 🚀 下一步计划

1. 完成剩余对话框组件的拆分
2. 优化 `useDialogs` composable，添加更多功能
3. 为每个对话框组件编写单元测试
4. 考虑将一些复杂的对话框进一步拆分成更小的子组件 