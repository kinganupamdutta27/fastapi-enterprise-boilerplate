"""
Business logic for the items feature.

Services sit between routes and repositories. They enforce business rules,
orchestrate messaging, and keep route handlers thin.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.api.v1.items.repository import item_repository
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)


class ItemService:

    def __init__(self) -> None:
        self.repo = item_repository

    async def create_item(self, name: str, description: str | None = None) -> dict[str, Any]:
        item = await self.repo.create(name=name, description=description)
        logger.info("Item created: %s", item.get("id"))
        return item

    async def get_item(self, item_id: uuid.UUID) -> dict[str, Any]:
        item = await self.repo.get_by_id(item_id)
        if item is None:
            raise NotFoundError(message=f"Item {item_id} not found")
        return item

    async def list_items(self, limit: int = 50, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
        """Return items and total count for pagination."""
        items = await self.repo.list_all(limit=limit, offset=offset)
        total = await self.repo.count()
        return items, total

    async def update_item(
        self, item_id: uuid.UUID, name: str | None = None, description: str | None = None
    ) -> dict[str, Any]:
        item = await self.repo.update(item_id, name=name, description=description)
        if item is None:
            raise NotFoundError(message=f"Item {item_id} not found")
        return item

    async def delete_item(self, item_id: uuid.UUID) -> None:
        deleted = await self.repo.delete(item_id)
        if not deleted:
            raise NotFoundError(message=f"Item {item_id} not found")
        logger.info("Item deleted: %s", item_id)

    async def bulk_create_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Create multiple items in a single atomic transaction."""
        created = await self.repo.bulk_create(items)
        logger.info("Bulk created %d items", len(created))
        return created


item_service = ItemService()
