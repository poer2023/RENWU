import os
import json
from typing import Dict, List, Optional
import google.generativeai as genai

class AIClient:
    def __init__(self):
        self.api_key = None
        self.model = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize or re-initialize the AI client with current API key"""
        # First try environment variable (for backward compatibility)
        api_key = os.getenv("GEMINI_API_KEY")
        
        # If not found, try to get from database
        if not api_key:
            try:
                from ..models import Setting
                from ..deps import engine
                from sqlmodel import Session
                
                # Use the same database engine as the main app
                with Session(engine) as db:
                    setting = db.get(Setting, "gemini_api_key")
                    if setting:
                        api_key = setting.value
            except Exception as e:
                print(f"Failed to load API key from database: {e}")
        
        self.api_key = api_key
        if self.api_key and self.api_key.strip():
            try:
                genai.configure(api_key=self.api_key)
                
                # Try different model names in order of preference
                model_names = [
                    'gemini-1.5-flash',
                    'gemini-1.5-pro', 
                    'gemini-pro',
                    'models/gemini-1.5-flash',
                    'models/gemini-1.5-pro',
                    'models/gemini-pro'
                ]
                
                self.model = None
                for model_name in model_names:
                    try:
                        self.model = genai.GenerativeModel(model_name)
                        print(f"AI client initialized successfully with model: {model_name}")
                        break
                    except Exception as model_error:
                        print(f"Failed to initialize model {model_name}: {model_error}")
                        continue
                
                if not self.model:
                    print("Failed to initialize any Gemini model")
            except Exception as e:
                print(f"Failed to configure AI client: {e}")
                self.model = None
        else:
            self.model = None
            print("No API key found, AI features will use fallback methods")
    
    def refresh_api_key(self):
        """Refresh API key from database - call this when settings are updated"""
        self._initialize_client()

    def parse_tasks(self, prompt: str) -> List[Dict]:
        """
        Parse natural language text into structured tasks using AI
        
        Args:
            prompt: Natural language description of tasks
            
        Returns:
            List of task dictionaries with title, description, urgency, module
        """
        if not self.model:
            # Fallback when no API key is configured
            return self._fallback_parse(prompt)
        
        try:
            system_prompt = """
            You are a task parsing assistant. Convert the given text into a structured list of tasks.
            
            For each task, determine:
            - title: A concise task title (required)
            - description: Detailed description (optional)
            - urgency: Priority level 0-4 (0=P0/Critical, 1=P1/High, 2=P2/Medium, 3=P3/Low, 4=P4/Backlog)
            - module: Category/module name (optional, infer from context)
            - parent_id: If this is a subtask, reference parent task by its index in the list
            
            Return ONLY a valid JSON array of task objects. No other text.
            
            Example output:
            [
              {
                "title": "Setup project",
                "description": "Initialize the project repository and basic structure",
                "urgency": 1,
                "module": "Development"
              },
              {
                "title": "Write tests",
                "description": "Create unit tests for the main functionality",
                "urgency": 2,
                "module": "Development",
                "parent_id": 0
              }
            ]
            """
            
            full_prompt = f"{system_prompt}\n\nText to parse:\n{prompt}"
            
            response = self.model.generate_content(full_prompt)
            
            # Try to parse the JSON response
            try:
                tasks = json.loads(response.text.strip())
                if isinstance(tasks, list):
                    return tasks
                else:
                    return [tasks] if isinstance(tasks, dict) else []
            except json.JSONDecodeError:
                # Fallback to simple parsing if JSON parsing fails
                return self._fallback_parse(prompt)
            
        except Exception as e:
            print(f"AI parsing failed: {e}")
            return self._fallback_parse(prompt)
    
    def _fallback_parse(self, prompt: str) -> List[Dict]:
        """
        Enhanced fallback parsing when AI is not available
        """
        import re
        
        # Try to extract structured data first
        tasks = []
        
        # Look for date + person + tasks pattern
        date_person_pattern = r'(\d{4}-\d{2}-\d{2})\s+([^\n\r]+?)\s+(?:需要|需求|任务|todo|task)'
        date_person_match = re.search(date_person_pattern, prompt, re.IGNORECASE)
        
        extracted_date = None
        extracted_person = None
        
        if date_person_match:
            extracted_date = date_person_match.group(1)
            extracted_person = date_person_match.group(2)
        
        # Split by lines and look for task items
        lines = prompt.strip().split('\n')
        current_module = "General"
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Skip header lines that might contain date/person info or task header (do this first)
            if (date_person_match and line in date_person_match.group(0)) or \
               (extracted_date and extracted_date in line and extracted_person and extracted_person in line) or \
               any(keyword in line for keyword in ['需要完成以下任务', '以下任务', 'following tasks', 'todo list', '待办事项']):
                continue
            
            # Check if this line contains module information
            if any(keyword in line for keyword in ['模块', '分类', '类别', '项目', 'module', 'category', 'project']):
                # Extract module name
                module_match = re.search(r'[：:]\s*(.+)', line)
                if module_match:
                    current_module = module_match.group(1).strip()
                continue
                
            # Look for numbered or bulleted lists
            task_patterns = [
                r'^\d+[.)]\s*(.+)',  # 1. 2. 3.
                r'^[•\-\*]\s*(.+)',  # • - *
                r'^[a-zA-Z][.)]\s*(.+)',  # a) b) c)
                r'^[\u4e00-\u9fff][）)]\s*(.+)',  # 一) 二) 三)
            ]
            
            task_text = None
            for pattern in task_patterns:
                match = re.match(pattern, line)
                if match:
                    task_text = match.group(1).strip()
                    break
            
            # If no pattern matched, treat as a plain task
            if not task_text and len(line) > 3:
                task_text = line
            
            if task_text:
                # Simple heuristics for urgency detection
                urgency = 2  # default medium
                if any(word in task_text.lower() for word in ['urgent', 'critical', 'asap', 'p0', '紧急', '重要']):
                    urgency = 0
                elif any(word in task_text.lower() for word in ['high', 'important', 'p1', '高优先级']):
                    urgency = 1
                elif any(word in task_text.lower() for word in ['low', 'later', 'p3', '低优先级']):
                    urgency = 3
                elif any(word in task_text.lower() for word in ['backlog', 'someday', 'p4', '待定']):
                    urgency = 4
                
                # Create description with context
                description = ""
                if extracted_date or extracted_person:
                    description = f"由 {extracted_person or '未知'} 于 {extracted_date or '未知日期'} 提出"
                
                tasks.append({
                    "title": task_text[:100],  # Limit title length
                    "description": description,
                    "urgency": urgency,
                    "module": current_module
                })
        
        # If no structured tasks found, create one from the whole prompt
        if not tasks:
            tasks = [{
                "title": prompt[:100],
                "description": "",
                "urgency": 2,
                "module": "General"
            }]
        
        return tasks

    def execute_assistant_command(self, command: str, content: str, context: Optional[str] = None) -> str:
        """
        Execute AI assistant commands like rewrite, add-emoji, summarize, make-subtasks
        """
        if not self.model:
            return self._fallback_assistant_command(command, content)
        
        try:
            prompts = {
                'rewrite': f"""
                Rewrite the following text to be clearer and more concise while maintaining the original meaning:
                
                Original text: {content}
                
                Return ONLY the rewritten text, no explanations or additional content.
                """,
                
                'add-emoji': f"""
                Add appropriate emojis to the following text to make it more engaging:
                
                Original text: {content}
                
                Return ONLY the text with emojis added, no explanations.
                """,
                
                'summarize': f"""
                Create a concise summary of the following text:
                
                Text to summarize: {content}
                
                Return ONLY the summary, no explanations or additional content.
                """,
                
                'make-subtasks': f"""
                Break down the following task into 3-5 smaller, actionable subtasks:
                
                Main task: {content}
                Context: {context or 'No additional context'}
                
                Return ONLY a JSON array of subtask objects with 'title' and 'description' fields. No other text.
                
                Example format:
                [
                  {{"title": "Research requirements", "description": "Gather and analyze requirements"}},
                  {{"title": "Create plan", "description": "Develop implementation plan"}}
                ]
                """
            }
            
            prompt = prompts.get(command, f"Process this content: {content}")
            response = self.model.generate_content(prompt)
            
            return response.text.strip()
            
        except Exception as e:
            print(f"AI assistant command failed: {e}")
            return self._fallback_assistant_command(command, content)
    
    def _fallback_assistant_command(self, command: str, content: str) -> str:
        """
        Fallback for assistant commands when AI is not available
        """
        if command == 'rewrite':
            return content  # Return original content
        elif command == 'add-emoji':
            # Add some basic emojis based on keywords
            if any(word in content.lower() for word in ['bug', 'fix', 'error']):
                return f"🐛 {content}"
            elif any(word in content.lower() for word in ['feature', 'new', 'add']):
                return f"✨ {content}"
            elif any(word in content.lower() for word in ['test', 'testing']):
                return f"🧪 {content}"
            elif any(word in content.lower() for word in ['document', 'doc']):
                return f"📝 {content}"
            else:
                return f"📋 {content}"
        elif command == 'summarize':
            # Simple truncation as fallback
            return content[:100] + "..." if len(content) > 100 else content
        elif command == 'make-subtasks':
            # Simple subtask generation
            return json.dumps([
                {"title": f"Plan: {content[:30]}...", "description": "Create detailed plan"},
                {"title": f"Execute: {content[:30]}...", "description": "Implement the task"},
                {"title": f"Review: {content[:30]}...", "description": "Review and test"}
            ])
        else:
            return content

    def generate_subtasks(self, parent_title: str, parent_description: str, max_subtasks: int = 5) -> List[Dict]:
        """
        Generate subtasks for a parent task
        """
        if not self.model:
            return self._fallback_generate_subtasks(parent_title, parent_description, max_subtasks)
        
        try:
            print(f"Attempting to generate subtasks using AI model: {self.model}")
            prompt = f"""
            Generate {max_subtasks} subtasks for the following parent task:
            
            Title: {parent_title}
            Description: {parent_description}
            
            Each subtask should be:
            - Specific and actionable
            - Estimated to take 1-4 hours
            - Contribute to completing the parent task
            
            Return ONLY a valid JSON array of subtask objects with these fields:
            - title: Short, actionable title
            - description: Detailed description
            - urgency: Priority level 0-4 (inherit from parent or adjust based on criticality)
            
            Example output:
            [
              {{
                "title": "Research requirements",
                "description": "Gather and analyze all requirements for the task",
                "urgency": 2
              }},
              {{
                "title": "Create implementation plan",
                "description": "Develop step-by-step implementation approach",
                "urgency": 2
              }}
            ]
            """
            
            print(f"Sending request to Gemini API...")
            response = self.model.generate_content(prompt)
            print(f"Received response from Gemini: {response.text[:100]}...")
            
            try:
                # Clean the response text - remove markdown code blocks if present
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    # Extract JSON from markdown code block
                    start = response_text.find('```json') + 7
                    end = response_text.rfind('```')
                    if end > start:
                        response_text = response_text[start:end].strip()
                elif response_text.startswith('```'):
                    # Handle generic code block
                    start = response_text.find('```') + 3
                    end = response_text.rfind('```')
                    if end > start:
                        response_text = response_text[start:end].strip()
                
                print(f"Cleaned response text: {response_text[:200]}...")
                
                subtasks = json.loads(response_text)
                if isinstance(subtasks, list):
                    print(f"Successfully parsed {len(subtasks)} subtasks from AI")
                    return subtasks[:max_subtasks]  # Limit to max_subtasks
                else:
                    print(f"AI returned non-list response: {type(subtasks)}")
                    return [subtasks] if isinstance(subtasks, dict) else []
            except json.JSONDecodeError as json_error:
                print(f"Failed to parse JSON from AI response: {json_error}")
                print(f"Raw response was: {response.text}")
                return self._fallback_generate_subtasks(parent_title, parent_description, max_subtasks)
            
        except Exception as e:
            print(f"Subtask generation failed: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_generate_subtasks(parent_title, parent_description, max_subtasks)
    
    def _fallback_generate_subtasks(self, parent_title: str, parent_description: str, max_subtasks: int = 5) -> List[Dict]:
        """
        Fallback subtask generation when AI is not available
        """
        base_subtasks = [
            {
                "title": f"Plan: {parent_title}",
                "description": f"Create detailed plan for: {parent_description or parent_title}",
                "urgency": 2
            },
            {
                "title": f"Research: {parent_title}",
                "description": f"Research and gather information for: {parent_title}",
                "urgency": 2
            },
            {
                "title": f"Implement: {parent_title}",
                "description": f"Execute the main work for: {parent_title}",
                "urgency": 2
            },
            {
                "title": f"Review: {parent_title}",
                "description": f"Review and validate completion of: {parent_title}",
                "urgency": 3
            },
            {
                "title": f"Document: {parent_title}",
                "description": f"Document the process and results for: {parent_title}",
                "urgency": 3
            }
        ]
        
        return base_subtasks[:max_subtasks]

    def generate_weekly_report(self, tasks_data: List[Dict], start_date: str, end_date: str) -> str:
        """
        Generate a weekly report from tasks data
        """
        if not self.model:
            return self._fallback_weekly_report(tasks_data, start_date, end_date)
        
        try:
            # Categorize tasks
            completed_tasks = [task for task in tasks_data if task.get('status') == 'completed']
            in_progress_tasks = [task for task in tasks_data if task.get('status') == 'in_progress']
            pending_tasks = [task for task in tasks_data if task.get('status') == 'pending']
            
            prompt = f"""
            Generate a professional weekly report in Markdown format for the period {start_date} to {end_date}.
            
            Task Data:
            - Completed Tasks ({len(completed_tasks)}): {completed_tasks}
            - In Progress Tasks ({len(in_progress_tasks)}): {in_progress_tasks}  
            - Pending Tasks ({len(pending_tasks)}): {pending_tasks}
            
            Structure the report with these sections:
            1. **Executive Summary** - Brief overview of the week
            2. **Completed Tasks** - List of finished tasks with brief descriptions
            3. **In Progress** - Current ongoing work
            4. **Upcoming/Pending** - Tasks planned for next week
            5. **Risks & Blockers** - Any identified issues or concerns
            6. **Next Week's Plan** - Key objectives for the following week
            
            Keep it concise but informative. Use bullet points and clear formatting.
            Focus on achievements, progress, and planning.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Weekly report generation failed: {e}")
            return self._fallback_weekly_report(tasks_data, start_date, end_date)
    
    def _fallback_weekly_report(self, tasks_data: List[Dict], start_date: str, end_date: str) -> str:
        """
        Fallback weekly report generation when AI is not available
        """
        completed_tasks = [task for task in tasks_data if task.get('status') == 'completed']
        in_progress_tasks = [task for task in tasks_data if task.get('status') == 'in_progress']
        pending_tasks = [task for task in tasks_data if task.get('status') == 'pending']
        
        report = f"""# Weekly Report ({start_date} to {end_date})

## Executive Summary
This week we worked on {len(tasks_data)} total tasks, with {len(completed_tasks)} completed, {len(in_progress_tasks)} in progress, and {len(pending_tasks)} pending.

## Completed Tasks ({len(completed_tasks)})
"""
        
        for task in completed_tasks:
            report += f"- **{task.get('title', 'Untitled')}**: {task.get('description', 'No description')}\n"
        
        report += f"""
## In Progress ({len(in_progress_tasks)})
"""
        
        for task in in_progress_tasks:
            report += f"- **{task.get('title', 'Untitled')}**: {task.get('description', 'No description')}\n"
        
        report += f"""
## Upcoming Tasks ({len(pending_tasks)})
"""
        
        for task in pending_tasks:
            report += f"- **{task.get('title', 'Untitled')}**: {task.get('description', 'No description')}\n"
        
        report += """
## Next Week's Plan
- Continue work on in-progress tasks
- Begin work on pending tasks
- Review and prioritize upcoming work

---
*Generated by TaskWall v2.0*
"""
        
        return report

    def find_similar_tasks(self, new_task_title: str, new_task_description: str, existing_tasks: List[Dict], threshold: float = 0.85) -> List[Dict]:
        """
        Find similar tasks using embeddings or text similarity fallback
        """
        if not existing_tasks:
            return []
            
        try:
            # Try to use AI embeddings if available
            if self.model:
                return self._ai_similarity_detection(new_task_title, new_task_description, existing_tasks, threshold)
            else:
                return self._fallback_similarity_detection(new_task_title, new_task_description, existing_tasks, threshold)
        except Exception as e:
            print(f"Similarity detection failed: {e}")
            return self._fallback_similarity_detection(new_task_title, new_task_description, existing_tasks, threshold)
    
    def _ai_similarity_detection(self, new_task_title: str, new_task_description: str, existing_tasks: List[Dict], threshold: float) -> List[Dict]:
        """
        Use AI to find similar tasks (placeholder for future embedding implementation)
        """
        # For now, use text-based similarity as AI embedding APIs would require additional setup
        return self._fallback_similarity_detection(new_task_title, new_task_description, existing_tasks, threshold)
    
    def _fallback_similarity_detection(self, new_task_title: str, new_task_description: str, existing_tasks: List[Dict], threshold: float) -> List[Dict]:
        """
        Fallback similarity detection using text-based algorithms
        """
        import re
        from difflib import SequenceMatcher
        
        new_text = f"{new_task_title} {new_task_description}".lower().strip()
        similar_tasks = []
        
        for task in existing_tasks:
            task_text = f"{task.get('title', '')} {task.get('description', '')}".lower().strip()
            
            # Calculate similarity using multiple methods
            scores = []
            
            # 1. Sequence matcher similarity
            seq_similarity = SequenceMatcher(None, new_text, task_text).ratio()
            scores.append(seq_similarity)
            
            # 2. Word overlap similarity
            new_words = set(re.findall(r'\w+', new_text))
            task_words = set(re.findall(r'\w+', task_text))
            if new_words and task_words:
                word_overlap = len(new_words.intersection(task_words)) / len(new_words.union(task_words))
                scores.append(word_overlap)
            
            # 3. Title similarity (higher weight)
            title_similarity = SequenceMatcher(None, new_task_title.lower(), task.get('title', '').lower()).ratio()
            scores.append(title_similarity * 1.5)  # Give title higher weight
            
            # Calculate weighted average
            avg_similarity = sum(scores) / len(scores) if scores else 0
            
            # Check if above threshold
            if avg_similarity >= threshold:
                similar_tasks.append({
                    "task": task,
                    "similarity_score": round(avg_similarity, 3),
                    "match_type": self._get_match_type(avg_similarity, title_similarity)
                })
        
        # Sort by similarity score (highest first)
        similar_tasks.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return similar_tasks[:5]  # Return top 5 matches
    
    def _get_match_type(self, avg_similarity: float, title_similarity: float) -> str:
        """
        Determine the type of match based on similarity scores
        """
        if title_similarity > 0.9:
            return "exact_title"
        elif avg_similarity > 0.95:
            return "near_duplicate"
        elif avg_similarity > 0.9:
            return "very_similar"
        elif avg_similarity > 0.85:
            return "similar"
        else:
            return "related"

    def analyze_task_risks(self, tasks: List[Dict]) -> Dict:
        """
        Analyze tasks for emotional indicators and risks
        """
        try:
            if self.model:
                return self._ai_risk_analysis(tasks)
            else:
                return self._fallback_risk_analysis(tasks)
        except Exception as e:
            print(f"Risk analysis failed: {e}")
            return self._fallback_risk_analysis(tasks)
    
    def _ai_risk_analysis(self, tasks: List[Dict]) -> Dict:
        """
        Use AI to analyze task risks (placeholder for future implementation)
        """
        # For now, use fallback analysis as comprehensive AI risk analysis would require specific training
        return self._fallback_risk_analysis(tasks)
    
    def _fallback_risk_analysis(self, tasks: List[Dict]) -> Dict:
        """
        Enhanced fallback risk analysis using advanced keyword detection and heuristics
        """
        import re
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        risky_tasks = []
        risk_summary = {
            "total_tasks": len(tasks),
            "high_risk": 0,
            "medium_risk": 0,
            "low_risk": 0,
            "risk_categories": {
                "delay": 0,
                "blocked": 0,
                "external_dependency": 0,
                "complexity": 0,
                "emotional_stress": 0,
                "resource_conflict": 0,
                "technical_debt": 0,
                "communication": 0
            },
            "risk_trends": {},
            "project_health_score": 0
        }
        
        # Enhanced risk detection keywords with weights and negation handling
        risk_keywords = {
            "delay": {
                "positive": ["延期", "推迟", "拖延", "延误", "滞后", "超期", "deadline", "late", "overdue", "behind", "慢", "赶不上"],
                "negative": ["不延期", "按时", "提前", "on time", "ahead"],
                "weight": 3
            },
            "blocked": {
                "positive": ["卡住", "阻塞", "等待", "依赖", "blocked", "waiting", "stuck", "pending", "暂停", "无法进行"],
                "negative": ["解除", "畅通", "继续", "unblocked", "proceeding"],
                "weight": 4
            },
            "external_dependency": {
                "positive": ["外部", "第三方", "依赖", "等待", "external", "third-party", "dependency", "vendor", "供应商"],
                "negative": ["内部", "自主", "independent", "internal"],
                "weight": 2
            },
            "complexity": {
                "positive": ["复杂", "困难", "challenging", "complex", "difficult", "unclear", "uncertain", "不确定", "模糊"],
                "negative": ["简单", "清晰", "明确", "simple", "clear", "straightforward"],
                "weight": 2
            },
            "emotional_stress": {
                "positive": ["压力", "紧急", "焦虑", "困扰", "stress", "urgent", "pressure", "worried", "confused", "疲惫", "加班"],
                "negative": ["轻松", "从容", "calm", "relaxed", "confident"],
                "weight": 3
            },
            "resource_conflict": {
                "positive": ["资源不足", "人手不够", "冲突", "竞争", "resource", "conflict", "shortage", "缺少"],
                "negative": ["资源充足", "人员到位", "sufficient", "adequate"],
                "weight": 3
            },
            "technical_debt": {
                "positive": ["技术债", "重构", "优化", "debt", "refactor", "legacy", "老代码", "维护困难"],
                "negative": ["新架构", "现代化", "clean", "optimized"],
                "weight": 2
            },
            "communication": {
                "positive": ["沟通问题", "理解偏差", "需求不明", "miscommunication", "unclear", "confusion", "误解"],
                "negative": ["沟通顺畅", "理解一致", "clear communication", "aligned"],
                "weight": 2
            }
        }
        
        # Build task dependency map for relationship analysis
        task_dependencies = defaultdict(list)
        for task in tasks:
            deps = task.get('dependencies', [])
            if deps:
                for dep in deps:
                    task_dependencies[task.get('id')].append(dep)
        
        # Analyze each task
        for task in tasks:
            task_text = f"{task.get('title', '')} {task.get('description', '')}".lower()
            task_risks = []
            risk_score = 0
            confidence_score = 1.0
            
            # Enhanced keyword analysis with negation handling
            for category, keyword_data in risk_keywords.items():
                positive_matches = sum(1 for keyword in keyword_data["positive"] if keyword in task_text)
                negative_matches = sum(1 for keyword in keyword_data["negative"] if keyword in task_text)
                
                # Calculate net risk score for this category
                net_matches = positive_matches - negative_matches
                if net_matches > 0:
                    task_risks.append(category)
                    risk_summary["risk_categories"][category] += 1
                    category_score = net_matches * keyword_data["weight"]
                    risk_score += category_score
                    
                    # Adjust confidence based on keyword strength
                    confidence_score *= (1 + 0.1 * positive_matches)
            
            # Dependency risk analysis
            task_id = task.get('id')
            if task_id in task_dependencies:
                dependency_count = len(task_dependencies[task_id])
                if dependency_count > 3:
                    task_risks.append("high_dependency")
                    risk_score += dependency_count * 0.5
                    
            # Cross-task relationship risk
            related_tasks = [t for t in tasks if t.get('module_id') == task.get('module_id') and t.get('id') != task.get('id')]
            if len(related_tasks) > 5:
                # High task density in module might indicate resource conflicts
                task_risks.append("resource_conflict")
                risk_score += 1
            
            # Priority-based risk with more nuanced scoring
            urgency = task.get('urgency', 2)
            if urgency == 0:  # P0 - Critical
                risk_score += 3
                task_risks.append("critical_priority")
            elif urgency == 1:  # P1 - High
                risk_score += 2
            elif urgency == 2:  # P2 - Medium
                risk_score += 0.5
            
            # Enhanced age-based risk analysis
            try:
                created_date = datetime.fromisoformat(task.get('created_at', '').replace('Z', '+00:00'))
                current_time = datetime.now().replace(tzinfo=created_date.tzinfo)
                days_old = (current_time - created_date).days
                
                # Progressive age-based risk
                if days_old > 60:
                    risk_score += 2
                    task_risks.append("very_stale")
                elif days_old > 30:
                    risk_score += 1.5
                    task_risks.append("stale")
                elif days_old > 14:
                    risk_score += 0.5
                    
                # Check for deadline proximity if available
                if task.get('due_date'):
                    try:
                        due_date = datetime.fromisoformat(task.get('due_date', '').replace('Z', '+00:00'))
                        days_until_due = (due_date - current_time).days
                        if days_until_due < 0:
                            risk_score += 4  # Overdue
                            task_risks.append("overdue")
                        elif days_until_due <= 1:
                            risk_score += 3  # Due soon
                            task_risks.append("due_soon")
                        elif days_until_due <= 3:
                            risk_score += 1
                    except:
                        pass
            except:
                pass
            
            # Task complexity analysis based on description length and content
            description_length = len(task.get('description', ''))
            if description_length > 500:
                risk_score += 0.5  # Very detailed tasks might be complex
            elif description_length < 20:
                risk_score += 0.3  # Very short descriptions might be unclear
                task_risks.append("unclear_scope")
            
            # Apply confidence adjustment
            final_risk_score = risk_score * confidence_score
            
            # Enhanced risk level determination with confidence consideration
            if final_risk_score >= 6:
                risk_level = "critical"
                risk_summary["high_risk"] += 1
            elif final_risk_score >= 4:
                risk_level = "high"
                risk_summary["high_risk"] += 1
            elif final_risk_score >= 2:
                risk_level = "medium" 
                risk_summary["medium_risk"] += 1
            else:
                risk_level = "low"
                risk_summary["low_risk"] += 1
            
            # Add to risky tasks if above threshold
            if final_risk_score >= 1.5:
                risky_tasks.append({
                    "task": task,
                    "risk_level": risk_level,
                    "risk_score": round(final_risk_score, 1),
                    "confidence_score": round(confidence_score, 2),
                    "risk_categories": list(set(task_risks)),
                    "recommendations": self._get_enhanced_risk_recommendations(task_risks, task, final_risk_score),
                    "priority_adjustment": self._calculate_priority_adjustment(task_risks, urgency),
                    "estimated_impact": self._estimate_task_impact(task, task_risks)
                })
        
        # Calculate project health score
        total_tasks = len(tasks)
        if total_tasks > 0:
            health_score = max(0, 100 - (
                (risk_summary["high_risk"] * 15) + 
                (risk_summary["medium_risk"] * 5) + 
                (risk_summary["low_risk"] * 1)
            ) / total_tasks * 100)
            risk_summary["project_health_score"] = round(health_score, 1)
        
        # Calculate risk trends (placeholder for historical data)
        risk_summary["risk_trends"] = self._calculate_risk_trends(risky_tasks)
        
        # Sort by risk score and confidence
        risky_tasks.sort(key=lambda x: (x["risk_score"], x["confidence_score"]), reverse=True)
        
        # Enhanced return with more insights
        return {
            "risk_summary": risk_summary,
            "risky_tasks": risky_tasks[:15],  # Top 15 risky tasks
            "suggestions": self._generate_enhanced_risk_suggestions(risk_summary, risky_tasks),
            "risk_distribution": self._calculate_risk_distribution(risky_tasks),
            "action_items": self._generate_action_items(risky_tasks[:5]),  # Top 5 for immediate action
            "project_insights": self._generate_project_insights(risk_summary, tasks)
        }
    
    def _get_enhanced_risk_recommendations(self, risk_categories: List[str], task: Dict, risk_score: float) -> List[str]:
        """
        Generate enhanced recommendations based on detected risk categories and context
        """
        recommendations = []
        urgency = task.get('urgency', 2)
        
        # Priority-based recommendations
        if "delay" in risk_categories:
            if urgency <= 1:
                recommendations.append("🚨 高优先级任务延期 - 立即重新安排资源和时间线")
            else:
                recommendations.append("📅 重新评估时间安排，考虑分解为更小的任务")
                
        if "blocked" in risk_categories:
            recommendations.append("🚫 识别阻塞原因，建立每日站会跟踪解除进度")
            if urgency <= 1:
                recommendations.append("⚡ 高优先级阻塞 - 考虑升级到管理层处理")
                
        if "external_dependency" in risk_categories:
            recommendations.append("🔗 建立外部依赖跟踪看板，设置定期检查点")
            recommendations.append("🔄 准备备选方案，减少对外部依赖的风险")
            
        if "complexity" in risk_categories:
            recommendations.append("🧩 分解复杂任务为可管理的子任务")
            if risk_score > 4:
                recommendations.append("👥 寻求技术专家支持或增加团队资源")
                
        if "emotional_stress" in risk_categories:
            recommendations.append("💪 关注团队心理健康，考虑工作负载重新分配")
            recommendations.append("🎯 设置更现实的期望和里程碑")
            
        if "resource_conflict" in risk_categories:
            recommendations.append("⚖️ 审查资源分配，优化任务优先级")
            recommendations.append("📊 使用工作负载分析工具平衡团队任务")
            
        if "technical_debt" in risk_categories:
            recommendations.append("🔧 安排技术债务清理时间，防止累积")
            
        if "communication" in risk_categories:
            recommendations.append("💬 加强团队沟通，明确需求和期望")
            
        if "stale" in risk_categories or "very_stale" in risk_categories:
            recommendations.append("🗑️ 审查任务相关性，考虑更新、合并或关闭")
            
        if "overdue" in risk_categories:
            recommendations.append("⏰ 任务已逾期 - 立即评估影响并制定恢复计划")
            
        if "due_soon" in risk_categories:
            recommendations.append("⏳ 任务即将到期 - 确保资源就位并准备交付")
            
        if "unclear_scope" in risk_categories:
            recommendations.append("📝 完善任务描述，明确验收标准和范围")
        
        # Generic recommendations based on risk score
        if risk_score > 5:
            recommendations.append("🎯 建议将此任务标记为本周重点关注项")
        
        if not recommendations:
            recommendations.append("✅ 定期更新任务状态，保持团队沟通畅通")
            
        return recommendations[:4]  # Limit to top 4 recommendations
    
    def _calculate_priority_adjustment(self, risk_categories: List[str], current_urgency: int) -> Dict:
        """
        Calculate suggested priority adjustment based on risk factors
        """
        adjustment = 0
        reasons = []
        
        if "overdue" in risk_categories:
            if current_urgency > 0:  # Only adjust if not already P0
                adjustment = current_urgency  # Boost to P0
                reasons.append("任务已逾期")
            
        if "blocked" in risk_categories and current_urgency > 1:
            adjustment = max(adjustment, 1)  # At least boost by 1
            reasons.append("任务被阻塞")
            
        if "critical_priority" in risk_categories:
            adjustment = 0  # Already at highest priority
            
        return {
            "suggested_urgency": max(0, current_urgency - adjustment),
            "adjustment": adjustment,
            "reasons": reasons
        }
    
    def _estimate_task_impact(self, task: Dict, risk_categories: List[str]) -> Dict:
        """
        Estimate the potential impact of task risks
        """
        impact_score = 1.0
        impact_areas = []
        
        # Base impact on task priority
        urgency = task.get('urgency', 2)
        if urgency == 0:
            impact_score *= 3
            impact_areas.append("关键业务功能")
        elif urgency == 1:
            impact_score *= 2
            impact_areas.append("重要项目里程碑")
            
        # Impact based on risk categories
        if "blocked" in risk_categories:
            impact_score *= 1.5
            impact_areas.append("下游任务进度")
            
        if "external_dependency" in risk_categories:
            impact_score *= 1.3
            impact_areas.append("合作伙伴关系")
            
        if "delay" in risk_categories:
            impact_areas.append("项目交付时间")
            
        return {
            "impact_score": round(impact_score, 1),
            "impact_areas": impact_areas,
            "severity": "高" if impact_score > 3 else "中" if impact_score > 1.5 else "低"
        }
    
    def _calculate_risk_trends(self, risky_tasks: List[Dict]) -> Dict:
        """
        Calculate risk trends (placeholder for historical analysis)
        """
        # This would use historical data in a real implementation
        return {
            "trend_direction": "stable",  # up, down, stable
            "weekly_change": 0,
            "risk_velocity": "正常",  # 风险产生速度
            "resolution_rate": "待分析"  # 风险解决率
        }
    
    def _calculate_risk_distribution(self, risky_tasks: List[Dict]) -> Dict:
        """
        Calculate risk distribution across categories and modules
        """
        category_distribution = {}
        module_distribution = {}
        
        for risky_task in risky_tasks:
            # Category distribution
            for category in risky_task["risk_categories"]:
                category_distribution[category] = category_distribution.get(category, 0) + 1
                
            # Module distribution
            module_id = risky_task["task"].get("module_id", "未分类")
            module_distribution[str(module_id)] = module_distribution.get(str(module_id), 0) + 1
        
        return {
            "by_category": category_distribution,
            "by_module": module_distribution,
            "total_risky_tasks": len(risky_tasks)
        }
    
    def _generate_action_items(self, top_risky_tasks: List[Dict]) -> List[Dict]:
        """
        Generate specific action items for top risky tasks
        """
        action_items = []
        
        for task in top_risky_tasks:
            action_item = {
                "task_id": task["task"].get("id"),
                "task_title": task["task"].get("title", ""),
                "urgency": "高" if task["risk_score"] > 4 else "中",
                "action": self._get_primary_action(task["risk_categories"]),
                "owner": "待分配",
                "deadline": "本周内" if task["risk_score"] > 4 else "下周内"
            }
            action_items.append(action_item)
            
        return action_items
    
    def _get_primary_action(self, risk_categories: List[str]) -> str:
        """
        Get the primary recommended action for a task
        """
        if "overdue" in risk_categories:
            return "立即制定恢复计划"
        elif "blocked" in risk_categories:
            return "解除阻塞因素"
        elif "delay" in risk_categories:
            return "重新安排时间线"
        elif "complexity" in risk_categories:
            return "分解任务或寻求支持"
        elif "emotional_stress" in risk_categories:
            return "调整工作负载"
        else:
            return "评估和监控"
    
    def _generate_project_insights(self, risk_summary: Dict, tasks: List[Dict]) -> Dict:
        """
        Generate high-level project insights
        """
        total_tasks = len(tasks)
        health_score = risk_summary.get("project_health_score", 0)
        
        insights = {
            "overall_health": "良好" if health_score > 80 else "一般" if health_score > 60 else "需要关注",
            "key_concerns": [],
            "strengths": [],
            "recommendations": []
        }
        
        # Analyze key concerns
        high_risk_ratio = risk_summary["high_risk"] / total_tasks if total_tasks > 0 else 0
        if high_risk_ratio > 0.2:
            insights["key_concerns"].append(f"高风险任务占比过高 ({high_risk_ratio:.1%})")
            
        # Analyze strengths
        low_risk_ratio = risk_summary["low_risk"] / total_tasks if total_tasks > 0 else 0
        if low_risk_ratio > 0.7:
            insights["strengths"].append("大部分任务风险可控")
            
        # Generate recommendations
        if health_score < 70:
            insights["recommendations"].append("建议召开风险评审会议")
            insights["recommendations"].append("重新评估项目优先级和资源分配")
        
        return insights
    
    def _generate_enhanced_risk_suggestions(self, risk_summary: Dict, risky_tasks: List[Dict]) -> List[str]:
        """
        Generate enhanced overall risk management suggestions
        """
        suggestions = []
        
        high_risk_count = risk_summary["high_risk"]
        total_tasks = risk_summary["total_tasks"]
        health_score = risk_summary.get("project_health_score", 100)
        
        # Health-based suggestions
        if health_score < 50:
            suggestions.append("🚨 项目健康度严重偏低，建议立即召开紧急风险评审会议")
        elif health_score < 70:
            suggestions.append("⚠️ 项目健康度需要关注，建议重新评估优先级和资源分配")
        elif health_score > 85:
            suggestions.append("✅ 项目健康度良好，继续保持当前管理水平")
        
        # Risk ratio analysis
        if high_risk_count > total_tasks * 0.3:
            suggestions.append("📊 高风险任务占比过高，建议进行任务优先级重排")
        
        # Category-specific suggestions
        if risk_summary["risk_categories"]["blocked"] > 0:
            suggestions.append("🚫 存在阻塞任务，建议建立阻塞问题升级机制")
            
        if risk_summary["risk_categories"]["delay"] > 0:
            suggestions.append("⏰ 存在延期风险，建议启动时间线重新规划")
            
        if risk_summary["risk_categories"]["emotional_stress"] > 0:
            suggestions.append("💪 团队压力较大，建议进行工作负载平衡分析")
            
        if risk_summary["risk_categories"]["external_dependency"] > 0:
            suggestions.append("🔗 外部依赖风险较高，建议建立供应商管理流程")
            
        if risk_summary["risk_categories"]["resource_conflict"] > 0:
            suggestions.append("⚖️ 资源冲突风险，建议优化资源分配策略")
        
        # Trend-based suggestions (placeholder)
        trends = risk_summary.get("risk_trends", {})
        if trends.get("trend_direction") == "up":
            suggestions.append("📈 风险趋势上升，建议加强监控频率")
        
        if not suggestions:
            suggestions.append("✅ 项目风险整体可控，继续保持良好的任务管理")
            
        return suggestions[:5]  # Limit to top 5 suggestions

    def create_theme_islands(self, tasks: List[Dict]) -> Dict:
        """
        Create theme islands by clustering similar tasks
        """
        try:
            if self.model:
                return self._ai_theme_clustering(tasks)
            else:
                return self._fallback_theme_clustering(tasks)
        except Exception as e:
            print(f"Theme island creation failed: {e}")
            return self._fallback_theme_clustering(tasks)
    
    def _ai_theme_clustering(self, tasks: List[Dict]) -> Dict:
        """
        Use AI to create theme islands using semantic similarity
        """
        try:
            if len(tasks) < 2:
                return {
                    "islands": [{"id": 1, "name": "所有任务", "color": "#1890ff", "tasks": tasks}],
                    "island_stats": {"total_islands": 1, "total_tasks": len(tasks)},
                    "suggestions": []
                }
            
            # Use AI to analyze and cluster tasks
            cluster_prompt = f"""
            分析以下 {len(tasks)} 个任务，根据主题相似性将它们分组为主题岛。
            
            任务列表：
            {json.dumps([{"id": t["id"], "title": t["title"], "description": t["description"]} for t in tasks], ensure_ascii=False, indent=2)}
            
            请按照以下要求分组：
            1. 每个主题岛至少3个任务
            2. 少于3个任务的归为"杂项"
            3. 为每个岛取一个简洁的中文名称
            4. 提供3个关键词描述每个岛的主题
            5. 最多创建6个主题岛
            
            返回JSON格式（不要其他文字）：
            {{
                "islands": [
                    {{
                        "id": 1,
                        "name": "岛屿名称",
                        "keywords": ["关键词1", "关键词2", "关键词3"],
                        "task_ids": [1, 2, 3]
                    }}
                ],
                "suggestions": ["建议1", "建议2"]
            }}
            """
            
            response = self.model.generate_content(cluster_prompt)
            result_text = response.text.strip()
            
            # Parse AI response
            try:
                ai_result = json.loads(result_text)
                return self._process_ai_clustering_result(ai_result, tasks)
            except json.JSONDecodeError:
                print(f"Failed to parse AI clustering result: {result_text}")
                return self._fallback_theme_clustering(tasks)
                
        except Exception as e:
            print(f"AI clustering failed: {e}")
            return self._fallback_theme_clustering(tasks)
    
    def _process_ai_clustering_result(self, ai_result: Dict, tasks: List[Dict]) -> Dict:
        """
        Process AI clustering result and assign colors
        """
        # Create a task lookup dict
        task_dict = {task["id"]: task for task in tasks}
        
        # Define color palette for islands
        colors = [
            "#FF6B6B",  # Red
            "#4ECDC4",  # Teal  
            "#45B7D1",  # Blue
            "#96CEB4",  # Green
            "#FFEAA7",  # Yellow
            "#DDA0DD",  # Plum
            "#F4A261",  # Orange
            "#E9C46A"   # Gold
        ]
        
        islands = []
        island_stats = {
            "total_islands": 0,
            "total_tasks": len(tasks),
            "island_distribution": {}
        }
        
        for i, ai_island in enumerate(ai_result.get("islands", [])):
            island_tasks = []
            
            # Get tasks for this island
            for task_id in ai_island.get("task_ids", []):
                if task_id in task_dict:
                    task = task_dict[task_id].copy()
                    task["island_id"] = ai_island["id"]
                    island_tasks.append(task)
            
            if island_tasks:  # Only create island if it has tasks
                island = {
                    "id": ai_island["id"],
                    "name": ai_island.get("name", f"主题岛 {i+1}"),
                    "color": colors[i % len(colors)],
                    "keywords": ai_island.get("keywords", []),
                    "tasks": island_tasks,
                    "size": len(island_tasks)
                }
                
                islands.append(island)
                island_stats["island_distribution"][island["name"]] = len(island_tasks)
        
        # Handle any remaining unassigned tasks
        assigned_task_ids = set()
        for island in islands:
            for task in island["tasks"]:
                assigned_task_ids.add(task["id"])
        
        unassigned_tasks = [task for task in tasks if task["id"] not in assigned_task_ids]
        if unassigned_tasks:
            misc_island = {
                "id": len(islands) + 1,
                "name": "杂项",
                "color": "#95A5A6",  # Gray
                "keywords": ["其他", "杂项"],
                "tasks": unassigned_tasks,
                "size": len(unassigned_tasks)
            }
            islands.append(misc_island)
            island_stats["island_distribution"]["杂项"] = len(unassigned_tasks)
        
        island_stats["total_islands"] = len(islands)
        
        return {
            "islands": islands,
            "island_stats": island_stats,
            "suggestions": ai_result.get("suggestions", [])
        }
    
    def _fallback_theme_clustering(self, tasks: List[Dict]) -> Dict:
        """
        Fallback theme clustering using keyword analysis and similarity
        """
        import re
        from collections import defaultdict, Counter
        
        if len(tasks) < 2:
            return {
                "islands": [{"id": 1, "name": "所有任务", "color": "#1890ff", "tasks": tasks}],
                "island_stats": {"total_islands": 1, "total_tasks": len(tasks)},
                "suggestions": ["任务数量较少，无需聚类分组"]
            }
        
        # Extract keywords from all tasks
        all_keywords = []
        task_keywords = {}
        
        for task in tasks:
            text = f"{task.get('title', '')} {task.get('description', '')}".lower()
            # Extract meaningful keywords (length > 2, Chinese/English)
            keywords = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]{3,}', text)
            # Filter common words
            filtered_keywords = [k for k in keywords if k not in ['the', 'and', 'task', '任务', '项目', '需要', '完成']]
            
            task_keywords[task.get('id')] = filtered_keywords
            all_keywords.extend(filtered_keywords)
        
        # Find most common themes
        keyword_counts = Counter(all_keywords)
        top_themes = [word for word, count in keyword_counts.most_common(8) if count > 1]
        
        # Create theme-based islands
        islands = []
        used_tasks = set()
        
        # Pre-defined island colors
        island_colors = [
            "#ff4d4f", "#fa8c16", "#fadb14", "#52c41a", 
            "#1890ff", "#722ed1", "#eb2f96", "#13c2c2"
        ]
        
        # Create islands based on common themes
        for i, theme in enumerate(top_themes):
            island_tasks = []
            for task in tasks:
                if task.get('id') in used_tasks:
                    continue
                    
                task_keywords_list = task_keywords.get(task.get('id'), [])
                if theme in task_keywords_list:
                    island_tasks.append(task)
                    used_tasks.add(task.get('id'))
            
            if island_tasks:
                islands.append({
                    "id": i + 1,
                    "name": f"{theme.title()} 相关",
                    "theme": theme,
                    "color": island_colors[i % len(island_colors)],
                    "tasks": island_tasks,
                    "task_count": len(island_tasks)
                })
        
        # Group remaining tasks by module or urgency
        remaining_tasks = [task for task in tasks if task.get('id') not in used_tasks]
        
        if remaining_tasks:
            # Group by module first
            module_groups = defaultdict(list)
            for task in remaining_tasks:
                module_id = task.get('module_id', 0)
                module_groups[module_id].append(task)
            
            for module_id, module_tasks in module_groups.items():
                if len(module_tasks) >= 2:  # Only create island if multiple tasks
                    islands.append({
                        "id": len(islands) + 1,
                        "name": f"模块 {module_id}",
                        "theme": "module",
                        "color": island_colors[len(islands) % len(island_colors)],
                        "tasks": module_tasks,
                        "task_count": len(module_tasks)
                    })
                    for task in module_tasks:
                        used_tasks.add(task.get('id'))
        
        # Put any remaining tasks in a "misc" island
        final_remaining = [task for task in tasks if task.get('id') not in used_tasks]
        if final_remaining:
            islands.append({
                "id": len(islands) + 1,
                "name": "其他任务",
                "theme": "misc",
                "color": "#8c8c8c",
                "tasks": final_remaining,
                "task_count": len(final_remaining)
            })
        
        # Generate statistics
        island_stats = {
            "total_islands": len(islands),
            "total_tasks": len(tasks),
            "largest_island": max(islands, key=lambda x: x["task_count"])["name"] if islands else None,
            "theme_distribution": {island["name"]: island["task_count"] for island in islands}
        }
        
        # Generate suggestions
        suggestions = self._generate_island_suggestions(islands, island_stats)
        
        return {
            "islands": islands,
            "island_stats": island_stats,
            "suggestions": suggestions
        }
    
    def _generate_island_suggestions(self, islands: List[Dict], stats: Dict) -> List[str]:
        """
        Generate suggestions based on island clustering results
        """
        suggestions = []
        
        total_islands = stats["total_islands"]
        total_tasks = stats["total_tasks"]
        
        if total_islands == 1:
            suggestions.append("所有任务被归为一类，考虑为不同类型的任务创建更具体的描述")
        elif total_islands > 6:
            suggestions.append("任务分类较为分散，可以考虑合并相似的主题")
        else:
            suggestions.append(f"任务已被合理分为 {total_islands} 个主题组")
        
        # Find largest island
        largest_island = max(islands, key=lambda x: x["task_count"]) if islands else None
        if largest_island and largest_island["task_count"] > total_tasks * 0.5:
            suggestions.append(f"'{largest_island['name']}' 主题包含过多任务，建议进一步细分")
        
        # Check for single-task islands
        single_task_islands = [island for island in islands if island["task_count"] == 1]
        if len(single_task_islands) > 3:
            suggestions.append("存在多个独立任务，考虑是否可以与其他主题合并")
        
        return suggestions

