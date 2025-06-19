#!/bin/bash

echo "🔍 TaskWall v2.0 部署验证"
echo "================================"

# Check Docker containers
echo "📦 检查Docker容器状态:"
docker-compose ps

echo ""
echo "🏥 健康检查:"

# Backend health check
echo -n "• 后端API (8000端口): "
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 正常运行"
else
    echo "❌ 服务异常"
fi

# Frontend health check  
echo -n "• 前端Web (3000端口): "
if curl -sf http://localhost:3000/ > /dev/null 2>&1; then
    echo "✅ 正常运行"
else
    echo "❌ 服务异常"
fi

echo ""
echo "🚀 访问地址:"
echo "• 前端应用: http://localhost:3000"
echo "• 后端API: http://localhost:8000"
echo "• API文档: http://localhost:8000/docs"

echo ""
echo "💡 管理命令:"
echo "• 查看日志: docker-compose logs -f"
echo "• 停止服务: docker-compose down"
echo "• 重启服务: docker-compose restart"

echo ""
echo "✨ TaskWall v2.0 AI功能列表:"
echo "• 🤖 AI助手笔 (/ai命令)"
echo "• 🔍 全局搜索 (⇧⌘K)"
echo "• 🧩 自动子任务生成"
echo "• 🔗 相似任务检测"
echo "• ⚖️ 工作量估算"
echo "• 📊 周报生成"
echo "• ⚠️ 风险雷达"
echo "• 🏝️ 主题岛聚类"