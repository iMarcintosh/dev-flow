"""
Notebook Tool for Custom Agents

Allows agents to search the user's personal notebook (notes) via ChromaDB.
"""
from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from app.services.knowledge_base import knowledge_base_service


class NotebookSearchInput(BaseModel):
    query: str = Field(description="Search query to find relevant notes and snippets in the user's notebook")


class NotebookTool(BaseTool):
    """Tool for searching the user's personal notebook."""

    name: str = "search_notebook"
    description: str = (
        "Search the user's personal developer notebook for notes, code snippets, and documentation. "
        "Use this when the user references their notes, asks about something they've documented, "
        "or wants to find a saved code snippet. Returns the most relevant note content."
    )
    args_schema: Type[BaseModel] = NotebookSearchInput
    user_id: str = ""

    def _run(self, query: str) -> str:
        try:
            collection_name = f"notebook_{self.user_id.replace('-', '_')}"
            results = knowledge_base_service.search_knowledge_base(
                agent_id=collection_name,
                query=query,
                n_results=5,
            )
            if not results:
                return "No relevant notes found in the notebook."

            output = "**Notebook Search Results:**\n\n"
            for i, result in enumerate(results, 1):
                note_title = result['metadata'].get('note_title', 'Untitled')
                text = result['text'][:600]
                distance = result.get('distance', 0)
                output += f"**Note {i}: {note_title}** (relevance: {1 - distance:.2f}):\n{text}\n\n"
            return output
        except Exception as e:
            return f"Error searching notebook: {str(e)}"

    async def _arun(self, query: str) -> str:
        return self._run(query)
