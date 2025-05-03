
# core/protocol.py
"""
פרוטוקול A2A לתקשורת בין סוכנים
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

class MessageType(Enum):
    """סוגי הודעות בפרוטוקול A2A"""
    TASK = "task"                   # הודעת משימה חדשה
    REQUEST = "request"             # בקשה מסוכן אחר
    RESPONSE = "response"           # תשובה לבקשה
    RESULT = "result"               # תוצאה סופית של משימה
    ERROR = "error"                 # הודעת שגיאה
    STATUS = "status"               # עדכון סטטוס
    NOTIFICATION = "notification"   # הודעת מידע
    ABORT = "abort"                 # ביטול משימה

class TaskStatus(Enum):
    """סטטוסי משימה"""
    PENDING = "pending"             # ממתינה לטיפול
    IN_PROGRESS = "in_progress"     # בביצוע
    COMPLETED = "completed"         # הושלמה בהצלחה
    FAILED = "failed"               # נכשלה
    ABORTED = "aborted"             # בוטלה

class Priority(Enum):
    """רמות עדיפות"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Message:
    """הודעה בפרוטוקול A2A"""
    message_id: str
    task_id: str
    sender: str
    recipient: str
    message_type: MessageType
    content: Dict[str, Any]
    created_at: str
    priority: Priority = Priority.MEDIUM
    parent_message_id: Optional[str] = None
    expires_at: Optional[str] = None
    
    def to_json(self) -> str:
        """המרה לפורמט JSON"""
        data = {
            "message_id": self.message_id,
            "task_id": self.task_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type.value,
            "content": self.content,
            "created_at": self.created_at,
            "priority": self.priority.value,
            "parent_message_id": self.parent_message_id,
            "expires_at": self.expires_at
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """יצירה מפורמט JSON"""
        data = json.loads(json_str)
        return cls(
            message_id=data["message_id"],
            task_id=data["task_id"],
            sender=data["sender"],
            recipient=data["recipient"],
            message_type=MessageType(data["message_type"]),
            content=data["content"],
            created_at=data["created_at"],
            priority=Priority(data.get("priority", Priority.MEDIUM.value)),
            parent_message_id=data.get("parent_message_id"),
            expires_at=data.get("expires_at")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """המרה למילון"""
        return {
            "message_id": self.message_id,
            "task_id": self.task_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type.value,
            "content": self.content,
            "created_at": self.created_at,
            "priority": self.priority.value,
            "parent_message_id": self.parent_message_id,
            "expires_at": self.expires_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """יצירה ממילון"""
        return cls(
            message_id=data["message_id"],
            task_id=data["task_id"],
            sender=data["sender"],
            recipient=data["recipient"],
            message_type=MessageType(data["message_type"]),
            content=data["content"],
            created_at=data["created_at"],
            priority=Priority(data.get("priority", Priority.MEDIUM.value)),
            parent_message_id=data.get("parent_message_id"),
            expires_at=data.get("expires_at")
        )

@dataclass
class TaskRequest:
    """בקשת משימה מעוצבת לסוכן"""
    task_id: str
    description: str
    context: Dict[str, Any]
    requirements: List[str]
    constraints: Dict[str, Any]
    priority: Priority = Priority.MEDIUM
    deadline: Optional[str] = None
    
    def to_message(self, sender: str, recipient: str) -> Message:
        """המרה להודעת משימה"""
        return Message(
            message_id=str(uuid.uuid4()),
            task_id=self.task_id,
            sender=sender,
            recipient=recipient,
            message_type=MessageType.TASK,
            content={
                "description": self.description,
                "context": self.context,
                "requirements": self.requirements,
                "constraints": self.constraints,
                "deadline": self.deadline
            },
            created_at=datetime.now().isoformat(),
            priority=self.priority
        )

@dataclass
class RequestForHelp:
    """בקשת עזרה מסוכן אחר"""
    original_task_id: str
    question: str
    required_capability: str
    context: Dict[str, Any]
    urgency: Priority = Priority.MEDIUM
    
    def to_message(self, sender: str, recipient: str) -> Message:
        """המרה להודעת בקשה"""
        return Message(
            message_id=str(uuid.uuid4()),
            task_id=self.original_task_id,
            sender=sender,
            recipient=recipient,
            message_type=MessageType.REQUEST,
            content={
                "question": self.question,
                "required_capability": self.required_capability,
                "context": self.context
            },
            created_at=datetime.now().isoformat(),
            priority=self.urgency
        )

class ProtocolValidator:
    """מוודא פרוטוקול A2A"""
    
    @staticmethod
    def validate_message(message: Message) -> bool:
        """
        אימות תקינות ההודעה
        
        Args:
            message: ההודעה לאימות
            
        Returns:
            האם ההודעה תקינה
        """
        required_fields = [
            "message_id", "task_id", "sender", "recipient",
            "message_type", "content", "created_at"
        ]
        
        # בדיקת קיום שדות חובה
        for field in required_fields:
            if not hasattr(message, field) or getattr(message, field) is None:
                logger.error(f"Missing required field: {field}")
                return False
        
        # בדיקת תקינות מזהי הודעה ומשימה
        if not isinstance(message.message_id, str) or not message.message_id:
            logger.error("Invalid message_id")
            return False
            
        if not isinstance(message.task_id, str) or not message.task_id:
            logger.error("Invalid task_id")
            return False
        
        # בדיקת תקינות סוג ההודעה
        if not isinstance(message.message_type, MessageType):
            logger.error("Invalid message_type")
            return False
        
        # בדיקת תקינות מבנה התוכן
        if not isinstance(message.content, dict):
            logger.error("Content must be a dictionary")
            return False
        
        # בדיקת תקינות זמנים
        try:
            datetime.fromisoformat(message.created_at)
            if message.expires_at:
                datetime.fromisoformat(message.expires_at)
        except ValueError:
            logger.error("Invalid datetime format")
            return False
        
        return True
    
    @staticmethod
    def validate_task_result(content: Dict[str, Any]) -> bool:
        """
        אימות תקינות תוצאת משימה
        
        Args:
            content: תוכן התוצאה
            
        Returns:
            האם התוצאה תקינה
        """
        required_fields = ["status", "result", "execution_time"]
        
        for field in required_fields:
            if field not in content:
                logger.error(f"Missing required field in result: {field}")
                return False
        
        # בדיקת תקינות סטטוס
        if content["status"] not in ["success", "partial", "failed"]:
            logger.error("Invalid status in result")
            return False
        
        return True
"""