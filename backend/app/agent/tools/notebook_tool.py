"""
Notebook Tool for Custom Agents

Allows agents to list, search, or create notes in the user's personal notebook.
"""
from typing import Any, List, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from app.services.knowledge_base import knowledge_base_service


class NotebookSearchInput(BaseModel):
    query: str = Field(
        default="",
        description=(
            "Search query to find specific notes. "
            "Leave empty or use 'list all' to show all notes in the notebook."
        )
    )


class NotebookTool(BaseTool):
    """Tool for listing and searching the user's personal notebook."""

    name: str = "search_notebook"
    description: str = (
        "Access the user's personal notebook — list all notes or search for specific ones. "
        "Use with empty query (or 'list all') when the user wants to see all their notes. "
        "Use with a specific query when searching for a topic, code snippet, or keyword. "
        "Always use this tool when the user asks about their notes, notebook, or saved content."
    )
    args_schema: Type[BaseModel] = NotebookSearchInput
    user_id: str = ""

    def _run(self, query: str = "") -> str:
        try:
            list_keywords = {"", "list", "all", "show", "alle", "zeige", "list all"}
            is_list_mode = query.strip().lower() in list_keywords

            if is_list_mode:
                return self._list_all_notes()
            else:
                return self._search_notes(query)
        except Exception as e:
            return f"Error accessing notebook: {str(e)}"

    def _list_all_notes(self) -> str:
        """List all notes from ChromaDB (no vector search)."""
        collection = knowledge_base_service.get_or_create_notebook_collection(self.user_id)
        if collection.count() == 0:
            return "The notebook is empty — no notes have been saved yet."

        all_data = collection.get()
        # Deduplicate by note_id, keep only first chunk per note
        seen_notes = {}
        if all_data['ids'] and all_data['metadatas']:
            for i, meta in enumerate(all_data['metadatas']):
                note_id = meta.get('note_id')
                chunk_idx = meta.get('chunk_index', 0)
                if note_id and note_id not in seen_notes and chunk_idx == 0:
                    seen_notes[note_id] = {
                        'title': meta.get('note_title', 'Untitled'),
                        'text': all_data['documents'][i][:400] if all_data['documents'] else ''
                    }

        if not seen_notes:
            return "The notebook is empty — no notes have been saved yet."

        output = f"**Notebook — {len(seen_notes)} note(s):**\n\n"
        for note in seen_notes.values():
            output += f"**{note['title']}**:\n{note['text']}\n\n"
        return output

    def _search_notes(self, query: str) -> str:
        """Vector search for relevant notes."""
        results = knowledge_base_service.search_notebook(
            user_id=self.user_id,
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
            output += f"**Note {i}: {note_title}** (relevance: {1 - distance/2:.2f}):\n{text}\n\n"
        return output

    async def _arun(self, query: str = "") -> str:
        return self._run(query)


class NotebookCreateInput(BaseModel):
    title: str = Field(description="Title of the note to create")
    content: str = Field(description="Content/body of the note")
    tags: List[str] = Field(default=[], description="Optional tags for the note")


class NotebookCreateTool(BaseTool):
    """Tool for creating new notes in the user's personal notebook."""

    name: str = "create_note"
    description: str = (
        "Create a new note in the user's personal notebook. "
        "Use when the user asks to save, write, or create a note. "
        "Always use this tool when the user says 'save this', 'create a note', "
        "'write this down', 'erstelle eine Notiz', or similar."
    )
    args_schema: Type[BaseModel] = NotebookCreateInput
    user_id: str = ""
    db: Any = Field(default=None, exclude=True)

    def _run(self, title: str, content: str, tags: List[str] = []) -> str:
        raise NotImplementedError("Use async version")

    async def _arun(self, title: str, content: str, tags: List[str] = []) -> str:
        try:
            from app.models.note import Note
            import uuid
            note = Note(
                user_id=uuid.UUID(self.user_id),
                title=title,
                content=content,
                tags=tags,
            )
            self.db.add(note)
            await self.db.commit()
            await self.db.refresh(note)
            from app.agent.memory.note_indexer import trigger_note_indexing
            trigger_note_indexing(str(note.id))
            return f"Note '{title}' created successfully (ID: {note.id})"
        except Exception as e:
            return f"Error creating note: {str(e)}"
