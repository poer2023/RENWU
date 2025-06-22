# TaskWall v3.0 AI Services

TaskWall v3.0的智能任务管理AI服务套件，提供全面的AI驱动任务管理功能。

## 🚀 快速开始

### 基础导入
```python
from app.ai import (
    AIServiceAggregator,    # 统一AI服务入口
    NLPService,            # 自然语言处理
    ClassificationService,  # 任务分类
    SimilarityService,     # 相似度检测
    PriorityService,       # 优先级评估
    DependencyService,     # 依赖分析
    WorkloadService,       # 工作负载管理
    VectorDBManager        # 向量数据库
)
```

### 创建AI聚合器
```python
from sqlalchemy.orm import Session
from app.ai import AIServiceAggregator

# 使用数据库会话创建聚合器
aggregator = AIServiceAggregator(db_session)
```

## 🧠 核心功能

### 1. 自然语言任务处理
将自然语言转换为结构化任务：

```python
# 处理单个自然语言输入
suggestion = aggregator.process_natural_language_task(
    text="紧急修复登录页面bug，今天必须完成",
    context={"user_id": "user123"},
    full_analysis=True
)

print(f"建议任务: {suggestion.suggested_task['title']}")
print(f"置信度: {suggestion.confidence}")
print(f"相似任务: {len(suggestion.similar_tasks)}个")
```

### 2. 任务分析
对现有任务进行全面AI分析：

```python
# 分析现有任务
task_data = {
    "id": 1,
    "title": "开发用户登录API",
    "description": "实现用户身份验证接口",
    "category": "开发",
    "priority": 2,
    "deadline": "2024-01-15T18:00:00Z"
}

analysis = aggregator.analyze_existing_task(
    task_data=task_data,
    context={"all_tasks": [...], "user_tasks": [...]}
)

print(f"分类结果: {analysis.classification_result.data}")
print(f"优先级: {analysis.priority_result.data}")
print(f"相似任务: {len(analysis.similarity_result.data)}")
```

### 3. 任务列表优化
优化整个任务列表：

```python
# 优化任务列表
tasks = [
    {"id": 1, "title": "任务A", "category": "开发"},
    {"id": 2, "title": "任务B", "category": "测试"},
    # ... 更多任务
]

optimization = aggregator.optimize_task_list(
    tasks=tasks,
    context={"time_frame": "this_week"}
)

print(f"优化建议: {optimization['recommendations']}")
print(f"最优执行顺序: {optimization['optimized_order']}")
```

### 4. 批量处理
批量处理多个自然语言输入：

```python
# 批量处理
task_inputs = [
    "修复支付bug",
    "设计新界面",
    "测试API接口"
]

results = aggregator.batch_process_tasks(task_inputs)
for result in results:
    print(f"任务: {result.suggested_task['title']}")
```

## 🔧 单独使用AI服务

### NLP服务
```python
nlp_service = NLPService(db_session)
result = nlp_service.process({
    "text": "明天开会讨论项目进度",
    "context": {}
})
```

### 分类服务
```python
classification_service = ClassificationService(db_session)
result = classification_service.process({
    "task_content": "开发登录API",
    "user_context": {}
})
```

### 优先级服务
```python
priority_service = PriorityService(db_session)
result = priority_service.process({
    "task_data": {
        "title": "紧急bug修复",
        "deadline": "2024-01-15T18:00:00Z"
    },
    "context": {}
})
```

### 相似度服务
```python
similarity_service = SimilarityService(db_session)
result = similarity_service.process({
    "task_content": "修复登录问题",
    "threshold": 0.7,
    "max_results": 5
})
```

### 依赖服务
```python
dependency_service = DependencyService(db_session)
result = dependency_service.process({
    "operation": "detect",
    "tasks": [...],
    "context": {}
})
```

### 工作负载服务
```python
workload_service = WorkloadService(db_session)
result = workload_service.process({
    "operation": "analyze",
    "tasks": [...],
    "time_frame": "this_week",
    "context": {}
})
```

