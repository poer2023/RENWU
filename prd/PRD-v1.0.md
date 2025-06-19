# Task Wall – PRD v1.0 (MVP Edition)

**Owner:** 大哥  **Created:** 2025-06-19  **Status:** Completed

> v1.0 MVP版本专注于核心的"快速捕获 + 便利贴画布"功能，为单人PM提供直观的任务管理工具。

---

# MVP – Low‑Fidelity Interaction Sketch & Task Breakdown

## 1 · Screen Layout (ASCII Wireframe)

```
┌──────────────────────────────────────────────────────────────┐
│  Top Bar:  ⌘P Quick‑Add | Search | Settings | Export | Backup │
├──────────────────────────────────────────────────────────────┤
│ Capture Panel (20%) │         Sticky‑Note Canvas (80%)        │
│ ─────────────────────│                                         │
│ [Text Input ▸Parse]  │   ┌─────────── P0 ───────────┐          │
│ [📄 Img ▸OCR]         │   │        Task A           │───┐      │
│ [Inbox]              │   └──────────────────────────┘   │      │
│                      │                  ▲               │      │
│                      │                  │               │      │
│                      │        ┌─────────┴────────┐      │      │
│                      │        │     Subtask      │◀─────┘      │
│                      │        └──────────────────┘             │
└──────────────────────┴─────────────────────────────────────────┘
                         ►  Right Drawer (Properties/History)
```

### 交互要点

1. **拖拽**：卡片自由排列，依赖连线自动吸附端点。
2. **颜色编码**：边框色 = 模块标签；背景渐深 = 紧急度 P0→P4。
3. **侧栏**：选中卡片时弹出属性面板，可编辑标题/描述/紧急度/模块；底部显示修改历史。
4. **快捷键**：`⌘P` 聚焦输入框；`⌘E` 导出；`⌘B` 手动备份。

---

## 2 · 主要流程

| # | 用户动作        | 系统行为                                 |
| - | ----------- | ------------------------------------ |
| 1 | 粘贴文本或上传截图   | 调用 `/ai/parse` (Gemini) → 结构化任务 JSON |
| 2 | AI 输出任务树    | 在 Inbox 预览 → 用户确认                    |
| 3 | 点击「创建」      | 生成卡片 → 按模块分列、紧急度排序初始位置               |
| 4 | 拖拽/连线/编辑    | 实时更新 SQLite；写 `history` 表            |
| 5 | 导出          | 生成 `.md` & `.json`；下载或存 `/backup`    |
| 6 | APScheduler | 每 4h 触发备份脚本，同路径追加新文件                 |

---

## 3 · 数据库 ER 摘要

```
Task (id, title, desc, urgency, module_id, parent_id, created_at, updated_at, ocr_src)
Module (id, name, color)
History (id, task_id, field, old_val, new_val, ts)
Setting (key, value)
```

---

## 4 · Milestone To‑Do

| 周次 | 模块       | 任务                                        | 负责人   |
| -- | -------- | ----------------------------------------- | ----- |
| W1 | 基础       | 初始化 Repo / Dockerfile / FastAPI skeleton  | Dev   |
|    |          | SQLite schema (SQLModel) & CRUD endpoints | Dev   |
|    | Front    | Vue3 Vite scaffold, Routing, UI lib setup | Front |
| W2 | Front    | Sticky‑note Canvas (vue3‑flowy) demo      | Front |
|    |          | Card component + drag / connect           | Front |
| W3 | AI & OCR | Integrate Tesseract (docker layer)        | Dev   |
|    |          | `/ai/parse` with Gemini key config        | Dev   |
| W4 | Data     | History log triggers                      | Dev   |
|    | Export   | Markdown + JSON export service            | Dev   |
|    | Cron     | APScheduler 4h backup                     | Dev   |
| W5 | Polish   | Settings page (API keys, backup interval) | Front |
|    | QA       | Edge‑case tests, performance tuning       | All   |
|    | Release  | v0.9 beta Docker image (<200 MB)          | Dev   |

---

## 5 · 后续迭代清单 (V1+)

* 甘特/时间轴视图切换
* 多人协作（WebSocket + Yjs）
* 日历同步 & 通知（iCal / Feishu Bot）
* AI 估时 & 周报自动生成
* 键盘导航 + 全局模糊搜索

---

## 6 · W1 Implementation Blueprint

### 6.1 Repository Structure

```
project-root/
├─ docker-compose.yml
├─ backend/
│  ├─ Dockerfile
│  ├─ app/
│  │  ├─ main.py          # FastAPI entry
│  │  ├─ models.py        # SQLModel tables
│  │  ├─ crud.py          # CRUD helpers
│  │  ├─ schemas.py       # Pydantic I/O models
│  │  ├─ deps.py          # DB session deps
│  │  └─ utils/
│  │     ├─ ai_client.py  # Gemini/GPT client wrapper
│  │     └─ ocr.py        # Tesseract wrapper
│  └─ requirements.txt
├─ frontend/
│  ├─ Dockerfile
│  ├─ vite.config.ts
│  ├─ index.html
│  └─ src/
│     ├─ main.ts
│     ├─ App.vue
│     ├─ components/
│     │  ├─ StickyCanvas.vue
│     │  ├─ TaskCard.vue
│     │  └─ RightDrawer.vue
│     └─ pages/
│        └─ Home.vue
└─ README.md
```

### 6.2 Backend Key Files

* **main.py** – mounts `/api` router, CORS, static export dir.
* **models.py** – defines `Task`, `Module`, `History`, `Setting` tables.
* **crud.py** – basic CRUD ops; wrapped with dependency‑injected DB session.
* **ai\_client.py** – pluggable interface `{model, api_key}` → `ask(prompt)`.
* **ocr.py** – `def extract_text(img_bytes) -> str` using pytesseract with lang `eng+chi_sim`.

### 6.3 Frontend Highlights

* **vue3-flowy** for canvas; register as `<StickyCanvas />`.
* Pinia store `useTasks()` for realtime state synced to backend.
* `TaskCard.vue` emits `update` events → REST `PATCH /tasks/{id}`.
* Hotkey plugin: `cmd+p`, `cmd+e`, `cmd+b`.

### 6.4 Docker Artifacts

**backend/Dockerfile**

```dockerfile
FROM python:3.12-slim AS base
RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-chi-sim && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**frontend/Dockerfile**

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /web
COPY frontend/ .
RUN npm i -g pnpm && pnpm i && pnpm run build

FROM nginx:alpine
COPY --from=builder /web/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**docker-compose.yml**

```yaml
version: "3.8"
services:
  api:
    build: ./backend
    volumes:
      - ./data:/app/data
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
    ports:
      - "8000:8000"

  web:
    build: ./frontend
    depends_on:
      - api
    ports:
      - "3000:80"
    restart: unless-stopped
```

### 6.5 Quickstart

```bash
# 1. clone repo & enter
$ git clone <repo> task-wall && cd task-wall

# 2. build & run
$ docker compose up -d --build

# 3. visit http://localhost:3000
```

---

## 7 · Core Features Delivered

✅ **快速任务捕获** - AI解析文本和图片生成任务  
✅ **便利贴画布** - 拖拽式任务管理界面  
✅ **任务依赖** - 可视化连线表示任务关系  
✅ **模块管理** - 按项目/模块组织任务  
✅ **优先级系统** - P0-P4紧急度分级  
✅ **历史记录** - 完整的操作审计日志  
✅ **数据导出** - Markdown和JSON格式导出  
✅ **自动备份** - 定时备份防止数据丢失

---

**End of PRD v1.0** 