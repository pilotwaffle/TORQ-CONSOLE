"""
Normalized Web Research Schema

All search providers (Tavily, Brave, DuckDuckGo) return data in this format.
This ensures Claude sees consistent structure and telemetry stays uniform.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class SearchProvider(str, Enum):
    """Supported search providers."""
    TAVILY = "tavily"
    BRAVE = "brave"
    DUCKDUCKGO = "ddg"


class ResearchSource(BaseModel):
    """A single search result from any provider."""
    title: str = Field(..., description="Source title")
    url: str = Field(..., description="Source URL")
    snippet: str = Field(..., description="Content snippet/preview")
    published_at: Optional[str] = Field(None, description="Publication date if available")
    score: float = Field(0.0, description="Relevance score 0-1")
    provider: SearchProvider = Field(..., description="Which provider returned this")

    # Extracted metadata
    domain: Optional[str] = Field(None, description="Extracted domain name")
    is_news: bool = Field(False, description="Is this a news source?")
    is_primary: bool = Field(False, description="Is this a primary source?")


class ResearchQuery(BaseModel):
    """Normalized research query with parameters."""
    query: str = Field(..., description="The search query")
    top_k: int = Field(5, description="Max results to return", ge=1, le=20)
    recency_days: Optional[int] = Field(None, description="Only results from last N days")
    domains: Optional[List[str]] = Field(None, description="Restrict to these domains")
    exclude_domains: Optional[List[str]] = Field(None, description="Exclude these domains")
    search_depth: str = Field("basic", description="basic or advanced research")
    include_raw_content: bool = Field(False, description="Fetch full page content")
    include_answer: bool = Field(False, description="Let provider generate answer")

    def cache_key(self) -> str:
        """Generate cache key for this query."""
        import hashlib
        normalized = self.query.lower().strip()
        parts = [
            normalized,
            str(self.top_k),
            str(self.recency_days or 0),
            self.search_depth,
        ]
        if self.domains:
            parts.append(",".join(sorted(self.domains)))
        key = ":".join(parts)
        return hashlib.sha256(key.encode()).hexdigest()[:16]


class ResearchResponse(BaseModel):
    """Normalized response from any search provider."""
    provider: SearchProvider
    items: List[ResearchSource]
    meta: Dict[str, Any] = Field(default_factory=dict)

    # Telemetry fields
    query: str
    result_count: int
    search_duration_ms: int
    cached: bool = False
    cache_hit: bool = False

    # Cost estimation
    estimated_cost_usd: float = 0.0

    class Config:
        use_enum_values = True


class SynthesisRequest(BaseModel):
    """Request to synthesize research results into an answer."""
    original_query: str
    sources: List[ResearchSource]
    context: Optional[str] = None
    require_citations: bool = True
    min_citations: int = 2
    citation_format: str = "markdown"  # markdown or json


class Citation(BaseModel):
    """A citation in the synthesized answer."""
    index: int
    title: str
    url: str
    snippet: Optional[str] = None
    confidence: float = 1.0


class SynthesisResponse(BaseModel):
    """Synthesized answer with citations."""
    answer: str
    citations: List[Citation]
    provider_used: str  # "anthropic", "openai", etc.
    model_used: str
    has_citations: bool
    citation_count: int
    confidence: float = Field(ge=0.0, le=1.0)

    # Research metadata
    research_duration_ms: int
    sources_consulted: int
    router_decision: str
    triggered_by: str  # Which signal triggered research mode


class ResearchTrace(BaseModel):
    """Complete trace of a research operation for telemetry."""
    trace_id: str
    session_id: str
    query: str

    # Routing decision
    router_decision: str
    router_signals: List[str]

    # Search execution
    provider_used: SearchProvider
    search_params: Dict[str, Any]
    result_count: int

    # Sources
    source_urls: List[str]
    source_titles: List[str]

    # Synthesis
    llm_provider: str
    llm_model: str
    has_citations: bool
    citation_count: int

    # Performance
    search_duration_ms: int
    synthesis_duration_ms: int
    total_duration_ms: int

    # Cost
    estimated_search_cost_usd: float
    estimated_llm_cost_usd: float
    estimated_total_cost_usd: float

    # Outcome
    confidence: float
    cached: bool
    cache_hit: bool

    # Deploy identity (for correlation)
    deploy_git_sha: str
    deploy_platform: str
    deploy_app_version: str

    timestamp: str
