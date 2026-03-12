"""
TORQ Console Dependency Injection

Provides singleton instances for workspace service and other dependencies.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from torq_console.settings import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_supabase_client() -> Client:
    """
    Get Supabase client (cached singleton).

    Uses TORQ's settings system for configuration.
    """
    settings = get_settings()
    url = settings.supabase.url
    key = settings.supabase.service_role_key

    if not url or not key:
        raise ValueError(
            "Supabase credentials not configured. "
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables."
        )

    return create_client(url, key)


def get_optional_supabase_client() -> Optional[Client]:
    """
    Get Supabase client, returning None if not configured.

    Useful for optional workspace features.
    """
    try:
        return get_supabase_client()
    except Exception:
        return None


def get_optional_llm_client() -> Optional[object]:
    """
    Get optional LLM client for workspace summarization.

    Returns None if Anthropic API is not configured.
    """
    try:
        import os

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        from anthropic import AsyncAnthropic

        return AsyncAnthropic(api_key=api_key)
    except Exception:
        return None
