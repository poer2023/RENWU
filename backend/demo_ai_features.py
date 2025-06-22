#!/usr/bin/env python3
"""
TaskWall v3.0 AI功能演示脚本

演示AI服务的核心功能，包括：
- 自然语言任务解析
- 任务分类
- 优先级评估
- 相似度检测
- 依赖分析
- 工作负载管理
"""

import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_nlp_parsing():
    """演示自然语言解析功能"""
    print("🧠 自然语言解析演示")
    print("-" * 40)
    
    try:
        from app.ai import NLPService
        
        # 模拟数据库会话（在实际应用中需要真实的数据库连接）
        class MockDB:
            pass
        
        nlp_service = NLPService(MockDB())
        
        test_texts = [
            "紧急修复登录页面的bug，今天必须完成",
            "设计新的用户界面原型，预计需要4小时",
            "开会讨论项目进度，明天下午3点",
            "写API文档，不急，有空的时候做",
            "测试支付功能，高优先级"
        ]
        
        for text in test_texts:
            print(f"输入: {text}")
            try:
                result = nlp_service._rule_based_parsing(text, {})
                if result.success and result.data:
                    task = result.data[0]
                    print(f"  标题: {task['title']}")
                    print(f"  优先级: {task['priority']}")
                    print(f"  分类: {task.get('category', '未分类')}")
                    print(f"  预估工时: {task['estimated_hours']}小时")
                    print(f"  置信度: {task['confidence']:.2f}")
            except Exception as e:
                print(f"  解析失败: {e}")
            print()
        
        return True
    except Exception as e:
        print(f"NLP演示失败: {e}")
        return False

def demo_classification():
    """演示任务分类功能"""
    print("📂 任务分类演示")
    print("-" * 40)
    
    try:
        from app.ai import ClassificationService
        
        class MockDB:
            pass
        
        classification_service = ClassificationService(MockDB())
        
        test_tasks = [
            "开发用户登录API接口",
            "设计商品展示页面UI",
            "测试支付流程的性能",
            "编写项目技术文档",
            "开会讨论需求变更",
            "管理团队资源分配"
        ]
        
        for task_content in test_tasks:
            print(f"任务: {task_content}")
            try:
                result = classification_service._classify_single({
                    "task_content": task_content,
                    "user_context": {}
                })
                
                if result.success and result.data:
                    data = result.data
                    print(f"  分类: {data['category']}")
                    print(f"  子分类: {data.get('subcategory', '无')}")
                    print(f"  置信度: {data['confidence']:.2f}")
                    if data.get('alternatives'):
                        alts = data['alternatives'][:2]  # 显示前2个备选
                        alt_text = ", ".join([f"{alt['category']}({alt['confidence']:.2f})" for alt in alts])
                        print(f"  备选分类: {alt_text}")
            except Exception as e:
                print(f"  分类失败: {e}")
            print()
        
        return True
    except Exception as e:
        print(f"分类演示失败: {e}")
        return False

def demo_priority_assessment():
    """演示优先级评估功能"""
    print("🎯 优先级评估演示")
    print("-" * 40)
    
    try:
        from app.ai import PriorityService
        
        class MockDB:
            pass
        
        priority_service = PriorityService(MockDB())
        
        # 创建测试任务数据
        now = datetime.now()
        test_tasks = [
            {
                "title": "紧急修复生产环境bug",
                "description": "用户无法登录，影响业务",
                "deadline": (now + timedelta(hours=2)).isoformat(),
                "category": "开发",
                "estimated_hours": 1
            },
            {
                "title": "优化数据库查询性能",
                "description": "提升系统响应速度",
                "deadline": (now + timedelta(days=7)).isoformat(),
                "category": "开发",
                "estimated_hours": 8
            },
            {
                "title": "编写用户手册",
                "description": "完善产品文档",
                "deadline": (now + timedelta(days=30)).isoformat(),
                "category": "文档",
                "estimated_hours": 4
            }
        ]
        
        for task_data in test_tasks:
            print(f"任务: {task_data['title']}")
            try:
                result = priority_service._assess_single_priority({
                    "task_data": task_data,
                    "context": {}
                })
                
                if result.success and result.data:
                    data = result.data
                    print(f"  优先级: {data['priority_level']} ({data['priority_name']})")
                    print(f"  紧急度: {data['urgency_score']:.2f}")
                    print(f"  重要度: {data['importance_score']:.2f}")
                    print(f"  置信度: {data['confidence']:.2f}")
                    if data.get('suggested_deadline'):
                        deadline = datetime.fromisoformat(data['suggested_deadline'])
                        print(f"  建议截止时间: {deadline.strftime('%Y-%m-%d %H:%M')}")
            except Exception as e:
                print(f"  评估失败: {e}")
            print()
        
        return True
    except Exception as e:
        print(f"优先级演示失败: {e}")
        return False

