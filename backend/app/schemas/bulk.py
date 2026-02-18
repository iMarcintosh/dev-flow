from pydantic import BaseModel
from typing import Optional, List
from app.models.item import ItemStatus
import uuid


class BulkReorderRequest(BaseModel):
    items: List[dict]  # [{"id": "...", "position": 1.5}, ...]


class UpdateStatusRequest(BaseModel):
    status: ItemStatus
    position: Optional[float] = None
