
# core/agent_manager.py
"""
from typing import Dict, List, Any, Optional, Union
import json
import uuid
import logging
from datetime import datetime

from .protocol import Message, MessageType, TaskStatus
from .message_broker import MessageBroker
from ..agents.base_agent import BaseAgent
from ..config import settings
from ..storage.database import Database

logger = logging.getLogger(__name__)

class AgentManager:
    """מנהל סוכני בינה מלאכותית במערכת"""
    
    def __init__(self):
        """אתחול מנהל הסוכנים"""
        self.agents: Dict[str, BaseAgent] = {}
        self.message_broker = MessageBroker()
        self.db = Database()
        self._load_agents()
        
    def _load_agents(self) -> None:
        """טעינת הסוכנים מתוך קובץ הקונפיגורציה"""
        try:
            with open(settings.AGENT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # יבוא דינמי של מחלקות הסוכנים
            from ..agents.product_agent import ProductAgent
            from ..agents.development_agent import DevelopmentAgent
            from ..agents.marketing_agent import MarketingAgent
            from ..agents.finance_agent import FinanceAgent  
            from ..agents.research_agent import ResearchAgent
            
            # מיפוי שמות סוכנים למחלקות
            agent_classes = {
                "product": ProductAgent,
                "development": DevelopmentAgent,
                "marketing": MarketingAgent,
                "finance": FinanceAgent,
                "research": ResearchAgent
            }
            
            # יצירת הסוכנים
            for agent_type, agent_config in config.get('agents', {}).items():
                if agent_type in agent_classes:
                    self.agents[agent_type] = agent_classes[agent_type](agent_config)
                    logger.info(f"Agent loaded: {agent_type}")
                else:
                    logger.warning(f"Unknown agent type: {agent_type}")
                    
        except Exception as e:
            logger.error(f"Failed to load agents: {str(e)}")
            raise
    
    def execute_task(self, task_description: str, initial_agent: Optional[str] = None) -> Dict[str, Any]:
        """
        ביצוע משימה חדשה במערכת
        
        Args:
            task_description: תיאור המשימה לביצוע
            initial_agent: סוג הסוכן הראשוני שיטפל במשימה (אופציונלי)
            
        Returns:
            תוצאות המשימה
        """
        # יצירת מזהה ייחודי למשימה
        task_id = str(uuid.uuid4())
        
        # יצירת רשומת משימה במסד הנתונים
        task_record = {
            "task_id": task_id,
            "description": task_description,
            "status": TaskStatus.PENDING.value,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "result": None,
            "history": []
        }
        self.db.create_task(task_record)
        
        # בחירת הסוכן המתאים לטיפול ראשוני במשימה
        if initial_agent and initial_agent in self.agents:
            handling_agent = self.agents[initial_agent]
        else:
            handling_agent = self._select_initial_agent(task_description)
        
        if not handling_agent:
            error_msg = "Could not find suitable agent for the task"
            self._update_task_status(task_id, TaskStatus.FAILED, error=error_msg)
            return {"error": error_msg, "task_id": task_id}
        
        # יצירת הודעת משימה ראשונית
        initial_message = Message(
            message_id=str(uuid.uuid4()),
            task_id=task_id,
            sender="system",
            recipient=handling_agent.agent_type,
            message_type=MessageType.TASK,
            content={"description": task_description},
            created_at=datetime.now().isoformat()
        )
        
        # שליחת המשימה לסוכן הראשוני
        logger.info(f"Starting task {task_id} with initial agent: {handling_agent.agent_type}")
        self._update_task_status(task_id, TaskStatus.IN_PROGRESS)
        
        # הוספת ההודעה הראשונית להיסטוריה
        self._add_to_history(task_id, initial_message.to_dict())
        
        # העברת המשימה לסוכן ועיבוד התוצאה
        result = self._process_task(handling_agent, initial_message)
        
        # עדכון סטטוס המשימה לפי התוצאה
        if result.get("status") == "success":
            self._update_task_status(task_id, TaskStatus.COMPLETED, result=result.get("result"))
        else:
            self._update_task_status(task_id, TaskStatus.FAILED, error=result.get("error"))
            
        # החזרת תוצאות המשימה
        return {
            "task_id": task_id,
            "status": result.get("status"),
            "result": result.get("result"),
            "error": result.get("error"),
            "history": self._get_task_history(task_id)
        }
    
    def _select_initial_agent(self, task_description: str) -> Optional[BaseAgent]:
        """
        בחירת הסוכן המתאים ביותר לטיפול ראשוני במשימה
        
        Args:
            task_description: תיאור המשימה
            
        Returns:
            הסוכן המתאים ביותר או None אם לא נמצא סוכן מתאים
        """
        # כאן יש להוסיף לוגיקה חכמה לבחירת הסוכן המתאים ביותר
        # לדוגמה, ניתן להשתמש במודל AI לניתוח המשימה וקביעת הסוכן המתאים
        
        # לצורך הדוגמה, נבחר את סוכן המוצר כברירת מחדל
        if "product" in self.agents:
            return self.agents["product"]
        
        # אם אין סוכן מוצר, נחזיר את הסוכן הראשון ברשימה
        if self.agents:
            return list(self.agents.values())[0]
            
        return None
    
    def _process_task(self, agent: BaseAgent, message: Message) -> Dict[str, Any]:
        """
        עיבוד המשימה על ידי הסוכן הנבחר
        
        Args:
            agent: הסוכן שיטפל במשימה
            message: הודעת המשימה
            
        Returns:
            תוצאות המשימה
        """
        try:
            # העברת המשימה לסוכן
            response = agent.process_message(message)
            
            # מעקב אחר התקדמות המשימה
            task_id = message.task_id
            current_agent = agent
            max_iterations = 10  # הגבלת מספר האיטרציות למניעת לולאות אינסופיות
            iterations = 0
            
            # התהליך ממשיך עד שהמשימה מסתיימת או עד שמגיעים למספר האיטרציות המקסימלי
            while iterations < max_iterations:
                iterations += 1
                
                # בדיקה האם הסוכן הנוכחי סיים את הטיפול במשימה
                if response.message_type == MessageType.RESULT:
                    return {
                        "status": "success",
                        "result": response.content
                    }
                
                # בדיקה האם הסוכן הנוכחי נתקל בשגיאה
                if response.message_type == MessageType.ERROR:
                    return {
                        "status": "error",
                        "error": response.content.get("error", "Unknown error")
                    }
                
                # בדיקה האם הסוכן הנוכחי מבקש סיוע מסוכן אחר
                if response.message_type == MessageType.REQUEST and response.recipient != "system":
                    # הוספת ההודעה להיסטוריה
                    self._add_to_history(task_id, response.to_dict())
                    
                    # בדיקה האם הסוכן המבוקש קיים
                    if response.recipient not in self.agents:
                        error_msg = f"Agent {response.recipient} not found"
                        self._add_to_history(task_id, {
                            "message_id": str(uuid.uuid4()),
                            "task_id": task_id,
                            "sender": "system",
                            "recipient": response.sender,
                            "message_type": MessageType.ERROR.value,
                            "content": {"error": error_msg},
                            "created_at": datetime.now().isoformat()
                        })
                        return {"status": "error", "error": error_msg}
                    
                    # העברת הבקשה לסוכן המבוקש
                    next_agent = self.agents[response.recipient]
                    response_from_next = next_agent.process_message(response)
                    
                    # הוספת התשובה להיסטוריה
                    self._add_to_history(task_id, response_from_next.to_dict())
                    
                    # החזרת התשובה לסוכן המקורי
                    response = current_agent.process_message(response_from_next)
                    
                    # הוספת התשובה החדשה להיסטוריה
                    self._add_to_history(task_id, response.to_dict())
                else:
                    # סיום האיטרציה הנוכחית - הסוכן לא ביקש עזרה מאף אחד או פנה למערכת
                    break
            
            # אם הגענו למספר האיטרציות המקסימלי ללא תוצאה סופית
            if iterations >= max_iterations:
                error_msg = "Max iterations reached without resolution"
                return {"status": "error", "error": error_msg}
            
            # התהליך הסתיים ללא תוצאה ברורה
            return {
                "status": "success",
                "result": response.content
            }
            
        except Exception as e:
            logger.error(f"Error processing task: {str(e)}")
            return {
                "status": "error",
                "error": f"Internal error: {str(e)}"
            }
    
    def _update_task_status(self, task_id: str, status: TaskStatus, result: Any = None, error: str = None) -> None:
        """
        עדכון סטטוס המשימה במסד הנתונים
        
        Args:
            task_id: מזהה המשימה
            status: הסטטוס החדש
            result: תוצאות המשימה (אופציונלי)
            error: הודעת שגיאה (אופציונלי)
        """
        update_data = {
            "status": status.value,
            "updated_at": datetime.now()
        }
        
        if result is not None:
            update_data["result"] = result
            
        if error is not None:
            update_data["error"] = error
            
        self.db.update_task(task_id, update_data)
    
    def _add_to_history(self, task_id: str, message_data: Dict[str, Any]) -> None:
        """
        הוספת הודעה להיסטוריית המשימה
        
        Args:
            task_id: מזהה המשימה
            message_data: נתוני ההודעה
        """
        self.db.add_message_to_history(task_id, message_data)
    
    def _get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """
        קבלת היסטוריית המשימה
        
        Args:
            task_id: מזהה המשימה
            
        Returns:
            רשימת ההודעות בהיסטוריית המשימה
        """
        task = self.db.get_task(task_id)
        return task.get("history", []) if task else []
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        קבלת סטטוס המשימה
        
        Args:
            task_id: מזהה המשימה
            
        Returns:
            מצב המשימה הנוכחי
        """
        task = self.db.get_task(task_id)
        if not task:
            return {"error": "Task not found"}
            
        return {
            "task_id": task.get("task_id"),
            "description": task.get("description"),
            "status": task.get("status"),
            "created_at": task.get("created_at"),
            "updated_at": task.get("updated_at"),
            "result": task.get("result"),
            "error": task.get("error", None)
        }
    
    def get_agent_info(self, agent_type: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        קבלת מידע על הסוכנים במערכת
        
        Args:
            agent_type: סוג הסוכן (אופציונלי)
            
        Returns:
            מידע על סוכן ספציפי או על כל הסוכנים
        """
        if agent_type:
            if agent_type not in self.agents:
                return {"error": f"Agent {agent_type} not found"}
                
            agent = self.agents[agent_type]
            return {
                "type": agent.agent_type,
                "name": agent.name,
                "description": agent.description,
                "capabilities": agent.capabilities
            }
        
        # החזרת מידע על כל הסוכנים
        return [
            {
                "type": agent.agent_type,
                "name": agent.name,
                "description": agent.description,
                "capabilities": agent.capabilities
            }
            for agent in self.agents.values()
        ]
"""