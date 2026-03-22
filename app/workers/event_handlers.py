"""
Event handler registry.

Register all event handlers here.  The handlers are wired up to the
chosen message broker (RabbitMQ or Kafka) during application startup.
"""

from __future__ import annotations

import logging

from app.messaging.base import Event

logger = logging.getLogger(__name__)


async def handle_item_created(event: Event) -> None:
    """Process an item.created event — example handler."""
    logger.info(
        "Handling item.created event_id=%s payload=%s",
        event.event_id,
        event.payload,
    )


async def handle_item_deleted(event: Event) -> None:
    """Process an item.deleted event — example handler."""
    logger.info(
        "Handling item.deleted event_id=%s payload=%s",
        event.event_id,
        event.payload,
    )
