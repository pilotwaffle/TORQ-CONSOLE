"""
Environment Configuration Management

Centralized settings management with:
- Runtime environment reads (not cached at import time)
- Duplicate key detection for dev/test
- Clean separation from module globals

Usage:
    from torq_console.settings import get_settings, reload_settings

    settings = get_settings()
    url = settings.supabase_url
"""

import os
import logging
from functools import lru_cache
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Detect if we're in development/test mode
_DEV_MODE = os.environ.get("RAILWAY_ENVIRONMENT", "") == "" and os.environ.get("VERCEL_ENV", "") == ""


def _check_duplicate_keys(env_file: str = ".env") -> None:
    """
    Check for duplicate keys in .env file.

    In dev/test mode, raises ValueError if duplicates found.
    In production, silently skips (no .env file in prod containers).
    """
    if not _DEV_MODE:
        return

    try:
        seen_keys = {}
        with open(env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key = line.split('=')[0].strip()
                    if key in seen_keys:
                        raise ValueError(
                            f"Duplicate key '{key}' found in .env at line {line_num}. "
                            f"Previously defined at line {seen_keys[key]}. "
                            f"Remove the old entry to avoid unpredictable behavior."
                        )
                    seen_keys[key] = line_num
    except FileNotFoundError:
        # No .env file - not an error in production
        pass


# Run duplicate check once at module load (dev/test only)
_check_duplicate_keys()


@dataclass
class SupabaseSettings:
    """Supabase configuration."""
    url: Optional[str] = None
    service_role_key: Optional[str] = None
    anon_key: Optional[str] = None
    project_ref: Optional[str] = None

    def __post_init__(self):
        if self.url:
            # Parse project ref from URL
            import re
            match = re.search(r'//([^.]+)\.supabase\.co', self.url)
            if match:
                self.project_ref = match.group(1)


@dataclass
class TelemetrySettings:
    """Telemetry configuration."""
    enabled: bool = True
    strict: bool = False
    sink: str = "supabase"  # supabase | memory | null


@dataclass
class Settings:
    """Centralized application settings."""

    supabase: SupabaseSettings = None
    telemetry: TelemetrySettings = None

    # Production flags
    is_production: bool = False
    is_railway: bool = False
    is_vercel: bool = False

    # Debug flags
    verbose: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get application settings (cached per process).

    Settings are read at call time, not at import time.
    Use reload_settings() to clear cache and re-read from environment.
    """
    # Read environment at call time
    return Settings(
        supabase=SupabaseSettings(
            url=os.getenv("SUPABASE_URL"),
            service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            anon_key=os.getenv("SUPABASE_ANON_KEY"),
        ),
        telemetry=TelemetrySettings(
            enabled=os.getenv("TORQ_TELEMETRY_ENABLED", "true").lower() == "true",
            strict=os.getenv("TORQ_TELEMETRY_STRICT", "false").lower() == "true",
            sink=os.getenv("TORQ_TELEMETRY_SINK", "supabase"),
        ),
        is_production=os.getenv("TORQ_CONSOLE_PRODUCTION", "false").lower() == "true",
        is_railway=bool(os.getenv("RAILWAY_ENVIRONMENT")),
        is_vercel=bool(os.getenv("VERCEL")),
        verbose=os.getenv("TORQ_VERBOSE", "false").lower() == "true",
    )


def reload_settings() -> Settings:
    """
    Clear settings cache and re-read from environment.

    Use this in tests to simulate environment changes.
    """
    get_settings.cache_clear()
    return get_settings()


def get_supabase_url() -> str:
    """Convenience helper for Supabase URL (runtime read)."""
    return get_settings().supabase.url or ""


def get_supabase_key() -> str:
    """
    Get Supabase key with fallback: service_role > anon.

    Returns empty string if neither is set.
    """
    settings = get_settings()
    return settings.supabase.service_role_key or settings.supabase.anon_key or ""
