"""
Natural Language Processing Service for TaskWall v3.0

Handles:
- Task parsing from natural language
- Batch task parsing
- Information extraction and structuring
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .base import AIServiceBase, AIResult, AIOperationType
from ..utils.ai_client import ask, ai_client
from ..models import PriorityLevel, TaskStatus


@dataclass
class ParsedTask:
    """Structured task data from NLP parsing"""
    title: str
    description: str = ""
    priority: int = 2
    category: Optional[str] = None
    tags: List[str] = None
    deadline: Optional[datetime] = None
    estimated_hours: float = 0.0
    confidence: float = 0.0
    reasoning: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.reasoning is None:
            self.reasoning = []


class TaskNLPParser:
    """Enhanced NLP parser for task extraction"""
    
    def __init__(self):
        self.priority_keywords = {
            0: ['紧急', '立即', '马上', '今天必须', 'urgent', 'asap', 'critical', '严重'],
            1: ['重要', '尽快', '优先', '这周', 'important', 'high', '高优先级'],
            2: ['一般', '正常', '常规', 'normal', 'medium', '中等'],
            3: ['不急', '有时间', '低优先级', 'low', 'later', '次要'],
            4: ['以后', '有空', '备用', 'backlog', 'someday', '待办']
        }
        
        self.time_patterns = {
            r'今天|today': lambda: datetime.now().replace(hour=23, minute=59),
            r'明天|tomorrow': lambda: datetime.now() + timedelta(days=1),
            r'后天': lambda: datetime.now() + timedelta(days=2),
            r'这周|this week': lambda: datetime.now() + timedelta(days=7-datetime.now().weekday()),
            r'下周|next week': lambda: datetime.now() + timedelta(days=14-datetime.now().weekday()),
            r'这个月|this month': lambda: datetime.now().replace(day=28, hour=23, minute=59),
            r'下个月|next month': lambda: (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=28),
            r'(\d+)天[后内]|in (\d+) days?': lambda m: datetime.now() + timedelta(days=int(m.group(1))),
            r'(\d+)周[后内]|in (\d+) weeks?': lambda m: datetime.now() + timedelta(weeks=int(m.group(1))),
            r'(\d+)小时[后内]|in (\d+) hours?': lambda m: datetime.now() + timedelta(hours=int(m.group(1)))
        }
        
        self.action_verbs = [
            '完成', '做', '写', '创建', '开发', '设计', '测试', '修复', '更新', '优化',
            'complete', 'do', 'write', 'create', 'develop', 'design', 'test', 'fix', 'update', 'optimize'
        ]
        
        self.category_keywords = {
            '开发': ['开发', '编程', '代码', '程序', 'develop', 'code', 'program', 'implement'],
            '测试': ['测试', '验证', '检查', 'test', 'verify', 'check', 'validate'],
            '会议': ['会议', '开会', '讨论', '沟通', 'meeting', 'discuss', 'call', 'sync'],
            '文档': ['文档', '文档', '报告', '记录', 'document', 'report', 'write', 'documentation'],
            '设计': ['设计', '原型', '界面', 'design', 'prototype', 'ui', 'ux'],
            '管理': ['管理', '计划', '安排', '组织', 'manage', 'plan', 'organize', 'schedule']
        }
    
    def extract_priority(self, text: str) -> Tuple[int, List[str]]:
        """Extract priority from text"""
        text_lower = text.lower()
        reasoning = []
        
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    reasoning.append(f"Found priority keyword: '{keyword}'")
                    return priority, reasoning
        
        reasoning.append("No priority keywords found, using default medium priority")
        return 2, reasoning  # Default medium priority
    
    def extract_time(self, text: str) -> Tuple[Optional[datetime], List[str]]:
        """Extract time information from text"""
        reasoning = []
        
        for pattern, time_func in self.time_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if callable(time_func):
                        if match.groups():
                            deadline = time_func(match)
                        else:
                            deadline = time_func()
                    else:
                        deadline = time_func
                    
                    reasoning.append(f"Found time pattern: '{match.group()}'")
                    return deadline, reasoning
                except Exception as e:
                    reasoning.append(f"Failed to parse time pattern: {e}")
        
        # Try to extract specific time formats
        time_match = re.search(r'(\d{1,2})[点:](\d{1,2})?', text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                today = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                if today <= datetime.now():
                    today += timedelta(days=1)  # Next day if time has passed
                reasoning.append(f"Found specific time: {hour}:{minute:02d}")
                return today, reasoning
        
        reasoning.append("No time information found")
        return None, reasoning
    
    def extract_category(self, text: str) -> Tuple[Optional[str], List[str]]:
        """Extract category from text"""
        text_lower = text.lower()
        reasoning = []
        
        # Score each category based on keyword matches
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = 0
            matched_keywords = []
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                category_scores[category] = score
                reasoning.append(f"Category '{category}' matched keywords: {matched_keywords}")
        
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            reasoning.append(f"Selected category: '{best_category}' (score: {category_scores[best_category]})")
            return best_category, reasoning
        
        reasoning.append("No category keywords found")
        return None, reasoning
    
    def extract_title(self, text: str) -> Tuple[str, List[str]]:
        """Extract task title from text"""
        reasoning = []
        
        # Remove time expressions and priority keywords for cleaner title
        clean_text = text
        for pattern in self.time_patterns.keys():
            clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
        
        for priority_keywords in self.priority_keywords.values():
            for keyword in priority_keywords:
                clean_text = clean_text.replace(keyword, '')
        
        # Remove common prefixes and clean up
        clean_text = re.sub(r'^(我要|需要|请|帮我|help me|need to|要)\s*', '', clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        if not clean_text:
            clean_text = text[:50]  # Fallback to first 50 chars
            reasoning.append("Used fallback title extraction")
        else:
            reasoning.append("Extracted title by removing time and priority keywords")
        
        # Limit title length
        if len(clean_text) > 100:
            clean_text = clean_text[:97] + "..."
            reasoning.append("Truncated title to 100 characters")
        
        return clean_text, reasoning
    
    def extract_tags(self, text: str, category: Optional[str] = None) -> Tuple[List[str], List[str]]:
        """Extract tags from text"""
        reasoning = []
        tags = []
        
        # Look for hashtags
        hashtag_matches = re.findall(r'#(\w+)', text)
        if hashtag_matches:
            tags.extend(hashtag_matches)
            reasoning.append(f"Found hashtags: {hashtag_matches}")
        
        # Add category as tag if available
        if category:
            tags.append(category)
            reasoning.append(f"Added category as tag: {category}")
        
        # Look for common tag patterns
        tag_patterns = {
            'frontend': ['前端', '界面', 'ui', 'frontend', 'vue', 'react'],
            'backend': ['后端', '服务器', 'api', 'backend', 'server'],
            'bug': ['bug', '错误', '问题', 'issue', '故障'],
            'feature': ['功能', '特性', 'feature', '需求'],
            'urgent': ['紧急', '急', 'urgent', 'hot']
        }
        
        text_lower = text.lower()
        for tag, keywords in tag_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                if tag not in tags:
                    tags.append(tag)
                    reasoning.append(f"Added inferred tag: {tag}")
        
        if not tags:
            reasoning.append("No tags found")
        
        return tags, reasoning
    
    def estimate_hours(self, text: str, category: Optional[str] = None) -> Tuple[float, List[str]]:
        """Estimate work hours from text"""
        reasoning = []
        
        # Look for explicit hour mentions
        hour_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:小时|hours?|h)', text, re.IGNORECASE)
        if hour_match:
            hours = float(hour_match.group(1))
            reasoning.append(f"Found explicit hour mention: {hours}")
            return hours, reasoning
        
        # Estimate based on category and task complexity
        base_estimates = {
            '会议': 1.0,
            '文档': 2.0,
            '设计': 4.0,
            '开发': 6.0,
            '测试': 3.0,
            '管理': 1.5
        }
        
        base_hours = base_estimates.get(category, 2.0)
        
        # Adjust based on complexity indicators
        complexity_multipliers = {
            'simple': 0.5, 'easy': 0.5, '简单': 0.5,
            'complex': 2.0, 'complicated': 2.0, '复杂': 2.0,
            'large': 1.5, 'big': 1.5, '大': 1.5,
            'small': 0.7, 'quick': 0.5, '小': 0.7, '快速': 0.5
        }
        
        text_lower = text.lower()
        for indicator, multiplier in complexity_multipliers.items():
            if indicator in text_lower:
                base_hours *= multiplier
                reasoning.append(f"Applied complexity multiplier {multiplier} for '{indicator}'")
                break
        
        reasoning.append(f"Base estimate for category '{category}': {base_hours} hours")
        return round(base_hours, 1), reasoning


class NLPService(AIServiceBase):
    """Natural Language Processing service for TaskWall v3.0"""
    
    def __init__(self, db, cache=None):
        super().__init__(db, cache)
        self.parser = TaskNLPParser()
    
    def get_operation_type(self) -> AIOperationType:
        return AIOperationType.PARSE
    
    def _process_internal(self, input_data: Dict[str, Any]) -> AIResult:
        """Process natural language text into structured tasks"""
        self._validate_input(input_data, ["text"])
        
        text = input_data["text"]
        context = input_data.get("context", {})
        
        # Determine if it's batch processing
        if self._is_batch_text(text):
            return self._process_batch_tasks(text, context)
        else:
            return self._process_single_task(text, context)
    
    def _is_batch_text(self, text: str) -> bool:
        """Check if text contains multiple tasks"""
        # Look for numbered lists, bullet points, or multiple sentences
        patterns = [
            r'^\s*\d+[\.\)]\s*',  # Numbered lists
            r'^\s*[-\*\+]\s*',    # Bullet points
            r'\n.*\n',            # Multiple lines
        ]
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # If multiple lines and any match list patterns
        if len(lines) > 1:
            for line in lines:
                for pattern in patterns:
                    if re.match(pattern, line):
                        return True
        
        return False
    
    def _process_single_task(self, text: str, context: Dict[str, Any]) -> AIResult:
        """Process single task from natural language"""
        try:
            # Use AI for complex parsing if available
            ai_result = self._try_ai_parsing(text, context)
            if ai_result:
                return ai_result
            
            # Fallback to rule-based parsing
            return self._rule_based_parsing(text, context)
            
        except Exception as e:
            return AIResult(
                success=False,
                data=None,
                confidence=0.0,
                reasoning=[f"Parsing failed: {str(e)}"],
                model_used="rule-based"
            )
    
    def _process_batch_tasks(self, text: str, context: Dict[str, Any]) -> AIResult:
        """Process multiple tasks from text"""
        try:
            # Split text into individual task segments
            task_segments = self._segment_tasks(text)
            
            parsed_tasks = []
            overall_confidence = 0.0
            overall_reasoning = []
            
            for i, segment in enumerate(task_segments):
                result = self._process_single_task(segment, context)
                if result.success and result.data:
                    parsed_tasks.extend(result.data if isinstance(result.data, list) else [result.data])
                    overall_confidence += result.confidence
                    if result.reasoning:
                        overall_reasoning.extend([f"Task {i+1}: {r}" for r in result.reasoning])
            
            # Calculate average confidence
            if parsed_tasks:
                overall_confidence = overall_confidence / len(task_segments)
            
            return AIResult(
                success=len(parsed_tasks) > 0,
                data=parsed_tasks,
                confidence=overall_confidence,
                reasoning=overall_reasoning,
                model_used="batch-processor"
            )
            
        except Exception as e:
            return AIResult(
                success=False,
                data=[],
                confidence=0.0,
                reasoning=[f"Batch parsing failed: {str(e)}"],
                model_used="batch-processor"
            )
    
    def _segment_tasks(self, text: str) -> List[str]:
        """Split text into individual task segments"""
        segments = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            # Remove list markers
            clean_line = re.sub(r'^\s*\d+[\.\)]\s*', '', line)
            clean_line = re.sub(r'^\s*[-\*\+]\s*', '', clean_line)
            
            if clean_line:
                segments.append(clean_line)
        
        return segments
    
    def _try_ai_parsing(self, text: str, context: Dict[str, Any]) -> Optional[AIResult]:
        """Try AI-powered parsing using Gemini"""
        try:
            # Construct AI prompt
            prompt = self._build_ai_prompt(text, context)
            
            # Call AI service
            ai_response = ask(prompt)
            
            # Handle different response formats
            if isinstance(ai_response, str):
                # Try to extract JSON from string response
                ai_task = self._extract_json_from_response(ai_response)
            elif isinstance(ai_response, list) and len(ai_response) > 0:
                ai_task = ai_response[0]
            elif isinstance(ai_response, dict):
                ai_task = ai_response
            else:
                return None
            
            if ai_task and isinstance(ai_task, dict):
                # Convert AI response to ParsedTask format
                parsed_task = self._convert_ai_response(ai_task, text)
                
                return AIResult(
                    success=True,
                    data=[parsed_task.__dict__],
                    confidence=ai_task.get('confidence', 0.8),
                    reasoning=ai_task.get('reasoning', ['AI parsed']),
                    model_used="gemini-pro"
                )
            
        except Exception as e:
            print(f"AI parsing failed: {e}")
        
        return None
    
    def _build_ai_prompt(self, text: str, context: Dict[str, Any]) -> str:
        """Build AI prompt for task parsing"""
        return f"""分析以下任务描述，提取关键信息并返回JSON：

