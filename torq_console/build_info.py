import os
import json
import logging
from datetime import datetime, timezone
from importlib.metadata import version as pkg_version, PackageNotFoundError

logger = logging.getLogger(__name__)

_DIST_NAME = "torq-console"
_SCHEMA_UPDATED = "2026-02-22"

# Captured once at import = process/container start time. No I/O here.
_CONTAINER_START_TIME = (
    datetime.now(timezone.utc)
    .replace(microsecond=0)
    .isoformat()
    .replace("+00:00", "Z")
)


def now_ts() -> str:
    """Current time as timezone-aware ISO 8601 with Z suffix."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _load_build_meta() -> dict:
    """Read build_meta.json written at Docker build time. Called per-request, not at import."""
    meta_path = os.path.join(os.path.dirname(__file__), "build_meta.json")
    try:
        with open(meta_path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def get_app_version_with_source() -> tuple:
    """Returns (version_string, source) where source is 'package', 'env', or 'default'."""
    try:
        return pkg_version(_DIST_NAME), "package"
    except PackageNotFoundError:
        env_val = os.getenv("APP_VERSION")
        if env_val and env_val.strip():
            return env_val.strip(), "env"
        return "dev", "default"


def is_package_installed() -> bool:
    try:
        pkg_version(_DIST_NAME)
        return True
    except PackageNotFoundError:
        return False


def get_git_sha() -> str:
    # Railway native var preferred - most authoritative for Railway deployments.
    # GIT_SHA last - Docker ARG, can be stale if set manually.
    for key in ("RAILWAY_GIT_COMMIT_SHA", "GITHUB_SHA", "SOURCE_COMMIT", "GIT_SHA"):
        val = os.getenv(key)
        if val and val.strip():
            return val.strip()[:12]
    return str(_load_build_meta().get("git_sha", "unknown"))[:12]


def get_build_time() -> str:
    return str(_load_build_meta().get("built_at", "unknown"))


def get_build_branch() -> str:
    # Priority: build_meta.json (from Docker build) > runtime env vars > unknown
    meta_branch = _load_build_meta().get("branch")
    if meta_branch and meta_branch != "unknown":
        return str(meta_branch)
    # Runtime env vars (Railway may provide these)
    return (
        os.getenv("RAILWAY_GIT_BRANCH") or
        os.getenv("GIT_BRANCH") or
        os.getenv("BRANCH") or
        "unknown"
    )


def get_container_start_time() -> str:
    return _CONTAINER_START_TIME


def get_platform() -> str:
    """Detect runtime platform from environment. Never hardcode."""
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"):
        return "railway"
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
        return "vercel"
    if os.getenv("DOCKER_CONTAINER") or os.path.exists("/.dockerenv"):
        return "docker"
    return "unknown"


def get_service_name() -> str:
    return {
        "railway": "railway-backend",
        "vercel": "vercel-api",
        "docker": "docker-local",
    }.get(get_platform(), "unknown")


def get_schema_updated() -> str:
    return _SCHEMA_UPDATED
