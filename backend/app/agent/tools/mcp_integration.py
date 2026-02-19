"""MCP (Model Context Protocol) Integration using langchain-mcp-adapters."""

import logging
from typing import List, Dict, Any
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


async def get_mcp_tools(server_configs: List[Dict[str, Any]]) -> List[BaseTool]:
    """
    Load tools from MCP servers using langchain-mcp-adapters.

    Args:
        server_configs: List of MCP server configs, each with:
            - name: str
            - command: str  (e.g. "npx" or "uvx")
            - args: list[str]
            - env: dict[str, str] (optional)

    Returns:
        List of LangChain BaseTool instances ready for bind_tools()
    """
    from langchain_mcp_adapters.client import MultiServerMCPClient

    if not server_configs:
        return []

    # Build MultiServerMCPClient config
    client_config = {}
    for server in server_configs:
        name = server.get("name")
        command = server.get("command")
        args = server.get("args", [])
        if not name or not command:
            logger.warning(f"MCP server config missing name or command, skipping: {server}")
            continue
        client_config[name] = {
            "transport": "stdio",
            "command": command,
            "args": args,
        }
        if server.get("env"):
            client_config[name]["env"] = server["env"]

    if not client_config:
        return []

    try:
        client = MultiServerMCPClient(client_config)
        tools = await client.get_tools()
        logger.info(f"✅ Loaded {len(tools)} MCP tools from {list(client_config.keys())}")
        return tools
    except Exception as e:
        logger.error(f"❌ Failed to load MCP tools: {e}")
        return []


# Example MCP server configs for reference
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
