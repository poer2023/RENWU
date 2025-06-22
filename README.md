# TaskWall - Visual Task Management

A modern, visual task management application featuring drag-and-drop sticky notes, AI-powered task parsing, and OCR capabilities.

## Features

- **Visual Task Canvas**: Drag-and-drop sticky note interface for intuitive task organization
- **Task Dependencies**: Create visual connections between tasks with drag-and-drop linking
- **AI Task Parsing**: Convert natural language descriptions into structured tasks using Gemini AI (with smart fallback parsing)
- **OCR Support**: Extract tasks from images and screenshots using Tesseract
- **Priority System**: P0-P4 priority levels with color-coded urgency indicators
- **Module Organization**: Categorize tasks into modules with custom colors
- **Task History**: Track all changes with detailed history logs
- **Auto Backup**: Automatic backups every 4 hours with configurable intervals
- **Export/Import**: Export tasks to JSON and Markdown formats for backup and sharing
- **Accessibility**: Full keyboard navigation, screen reader support, and high contrast mode
- **Error Handling**: Comprehensive error management with user-friendly notifications

## Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) Gemini API key for AI parsing features

### Run with Docker

```bash
# Clone and navigate to project
git clone https://github.com/poer2023/RENWU.git taskwall
cd taskwall

# Start the application
docker compose up -d --build

# Access the application
# Frontend: http://localhost:3000
# API Documentation: http://localhost:8000/docs
```

### Configuration

1. **Gemini API Key** (Optional): 
   - Go to Settings in the web interface
   - Enter your Gemini API key for AI-powered task parsing
   - Without this, basic text parsing will be used as fallback

2. **Database**: 
   - SQLite database is automatically created in `./data/taskwall.db`
   - Data persists between container restarts

## Project Structure