## 📊 AI洞察

获取AI驱动的用户洞察：

```python
insights = aggregator.get_ai_insights(
    user_id="user123",
    time_frame="this_week"
)

print(f"工作负载: {insights['insights']['workload']}")
print(f"优先级分布: {insights['insights']['priorities']}")
print(f"建议: {insights['insights']['recommendations']}")
```

## 🔍 服务状态监控

检查AI服务健康状态：

```python
status = aggregator.get_service_status()
print(f"整体健康状态: {status['overall_health']}")
print(f"服务状态: {status['services']}")
print(f"向量数据库: {status['vector_database']}")
```

## ⚙️ 配置

### 环境依赖
- **必需**: SQLModel, FastAPI, 数据库连接
- **可选**: Redis (缓存), ChromaDB (向量搜索), sentence-transformers (语义相似度)

### 配置选项
```python
# 缓存配置
cache = AICache(redis_client=your_redis_client)

# 向量数据库配置
vector_db = VectorDBManager(
    db_session,
    persist_directory="./data/chroma"
)

# 带缓存的服务
service = NLPService(db_session, cache=cache)
```

## 🎯 性能优化

### 并行处理
AI聚合器自动并行执行多个AI服务，提高处理速度。

### 智能缓存
- Redis缓存热门查询结果
- 向量数据库缓存语义搜索
- 分层TTL策略优化内存使用

### 优雅降级
- Redis不可用时自动禁用缓存
- ChromaDB不可用时使用规则匹配
- 服务异常时提供备用策略

## 🔧 错误处理

```python
from app.ai.base import AIError

try:
    result = aggregator.process_natural_language_task("...")
except AIError as e:
    print(f"AI操作失败: {e.message}")
    print(f"操作类型: {e.operation}")
    if e.original_error:
        print(f"原始错误: {e.original_error}")
```

## 📈 监控和日志

AI服务自动记录：
- 操作日志（AILog表）
- 用户反馈（AIFeedback表）
- 性能指标
- 错误追踪

查看AI日志：
```python
from app.models import AILog
logs = db_session.query(AILog).filter(
    AILog.operation == "parse"
).order_by(AILog.created_at.desc()).limit(10).all()
```

## 🚀 集成到API

FastAPI集成示例：
```python
from fastapi import APIRouter, Depends
from app.ai import AIServiceAggregator

router = APIRouter()

@router.post("/ai/parse-task")
async def parse_task(
    text: str,
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    suggestion = aggregator.process_natural_language_task(text)
    return suggestion.suggested_task

@router.post("/ai/analyze-task")
async def analyze_task(
    task_data: dict,
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    analysis = aggregator.analyze_existing_task(task_data)
    return {
        "classification": analysis.classification_result.data,
        "priority": analysis.priority_result.data,
        "recommendations": analysis.recommendations
    }
```

## 🧪 测试

运行测试套件：
```bash
# 基础导入测试
python test_ai_services.py

# 功能演示
python demo_ai_features.py
```

## 📝 最佳实践

1. **使用聚合器**: 推荐使用`AIServiceAggregator`而不是直接调用单独服务
2. **提供上下文**: 尽可能提供丰富的上下文信息提高AI准确性
3. **缓存策略**: 在生产环境中配置Redis缓存
4. **错误处理**: 妥善处理AI服务可能的异常情况
5. **监控日志**: 定期检查AI操作日志和性能指标
6. **用户反馈**: 收集用户反馈持续改进AI模型

## 🔮 未来扩展

TaskWall v3.0 AI服务设计为高度可扩展：
- 新增AI服务只需继承`AIServiceBase`
- 支持自定义AI模型集成
- 可扩展的向量数据库后端
- 插件化的分析策略

---

**注意**: 这是TaskWall v3.0 Sprint 1的AI基础设施实现。随着项目发展，更多高级功能将在后续Sprint中推出。