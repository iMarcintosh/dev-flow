from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.item import ItemType, ItemStatus, ItemPriority
import uuid


class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    type: ItemType = ItemType.TASK
    priority: ItemPriority = ItemPriority.MEDIUM
    tags: List[str] = []


class ItemCreate(ItemBase):
    project_id: uuid.UUID
    assignee_id: Optional[uuid.UUID] = None
    parent_id: Optional[uuid.UUID] = None
    status: ItemStatus = ItemStatus.BACKLOG


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    type: Optional[ItemType] = None
    status: Optional[ItemStatus] = None
    priority: Optional[ItemPriority] = None
    assignee_id: Optional[uuid.UUID] = None
    parent_id: Optional[uuid.UUID] = None
    tags: Optional[List[str]] = None
    position: Optional[float] = None


class ItemResponse(ItemBase):
    id: uuid.UUID
    project_id: uuid.UUID
    status: ItemStatus
    assignee_id: Optional[uuid.UUID] = None
    parent_id: Optional[uuid.UUID] = None
    position: float
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True
