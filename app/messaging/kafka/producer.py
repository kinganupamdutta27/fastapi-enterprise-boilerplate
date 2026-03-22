"""
Kafka producer using aiokafka.

Publishes events to Kafka topics with automatic batching and compression.
"""

from __future__ import annotations

import json
import logging

from aiokafka import AIOKafkaProducer

from app.core.config import settings
from app.messaging.base import BaseProducer, Event

logger = logging.getLogger(__name__)


class KafkaProducer(BaseProducer):

    def __init__(self, bootstrap_servers: str | None = None) -> None:
        self._bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self._producer: AIOKafkaProducer | None = None

    async def connect(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            compression_type="gzip",
            acks="all",
        )
        await self._producer.start()
        logger.info("Kafka producer connected to %s", self._bootstrap_servers)

    async def disconnect(self) -> None:
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer disconnected")

    async def publish(self, topic: str, event: Event) -> None:
        if not self._producer:
            raise RuntimeError("Kafka producer is not connected")

        await self._producer.send_and_wait(
            topic,
            value=event.to_dict(),
            key=event.event_id.encode("utf-8"),
        )
        logger.debug("Published event %s to Kafka topic %s", event.event_id, topic)
