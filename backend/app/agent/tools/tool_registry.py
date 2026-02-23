"""
Tool Registry for Custom Agents.

Manages available tools that custom agents can use.
"""

from typing import Dict, List, Optional, Any, Callable, Type
from pydantic import BaseModel, Field
from langchain_core.tools import Tool, BaseTool, StructuredTool
from langchain_core.language_models import BaseChatModel


# Tool Definitions
AVAILABLE_TOOLS: Dict[str, dict] = {
    "board": {
        "name": "Board Management",
        "description": "Create, update, and manage board items (tasks, bugs, stories)",
        "category": "productivity",
        "functions": ["create_task", "list_items", "update_status", "add_comment"],
    },
    "web_search": {
        "name": "Web Search & URL Reading",
        "description": "Search the web with DuckDuckGo and read content from URLs",
        "category": "research",
        "functions": ["web_search", "read_url", "read_url_jina"],
    },
    "weather": {
        "name": "Weather Information",
        "description": "Get current weather for any location using OpenWeatherMap",
        "category": "information",
        "functions": ["get_weather"],
    },
    "code_execution": {
        "name": "Code Execution",
        "description": "Execute Python, JavaScript, or Bash code in sandboxed Docker containers",
        "category": "development",
        "functions": ["run_python", "run_javascript", "run_bash"],
    },
    "knowledge_base": {
        "name": "Knowledge Base Search",
        "description": "Search agent's uploaded knowledge files (RAG)",
        "category": "knowledge",
        "functions": ["search_knowledge"],
    },
    "mcp": {
        "name": "MCP Servers",
        "description": "Access tools from Model Context Protocol servers (filesystem, GitHub, etc.)",
        "category": "integration",
        "functions": ["mcp_tools"],
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


class CreateTaskInput(BaseModel):
    title: str = Field(description="Task title")
    description: str = Field(default="", description="Task description")
    type: str = Field(default="task", description="Item type: epic, story, bug, task, spike")
    priority: str = Field(default="medium", description="Priority: low, medium, high, urgent")


class ListItemsInput(BaseModel):
    status: str = Field(default="", description="Optional status filter: backlog, in_progress, review, done. Leave empty for all items.")


class UpdateStatusInput(BaseModel):
    item_id: str = Field(description="UUID of the item to update")
    new_status: str = Field(description="New status: backlog, in_progress, review, done")


class AddCommentInput(BaseModel):
    item_id: str = Field(description="UUID of the item to comment on")
    comment: str = Field(description="Comment text to add")


def create_board_tools(db, user_id: str, project_id: str) -> List[StructuredTool]:
    """
    Create LangChain tools for board operations.

    Args:
        db: Database session
        user_id: User ID for permissions
        project_id: Project ID for board items

    Returns:
        List of LangChain StructuredTool objects
    """
    from app.models.item import Item
    from sqlalchemy import select
    import uuid

    async def create_task(title: str, description: str = "", type: str = "task", priority: str = "medium") -> str:
        try:
            item = Item(
                project_id=uuid.UUID(project_id),
                title=title,
                description=description,
                type=type,
                status="backlog",
                priority=priority,
                created_by=uuid.UUID(user_id),
            )
            db.add(item)
            await db.commit()
            return f"✅ Created {item.type} '{item.title}' (ID: {item.id})"
        except Exception as e:
            return f"❌ Error creating task: {str(e)}"

    async def list_items(status: str = "") -> str:
        try:
            query = select(Item).where(Item.project_id == uuid.UUID(project_id))
            if status:
                query = query.where(Item.status == status)
            query = query.order_by(Item.created_at.desc()).limit(50)
            result = await db.execute(query)
            items = result.scalars().all()
            if not items:
                return "📋 No items found."
            lines = [f"📋 Found {len(items)} items:"]
            for it in items:
                lines.append(f"- [{it.status}] {it.type}: {it.title} (ID: {it.id})")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Error listing items: {str(e)}"

    async def update_status(item_id: str, new_status: str) -> str:
        try:
            result = await db.execute(select(Item).where(Item.id == uuid.UUID(item_id)))
            item = result.scalar_one_or_none()
            if not item:
                return f"❌ Item {item_id} not found"
            old_status = item.status
            item.status = new_status
            await db.commit()
            return f"✅ Updated '{item.title}' status: {old_status} → {new_status}"
        except Exception as e:
            return f"❌ Error updating status: {str(e)}"

    async def add_comment(item_id: str, comment: str) -> str:
        try:
            result = await db.execute(select(Item).where(Item.id == uuid.UUID(item_id)))
            item = result.scalar_one_or_none()
            if not item:
                return f"❌ Item {item_id} not found"
            # TODO: Add to comments table when implemented
            return f"✅ Added comment to '{item.title}'"
        except Exception as e:
            return f"❌ Error adding comment: {str(e)}"

    tools = [
        StructuredTool.from_function(
            coroutine=create_task,
            name="create_task",
            description=(
                "ALWAYS use this tool when the user asks to create, add, or write a new item on the board. "
                "Call this when the user says 'erstelle', 'create', 'add', 'anlegen', 'new task', 'new epic', etc. "
                "Use type='epic' for epics, 'story' for user stories, 'bug' for bugs, 'task' for tasks, 'spike' for spikes."
            ),
            args_schema=CreateTaskInput,
        ),
        StructuredTool.from_function(
            coroutine=list_items,
            name="list_items",
            description=(
                "List board items. Use this to answer questions about tasks, bugs, stories, or the backlog. "
                "Call this when asked 'what is in the backlog', 'show me all tasks', 'what is in progress', etc. "
                "Pass status to filter (backlog, in_progress, review, done), or leave empty for all items."
            ),
            args_schema=ListItemsInput,
        ),
        StructuredTool.from_function(
            coroutine=update_status,
            name="update_status",
            description="Update a board item's status. Valid statuses: backlog, in_progress, review, done.",
            args_schema=UpdateStatusInput,
        ),
        StructuredTool.from_function(
            coroutine=add_comment,
            name="add_comment",
            description="Add a comment to a board item.",
            args_schema=AddCommentInput,
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


def get_tools_list(
    tool_names: List[str],
    db=None,
    user_id: str = None,
    project_id: str = None,
    agent_id: str = None,
) -> List[BaseTool]:
    """
    Get list of tools based on tool names.
    
    Returns a list of tool instances that can be used with bind_tools() or AgentExecutor.
    """
    from app.agent.tools.code_execution_tool import code_execution_tool
    from app.agent.tools.knowledge_base_tool import KnowledgeBaseTool
    from app.agent.tools.web_tools import web_search, read_url, read_url_jina, get_weather
    
    import logging
    logger = logging.getLogger(__name__)
    
    tools = []
    
    for tool_name in tool_names:
        if tool_name == "board":
            if db and project_id:
                tools.extend(create_board_tools(db, user_id, project_id))
        
        elif tool_name == "web_search":
            tools.append(web_search)
            tools.append(read_url)
            tools.append(read_url_jina)
            logger.info(f"✅ Added web_search, read_url, read_url_jina tools")
        
        elif tool_name == "weather":
            tools.append(get_weather)
            logger.info(f"✅ Added get_weather tool")
        
        elif tool_name == "code_execution":
            tools.append(code_execution_tool)
            logger.info(f"✅ Added code_execution tool")
        
        elif tool_name == "knowledge_base":
            if agent_id:
                kb_tool = KnowledgeBaseTool(agent_id=agent_id)
                tools.append(kb_tool)
                logger.info(f"✅ Added knowledge_base tool for agent {agent_id}")
            else:
                logger.warning(f"⚠️ knowledge_base tool requested but no agent_id provided")
    
    logger.info(f"📦 Prepared {len(tools)} tools: {[t.name for t in tools]}")
    return tools


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
    from app.agent.tools.web_tools import web_search, read_url, read_url_jina, get_weather
    
    import logging
    logger = logging.getLogger(__name__)
    
    tools = []
    
    for tool_name in tool_names:
        if tool_name == "board":
            if db and project_id:
                tools.extend(create_board_tools(db, user_id, project_id))
        
        elif tool_name == "web_search":
            tools.append(web_search)
            tools.append(read_url)
            tools.append(read_url_jina)
        
        elif tool_name == "weather":
            tools.append(get_weather)
        
        elif tool_name == "code_execution":
            tools.append(code_execution_tool)
            logger.info(f"✅ Added code_execution tool")
        
        elif tool_name == "knowledge_base":
            if agent_id:
                kb_tool = KnowledgeBaseTool(agent_id=agent_id)
                tools.append(kb_tool)
                logger.info(f"✅ Added knowledge_base tool for agent {agent_id}")
            else:
                logger.warning(f"⚠️ knowledge_base tool requested but no agent_id provided")
    
    if not tools:
        logger.warning("⚠️ No tools to bind!")
        return llm
    
    logger.info(f"🔧 Attempting to bind {len(tools)} tools: {[t.name for t in tools]}")
    
    # Try to bind tools (not all LLMs support this)
    try:
        if hasattr(llm, 'bind_tools'):
            bound_llm = llm.bind_tools(tools)
            logger.info(f"✅ Successfully bound tools to LLM")
            return bound_llm
        else:
            logger.warning(f"⚠️ LLM does not support bind_tools method")
            return llm
    except Exception as e:
        logger.error(f"❌ Error binding tools: {e}")
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
