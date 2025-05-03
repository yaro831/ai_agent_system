"""
נתיבי API למערכת סוכני בינה מלאכותית
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Body, Query, Path, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from ..core.agent_manager import AgentManager
from ..storage.database import Database
from ..config import settings
from ..core.protocol import Message, MessageType, TaskStatus
from ..core.utils import generate_task_id, safe_json_dumps, safe_json_loads
from .schemas import (
    TaskCreate, 
    TaskResponse, 
    MessageCreate, 
    MessageResponse, 
    AgentInfo, 
    SystemStatus,
    ErrorResponse
)

logger = logging.getLogger(__name__)

# יצירת ראוטר FastAPI
router = APIRouter()

# אתחול מנהל הסוכנים
agent_manager = AgentManager()

# אתחול מסד הנתונים
db = Database()

# אבטחה - בדיקת API Key
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    אימות מפתח API
    
    Args:
        api_key: מפתח ה-API מה-header
        
    Returns:
        מפתח ה-API אם תקין
        
    Raises:
        HTTPException: אם המפתח לא תקין
    """
    if api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key

# נתיב בריאות המערכת - לא דורש אימות
@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """בדיקת בריאות המערכת"""
    return {
        "status": "healthy",
        "version": settings.PROTOCOL_VERSION,
        "timestamp": datetime.now().isoformat()
    }

# נתיבי משימות
@router.post("/tasks", response_model=TaskResponse, responses={400: {"model": ErrorResponse}})
async def create_task(
    task: TaskCreate = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """
    יצירת משימה חדשה
    
    Args:
        task: נתוני המשימה
        
    Returns:
        פרטי המשימה שנוצרה
    """
    try:
        # ביצוע המשימה
        result = agent_manager.execute_task(
            task_description=task.description,
            initial_agent=task.initial_agent
        )
        
        # החזרת התוצאה
        return result
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create task: {str(e)}"
        )

@router.get("/tasks/{task_id}", response_model=TaskResponse, responses={404: {"model": ErrorResponse}})
async def get_task(
    task_id: str = Path(..., description="מזהה המשימה"),
    api_key: str = Depends(verify_api_key)
):
    """
    קבלת פרטי משימה
    
    Args:
        task_id: מזהה המשימה
    
    Returns:
        פרטי המשימה
    """
    task = agent_manager.get_task_status(task_id)
    
    if not task or "error" in task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return task

@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    limit: int = Query(100, description="מספר מקסימלי של תוצאות"),
    skip: int = Query(0, description="מספר תוצאות לדילוג"),
    status: Optional[str] = Query(None, description="סינון לפי סטטוס"),
    api_key: str = Depends(verify_api_key)
):
    """
    קבלת רשימת משימות
    
    Args:
        limit: מספר מקסימלי של תוצאות
        skip: מספר תוצאות לדילוג
        status: סינון לפי סטטוס
        
    Returns:
        רשימת משימות
    """
    # הכנת פילטרים
    filters = {}
    if status:
        filters["status"] = status
    
    # קבלת המשימות ממסד הנתונים
    tasks = db.get_all_tasks(limit=limit, skip=skip, filters=filters)
    
    return tasks

@router.delete("/tasks/{task_id}", response_model=Dict[str, Any], responses={404: {"model": ErrorResponse}})
async def delete_task(
    task_id: str = Path(..., description="מזהה המשימה"),
    api_key: str = Depends(verify_api_key)
):
    """
    מחיקת משימה
    
    Args:
        task_id: מזהה המשימה
        
    Returns:
        אישור מחיקה
    """
    # בדיקה אם המשימה קיימת
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    # מחיקת המשימה
    success = db.delete_task(task_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task with ID {task_id}"
        )
    
    return {"status": "success", "message": f"Task {task_id} deleted successfully"}

