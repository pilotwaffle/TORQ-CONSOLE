"""
Production-Grade Web Research Module

Prince Flowers web research with:
- Traceable & auditable operations
- Citation enforcement
- Caching & deduplication
- Conservative routing
- Security hardening
- Normalized provider outputs

Usage:
    from torq_console.research import research

    response = await research("What are Bitcoin price predictions for 2026?")
    print(response.answer)
    print(f"Sources: {response.citations}")
"""

from .coordinator import (
    research,
    get_research_coordinator,
    ResearchCoordinator,
)

from .router import ResearchRouter, get_research_router
from .cache import QueryCache, get_query_cache, get_url_cache
from .citations import CitationPolicy, get_citation_policy
from .security import WebSecurityChecker, get_security_checker
from .schema import (
    SearchProvider,
    ResearchSource,
    ResearchQuery,
    ResearchResponse,
    SynthesisResponse,
    SynthesisRequest,
    ResearchTrace,
    Citation,
)

__all__ = [
    # Main entry point
    "research",
    "get_research_coordinator",
    "ResearchCoordinator",
    # Router
    "ResearchRouter",
    "get_research_router",
    # Cache
    "QueryCache",
    "get_query_cache",
    "get_url_cache",
    # Citations
    "CitationPolicy",
    "get_citation_policy",
    # Security
    "WebSecurityChecker",
    "get_security_checker",
    # Schema
    "SearchProvider",
    "ResearchSource",
    "ResearchQuery",
    "ResearchResponse",
    "SynthesisResponse",
    "SynthesisRequest",
    "ResearchTrace",
    "Citation",
]