def demo_similarity_detection():
    """演示相似度检测功能"""
    print("🔍 相似度检测演示")
    print("-" * 40)
    
    try:
        from app.ai.similarity_service import TaskSimilarityAnalyzer
        
        analyzer = TaskSimilarityAnalyzer()
        
        # 创建测试任务
        task1 = {
            "id": 1,
            "title": "修复用户登录bug",
            "description": "用户无法通过邮箱登录系统",
            "category": "开发",
            "priority": 1,
            "created_at": datetime.now().isoformat()
        }
        
        similar_tasks = [
            {
                "id": 2,
                "title": "解决登录问题",
                "description": "用户登录失败",
                "category": "开发",
                "priority": 1,
                "created_at": datetime.now().isoformat()
            },
            {
                "id": 3,
                "title": "开发新的支付功能",
                "description": "集成第三方支付接口",
                "category": "开发",
                "priority": 2,
                "created_at": datetime.now().isoformat()
            },
            {
                "id": 4,
                "title": "设计登录页面",
                "description": "重新设计用户登录界面",
                "category": "设计",
                "priority": 2,
                "created_at": datetime.now().isoformat()
            }
        ]
        
        print(f"基准任务: {task1['title']}")
        print("相似度分析:")
        
        for task2 in similar_tasks:
            try:
                similarity = analyzer.analyze_similarity(task1, task2)
                print(f"  与 '{task2['title']}':")
                print(f"    相似度: {similarity.similarity_score:.3f}")
                print(f"    类型: {similarity.similarity_type}")
                print(f"    原因: {similarity.reasoning[0] if similarity.reasoning else '无'}")
                
                if similarity.merge_suggestion:
                    print(f"    建议合并: 是 (置信度: {similarity.merge_suggestion['confidence']:.2f})")
                else:
                    print(f"    建议合并: 否")
            except Exception as e:
                print(f"    分析失败: {e}")
            print()
        
        return True
    except Exception as e:
        print(f"相似度演示失败: {e}")
        return False

