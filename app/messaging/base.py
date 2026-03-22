"""
Abstract message broker interface.

All concrete implementations (RabbitMQ, Kafka, Redis Streams, etc.)
implement this contract so that business logic is decoupled from the
transport mechanism.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine
from uuid import uuid4


@dataclass
class Event:
    """Canonical event envelope shared across all brokers."""

    event_type: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "app"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "source": self.source,
            "payload": self.payload,
            "metadata": self.metadata,
        }


EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class BaseProducer(abc.ABC):
    @abc.abstractmethod
    async def connect(self) -> None: ...

    @abc.abstractmethod
    async def disconnect(self) -> None: ...

    @abc.abstractmethod
    async def publish(self, topic: str, event: Event) -> None: ...


class BaseConsumer(abc.ABC):
    @abc.abstractmethod
    async def connect(self) -> None: ...

    @abc.abstractmethod
    async def disconnect(self) -> None: ...

    @abc.abstractmethod
    async def subscribe(self, topic: str, handler: EventHandler) -> None: ...

    @abc.abstractmethod
    async def start_consuming(self) -> None: ...