```
RENWU/                              # 项目根目录
├── README.md                       # 项目说明文档
├── docker-compose.yml              # Docker编排配置
├── start.sh                        # 开发环境启动脚本
├── .gitignore                      # Git忽略文件配置
│
├── backend/                        # 后端服务 (FastAPI)
│   ├── app/                        # 应用核心代码
│   │   ├── main.py                 # FastAPI应用入口
│   │   ├── models.py               # 数据库模型定义
│   │   ├── schemas.py              # API请求/响应模型
│   │   ├── crud.py                 # 数据库操作
│   │   ├── deps.py                 # 依赖注入
│   │   ├── ai/                     # AI服务模块
│   │   │   ├── base.py             # AI服务基类
│   │   │   ├── nlp_service.py      # 自然语言处理
│   │   │   ├── similarity_service.py # 相似性检测
│   │   │   ├── priority_service.py # 优先级分析
│   │   │   └── workload_service.py # 工作量分析
│   │   ├── routers/                # API路由模块
│   │   │   ├── tasks.py            # 任务相关API
│   │   │   ├── modules.py          # 模块管理API
│   │   │   ├── ai_v3.py            # AI功能API
│   │   │   └── dependencies.py     # 依赖关系API
│   │   └── utils/                  # 工具模块
│   │       ├── ai_client.py        # AI客户端
│   │       ├── backup.py           # 备份工具
│   │       └── ocr.py              # OCR处理
│   ├── Dockerfile                  # 后端Docker配置
│   └── requirements.txt            # Python依赖
│
├── frontend/                       # 前端应用 (Vue 3)
│   ├── src/                        # 源代码目录
│   │   ├── main.ts                 # Vue应用入口
│   │   ├── App.vue                 # 根组件
│   │   ├── components/             # Vue组件
│   │   │   ├── TaskCard.vue        # 任务卡片组件
│   │   │   ├── StickyCanvas.vue    # 拖拽画布组件
│   │   │   ├── TaskConnections.vue # 任务连线组件
│   │   │   ├── canvas/             # 画布相关组件
│   │   │   ├── dialogs/            # 对话框组件
│   │   │   └── task/               # 任务相关组件
│   │   ├── composables/            # Vue组合式函数
│   │   │   ├── useUnifiedDragSystem.ts # 统一拖拽系统
│   │   │   ├── useTaskOperations.ts    # 任务操作
│   │   │   ├── useAIAssistantV3.ts     # AI助手v3
│   │   │   └── useConnections.ts       # 连线管理
│   │   ├── pages/                  # 页面组件
│   │   │   └── Home.vue            # 主页面
│   │   ├── stores/                 # 状态管理 (Pinia)
│   │   │   ├── tasks.ts            # 任务状态
│   │   │   └── settings.ts         # 设置状态
│   │   └── styles/                 # 样式文件
│   │       ├── index.css           # 主样式
│   │       ├── components.css      # 组件样式
│   │       └── variables.css       # CSS变量
│   ├── tests/                      # 前端测试 (Playwright)
│   │   ├── 00-smoke-test.spec.ts   # 冒烟测试
│   │   ├── 02-task-management.spec.ts # 任务管理测试
│   │   └── 06-view-switching.spec.ts  # 视图切换测试
│   ├── Dockerfile                  # 前端Docker配置
│   ├── package.json                # 依赖和脚本配置
│   ├── vite.config.ts              # Vite构建配置
│   └── playwright.config.ts        # 测试配置
│
├── data/                           # 数据存储目录
│   ├── taskwall.db                 # SQLite数据库
│   └── backup/                     # 自动备份文件
│
├── docs/                           # 项目文档
│   ├── PROJECT_DEVELOPMENT_GUIDE.md # 开发指南
│   ├── REFACTORING_GUIDE.md        # 重构指南
│   ├── MODULARIZATION_ANALYSIS.md  # 模块化分析
│   ├── AI_SETUP_GUIDE.md           # AI配置指南
│   ├── DEPLOYMENT.md               # 部署指南
│   └── 技术实现文档.md              # 技术实现文档
│
├── scripts/                        # 脚本工具
│   ├── build-production.sh         # 生产构建脚本
│   ├── run-tests.sh                # 测试运行脚本
│   └── verify-deployment.sh        # 部署验证脚本
│
├── testing/                        # 测试相关文件
│   ├── test_ai_integration.py      # AI集成测试
│   ├── test_connection_debug.html  # 连接调试测试
│   ├── test_all_apis.html          # API综合测试
│   └── debug_middle_click.html     # 中键点击调试
│
├── logs/                           # 日志文件
│   ├── backend.log                 # 后端日志
│   ├── frontend.log                # 前端日志
│   └── startup.log                 # 启动日志
│
├── prd/                            # 产品需求文档
│   ├── PRD-v3.0-Master.md          # 主需求文档
│   ├── PRD-v3.0-AI-Features.md     # AI功能需求
│   └── PRD-v3.0-Technical-Architecture.md # 技术架构
│
└── tests/                          # 集成测试
    ├── test_current_api.py         # 当前API测试
    ├── test_connections.html       # 连接功能测试
    └── test_subtasks.py            # 子任务测试
```

## Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with SQLModel for database operations
- **Database**: SQLite with automatic schema creation
- **AI Integration**: Google Gemini API for task parsing
- **OCR**: Tesseract for text extraction from images
- **Features**: RESTful API, automatic documentation, CORS support

### Frontend (Vue 3)
- **Framework**: Vue 3 with Composition API
- **State Management**: Pinia for reactive state
- **UI Library**: Element Plus for components
- **Build Tool**: Vite for fast development and optimized builds
- **Features**: Drag-and-drop canvas, real-time updates, responsive design

## API Endpoints

