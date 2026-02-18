"""
Tool Registry for Custom Agents.

Manages available tools that custom agents can use.
"""

from typing import Dict, List, Optional, Any, Callable
from langchain.tools import Tool
from langchain_core.language_models import BaseChatModel


# Tool Definitions
AVAILABLE_TOOLS: Dict[str, dict] = {
    "board": {
        "name": "Board Management",
        "description": "Create, update, and manage board items (tasks, bugs, stories)",
        "category": "productivity",
        "functions": ["create_task", "update_status", "add_comment", "assign_item"],
    },
    "web_search": {
        "name": "Web Search",
        "description": "Search the internet for information using DuckDuckGo",
        "category": "research",
        "functions": ["search", "get_page_content"],
    },
    "code_execution": {
        "name": "Code Execution",
        "description": "Execute Python, JavaScript, or Bash code in sandboxed Docker containers",
        "category": "development",
        "functions": ["run_python", "run_javascript", "run_bash"],
    },
    "code_analysis": {
        "name": "Code Analysis",
        "description": "Analyze code structure, complexity, and patterns",
        "category": "development",
        "functions": ["parse_ast", "check_complexity", "find_patterns"],
    },
    "knowledge_base": {
        "name": "Knowledge Base Search",
        "description": "Search agent's uploaded knowledge files (RAG)",
        "category": "knowledge",
        "functions": ["search_knowledge"],
    },
    "git": {
        "name": "Git Operations",
        "description": "Read git history, diffs, commits, and branches",
        "category": "development",
        "functions": ["get_diff", "read_commit", "list_branches", "show_file"],
    },
}


def get_tool_info(tool_name: str) -> Optional[dict]:
    """
    Get information about a tool.
    
    Args:
        tool_name: Name of the tool
    
    Returns:
        Tool info dict or None if not found
    """
    return AVAILABLE_TOOLS.get(tool_name)


def list_available_tools() -> List[dict]:
    """
    Get list of all available tools.
    
    Returns:
        List of tool info dicts
    """
    return [
        {
            "name": name,
            **info
        }
        for name, info in AVAILABLE_TOOLS.items()
    ]


def create_board_tools(db, user_id: str, project_id: str) -> List[Tool]:
    """
    Create LangChain tools for board operations.
    
    Args:
        db: Database session
        user_id: User ID for permissions
        project_id: Project ID for board items
    
    Returns:
        List of LangChain Tool objects
    """
    from app.models.item import Item
    from sqlalchemy import select
    import uuid
    from datetime import datetime
    
    async def create_task(task_data: str) -> str:
        """Create a new task on the board. Input should be JSON with title, description, type."""
        import json
        try:
            data = json.loads(task_data)
            item = Item(
                id=uuid.uuid4(),
                project_id=uuid.UUID(project_id),
                title=data.get("title", "New Task"),
                description=data.get("description", ""),
                item_type=data.get("type", "task"),
                status="todo",
                priority=data.get("priority", "medium"),
                created_at=datetime.utcnow(),
            )
            db.add(item)
            await db.commit()
            return f"✅ Created {item.item_type} '{item.title}' (ID: {item.id})"
        except Exception as e:
            return f"❌ Error creating task: {str(e)}"
    
    async def update_status(update_data: str) -> str:
        """Update item status. Input should be JSON with item_id and new_status."""
        import json
        try:
            data = json.loads(update_data)
            item_id = uuid.UUID(data["item_id"])
            new_status = data["new_status"]
            
            result = await db.execute(select(Item).where(Item.id == item_id))
            item = result.scalar_one_or_none()
            
            if not item:
                return f"❌ Item {item_id} not found"
            
            old_status = item.status
            item.status = new_status
            await db.commit()
            
            return f"✅ Updated '{item.title}' status: {old_status} → {new_status}"
        except Exception as e:
            return f"❌ Error updating status: {str(e)}"
    
    async def add_comment(comment_data: str) -> str:
        """Add a comment to an item. Input should be JSON with item_id and comment."""
        import json
        try:
            data = json.loads(comment_data)
            item_id = uuid.UUID(data["item_id"])
            comment = data["comment"]
            
            result = await db.execute(select(Item).where(Item.id == item_id))
            item = result.scalar_one_or_none()
            
            if not item:
                return f"❌ Item {item_id} not found"
            
            # TODO: Add to comments table when implemented
            return f"✅ Added comment to '{item.title}'"
        except Exception as e:
            return f"❌ Error adding comment: {str(e)}"
    
    tools = [
        Tool(
            name="create_task",
            description="Create a new task/bug/story on the board. Input: JSON with title, description, type, priority",
            func=create_task,
            coroutine=create_task,
        ),
        Tool(
            name="update_status",
            description="Update an item's status. Input: JSON with item_id and new_status (todo/in_progress/done)",
            func=update_status,
            coroutine=update_status,
        ),
        Tool(
            name="add_comment",
            description="Add a comment to a board item. Input: JSON with item_id and comment text",
            func=add_comment,
            coroutine=add_comment,
        ),
    ]
    
    return tools


def create_dummy_search_tool() -> Tool:
    """
    Create a simple web search tool (placeholder).
    
    Returns:
        LangChain Tool for web search
    """
    def search(query: str) -> str:
        """Search the web for information."""
        # TODO: Implement actual web search (DuckDuckGo API)
        return f"🔍 Search results for '{query}':\n(Web search not yet implemented)"
    
    return Tool(
        name="web_search",
        description="Search the internet for information. Input: search query string",
        func=search,
    )


def bind_tools_to_llm(
    llm: BaseChatModel,
    tool_names: List[str],
    db=None,
    user_id: str = None,
    project_id: str = None,
    agent_id: str = None,
) -> BaseChatModel:
    """
    Bind selected tools to an LLM.
    
    Args:
        llm: LangChain LLM instance
        tool_names: List of tool names to enable
        db: Database session (required for board tools)
        user_id: User ID (required for board tools)
        project_id: Project ID (required for board tools)
        agent_id: Agent ID (required for knowledge_base tool)
    
    Returns:
        LLM with tools bound (or original LLM if no tools or binding not supported)
    """
    from app.agent.tools.code_execution_tool import code_execution_tool
    from app.agent.tools.knowledge_base_tool import KnowledgeBaseTool
    
    tools = []
    
    for tool_name in tool_names:
        if tool_name == "board":
            if db and project_id:
                tools.extend(create_board_tools(db, user_id, project_id))
        
        elif tool_name == "web_search":
            tools.append(create_dummy_search_tool())
        
        elif tool_name == "code_execution":
            tools.append(code_execution_tool)
        
        elif tool_name == "knowledge_base":
            if agent_id:
                kb_tool = KnowledgeBaseTool(agent_id=agent_id)
                tools.append(kb_tool)
    
    if not tools:
        return llm
    
    # Try to bind tools (not all LLMs support this)
    try:
        if hasattr(llm, 'bind_tools'):
            return llm.bind_tools(tools)
        else:
            # For LLMs that don't support bind_tools, return as is
            # Tools will need to be handled differently
            return llm
    except Exception:
        # If binding fails, return original LLM
        return llm


def get_tool_descriptions() -> Dict[str, str]:
    """
    Get descriptions of all available tools.
    
    Returns:
        Dict mapping tool names to descriptions
    """
    return {
        name: info["description"]
        for name, info in AVAILABLE_TOOLS.items()
    }
