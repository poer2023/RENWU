#!/bin/bash

echo "🚀 启动 TaskWall v2.0 应用..."

# 检查并创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装后端依赖
echo "📦 安装后端依赖..."
cd backend
pip install -r requirements.txt

# 启动后端服务器
echo "🖥️ 启动后端API服务器..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ..

# 安装前端依赖
echo "📦 安装前端依赖..."
cd frontend
npm install

# 启动前端开发服务器
echo "🌐 启动前端开发服务器..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ TaskWall v2.0 已启动！"
echo ""
echo "🔗 访问链接："
echo "   前端应用: http://localhost:5173"
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "🎯 v2.0 新功能："
echo "   🤖 AI助手笔 - 在任务卡片中输入 '/' 触发AI命令"
echo "   🔍 全局搜索 - 按 Shift+Cmd+K 打开全局搜索"
echo "   🔧 自动子任务 - 点击任务卡片的生成子任务按钮"
echo "   🔗 相似任务检测 - 创建任务时自动检测相似任务"
echo "   📊 工时负载分析 - 右侧工时负载侧栏"
echo "   📈 一键周报生成 - 点击Weekly Report按钮"
echo "   ⚠️ 风险雷达 - 右上角风险指示器"
echo "   🏝️ 主题岛聚类 - 点击主题岛按钮切换视图"
echo ""
echo "⏹️ 停止服务请按 Ctrl+C"

# 等待用户中断
wait

# 清理进程
echo "🛑 正在停止服务..."
kill $BACKEND_PID 2>/dev/null
kill $FRONTEND_PID 2>/dev/null
echo "✅ 服务已停止"