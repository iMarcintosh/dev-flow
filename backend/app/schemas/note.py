from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class NoteCreate(BaseModel):
    title: str = Field(default="Untitled", max_length=500)
    content: str = Field(default="")
    tags: List[str] = Field(default_factory=list)
    is_pinned: bool = False
    project_id: Optional[str] = None


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=500)
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None
    project_id: Optional[str] = None


class NoteResponse(BaseModel):
    id: str
    user_id: str
    project_id: Optional[str] = None
    title: str
    content: str
    tags: List[str]
    is_pinned: bool
    chroma_indexed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, note) -> "NoteResponse":
        return cls(
            id=str(note.id),
            user_id=str(note.user_id),
            project_id=str(note.project_id) if note.project_id else None,
            title=note.title,
            content=note.content,
            tags=note.tags or [],
            is_pinned=note.is_pinned,
            chroma_indexed=note.chroma_indexed,
            created_at=note.created_at,
            updated_at=note.updated_at,
        )


class NoteListResponse(BaseModel):
    notes: List[NoteResponse]
    total: int


class NoteSearchResult(BaseModel):
    text: str
    metadata: dict
    distance: Optional[float] = None
    note_id: Optional[str] = None
    note_title: Optional[str] = None
