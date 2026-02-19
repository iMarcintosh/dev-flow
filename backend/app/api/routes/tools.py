"""API endpoint for available tools."""

from fastapi import APIRouter, Depends
from app.models.user import User
from app.api.routes.auth import get_current_user
from app.agent.tools.tool_registry import AVAILABLE_TOOLS

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("/available")
async def get_available_tools(current_user: User = Depends(get_current_user)):
    """
    Get list of available tools for custom agents.
    
    Returns tools from the tool registry with their metadata.
    """
    # Convert AVAILABLE_TOOLS dict to list format for frontend
    tools_list = []
    
    for tool_id, tool_info in AVAILABLE_TOOLS.items():
        tools_list.append({
            "id": tool_id,
            "name": tool_info["name"],
            "description": tool_info["description"],
            "category": tool_info["category"],
            "functions": tool_info.get("functions", [])
        })
    
    return {
        "success": True,
        "tools": tools_list
    }
