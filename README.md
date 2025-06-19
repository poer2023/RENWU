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
git clone <repository> taskwall
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

### Key Components

#### Backend Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── models.py            # SQLModel database models
│   ├── schemas.py           # Pydantic request/response models
│   ├── crud.py              # Database operations
│   ├── deps.py              # Dependency injection
│   └── utils/
│       ├── ai_client.py     # Gemini AI integration
│       └── ocr.py           # Tesseract OCR wrapper
├── Dockerfile
└── requirements.txt
```

#### Frontend Structure
```
frontend/
├── src/
│   ├── main.ts              # Vue application entry
│   ├── App.vue              # Root component
│   ├── components/
│   │   ├── TaskCard.vue     # Individual task sticky note
│   │   ├── StickyCanvas.vue # Drag-and-drop canvas
│   │   └── RightDrawer.vue  # Task properties panel
│   ├── pages/
│   │   └── Home.vue         # Main application layout
│   └── stores/
│       └── tasks.ts         # Pinia state management
├── Dockerfile
├── package.json
└── vite.config.ts
```

## API Endpoints

### Tasks
- `GET /tasks/` - List all tasks
- `POST /tasks/` - Create new task
- `GET /tasks/{id}` - Get specific task
- `PATCH /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task
- `GET /tasks/{id}/history` - Get task change history

### Modules
- `GET /modules/` - List all modules
- `POST /modules/` - Create new module
- `DELETE /modules/{id}` - Delete module

### AI & OCR
- `POST /ai/parse` - Parse text into structured tasks
- `POST /ocr/` - Extract text from uploaded images

### Health & Settings
- `GET /health` - Health check endpoint
- `GET /settings/` - List settings
- `PUT /settings/{key}` - Update setting

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

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend  
cd frontend
npm install
npm run dev
```

### Environment Variables

- `DATABASE_URL` - SQLite database path (default: sqlite:///data/taskwall.db)
- `GEMINI_API_KEY` - Google Gemini API key (optional)

### Testing

```bash
# Test API endpoints
curl http://localhost:8000/health

# Test task creation
curl -X POST http://localhost:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "urgency": 2}'
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
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review API documentation at `/docs`