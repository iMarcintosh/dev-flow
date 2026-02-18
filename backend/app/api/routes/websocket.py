"""
WebSocket endpoint for real-time agent chat streaming.

Provides real-time streaming responses from agents via WebSocket.
"""
import json
import logging
from typing import Dict, Optional
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user_ws
from app.models.user import User
from app.models.custom_agent import CustomAgent
from app.agent.custom_agent_runner import run_custom_agent_streaming
from sqlalchemy import select

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connected: {connection_id}")
    
    def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_json(self, connection_id: str, data: dict):
        """Send JSON message to connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(data)
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
    
    async def send_text(self, connection_id: str, message: str):
        """Send text message to connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending text to {connection_id}: {e}")


manager = ConnectionManager()


@router.websocket("/ws/agent-chat/{agent_id}")
async def agent_chat_websocket(
    websocket: WebSocket,
    agent_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for agent chat with streaming responses.
    
    Message format (client -> server):
    {
        "type": "message",
        "content": "user message",
        "conversation_id": "optional-uuid",
        "project_id": "optional-uuid"
    }
    
    Message format (server -> client):
    {
        "type": "start",
        "message_id": "uuid"
    }
    {
        "type": "stream",
        "content": "partial response text"
    }
    {
        "type": "end",
        "full_content": "complete response"
    }
    {
        "type": "error",
        "error": "error message"
    }
    """
    connection_id = f"{agent_id}_{id(websocket)}"
    
    try:
        # Verify token and get user
        user = await get_current_user_ws(token, db)
        if not user:
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        # Verify agent exists and user has access
        result = await db.execute(
            select(CustomAgent).where(CustomAgent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            await websocket.close(code=1008, reason="Agent not found")
            return
        
        # Check access permissions
        if agent.visibility == "private" and str(agent.user_id) != str(user.id):
            await websocket.close(code=1008, reason="Access denied")
            return
        
        # Accept connection
        await manager.connect(websocket, connection_id)
        
        # Send connection success
        await manager.send_json(connection_id, {
            "type": "connected",
            "agent_id": agent_id,
            "agent_name": agent.name
        })
        
        # Message loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") != "message":
                continue
            
            user_message = message_data.get("content", "")
            conversation_id = message_data.get("conversation_id")
            project_id = message_data.get("project_id")
            
            # Send start signal
            await manager.send_json(connection_id, {
                "type": "start"
            })
            
            try:
                # Stream agent response
                async for chunk in run_custom_agent_streaming(
                    db=db,
                    agent_id=UUID(agent_id),
                    user_id=user.id,
                    input_text=user_message,
                    project_id=UUID(project_id) if project_id else None,
                    conversation_id=UUID(conversation_id) if conversation_id else None,
                ):
                    # Send chunk
                    await manager.send_json(connection_id, {
                        "type": "stream",
                        "content": chunk
                    })
                
                # Send end signal
                await manager.send_json(connection_id, {
                    "type": "end"
                })
                
            except Exception as e:
                logger.error(f"Error in agent execution: {e}")
                await manager.send_json(connection_id, {
                    "type": "error",
                    "error": str(e)
                })
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"Client disconnected: {connection_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection_id)
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
