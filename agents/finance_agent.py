"""
מימוש של סוכן פיננסי
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.protocol import Message, MessageType
from ..config import settings
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class FinanceAgent(BaseAgent):
    """סוכן פיננסי - אחראי על תכנון תקציב, ניתוח עלויות ומודלים עסקיים"""
    
    def _initialize_skills(self) -> Dict[str, Any]:
        """אתחול מיומנויות הסוכן"""
        return {
            "budget_planning": {
                "description": "תכנון תקציב",
                "level": 5
            },
            "cost_analysis": {
                "description": "ניתוח עלויות",
                "level": 5
            },
            "revenue_projection": {
                "description": "תחזיות הכנסות",
                "level": 4
            },
            "financial_modeling": {
                "description": "מודלים פיננסיים",
                "level": 5
            },
            "investment_analysis": {
                "description": "ניתוח השקעות",
                "level": 4
            },
            "pricing_modeling": {
                "description": "מודלי תמחור",
                "level": 4
            },
            "burn_rate_analysis": {
                "description": "ניתוח קצב שריפת מזומנים",
                "level": 5
            },
            "break_even_analysis": {
                "description": "ניתוח נקודת איזון",
                "level": 5
            }
        }
    
    def _process_request(self, message: Message) -> Dict[str, Any]:
        """
        טיפול בבקשות לסוכן פיננסי
        
        Args:
            message: הודעת הבקשה
            
        Returns:
            תוצאות הבקשה
        """
        logger.info(f"FinanceAgent processing message: {message.message_type.value}")
        
        content = message.content
        message_type = message.message_type
        
        # טיפול במשימה חדשה
        if message_type == MessageType.TASK:
            return self._handle_finance_task(content)
        
        # טיפול בבקשת מידע מסוכן אחר
        elif message_type == MessageType.REQUEST:
            return self._handle_finance_request(content)
        
        # טיפול בתשובה מסוכן אחר
        elif message_type == MessageType.RESPONSE:
            return self._process_response_info(content)
        
        # ברירת מחדל - שגיאה
        return {
            "status": "error",
            "error": "Unsupported message type for FinanceAgent"
        }
    
    def _handle_finance_task(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        טיפול במשימה פיננסית
        
        Args:
            content: תוכן המשימה
            
        Returns:
            תוצאות המשימה
        """
        task_description = content.get("description", "")
        context = content.get("context", {})
        requirements = content.get("requirements", [])
        
        # ניתוח סוג המשימה
        task_type = self._analyze_finance_task_type(task_description)
        
        # בדיקה אם יש צורך לבקש מידע נוסף מסוכנים אחרים
        if task_type == "revenue_projection" and "market_data" not in context:
            return {
                "status": "pending",
                "requires_assistance": True,
                "required_agent": "research",
                "required_capability": "market_research",
                "question": f"צריך נתוני שוק לתחזית הכנסות: {task_description}",
                "context": {
                    "task_description": task_description,
                    "requirements": requirements
                }
            }
        
        if task_type == "budget_planning" and "development_estimates" not in context:
            return {
                "status": "pending",
                "requires_assistance": True,
                "required_agent": "development",
                "required_capability": "technical_planning",
                "question": f"צריך הערכות משאבי פיתוח לתכנון תקציב: {task_description}",
                "context": {
                    "task_description": task_description,
                    "requirements": requirements
                }
            }
            
        # עיבוד המשימה
        return self._process_finance_task(task_type, task_description, context, requirements)
    
    def _analyze_finance_task_type(self, task_description: str) -> str:
        """
        ניתוח סוג המשימה הפיננסית
        
        Args:
            task_description: תיאור המשימה
            
        Returns:
            סוג המשימה
        """
        # ניתוח פשוט על בסיס מילות מפתח
        lower_desc = task_description.lower()
        
        if any(keyword in lower_desc for keyword in ["תקציב", "budget", "הוצאות", "expenses"]):
            return "budget_planning"
        
        if any(keyword in lower_desc for keyword in ["עלויות", "costs", "הוצאות", "expenses"]):
            return "cost_analysis"
            
        if any(keyword in lower_desc for keyword in ["הכנסות", "revenue", "מכירות", "sales"]):
            return "revenue_projection"
            
        if any(keyword in lower_desc for keyword in ["מודל פיננסי", "financial model", "תזרים", "cash flow"]):
            return "financial_modeling"
            
        if any(keyword in lower_desc for keyword in ["השקעה", "investment", "roi", "capital"]):
            return "investment_analysis"
            
        if any(keyword in lower_desc for keyword in ["תמחור", "pricing", "מחיר", "price"]):
            return "pricing_modeling"
            
        if any(keyword in lower_desc for keyword in ["burn rate", "cash burn", "שריפת מזומנים"]):
            return "burn_rate_analysis"
            
        if any(keyword in lower_desc for keyword in ["break even", "נקודת איזון", "איזון תקציבי"]):
            return "break_even_analysis"
            
        # ברירת מחדל
        return "financial_modeling"
    
    def _process_finance_task(self, task_type: str, task_description: str, 
                             context: Dict[str, Any], requirements: List[str]) -> Dict[str, Any]:
        """
        עיבוד משימה פיננסית
        
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
                "content": f"{self.system_prompt}\n\nתפקידך לבצע משימת {task_type} כמנהל פיננסי מומחה."
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
כלול בתשובתך מספרים, הנחות, וחישובים רלוונטיים.
                """
            }
        ]
        
        # שליחה לOpenAI
        response = self._call_openai(messages)
        
        # עיבוד וחילוץ נתונים פיננסיים
        financial_data = self._extract_financial_data(response, task_type)
        
        # עיבוד וארגון התוצאה
        result = {
            "status": "complete",
            "task_type": task_type,
            "result": response,
            "financial_data": financial_data,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "agent": {
                    "type": self.agent_type,
                    "name": self.name
                }
            }
        }
        
        return result
    
    def _extract_financial_data(self, response: str, task_type: str) -> Dict[str, Any]:
        """
        חילוץ נתונים פיננסיים מתשובת ה-AI
        
        Args:
            response: תשובת ה-AI
            task_type: סוג המשימה
        
        Returns:
            נתונים פיננסיים שחולצו
        """
        # נתונים שיחולצו לפי סוג המשימה
        financial_data = {}
        
        # חיפוש נתונים בסיסיים
        import re
        
        # חילוץ מספרים עם סימון מטבע (לדוגמה: $10,000 או ₪50,000)
        currency_pattern = r'([$€£₪]\s?[\d,]+(?:\.\d+)?|\d+(?:,\d+)*(?:\.\d+)?\s?[$€£₪])'
        currency_matches = re.findall(currency_pattern, response)
        if currency_matches:
            financial_data["identified_amounts"] = currency_matches
        
        # חילוץ אחוזים
        percentage_pattern = r'(\d+(?:\.\d+)?%)'
        percentage_matches = re.findall(percentage_pattern, response)
        if percentage_matches:
            financial_data["identified_percentages"] = percentage_matches
        
        # חילוץ נתונים ספציפיים לפי סוג המשימה
        if task_type == "budget_planning":
            budget_total_pattern = r'(?:תקציב כולל|סך תקציב|total budget)[:\s]+([₪$€£]?\s?[\d,]+(?:\.\d+)?)'
            match = re.search(budget_total_pattern, response, re.IGNORECASE)
            if match:
                financial_data["total_budget"] = match.group(1).strip()
                
        elif task_type == "revenue_projection":
            revenue_pattern = r'(?:הכנסות צפויות|תחזית הכנסות|projected revenue)[:\s]+([₪$€£]?\s?[\d,]+(?:\.\d+)?)'
            match = re.search(revenue_pattern, response, re.IGNORECASE)
            if match:
                financial_data["projected_revenue"] = match.group(1).strip()
                
        elif task_type == "break_even_analysis":
            break_even_pattern = r'(?:נקודת איזון|break[- ]even)[:\s]+([\d,]+(?:\.\d+)?(?:\s?יחידות|\s?units)?)'
            match = re.search(break_even_pattern, response, re.IGNORECASE)
            if match:
                financial_data["break_even_point"] = match.group(1).strip()
                
        # חילוץ תאריכים רלוונטיים
        date_pattern = r'\b(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4})\b'
        date_matches = re.findall(date_pattern, response)
        if date_matches:
            financial_data["identified_dates"] = date_matches
        
        return financial_data
    
    def _handle_finance_request(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        טיפול בבקשת מידע פיננסי
        
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
                "error": f"FinanceAgent does not have the required capability: {required_capability}"
            }
        
        # הכנת פרומפט לOpenAI
        messages = [
            {
                "role": "system",
                "content": f"{self.system_prompt}\n\nאתה מנהל פיננסי מומחה. ענה על שאלות בנושאי {required_capability}."
            },
            {
                "role": "user",
                "content": f"""
שאלה: {question}

הקשר:
{json.dumps(context, ensure_ascii=False, indent=2) if context else 'אין הקשר נוסף'}

אנא ספק תשובה מקצועית ומקיפה, תוך שימוש במומחיות שלך בתחום הפיננסי.
ספק ניתוח מספרי ותובנות עסקיות כאשר רלוונטי.
                """
            }
        ]
        
        # שליחה לOpenAI
        response = self._call_openai(messages)
        
        # חילוץ נתונים פיננסיים
        financial_data = self._extract_financial_data(response, required_capability)
        
        result = {
            "status": "success",
            "answer": response,
            "capability_used": required_capability,
            "financial_data": financial_data,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "agent": {
                    "type": self.agent_type,
                    "name": self.name
                }
            }
        }
            
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
