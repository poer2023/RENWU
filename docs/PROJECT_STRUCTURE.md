# TaskWall - 项目结构文档

> **TaskWall v2.0** - AI增强版可视化任务管理系统  
> **最后更新**: 2025-06-21  
> **版本**: v2.0.0

## 📋 项目概述

TaskWall 是一个基于AI增强的可视化任务管理应用，采用便利贴式画布界面，支持拖拽操作、智能任务解析、自动子任务分解等8大AI功能，为个人和团队提供高效的任务管理体验。

### 🎯 核心功能特性

**v1.0 MVP基础功能**:
- ✅ AI文本/图片解析生成任务 
- ✅ 拖拽式任务管理画布
- ✅ 任务依赖可视化连线
- ✅ 模块化项目组织 
- ✅ P0-P4优先级系统
- ✅ 操作历史记录
- ✅ 数据导出和备份

**v2.0 AI增强功能**:
- 🤖 `/ai` 智能助手笔 - 上下文感知的内容生成
- 🔍 全局模糊搜索 (⇧⌘K) - 快速定位任务内容
- 🔧 自动子任务分解 - AI智能拆分复杂任务
- 🔗 相似任务检测 - 自动发现重复和关联
- 📊 工时负载预警 - 智能负载平衡提醒
- 🏝️ 主题岛聚类视图 - AI自动任务分组
- 📈 一键周报生成 - 自动总结进展和计划
- ⚠️ 情绪风险雷达 - 智能识别项目风险

## 🏗️ 技术架构

### 技术栈概览
```
Frontend (Vue 3)    ←→    Backend (FastAPI)    ←→    AI Services (Gemini)
- 组件化设计                - RESTful API                - 自然语言处理
- 状态管理 (Pinia)          - 数据库操作 (SQLite)         - 智能分析
- 实时交互                  - AI集成                     - 内容生成
```

### 核心技术选型
- **前端**: Vue 3 + Composition API + Pinia + Element Plus + Vite
- **后端**: FastAPI + SQLModel + SQLite + Uvicorn  
- **AI服务**: Google Gemini Pro + Tesseract OCR
- **部署**: Docker + Docker Compose
- **开发工具**: TypeScript + Python 3.12

## 📁 项目目录结构

