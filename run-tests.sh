#!/bin/bash

# TaskWall Playwright 测试运行脚本
# 使用方法: ./run-tests.sh [选项]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
HEADED=false
DEBUG=false
UI=false
BROWSER="chromium"
WORKERS=1
RETRIES=1
TIMEOUT=30000

# 解析命令行参数
while [[ $# -gt 0 ]]; do
  case $1 in
    --headed)
      HEADED=true
      shift
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    --ui)
      UI=true
      shift
      ;;
    --browser)
      BROWSER="$2"
      shift 2
      ;;
    --workers)
      WORKERS="$2"
      shift 2
      ;;
    --retries)
      RETRIES="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    --help)
      echo "TaskWall 前端测试运行器"
      echo ""
      echo "使用方法: $0 [选项]"
      echo ""
      echo "选项:"
      echo "  --headed         在有头模式下运行浏览器"
      echo "  --debug          启用调试模式"
      echo "  --ui             打开Playwright UI模式"
      echo "  --browser NAME   指定浏览器 (chromium|firefox|webkit)"
      echo "  --workers NUM    并行worker数量 (默认: 1)"
      echo "  --retries NUM    失败重试次数 (默认: 1)"
      echo "  --timeout MS     测试超时时间 (默认: 30000ms)"
      echo "  --help           显示此帮助信息"
      echo ""
      echo "示例:"
      echo "  $0                    # 运行所有测试"
      echo "  $0 --headed --debug   # 有头模式调试"
      echo "  $0 --ui               # UI模式"
      echo "  $0 --browser firefox  # 使用Firefox"
      exit 0
      ;;
    *)
      echo "未知选项: $1"
      echo "使用 --help 查看帮助"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}🧪 TaskWall 前端测试套件${NC}"
echo -e "${BLUE}===========================${NC}"
echo ""

# 检查依赖
echo -e "${YELLOW}📋 检查依赖...${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js 未安装${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm 未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Node.js $(node --version)${NC}"
echo -e "${GREEN}✅ npm $(npm --version)${NC}"

# 检查项目目录
if [ ! -f "frontend/package.json" ]; then
    echo -e "${RED}❌ 未在正确的项目根目录执行脚本${NC}"
    echo -e "${YELLOW}请确保在包含 frontend/ 目录的项目根目录下运行此脚本${NC}"
    exit 1
fi

# 进入前端目录
cd frontend

# 检查依赖是否已安装
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 安装依赖包...${NC}"
    npm install
fi

# 检查Playwright是否已安装
if [ ! -d "node_modules/@playwright" ]; then
    echo -e "${YELLOW}🎭 安装 Playwright...${NC}"
    npm install @playwright/test
fi

# 安装浏览器
echo -e "${YELLOW}🌐 检查浏览器安装...${NC}"
npx playwright install --with-deps

# 检查后端服务
echo -e "${YELLOW}🔍 检查后端服务...${NC}"
if ! curl -s http://localhost:8765/health > /dev/null; then
    echo -e "${YELLOW}⚠️  后端服务未运行，尝试启动...${NC}"
    
    # 检查是否有start.sh脚本
    if [ -f "../start.sh" ]; then
        echo -e "${BLUE}🚀 使用 start.sh 启动服务...${NC}"
        cd ..
        ./start.sh &
        START_PID=$!
        cd frontend
        
        # 等待服务启动
        echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
        for i in {1..30}; do
            if curl -s http://localhost:8765/health > /dev/null && curl -s http://localhost:3000 > /dev/null; then
                echo -e "${GREEN}✅ 服务已启动${NC}"
                break
            fi
            if [ $i -eq 30 ]; then
                echo -e "${RED}❌ 服务启动超时${NC}"
                exit 1
            fi
            sleep 2
        done
    else
        echo -e "${RED}❌ 无法启动后端服务，请手动启动${NC}"
        echo -e "${YELLOW}请运行: ./start.sh${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 后端服务已运行${NC}"
fi

# 检查前端服务
if ! curl -s http://localhost:3000 > /dev/null; then
    echo -e "${YELLOW}⚠️  前端服务未运行${NC}"
    echo -e "${YELLOW}Playwright 将自动启动前端服务${NC}"
fi

# 构建测试命令
TEST_CMD="npx playwright test"

if [ "$HEADED" = true ]; then
    TEST_CMD="$TEST_CMD --headed"
fi

if [ "$DEBUG" = true ]; then
    TEST_CMD="$TEST_CMD --debug"
fi

if [ "$UI" = true ]; then
    TEST_CMD="$TEST_CMD --ui"
fi

if [ "$BROWSER" != "chromium" ]; then
    TEST_CMD="$TEST_CMD --project=$BROWSER"
fi

if [ "$WORKERS" != "1" ]; then
    TEST_CMD="$TEST_CMD --workers=$WORKERS"
fi

# 设置环境变量
export PLAYWRIGHT_TEST_TIMEOUT=$TIMEOUT

# 运行测试
echo ""
echo -e "${BLUE}🎭 开始运行 Playwright 测试...${NC}"
echo -e "${BLUE}命令: $TEST_CMD${NC}"
echo -e "${BLUE}浏览器: $BROWSER${NC}"
echo -e "${BLUE}Worker数量: $WORKERS${NC}"
echo -e "${BLUE}超时时间: ${TIMEOUT}ms${NC}"
echo ""

# 创建测试结果目录
mkdir -p test-results

# 运行测试
if eval $TEST_CMD; then
    echo ""
    echo -e "${GREEN}🎉 所有测试通过！${NC}"
    
    # 生成测试报告
    if [ -f "playwright-report/index.html" ]; then
        echo -e "${BLUE}📊 测试报告已生成: playwright-report/index.html${NC}"
        echo -e "${YELLOW}运行以下命令查看报告:${NC}"
        echo -e "${YELLOW}  npx playwright show-report${NC}"
    fi
    
    EXIT_CODE=0
else
    echo ""
    echo -e "${RED}❌ 测试失败${NC}"
    
    # 显示失败信息
    if [ -f "test-results/results.json" ]; then
        echo -e "${YELLOW}📋 检查测试结果: test-results/results.json${NC}"
    fi
    
    if [ -f "playwright-report/index.html" ]; then
        echo -e "${YELLOW}📊 查看详细报告:${NC}"
        echo -e "${YELLOW}  npx playwright show-report${NC}"
    fi
    
    EXIT_CODE=1
fi

# 清理
if [ ! -z "$START_PID" ]; then
    echo -e "${YELLOW}🧹 清理启动的服务...${NC}"
    kill $START_PID 2>/dev/null || true
fi

echo ""
echo -e "${BLUE}测试完成！${NC}"

exit $EXIT_CODE