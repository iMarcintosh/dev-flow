"""
Knowledge Base Tool for Custom Agents

Allows agents to search their knowledge base (uploaded files).
"""
from typing import Type, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from app.services.knowledge_base import knowledge_base_service


class KnowledgeBaseInput(BaseModel):
    """Input schema for knowledge base search"""
    query: str = Field(..., description="Search query to find relevant information in knowledge base")


class KnowledgeBaseTool(BaseTool):
    """Tool for searching agent's knowledge base"""
    
    name: str = "search_knowledge_base"
    description: str = (
        "🔍 Search the agent's knowledge base for relevant information. "
        "Use this when the user asks about specific documents, files, or information "
        "that was uploaded to the agent's knowledge base. "
        "Returns the most relevant text chunks from uploaded files."
    )
    args_schema: Type[BaseModel] = KnowledgeBaseInput
    return_direct: bool = False
    agent_id: str = ""  # Will be set when tool is created
    
    def _run(self, query: str) -> str:
        """Search knowledge base synchronously"""
        try:
            results = knowledge_base_service.search_knowledge_base(
                agent_id=self.agent_id,
                query=query,
                n_results=3
            )
            
            if not results:
                return "❌ No relevant information found in knowledge base."
            
            # Format results
            output = "📚 **Knowledge Base Search Results:**\n\n"
            for i, result in enumerate(results, 1):
                filename = result['metadata'].get('filename', 'Unknown')
                text = result['text'][:500]  # Limit text length
                distance = result.get('distance', 0)
                
                output += f"**Result {i}** (from {filename}, relevance: {1 - distance:.2f}):\n"
                output += f"{text}\n\n"
            
            return output
            
        except Exception as e:
            return f"❌ Error searching knowledge base: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """Search knowledge base asynchronously"""
        # For now, just call sync version
        return self._run(query)
