"""
סכמות Pydantic עבור ה-API
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# סכמות בסיסיות

class ErrorResponse(BaseModel):
    """מודל לשגיאות"""
    status: str = Field("error", description="סטטוס")
    message: str = Field(..., description="הודעת שגיאה")
    details: Optional[Dict[str, Any]] = Field(None, description="פרטים נוספים")

# סכמות משימות

class TaskCreate(BaseModel):
    """מודל ליצירת משימה חדשה"""
    description: str = Field(..., description="תיאור המשימה")
    context: Optional[Dict[str, Any]] = Field({}, description="הקשר המשימה")
    requirements: Optional[List[str]] = Field([], description="דרישות המשימה")
    initial_agent: Optional[str] = Field(None, description="סוכן ראשוני")

class TaskResponse(BaseModel):
    """מודל לתגובת משימה"""
    task_id: str = Field(..., description="מזהה המשימה")
    description: str = Field(..., description="תיאור המשימה")
    status: str = Field(..., description="סטטוס המשימה")
    created_at: str = Field(..., description="זמן יצירה")
    updated_at: str = Field(..., description="זמן עדכון אחרון")
    result: Optional[Any] = Field(None, description="תוצאות המשימה")
    error: Optional[str] = Field(None, description="שגיאה (אם יש)")
    history: Optional[List[Dict[str, Any]]] = Field([], description="היסטוריית הודעות")

# סכמות הודעות

class MessageCreate(BaseModel):
    """מודל ליצירת הודעה חדשה"""
    task_id: str = Field(..., description="מזהה המשימה")
    sender: str = Field(..., description="שולח ההודעה")
    recipient: str = Field(..., description="מקבל ההודעה")
    message_type: str = Field(..., description="סוג ההודעה")
    content: Dict[str, Any] = Field(..., description="תוכן ההודעה")
    parent_message_id: Optional[str] = Field(None, description="מזהה הודעת אב")

class MessageResponse(BaseModel):
    """מודל לתגובת הודעה"""
    message_id: str = Field(..., description="מזהה ההודעה")
    task_id: str = Field(..., description="מזהה המשימה")
    sender: str = Field(..., description="שולח ההודעה")
    recipient: str = Field(..., description="מקבל ההודעה")
    message_type: str = Field(..., description="סוג ההודעה")
    content: Dict[str, Any] = Field(..., description="תוכן ההודעה")
    created_at: str = Field(..., description="זמן יצירה")
    parent_message_id: Optional[str] = Field(None, description="מזהה הודעת אב")

# סכמות סוכנים

class Capability(BaseModel):
    """מודל ליכולת של סוכן"""
    description: str = Field(..., description="תיאור היכולת")
    level: int = Field(..., ge=1, le=5, description="רמת היכולת")

class AgentInfo(BaseModel):
    """מודל למידע על סוכן"""
    type: str = Field(..., description="סוג הסוכן")
    name: str = Field(..., description="שם הסוכן")
    description: str = Field(..., description="תיאור הסוכן")
    capabilities: List[str] = Field(..., description="יכולות הסוכן")
    status: Optional[str] = Field("active", description="סטטוס הסוכן")
    current_task: Optional[str] = Field(None, description="משימה נוכחית")

# סכמות מערכת

class SystemStatus(BaseModel):
    """מודל לסטטוס מערכת"""
    status: str = Field(..., description="סטטוס המערכת")
    version: str = Field(..., description="גרסת המערכת")
    task_count: int = Field(..., description="מספר משימות")
    message_count: int = Field(..., description="מספר הודעות")
    agent_count: int = Field(..., description="מספר סוכנים")
    active_tasks: int = Field(..., description="מספר משימות פעילות")
    task_status_distribution: Dict[str, int] = Field(..., description="התפלגות סטטוס משימות")
    timestamp: str = Field(..., description="זמן בדיקה")
    uptime: str = Field(..., description="זמן פעילות")