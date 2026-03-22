"""
RabbitMQ consumer using aio-pika.

Subscribes to queues bound to a topic exchange.  Each handler runs in
the asyncio event loop and can acknowledge/reject messages.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import aio_pika

from app.core.config import settings
from app.messaging.base import BaseConsumer, Event, EventHandler

logger = logging.getLogger(__name__)


class RabbitMQConsumer(BaseConsumer):

    def __init__(
        self,
        url: str | None = None,
        exchange_name: str = "app_events",
        queue_prefix: str = "app",
    ) -> None:
        self._url = url or settings.rabbitmq_url
        self._exchange_name = exchange_name
        self._queue_prefix = queue_prefix
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._handlers: dict[str, EventHandler] = {}

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=settings.rabbitmq_prefetch_count)
        logger.info("RabbitMQ consumer connected")

    async def disconnect(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("RabbitMQ consumer disconnected")

    async def subscribe(self, topic: str, handler: EventHandler) -> None:
        self._handlers[topic] = handler

    async def start_consuming(self) -> None:
        if not self._channel:
            raise RuntimeError("RabbitMQ consumer is not connected")

        exchange = await self._channel.declare_exchange(
            self._exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )

        for topic, handler in self._handlers.items():
            queue_name = f"{self._queue_prefix}.{topic}"
            queue = await self._channel.declare_queue(queue_name, durable=True)
            await queue.bind(exchange, routing_key=topic)

            async def _on_message(
                message: aio_pika.abc.AbstractIncomingMessage,
                _handler: EventHandler = handler,
            ) -> None:
                async with message.process():
                    try:
                        data: dict[str, Any] = json.loads(message.body)
                        event = Event(
                            event_id=data.get("event_id", ""),
                            event_type=data.get("event_type", ""),
                            timestamp=data.get("timestamp", ""),
                            source=data.get("source", ""),
                            payload=data.get("payload", {}),
                            metadata=data.get("metadata", {}),
                        )
                        await _handler(event)
                    except Exception:
                        logger.exception("Failed to process message")

            await queue.consume(_on_message)
            logger.info("Subscribed to RabbitMQ topic=%s queue=%s", topic, queue_name)
