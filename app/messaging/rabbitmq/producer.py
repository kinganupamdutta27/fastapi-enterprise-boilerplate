"""
RabbitMQ producer using aio-pika.

Publishes events to RabbitMQ exchanges with automatic reconnection.
"""

from __future__ import annotations

import json
import logging

import aio_pika

from app.core.config import settings
from app.messaging.base import BaseProducer, Event

logger = logging.getLogger(__name__)


class RabbitMQProducer(BaseProducer):

    def __init__(self, url: str | None = None, exchange_name: str = "app_events") -> None:
        self._url = url or settings.rabbitmq_url
        self._exchange_name = exchange_name
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            self._exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )
        logger.info("RabbitMQ producer connected, exchange=%s", self._exchange_name)

    async def disconnect(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("RabbitMQ producer disconnected")

    async def publish(self, topic: str, event: Event) -> None:
        if not self._exchange:
            raise RuntimeError("RabbitMQ producer is not connected")

        message = aio_pika.Message(
            body=json.dumps(event.to_dict()).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=event.event_id,
        )
        await self._exchange.publish(message, routing_key=topic)
        logger.debug("Published event %s to topic %s", event.event_id, topic)
