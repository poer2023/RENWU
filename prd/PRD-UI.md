# TaskWall – UI/UX Style PRD (v3.0)

**Purpose:** 定义全新的视觉语言和交互范式，使 TaskWall 呈现 **n8n / Dify 风格**的现代、模块化体验。
**Author:** 大哥  **Date:** 2025‑06‑19

---

## 1 · Background & Rationale

MVP 使用便利贴卡片视觉，虽轻量但显得散乱、缺少系统感。参考 **n8n**（节点流编辑器）与 **Dify**（面板式 AI Studio）的设计语言，我们期望提供：

1. **模块化节点** —— 卡片即节点，可在画布上自由布线，层次关系直观。
2. **沉浸式工作区** —— 无干扰大画布 + 折叠式侧栏，专注任务编排。
3. **黑暗主题 & 低饱和色系** —— 呈现专业、低噪视觉，避免 Post‑it 色彩杂乱。

---

## 2 · Design Goals & Metrics

| 目标    | 指标                           |
| ----- | ---------------------------- |
| 信息清晰度 | 用户在 60 秒内能准确讲述 5 个任务关系（访谈）   |
| 视觉满意度 | 视觉满意度问卷 ≥ 4.0 / 5.0          |
| 操作流畅度 | 节点拖拽/连线帧率 ≥ 60 fps on MBP M1 |

---

## 3 · Reference Benchmark

| 产品       | 借鉴要点                                                                               |
| -------- | ---------------------------------------------------------------------------------- |
| **n8n**  | • 中性色深画布 (#1E1E1E)<br>• 节点圆角卡片 + Port 连接点<br>• 折叠式左侧节点库、右侧属性面板                     |
| **Dify** | • 干净 top bar + tabbed secondary nav<br>• 卡片悬浮微阴影、柔和配色<br>• 全局 Command‑K 搜索 palette |

---

## 4 · Visual Language

### 4.1 Color Tokens (Tailwind Variables)

| Token         | Hex                       | 用途         |
| ------------- | ------------------------- | ---------- |
| `--bg-base`   | #1F1F23                   | 主画布背景（暗）   |
| `--card-bg`   | #26262C                   | 节点卡片背景     |
| `--card-elev` | 0 2px 6px rgba(0,0,0,.25) | 阴影         |
| `--primary`   | #3B82F6                   | 主操作按钮、选中连线 |
| `--info`      | #8B5CF6                   | P2 紧急度边框   |
| `--warning`   | #F97316                   | P1 边框      |
| `--danger`    | #EF4444                   | P0 边框      |
| `--success`   | #22C55E                   | P3 边框      |

### 4.2 Typography

* Font Family: `Inter`, 14 px Base, 400/600 Weight
* Heading inside node: 600 16 px
* Use `tracking-tight`, line‑height 1.4

### 4.3 Elevation & Corners

* Node card: `rounded-xl` (12 px)
* Hover: translateZ(6px) + stronger shadow

---

## 5 · Layout Specification

```
┌─────────────────────────────────────────────────────────────┐
│ Top Bar  |  Command‑K Global Search  |   User / Settings    │
├─────────────────────────┬──────────────────────────────────┤
│ Left Drawer (toggle)    │                                  │
│ • Quick Add (⌘P)        │    Infinite Canvas (Pan+Zoom)    │
│ • Module Library        │    • Node Cards                  │
│ • AI Tools (shortcuts)  │    • Curved Connectors           │
│                         │                                  │
├─────────────────────────┴────────┬─────────────────────────┤
│    Timeline / Theme Island Tabs  │ Right Drawer (properties)│
└───────────────────────────────────┴─────────────────────────┘
```

* **Canvas**：Pan (Space+Drag) / Zoom (⌘+滚轮) / Reset (⌘0)
* **Drawers**：`⌘B` 左侧库切换；`TAB` 右侧属性折叠
* **Tabs**：主画布、时间轴、主题岛，一键切换视图

---

## 6 · Component Specs

### 6.1 Node Card

| 区域     | 描述                                                                              |
| ------ | ------------------------------------------------------------------------------- |
| Header | Title + urgency badge (color border strip 4 px)                                 |
| Ports  | Left: input (⬅︎) 1; Right: output (➡︎) 1; Subtasks use bottom Port dotted stack |
| Body   | Markdown description (ellipsised)                                               |
| Footer | Module pill + icons (comment, attachment)                                       |

### 6.2 Connectors

* Curved bezier, `stroke-2`, animate on hover (pulse)
* Click connector → context menu: "Set dependency type" / "Remove"

### 6.3 Command Palette (⇧⌘P)

* Fuzzy search tasks, modules, commands (Add Node, Toggle Island…)
* Dark overlay 80%; 480 px width, rounded-lg

---

## 7 · Interaction Patterns

1. **Drag‑to‑Select**：`Shift` + drag rectangle → group move
2. **Mini‑Map**：右下角 160 × 120，显示画布缩略
3. **Snap Grid**：网格 16 px 隐形；拖拽时卡片吸附
4. **Undo/Redo**：`⌘Z / ⌘⇧Z`，维持 50 steps

---

## 8 · Theme Island Mode Adaptation

* 当 Island View 打开：

  * Island 背景 `--card-bg` 提亮 4%
  * Group Label tag 18 px bold, accent color from island palette
  * Fold → island scale to 0.85 + opacity 0.3

---

## 9 · Accessibility & Dark/Light

* 默认 Dark；Light beta via `prefers-color-scheme` toggle
* WCAG AA：对比度≥4.5 (text vs bg)
* Keyboard reachable: Tab order → Canvas nodes (outline ring)

---

## 10 · Technical Notes

* **Front‑end Stack**: Vue 3 + Tailwind + vite-plugin-windicss; D3‑force for layout; `reactflow/vueflow` for nodes if available.
* **CSS Tokens** stored in `:root` and toggled via `data-theme="dark/light"`.
* **Performance**: Virtualise nodes > 300 using viewport culling.

---

## 11 · Roll‑out Plan

| Sprint | 目标                                        |
| ------ | ----------------------------------------- |
| **S1** | 基础 Dark 主题 + 新节点 UI + Canvas pan/zoom     |
| **S2** | Drawer / Command Palette / Snap Grid      |
| **S3** | Curved connectors + Mini‑map + Undo/Redo  |
| **S4** | Theme Island adaptation + Light mode beta |

---

## 12 · Acceptance Criteria

1. 新 UI 通过 8 人可用性测试 SUS ≥ 80。
2. Canvas 100 节点拖拽帧率 ≥ 55 fps。
3. Command Palette 搜索任务 1k 条时响应 ≤ 150 ms。

---

**End of Document**