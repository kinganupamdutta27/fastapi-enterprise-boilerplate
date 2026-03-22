"""Data-access layer for the items feature module."""

from __future__ import annotations

import uuid
from typing import Any

from app.db.repository import BaseRepository


class ItemRepository(BaseRepository):

    async def create(self, name: str, description: str | None = None) -> dict[str, Any]:
        item_id = uuid.uuid4()
        row = await self.fetch_one(
            """
            INSERT INTO items (id, name, description)
            VALUES ($1, $2, $3)
            RETURNING id, name, description, created_at, updated_at
            """,
            item_id,
            name,
            description,
        )
        return row or {}

    async def get_by_id(self, item_id: uuid.UUID) -> dict[str, Any] | None:
        return await self.fetch_one(
            "SELECT id, name, description, created_at, updated_at FROM items WHERE id = $1",
            item_id,
        )

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        return await self.fetch_all(
            "SELECT id, name, description, created_at, updated_at "
            "FROM items ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit,
            offset,
        )

    async def count(self) -> int:
        """Return total number of items (demonstrates fetch_val)."""
        result = await self.fetch_val("SELECT count(*) FROM items")
        return result or 0

    async def update(self, item_id: uuid.UUID, **fields: Any) -> dict[str, Any] | None:
        set_clauses: list[str] = []
        args: list[Any] = []
        idx = 1
        for key, value in fields.items():
            if value is not None:
                set_clauses.append(f"{key} = ${idx}")
                args.append(value)
                idx += 1

        if not set_clauses:
            return await self.get_by_id(item_id)

        set_clauses.append("updated_at = now()")
        args.append(item_id)

        query = (
            f"UPDATE items SET {', '.join(set_clauses)} "
            f"WHERE id = ${idx} "
            f"RETURNING id, name, description, created_at, updated_at"
        )
        return await self.fetch_one(query, *args)

    async def delete(self, item_id: uuid.UUID) -> bool:
        result = await self.execute("DELETE FROM items WHERE id = $1", item_id)
        return result == "DELETE 1"

    async def bulk_create(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Insert multiple items atomically inside a single transaction."""
        created: list[dict[str, Any]] = []
        async with self.transactional() as conn:
            for item_data in items:
                item_id = uuid.uuid4()
                row = await conn.fetchrow(
                    """
                    INSERT INTO items (id, name, description)
                    VALUES ($1, $2, $3)
                    RETURNING id, name, description, created_at, updated_at
                    """,
                    item_id,
                    item_data["name"],
                    item_data.get("description"),
                )
                if row:
                    created.append(dict(row))
        return created


item_repository = ItemRepository()
