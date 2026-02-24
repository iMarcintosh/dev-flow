from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.item import Item, ItemStatus
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from app.schemas.bulk import UpdateStatusRequest, BulkReorderRequest
from app.api.routes.auth import get_current_user
from typing import List, Optional
import uuid

router = APIRouter()


async def verify_project_access(project_id: uuid.UUID, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_data: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify project access
    await verify_project_access(item_data.project_id, current_user, db)
    
    # Get max position for the status column
    result = await db.execute(
        select(Item).where(
            and_(
                Item.project_id == item_data.project_id,
                Item.status == item_data.status
            )
        ).order_by(Item.position.desc())
    )
    last_item = result.scalars().first()
    next_position = (last_item.position + 1.0) if last_item else 1.0
    
    new_item = Item(
        project_id=item_data.project_id,
        title=item_data.title,
        description=item_data.description,
        acceptance_criteria=item_data.acceptance_criteria,
        type=item_data.type,
        status=item_data.status,
        priority=item_data.priority,
        assignee_id=item_data.assignee_id,
        parent_id=item_data.parent_id,
        tags=item_data.tags,
        position=next_position,
        created_by=current_user.id
    )
    
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    from app.agent.memory.indexer import trigger_item_indexing
    trigger_item_indexing(str(new_item.id))

    return ItemResponse.model_validate(new_item)


@router.get("/", response_model=List[ItemResponse])
async def list_items(
    project_id: Optional[uuid.UUID] = Query(None),
    status: Optional[ItemStatus] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Build query
    query = select(Item)
    conditions = []
    
    if project_id:
        await verify_project_access(project_id, current_user, db)
        conditions.append(Item.project_id == project_id)
    
    if status:
        conditions.append(Item.status == status)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(Item.position.asc())
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return [ItemResponse.model_validate(item) for item in items]


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Verify project access
    await verify_project_access(item.project_id, current_user, db)
    
    return ItemResponse.model_validate(item)


@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: uuid.UUID,
    item_data: ItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Verify project access
    await verify_project_access(item.project_id, current_user, db)
    
    # Update fields
    update_data = item_data.model_dump(exclude_unset=True)
    embedding_relevant_fields = {'title', 'description', 'acceptance_criteria', 'type'}
    content_changed = bool(update_data.keys() & embedding_relevant_fields)
    for field, value in update_data.items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)

    if content_changed:
        from app.agent.memory.indexer import trigger_item_indexing
        trigger_item_indexing(str(item.id))

    return ItemResponse.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Verify project access
    await verify_project_access(item.project_id, current_user, db)
    
    await db.delete(item)
    await db.commit()


@router.patch("/{item_id}/status", response_model=ItemResponse)
async def update_item_status(
    item_id: uuid.UUID,
    status_update: UpdateStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    await verify_project_access(item.project_id, current_user, db)
    
    # Update status
    item.status = status_update.status
    
    # Update position if provided, otherwise set to end of column
    if status_update.position is not None:
        item.position = status_update.position
    else:
        # Get max position in new status column
        result = await db.execute(
            select(Item).where(
                and_(
                    Item.project_id == item.project_id,
                    Item.status == status_update.status
                )
            ).order_by(Item.position.desc())
        )
        last_item = result.scalars().first()
        item.position = (last_item.position + 1.0) if last_item else 1.0
    
    await db.commit()
    await db.refresh(item)
    
    return ItemResponse.model_validate(item)


@router.post("/bulk-reorder", status_code=status.HTTP_200_OK)
async def bulk_reorder_items(
    reorder_data: BulkReorderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify all items exist and user has access
    item_ids = [uuid.UUID(item["id"]) for item in reorder_data.items]
    result = await db.execute(select(Item).where(Item.id.in_(item_ids)))
    items = result.scalars().all()
    
    if len(items) != len(item_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some items not found"
        )
    
    # Verify project access for all items
    project_ids = set(item.project_id for item in items)
    for project_id in project_ids:
        await verify_project_access(project_id, current_user, db)
    
    # Update positions
    for item_data in reorder_data.items:
        await db.execute(
            update(Item)
            .where(Item.id == uuid.UUID(item_data["id"]))
            .values(position=item_data["position"])
        )
    
    await db.commit()
    
    return {"success": True, "updated": len(item_ids)}


# Agent Assignment Endpoints
@router.post("/{item_id}/assign-agent")
async def assign_agent_to_item(
    item_id: uuid.UUID,
    agent_id: uuid.UUID = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Assign a custom agent to a board item."""
    # Get item
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Verify project access
    await verify_project_access(item.project_id, current_user, db)
    
    # Verify agent exists and user has access
    from app.services.custom_agent_service import get_agent_by_id
    agent = await get_agent_by_id(agent_id, current_user.id, db)
    
    # Assign agent
    item.assigned_agent_id = agent_id
    await db.commit()
    await db.refresh(item)
    
    return {"status": "success", "item_id": str(item_id), "agent_id": str(agent_id)}


@router.delete("/{item_id}/assign-agent")
async def unassign_agent_from_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove agent assignment from a board item."""
    # Get item
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Verify project access
    await verify_project_access(item.project_id, current_user, db)
    
    # Unassign agent
    item.assigned_agent_id = None
    await db.commit()
    
    return {"status": "success"}


@router.post("/{item_id}/agent-action")
async def trigger_agent_action(
    item_id: uuid.UUID,
    message: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger the assigned agent to act on this item with a specific message."""
    # Get item with agent
    result = await db.execute(
        select(Item).where(Item.id == item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if not item.assigned_agent_id:
        raise HTTPException(status_code=400, detail="No agent assigned to this item")
    
    # Verify project access
    await verify_project_access(item.project_id, current_user, db)
    
    # Run agent with context about the item
    from app.agent.custom_agent_runner import run_custom_agent
    
    # Build context-aware message
    context_message = f"""You are helping with this board item:

Title: {item.title}
Description: {item.description or 'No description'}
Status: {item.status.value}
Priority: {item.priority.value}
Type: {item.type.value}

User request: {message}

Please help with this item. You can use board tools to update the status, add comments, or create related tasks."""
    
    result = await run_custom_agent(
        agent_id=item.assigned_agent_id,
        user_id=current_user.id,
        input_text=context_message,
        db=db,
        project_id=item.project_id
    )
    
    return {
        "status": "success",
        "agent_response": result.get("response"),
        "error": result.get("error")
    }
