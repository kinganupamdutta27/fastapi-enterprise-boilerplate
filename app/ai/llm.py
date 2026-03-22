"""
LLM client factory.

Provides a single function to get a configured ChatOpenAI (or any
LangChain-compatible chat model) so every module uses the same settings.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_chat_model():
    """Return a cached LangChain ChatOpenAI instance.

    Import is deferred so the module doesn't fail at import time
    when langchain is not installed (it's an optional dependency).
    """
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model_name,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        api_key=settings.openai_api_key,
    )
