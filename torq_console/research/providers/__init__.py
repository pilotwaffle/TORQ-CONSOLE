"""
Provider Adapters with Normalized Output

Each search provider (Tavily, Brave, DuckDuckGo) returns data in a different format.
These adapters normalize everything into the ResearchResponse schema.
"""

import os
import logging
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from ..schema import (
    SearchProvider,
    ResearchSource,
    ResearchResponse,
    ResearchQuery,
)

logger = logging.getLogger(__name__)


class BaseSearchProvider:
    """Base class for search providers with normalized output."""

    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout

    async def search(self, query: ResearchQuery) -> ResearchResponse:
        """Execute search and return normalized response."""
        raise NotImplementedError

    def _to_research_source(self, raw_item: Dict[str, Any]) -> ResearchSource:
        """Convert provider-specific item to ResearchSource."""
        raise NotImplementedError

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return None


class TavilyProvider(BaseSearchProvider):
    """
    Tavily Search API adapter.

    Tavily is optimized for AI/LLM applications with clean, relevant results.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY required")
        super().__init__(api_key, timeout)
        self.base_url = "https://api.tavily.com/search"

    async def search(self, query: ResearchQuery) -> ResearchResponse:
        """Execute Tavily search."""
        import time
        start_time = time.time()

        # Build request
        payload = {
            "api_key": self.api_key,
            "query": query.query,
            "max_results": query.top_k,
            "search_depth": query.search_depth,
            "include_answer": query.include_answer,
            "include_raw_content": query.include_raw_content,
        }

        if query.recency_days:
            # Tavily uses days parameter
            payload["days"] = query.recency_days

        if query.domains:
            payload["include_domains"] = query.domains

        if query.exclude_domains:
            payload["exclude_domains"] = query.exclude_domains

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.base_url, json=payload)
                response.raise_for_status()
                data = response.json()

        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            # Return empty response on error
            return ResearchResponse(
                provider=SearchProvider.TAVILY,
                items=[],
                meta={"query": query.query, "error": str(e)},
                query=query.query,
                result_count=0,
                search_duration_ms=int((time.time() - start_time) * 1000),
            )

        # Extract answer if provided
        answer = data.get("answer", "")

        # Normalize results
        items = []
        for result in data.get("results", []):
            source = ResearchSource(
                title=result.get("title", ""),
                url=result.get("url", ""),
                snippet=result.get("content", ""),
                published_at=result.get("published_date"),
                score=result.get("score", 0.0),
                provider=SearchProvider.TAVILY,
                domain=self._extract_domain(result.get("url", "")),
            )
            items.append(source)

        duration_ms = int((time.time() - start_time) * 1000)

        return ResearchResponse(
            provider=SearchProvider.TAVILY,
            items=items,
            meta={
                "query": query.query,
                "answer": answer,
                "has_answer": bool(answer),
            },
            query=query.query,
            result_count=len(items),
            search_duration_ms=duration_ms,
            estimated_cost_usd=self._estimate_cost(query.top_k),
        )

    def _estimate_cost(self, top_k: int) -> float:
        """Estimate Tavily API cost in USD."""
        # Tavily: $5/month for developer tier (1000 requests)
        # Approx $0.005 per request
        return 0.005


class BraveProvider(BaseSearchProvider):
    """
    Brave Search API adapter.

    Brave provides 2,000 free queries/month with decent web coverage.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        api_key = api_key or os.getenv("BRAVE_SEARCH_API_KEY")
        if not api_key:
            raise ValueError("BRAVE_SEARCH_API_KEY required")
        super().__init__(api_key, timeout)
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    async def search(self, query: ResearchQuery) -> ResearchResponse:
        """Execute Brave search."""
        import time
        start_time = time.time()

        # Build request
        params = {
            "q": query.query,
            "count": query.top_k,
            "text_decorations": False,
            "search_lang": "en",
        }

        # Brave doesn't have native recency filter, use Freshness API
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

        except Exception as e:
            logger.error(f"Brave search error: {e}")
            return ResearchResponse(
                provider=SearchProvider.BRAVE,
                items=[],
                meta={"query": query.query, "error": str(e)},
                query=query.query,
                result_count=0,
                search_duration_ms=int((time.time() - start_time) * 1000),
            )

        # Normalize results
        items = []
        web_results = data.get("web", {}).get("results", [])

        for result in web_results[:query.top_k]:
            source = ResearchSource(
                title=result.get("title", ""),
                url=result.get("url", ""),
                snippet=result.get("description", ""),
                published_at=None,  # Brave doesn't provide publish date
                score=0.0,  # Brave doesn't provide scores
                provider=SearchProvider.BRAVE,
                domain=self._extract_domain(result.get("url", "")),
            )
            items.append(source)

        duration_ms = int((time.time() - start_time) * 1000)

        return ResearchResponse(
            provider=SearchProvider.BRAVE,
            items=items,
            meta={"query": query.query},
            query=query.query,
            result_count=len(items),
            search_duration_ms=duration_ms,
            estimated_cost_usd=self._estimate_cost(),
        )

    def _estimate_cost(self) -> float:
        """Estimate Brave API cost in USD."""
        # Brave: Free tier = 2,000 requests/month
        # Then $0.003 per 1,000 queries
        return 0.003  # Effectively free for our volume