```
TaskWall/
├── 📂 backend/                     # FastAPI后端服务
│   ├── 📂 app/                     # 应用核心代码
│   │   ├── main.py                 # FastAPI应用入口点
│   │   ├── models.py               # SQLModel数据模型定义
│   │   ├── schemas.py              # Pydantic请求/响应模型
│   │   ├── crud.py                 # 数据库CRUD操作
│   │   ├── deps.py                 # 依赖注入配置
│   │   └── 📂 utils/               # 工具模块
│   │       ├── ai_client.py        # AI客户端(Gemini集成)
│   │       ├── backup.py           # 自动备份服务
│   │       ├── export.py           # 数据导出服务
│   │       └── ocr.py             # OCR文字识别服务
│   ├── 📂 data/                    # 数据存储目录
│   │   └── taskwall.db             # SQLite数据库文件
│   ├── Dockerfile                  # 后端Docker配置
│   ├── requirements.txt            # Python依赖包
│   ├── init_data.py               # 数据库初始化脚本
│   └── recreate_tables.py         # 数据库表重建脚本
├── 📂 frontend/                    # Vue 3前端应用
│   ├── 📂 src/                     # 前端源代码
│   │   ├── main.ts                 # Vue应用入口点
│   │   ├── App.vue                 # 根组件
│   │   ├── 📂 components/          # Vue组件库
│   │   │   ├── StickyCanvas.vue    # 主画布组件(任务拖拽)
│   │   │   ├── TaskCard.vue        # 任务卡片组件
│   │   │   ├── AIAssistantPrompt.vue     # AI助手弹窗
│   │   │   ├── GlobalSearch.vue          # 全局搜索组件
│   │   │   ├── CommandPalette.vue        # 命令面板
│   │   │   ├── WorkloadSidebar.vue       # 工时负载侧栏
│   │   │   ├── SimilarTaskDialog.vue     # 相似任务对话框
│   │   │   ├── RiskRadar.vue             # 风险雷达组件
│   │   │   ├── RightDrawer.vue           # 任务属性抽屉
│   │   │   ├── TaskDetailsPopup.vue      # 任务详情弹窗
│   │   │   ├── SubtaskConfirmationDialog.vue # 子任务确认对话框
│   │   │   ├── TemporarySubtaskCard.vue  # 临时子任务卡片
│   │   │   ├── TaskConnections.vue       # 任务连线组件
│   │   │   ├── MiniMap.vue              # 画布缩略图
│   │   │   └── DebugTaskList.vue        # 调试任务列表
│   │   ├── 📂 composables/         # 组合式函数(Vue 3 Composition API)
│   │   │   ├── useAIAssistant.ts         # AI助手逻辑
│   │   │   ├── useSimilarityDetection.ts # 相似度检测
│   │   │   └── useKeyboard.ts            # 快捷键管理
│   │   ├── 📂 stores/              # Pinia状态管理
│   │   │   ├── tasks.ts            # 任务状态管理
│   │   │   └── settings.ts         # 应用设置状态
│   │   ├── 📂 pages/               # 页面组件
│   │   │   └── Home.vue            # 主页面布局
│   │   └── 📂 utils/               # 前端工具函数
│   │       ├── accessibility.ts    # 无障碍功能
│   │       ├── autoArrange.ts      # 自动布局算法
│   │       └── errorHandler.ts     # 错误处理
│   ├── Dockerfile                  # 前端Docker配置
│   ├── package.json               # Node.js依赖配置
│   ├── package-lock.json          # 依赖锁定文件
│   ├── vite.config.ts             # Vite构建配置
│   ├── tsconfig.json              # TypeScript配置
│   └── shims-vue.d.ts             # Vue类型声明
├── 📂 data/                        # 数据文件目录
│   ├── taskwall.db                # 主数据库文件
│   └── 📂 backup/                  # 自动备份文件
│       ├── taskwall_backup_*.json  # JSON格式备份
│       └── taskwall_backup_*.md    # Markdown格式备份
├── 📂 prd/                         # 产品需求文档
│   ├── README.md                   # PRD管理总览
│   ├── PRD-v1.0.md                # v1.0 MVP版本需求
│   └── PRD-v2.0.md                # v2.0 AI增强版本需求
├── 📂 docs/                        # 项目文档目录
│   ├── 技术实现文档.md               # 技术架构详细说明
│   ├── 部署指南.md                  # 部署操作指南
│   └── v2.0-功能演示.md             # v2.0功能演示文档
├── 📂 scripts/                     # 脚本文件
│   └── build-production.sh        # 生产环境构建脚本
├── 📂 tests/                       # 测试文件目录
│   ├── test_project.py            # 项目集成测试
│   ├── test_current_api.py        # 当前API测试
│   ├── test_real_api.py           # 真实API测试  
│   ├── test_subtasks.py           # 子任务功能测试
│   ├── test_simple_api.py         # 简单API测试
│   ├── test_frontend.js           # 前端测试
│   └── test_features.html         # 功能测试页面
├── 📂 logs/                        # 日志文件目录
│   ├── backend_8765.log           # 后端8765端口日志
│   ├── backend_output.log         # 后端输出日志
│   ├── frontend.log               # 前端日志
│   ├── frontend_3000.log          # 前端3000端口日志
│   └── startup.log                # 启动日志
├── docker-compose.yml             # Docker Compose配置
├── start.sh                       # 应用启动脚本
├── verify-deployment.sh           # 部署验证脚本
├── README.md                      # 项目说明文档
├── DEPLOYMENT.md                  # 部署说明文档
├── FEATURE_TEST_GUIDE.md          # 功能测试指南
├── AI_SETUP_GUIDE.md              # AI设置指南
└── PROJECT_STRUCTURE.md           # 本文档 - 项目结构说明
```

## 🔌 API接口文档

### 核心API端点

**任务管理**:
- `GET /tasks/` - 获取所有任务列表
- `POST /tasks/` - 创建新任务
- `GET /tasks/{id}` - 获取特定任务详情
- `PATCH /tasks/{id}` - 更新任务信息
- `DELETE /tasks/{id}` - 删除任务
- `GET /tasks/{id}/history` - 获取任务变更历史

**AI功能**:
- `POST /ai/parse` - AI解析文本生成结构化任务
- `POST /ai/assistant` - AI助手处理命令(`/ai`功能)
- `POST /ai/subtasks` - 自动生成子任务
- `POST /ai/similarity` - 相似任务检测
- `POST /ai/weekly-report` - 生成周报
- `POST /ai/risk-analysis` - 风险分析
- `POST /ai/theme-islands` - 主题岛聚类

**模块管理**:
- `GET /modules/` - 获取所有模块
- `POST /modules/` - 创建新模块
- `DELETE /modules/{id}` - 删除模块

**工具功能**:
- `POST /ocr/` - OCR文字识别
- `GET /export/` - 数据导出
- `POST /backup/` - 手动备份
- `GET /health` - 健康检查
- `GET /settings/` - 获取设置
- `PUT /settings/{key}` - 更新设置

## 🚀 快速开始

### 环境要求
- Docker & Docker Compose
- (可选) Google Gemini API Key

### 启动应用
```bash
# 1. 克隆项目
git clone <repository> taskwall
cd taskwall

# 2. 启动应用
./start.sh

# 3. 访问应用
# 前端: http://localhost:5173
# API文档: http://localhost:8000/docs
```

