# TaskWall 端口配置规范

## 📋 标准端口配置

### 开发环境
- **前端服务**: `3000` (Vite开发服务器)
- **后端API**: `8765` (FastAPI + Uvicorn)

### 生产环境 (Docker)
- **前端服务**: `3000` → Nginx容器
- **后端API**: `8000` → FastAPI容器

## 🔧 配置文件说明

### 1. 开发环境配置

**后端启动命令**:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
```

**前端代理配置** (`frontend/vite.config.ts`):
```typescript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8765',
      changeOrigin: true,
    },
  },
}
```

**启动脚本** (`start.sh`):
- 后端: 端口 8765
- 前端: 端口 3000 (npm run dev)

### 2. 生产环境配置

**Docker Compose** (`docker-compose.yml`):
```yaml
services:
  api:
    ports:
      - "8000:8000"
  web:
    ports:
      - "3000:80"
```

## ⚠️ 注意事项

### 开发环境
1. **必须使用 `--host 0.0.0.0`**: 不能使用 `127.0.0.1`，否则前端无法连接
2. **Vite代理不能重写路径**: 直接转发 `/api/*` 到后端
3. **端口冲突检查**: 启动前检查端口占用情况

### 生产环境
1. **Docker端口映射**: 容器内端口与宿主机端口的映射
2. **反向代理**: 建议使用Nginx作为反向代理
3. **CORS配置**: 生产环境需要正确配置CORS域名

## 🔍 端口检查命令

```bash
# 检查端口占用
lsof -i :3000  # 前端端口
lsof -i :8765  # 后端端口 (开发)
lsof -i :8000  # 后端端口 (生产)

# 终止占用进程
pkill -f "vite.*3000"     # 终止前端进程
pkill -f "uvicorn.*8765"  # 终止后端进程(开发)
pkill -f "uvicorn.*8000"  # 终止后端进程(生产)
```

## 🚀 快速启动检查清单

### 开发环境启动前检查
- [ ] 端口3000未被占用
- [ ] 端口8765未被占用  
- [ ] Python虚拟环境已激活
- [ ] Node.js和npm已安装

### 启动后验证
- [ ] 后端健康检查: `curl http://localhost:8765/health`
- [ ] 前端页面访问: `http://localhost:3000`
- [ ] API文档访问: `http://localhost:8765/docs`

---
*最后更新: 2025-06-22*