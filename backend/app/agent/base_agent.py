from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel
from typing import Optional, Any, List
import uuid
from datetime import datetime


class AgentTrigger(str, Enum):
    MANUAL = "manual"
    CHAT = "chat"
    EVENT = "event"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"


class AgentInput(BaseModel):
    project_id: str
    user_id: str
    data: dict


class AgentResult(BaseModel):
    success: bool
    output: dict
    items_created: List[str] = []
    message: str = ""
    error: Optional[str] = None


class BaseDevFlowAgent(ABC):
    """
    Abstract base class for all DevFlow agents.
    
    Agents are self-contained units that perform specific tasks
    within the DevFlow ecosystem. They can be triggered manually,
    by chat, by events, on a schedule, or via webhooks.
    """
    
    name: str
    description: str
    trigger: AgentTrigger
    schedule: Optional[str] = None  # Cron string for SCHEDULED agents
    
    def __init__(self):
        if not hasattr(self, 'name') or not self.name:
            raise ValueError(f"{self.__class__.__name__} must define a 'name' attribute")
        if not hasattr(self, 'description') or not self.description:
            raise ValueError(f"{self.__class__.__name__} must define a 'description' attribute")
        if not hasattr(self, 'trigger') or not self.trigger:
            raise ValueError(f"{self.__class__.__name__} must define a 'trigger' attribute")
    
    @abstractmethod
    async def run(self, input_data: AgentInput, run_id: str) -> AgentResult:
        """
        Execute the agent's main logic.
        
        Args:
            input_data: The input data for the agent
            run_id: Unique identifier for this run (for logging)
        
        Returns:
            AgentResult with success status and output
        """
        pass
    
    async def log(self, run_id: str, message: str, level: str = "info"):
        """
        Log a message for this agent run.
        
        This will be stored in the database and pushed via WebSocket
        to connected clients.
        
        Args:
            run_id: The run ID to log for
            message: The log message
            level: Log level (info, warning, error)
        """
        from app.database import async_session_maker
        from app.models.agent_run import AgentRunLog
        from sqlalchemy import select
        from app.services.websocket import manager
        
        async with async_session_maker() as db:
            log_entry = AgentRunLog(
                agent_run_id=uuid.UUID(run_id),
                level=level,
                message=message,
                timestamp=datetime.utcnow()
            )
            db.add(log_entry)
            await db.commit()
        
        # Push via WebSocket
        await manager.broadcast_to_run(run_id, {
            "type": "agent_log",
            "run_id": run_id,
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def to_dict(self) -> dict:
        """Serialize agent metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger.value,
            "schedule": self.schedule
        }