### 配置AI功能
1. 打开应用设置页面
2. 输入 Google Gemini API Key
3. 启用所需的AI功能

## 📊 数据库设计

### 核心数据表

**Task (任务表)**:
```sql
- id: INTEGER PRIMARY KEY 
- title: VARCHAR(255) NOT NULL
- description: TEXT  
- urgency: INTEGER (0-4, P0-P4优先级)
- module_id: INTEGER (外键到Module表)
- parent_id: INTEGER (父任务ID,用于子任务)
- position_x: FLOAT (画布X坐标)
- position_y: FLOAT (画布Y坐标) 
- status: VARCHAR(50) (pending/in_progress/completed)
- estimated_hours: FLOAT (预估工时)
- created_at: DATETIME
- updated_at: DATETIME
- ocr_source: VARCHAR(255) (OCR来源文件)
```

**Module (模块表)**:
```sql
- id: INTEGER PRIMARY KEY
- name: VARCHAR(100) NOT NULL
- color: VARCHAR(7) (十六进制颜色代码)
- created_at: DATETIME
```

**History (历史记录表)**:
```sql
- id: INTEGER PRIMARY KEY
- task_id: INTEGER (外键到Task表)
- field_name: VARCHAR(100) (变更字段名)
- old_value: TEXT (旧值)
- new_value: TEXT (新值) 
- timestamp: DATETIME
- operation: VARCHAR(50) (create/update/delete)
```

**Setting (设置表)**:
```sql
- key: VARCHAR(100) PRIMARY KEY
- value: TEXT
- updated_at: DATETIME
```

## 🔧 开发指南

### 本地开发环境搭建

**后端开发**:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**前端开发**:
```bash  
cd frontend
npm install
npm run dev  # 启动开发服务器(端口5173)
```

**数据库管理**:
```bash
cd backend
python init_data.py      # 初始化数据库
python recreate_tables.py # 重建表结构
```

### 测试指南

**运行测试**:
```bash
# Python后端测试
cd tests
python test_project.py           # 项目集成测试
python test_current_api.py       # API接口测试
python test_subtasks.py          # 子任务功能测试

# 前端测试  
cd tests
node test_frontend.js            # 前端功能测试
open test_features.html          # 在浏览器中打开功能测试页面
```

**测试覆盖**:
- API接口完整性测试
- AI功能集成测试  
- 前端组件单元测试
- 端到端功能测试

### 代码规范

**Python后端**:
- 遵循PEP 8代码风格
- 使用类型注解(Type Hints)
- SQLModel用于数据库操作
- FastAPI用于API开发

**TypeScript前端**:
- 遵循ESLint + Prettier规范
- Vue 3 Composition API风格
- 组件式开发模式
- TypeScript严格模式

## 🔒 安全考虑

### 数据隐私
- AI调用仅发送必要的任务内容
- 敏感数据本地处理，不上传云端
- 用户可选择关闭AI功能
- API密钥加密存储

### API安全
- 输入验证和数据清理
- SQL注入防护(SQLModel ORM)
- 跨站脚本攻击防护
- CORS配置限制

## 📈 性能优化

### 前端性能
- 组件懒加载
- 虚拟滚动处理大数据量
- 防抖搜索避免频繁调用
- 智能缓存AI响应结果

### 后端性能  
- 数据库索引优化
- API响应缓存
- 批量处理减少网络请求
- 连接池优化

### AI调用优化
- Prompt结果缓存
- 降级机制(AI失败时使用规则引擎)
- 批量AI请求合并
- 超时控制

## 🌐 部署方案

### Docker部署(推荐)
```bash
# 生产环境部署
docker compose -f docker-compose.yml up -d

# 开发环境部署  
docker compose up -d --build
```

### 手动部署
```bash
# 后端部署
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端部署
cd frontend  
npm install
npm run build
# 将dist目录部署到Web服务器
```

### 环境配置
- `DATABASE_URL`: 数据库连接地址
- `GEMINI_API_KEY`: Google Gemini API密钥
- `CORS_ORIGINS`: 允许的跨域源地址

## 📞 支持与反馈

### 问题报告
- GitHub Issues: 提交Bug报告和功能请求  
- 邮件联系: 技术支持邮箱
- 文档问题: 通过PR提交文档改进

### 贡献指南
1. Fork项目仓库
2. 创建功能分支 
3. 提交代码变更
4. 创建Pull Request
5. 代码审查和合并

### 版本发布
- 主版本: 重大功能更新或架构调整
- 次版本: 新功能添加和功能增强  
- 修订版本: Bug修复和小幅改进

---

**TaskWall v2.0** - 让AI成为你的任务管理助手！ 🚀

*最后更新: 2025-06-21*