"""
MCP (Model Context Protocol) Integration for Custom Agents.

Allows custom agents to use MCP servers as tools.
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool, tool
import asyncio
import json

logger = logging.getLogger(__name__)


class MCPToolWrapper(BaseTool):
    """Wrapper to convert MCP tool to LangChain tool."""
    
    name: str
    description: str
    mcp_server_name: str
    mcp_tool_name: str
    _client: Any = None  # MCP client instance
    
    def __init__(self, name: str, description: str, mcp_server_name: str, mcp_tool_name: str, client: Any):
        super().__init__()
        self.name = name
        self.description = description
        self.mcp_server_name = mcp_server_name
        self.mcp_tool_name = mcp_tool_name
        self._client = client
    
    def _run(self, **kwargs) -> str:
        """Execute MCP tool synchronously."""
        try:
            # Run async method in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._arun(**kwargs))
                return result
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error executing MCP tool {self.name}: {e}")
            return f"Error: {str(e)}"
    
    async def _arun(self, **kwargs) -> str:
        """Execute MCP tool asynchronously."""
        try:
            # Call MCP server tool
            result = await self._client.call_tool(
                server_name=self.mcp_server_name,
                tool_name=self.mcp_tool_name,
                arguments=kwargs
            )
            
            # Format result
            if isinstance(result, dict):
                return json.dumps(result, indent=2)
            return str(result)
            
        except Exception as e:
            logger.error(f"Error calling MCP tool {self.name}: {e}")
            return f"Error: {str(e)}"


class MCPClient:
    """
    Simple MCP client for custom agents.
    
    In production, this would use the official MCP SDK.
    For now, this is a placeholder implementation.
    """
    
    def __init__(self):
        self.servers: Dict[str, Any] = {}
        logger.info("MCP Client initialized")
    
    async def add_server(self, name: str, config: Dict[str, Any]) -> None:
        """
        Add an MCP server.
        
        Args:
            name: Server name
            config: Server configuration (command, args, env)
        """
        logger.info(f"Adding MCP server: {name}")
        # TODO: Actually connect to MCP server
        self.servers[name] = {
            "name": name,
            "config": config,
            "connected": False,
            "tools": []
        }
    
    async def get_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """
        Get available tools from an MCP server.
        
        Args:
            server_name: Name of the MCP server
            
        Returns:
            List of tool definitions
        """
        if server_name not in self.servers:
            logger.warning(f"MCP server {server_name} not found")
            return []
        
        # TODO: Actually fetch tools from MCP server
        # For now, return mock tools
        return [
            {
                "name": f"{server_name}_example_tool",
                "description": f"Example tool from {server_name} MCP server",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Query parameter"}
                    }
                }
            }
        ]
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on an MCP server.
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if server_name not in self.servers:
            raise ValueError(f"MCP server {server_name} not found")
        
        logger.info(f"Calling MCP tool: {server_name}.{tool_name} with {arguments}")
        
        # TODO: Actually call MCP server tool
        # For now, return mock result
        return {
            "status": "success",
            "message": f"Mock result from {server_name}.{tool_name}",
            "arguments": arguments
        }
    
    async def close(self) -> None:
        """Close all MCP server connections."""
        logger.info("Closing MCP client connections")
        self.servers.clear()


async def get_mcp_tools(server_configs: List[Dict[str, Any]]) -> List[BaseTool]:
    """
    Convert MCP server tools to LangChain tools.
    
    Args:
        server_configs: List of MCP server configurations
        
    Returns:
        List of LangChain BaseTool instances
    """
    client = MCPClient()
    tools = []
    
    try:
        # Add all servers
        for config in server_configs:
            server_name = config.get("name")
            if not server_name:
                logger.warning("MCP server config missing name, skipping")
                continue
            
            await client.add_server(server_name, config)
            
            # Get tools from this server
            mcp_tools = await client.get_tools(server_name)
            
            # Convert to LangChain tools
            for mcp_tool in mcp_tools:
                tool_name = mcp_tool.get("name", "unknown")
                description = mcp_tool.get("description", "No description")
                
                wrapped_tool = MCPToolWrapper(
                    name=tool_name,
                    description=description,
                    mcp_server_name=server_name,
                    mcp_tool_name=tool_name,
                    client=client
                )
                
                tools.append(wrapped_tool)
                logger.info(f"✅ Added MCP tool: {tool_name} from {server_name}")
        
        return tools
        
    except Exception as e:
        logger.error(f"Error loading MCP tools: {e}")
        return []


# Example MCP server configs for testing
EXAMPLE_MCP_SERVERS = [
    {
        "name": "filesystem",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        "env": {}
    },
    {
        "name": "github",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
            "GITHUB_TOKEN": ""  # Set from config
        }
    }
]
