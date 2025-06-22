# TaskWall 端口配置总结

## 当前配置

### 后端服务
- **本地开发**: 端口 `8765`
  - 配置文件: `start.sh`
  - 启动命令: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8765`
  
- **Docker 部署**: 
  - 容器内部: 端口 `8000`
  - 主机映射: 端口 `8765`
  - 配置文件: `docker-compose.yml`

### 前端服务
- **本地开发**: 端口 `3000`
  - 配置文件: `frontend/vite.config.ts`
  - API 代理配置:
    ```typescript
    proxy: {
      '/api': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/ai': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
    }
    ```

- **Docker 部署**: 
  - 容器内部: 端口 `80`
  - 主机映射: 端口 `3000`

## API 访问路径

### 前端访问 API
- 前端代码使用相对路径: `/api/*` 或 `/ai/*`
- Vite 开发服务器自动代理到: `http://localhost:8765`

### 直接访问后端
- API 文档: `http://localhost:8765/docs`
- 健康检查: `http://localhost:8765/health`

## 已修复的问题

1. **API 路径不一致**
   - 修复了 `/ai/v3/workload/analyze` → `/api/ai/v3/workload/analyze`
   - 文件: `Home.vue`, `useAIAnalysis.ts`, `useHomeAI.ts`

2. **Vite 代理配置**
   - 确保代理目标指向正确的后端端口 8765
   - 文件: `frontend/vite.config.ts`

3. **Docker Compose 端口映射**
   - 修正了后端服务的端口映射: `8765:8000`
   - 文件: `docker-compose.yml`

## 启动命令

### 本地开发
```bash
# 启动所有服务
./start.sh

# 或分别启动
# 后端
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8765

# 前端
cd frontend
npm run dev
```

### Docker 部署
```bash
docker-compose up -d
```

## 注意事项

1. 确保端口 8765 和 3000 没有被其他程序占用
2. 前端开发时不要直接访问后端 API，应该通过前端代理访问
3. 生产环境部署时需要配置正确的 CORS 设置 