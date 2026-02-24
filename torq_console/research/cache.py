"""
Research Cache Layer

Implements multi-level caching to control cost and latency:
1. Query cache - keyed by normalized query + params + recency bucket
2. URL content cache - cached page content
3. Request coalescing - multiple concurrent same queries = one search

TTL Strategy:
- News/current events: 15-60 minutes
- General facts: 1-7 days
- URL content: 7-30 days
"""

import hashlib
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CachedResult:
    """A cached research result."""
    query: str
    params: Dict[str, Any]
    response: Dict[str, Any]
    created_at: str
    ttl_seconds: int
    hit_count: int = 0
    last_accessed: str = ""

    def is_expired(self) -> bool:
        """Check if this cached result has expired."""
        created = datetime.fromisoformat(self.created_at)
        expiry = created + timedelta(seconds=self.ttl_seconds)
        return datetime.now(timezone.utc) > expiry

    def touch(self):
        """Update last_accessed time and increment hit count."""
        self.last_accessed = datetime.now(timezone.utc).isoformat()
        self.hit_count += 1


class QueryCache:
    """
    Cache for research queries with TTL based on query type.

    TTL Strategy:
    - Time-sensitive (news, prices, etc.): 15-60 minutes
    - General facts: 1-7 days
    - Conceptual definitions: 7-30 days
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: int = 3600,  # 1 hour default
    ):
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: Dict[str, CachedResult] = {}
        self._lock = asyncio.Lock()

    def _get_cache_key(self, query: str, params: Dict[str, Any]) -> str:
        """Generate cache key from query and params."""
        # Normalize query
        normalized = query.lower().strip()
        # Create key from normalized query + relevant params
        key_parts = [
            normalized,
            str(params.get("top_k", 5)),
            str(params.get("recency_days", "")),
            params.get("search_depth", "basic"),
        ]
        key = ":".join(key_parts)
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _determine_ttl(self, query: str, params: Dict[str, Any]) -> int:
        """Determine TTL based on query type."""
        query_lower = query.lower()

        # Time-sensitive queries = shorter TTL
        if any(word in query_lower for word in [
            "today", "latest", "breaking", "now", "current",
            "price", "stock", "market", "crypto", "trading",
        ]):
            return 900  # 15 minutes

        # News events = short TTL
        if any(word in query_lower for word in [
            "news", "headline", "breaking", "just announced",
        ]):
            return 1800  # 30 minutes

        # General facts = longer TTL
        if any(word in query_lower for word in [
            "what is", "define", "explain", "how does",
        ]):
            return 86400  # 1 day

        # Default
        return self.default_ttl_seconds

    async def get(
        self,
        query: str,
        params: Dict[str, Any],
    ) -> Optional[CachedResult]:
        """Get cached result if available and not expired."""
        async with self._lock:
            key = self._get_cache_key(query, params)

            if key not in self._cache:
                return None

            cached = self._cache[key]

            if cached.is_expired():
                # Remove expired entry
                del self._cache[key]
                logger.debug(f"Cache expired for query: {query[:50]}...")
                return None

            # Update access stats
            cached.touch()
            logger.info(f"Cache HIT for query: {query[:50]}...")
            return cached

    async def set(
        self,
        query: str,
        params: Dict[str, Any],
        response: Dict[str, Any],
        ttl_seconds: Optional[int] = None,
    ) -> CachedResult:
        """Cache a research result."""
        async with self._lock:
            key = self._get_cache_key(query, params)

            # Determine TTL
            if ttl_seconds is None:
                ttl_seconds = self._determine_ttl(query, params)

            # Create cache entry
            cached = CachedResult(
                query=query,
                params=params,
                response=response,
                created_at=datetime.now(timezone.utc).isoformat(),
                ttl_seconds=ttl_seconds,
                last_accessed=datetime.now(timezone.utc).isoformat(),
            )

            # Enforce max size
            if len(self._cache) >= self.max_size:
                await self._evict_oldest()

            self._cache[key] = cached
            logger.info(
                f"Cached query (TTL={ttl_seconds}s, {len(self._cache)}/{self.max_size}): "
                f"{query[:50]}..."
            )

            return cached

    async def _evict_oldest(self):
        """Evict the oldest/least-recently-used entry."""
        if not self._cache:
            return

        # Sort by last_accessed, evict oldest
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed or self._cache[k].created_at
        )
        del self._cache[oldest_key]
        logger.debug(f"Evicted cache entry: {oldest_key}")

    async def invalidate(self, query: Optional[str] = None):
        """Invalidate cache entries."""
        async with self._lock:
            if query is None:
                # Clear all
                self._cache.clear()
                logger.info("Cleared entire query cache")
            else:
                # Clear entries matching query (partial match)
                to_remove = [
                    k for k, v in self._cache.items()
                    if query.lower() in v.query.lower()
                ]
                for k in to_remove:
                    del self._cache[k]
                logger.info(f"Invalidated {len(to_remove)} cache entries for: {query}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_count": sum(c.hit_count for c in self._cache.values()),
        }


class RequestCoalescer:
    """
    Coalesce concurrent identical requests.

    If multiple requests for the same query arrive within a short window,
    only execute one search and share the result.
    """

    def __init__(self, coalesce_window_ms: int = 5000):
        self.coalesce_window_ms = coalesce_window_ms
        self._pending: Dict[str, asyncio.Future] = {}

    def _get_key(self, query: str, params: Dict[str, Any]) -> str:
        """Generate coalescing key."""
        key = f"{query.lower()}:{str(sorted(params.items()))}"
        return hashlib.sha256(key.encode()).hexdigest()[:12]

    async def coalesce(
        self,
        query: str,
        params: Dict[str, Any],
        search_func: callable,
    ) -> Any:
        """
        Either join an existing pending request or start a new one.

        Args:
            query: The search query
            params: Search parameters
            search_func: Async function that performs the search

        Returns:
            The search result (from either the shared or new request)
        """
        key = self._get_key(query, params)

        # Check if there's already a pending request for this
        if key in self._pending:
            logger.info(f"Coalescing request for: {query[:50]}...")
            return await self._pending[key]

        # Create a future for this request
        future = asyncio.Future()
        self._pending[key] = future

        try:
            # Execute the search
            result = await search_func()

            # Complete the future
            future.set_result(result)
            return result

        except Exception as e:
            future.set_exception(e)
            raise

        finally:
            # Clean up
            self._pending.pop(key, None)

    def get_pending_count(self) -> int:
        """Get number of pending coalesced requests."""
        return len(self._pending)


class URLCache:
    """
    Cache for URL content to avoid re-fetching pages.

    TTL: 7-30 days depending on content type.
    """

    def __init__(
        self,
        max_size: int = 500,
        default_ttl_seconds: int = 604800,  # 7 days default
    ):
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: Dict[str, CachedResult] = {}

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL."""
        return hashlib.sha256(url.encode()).hexdigest()[:12]

    async def get(self, url: str) -> Optional[str]:
        """Get cached URL content."""
        key = self._get_cache_key(url)

        if key not in self._cache:
            return None

        cached = self._cache[key]

        if cached.is_expired():
            del self._cache[key]
            return None

        cached.touch()
        logger.debug(f"URL cache HIT: {url[:50]}...")
        return cached.response.get("content")

    async def set(
        self,
        url: str,
        content: str,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Cache URL content."""
        key = self._get_cache_key(url)

        if ttl_seconds is None:
            # News URLs get shorter TTL
            if any(domain in url for domain in [
                "news.", "reuters", "bloomberg", "cnbc",
                "techcrunch", "wired", "ars technica"
            ]):
                ttl_seconds = 86400  # 1 day for news
            else:
                ttl_seconds = self.default_ttl_seconds

        cached = CachedResult(
            query=url,  # Using URL as query
            params={},
            response={"content": content},
            created_at=datetime.now(timezone.utc).isoformat(),
            ttl_seconds=ttl_seconds,
        )

        # Enforce max size
        if len(self._cache) >= self.max_size:
            oldest_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k].created_at
            )
            del self._cache[oldest_key]

        self._cache[key] = cached
        logger.debug(f"URL cached (TTL={ttl_seconds}s): {url[:50]}...")


# Singleton instances
_query_cache: Optional[QueryCache] = None
_coalescer: Optional[RequestCoalescer] = None
_url_cache: Optional[URLCache] = None


def get_query_cache() -> QueryCache:
    """Get the singleton query cache instance."""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache


def get_request_coalescer() -> RequestCoalescer:
    """Get the singleton request coalescer instance."""
    global _coalescer
    if _coalescer is None:
        _coalescer = RequestCoalescer()
    return _coalescer


def get_url_cache() -> URLCache:
    """Get the singleton URL cache instance."""
    global _url_cache
    if _url_cache is None:
        _url_cache = URLCache()
    return _url_cache
