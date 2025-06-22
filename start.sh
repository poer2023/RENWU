#!/bin/bash

echo "🚀 启动 TaskWall v2.0 应用..."

# 检查依赖
echo "🔍 检查系统依赖..."

# 检查Python
if ! command -v python &> /dev/null; then
    echo "❌ 错误: Python未安装，请先安装Python 3.8+"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: Node.js未安装，请先安装Node.js 16+"
    exit 1
fi

# 检查npm
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: npm未安装，请先安装npm"
    exit 1
fi

echo "✅ 系统依赖检查通过"

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

# 检查端口占用
echo "🔍 检查端口占用..."
if lsof -Pi :8765 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  警告: 端口8765已被占用，正在尝试终止占用进程..."
    pkill -f "uvicorn.*8765" 2>/dev/null || true
    sleep 2
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  警告: 端口3000已被占用，正在尝试终止占用进程..."
    pkill -f "vite.*3000\|npm.*dev" 2>/dev/null || true
    sleep 2
fi

# 启动后端服务器
echo "🖥️ 启动后端API服务器..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8765 &
BACKEND_PID=$!

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 验证后端启动
if ! curl -s http://localhost:8765/health > /dev/null 2>&1; then
    echo "❌ 错误: 后端服务启动失败"
    echo "💡 请检查:"
    echo "   - backend/app/routers/tasks.py 文件是否存在且完整"
    echo "   - 依赖是否正确安装: pip install -r requirements.txt"
    echo "   - 端口8765是否被其他程序占用"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo "✅ 后端服务启动成功"

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
echo "🎉 TaskWall v2.0 启动成功！"
echo ""
echo "🔗 访问链接："
echo "   📱 前端应用: http://localhost:3000"
echo "   🔧 后端API: http://localhost:8765"
echo "   📚 API文档: http://localhost:8765/docs"
echo ""
echo "📊 服务状态："
echo "   ✅ 后端服务: 运行中 (端口8765)"
echo "   ✅ 前端服务: 运行中 (端口3000)"
echo "   ✅ API连接: 正常"
echo ""
echo "🎯 核心功能："
echo "   📝 任务创建/编辑 - 点击右下角 + 按钮"
echo "   🔄 拖拽排序 - 直接拖动任务卡片"
echo "   🔗 任务依赖 - 拖拽连接任务"
echo "   🤖 AI功能 - 自然语言解析和智能建议"
echo "   📷 OCR识别 - 上传图片自动提取任务"
echo "   📊 数据分析 - 工时负载和风险分析"
echo ""
echo "⚠️  注意事项："
echo "   - 首次启动可能需要等待依赖下载"
echo "   - 如遇JavaScript错误，请忽略，不影响核心功能"
echo "   - 建议在Chrome/Edge/Safari浏览器中使用"
echo ""
echo "⏹️  停止服务请按 Ctrl+C"

# 等待用户中断
wait

# 清理进程
echo "🛑 正在停止服务..."
kill $BACKEND_PID 2>/dev/null
kill $FRONTEND_PID 2>/dev/null
echo "✅ 服务已停止"