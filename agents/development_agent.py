"""
מימוש של סוכן פיתוח
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.protocol import Message, MessageType
from ..config import settings
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class DevelopmentAgent(BaseAgent):
    """סוכן פיתוח - אחראי על תכנון טכנולוגי, ארכיטקטורה, ופיתוח תוכנה"""
    
    def _initialize_skills(self) -> Dict[str, Any]:
        """אתחול מיומנויות הסוכן"""
        return {
            "architecture_design": {
                "description": "תכנון ארכיטקטורת מערכת",
                "level": 5
            },
            "tech_stack_evaluation": {
                "description": "הערכת טכנולוגיות",
                "level": 5
            },
            "code_review": {
                "description": "סקירת קוד",
                "level": 4
            },
            "technical_planning": {
                "description": "תכנון טכני",
                "level": 5
            },
            "api_design": {
                "description": "תכנון API",
                "level": 4
            },
            "database_design": {
                "description": "תכנון מסדי נתונים",
                "level": 4
            },
            "code_generation": {
                "description": "יצירת קוד",
                "level": 5
            },
            "devops": {
                "description": "תהליכי פיתוח והפעלה",
                "level": 3
            },
            "security_assessment": {
                "description": "הערכת אבטחה",
                "level": 3
            }
        }
    
    def _process_request(self, message: Message) -> Dict[str, Any]:
        """
        טיפול בבקשות לסוכן פיתוח
        
        Args:
            message: הודעת הבקשה
            
        Returns:
            תוצאות הבקשה
        """
        logger.info(f"DevelopmentAgent processing message: {message.message_type.value}")
        
        content = message.content
        message_type = message.message_type
        
        # טיפול במשימה חדשה
        if message_type == MessageType.TASK:
            return self._handle_development_task(content)
        
        # טיפול בבקשת מידע מסוכן אחר
        elif message_type == MessageType.REQUEST:
            return self._handle_development_request(content)
        
        # טיפול בתשובה מסוכן אחר
        elif message_type == MessageType.RESPONSE:
            return self._process_response_info(content)
        
        # ברירת מחדל - שגיאה
        return {
            "status": "error",
            "error": "Unsupported message type for DevelopmentAgent"
        }
    
    def _handle_development_task(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        טיפול במשימת פיתוח
        
        Args:
            content: תוכן המשימה
            
        Returns:
            תוצאות המשימה
        """
        task_description = content.get("description", "")
        context = content.get("context", {})
        requirements = content.get("requirements", [])
        
        # ניתוח סוג המשימה
        task_type = self._analyze_development_task_type(task_description)
        
        # בדיקה אם יש צורך לבקש מידע נוסף מסוכנים אחרים
        if task_type == "system_requirements" and "product_requirements" not in context:
            return {
                "status": "pending",
                "requires_assistance": True,
                "required_agent": "product",
                "required_capability": "requirements_analysis",
                "question": f"צריך אפיון מוצר מפורט עבור: {task_description}",
                "context": {
                    "task_description": task_description,
                    "requirements": requirements
                }
            }
        
        if task_type == "cost_estimation" and "budget_constraints" not in context:
            return {
                "status": "pending",
                "requires_assistance": True,
                "required_agent": "finance",
                "required_capability": "budget_planning",
                "question": f"צריך מסגרת תקציב לפיתוח: {task_description}",
                "context": {
                    "task_description": task_description,
                    "requirements": requirements
                }
            }
            
        # עיבוד המשימה
        return self._process_development_task(task_type, task_description, context, requirements)
    
    def _analyze_development_task_type(self, task_description: str) -> str:
        """
        ניתוח סוג משימת הפיתוח
        
        Args:
            task_description: תיאור המשימה
            
        Returns:
            סוג המשימה
        """
        # ניתוח פשוט על בסיס מילות מפתח
        lower_desc = task_description.lower()
        
        if any(keyword in lower_desc for keyword in ["ארכיטקטורה", "מבנה", "תכנון"]):
            return "architecture_design"
        
        if any(keyword in lower_desc for keyword in ["tech stack", "טכנולוגיות", "כלים", "תשתית"]):
            return "tech_stack_evaluation"
            
        if any(keyword in lower_desc for keyword in ["api", "ממשק", "שירות", "endpoint"]):
            return "api_design"
            
        if any(keyword in lower_desc for keyword in ["database", "מסד נתונים", "db", "אחסון"]):
            return "database_design"
            
        if any(keyword in lower_desc for keyword in ["קוד", "לכתוב", "לפתח", "יישום"]):
            return "code_generation"
            
        if any(keyword in lower_desc for keyword in ["סקירה", "review", "בדיקה", "קוד קיים"]):
            return "code_review"
            
        if any(keyword in lower_desc for keyword in ["devops", "ci/cd", "deployment", "הטמעה"]):
            return "devops"
            
        if any(keyword in lower_desc for keyword in ["אבטחה", "security", "סיכון", "פרצה"]):
            return "security_assessment"
            
        if any(keyword in lower_desc for keyword in ["דרישות", "אפיון", "specification"]):
            return "system_requirements"
            
        if any(keyword in lower_desc for keyword in ["עלות", "תקציב", "הערכה", "משאבים"]):
            return "cost_estimation"
            
        # ברירת מחדל
        return "technical_planning"
    
    def _process_development_task(self, task_type: str, task_description: str, 
                                context: Dict[str, Any], requirements: List[str]) -> Dict[str, Any]:
        """
        עיבוד משימת פיתוח
        
        Args:
            task_type: סוג המשימה
            task_description: תיאור המשימה
            context: הקשר המשימה
            requirements: דרישות המשימה
            
        Returns:
            תוצאות המשימה
        """
        # הכנת פרומפט לOpenAI
        messages = [
            {
                "role": "system",
                "content": f"{self.system_prompt}\n\nתפקידך לבצע משימת {task_type} כמנהל פיתוח מומחה."
            },
            {
                "role": "user",
                "content": f"""
משימה: {task_description}

הקשר:
{json.dumps(context, ensure_ascii=False, indent=2) if context else 'אין הקשר נוסף'}

דרישות:
{json.dumps(requirements, ensure_ascii=False, indent=2) if requirements else 'אין דרישות מוגדרות'}

אנא בצע את המשימה בצורה המקצועית ביותר, וספק תוצאה מפורטת ומקיפה.
אם המשימה כוללת יצירת קוד, ספק קוד איכותי עם הסברים.
                """
            }
        ]
        
        # שליחה לOpenAI
        response = self._call_openai(messages)
        
        # עיבוד וארגון התוצאה
        result = {
            "status": "complete",
            "task_type": task_type,
            "result": response,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "agent": {
                    "type": self.agent_type,
                    "name": self.name
                }
            }
        }
        
        # הוספת קוד אם רלוונטי
        if task_type in ["code_generation", "api_design"]:
            code_segments = self._extract_code_from_response(response)
            if code_segments:
                result["code_segments"] = code_segments
        
        return result
    
    def _extract_code_from_response(self, response: str) -> List[Dict[str, str]]:
        """
        חילוץ קטעי קוד מתשובת AI
        
        Args:
            response: תשובת AI
            
        Returns:
            רשימת קטעי קוד שחולצו
        """
        code_segments = []
        
        # חיפוש בסיסי לקטעי קוד עם סימני ```
        import re
        pattern = r'```(\w*)\n([\s\S]*?)```'
        matches = re.findall(pattern, response)
        
        for language, code in matches:
            language = language.strip().lower() or "unknown"
            code_segments.append({
                "language": language,
                "code": code
            })
        
        return code_segments
    
    def _handle_development_request(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        טיפול בבקשת מידע הקשור לפיתוח
        
        Args:
            content: תוכן הבקשה
            
        Returns:
            תשובה לבקשה
        """
        question = content.get("question", "")
        required_capability = content.get("required_capability", "")
        context = content.get("context", {})
        
        # בדיקה אם יש לסוכן את היכולת הנדרשת
        if required_capability and required_capability not in self.skills:
            return {
                "status": "error",
                "error": f"DevelopmentAgent does not have the required capability: {required_capability}"
            }
        
        # הכנת פרומפט לOpenAI
        messages = [
            {
                "role": "system",
                "content": f"{self.system_prompt}\n\nאתה מנהל פיתוח ומהנדס תוכנה מומחה. ענה על שאלות בנושאי {required_capability}."
            },
            {
                "role": "user",
                "content": f"""
שאלה: {question}

הקשר:
{json.dumps(context, ensure_ascii=False, indent=2) if context else 'אין הקשר נוסף'}

אנא ספק תשובה מקצועית ומקיפה, תוך שימוש במומחיות שלך בתחום הפיתוח והתכנון הטכני.
אם רלוונטי, כלול דוגמאות קוד, תרשימים או הצעות ארכיטקטורה.
                """
            }
        ]
        
        # שליחה לOpenAI
        response = self._call_openai(messages)
        
        # חילוץ קטעי קוד אם קיימים
        code_segments = self._extract_code_from_response(response)
        
        result = {
            "status": "success",
            "answer": response,
            "capability_used": required_capability,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "agent": {
                    "type": self.agent_type,
                    "name": self.name
                }
            }
        }
        
        if code_segments:
            result["code_segments"] = code_segments
            
        return result
    
    def _process_response_info(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        עיבוד מידע שהתקבל מסוכן אחר
        
        Args:
            content: תוכן התשובה
            
        Returns:
            תוצאות העיבוד
        """
        # במקרה הפשוט, נחזיר שהמידע התקבל ועובד
        return {
            "status": "success",
            "message": "Information processed successfully",
            "processed_data": content,
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                "agent": {
                    "type": self.agent_type,
                    "name": self.name
                }
            }
        }