"""
Kafka consumer using aiokafka.

Runs a consumer loop in the background, dispatching events to registered handlers.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.messaging.base import BaseConsumer, Event, EventHandler

logger = logging.getLogger(__name__)


class KafkaConsumer(BaseConsumer):

    def __init__(
        self,
        bootstrap_servers: str | None = None,
        group_id: str | None = None,
    ) -> None:
        self._bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self._group_id = group_id or settings.kafka_consumer_group
        self._consumer: AIOKafkaConsumer | None = None
        self._handlers: dict[str, EventHandler] = {}
        self._running = False

    async def connect(self) -> None:
        topics = list(self._handlers.keys())
        if not topics:
            logger.warning("No topics registered; skipping Kafka consumer start")
            return

        self._consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        await self._consumer.start()
        logger.info("Kafka consumer connected, topics=%s", topics)

    async def disconnect(self) -> None:
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            logger.info("Kafka consumer disconnected")

    async def subscribe(self, topic: str, handler: EventHandler) -> None:
        self._handlers[topic] = handler

    async def start_consuming(self) -> None:
        if not self._consumer:
            raise RuntimeError("Kafka consumer is not connected")

        self._running = True
        try:
            async for msg in self._consumer:
                if not self._running:
                    break

                handler = self._handlers.get(msg.topic)
                if not handler:
                    continue

                try:
                    data: dict[str, Any] = msg.value
                    event = Event(
                        event_id=data.get("event_id", ""),
                        event_type=data.get("event_type", ""),
                        timestamp=data.get("timestamp", ""),
                        source=data.get("source", ""),
                        payload=data.get("payload", {}),
                        metadata=data.get("metadata", {}),
                    )
                    await handler(event)
                except Exception:
                    logger.exception("Failed to process Kafka message topic=%s", msg.topic)
        except Exception:
            if self._running:
                logger.exception("Kafka consumer loop error")
