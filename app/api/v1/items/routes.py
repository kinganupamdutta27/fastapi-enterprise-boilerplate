"""Item CRUD REST endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import PaginationParams, get_pagination
from app.api.v1.items.schemas import (
    BulkItemCreate,
    ItemCreate,
    ItemListResponse,
    ItemResponse,
    ItemUpdate,
)
from app.api.v1.items.service import item_service

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(payload: ItemCreate):
    return await item_service.create_item(name=payload.name, description=payload.description)


@router.post("/bulk", response_model=list[ItemResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_items(payload: BulkItemCreate):
    """Create multiple items in a single atomic transaction."""
    items_data = [item.model_dump() for item in payload.items]
    return await item_service.bulk_create_items(items_data)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: uuid.UUID):
    return await item_service.get_item(item_id)


@router.get("/", response_model=ItemListResponse)
async def list_items(pagination: PaginationParams = Depends(get_pagination)):
    items, total = await item_service.list_items(
        limit=pagination.limit, offset=pagination.offset
    )
    return ItemListResponse(
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(item_id: uuid.UUID, payload: ItemUpdate):
    return await item_service.update_item(
        item_id, name=payload.name, description=payload.description
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: uuid.UUID):
    await item_service.delete_item(item_id)
