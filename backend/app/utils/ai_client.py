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
        Fallback risk analysis using keyword detection and heuristics
        """
        import re
        from datetime import datetime, timedelta
        
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
                "emotional_stress": 0
            }
        }
        
        # Risk detection keywords
        risk_keywords = {
            "delay": ["延期", "推迟", "拖延", "延误", "滞后", "超期", "deadline", "late", "overdue"],
            "blocked": ["卡住", "阻塞", "等待", "依赖", "blocked", "waiting", "stuck", "pending"],
            "external_dependency": ["外部", "第三方", "依赖", "等待", "external", "third-party", "dependency"],
            "complexity": ["复杂", "困难", "challenging", "complex", "difficult", "unclear", "uncertain"],
            "emotional_stress": ["压力", "紧急", "焦虑", "困扰", "stress", "urgent", "pressure", "worried", "confused"]
        }
        
        for task in tasks:
            task_text = f"{task.get('title', '')} {task.get('description', '')}".lower()
            task_risks = []
            risk_score = 0
            
            # Check for risk indicators
            for category, keywords in risk_keywords.items():
                for keyword in keywords:
                    if keyword in task_text:
                        task_risks.append(category)
                        risk_summary["risk_categories"][category] += 1
                        
                        # Risk scoring
                        if category in ["delay", "blocked"]:
                            risk_score += 3
                        elif category in ["external_dependency", "emotional_stress"]:
                            risk_score += 2
                        else:
                            risk_score += 1
                        break
            
            # Priority-based risk (high priority tasks are inherently risky)
            urgency = task.get('urgency', 2)
            if urgency <= 1:  # P0, P1
                risk_score += 2
            
            # Age-based risk (old tasks might be stale)
            try:
                created_date = datetime.fromisoformat(task.get('created_at', '').replace('Z', '+00:00'))
                days_old = (datetime.now().replace(tzinfo=created_date.tzinfo) - created_date).days
                if days_old > 30:
                    risk_score += 1
                    task_risks.append("stale")
                elif days_old > 14:
                    risk_score += 0.5
            except:
                pass
            
            # Determine risk level
            if risk_score >= 4:
                risk_level = "high"
                risk_summary["high_risk"] += 1
            elif risk_score >= 2:
                risk_level = "medium" 
                risk_summary["medium_risk"] += 1
            else:
                risk_level = "low"
                risk_summary["low_risk"] += 1
            
            # Add to risky tasks if above threshold
            if risk_score >= 2:
                risky_tasks.append({
                    "task": task,
                    "risk_level": risk_level,
                    "risk_score": round(risk_score, 1),
                    "risk_categories": list(set(task_risks)),
                    "recommendations": self._get_risk_recommendations(task_risks, task)
                })
        
        # Sort by risk score
        risky_tasks.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return {
            "risk_summary": risk_summary,
            "risky_tasks": risky_tasks[:10],  # Top 10 risky tasks
            "suggestions": self._generate_risk_suggestions(risk_summary, risky_tasks)
        }
    
    def _get_risk_recommendations(self, risk_categories: List[str], task: Dict) -> List[str]:
        """
        Generate recommendations based on detected risk categories
        """
        recommendations = []
        
        if "delay" in risk_categories:
            recommendations.append("重新评估时间安排，考虑分解为更小的任务")
        if "blocked" in risk_categories:
            recommendations.append("识别阻塞原因，寻找替代方案或升级处理")
        if "external_dependency" in risk_categories:
            recommendations.append("建立外部依赖跟踪，设置提醒和备选方案")
        if "complexity" in risk_categories:
            recommendations.append("分解复杂任务，寻求专家支持或额外资源")
        if "emotional_stress" in risk_categories:
            recommendations.append("关注团队情绪，提供支持或调整工作负载")
        if "stale" in risk_categories:
            recommendations.append("审查任务相关性，考虑更新或关闭")
        
        if not recommendations:
            recommendations.append("定期更新任务状态，保持沟通畅通")
            
        return recommendations
    
    def _generate_risk_suggestions(self, risk_summary: Dict, risky_tasks: List[Dict]) -> List[str]:
        """
        Generate overall suggestions based on risk analysis
        """
        suggestions = []
        
        total_tasks = risk_summary["total_tasks"]
        high_risk = risk_summary["high_risk"]
        risk_categories = risk_summary["risk_categories"]
        
        if high_risk > 0:
            suggestions.append(f"发现 {high_risk} 个高风险任务，建议优先关注和处理")
        
        # Category-specific suggestions
        if risk_categories["delay"] > total_tasks * 0.2:
            suggestions.append("多个任务存在延期风险，建议审查项目时间安排")
        
        if risk_categories["blocked"] > 0:
            suggestions.append("存在阻塞任务，建议建立日常阻塞清理机制")
        
        if risk_categories["external_dependency"] > 0:
            suggestions.append("外部依赖较多，建议加强沟通和风险控制")
        
        if risk_categories["emotional_stress"] > 0:
            suggestions.append("团队压力较大，建议关注工作负载和心理健康")
        
        if len(suggestions) == 0:
            suggestions.append("整体风险较低，保持良好的任务管理习惯")
        
        return suggestions

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
    """
    Convenience function to parse tasks using AI
    """
    return ai_client.parse_tasks(prompt)

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