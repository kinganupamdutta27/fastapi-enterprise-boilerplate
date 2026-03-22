"""Pydantic request / response schemas for items."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["Widget X"])
    description: str | None = Field(None, max_length=2000, examples=["A high-quality widget"])


class ItemUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)


class ItemResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ItemListResponse(BaseModel):
    items: list[ItemResponse]
    total: int
    limit: int
    offset: int


class BulkItemCreate(BaseModel):
    items: list[ItemCreate] = Field(..., min_length=1, max_length=100)
