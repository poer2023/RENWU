# TaskWall – UI/UX Unified PRD (v5.0)

**Purpose:** 定义全新的视觉语言和交互范式，使 TaskWall 呈现 **n8n / Dify 风格**的现代、模块化体验。结合浅色主题优化，提供清晰可视的任务管理界面。
**Author:** Claude Code Assistant  **Date:** 2025‑06‑20

---

## 1 · Background & Evolution

### 1.1 设计演进历程
- **v1.0-v2.0**: MVP 便利贴风格，轻量但缺少系统感
- **v3.0**: 引入 n8n/Dify 暗色主题，模块化节点设计
- **v4.0**: 切换到浅色主题，解决可视性问题
- **v5.0**: 统一设计语言，完善交互体验

### 1.2 核心设计理念
1. **模块化节点** —— 卡片即节点，可在画布上自由布线，层次关系直观
2. **沉浸式工作区** —— 无干扰大画布 + 折叠式侧栏，专注任务编排
3. **明亮清晰主题** —— 浅色系为主，提供专业、清晰的视觉体验
4. **直观交互** —— 借鉴现代设计工具的最佳实践

---

## 2 · Design Goals & Metrics

| 目标    | 指标                           | 状态 |
| ----- | ---------------------------- | -- |
| 信息清晰度 | 用户在 60 秒内能准确讲述 5 个任务关系（访谈）   | ✅  |
| 视觉满意度 | 视觉满意度问卷 ≥ 4.0 / 5.0          | ✅  |
| 操作流畅度 | 节点拖拽/连线帧率 ≥ 60 fps on MBP M1 | 🔄 |
| 可访问性  | WCAG AA 对比度 ≥ 4.5            | ✅  |

---

## 3 · Reference Benchmark

| 产品       | 借鉴要点                                                                               |
| -------- | ---------------------------------------------------------------------------------- |
| **n8n**  | • 节点圆角卡片 + Port 连接点<br>• 折叠式左侧节点库、右侧属性面板<br>• 流式布局和连接线设计                     |
| **Dify** | • 干净 top bar + tabbed secondary nav<br>• 卡片悬浮微阴影、柔和配色<br>• 全局 Command‑K 搜索 palette |
| **Figma** | • 无限画布缩放和平移<br>• 多选和群组操作<br>• 智能对齐和网格吸附                                        |

---

## 4 · Visual Language

### 4.1 Light Theme Color Tokens (主色系)

| Token             | Value                            | 用途                      |
| ----------------- | -------------------------------- | ----------------------- |
| `--bg-base`       | #F8F9FC                          | 画布主背景（超淡灰白）             |
| `--panel-bg`      | #FFFFFF                          | 侧栏、抽屉、顶部栏背景             |
| `--card-bg`       | #FFFFFF                          | 节点卡片背景                  |
| `--card-shadow`   | 0 2px 6px rgba(16,24,40,.08)    | 柔和阴影                    |
| `--primary`       | #2563EB                          | 主操作按钮、选中连线              |
| `--danger`        | #F87171                          | P0 紧急度边框                |
| `--warning`       | #FB923C                          | P1 边框                   |
| `--info`          | #60A5FA                          | P2 边框                   |
| `--success`       | #34D399                          | P3 边框                   |
| `--neutral`       | #1F2937                          | 主文本深灰                   |
| `--border-subtle` | #F4F4F5                          | 分割线                     |
| `--grid-line`     | rgba(0,0,0,0.05)                 | 16px 隐形网格，拖动时显示参考        |

### 4.2 Typography

- **Font Family**: `Inter`, sans-serif fallback
- **Base Size**: 14px (--font-size-sm)
- **Node Title**: 16px, 600 weight (--font-weight-semibold)
- **Body Text**: 14px, 400 weight
- **Line Height**: 1.4 (--line-height-normal)
- **Letter Spacing**: -0.01em

### 4.3 Elevation & Corners

- **Node Card**: `border-radius: 12px` (--radius-lg)
- **Panels**: `border-radius: 8px` (--radius-md)
- **Buttons**: `border-radius: 6px` (--radius-sm)
- **Hover Elevation**: `translateY(-2px)` + enhanced shadow

---

## 5 · Layout Specification

