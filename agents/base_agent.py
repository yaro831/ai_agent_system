"""
מחלקת בסיס לכל הסוכנים במערכת
"""
import logging
import json
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

import openai

from ..core.protocol import Message, MessageType, TaskStatus
from ..config import settings
from ..core.utils import safe_json_dumps, retry_with_backoff

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """מחלקת בסיס לסוכני בינה מלאכותית"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        אתחול הסוכן
        
        Args:
            config: קונפיגורציה ספציפית לסוכן
        """
        self.agent_type = config.get("agent_type", self.__class__.__name__.lower().replace("agent", ""))
        self.name = config.get("name", "")
        self.description = config.get("description", "")
        self.model = config.get("model", settings.DEFAULT_MODEL)
        self.temperature = config.get("temperature", settings.DEFAULT_AGENT_PARAMS["temperature"])
        self.system_prompt = config.get("system_prompt", "")
        self.capabilities = config.get("capabilities", [])
        
        # OpenAI client initialization
        self.client = openai.Client(
            api_key=settings.OPENAI_API_KEY,
            organization=settings.OPENAI_ORG_ID
        )
        
        # Agent state
        self.current_task = None
        self.task_history = []
        self.skills = self._initialize_skills()
        
        logger.info(f"Initialized agent: {self.agent_type}")
    
    @abstractmethod
    def _initialize_skills(self) -> Dict[str, Any]:
        """אתחול מיומנויות ספציפיות לסוכן - חייב להיות מוגדר בסוכנים הנגזרים"""
        pass
    
    @abstractmethod
    def _process_request(self, message: Message) -> Dict[str, Any]:
        """עיבוד בקשה - חייב להיות מוגדר בסוכנים הנגזרים"""
        pass
    
    def process_message(self, message: Message) -> Message:
        """
        עיבוד הודעה כללית
        
        Args:
            message: ההודעה לעיבוד
            
        Returns:
            תגובה להודעה
        """
        try:
            # Validate message
            if not self._validate_message(message):
                return self._create_error_response(message, "Invalid message format")
            
            # Process based on message type
            if message.message_type == MessageType.TASK:
                return self._handle_task(message)
            elif message.message_type == MessageType.REQUEST:
                return self._handle_request(message)
            elif message.message_type == MessageType.RESPONSE:
                return self._handle_response(message)
            elif message.message_type == MessageType.STATUS:
                return self._handle_status_request(message)
            else:
                return self._create_error_response(message, f"Unsupported message type: {message.message_type}")
                
        except Exception as e:
            logger.error(f"Error processing message in {self.agent_type}: {str(e)}")
            return self._create_error_response(message, str(e))
    
    def _handle_task(self, message: Message) -> Message:
        """טיפול במשימה חדשה"""
        self.current_task = message
        self.task_history.append(message)
        
        # Process the task using agent's capabilities
        result = self._process_request(message)
        
        # Check if we need help from other agents
        if result.get("requires_assistance"):
            needed_capability = result.get("required_capability")
            needed_agent = result.get("required_agent")
            
            # Create request to other agent
            request_message = Message(
                message_id=str(uuid.uuid4()),
                task_id=message.task_id,
                sender=self.agent_type,
                recipient=needed_agent,
                message_type=MessageType.REQUEST,
                content={
                    "question": result.get("question"),
                    "context": result.get("context", {}),
                    "required_capability": needed_capability
                },
                created_at=datetime.now().isoformat(),
                parent_message_id=message.message_id
            )
            
            return request_message
        
        # Return result directly
        return self._create_result_response(message, result)
    
    def _handle_request(self, message: Message) -> Message:
        """טיפול בבקשה לעזרה"""
        result = self._process_request(message)
        
        # Create response to the requesting agent
        response_message = Message(
            message_id=str(uuid.uuid4()),
            task_id=message.task_id,
            sender=self.agent_type,
            recipient=message.sender,
            message_type=MessageType.RESPONSE,
            content=result,
            created_at=datetime.now().isoformat(),
            parent_message_id=message.message_id
        )
        
        return response_message
    
    def _handle_response(self, message: Message) -> Message:
        """טיפול בתשובה מסוכן אחר"""
        # Update current task with the received information
        if self.current_task:
            self._update_task_context(message.content)
            
            # Continue processing the task with the new information
            result = self._process_request(self.current_task)
            
            # Check if task is complete
            if result.get("status") == "complete":
                return self._create_result_response(self.current_task, result)
            else:
                # Need more information or different agent
                return self._handle_task(self.current_task)
        
        return self._create_error_response(message, "No active task to update")
    
    def _handle_status_request(self, message: Message) -> Message:
        """טיפול בבקשת סטטוס"""
        status_info = {
            "agent_type": self.agent_type,
            "status": "active",
            "current_task": self.current_task.message_id if self.current_task else None,
            "capabilities": self.capabilities,
            "task_history_size": len(self.task_history)
        }
        
        response_message = Message(
            message_id=str(uuid.uuid4()),
            task_id=message.task_id,
            sender=self.agent_type,
            recipient=message.sender,
            message_type=MessageType.RESPONSE,
            content=status_info,
            created_at=datetime.now().isoformat(),
            parent_message_id=message.message_id
        )
        
        return response_message
    
    @retry_with_backoff(max_retries=3, exceptions=(openai.RateLimitError, openai.APIError))
    def _call_openai(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """קריאה ל-OpenAI API עם retry"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=kwargs.get("max_tokens", settings.MAX_TOKENS_PER_REQUEST),
                **kwargs
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    def _prepare_prompt(self, message: Message) -> List[Dict[str, str]]:
        """הכנת הפרומפט לOpenAI"""
        messages = []
        
        # Add system prompt
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        # Add conversation history (last 5 messages)
        for msg in self.task_history[-5:]:
            role = "user" if msg.sender != self.agent_type else "assistant"
            messages.append({
                "role": role,
                "content": safe_json_dumps(msg.content)
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": safe_json_dumps(message.content)
        })
        
        return messages
    
    def _update_task_context(self, new_information: Dict[str, Any]) -> None:
        """עדכון הקשר המשימה הנוכחית"""
        if self.current_task and isinstance(self.current_task.content, dict):
            self.current_task.content.setdefault("context", {}).update(new_information)
    
    def _validate_message(self, message: Message) -> bool:
        """אימות תקינות ההודעה"""
        required_fields = ["message_id", "task_id", "sender", "recipient", "message_type", "content"]
        
        for field in required_fields:
            if not hasattr(message, field) or getattr(message, field) is None:
                logger.error(f"Missing required field: {field}")
                return False
        
        return True
    
    def _create_result_response(self, original_message: Message, result: Dict[str, Any]) -> Message:
        """יצירת הודעת תוצאה"""
        return Message(
            message_id=str(uuid.uuid4()),
            task_id=original_message.task_id,
            sender=self.agent_type,
            recipient=original_message.sender if original_message.sender != "system" else "system",
            message_type=MessageType.RESULT,
            content=result,
            created_at=datetime.now().isoformat(),
            parent_message_id=original_message.message_id
        )
    
    def _create_error_response(self, original_message: Message, error_message: str) -> Message:
        """יצירת הודעת שגיאה"""
        return Message(
            message_id=str(uuid.uuid4()),
            task_id=original_message.task_id,
            sender=self.agent_type,
            recipient=original_message.sender if original_message.sender != "system" else "system",
            message_type=MessageType.ERROR,
            content={"error": error_message},
            created_at=datetime.now().isoformat(),
            parent_message_id=original_message.message_id
        )
    
    def get_capabilities(self) -> List[str]:
        """קבלת רשימת היכולות של הסוכן"""
        return self.capabilities
    
    def get_status(self) -> Dict[str, Any]:
        """קבלת סטטוס הסוכן"""
        return {
            "agent_type": self.agent_type,
            "name": self.name,
            "status": "active" if self.current_task else "idle",
            "current_task": self.current_task.task_id if self.current_task else None,
            "tasks_processed": len(self.task_history),
            "capabilities": self.capabilities
        }