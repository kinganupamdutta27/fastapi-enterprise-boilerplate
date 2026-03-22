"""Unit tests for Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.v1.items.schemas import ItemCreate


def test_item_create_valid():
    item = ItemCreate(name="Widget", description="A widget")
    assert item.name == "Widget"


def test_item_create_empty_name_fails():
    with pytest.raises(ValidationError):
        ItemCreate(name="")


def test_item_create_description_optional():
    item = ItemCreate(name="Widget")
    assert item.description is None
