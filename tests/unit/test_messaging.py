"""Unit tests for the event data model."""

from __future__ import annotations

from app.messaging.base import Event


def test_event_to_dict():
    event = Event(event_type="item.created", payload={"name": "Widget"})
    data = event.to_dict()
    assert data["event_type"] == "item.created"
    assert data["payload"]["name"] == "Widget"
    assert "event_id" in data
    assert "timestamp" in data


def test_event_default_source():
    event = Event(event_type="test", payload={})
    assert event.source == "app"