### Tasks
- `GET /api/tasks/` - List all tasks
- `POST /api/tasks/` - Create new task
- `GET /api/tasks/{id}` - Get specific task
- `PATCH /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task
- `GET /api/tasks/{id}/history` - Get task change history

### Modules
- `GET /api/modules/` - List all modules
- `POST /api/modules/` - Create new module
- `DELETE /api/modules/{id}` - Delete module

### AI & OCR
- `POST /api/ai/parse` - Parse text into structured tasks
- `POST /api/ai/theme-islands` - Create theme islands
- `POST /api/ocr/` - Extract text from uploaded images

### Health & Settings
- `GET /health` - Health check endpoint
- `GET /api/settings/` - List settings
- `PUT /api/settings/{key}` - Update setting

## Usage Guide

### Creating Tasks

1. **Quick Add**: Use the left panel to enter task descriptions
2. **AI Parsing**: Paste natural language text and click "Parse with AI"
3. **Image Upload**: Drag and drop images containing text to extract tasks
4. **Manual Entry**: Use the ⌘P shortcut or Quick Add button for manual task creation

### Managing Tasks

1. **Drag and Drop**: Move tasks around the canvas by dragging
2. **Edit in Place**: Double-click tasks to edit titles and descriptions
3. **Properties Panel**: Click tasks to open the right drawer for detailed editing
4. **Priority Levels**: 
   - P0 (Critical) - Red background
   - P1 (High) - Orange background  
   - P2 (Medium) - Yellow background
   - P3 (Low) - Green background
   - P4 (Backlog) - Blue background

### Organization

1. **Modules**: Create colored modules to categorize tasks
2. **Parent-Child**: Set parent tasks to create hierarchies
3. **History**: View all changes in the task properties panel
4. **Export**: Download all tasks as JSON for backup

### Keyboard Shortcuts

- `⌘P` / `Ctrl+P` - Quick Add Task
- `⌘E` / `Ctrl+E` - Export Tasks
- `⌘B` / `Ctrl+B` - Manual Backup (planned feature)

## Development

### 🚀 开发环境启动 (标准流程)

#### 方式一：使用启动脚本 (推荐)

```bash
# 一键启动 (自动处理依赖和服务启动)
chmod +x start.sh
./start.sh
```

#### 方式二：手动启动

**步骤1: 创建虚拟环境 (首次运行)**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

**步骤2: 启动后端服务**
```bash
cd backend
pip install -r requirements.txt

# 关键：必须使用 0.0.0.0 作为host，端口8765
python -m uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
```

**步骤3: 启动前端服务 (新终端)**
```bash
cd frontend
npm install

# 前端运行在端口3000，代理请求到后端8765
npm run dev
```

#### 访问地址
- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8765  
- **API文档**: http://localhost:8765/docs

> 📋 **端口配置详情**: 查看 [docs/PORT_CONFIGURATION.md](docs/PORT_CONFIGURATION.md) 了解完整的端口配置规范

### ⚠️ 常见开发问题解决

#### 问题1: 后端启动失败
**现象**: `AttributeError: module 'app.routers.tasks' has no attribute 'router'`
**解决**: 确保 `backend/app/routers/tasks.py` 文件完整且包含 `router` 对象

#### 问题2: 前端API连接失败 (404错误)
**现象**: 前端控制台显示 `/api/tasks/` 404错误
**原因**: Vite代理配置问题或后端未正确启动
**解决**: 
1. 确认后端运行在端口8765
2. 检查 `frontend/vite.config.ts` 代理配置：
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8765',
      changeOrigin: true,
    },
  },
}
```

#### 问题3: 后端无法访问 (Connection refused)
**原因**: 使用了错误的host参数 `127.0.0.1`
**解决**: 必须使用 `--host 0.0.0.0` 参数启动后端

#### 问题4: 端口冲突
**解决**: 
```bash
# 检查端口占用
lsof -i :8765  # 检查后端端口
lsof -i :3000  # 检查前端端口

# 终止占用进程
kill -9 <PID>
```

