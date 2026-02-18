from typing import Dict, List
from fastapi import WebSocket
import json


class ConnectionManager:
    """
    Manages WebSocket connections for real-time agent updates.
    
    Clients can subscribe to specific agent runs and receive
    live log updates and status changes.
    """
    
    def __init__(self):
        # Map of run_id -> list of connected WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, run_id: str):
        """Accept a WebSocket connection for a specific run."""
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = []
        self.active_connections[run_id].append(websocket)
        print(f"✓ WebSocket connected for run {run_id}")
    
    def disconnect(self, websocket: WebSocket, run_id: str):
        """Remove a WebSocket connection."""
        if run_id in self.active_connections:
            if websocket in self.active_connections[run_id]:
                self.active_connections[run_id].remove(websocket)
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]
        print(f"✓ WebSocket disconnected from run {run_id}")
    
    async def broadcast_to_run(self, run_id: str, message: dict):
        """Send a message to all clients watching a specific run."""
        if run_id not in self.active_connections:
            return
        
        # Remove disconnected clients
        disconnected = []
        for websocket in self.active_connections[run_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws, run_id)


# Global singleton
manager = ConnectionManager()