输入文本："{text}"

请严格按照以下JSON格式返回，不要包含任何其他文字：

{{
    "title": "任务的简洁标题（从输入文本中提取或概括，不超过50字）",
    "description": "任务的详细描述（可选）",
    "priority": 优先级数字（0=紧急,1=高,2=中,3=低,4=待办），
    "category": "任务分类（开发/测试/会议/文档/设计/管理/其他）",
    "tags": ["相关标签数组"],
    "deadline": "截止时间ISO格式或null",
    "estimated_hours": 预估工时数字,
    "confidence": 解析置信度（0.0-1.0）,
    "reasoning": ["解析依据说明"]
}}

解析规则：
- 优先级关键词：紧急/急/立即→0，重要/高优先级→1，一般/正常/中等→2，低/不急→3，待办/以后→4
- 时间提取：明天、下周、几点、几天后等相对时间
- 工时提取：明确提到的小时数，如"2小时"、"半天"等
- 分类提取：开会→会议，开发/编程→开发，测试/检查→测试等

只返回JSON，不要任何解释文字。"""
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from AI response string"""
        try:
            # Try direct JSON parsing first
            return json.loads(response)
        except:
            pass
        
        try:
            # Look for JSON block in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return None
    
    def _convert_ai_response(self, ai_task: Dict[str, Any], original_text: str) -> ParsedTask:
        """Convert AI response to ParsedTask object"""
        # Parse deadline if provided
        deadline = None
        if ai_task.get('deadline'):
            try:
                deadline = datetime.fromisoformat(ai_task['deadline'].replace('Z', '+00:00'))
            except:
                pass
        
        return ParsedTask(
            title=ai_task.get('title', original_text[:50]),
            description=ai_task.get('description', ''),
            priority=max(0, min(4, ai_task.get('priority', 2))),
            category=ai_task.get('category'),
            tags=ai_task.get('tags', []),
            deadline=deadline,
            estimated_hours=max(0, ai_task.get('estimated_hours', 0.0)),
            confidence=ai_task.get('confidence', 0.8),
            reasoning=ai_task.get('reasoning', ['AI parsed'])
        )
    
    def _rule_based_parsing(self, text: str, context: Dict[str, Any]) -> AIResult:
        """Fallback rule-based parsing"""
        reasoning = []
        
        # Extract information using rule-based parser
        title, title_reasoning = self.parser.extract_title(text)
        priority, priority_reasoning = self.parser.extract_priority(text)
        deadline, time_reasoning = self.parser.extract_time(text)
        category, category_reasoning = self.parser.extract_category(text)
        tags, tag_reasoning = self.parser.extract_tags(text, category)
        estimated_hours, hours_reasoning = self.parser.estimate_hours(text, category)
        
        # Combine all reasoning
        reasoning.extend(title_reasoning)
        reasoning.extend(priority_reasoning)
        reasoning.extend(time_reasoning)
        reasoning.extend(category_reasoning)
        reasoning.extend(tag_reasoning)
        reasoning.extend(hours_reasoning)
        
        # Calculate confidence based on extracted information
        confidence = self._calculate_confidence(title, priority, deadline, category, tags)
        
        parsed_task = ParsedTask(
            title=title,
            description="",  # Rule-based doesn't generate descriptions
            priority=priority,
            category=category,
            tags=tags,
            deadline=deadline,
            estimated_hours=estimated_hours,
            confidence=confidence,
            reasoning=reasoning
        )
        
        return AIResult(
            success=True,
            data=[parsed_task.__dict__],
            confidence=confidence,
            reasoning=reasoning,
            model_used="rule-based"
        )
    
    def _calculate_confidence(self, title: str, priority: int, deadline: Optional[datetime], 
                            category: Optional[str], tags: List[str]) -> float:
        """Calculate parsing confidence score"""
        confidence = 0.5  # Base confidence
        
        # Title quality
        if len(title) > 5:
            confidence += 0.2
        
        # Priority extraction
        if priority != 2:  # Non-default priority
            confidence += 0.1
        
        # Time information
        if deadline:
            confidence += 0.15
        
        # Category detection
        if category:
            confidence += 0.1
        
        # Tags
        if tags:
            confidence += 0.05
        
        return min(1.0, confidence)