#### 问题5: 前端JavaScript错误
**现象**: `ReferenceError: isInitializing is not defined`
**状态**: 已知问题，不影响核心功能
**临时解决**: 忽略此错误，核心功能正常

### 🔧 开发环境配置

### Environment Variables

- `DATABASE_URL` - SQLite database path (default: sqlite:///data/taskwall.db)
- `GEMINI_API_KEY` - Google Gemini API key (optional)

### Testing

```bash
# Test API endpoints
curl http://localhost:8765/health

# Test task creation
curl -X POST http://localhost:8765/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "urgency": 2}'

# Run frontend tests
cd frontend
npm test
```

## Deployment

### Production Deployment

1. **Environment Setup**:
   ```bash
   # Set production environment variables
   export GEMINI_API_KEY="your-api-key"
   ```

2. **Docker Compose**:
   ```bash
   docker compose -f docker-compose.yml up -d
   ```

3. **Reverse Proxy** (recommended):
   Configure nginx or similar to proxy requests to the application

### Data Backup

- Database: `./data/taskwall.db`
- Export: Use the Export feature in the web interface
- Container volumes: Backup the `./data` directory

## Troubleshooting

### Common Issues

1. **Port Conflicts**: 
   - Change ports in docker-compose.yml if 3000 or 8000 are in use

2. **Database Permissions**:
   - Ensure `./data` directory is writable
   - Check Docker volume permissions

3. **AI Parsing Not Working**:
   - Verify Gemini API key in Settings
   - Check API quota and billing status
   - Fallback text parsing will be used without API key

4. **OCR Issues**:
   - Ensure image files are readable
   - Check Tesseract language support
   - Try different image formats (PNG, JPG)

### Logs

```bash
# View application logs
docker compose logs -f

# Backend logs only
docker compose logs -f api

# Frontend logs only  
docker compose logs -f web

# Check development logs
tail -f logs/backend.log
tail -f logs/frontend.log
```

## Development Guidelines

For detailed development guidelines, including:
- 🏗️ **Technical Stack** - Complete frontend and backend technology specifications
- 🏛️ **Project Architecture** - Detailed architectural diagrams and patterns
- 📝 **Development Standards** - Coding conventions and best practices
- 🚀 **Development Workflow** - Git workflow and deployment procedures
- 📚 **Best Practices** - Performance optimization and security guidelines

**👉 Please refer to: [Project Development Guide](docs/PROJECT_DEVELOPMENT_GUIDE.md)**

## Documentation

- 📋 [Project Development Guide](docs/PROJECT_DEVELOPMENT_GUIDE.md) - Complete development standards and workflow
- 🔧 [Refactoring Guide](docs/REFACTORING_GUIDE.md) - Component architecture and patterns
- 📊 [Modularization Analysis](docs/MODULARIZATION_ANALYSIS.md) - Code structure analysis
- 📈 [Modularization Completion Report](docs/MODULARIZATION_COMPLETION_REPORT.md) - Refactoring results
- 🚀 [AI Setup Guide](docs/AI_SETUP_GUIDE.md) - AI功能配置指南
- 📖 [Feature Test Guide](docs/FEATURE_TEST_GUIDE.md) - 功能测试指南
- 🔧 [Port Configuration](docs/PORT_CONFIGURATION.md) - 端口配置说明

## Contributing

1. **Read the Development Guide**: Start with [docs/PROJECT_DEVELOPMENT_GUIDE.md](docs/PROJECT_DEVELOPMENT_GUIDE.md)
2. **Follow Coding Standards**: Ensure code meets project specifications
3. **Create Feature Branch**: Use naming convention from the guide
4. **Write Tests**: Include appropriate unit and integration tests
5. **Submit Pull Request**: Follow the code review checklist

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- 📋 Create an issue in the repository
- 📖 Check the [troubleshooting section](#troubleshooting)
- 📚 Review [development documentation](docs/)
- 🔗 Review API documentation at `/docs`