# נתיבי הודעות
@router.get("/tasks/{task_id}/messages", response_model=List[MessageResponse])
async def get_task_messages(
    task_id: str = Path(..., description="מזהה המשימה"),
    api_key: str = Depends(verify_api_key)
):
    """
    קבלת הודעות של משימה
    
    Args:
        task_id: מזהה המשימה
        
    Returns:
        רשימת הודעות
    """
    # בדיקה אם המשימה קיימת
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    # קבלת ההודעות
    messages = db.get_messages_by_task(task_id)
    
    return messages

@router.post("/messages", response_model=MessageResponse, responses={400: {"model": ErrorResponse}})
async def create_message(
    message: MessageCreate = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """
    יצירת הודעה חדשה
    
    Args:
        message: נתוני ההודעה
        
    Returns:
        פרטי ההודעה שנוצרה
    """
    try:
        # המרה לאובייקט Message
        new_message = Message(
            message_id=generate_task_id(),
            task_id=message.task_id,
            sender=message.sender,
            recipient=message.recipient,
            message_type=MessageType(message.message_type),
            content=message.content,
            created_at=datetime.now().isoformat(),
            parent_message_id=message.parent_message_id
        )
        
        # העברת ההודעה למנהל הסוכנים
        response = agent_manager.process_message(new_message.recipient, new_message)
        
        # החזרת התשובה
        return response.to_dict()
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create message: {str(e)}"
        )

# נתיבי סוכנים
@router.get("/agents", response_model=List[AgentInfo])
async def list_agents(
    api_key: str = Depends(verify_api_key)
):
    """
    קבלת רשימת סוכנים
    
    Returns:
        רשימת סוכנים
    """
    return agent_manager.get_agent_info()

@router.get("/agents/{agent_type}", response_model=AgentInfo, responses={404: {"model": ErrorResponse}})
async def get_agent_info(
    agent_type: str = Path(..., description="סוג הסוכן"),
    api_key: str = Depends(verify_api_key)
):
    """
    קבלת מידע על סוכן
    
    Args:
        agent_type: סוג הסוכן
        
    Returns:
        מידע על הסוכן
    """
    agent_info = agent_manager.get_agent_info(agent_type)
    
    if not agent_info or "error" in agent_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_type} not found"
        )
    
    return agent_info

# נתיבי סטטוס מערכת
@router.get("/system/status", response_model=SystemStatus)
async def get_system_status(
    api_key: str = Depends(verify_api_key)
):
    """
    קבלת סטטוס מערכת
    
    Returns:
        סטטוס המערכת
    """
    # קבלת סטטיסטיקות ממסד הנתונים
    db_stats = db.get_statistics()
    
    # שילוב עם סטטוס מערכת קיים
    system_status = db.get_system_status()
    
    # שילוב הנתונים
    combined_status = {**system_status, **db_stats}
    
    # הוספת נתונים נוספים
    combined_status["version"] = settings.PROTOCOL_VERSION
    combined_status["uptime"] = "Unknown"  # ניתן להוסיף מנגנון מדידת זמן פעילות
    
    return combined_status

@router.post("/system/shutdown", response_model=Dict[str, Any])
async def shutdown_system(
    api_key: str = Depends(verify_api_key)
):
    """
    כיבוי מערכת
    
    Returns:
        אישור כיבוי
    """
    logger.warning("System shutdown requested via API")
    
    # במציאות כאן היינו מבצעים כיבוי מסודר של המערכת
    
    return {
        "status": "success",
        "message": "System shutdown initiated",
        "timestamp": datetime.now().isoformat()
    }

def create_app() -> FastAPI:
    """
    יצירת אפליקציית FastAPI
    
    Returns:
        אפליקציית FastAPI מוגדרת
    """
    # יצירת אפליקציה
    app = FastAPI(
        title="AI Agent System API",
        description="ממשק API למערכת סוכני בינה מלאכותית",
        version=settings.PROTOCOL_VERSION
    )
    
    # הוספת CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # בסביבת ייצור - יש להגדיר את המקורות המותרים
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # הוספת ראוטר
    app.include_router(router, prefix="/api")
    
    # טיפול בשגיאות כללי
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": f"Internal server error: {str(exc)}"}
        )
    
    return app