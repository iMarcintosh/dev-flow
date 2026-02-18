"""
Knowledge Base API Endpoints

Handles file uploads and management for agent knowledge bases.
"""
import os
import tempfile
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel

from app.auth import get_current_user
from app.models.user import User
from app.models.custom_agent import CustomAgent
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.knowledge_base import knowledge_base_service

router = APIRouter(prefix="/api/knowledge-base", tags=["knowledge_base"])


class FileUploadResponse(BaseModel):
    success: bool
    file_id: str = None
    filename: str = None
    chunks_added: int = 0
    error: str = None


class FileListResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str


class SearchRequest(BaseModel):
    query: str
    n_results: int = 5


class SearchResult(BaseModel):
    text: str
    metadata: dict
    distance: float = None


@router.post("/{agent_id}/upload", response_model=FileUploadResponse)
async def upload_file(
    agent_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload file to agent's knowledge base
    
    Supported file types: PDF, TXT, MD, PY, JS, TS, etc.
    """
    # Verify agent belongs to user
    result = await db.execute(
        select(CustomAgent).where(
            CustomAgent.id == agent_id,
            CustomAgent.user_id == current_user.id
        )
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.txt', '.md', '.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.yaml', '.yml'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_path = tmp_file.name
        shutil.copyfileobj(file.file, tmp_file)
    
    try:
        # Add to knowledge base
        result = await knowledge_base_service.add_file_to_knowledge_base(
            agent_id=agent_id,
            file_path=tmp_path,
            filename=file.filename,
            file_type=file.content_type or file_ext
        )
        
        return FileUploadResponse(**result)
        
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/{agent_id}/files", response_model=List[FileListResponse])
async def list_files(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all files in agent's knowledge base"""
    # Verify agent belongs to user
    result = await db.execute(
        select(CustomAgent).where(
            CustomAgent.id == agent_id,
            CustomAgent.user_id == current_user.id
        )
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    files = knowledge_base_service.list_files(agent_id)
    return [FileListResponse(**f) for f in files]


@router.delete("/{agent_id}/files/{file_id}")
async def delete_file(
    agent_id: str,
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete file from agent's knowledge base"""
    # Verify agent belongs to user
    result = await db.execute(
        select(CustomAgent).where(
            CustomAgent.id == agent_id,
            CustomAgent.user_id == current_user.id
        )
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    success = knowledge_base_service.delete_file(agent_id, file_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"success": True}


@router.post("/{agent_id}/search", response_model=List[SearchResult])
async def search_knowledge_base(
    agent_id: str,
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search agent's knowledge base"""
    # Verify agent belongs to user
    result = await db.execute(
        select(CustomAgent).where(
            CustomAgent.id == agent_id,
            CustomAgent.user_id == current_user.id
        )
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    results = knowledge_base_service.search_knowledge_base(
        agent_id=agent_id,
        query=request.query,
        n_results=request.n_results
    )
    
    return [SearchResult(**r) for r in results]
