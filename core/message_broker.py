
# core/message_broker.py
"""
מתווך הודעות לניהול תקשורת בין סוכנים
"""
from typing import Dict, List, Any, Optional, Callable
import json
import logging
import uuid
from datetime import datetime
import asyncio
from queue import Queue
import threading

from .protocol import Message, MessageType

logger = logging.getLogger(__name__)

class MessageBroker:
    """מתווך הודעות לניהול תקשורת בין סוכנים במערכת"""
    
    def __init__(self):
        """אתחול מתווך ההודעות"""
        self.queues: Dict[str, Queue] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_history: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        
    def publish(self, message: Message) -> None:
        """
        פרסום הודעה לכל המנויים
        
        Args:
            message: ההודעה לפרסום
        """
        with self.lock:
            # הוספת ההודעה להיסטוריה
            self.message_history.append(message.to_dict())
            
            # שליחת ההודעה לכל המנויים על המקבל
            if message.recipient in self.subscribers:
                for callback in self.subscribers[message.recipient]:
                    try:
                        callback(message)
                    except Exception as e:
                        logger.error(f"Error sending message to subscriber: {e}")
            
            # הוספת ההודעה לתור המקבל אם הוא קיים
            if message.recipient in self.queues:
                self.queues[message.recipient].put(message)
    
    def subscribe(self, agent_type: str, callback: Callable) -> None:
        """
        הרשמה לקבלת הודעות
        
        Args:
            agent_type: סוג הסוכן המנוי
            callback: פונקציה לטיפול בהודעות
        """
        with self.lock:
            if agent_type not in self.subscribers:
                self.subscribers[agent_type] = []
            self.subscribers[agent_type].append(callback)
    
    def create_queue(self, agent_type: str) -> Queue:
        """
        יצירת תור להודעות
        
        Args:
            agent_type: סוג הסוכן
            
        Returns:
            התור שנוצר
        """
        with self.lock:
            if agent_type not in self.queues:
                self.queues[agent_type] = Queue()
            return self.queues[agent_type]
    
    def get_message(self, agent_type: str, timeout: Optional[float] = None) -> Optional[Message]:
        """
        קבלת הודעה מהתור
        
        Args:
            agent_type: סוג הסוכן
            timeout: זמן המתנה מקסימלי (אופציונלי)
            
        Returns:
            הודעה או None אם אין בתור
        """
        if agent_type not in self.queues:
            return None
            
        queue = self.queues[agent_type]
        try:
            return queue.get(timeout=timeout)
        except:
            return None
    
    def get_history(self, filter_by: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        קבלת היסטוריית הודעות
        
        Args:
            filter_by: מסנני חיפוש (אופציונלי)
            
        Returns:
            רשימת ההודעות
        """
        with self.lock:
            if not filter_by:
                return self.message_history.copy()
            
            filtered_history = []
            for message in self.message_history:
                match = True
                for key, value in filter_by.items():
                    if key in message and message[key] != value:
                        match = False
                        break
                if match:
                    filtered_history.append(message)
            
            return filtered_history
    
    def clear_history(self) -> None:
        """מחיקת היסטוריית ההודעות"""
        with self.lock:
            self.message_history = []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        קבלת סטטיסטיקות על מתווך ההודעות
        
        Returns:
            סטטיסטיקות המערכת
        """
        with self.lock:
            message_types_count = {}
            for message in self.message_history:
                msg_type = message.get('message_type', 'unknown')
                message_types_count[msg_type] = message_types_count.get(msg_type, 0) + 1
            
            return {
                "total_messages": len(self.message_history),
                "message_types": message_types_count,
                "active_queues": list(self.queues.keys()),
                "subscribers": {agent: len(subs) for agent, subs in self.subscribers.items()}
            }
"""