```
┌─────────────────────────────────────────────────────────────┐
│ Modern TopBar | Command‑K Search | User Menu | Settings   │
├─────────────────────────┬──────────────────────────────────┤
│ Left Drawer (⌘B)        │                                  │
│ • Quick Add (⌘N)        │    Infinite Canvas (Pan+Zoom)    │
│ • Module Library        │    • Node Cards (左侧竖条设计)        │
│ • AI Assistant         │    • Curved Bezier Connectors    │
│ • Task Templates        │    • 16px Snap Grid             │
│                         │    • Mini-map (右下角)            │
├─────────────────────────┴────────┬─────────────────────────┤
│ Bottom Status Bar | View Modes   │ Right Properties (Tab) │
└───────────────────────────────────┴─────────────────────────┘
```

### 5.1 Canvas 交互
- **Pan**: Space+Drag 或 Middle Mouse Button
- **Zoom**: ⌘+滚轮 或 Pinch Gesture
- **Reset View**: ⌘+0
- **Fit All**: ⌘+1

### 5.2 Keyboard Shortcuts
- **Drawers**: `⌘B` 左侧库切换；`Tab` 右侧属性折叠
- **Global**: `⌘K` Command Palette；`⌘N` Quick Add
- **Selection**: `⌘A` 全选；`Shift+Click` 多选；`⌘G` 群组

---

## 6 · Component Specifications

### 6.1 Node Card (Enhanced)

| 区域             | 规格                                    | 设计要点                            |
| -------------- | ------------------------------------- | ------------------------------- |
| **Priority Strip** | 4px 竖条 (左侧)                          | 左色条比顶色条更现代；圆角 12px 不变           |
| **Card Body**      | `--card-bg`, 12px 圆角, `--card-shadow` | 悬停加 `translateY(-2px)` + 阴影深度倍增 |
| **Header**         | Title + Priority Badge                | 16px font-weight-semibold       |
| **Ports**          | Left: input; Right: output           | 12px 圆点，悬停高亮，连接时动画             |
| **Body**           | Markdown description (省略)             | 最多3行，超出显示...                   |
| **Footer**         | Module pill + Meta badges            | 时间、工时估算等                        |
| **Actions**        | Edit, AI Generate, Delete            | 选中时显示，幽灵按钮样式                   |

### 6.2 Connection System

```typescript
interface Connection {
  type: 'bezier' | 'straight' | 'stepped'
  strokeWidth: 2 | 3  // 悬停时加粗
  color: 'primary' | 'success' | 'warning'
  animated: boolean   // 数据流动画
  markers: {
    start?: 'dot' | 'arrow'
    end: 'arrow' | 'diamond'
  }
}
```

- **Bezier Curves**: 平滑曲线，自动计算控制点
- **Hover Effects**: 高亮整条路径，显示依赖类型
- **Context Menu**: 右键连接线 → 编辑依赖类型、删除连接

### 6.3 Command Palette (Global Search)

```
┌─────────────────── ⌘K ────────────────────┐
│ 🔍 Search tasks, commands, modules...     │
├───────────────────────────────────────────┤
│ 📝 Create new task                    ⌘N │
│ 🤖 AI Generate subtasks              ⌘⇧G │
│ 🏝️ Toggle Island View                ⌘I │
│ ⚡ Auto-arrange layout               ⌘⇧A │
│ ────────────────────────────────────────── │
│ 📋 "Backend API Design" (Task #123)       │
│ 📋 "User Authentication" (Task #456)      │
├───────────────────────────────────────────┤
│ ↑↓ Navigate • Enter Select • Esc Close   │
└───────────────────────────────────────────┘
```

- **Fuzzy Search**: 支持任务标题、描述、模块名称
- **Command Support**: 快速访问功能和创建操作
- **Keyboard Navigation**: 纯键盘操作流程

---

## 7 · Advanced Interaction Patterns

### 7.1 Selection & Multi-Operations
- **Click**: 单选节点
- **Shift+Click**: 多选添加/移除
- **Drag Rectangle**: 框选多个节点
- **⌘+G**: 群组选中的节点
- **Delete**: 删除选中节点（确认对话框）

### 7.2 Canvas Navigation
- **Mini-Map**: 右下角 160×120px 缩略图
- **Viewport Indicator**: 当前视图范围高亮
- **Quick Navigate**: 点击 Mini-map 快速跳转

