"""
TaskWall v3.0 AI服务API路由器

提供完整的AI驱动任务管理API端点：
- 自然语言任务解析
- 任务智能分析
- 批量任务处理
- AI洞察和建议
- 任务优化
- 服务健康监控
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Dict, Any
from datetime import datetime

from ..deps import get_db
from ..schemas import (
    AITaskParseRequest, AITaskParseResponse,
    AITaskAnalysisRequest, AITaskAnalysisResponse,
    AIBatchProcessRequest, AIBatchProcessResponse,
    AIInsightsRequest, AIInsightsResponse,
    AIOptimizeTasksRequest, AIOptimizeTasksResponse,
    AIServiceStatusResponse
)
from ..ai import AIServiceAggregator
from ..ai.base import AIError

router = APIRouter(prefix="/api/ai/v3", tags=["AI Services v3.0"])

def get_ai_aggregator(db: Session = Depends(get_db)) -> AIServiceAggregator:
    """获取AI服务聚合器实例"""
    return AIServiceAggregator(db)

@router.post("/parse-task", response_model=AITaskParseResponse)
async def parse_natural_language_task(
    request: AITaskParseRequest,
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """
    将自然语言转换为结构化任务
    
    支持功能：
    - 中英文混合解析
    - 智能信息提取（标题、描述、优先级、分类、截止时间等）
    - 相似任务检测
    - AI增强建议
    """
    try:
        suggestion = aggregator.process_natural_language_task(
            text=request.text,
            context=request.context,
            full_analysis=request.full_analysis
        )
        
        return AITaskParseResponse(
            suggested_task=suggestion.suggested_task,
            confidence=suggestion.confidence,
            reasoning=suggestion.reasoning,
            ai_enhancements={k: v.to_dict() if hasattr(v, 'to_dict') else v 
                           for k, v in suggestion.ai_enhancements.items()},
            similar_tasks=suggestion.similar_tasks,
            success=True
        )
        
    except AIError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"AI任务解析失败: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"任务解析出错: {str(e)}"
        )

@router.post("/analyze-task", response_model=AITaskAnalysisResponse)
async def analyze_existing_task(
    request: AITaskAnalysisRequest,
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """
    对现有任务进行全面AI分析
    
    分析维度：
    - 任务分类
    - 相似度检测
    - 优先级评估
    - 依赖关系分析
    - 工作负载影响
    """
    try:
        analysis = aggregator.analyze_existing_task(
            task_data=request.task_data,
            context=request.context
        )
        
        return AITaskAnalysisResponse(
            classification_result=analysis.classification_result.to_dict() if analysis.classification_result else None,
            similarity_result=analysis.similarity_result.to_dict() if analysis.similarity_result else None,
            priority_result=analysis.priority_result.to_dict() if analysis.priority_result else None,
            dependency_result=analysis.dependency_result.to_dict() if analysis.dependency_result else None,
            workload_result=analysis.workload_result.to_dict() if analysis.workload_result else None,
            overall_confidence=analysis.overall_confidence,
            processing_time=analysis.processing_time,
            recommendations=analysis.recommendations,
            success=True
        )
        
    except AIError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"AI任务分析失败: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"任务分析出错: {str(e)}"
        )

@router.post("/batch-process", response_model=AIBatchProcessResponse)
async def batch_process_tasks(
    request: AIBatchProcessRequest,
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """
    批量处理多个自然语言任务输入
    
    特性：
    - 并行处理提高效率
    - 快速解析模式
    - 统一结果格式
    """
    try:
        results = aggregator.batch_process_tasks(
            task_inputs=request.task_inputs,
            context=request.context
        )
        
        # 转换结果格式
        formatted_results = []
        for result in results:
            formatted_results.append({
                "suggested_task": result.suggested_task,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "ai_enhancements": {k: v.to_dict() if hasattr(v, 'to_dict') else v 
                                  for k, v in result.ai_enhancements.items()},
                "similar_tasks": result.similar_tasks
            })
        
        return AIBatchProcessResponse(
            results=formatted_results,
            success=True
        )
        
    except AIError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"AI批量处理失败: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"批量处理出错: {str(e)}"
        )

@router.post("/optimize-tasks", response_model=AIOptimizeTasksResponse)
async def optimize_task_list(
    request: AIOptimizeTasksRequest,
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """
    优化任务列表
    
    优化内容：
    - 工作负载分析
    - 依赖关系检测
    - 优先级洞察
    - 相似任务分组
    - 执行顺序建议
    """
    try:
        optimization = aggregator.optimize_task_list(
            tasks=request.tasks,
            context=request.context
        )
        
        if not optimization["success"]:
            raise Exception(optimization.get("error", "优化失败"))
        
        return AIOptimizeTasksResponse(
            original_task_count=optimization["original_task_count"],
            analysis_results=optimization["analysis_results"],
            recommendations=optimization["recommendations"],
            optimized_order=optimization["optimized_order"],
            processing_time=optimization["processing_time"],
            success=True
        )
        
    except AIError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"AI任务优化失败: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"任务优化出错: {str(e)}"
        )

@router.get("/insights", response_model=AIInsightsResponse)
async def get_ai_insights(
    user_id: str = "default",
    time_frame: str = "this_week",
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """
    获取AI驱动的用户洞察
    
    洞察内容：
    - 工作负载分析
    - 优先级分布
    - 任务模式识别
    - 生产力建议
    - 系统使用统计
    """
    try:
        insights_result = aggregator.get_ai_insights(
            user_id=user_id,
            time_frame=time_frame
        )
        
        if not insights_result["success"]:
            raise Exception(insights_result.get("error", "洞察获取失败"))
        
        return AIInsightsResponse(
            insights=insights_result["insights"],
            task_count=insights_result["task_count"],
            recommendations=insights_result["insights"].get("recommendations", []),
            success=True
        )
        
    except AIError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"AI洞察获取失败: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"洞察获取出错: {str(e)}"
        )

@router.get("/status", response_model=AIServiceStatusResponse)
async def get_ai_service_status(
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """
    获取AI服务健康状态
    
    状态信息：
    - 各AI服务运行状态
    - 向量数据库状态
    - 整体健康评估
    - 性能指标
    """
    try:
        status = aggregator.get_service_status()
        
        return AIServiceStatusResponse(
            overall_health=status["overall_health"],
            services=status["services"],
            vector_database=status["vector_database"],
            timestamp=status["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"状态获取出错: {str(e)}"
        )

# 单独的AI服务端点（为高级用户提供）

@router.post("/nlp/parse")
async def nlp_parse_only(
    text: str,
    context: Dict[str, Any] = {},
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """仅使用NLP服务解析任务"""
    try:
        result = aggregator.nlp_service.process({
            "text": text,
            "context": context
        })
        return {"result": result.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/classification/classify")
async def classify_task_only(
    task_content: str,
    user_context: Dict[str, Any] = {},
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """仅使用分类服务分类任务"""
    try:
        result = aggregator.classification_service.process({
            "task_content": task_content,
            "user_context": user_context
        })
        return {"result": result.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/similarity/find")
async def find_similar_tasks_only(
    task_content: str,
    threshold: float = 0.7,
    max_results: int = 5,
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """仅使用相似度服务查找相似任务"""
    try:
        result = aggregator.similarity_service.process({
            "task_content": task_content,
            "threshold": threshold,
            "max_results": max_results
        })
        return {"result": result.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/priority/assess")
async def assess_priority_only(
    task_data: Dict[str, Any],
    context: Dict[str, Any] = {},
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """仅使用优先级服务评估任务优先级"""
    try:
        result = aggregator.priority_service.process({
            "task_data": task_data,
            "context": context
        })
        return {"result": result.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dependency/detect")
async def detect_dependencies_only(
    tasks: List[Dict[str, Any]],
    context: Dict[str, Any] = {},
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """仅使用依赖服务检测任务依赖"""
    try:
        result = aggregator.dependency_service.process({
            "operation": "detect",
            "tasks": tasks,
            "context": context
        })
        return {"result": result.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workload/analyze")
async def analyze_workload_only(
    request: dict,
    db: Session = Depends(get_db),
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """分析工作负载 - 支持基于日期的任务分析"""
    try:
        from ..crud import TaskCRUD
        from datetime import datetime, date as date_type
        
        # 解析请求中的日期
        target_date_str = request.get('date')
        if target_date_str:
            target_date = datetime.fromisoformat(target_date_str).date()
        else:
            target_date = date_type.today()
        
        # 从数据库获取所有任务
        all_tasks = TaskCRUD.read_all(db)
        
        # 转换为字典格式用于分析
        tasks_data = []
        total_hours = 0.0
        
        for task in all_tasks:
            # 估算任务时间（如果没有设置）
            estimated_hours = task.estimated_hours
            if estimated_hours == 0.0:
                # 基于优先级的默认估算: P0=8h, P1=6h, P2=4h, P3=2h, P4=1h
                hour_map = {0: 8.0, 1: 6.0, 2: 4.0, 3: 2.0, 4: 1.0}
                estimated_hours = hour_map.get(task.urgency, 4.0)
            
            task_dict = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "urgency": task.urgency,
                "estimated_hours": estimated_hours,
                "module_id": task.module_id,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            }
            
            tasks_data.append(task_dict)
            total_hours += estimated_hours
        
        # 计算工作负载指标
        capacity_hours = 8.0  # 每日工作容量
        workload_percentage = (total_hours / capacity_hours) * 100 if capacity_hours > 0 else 0
        
        # 确定冲突级别
        if workload_percentage <= 80:
            conflict_level = "green"
        elif workload_percentage <= 120:
            conflict_level = "yellow"
        else:
            conflict_level = "red"
        
        # 返回标准化的工作负载分析结果
        return {
            "success": True,
            "total_hours": round(total_hours, 2),
            "workload_percentage": round(workload_percentage, 2),
            "capacity_hours": capacity_hours,
            "tasks_count": len(tasks_data),
            "tasks": tasks_data[:10],  # 只返回前10个任务以避免响应过大
            "conflict_level": conflict_level,
            "analysis_date": target_date.isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "total_hours": 0.0,
            "workload_percentage": 0.0,
            "capacity_hours": 8.0,
            "tasks_count": 0,
            "tasks": [],
            "conflict_level": "green",
            "analysis_date": date_type.today().isoformat(),
            "error": str(e)
        }

# 向量数据库管理端点

@router.get("/vector-db/stats")
async def get_vector_db_stats(
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """获取向量数据库统计信息"""
    try:
        stats = aggregator.vector_db.get_vector_stats()
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vector-db/update-all")
async def update_all_vectors(
    force: bool = False,
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """更新所有任务的向量"""
    try:
        updated_count = aggregator.vector_db.update_all_task_vectors(force=force)
        return {
            "message": f"更新了 {updated_count} 个任务向量",
            "updated_count": updated_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI反馈和学习端点

@router.post("/feedback")
async def submit_ai_feedback(
    operation_type: str,
    input_data: Dict[str, Any],
    ai_result: Dict[str, Any],
    user_correction: Dict[str, Any] = None,
    feedback_type: str = "accept",
    aggregator: AIServiceAggregator = Depends(get_ai_aggregator)
):
    """提交AI服务反馈用于学习改进"""
    try:
        # 根据操作类型选择对应的服务
        service_map = {
            "parse": aggregator.nlp_service,
            "classify": aggregator.classification_service,
            "similarity": aggregator.similarity_service,
            "priority": aggregator.priority_service,
            "dependency": aggregator.dependency_service,
            "workload": aggregator.workload_service
        }
        
        service = service_map.get(operation_type)
        if not service:
            raise HTTPException(status_code=400, detail="无效的操作类型")
        
        service.record_user_feedback(
            input_data=input_data,
            ai_result=ai_result,
            user_correction=user_correction,
            feedback_type=feedback_type
        )
        
        return {"message": "反馈提交成功", "success": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"反馈提交失败: {str(e)}")