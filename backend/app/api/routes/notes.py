"""
Notes API — Developer Notebook endpoints.
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String, cast, any_

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse
import uuid

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.post("/", response_model=NoteResponse)
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = Note(
        user_id=current_user.id,
        project_id=uuid.UUID(note_data.project_id) if note_data.project_id else None,
        title=note_data.title,
        content=note_data.content,
        tags=note_data.tags,
        is_pinned=note_data.is_pinned,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return NoteResponse.from_orm_model(note)


@router.get("/tags/all", response_model=List[str])
async def get_all_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all distinct tags used by the current user."""
    result = await db.execute(
        select(Note.tags).where(Note.user_id == current_user.id)
    )
    all_tags_lists = result.scalars().all()
    tags = set()
    for tag_list in all_tags_lists:
        if tag_list:
            tags.update(tag_list)
    return sorted(tags)


@router.get("/", response_model=NoteListResponse)
async def list_notes(
    tag: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    pinned_only: bool = Query(False),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Note).where(Note.user_id == current_user.id)

    if pinned_only:
        query = query.where(Note.is_pinned == True)
    if project_id:
        query = query.where(Note.project_id == uuid.UUID(project_id))
    if tag:
        query = query.where(Note.tags.any(tag))
    if search:
        query = query.where(
            or_(
                Note.title.ilike(f"%{search}%"),
                Note.content.ilike(f"%{search}%"),
            )
        )

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Sort: pinned first, then updated_at DESC
    query = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    notes = result.scalars().all()

    return NoteListResponse(
        notes=[NoteResponse.from_orm_model(n) for n in notes],
        total=total,
    )


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Note).where(Note.id == uuid.UUID(note_id), Note.user_id == current_user.id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse.from_orm_model(note)


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Note).where(Note.id == uuid.UUID(note_id), Note.user_id == current_user.id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    update_data = note_data.model_dump(exclude_unset=True)
    content_changed = "title" in update_data or "content" in update_data or "tags" in update_data

    for field, value in update_data.items():
        if field == "project_id":
            setattr(note, field, uuid.UUID(value) if value else None)
        else:
            setattr(note, field, value)

    if content_changed:
        note.chroma_indexed = False

    await db.commit()
    await db.refresh(note)
    return NoteResponse.from_orm_model(note)


@router.delete("/{note_id}")
async def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Note).where(Note.id == uuid.UUID(note_id), Note.user_id == current_user.id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Delete from ChromaDB
    try:
        from app.services.knowledge_base import knowledge_base_service
        user_id_clean = str(current_user.id).replace("-", "_")
        file_id = f"note_{note_id.replace('-', '_')}"
        collection_name = f"notebook_{user_id_clean}"
        knowledge_base_service.delete_file(collection_name, file_id)
    except Exception:
        pass  # Don't fail if ChromaDB cleanup fails

    await db.delete(note)
    await db.commit()
    return {"success": True}
