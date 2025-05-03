"""
מימוש של סוכן מחקר
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.protocol import Message, MessageType
from ..config import settings
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    """סוכן מחקר - אחראי על מחקר שוק, ניתוח מתחרים, וזיהוי מגמות"""
    
    def _initialize_skills(self) -> Dict[str, Any]:
        """אתחול מיומנויות הסוכן"""
        return {
            "market_research": {
                "description": "מחקר שוק",
                "level": 5
            },
            "competitor_analysis": {
                "description": "ניתוח מתחרים",
                "level": 5
            },
            "trend_identification": {
                "description": "זיהוי מגמות",
                "level": 4
            },
            "opportunity_assessment": {
                "description": "הערכת הזדמנויות",
                "level": 4
            },
            "data_analysis": {
                "description": "ניתוח נתונים",
                "level": 4
            },
            "user_research": {
                "description": "מחקר משתמשים",
                "level": 3
            },
            "industry_analysis": {
                "description": "ניתוח תעשייה",
                "level": 5
            },
            "technology_assessment": {
                "description": "הערכת טכנולוגיות",
                "level": 3
            }
        }
    
    def _process_request(self, message: Message) -> Dict[str, Any]:
        """
        טיפול בבקשות לסוכן מחקר
        
        Args:
            message: הודעת הבקשה
            
        Returns:
            תוצאות הבקשה
        """
        logger.info(f"ResearchAgent processing message: {message.message_type.value}")
        
        content = message.content
        message_type = message.message_type
        
        # טיפול במשימה חדשה
        if message_type == MessageType.TASK:
            return self._handle_research_task(content)
        
        # טיפול בבקשת מידע מסוכן אחר
        elif message_type == MessageType.REQUEST:
            return self._handle_research_request(content)
        
        # טיפול בתשובה מסוכן אחר
        elif message_type == MessageType.RESPONSE:
            return self._process_response_info(content)
        
        # ברירת מחדל - שגיאה
        return {
            "status": "error",
            "error": "Unsupported message type for ResearchAgent"
        }
    
    def _handle_research_task(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        טיפול במשימת מחקר
        
        Args:
            content: תוכן המשימה
            
        Returns:
            תוצאות המשימה
        """
        task_description = content.get("description", "")
        context = content.get("context", {})
        requirements = content.get("requirements", [])
        
        # ניתוח סוג המשימה
        task_type = self._analyze_research_task_type(task_description)
        
        # בדיקה אם יש צורך לבקש מידע נוסף מסוכנים אחרים
        if task_type == "opportunity_assessment" and "financial_constraints" not in context:
            return {
                "status": "pending",
                "requires_assistance": True,
                "required_agent": "finance",
                "required_capability": "investment_analysis",
                "question": f"צריך ניתוח פיננסי להערכת הזדמנויות: {task_description}",
                "context": {
                    "task_description": task_description,
                    "requirements": requirements
                }
            }
        
        if task_type == "technology_assessment" and "technical_requirements" not in context:
            return {
                "status": "pending",
                "requires_assistance": True,
                "required_agent": "development",
                "required_capability": "tech_stack_evaluation",
                "question": f"צריך הערכה טכנית של טכנולוגיות: {task_description}",
                "context": {
                    "task_description": task_description,
                    "requirements": requirements
                }
            }
            
        # עיבוד המשימה
        return self._process_research_task(task_type, task_description, context, requirements)
    
    def _analyze_research_task_type(self, task_description: str) -> str:
        """
        ניתוח סוג משימת המחקר
        
        Args:
            task_description: תיאור המשימה
            
        Returns:
            סוג המשימה
        """
        # ניתוח פשוט על בסיס מילות מפתח
        lower_desc = task_description.lower()
        
        if any(keyword in lower_desc for keyword in ["שוק", "market research", "מחקר שוק"]):
            return "market_research"
        
        if any(keyword in lower_desc for keyword in ["מתחרים", "competitors", "ניתוח מתחרים"]):
            return "competitor_analysis"
            
        if any(keyword in lower_desc for keyword in ["מגמות", "trends", "זיהוי מגמות"]):
            return "trend_identification"
            
        if any(keyword in lower_desc for keyword in ["הזדמנויות", "opportunities", "הערכת הזדמנויות"]):
            return "opportunity_assessment"
            
        if any(keyword in lower_desc for keyword in ["נתונים", "data", "ניתוח נתונים"]):
            return "data_analysis"
            
        if any(keyword in lower_desc for keyword in ["משתמשים", "users", "לקוחות", "מחקר משתמשים"]):
            return "user_research"
            
        if any(keyword in lower_desc for keyword in ["תעשייה", "industry", "ניתוח תעשייה", "ענף"]):
            return "industry_analysis"
            
        if any(keyword in lower_desc for keyword in ["טכנולוגיה", "technology", "הערכת טכנולוגיות"]):
            return "technology_assessment"
            
        # ברירת מחדל
        return "market_research"
    
    def _process_research_task(self, task_type: str, task_description: str, 
                              context: Dict[str, Any], requirements: List[str]) -> Dict[str, Any]:
        """
        עיבוד משימת מחקר
        
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
                "content": f"{self.system_prompt}\n\nתפקידך לבצע משימת {task_type} כחוקר שוק מומחה."
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
כלול בתשובתך נתונים ותובנות ספציפיות, וציין מקורות ככל שניתן.
                """
            }
        ]
        
        # שליחה לOpenAI
        response = self._call_openai(messages)
        
        # עיבוד התוצאה
        findings = self._extract_research_findings(response, task_type)
        
        # עיבוד וארגון התוצאה
        result = {
            "status": "complete",
            "task_type": task_type,
            "result": response,
            "findings": findings,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "agent": {
                    "type": self.agent_type,
                    "name": self.name
                }
            }
        }
        
        return result
    
    def _extract_research_findings(self, response: str, task_type: str) -> Dict[str, Any]:
        """
        חילוץ ממצאי מחקר מתשובת ה-AI
        
        Args:
            response: תשובת ה-AI
            task_type: סוג המשימה
        
        Returns:
            ממצאי מחקר מארגנים
        """
        findings = {}
        
        # חילוץ מידע כללי
        import re
        
        # חילוץ סעיפים/רשימות
        bullet_points_pattern = r'•\s*(.*?)(?:\n|$)'
        bullet_points = re.findall(bullet_points_pattern, response)
        
        numbered_points_pattern = r'\d+\.\s*(.*?)(?:\n|$)'
        numbered_points = re.findall(numbered_points_pattern, response)
        
        if bullet_points or numbered_points:
            findings["key_points"] = bullet_points + numbered_points
        
        # חילוץ שמות חברות/ארגונים
        # רשימה בסיסית של חברות טכנולוגיה מובילות
        companies = ["Google", "Facebook", "Meta", "Apple", "Microsoft", "Amazon", "גוגל", "פייסבוק",
                    "מיקרוסופט", "אמזון", "אפל", "טסלה", "Tesla", "IBM", "אייבמ", "Oracle", "אורקל"]
        
        found_companies = []
        for company in companies:
            if company.lower() in response.lower():
                found_companies.append(company)
                
        if found_companies:
            findings["mentioned_companies"] = list(set(found_companies))
        
        # התאמת חילוץ לסוג המשימה
        if task_type == "market_research":
            # חילוץ גודל שוק (מספרים עם סימון כספי)
            market_size_pattern = r'([$€£₪]?\s?[\d,]+(?:\.\d+)?\s?(?:מיליון|מיליארד|אלף|אלפי|טריליון|מ\'|מ"ש|מ״ש|million|billion|trillion)?)'
            market_size_matches = re.findall(market_size_pattern, response)
            if market_size_matches:
                findings["market_size_mentions"] = market_size_matches[:3]  # לוקח עד 3 אזכורים
                
        elif task_type == "competitor_analysis":
            # חילוץ שמות מתחרים והשוואה
            competitors_section_pattern = r'(?:מתחרים|תחרות|השוואה|competitors).*?:(.*?)(?:\n\n|\Z)'
            competitors_match = re.search(competitors_section_pattern, response, re.IGNORECASE | re.DOTALL)
            if competitors_match:
                findings["competitors_section"] = competitors_match.group(1).strip()
                
        elif task_type == "trend_identification":
            # חילוץ מילות מגמה
            trend_words = ["trend", "מגמה", "צומח", "growing", "עולה", "יורד", "declining",
                          "חדש", "new", "עתידי", "future", "מתפתח", "emerging", "disruptive"]
            
            trend_sentences = []
            sentences = re.split(r'[.!?]+', response)
            for sentence in sentences:
                if any(word in sentence.lower() for word in trend_words):
                    trend_sentences.append(sentence.strip())
                    
            if trend_sentences:
                findings["trend_sentences"] = trend_sentences
                
        elif task_type == "data_analysis":
            # חילוץ מספרים ואחוזים
            percentage_pattern = r'(\d+(?:\.\d+)?%)'
            percentage_matches = re.findall(percentage_pattern, response)
            if percentage_matches:
                findings["percentage_mentions"] = percentage_matches
        
        return findings
    
    def _handle_research_request(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        טיפול בבקשת מידע מחקרי
        
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
                "error": f"ResearchAgent does not have the required capability: {required_capability}"
            }
        
        # הכנת פרומפט לOpenAI
        messages = [
            {
                "role": "system",
                "content": f"{self.system_prompt}\n\nאתה חוקר שוק מומחה. ענה על שאלות בנושאי {required_capability}."
            },
            {
                "role": "user",
                "content": f"""
שאלה: {question}

הקשר:
{json.dumps(context, ensure_ascii=False, indent=2) if context else 'אין הקשר נוסף'}

אנא ספק תשובה מקצועית ומקיפה, תוך שימוש במומחיות שלך בתחום המחקר.
בסס את תשובתך על נתונים עדכניים ותובנות שוק, וציין מקורות אפשריים.
                """
            }
        ]
        
        # שליחה לOpenAI
        response = self._call_openai(messages)
        
        # חילוץ ממצאים
        findings = self._extract_research_findings(response, required_capability)
        
        result = {
            "status": "success",
            "answer": response,
            "capability_used": required_capability,
            "findings": findings,
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
