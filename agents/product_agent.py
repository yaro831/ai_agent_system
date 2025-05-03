"""
מימוש של סוכן מנהל מוצר
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.protocol import Message, MessageType
from ..config import settings
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ProductAgent(BaseAgent):
    """סוכן מנהל מוצר - אחראי על אסטרטגיית מוצר, אפיון, ותעדוף דרישות"""
    
    def _initialize_skills(self) -> Dict[str, Any]:
        """אתחול מיומנויות הסוכן"""
        return {
            "product_strategy": {
                "description": "פיתוח אסטרטגיית מוצר",
                "level": 5
            },
            "requirements_analysis": {
                "description": "ניתוח דרישות ואפיון מוצר",
                "level": 5
            },
            "roadmap_planning": {
                "description": "תכנון מפת דרכים למוצר",
                "level": 4
            },
            "feature_prioritization": {
                "description": "תעדוף פיצ'רים ודרישות",
                "level": 5
            },
            "market_analysis": {
                "description": "ניתוח שוק ומתחרים",
                "level": 3
            },
            "user_persona_creation": {
                "description": "יצירת פרסונות משתמשים",
                "level": 4
            }
        }
    
    def _process_request(self, message: Message) -> Dict[str, Any]:
        """
        טיפול בבקשות לסוכן מנהל המוצר
        
        Args:
            message: הודעת הבקשה
            
        Returns:
            תוצאות הבקשה
        """
        logger.info(f"ProductAgent processing message: {message.message_type.value}")
        
        content = message.content
        message_type = message.message_type
        
        # טיפול במשימה חדשה
        if message_type == MessageType.TASK:
            return self._handle_product_task(content)
        
        # טיפול בבקשת מידע מסוכן אחר
        elif message_type == MessageType.REQUEST:
            return self._handle_product_request(content)
        
        # טיפול בתשובה מסוכן אחר
        elif message_type == MessageType.RESPONSE:
            return self._process_response_info(content)
        
        # ברירת מחדל - שגיאה
        return {
            "status": "error",
            "error": "Unsupported message type for ProductAgent"
        }
    
    def _handle_product_task(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        טיפול במשימת ניהול מוצר
        
        Args:
            content: תוכן המשימה
            
        Returns:
            תוצאות המשימה
        """
        task_description = content.get("description", "")
        context = content.get("context", {})
        requirements = content.get("requirements", [])
        
        # ניתוח סוג המשימה
        task_type = self._analyze_product_task_type(task_description)
        
        # בדיקה אם יש צורך לבקש מידע נוסף מסוכנים אחרים
        if task_type == "market_research" and "market_data" not in context:
            return {
                "status": "pending",
                "requires_assistance": True,
                "required_agent": "research",
                "required_capability": "market_research",
                "question": f"צריך מחקר שוק עבור: {task_description}",
                "context": {
                    "task_description": task_description,
                    "requirements": requirements
                }
            }
        
        if task_type == "technical_feasibility" and "technical_assessment" not in context:
            return {
                "status": "pending",
                "requires_assistance": True,
                "required_agent": "development",
                "required_capability": "technical_planning",
                "question": f"האם ניתן ליישם טכנית: {task_description}?",
                "context": {
                    "task_description": task_description,
                    "requirements": requirements
                }
            }
            
        # עיבוד המשימה
        return self._process_product_task(task_type, task_description, context, requirements)
    
    def _analyze_product_task_type(self, task_description: str) -> str:
        """
        ניתוח סוג משימת המוצר
        
        Args:
            task_description: תיאור המשימה
            
        Returns:
            סוג המשימה
        """
        # ניתוח פשוט על בסיס מילות מפתח
        lower_desc = task_description.lower()
        
        if any(keyword in lower_desc for keyword in ["שוק", "מתחרים", "מחקר", "סקירה"]):
            return "market_research"
        
        if any(keyword in lower_desc for keyword in ["דרך", "מפת", "רודמאפ", "יעדים", "תכנון"]):
            return "roadmap_planning"
            
        if any(keyword in lower_desc for keyword in ["דרישות", "אפיון", "מאפיינים", "צרכים"]):
            return "requirements_analysis"
            
        if any(keyword in lower_desc for keyword in ["תעדוף", "עדיפות", "סדר", "חשיבות"]):
            return "feature_prioritization"
            
        if any(keyword in lower_desc for keyword in ["אסטרטגיה", "חזון", "כיוון", "מטרות"]):
            return "product_strategy"
            
        if any(keyword in lower_desc for keyword in ["טכני", "יישום", "פיתוח", "אפשרי"]):
            return "technical_feasibility"
            
        # ברירת מחדל
        return "product_strategy"
    
    def _process_product_task(self, task_type: str, task_description: str, 
                            context: Dict[str, Any], requirements: List[str]) -> Dict[str, Any]:
        """
        עיבוד משימת מוצר
        
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
                "content": f"{self.system_prompt}\n\nתפקידך לבצע משימת {task_type} כמנהל מוצר מומחה."
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
        
        return result
    
    def _handle_product_request(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        טיפול בבקשת מידע הקשור למוצר
        
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
                "error": f"ProductAgent does not have the required capability: {required_capability}"
            }
        
        # הכנת פרומפט לOpenAI
        messages = [
            {
                "role": "system",
                "content": f"{self.system_prompt}\n\nאתה מנהל מוצר מומחה. ענה על שאלות בנושאי {required_capability}."
            },
            {
                "role": "user",
                "content": f"""
שאלה: {question}

הקשר:
{json.dumps(context, ensure_ascii=False, indent=2) if context else 'אין הקשר נוסף'}

אנא ספק תשובה מקצועית ומקיפה, תוך שימוש במומחיות שלך בתחום ניהול מוצר.
                """
            }
        ]
        
        # שליחה לOpenAI
        response = self._call_openai(messages)
        
        return {
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