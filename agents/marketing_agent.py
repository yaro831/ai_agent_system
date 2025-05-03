"""
מימוש של סוכן שיווק
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.protocol import Message, MessageType
from ..config import settings
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class MarketingAgent(BaseAgent):
    """סוכן שיווק - אחראי על אסטרטגיית שיווק, מסרים שיווקיים ואסטרטגיית מותג"""
    
    def _initialize_skills(self) -> Dict[str, Any]:
        """אתחול מיומנויות הסוכן"""
        return {
            "market_analysis": {
                "description": "ניתוח שוק",
                "level": 4
            },
            "brand_strategy": {
                "description": "אסטרטגיית מותג",
                "level": 5
            },
            "campaign_planning": {
                "description": "תכנון קמפיינים",
                "level": 5
            },
            "content_creation": {
                "description": "יצירת תוכן",
                "level": 5
            },
            "social_media_strategy": {
                "description": "אסטרטגיית מדיה חברתית",
                "level": 4
            },
            "marketing_analysis": {
                "description": "ניתוח מטריקות שיווק",
                "level": 3
            },
            "customer_segmentation": {
                "description": "פילוח לקוחות",
                "level": 4
            },
            "pricing_strategy": {
                "description": "אסטרטגיית תמחור",
                "level": 3
            }
        }
    
    def _process_request(self, message: Message) -> Dict[str, Any]:
        """
        טיפול בבקשות לסוכן שיווק
        
        Args:
            message: הודעת הבקשה
            
        Returns:
            תוצאות הבקשה
        """
        logger.info(f"MarketingAgent processing message: {message.message_type.value}")
        
        content = message.content
        message_type = message.message_type
        
        # טיפול במשימה חדשה
        if message_type == MessageType.TASK:
            return self._handle_marketing_task(content)
        
        # טיפול בבקשת מידע מסוכן אחר
        elif message_type == MessageType.REQUEST:
            return self._handle_marketing_request(content)
        
        # טיפול בתשובה מסוכן אחר
        elif message_type == MessageType.RESPONSE:
            return self._process_response_info(content)
        
        # ברירת מחדל - שגיאה
        return {
            "status": "error",
            "error": "Unsupported message type for MarketingAgent"
        }
    
    def _handle_marketing_task(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        טיפול במשימת שיווק
        
        Args:
            content: תוכן המשימה
            
        Returns:
            תוצאות המשימה
        """
        task_description = content.get("description", "")
        context = content.get("context", {})
        requirements = content.get("requirements", [])
        
        # ניתוח סוג המשימה
        task_type = self._analyze_marketing_task_type(task_description)
        
        # בדיקה אם יש צורך לבקש מידע נוסף מסוכנים אחרים
        if task_type == "market_analysis" and "market_data" not in context:
            return {
                "status": "pending",
                "requires_assistance": True,
                "required_agent": "research",
                "required_capability": "market_research",
                "question": f"צריך נתוני שוק לניתוח שיווקי: {task_description}",
                "context": {
                    "task_description": task_description,
                    "requirements": requirements
                }
            }
        
        if task_type == "pricing_strategy" and "financial_analysis" not in context:
            return {
                "status": "pending",
                "requires_assistance": True,
                "required_agent": "finance",
                "required_capability": "financial_modeling",
                "question": f"צריך ניתוח פיננסי לתמחור מוצר: {task_description}",
                "context": {
                    "task_description": task_description,
                    "requirements": requirements
                }
            }
            
        if task_type == "content_creation" and "product_details" not in context:
            return {
                "status": "pending",
                "requires_assistance": True,
                "required_agent": "product",
                "required_capability": "requirements_analysis",
                "question": f"צריך מידע מפורט על המוצר ליצירת תוכן שיווקי: {task_description}",
                "context": {
                    "task_description": task_description,
                    "requirements": requirements
                }
            }
            
        # עיבוד המשימה
        return self._process_marketing_task(task_type, task_description, context, requirements)
    
    def _analyze_marketing_task_type(self, task_description: str) -> str:
        """
        ניתוח סוג משימת השיווק
        
        Args:
            task_description: תיאור המשימה
            
        Returns:
            סוג המשימה
        """
        # ניתוח פשוט על בסיס מילות מפתח
        lower_desc = task_description.lower()
        
        if any(keyword in lower_desc for keyword in ["ניתוח שוק", "חקר שוק", "סקירת שוק", "מחקר שוק"]):
            return "market_analysis"
        
        if any(keyword in lower_desc for keyword in ["מותג", "brand", "מיתוג", "לוגו", "זהות"]):
            return "brand_strategy"
            
        if any(keyword in lower_desc for keyword in ["קמפיין", "פרסום", "campaign", "מסע פרסום"]):
            return "campaign_planning"
            
        if any(keyword in lower_desc for keyword in ["תוכן", "מאמר", "פוסט", "וידאו", "בלוג"]):
            return "content_creation"
            
        if any(keyword in lower_desc for keyword in ["מדיה חברתית", "סושיאל", "פייסבוק", "אינסטגרם", "טוויטר"]):
            return "social_media_strategy"
            
        if any(keyword in lower_desc for keyword in ["מטריקות", "מדדים", "ביצועים", "אנליטיקה", "roi"]):
            return "marketing_analysis"
            
        if any(keyword in lower_desc for keyword in ["פילוח", "סגמנטציה", "קהל יעד", "לקוחות", "משתמשים"]):
            return "customer_segmentation"
            
        if any(keyword in lower_desc for keyword in ["תמחור", "מחיר", "מבצע", "הנחה", "חבילות"]):
            return "pricing_strategy"
            
        # ברירת מחדל
        return "campaign_planning"
    
    def _process_marketing_task(self, task_type: str, task_description: str, 
                              context: Dict[str, Any], requirements: List[str]) -> Dict[str, Any]:
        """
        עיבוד משימת שיווק
        
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
                "content": f"{self.system_prompt}\n\nתפקידך לבצע משימת {task_type} כמנהל שיווק מומחה."
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
        
        # הוספת מידע נוסף לפי סוג המשימה
        if task_type == "content_creation":
            result["content_type"] = self._identify_content_type(task_description)
            result["target_audience"] = self._extract_target_audience(task_description, context)
            
        if task_type == "campaign_planning":
            result["channels"] = self._identify_marketing_channels(task_description, context)
            result["timeline"] = self._extract_campaign_timeline(task_description, context)
        
        return result
    
    def _identify_content_type(self, task_description: str) -> str:
        """זיהוי סוג התוכן"""
        lower_desc = task_description.lower()
        
        if "וידאו" in lower_desc or "סרטון" in lower_desc:
            return "video"
        elif "בלוג" in lower_desc or "מאמר" in lower_desc:
            return "blog"
        elif "אימייל" in lower_desc or "דיוור" in lower_desc:
            return "email"
        elif "סושיאל" in lower_desc or "פוסט" in lower_desc:
            return "social_media"
        elif "לנדינג" in lower_desc or "דף נחיתה" in lower_desc:
            return "landing_page"
        elif "מצגת" in lower_desc or "פרזנטציה" in lower_desc:
            return "presentation"
        else:
            return "general"
    
    def _extract_target_audience(self, task_description: str, context: Dict[str, Any]) -> List[str]:
        """חילוץ קהל היעד"""
        # מחזיר קהל יעד מהקונטקסט אם קיים
        if context.get("target_audience"):
            return context["target_audience"]
            
        # אחרת, מחזיר רשימה כללית
        return ["קהל כללי"]
    
    def _identify_marketing_channels(self, task_description: str, context: Dict[str, Any]) -> List[str]:
        """זיהוי ערוצי שיווק"""
        # מחזיר ערוצים מהקונטקסט אם קיימים
        if context.get("channels"):
            return context["channels"]
            
        # אחרת, מחזיר רשימה כללית
        channels = []
        lower_desc = task_description.lower()
        
        if any(keyword in lower_desc for keyword in ["פייסבוק", "facebook"]):
            channels.append("facebook")
        if any(keyword in lower_desc for keyword in ["אינסטגרם", "instagram"]):
            channels.append("instagram")
        if any(keyword in lower_desc for keyword in ["טוויטר", "twitter"]):
            channels.append("twitter")
        if any(keyword in lower_desc for keyword in ["לינקדאין", "linkedin"]):
            channels.append("linkedin")
        if any(keyword in lower_desc for keyword in ["גוגל", "google"]):
            channels.append("google_ads")
        if any(keyword in lower_desc for keyword in ["אימייל", "email", "דיוור"]):
            channels.append("email")
        if any(keyword in lower_desc for keyword in ["יוטיוב", "youtube"]):
            channels.append("youtube")
            
        # אם לא זיהינו שום ערוץ, נחזיר רשימה כללית
        if not channels:
            channels = ["social_media", "email", "web"]
            
        return channels
    
    def _extract_campaign_timeline(self, task_description: str, context: Dict[str, Any]) -> Dict[str, str]:
        """חילוץ ציר זמן לקמפיין"""
        # מחזיר ציר זמן מהקונטקסט אם קיים
        if context.get("timeline"):
            return context["timeline"]
            
        # אחרת, מחזיר ברירת מחדל
        return {
            "start_date": "לא צוין",
            "end_date": "לא צוין",
            "duration": "לא צוין"
        }
    
    def _handle_marketing_request(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        טיפול בבקשת מידע הקשור לשיווק
        
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
                "error": f"MarketingAgent does not have the required capability: {required_capability}"
            }
        
        # הכנת פרומפט לOpenAI
        messages = [
            {
                "role": "system",
                "content": f"{self.system_prompt}\n\nאתה מנהל שיווק מומחה. ענה על שאלות בנושאי {required_capability}."
            },
            {
                "role": "user",
                "content": f"""
שאלה: {question}

הקשר:
{json.dumps(context, ensure_ascii=False, indent=2) if context else 'אין הקשר נוסף'}

אנא ספק תשובה מקצועית ומקיפה, תוך שימוש במומחיות שלך בתחום השיווק והמסרים השיווקיים.
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