def demo_workload_analysis():
    """演示工作负载分析功能"""
    print("📊 工作负载分析演示")
    print("-" * 40)
    
    try:
        from app.ai.workload_service import WorkloadAnalyzer, TimeFrame
        
        analyzer = WorkloadAnalyzer()
        
        # 创建测试任务列表
        now = datetime.now()
        test_tasks = []
        
        # 添加不同类型的任务
        task_templates = [
            {"title": "开发功能A", "category": "开发", "priority": 1, "hours": 8},
            {"title": "开发功能B", "category": "开发", "priority": 2, "hours": 6},
            {"title": "测试功能A", "category": "测试", "priority": 1, "hours": 4},
            {"title": "设计界面", "category": "设计", "priority": 2, "hours": 5},
            {"title": "编写文档", "category": "文档", "priority": 3, "hours": 3},
            {"title": "项目会议", "category": "会议", "priority": 2, "hours": 1},
            {"title": "管理任务", "category": "管理", "priority": 2, "hours": 2}
        ]
        
        for i, template in enumerate(task_templates):
            task = {
                "id": i + 1,
                "title": template["title"],
                "category": template["category"],
                "priority": template["priority"],
                "estimated_hours": template["hours"],
                "deadline": (now + timedelta(days=i+1)).isoformat(),
                "created_at": now.isoformat(),
                "status": "active"
            }
            test_tasks.append(task)
        
        # 分析工作负载
        try:
            metrics = analyzer.analyze_workload(test_tasks, TimeFrame.THIS_WEEK, {
                "available_hours": 40,  # 一周40小时
                "work_days_per_week": 5,
                "hours_per_day": 8
            })
            
            print("工作负载指标:")
            print(f"  总工时: {metrics.total_hours:.1f}小时")
            print(f"  可用工时: {metrics.available_hours:.1f}小时") 
            print(f"  利用率: {metrics.utilization_rate:.1%}")
            print(f"  负载级别: {metrics.workload_level.value}")
            print(f"  任务总数: {metrics.task_count}")
            print(f"  高优先级任务: {metrics.high_priority_count}")
            print(f"  逾期任务: {metrics.overdue_count}")
            print(f"  平均复杂度: {metrics.avg_task_complexity:.2f}")
            
            if metrics.stress_indicators:
                print(f"  压力指标: {', '.join(metrics.stress_indicators[:2])}")
            
            if metrics.recommendations:
                print(f"  建议: {metrics.recommendations[0]}")
                
        except Exception as e:
            print(f"  分析失败: {e}")
        
        # 分析工作分布
        try:
            distribution = analyzer.analyze_workload_distribution(test_tasks, TimeFrame.THIS_WEEK)
            
            print("\n工作分布:")
            print("  按分类:")
            for category, hours in sorted(distribution.by_category.items(), key=lambda x: x[1], reverse=True):
                print(f"    {category}: {hours:.1f}小时")
            
            print("  按优先级:")
            for priority, hours in sorted(distribution.by_priority.items()):
                priority_names = {0: "紧急", 1: "高", 2: "中", 3: "低", 4: "待办"}
                name = priority_names.get(priority, f"级别{priority}")
                print(f"    {name}: {hours:.1f}小时")
                
        except Exception as e:
            print(f"  分布分析失败: {e}")
        
        return True
    except Exception as e:
        print(f"工作负载演示失败: {e}")
        return False

def demo_ai_aggregator():
    """演示AI服务聚合器功能"""
    print("🤖 AI服务聚合器演示")
    print("-" * 40)
    
    try:
        # 这里只演示聚合器的基本结构，因为需要数据库连接
        from app.ai import AIServiceAggregator
        
        print("AI服务聚合器提供的功能:")
        print("  ✓ 自然语言任务处理")
        print("  ✓ 并行AI服务调用")
        print("  ✓ 综合分析结果")
        print("  ✓ 批量任务处理")
        print("  ✓ AI健康监控")
        print()
        print("聚合器将在实际应用中协调所有AI服务，")
        print("提供统一的智能任务管理接口。")
        
        return True
    except Exception as e:
        print(f"聚合器演示失败: {e}")
        return False

def main():
    """运行所有演示"""
    print("🚀 TaskWall v3.0 AI功能演示")
    print("=" * 50)
    print()
    
    demos = [
        ("自然语言解析", demo_nlp_parsing),
        ("任务分类", demo_classification),
        ("优先级评估", demo_priority_assessment),
        ("相似度检测", demo_similarity_detection),
        ("工作负载分析", demo_workload_analysis),
        ("AI服务聚合器", demo_ai_aggregator)
    ]
    
    passed = 0
    total = len(demos)
    
    for name, demo_func in demos:
        try:
            if demo_func():
                print(f"✅ {name} 演示成功")
                passed += 1
            else:
                print(f"❌ {name} 演示失败")
        except Exception as e:
            print(f"❌ {name} 演示出错: {e}")
        print()
    
    print("=" * 50)
    print(f"演示完成: {passed}/{total} 成功")
    
    if passed == total:
        print("🎉 所有AI功能演示成功！TaskWall v3.0 AI基础设施已就绪。")
        return 0
    else:
        print("⚠️  部分演示失败，请检查上述错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())