# Global instance
ai_client = AIClient()

def ask(prompt: str) -> List[Dict]:
    """Ask AI a question and get structured response"""
    client = AIClient()
    
    # Check if this is a task parsing request
    if any(keyword in prompt.lower() for keyword in ['json格式', 'json', '解析', '提取', 'parse']):
        # For single task parsing, call the model directly
        if not client.model:
            return []
        
        try:
            response = client.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Try to extract JSON from response
            import json
            import re
            
            # First try direct JSON parsing
            try:
                result = json.loads(response_text)
                return [result] if isinstance(result, dict) else result
            except:
                pass
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return [result] if isinstance(result, dict) else result
                except:
                    pass
            
            # If no JSON found, return empty
            return []
            
        except Exception as e:
            print(f"Direct AI call failed: {e}")
            return []
    else:
        # For other requests, use the original parse_tasks method
        return client.parse_tasks(prompt)

def assistant_command(command: str, content: str, context: Optional[str] = None) -> str:
    """
    Execute AI assistant commands
    """
    return ai_client.execute_assistant_command(command, content, context)

def generate_subtasks(parent_title: str, parent_description: str, max_subtasks: int = 5) -> List[Dict]:
    """
    Generate subtasks for a parent task
    """
    return ai_client.generate_subtasks(parent_title, parent_description, max_subtasks)

def generate_weekly_report(tasks_data: List[Dict], start_date: str, end_date: str) -> str:
    """
    Generate a weekly report from tasks data
    """
    return ai_client.generate_weekly_report(tasks_data, start_date, end_date)

def find_similar_tasks(new_task_title: str, new_task_description: str, existing_tasks: List[Dict], threshold: float = 0.85) -> List[Dict]:
    """
    Find similar tasks using embeddings or text similarity
    """
    return ai_client.find_similar_tasks(new_task_title, new_task_description, existing_tasks, threshold)

def analyze_task_risks(tasks: List[Dict]) -> Dict:
    """
    Analyze tasks for risks and emotional indicators
    """
    return ai_client.analyze_task_risks(tasks)

def create_theme_islands(tasks: List[Dict]) -> Dict:
    """
    Create theme islands by clustering similar tasks
    """
    return ai_client.create_theme_islands(tasks)