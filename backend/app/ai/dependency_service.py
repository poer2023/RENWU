"""
Dependency Analysis Service for TaskWall v3.0

Handles:
- Task dependency detection
- Dependency graph analysis
- Circular dependency detection
- Optimal task ordering
"""

import json
import re
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from .base import AIServiceBase, AIResult, AIOperationType
from ..models import Task, DependencyType


class DependencyStrength(str, Enum):
    """Dependency strength levels"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    CRITICAL = "critical"


@dataclass
class DependencyRelation:
    """Represents a dependency relationship"""
    source_task_id: int
    target_task_id: int
    dependency_type: DependencyType
    strength: DependencyStrength
    confidence: float
    reasoning: List[str]
    auto_detected: bool = True
    
    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = []


@dataclass
class DependencyGraph:
    """Task dependency graph representation"""
    nodes: Set[int]
    edges: List[DependencyRelation]
    adjacency_list: Dict[int, List[int]]
    reverse_adjacency_list: Dict[int, List[int]]
    
    def __post_init__(self):
        if not self.adjacency_list:
            self.adjacency_list = defaultdict(list)
        if not self.reverse_adjacency_list:
            self.reverse_adjacency_list = defaultdict(list)


class DependencyAnalyzer:
    """Advanced dependency analysis engine"""
    
    def __init__(self):
        # Dependency indicator patterns
        self.dependency_patterns = {
            DependencyType.BLOCKS: [
                r'(完成|finish).*后.*才能',
                r'(等待|wait).*完成',
                r'(依赖|depend).*',
                r'需要.*先.*',
                r'(前置|prerequisite).*',
                r'after.*complete',
                r'depends on',
                r'blocked by',
                r'requires.*first'
            ],
            DependencyType.SUBTASK: [
                r'(子任务|subtask)',
                r'(分解|break down).*为',
                r'(包含|includes?).*步骤',
                r'consists of',
                r'part of',
                r'under.*task'
            ],
            DependencyType.ENABLES: [
                r'(然后|then).*',
                r'(接着|next).*',
                r'(顺序|sequence).*',
                r'followed by',
                r'in order',
                r'step.*\d+'
            ],
            DependencyType.RESOURCE_SHARED: [
                r'(共享|share).*资源',
                r'(同一|same).*人员',
                r'(相同|same).*环境',
                r'shared resource',
                r'same team',
                r'common.*component'
            ]
        }
        
        # Keyword patterns for different dependency strengths
        self.strength_indicators = {
            DependencyStrength.CRITICAL: [
                '必须', '绝对', '关键', 'critical', 'must', 'essential', '不可缺少'
            ],
            DependencyStrength.STRONG: [
                '重要', '需要', '应该', 'important', 'should', 'required', '强烈依赖'
            ],
            DependencyStrength.MODERATE: [
                '最好', '建议', '推荐', 'recommend', 'suggest', 'prefer', '适宜'
            ],
            DependencyStrength.WEAK: [
                '可选', '考虑', '可能', 'optional', 'consider', 'might', '弱依赖'
            ]
        }
        
        # Task similarity indicators for dependency detection
        self.similarity_indicators = {
            'same_category': 0.3,
            'shared_keywords': 0.4,
            'similar_timeline': 0.2,
            'related_files': 0.5,
            'same_assignee': 0.3
        }
    
    def detect_dependencies(
        self, 
        tasks: List[Dict[str, Any]], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[DependencyRelation]:
        """Detect dependencies among tasks"""
        
        dependencies = []
        
        # Analyze each pair of tasks
        for i, task1 in enumerate(tasks):
            for j, task2 in enumerate(tasks):
                if i == j:
                    continue
                
                # Check for dependency from task1 to task2
                dependency = self._analyze_task_pair(task1, task2, context)
                if dependency:
                    dependencies.append(dependency)
        
        # Remove duplicate dependencies
        dependencies = self._deduplicate_dependencies(dependencies)
        
        return dependencies
    
    def _analyze_task_pair(
        self, 
        task1: Dict[str, Any], 
        task2: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> Optional[DependencyRelation]:
        """Analyze dependency between two specific tasks"""
        
        task1_id = task1.get('id', 0)
        task2_id = task2.get('id', 0)
        
        # Get task content for analysis
        task1_content = self._get_task_content(task1)
        task2_content = self._get_task_content(task2)
        
        # Check explicit dependencies in content
        explicit_dep = self._check_explicit_dependency(task1_content, task2_content, task2)
        if explicit_dep:
            return DependencyRelation(
                source_task_id=task1_id,
                target_task_id=task2_id,
                dependency_type=explicit_dep['type'],
                strength=explicit_dep['strength'],
                confidence=explicit_dep['confidence'],
                reasoning=explicit_dep['reasoning']
            )
        
        # Check implicit dependencies
        implicit_dep = self._check_implicit_dependency(task1, task2, context)
        if implicit_dep:
            return DependencyRelation(
                source_task_id=task1_id,
                target_task_id=task2_id,
                dependency_type=implicit_dep['type'],
                strength=implicit_dep['strength'],
                confidence=implicit_dep['confidence'],
                reasoning=implicit_dep['reasoning']
            )
        
        return None
    
    def _get_task_content(self, task: Dict[str, Any]) -> str:
        """Get combined task content for analysis"""
        return " ".join([
            task.get('title', ''),
            task.get('description', ''),
            " ".join(task.get('tags', []))
        ]).lower()
    
    def _check_explicit_dependency(
        self, 
        content1: str, 
        content2: str, 
        task2: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check for explicit dependency indicators"""
        
        import re
        
        # Check if task1 explicitly mentions task2
        task2_title = task2.get('title', '').lower()
        task2_id = str(task2.get('id', ''))
        
        # Look for references to task2 in task1's content
        references = []
        if task2_title and task2_title in content1:
            references.append(f"References task title: '{task2_title}'")
        if task2_id and task2_id in content1:
            references.append(f"References task ID: {task2_id}")
        
        if not references:
            return None
        
        # Determine dependency type and strength
        best_match = None
        max_confidence = 0.0
        
        for dep_type, patterns in self.dependency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content1, re.IGNORECASE):
                    confidence = 0.8  # High confidence for explicit patterns
                    
                    # Determine strength
                    strength = self._determine_dependency_strength(content1)
                    
                    if confidence > max_confidence:
                        max_confidence = confidence
                        best_match = {
                            'type': dep_type,
                            'strength': strength,
                            'confidence': confidence,
                            'reasoning': references + [f"Pattern match: {pattern}"]
                        }
        
        return best_match
    
    def _check_implicit_dependency(
        self, 
        task1: Dict[str, Any], 
        task2: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Check for implicit dependency indicators"""
        
        reasoning = []
        confidence = 0.0
        dependency_type = DependencyType.BLOCKS  # Default
        
        # Timeline-based dependencies
        timeline_score = self._analyze_timeline_dependency(task1, task2)
        if timeline_score > 0.3:
            confidence += timeline_score * 0.4
            reasoning.append(f"Timeline suggests dependency (score: {timeline_score:.2f})")
        
        # Category-based dependencies
        category_score = self._analyze_category_dependency(task1, task2)
        if category_score > 0.3:
            confidence += category_score * 0.3
            reasoning.append(f"Category similarity (score: {category_score:.2f})")
        
        # Keyword-based dependencies
        keyword_score = self._analyze_keyword_dependency(task1, task2)
        if keyword_score > 0.3:
            confidence += keyword_score * 0.3
            reasoning.append(f"Keyword overlap (score: {keyword_score:.2f})")
        
        # Resource-based dependencies
        if context:
            resource_score = self._analyze_resource_dependency(task1, task2, context)
            if resource_score > 0.3:
                confidence += resource_score * 0.2
                reasoning.append(f"Resource dependency (score: {resource_score:.2f})")
                dependency_type = DependencyType.RESOURCE
        
        # Only return if confidence is above threshold
        if confidence > 0.6:
            strength = DependencyStrength.MODERATE if confidence > 0.7 else DependencyStrength.WEAK
            return {
                'type': dependency_type,
                'strength': strength,
                'confidence': min(confidence, 1.0),
                'reasoning': reasoning
            }
        
        return None
    
    def _analyze_timeline_dependency(self, task1: Dict[str, Any], task2: Dict[str, Any]) -> float:
        """Analyze timeline-based dependency likelihood"""
        
        deadline1 = task1.get('deadline')
        deadline2 = task2.get('deadline')
        
        if not deadline1 or not deadline2:
            return 0.0
        
        try:
            from datetime import datetime
            
            if isinstance(deadline1, str):
                deadline1_dt = datetime.fromisoformat(deadline1.replace('Z', '+00:00'))
            else:
                deadline1_dt = deadline1
                
            if isinstance(deadline2, str):
                deadline2_dt = datetime.fromisoformat(deadline2.replace('Z', '+00:00'))
            else:
                deadline2_dt = deadline2
            
            time_diff = (deadline2_dt - deadline1_dt).total_seconds()
            
            # If task1 deadline is before task2, potential dependency
            if 0 < time_diff <= 86400 * 7:  # Within a week
                return 0.8
            elif 0 < time_diff <= 86400 * 30:  # Within a month
                return 0.5
            elif time_diff > 0:
                return 0.2
            
        except Exception:
            pass
        
        return 0.0
    
    def _analyze_category_dependency(self, task1: Dict[str, Any], task2: Dict[str, Any]) -> float:
        """Analyze category-based dependency likelihood"""
        
        cat1 = task1.get('category', '').lower()
        cat2 = task2.get('category', '').lower()
        
        if not cat1 or not cat2:
            return 0.0
        
        # Define category dependency relationships
        category_dependencies = {
            '设计': ['开发', '测试'],
            '开发': ['测试', '部署'],
            '测试': ['部署', '上线'],
            '文档': ['培训', '发布']
        }
        
        if cat1 in category_dependencies and cat2 in category_dependencies[cat1]:
            return 0.7
        elif cat1 == cat2:
            return 0.4
        
        return 0.0
    
    def _analyze_keyword_dependency(self, task1: Dict[str, Any], task2: Dict[str, Any]) -> float:
        """Analyze keyword overlap for dependency detection"""
        
        content1 = self._get_task_content(task1)
        content2 = self._get_task_content(task2)
        
        if not content1 or not content2:
            return 0.0
        
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        # Remove common words
        common_words = {'的', '是', '和', '或', '但', 'the', 'and', 'or', 'but', 'with', 'for'}
        words1 -= common_words
        words2 -= common_words
        
        if not words1 or not words2:
            return 0.0
        
        overlap = len(words1 & words2)
        union = len(words1 | words2)
        
        return overlap / union if union > 0 else 0.0
    
    def _analyze_resource_dependency(
        self, 
        task1: Dict[str, Any], 
        task2: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> float:
        """Analyze resource-based dependencies"""
        
        score = 0.0
        
        # Same assignee
        assignee1 = task1.get('assignee') or context.get('default_assignee')
        assignee2 = task2.get('assignee') or context.get('default_assignee')
        
        if assignee1 and assignee2 and assignee1 == assignee2:
            score += 0.3
        
        # Shared resources mentioned in context
        shared_resources = context.get('shared_resources', [])
        for resource in shared_resources:
            if (resource.lower() in self._get_task_content(task1) and 
                resource.lower() in self._get_task_content(task2)):
                score += 0.4
                break
        
        return min(score, 1.0)
    
    def _determine_dependency_strength(self, content: str) -> DependencyStrength:
        """Determine dependency strength from content"""
        
        for strength, keywords in self.strength_indicators.items():
            for keyword in keywords:
                if keyword in content:
                    return strength
        
        return DependencyStrength.MODERATE  # Default
    
    def _deduplicate_dependencies(self, dependencies: List[DependencyRelation]) -> List[DependencyRelation]:
        """Remove duplicate dependency relations"""
        
        seen = set()
        unique_deps = []
        
        for dep in dependencies:
            key = (dep.source_task_id, dep.target_task_id, dep.dependency_type)
            if key not in seen:
                seen.add(key)
                unique_deps.append(dep)
        
        return unique_deps
    
    def build_dependency_graph(self, dependencies: List[DependencyRelation]) -> DependencyGraph:
        """Build a dependency graph from relations"""
        
        nodes = set()
        adjacency_list = defaultdict(list)
        reverse_adjacency_list = defaultdict(list)
        
        for dep in dependencies:
            nodes.add(dep.source_task_id)
            nodes.add(dep.target_task_id)
            adjacency_list[dep.source_task_id].append(dep.target_task_id)
            reverse_adjacency_list[dep.target_task_id].append(dep.source_task_id)
        
        return DependencyGraph(
            nodes=nodes,
            edges=dependencies,
            adjacency_list=dict(adjacency_list),
            reverse_adjacency_list=dict(reverse_adjacency_list)
        )
    
    def detect_circular_dependencies(self, graph: DependencyGraph) -> List[List[int]]:
        """Detect circular dependencies in the graph"""
        
        def dfs(node, path, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.adjacency_list.get(node, []):
                if neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
                elif neighbor not in visited:
                    cycle = dfs(neighbor, path[:], visited, rec_stack)
                    if cycle:
                        return cycle
            
            rec_stack.remove(node)
            return None
        
        visited = set()
        cycles = []
        
        for node in graph.nodes:
            if node not in visited:
                cycle = dfs(node, [], visited, set())
                if cycle:
                    cycles.append(cycle)
        
        return cycles
    
    def get_topological_order(self, graph: DependencyGraph) -> Optional[List[int]]:
        """Get topological ordering of tasks (if no cycles exist)"""
        
        # Check for cycles first
        cycles = self.detect_circular_dependencies(graph)
        if cycles:
            return None  # Cannot order with cycles
        
        # Kahn's algorithm
        in_degree = defaultdict(int)
        for node in graph.nodes:
            in_degree[node] = len(graph.reverse_adjacency_list.get(node, []))
        
        queue = deque([node for node in graph.nodes if in_degree[node] == 0])
        topo_order = []
        
        while queue:
            node = queue.popleft()
            topo_order.append(node)
            
            for neighbor in graph.adjacency_list.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return topo_order if len(topo_order) == len(graph.nodes) else None
    
    def get_critical_path(self, graph: DependencyGraph, task_durations: Dict[int, float]) -> List[int]:
        """Find critical path through the dependency graph"""
        
        # This is a simplified version - in practice, you'd want a more sophisticated algorithm
        topo_order = self.get_topological_order(graph)
        if not topo_order:
            return []
        
        # Calculate earliest start times
        earliest_start = defaultdict(float)
        
        for node in topo_order:
            max_predecessor_time = 0.0
            for predecessor in graph.reverse_adjacency_list.get(node, []):
                predecessor_finish = earliest_start[predecessor] + task_durations.get(predecessor, 0)
                max_predecessor_time = max(max_predecessor_time, predecessor_finish)
            earliest_start[node] = max_predecessor_time
        
        # Find the path with maximum total duration
        max_end_time = 0.0
        critical_end_node = None
        
        for node in graph.nodes:
            end_time = earliest_start[node] + task_durations.get(node, 0)
            if end_time > max_end_time:
                max_end_time = end_time
                critical_end_node = node
        
        # Backtrack to find the critical path
        if not critical_end_node:
            return []
        
        critical_path = []
        current = critical_end_node
        
        while current is not None:
            critical_path.append(current)
            
            # Find the predecessor that determines the critical path
            next_node = None
            required_start = earliest_start[current]
            
            for predecessor in graph.reverse_adjacency_list.get(current, []):
                predecessor_finish = earliest_start[predecessor] + task_durations.get(predecessor, 0)
                if abs(predecessor_finish - required_start) < 0.01:  # Floating point tolerance
                    next_node = predecessor
                    break
            
            current = next_node
        
        critical_path.reverse()
        return critical_path


class DependencyService(AIServiceBase):
    """Dependency analysis service for TaskWall v3.0"""
    
    def __init__(self, db, cache=None):
        super().__init__(db, cache)
        self.analyzer = DependencyAnalyzer()
    
    def get_operation_type(self) -> AIOperationType:
        return AIOperationType.DEPENDENCY
    
    def _process_internal(self, input_data: Dict[str, Any]) -> AIResult:
        """Analyze task dependencies"""
        
        operation = input_data.get("operation", "detect")
        
        if operation == "detect":
            return self._detect_dependencies(input_data)
        elif operation == "analyze_graph":
            return self._analyze_dependency_graph(input_data)
        elif operation == "find_cycles":
            return self._find_circular_dependencies(input_data)
        elif operation == "topological_sort":
            return self._get_topological_order(input_data)
        elif operation == "critical_path":
            return self._find_critical_path(input_data)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def _detect_dependencies(self, input_data: Dict[str, Any]) -> AIResult:
        """Detect dependencies among tasks"""
        self._validate_input(input_data, ["tasks"])
        
        tasks = input_data["tasks"]
        context = input_data.get("context", {})
        
        # Detect dependencies
        dependencies = self.analyzer.detect_dependencies(tasks, context)
        
        # Convert to serializable format
        dep_data = []
        for dep in dependencies:
            dep_data.append({
                "source_task_id": dep.source_task_id,
                "target_task_id": dep.target_task_id,
                "dependency_type": dep.dependency_type.value,
                "strength": dep.strength.value,
                "confidence": dep.confidence,
                "reasoning": dep.reasoning,
                "auto_detected": dep.auto_detected
            })
        
        # Calculate overall confidence
        avg_confidence = sum(dep.confidence for dep in dependencies) / len(dependencies) if dependencies else 0.0
        
        return AIResult(
            success=True,
            data={
                "dependencies": dep_data,
                "total_dependencies": len(dependencies),
                "average_confidence": avg_confidence
            },
            confidence=avg_confidence,
            reasoning=[f"Detected {len(dependencies)} dependencies with average confidence {avg_confidence:.2f}"],
            model_used="dependency-analyzer"
        )
    
    def _analyze_dependency_graph(self, input_data: Dict[str, Any]) -> AIResult:
        """Analyze the dependency graph structure"""
        self._validate_input(input_data, ["dependencies"])
        
        # Convert dependencies back to objects
        dependencies = []
        for dep_data in input_data["dependencies"]:
            dep = DependencyRelation(
                source_task_id=dep_data["source_task_id"],
                target_task_id=dep_data["target_task_id"],
                dependency_type=DependencyType(dep_data["dependency_type"]),
                strength=DependencyStrength(dep_data["strength"]),
                confidence=dep_data["confidence"],
                reasoning=dep_data["reasoning"],
                auto_detected=dep_data.get("auto_detected", True)
            )
            dependencies.append(dep)
        
        # Build graph
        graph = self.analyzer.build_dependency_graph(dependencies)
        
        # Analyze graph properties
        analysis = {
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges),
            "nodes_with_dependencies": len([n for n in graph.nodes if graph.adjacency_list.get(n)]),
            "nodes_with_dependents": len([n for n in graph.nodes if graph.reverse_adjacency_list.get(n)]),
            "max_outgoing_dependencies": max([len(deps) for deps in graph.adjacency_list.values()] + [0]),
            "max_incoming_dependencies": max([len(deps) for deps in graph.reverse_adjacency_list.values()] + [0]),
            "isolated_nodes": [n for n in graph.nodes 
                             if not graph.adjacency_list.get(n) and not graph.reverse_adjacency_list.get(n)]
        }
        
        return AIResult(
            success=True,
            data=analysis,
            confidence=1.0,
            reasoning=[f"Analyzed dependency graph with {analysis['total_nodes']} nodes and {analysis['total_edges']} edges"],
            model_used="graph-analyzer"
        )
    
    def _find_circular_dependencies(self, input_data: Dict[str, Any]) -> AIResult:
        """Find circular dependencies in the graph"""
        self._validate_input(input_data, ["dependencies"])
        
        # Convert and build graph
        dependencies = self._convert_dependencies(input_data["dependencies"])
        graph = self.analyzer.build_dependency_graph(dependencies)
        
        # Find cycles
        cycles = self.analyzer.detect_circular_dependencies(graph)
        
        return AIResult(
            success=True,
            data={
                "has_cycles": len(cycles) > 0,
                "cycles": cycles,
                "cycle_count": len(cycles)
            },
            confidence=1.0,
            reasoning=[f"Found {len(cycles)} circular dependencies" if cycles else "No circular dependencies found"],
            model_used="cycle-detector"
        )
    
    def _get_topological_order(self, input_data: Dict[str, Any]) -> AIResult:
        """Get topological ordering of tasks"""
        self._validate_input(input_data, ["dependencies"])
        
        # Convert and build graph
        dependencies = self._convert_dependencies(input_data["dependencies"])
        graph = self.analyzer.build_dependency_graph(dependencies)
        
        # Get topological order
        topo_order = self.analyzer.get_topological_order(graph)
        
        if topo_order is None:
            return AIResult(
                success=False,
                data={"error": "Cannot create topological order due to circular dependencies"},
                confidence=1.0,
                reasoning=["Circular dependencies prevent topological ordering"],
                model_used="topological-sorter"
            )
        
        return AIResult(
            success=True,
            data={
                "topological_order": topo_order,
                "can_be_ordered": True
            },
            confidence=1.0,
            reasoning=[f"Generated topological order for {len(topo_order)} tasks"],
            model_used="topological-sorter"
        )
    
    def _find_critical_path(self, input_data: Dict[str, Any]) -> AIResult:
        """Find critical path through dependencies"""
        self._validate_input(input_data, ["dependencies", "task_durations"])
        
        # Convert and build graph
        dependencies = self._convert_dependencies(input_data["dependencies"])
        graph = self.analyzer.build_dependency_graph(dependencies)
        task_durations = input_data["task_durations"]
        
        # Find critical path
        critical_path = self.analyzer.get_critical_path(graph, task_durations)
        
        # Calculate total duration
        total_duration = sum(task_durations.get(task_id, 0) for task_id in critical_path)
        
        return AIResult(
            success=len(critical_path) > 0,
            data={
                "critical_path": critical_path,
                "total_duration": total_duration,
                "path_length": len(critical_path)
            },
            confidence=0.8,  # Critical path calculation has some uncertainty
            reasoning=[f"Critical path contains {len(critical_path)} tasks with total duration {total_duration}"],
            model_used="critical-path-finder"
        )
    
    def _convert_dependencies(self, dep_data_list: List[Dict[str, Any]]) -> List[DependencyRelation]:
        """Convert dependency data back to objects"""
        dependencies = []
        for dep_data in dep_data_list:
            dep = DependencyRelation(
                source_task_id=dep_data["source_task_id"],
                target_task_id=dep_data["target_task_id"],
                dependency_type=DependencyType(dep_data["dependency_type"]),
                strength=DependencyStrength(dep_data["strength"]),
                confidence=dep_data["confidence"],
                reasoning=dep_data["reasoning"],
                auto_detected=dep_data.get("auto_detected", True)
            )
            dependencies.append(dep)
        return dependencies