class DuckDuckGoProvider(BaseSearchProvider):
    """
    DuckDuckGo Instant Answer API adapter (fallback).

    Free but limited results. No API key required.
    """

    def __init__(self, timeout: int = 30):
        super().__init__("", timeout)
        self.base_url = "https://api.duckduckgo.com/"

    async def search(self, query: ResearchQuery) -> ResearchResponse:
        """Execute DuckDuckGo search (no API key needed)."""
        import time
        start_time = time.time()

        params = {
            "q": query.query,
            "format": "json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.base_url,
                    params=params,
                )
                data = response.json()

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return ResearchResponse(
                provider=SearchProvider.DUCKDUCKGO,
                items=[],
                meta={"query": query.query, "error": str(e)},
                query=query.query,
                result_count=0,
                search_duration_ms=int((time.time() - start_time) * 1000),
            )

        # Normalize results
        items = []

        # DDG returns RelatedTopics mainly
        for topic in data.get("RelatedTopics", [])[:query.top_k]:
            if topic.get("Text") and topic.get("FirstURL"):
                source = ResearchSource(
                    title=topic.get("Text", "").split(" - ")[0],
                    url=topic.get("FirstURL", ""),
                    snippet=topic.get("Text", ""),
                    published_at=None,
                    score=0.0,
                    provider=SearchProvider.DUCKDUCKGO,
                    domain=self._extract_domain(topic.get("FirstURL", "")),
                )
                items.append(source)

        duration_ms = int((time.time() - start_time) * 1000)

        return ResearchResponse(
            provider=SearchProvider.DUCKDUCKGO,
            items=items,
            meta={"query": query.query},
            query=query.query,
            result_count=len(items),
            search_duration_ms=duration_ms,
            estimated_cost_usd=0.0,  # Free
        )


def create_provider(
    provider_name: str,
    api_key: Optional[str] = None,
) -> BaseSearchProvider:
    """Factory function to create a search provider."""
    providers = {
        "tavily": TavilyProvider,
        "brave": BraveProvider,
        "duckduckgo": DuckDuckGoProvider,
        "ddg": DuckDuckGoProvider,
    }

    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}")

    # DuckDuckGo doesn't need API key
    if provider_name.lower() in ["duckduckgo", "ddg"]:
        return provider_class()

    return provider_class(api_key=api_key)


async def search_with_fallback(
    query: ResearchQuery,
    providers: List[str] = ["tavily", "brave", "duckduckgo"],
) -> ResearchResponse:
    """
    Execute search with automatic fallback.

    Tries providers in order, falling back to next on failure.
    """
    import time

    for provider_name in providers:
        start_time = time.time()
        try:
            provider = create_provider(provider_name)
            response = await provider.search(query)

            if response.result_count > 0:
                logger.info(
                    f"Search successful with {provider_name}: "
                    f"{response.result_count} results in {response.search_duration_ms}ms"
                )
                response.search_duration_ms += int((time.time() - start_time) * 1000)
                return response

            # No results, try next
            logger.warning(f"{provider_name} returned 0 results, trying next...")

        except Exception as e:
            logger.warning(f"{provider_name} failed: {e}, trying next...")

    # All providers failed
    return ResearchResponse(
        provider=SearchProvider.DUCKDUCKGO,
        items=[],
        meta={"query": query.query, "error": "All providers failed"},
        query=query.query,
        result_count=0,
        search_duration_ms=int((time.time() - start_time) * 1000),
    )