### 7.3 Smart Layout Features
- **Snap Grid**: 16px 网格，拖拽时自动吸附
- **Alignment Guides**: 拖拽时显示对齐线
- **Auto-Arrange**: ⌘⇧A 智能排列所有节点
- **Undo/Redo**: ⌘Z/⌘⇧Z，维持 50 steps

---

## 8 · Theme Island Mode Integration

### 8.1 Island View Adaptations
当 Island View 激活时：

- **Background**: Island 区域使用 `--panel-bg` + 淡色边框
- **Headers**: Island 标题使用 accent color，16px bold
- **Collapse**: 折叠时 scale(0.85) + opacity(0.3)
- **Transitions**: 240ms ease-in-out 动画

### 8.2 Color Strategy
```css
.island-view {
  --island-bg: rgba(37, 99, 235, 0.03);
  --island-border: rgba(37, 99, 235, 0.1);
  --island-header: var(--primary);
}
```

---

## 9 · Accessibility & Responsive Design

### 9.1 WCAG Compliance
- **Contrast Ratio**: Text/background ≥ 4.5 (AA level)
- **Focus Indicators**: 2px solid outline for keyboard navigation
- **Screen Reader**: Proper ARIA labels for canvas elements
- **Color Independence**: 不仅依赖颜色传达信息

### 9.2 Theme Support
- **Default**: Light theme (`data-theme="light"`)
- **System Preference**: 支持 `prefers-color-scheme`
- **Manual Toggle**: Settings 中手动切换
- **High Contrast**: 可选高对比度模式

---

## 10 · Performance & Technical Specifications

### 10.1 Canvas Optimization
- **Virtualization**: >100 节点时启用视口裁剪
- **GPU Acceleration**: 使用 CSS transforms 和 will-change
- **Debounced Updates**: 拖拽过程中限制重绘频率
- **Memory Management**: 及时清理未使用的 DOM 元素

### 10.2 技术栈
```json
{
  "frontend": {
    "framework": "Vue 3 + Composition API",
    "styling": "CSS Custom Properties + Tailwind utility",
    "canvas": "Native DOM + SVG for connections",
    "state": "Pinia stores",
    "build": "Vite + TypeScript"
  },
  "design_tokens": {
    "storage": ":root CSS variables",
    "toggle": "data-theme attribute",
    "fallbacks": "Progressive enhancement"
  }
}
```

---

## 11 · Implementation Roadmap

| Phase | 功能模块                                    | 状态 |
| ----- | --------------------------------------- | -- |
| **P1** | 浅色主题 + 左侧竖条节点设计                        | ✅  |
| **P2** | Canvas 优化 + 网格系统 + Mini-map             | 🔄 |
| **P3** | Command Palette + 全局搜索                  | 🔄 |
| **P4** | 侧边栏折叠 + 属性面板                           | 📋 |
| **P5** | 高级交互（多选、群组、智能排列）                        | 📋 |
| **P6** | Theme Island 集成优化                      | 📋 |

---

## 12 · Acceptance Criteria

### 12.1 用户体验指标
1. **可用性测试**: 8人 SUS 评分 ≥ 80
2. **任务完成率**: 核心功能 >95% 成功率
3. **学习曲线**: 新用户 5 分钟内完成基础操作

### 12.2 技术性能指标
1. **渲染性能**: 100 节点拖拽帧率 ≥ 55 fps
2. **搜索响应**: 1k 任务搜索响应 ≤ 150ms
3. **内存使用**: 长时间使用内存增长 <50MB

### 12.3 视觉质量指标
1. **设计一致性**: 所有组件遵循统一 Design System
2. **响应式适配**: 支持 1024px - 2560px 屏幕
3. **动画流畅度**: 所有过渡动画 60fps

---

## 13 · 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v5.0 | 2025-06-20 | 合并所有UI PRD，统一设计语言，明确实现路径 |
| v4.0 | 2025-06-20 | 切换到浅色主题，左侧竖条设计 |
| v3.0 | 2025-06-19 | n8n/Dify 风格，暗色主题 |
| v2.0 | 2025-06-18 | Theme Island 功能 |
| v1.0 | 2025-06-17 | 初始便利贴设计 |

---

**End of Unified PRD Document**