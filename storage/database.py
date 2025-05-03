 """
מודול לניהול מסד נתונים למערכת סוכני בינה מלאכותית
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import uuid
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

from ..config import settings
from ..core.utils import safe_json_dumps

logger = logging.getLogger(__name__)

class Database:
    """מנהל מסד נתונים למערכת"""
    
    def __init__(self):
        """אתחול חיבור מסד הנתונים"""
        try:
            # ניסיון להתחבר למסד הנתונים
            self.client = MongoClient(settings.DB_URI)
            self.db = self.client[settings.DB_NAME]
            
            # בדיקת חיבור
            self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
            # יצירת קולקציות אם לא קיימות
            self._initialize_collections()
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self._setup_fallback_storage()
            
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            self._setup_fallback_storage()
    
    def _initialize_collections(self):
        """יצירת קולקציות בסיסיות"""
        # רשימת קולקציות רצויות
        collections = [
            "tasks",
            "agents",
            "messages",
            "logs",
            "system_status"
        ]
        
        # יצירת קולקציות אם לא קיימות
        existing_collections = self.db.list_collection_names()
        for collection in collections:
            if collection not in existing_collections:
                self.db.create_collection(collection)
                logger.info(f"Created collection: {collection}")
        
        # יצירת אינדקסים
        self.db.tasks.create_index("task_id", unique=True)
        self.db.agents.create_index("agent_type", unique=True)
        self.db.messages.create_index("message_id", unique=True)
        self.db.messages.create_index("task_id")
    
    def _setup_fallback_storage(self):
        """הגדרת מנגנון אחסון חלופי למקרה של שגיאה בחיבור ל-MongoDB"""
        logger.warning("Setting up fallback storage using JSON files")
        
        # הגדרת שימוש באחסון מבוסס קבצים
        self.using_fallback = True
        
        # יצירת תיקיית אחסון אם לא קיימת
        self.storage_dir = os.path.join(os.path.dirname(__file__), "..", "..", "storage_files")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # יצירת קבצי אחסון בסיסיים אם לא קיימים
        self.files = {
            "tasks": os.path.join(self.storage_dir, "tasks.json"),
            "agents": os.path.join(self.storage_dir, "agents.json"),
            "messages": os.path.join(self.storage_dir, "messages.json"),
            "logs": os.path.join(self.storage_dir, "logs.json"),
            "system_status": os.path.join(self.storage_dir, "system_status.json")
        }
        
        # יצירת קבצים ריקים אם לא קיימים
        for file_path in self.files.values():
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False)
    
    def _load_data(self, collection: str) -> List[Dict[str, Any]]:
        """טעינת נתונים מאחסון מבוסס קבצים"""
        if not hasattr(self, "using_fallback") or not self.using_fallback:
            return []
            
        try:
            with open(self.files[collection], "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {collection} data: {str(e)}")
            return []
    
    def _save_data(self, collection: str, data: List[Dict[str, Any]]) -> bool:
        """שמירת נתונים באחסון מבוסס קבצים"""
        if not hasattr(self, "using_fallback") or not self.using_fallback:
            return False
            
        try:
            with open(self.files[collection], "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving {collection} data: {str(e)}")
            return False
    
    def create_task(self, task_data: Dict[str, Any]) -> bool:
        """
        יצירת משימה חדשה
        
        Args:
            task_data: נתוני המשימה
            
        Returns:
            האם היצירה הצליחה
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                tasks = self._load_data("tasks")
                
                # בדיקה אם המשימה כבר קיימת
                for task in tasks:
                    if task.get("task_id") == task_data.get("task_id"):
                        return False
                
                # הוספת המשימה
                tasks.append(task_data)
                return self._save_data("tasks", tasks)
            else:
                # שימוש במסד נתונים
                result = self.db.tasks.insert_one(task_data)
                return result.acknowledged
                
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        קבלת נתוני משימה
        
        Args:
            task_id: מזהה המשימה
            
        Returns:
            נתוני המשימה או None אם לא נמצאה
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                tasks = self._load_data("tasks")
                for task in tasks:
                    if task.get("task_id") == task_id:
                        return task
                return None
            else:
                # שימוש במסד נתונים
                return self.db.tasks.find_one({"task_id": task_id})
                
        except Exception as e:
            logger.error(f"Error getting task: {str(e)}")
            return None
    
    def update_task(self, task_id: str, update_data: Dict[str, Any]) -> bool:
        """
        עדכון נתוני משימה
        
        Args:
            task_id: מזהה המשימה
            update_data: נתוני העדכון
            
        Returns:
            האם העדכון הצליח
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                tasks = self._load_data("tasks")
                
                for i, task in enumerate(tasks):
                    if task.get("task_id") == task_id:
                        # עדכון הנתונים (שמירה על שדות מקוריים שאינם בעדכון)
                        for key, value in update_data.items():
                            task[key] = value
                        tasks[i] = task
                        return self._save_data("tasks", tasks)
                
                return False
            else:
                # שימוש במסד נתונים
                result = self.db.tasks.update_one(
                    {"task_id": task_id},
                    {"$set": update_data}
                )
                return result.modified_count > 0
                
        except Exception as e:
            logger.error(f"Error updating task: {str(e)}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """
        מחיקת משימה
        
        Args:
            task_id: מזהה המשימה
            
        Returns:
            האם המחיקה הצליחה
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                tasks = self._load_data("tasks")
                
                for i, task in enumerate(tasks):
                    if task.get("task_id") == task_id:
                        tasks.pop(i)
                        return self._save_data("tasks", tasks)
                
                return False
            else:
                # שימוש במסד נתונים
                result = self.db.tasks.delete_one({"task_id": task_id})
                
                # מחיקת הודעות קשורות
                self.db.messages.delete_many({"task_id": task_id})
                
                return result.deleted_count > 0
                
        except Exception as e:
            logger.error(f"Error deleting task: {str(e)}")
            return False
    
    def get_all_tasks(self, limit: int = 100, skip: int = 0, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        קבלת כל המשימות
        
        Args:
            limit: מספר מקסימלי של תוצאות
            skip: מספר תוצאות לדילוג
            filters: פילטרים לחיפוש
            
        Returns:
            רשימת משימות
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                tasks = self._load_data("tasks")
                
                # פילטור
                if filters:
                    filtered_tasks = []
                    for task in tasks:
                        match = True
                        for key, value in filters.items():
                            if key not in task or task[key] != value:
                                match = False
                                break
                        if match:
                            filtered_tasks.append(task)
                    tasks = filtered_tasks
                
                # דילוג ומגבלת תוצאות
                return tasks[skip:skip + limit]
            else:
                # שימוש במסד נתונים
                query = filters or {}
                return list(self.db.tasks.find(query).skip(skip).limit(limit))
                
        except Exception as e:
            logger.error(f"Error getting all tasks: {str(e)}")
            return []
    
    def add_message_to_history(self, task_id: str, message_data: Dict[str, Any]) -> bool:
        """
        הוספת הודעה להיסטוריית משימה
        
        Args:
            task_id: מזהה המשימה
            message_data: נתוני ההודעה
            
        Returns:
            האם ההוספה הצליחה
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                
                # שמירת ההודעה בקובץ הודעות
                messages = self._load_data("messages")
                messages.append(message_data)
                self._save_data("messages", messages)
                
                # עדכון היסטוריית המשימה
                tasks = self._load_data("tasks")
                for i, task in enumerate(tasks):
                    if task.get("task_id") == task_id:
                        if "history" not in task:
                            task["history"] = []
                        task["history"].append(message_data)
                        tasks[i] = task
                        return self._save_data("tasks", tasks)
                
                return False
            else:
                # שימוש במסד נתונים
                
                # שמירת ההודעה בקולקציית הודעות
                self.db.messages.insert_one(message_data)
                
                # עדכון היסטוריית המשימה
                result = self.db.tasks.update_one(
                    {"task_id": task_id},
                    {"$push": {"history": message_data}}
                )
                
                return result.modified_count > 0
                
        except Exception as e:
            logger.error(f"Error adding message to history: {str(e)}")
            return False
    
    def get_messages_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """
        קבלת הודעות של משימה
        
        Args:
            task_id: מזהה המשימה
            
        Returns:
            רשימת הודעות
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                messages = self._load_data("messages")
                
                return [msg for msg in messages if msg.get("task_id") == task_id]
            else:
                # שימוש במסד נתונים
                return list(self.db.messages.find({"task_id": task_id}).sort("created_at", 1))
                
        except Exception as e:
            logger.error(f"Error getting messages by task: {str(e)}")
            return []
    
    def save_agent_config(self, agent_type: str, config: Dict[str, Any]) -> bool:
        """
        שמירת קונפיגורציית סוכן
        
        Args:
            agent_type: סוג הסוכן
            config: נתוני הקונפיגורציה
            
        Returns:
            האם השמירה הצליחה
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                agents = self._load_data("agents")
                
                # חיפוש הסוכן הקיים
                for i, agent in enumerate(agents):
                    if agent.get("agent_type") == agent_type:
                        agents[i] = config
                        return self._save_data("agents", agents)
                
                # הוספת סוכן חדש
                agents.append(config)
                return self._save_data("agents", agents)
            else:
                # שימוש במסד נתונים
                result = self.db.agents.update_one(
                    {"agent_type": agent_type},
                    {"$set": config},
                    upsert=True
                )
                
                return result.acknowledged
                
        except Exception as e:
            logger.error(f"Error saving agent config: {str(e)}")
            return False
    
    def get_agent_config(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """
        קבלת קונפיגורציית סוכן
        
        Args:
            agent_type: סוג הסוכן
            
        Returns:
            נתוני הקונפיגורציה או None אם לא נמצא
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                agents = self._load_data("agents")
                
                for agent in agents:
                    if agent.get("agent_type") == agent_type:
                        return agent
                
                return None
            else:
                # שימוש במסד נתונים
                return self.db.agents.find_one({"agent_type": agent_type})
                
        except Exception as e:
            logger.error(f"Error getting agent config: {str(e)}")
            return None
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """
        קבלת כל הסוכנים
        
        Returns:
            רשימת כל הסוכנים
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                return self._load_data("agents")
            else:
                # שימוש במסד נתונים
                return list(self.db.agents.find())
                
        except Exception as e:
            logger.error(f"Error getting all agents: {str(e)}")
            return []
    
    def log_system_event(self, event_data: Dict[str, Any]) -> bool:
        """
        רישום אירוע מערכת
        
        Args:
            event_data: נתוני האירוע
            
        Returns:
            האם הרישום הצליח
        """
        try:
            # הוספת חותמת זמן אם לא קיימת
            if "timestamp" not in event_data:
                event_data["timestamp"] = datetime.now().isoformat()
            
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                logs = self._load_data("logs")
                logs.append(event_data)
                return self._save_data("logs", logs)
            else:
                # שימוש במסד נתונים
                result = self.db.logs.insert_one(event_data)
                return result.acknowledged
                
        except Exception as e:
            logger.error(f"Error logging system event: {str(e)}")
            return False
    
    def update_system_status(self, status_data: Dict[str, Any]) -> bool:
        """
        עדכון סטטוס מערכת
        
        Args:
            status_data: נתוני הסטטוס
            
        Returns:
            האם העדכון הצליח
        """
        try:
            # הוספת חותמת זמן
            status_data["updated_at"] = datetime.now().isoformat()
            
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                statuses = self._load_data("system_status")
                
                # אם אין רשומות, מוסיפים רשומה חדשה
                if not statuses:
                    statuses.append(status_data)
                else:
                    # עדכון הרשומה האחרונה
                    statuses[-1] = {**statuses[-1], **status_data}
                
                return self._save_data("system_status", statuses)
            else:
                # שימוש במסד נתונים - החלפת הרשומה האחרונה או יצירת חדשה
                result = self.db.system_status.update_one(
                    {"_id": "current"},  # מזהה קבוע לסטטוס נוכחי
                    {"$set": status_data},
                    upsert=True
                )
                
                return result.acknowledged
                
        except Exception as e:
            logger.error(f"Error updating system status: {str(e)}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        קבלת סטטוס מערכת נוכחי
        
        Returns:
            נתוני הסטטוס או מילון ריק אם אין נתונים
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                statuses = self._load_data("system_status")
                return statuses[-1] if statuses else {}
            else:
                # שימוש במסד נתונים
                status = self.db.system_status.find_one({"_id": "current"})
                return status or {}
                
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """
        ניקוי נתונים ישנים
        
        Args:
            days_to_keep: מספר ימים לשמירת נתונים
            
        Returns:
            האם הניקוי הצליח
        """
        try:
            # חישוב תאריך סף
            threshold_date = datetime.now() - datetime.timedelta(days=days_to_keep)
            threshold_str = threshold_date.isoformat()
            
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                
                # ניקוי משימות ישנות
                tasks = self._load_data("tasks")
                tasks = [task for task in tasks if task.get("created_at", "") >= threshold_str]
                self._save_data("tasks", tasks)
                
                # ניקוי הודעות ישנות
                messages = self._load_data("messages")
                messages = [msg for msg in messages if msg.get("created_at", "") >= threshold_str]
                self._save_data("messages", messages)
                
                # ניקוי לוגים ישנים
                logs = self._load_data("logs")
                logs = [log for log in logs if log.get("timestamp", "") >= threshold_str]
                self._save_data("logs", logs)
                
                return True
            else:
                # שימוש במסד נתונים
                
                # ניקוי משימות ישנות
                self.db.tasks.delete_many({"created_at": {"$lt": threshold_str}})
                
                # ניקוי הודעות ישנות
                self.db.messages.delete_many({"created_at": {"$lt": threshold_str}})
                
                # ניקוי לוגים ישנים
                self.db.logs.delete_many({"timestamp": {"$lt": threshold_str}})
                
                return True
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        קבלת סטטיסטיקות על המערכת
        
        Returns:
            נתוני סטטיסטיקה
        """
        stats = {
            "timestamp": datetime.now().isoformat(),
            "task_count": 0,
            "message_count": 0,
            "agent_count": 0,
            "task_status_distribution": {},
            "active_tasks": 0
        }
        
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                
                # ספירת משימות
                tasks = self._load_data("tasks")
                stats["task_count"] = len(tasks)
                
                # ספירת סטטוסי משימות
                status_count = {}
                for task in tasks:
                    status = task.get("status", "unknown")
                    status_count[status] = status_count.get(status, 0) + 1
                    
                    # ספירת משימות פעילות
                    if status == "in_progress":
                        stats["active_tasks"] += 1
                
                stats["task_status_distribution"] = status_count
                
                # ספירת הודעות
                messages = self._load_data("messages")
                stats["message_count"] = len(messages)
                
                # ספירת סוכנים
                agents = self._load_data("agents")
                stats["agent_count"] = len(agents)
                
            else:
                # שימוש במסד נתונים
                
                # ספירת משימות
                stats["task_count"] = self.db.tasks.count_documents({})
                
                # ספירת סטטוסי משימות
                status_count = {}
                for status_doc in self.db.tasks.aggregate([
                    {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                ]):
                    status_count[status_doc["_id"] or "unknown"] = status_doc["count"]
                    
                    # ספירת משימות פעילות
                    if status_doc["_id"] == "in_progress":
                        stats["active_tasks"] = status_doc["count"]
                
                stats["task_status_distribution"] = status_count
                
                # ספירת הודעות
                stats["message_count"] = self.db.messages.count_documents({})
                
                # ספירת סוכנים
                stats["agent_count"] = self.db.agents.count_documents({})
                
            return stats
                
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return stats
"""load(f)
        except Exception as e:
            logger.error(f"Error loading {collection} data: {str(e)}")
            return []
    
    def _save_data(self, collection: str, data: List[Dict[str, Any]]) -> bool:
        """שמירת נתונים באחסון מבוסס קבצים"""
        if not hasattr(self, "using_fallback") or not self.using_fallback:
            return False
            
        try:
            with open(self.files[collection], "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving {collection} data: {str(e)}")
            return False
    
    def create_task(self, task_data: Dict[str, Any]) -> bool:
        """
        יצירת משימה חדשה
        
        Args:
            task_data: נתוני המשימה
            
        Returns:
            האם היצירה הצליחה
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                tasks = self._load_data("tasks")
                
                # בדיקה אם המשימה כבר קיימת
                for task in tasks:
                    if task.get("task_id") == task_data.get("task_id"):
                        return False
                
                # הוספת המשימה
                tasks.append(task_data)
                return self._save_data("tasks", tasks)
            else:
                # שימוש במסד נתונים
                result = self.db.tasks.insert_one(task_data)
                return result.acknowledged
                
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        קבלת נתוני משימה
        
        Args:
            task_id: מזהה המשימה
            
        Returns:
            נתוני המשימה או None אם לא נמצאה
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                tasks = self._load_data("tasks")
                for task in tasks:
                    if task.get("task_id") == task_id:
                        return task
                return None
            else:
                # שימוש במסד נתונים
                return self.db.tasks.find_one({"task_id": task_id})
                
        except Exception as e:
            logger.error(f"Error getting task: {str(e)}")
            return None
    
    def update_task(self, task_id: str, update_data: Dict[str, Any]) -> bool:
        """
        עדכון נתוני משימה
        
        Args:
            task_id: מזהה המשימה
            update_data: נתוני העדכון
            
        Returns:
            האם העדכון הצליח
        """
        try:
            if hasattr(self, "using_fallback") and self.using_fallback:
                # שימוש באחסון מבוסס קבצים
                tasks = self._load_data("tasks")
                
                for i, task in enumerate(tasks):
                    if task.get("task_id") == task_id:
                        # עדכון הנתונים (שמירה על שדות מקוריים שאינם בעדכון)
                        for key, value in update_data.items():
                            task[key] = value
                        tasks[i] = task
                        return self._save_data("tasks", tasks)
                
                return
