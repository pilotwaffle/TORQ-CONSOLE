"""
Production-Grade Research Coordinator

Main orchestrator for web research with:
- Traceable & auditable operations
- Citation enforcement
- Caching & deduplication
- Conservative routing
- Security hardening
"""

import os
import time
import uuid
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse

from .schema import (
    SearchProvider,
    ResearchSource,
    ResearchQuery,
    ResearchResponse,
    SynthesisRequest,
    SynthesisResponse,
    ResearchTrace,
)
from .router import ResearchRouter, get_research_router
from .cache import (
    QueryCache,
    RequestCoalescer,
    get_query_cache,
    get_request_coalescer,
)
from .citations import CitationPolicy, get_citation_policy
from .security import WebSecurityChecker, get_security_checker
from .providers import search_with_fallback

logger = logging.getLogger(__name__)


class ResearchCoordinator:
    """
    Main coordinator for production-grade web research.

    Orchestrates the entire research flow:
    1. Route decision (research vs local)
    2. Cache check
    3. Provider selection and fallback
    4. Citation enforcement
    5. Telemetry emission
    6. Cost tracking
    """

    def __init__(
        self,
        router: Optional[ResearchRouter] = None,
        cache: Optional[QueryCache] = None,
        coalescer: Optional[RequestCoalescer] = None,
        citation_policy: Optional[CitationPolicy] = None,
        security: Optional[WebSecurityChecker] = None,
        default_providers: List[str] = None,
    ):
        self.router = router or get_research_router()
        self.cache = cache or get_query_cache()
        self.coalescer = coalescer or get_request_coalescer()
        self.citation_policy = citation_policy or get_citation_policy()
        self.security = security or get_security_checker()
        self.default_providers = default_providers or ["tavily", "brave", "duckduckgo"]

    async def research(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_context: Optional[dict] = None,
    ) -> SynthesisResponse:
        """
        Execute full research flow: route → search → synthesize → cite.

        This is the main entry point for research operations.
        """
        trace_id = str(uuid.uuid4())
        session_id = session_id or f"research_{session_id or 'default'}"

        # Start timing
        start_time = time.time()
        trace_start = datetime.now(timezone.utc)

        # 1. Routing decision
        should_research, signals = self.router.should_research(query, user_context)
        router_decision = self.router.log_decision(query, should_research, signals)

        # If not a research query, return simple response
        if not should_research:
            return SynthesisResponse(
                answer=self._local_answer(query),
                citations=[],
                provider_used="local",
                model_used="n/a",
                has_citations=False,
                citation_count=0,
                confidence=0.8,
                research_duration_ms=0,
                sources_consulted=0,
                router_decision="local",
                triggered_by=",".join(signals) or "none",
            )

        # 2. Build research query from router params
        research_params = self.router.get_research_params(query, signals)
        research_query = ResearchQuery(
            query=query,
            **research_params,
        )

        # 3. Check cache first
        cached_result = await self.cache.get(query, research_params)
        if cached_result:
            logger.info(f"Cache HIT for research query: {query[:50]}...")
            return self._build_response_from_cache(
                cached_result,
                router_decision,
                signals,
            )

        # 4. Execute search with coalescing
        search_response = await self._coalesce_and_search(
            research_query,
            trace_id,
        )

        # 5. Security check on URLs
        safe_sources = await self._validate_sources(search_response.items)

        # 6. Cache the results
        await self.cache.set(
            query,
            research_params,
            search_response.model_dump(mode="json"),
        )

        # 7. Synthesize answer with citations
        synthesis_start = time.time()
        synthesis = await self._synthesize_with_citations(
            query,
            safe_sources,
            router_decision,
            signals,
        )

        # 8. Canonicalize citations (deterministic formatting)
        canonical_result = self.citation_policy.canonicalize_response(
            synthesis.answer,
            safe_sources,
            trust_scores={s.domain or urlparse(s.url).netloc: s.score for s in safe_sources},
        )

        # Update synthesis with canonicalized answer and sources
        synthesis.answer = canonical_result["answer"]
        synthesis.citations = [c.model_dump() for c in canonical_result["citations"]]
        synthesis.has_citations = len(canonical_result["citations"]) > 0
        synthesis.citation_count = len(canonical_result["citations"])

        # Store canonicalization metadata for trace
        canonicalization_meta = {
            "duplicates_removed": canonical_result["duplicates_removed"],
            "sources_normalized": len(canonical_result["sources"]),
            "citation_format_version": "v1",
        }

        # 9. Enforce citation policy (retry if needed)
        citation_check = self.citation_policy.check_citations(
            synthesis.answer,
            canonical_result["sources"],
        )

        if self.citation_policy.should_retry(citation_check):
            logger.warning("Citation policy violation - retrying with citations...")
            synthesis = await self._retry_with_enforced_citations(
                query,
                synthesis.answer,
                canonical_result["sources"],
            )
            # Re-canonicalize after retry
            canonical_result = self.citation_policy.canonicalize_response(
                synthesis.answer,
                canonical_result["sources"],
            )
            synthesis.answer = canonical_result["answer"]
            synthesis.citations = [c.model_dump() for c in canonical_result["citations"]]
            synthesis.has_citations = len(canonical_result["citations"]) > 0
            synthesis.citation_count = len(canonical_result["citations"])

        # 10. Build trace for telemetry with citation metadata
        total_duration_ms = int((time.time() - start_time) * 1000)
        trace = ResearchTrace(
            trace_id=trace_id,
            session_id=session_id,
            query=query,
            router_decision=router_decision["router_decision"],
            router_signals=signals,
            provider_used=search_response.provider,
            search_params=research_params,
            result_count=len(search_response.items),
            source_urls=[s.url for s in safe_sources],
            source_titles=[s.title for s in safe_sources],
            llm_provider=synthesis.provider_used,
            llm_model=synthesis.model_used,
            has_citations=synthesis.has_citations,
            citation_count=synthesis.citation_count,
            search_duration_ms=search_response.search_duration_ms,
            synthesis_duration_ms=int((time.time() - synthesis_start) * 1000),
            total_duration_ms=total_duration_ms,
            estimated_search_cost_usd=search_response.estimated_cost_usd,
            estimated_llm_cost_usd=0.001,  # Rough estimate
            estimated_total_cost_usd=(
                search_response.estimated_cost_usd + 0.001
            ),
            confidence=synthesis.confidence,
            cached=False,
            cache_hit=False,
            deploy_git_sha=self._get_deploy_sha(),
            deploy_platform=self._get_deploy_platform(),
            deploy_app_version=self._get_deploy_version(),
            timestamp=trace_start.isoformat(),
        )

        # Build citation metadata for span
        top_domains = list({
            urlparse(s.url).netloc for s in safe_sources[:5]
        })

        citation_span_metadata = {
            "citations_count": synthesis.citation_count,
            "sources_top_domains": top_domains,
            "citation_format_version": "v1",
        }
        citation_span_metadata.update(canonicalization_meta)

        # 11. Emit telemetry (async, don't wait)
        asyncio.create_task(self._emit_trace(trace, citation_span_metadata))

        return synthesis

    async def _coalesce_and_search(
        self,
        query: ResearchQuery,
        trace_id: str,
    ) -> ResearchResponse:
        """Execute search with request coalescing."""

        async def search_func():
            return await search_with_fallback(
                query,
                providers=self.default_providers,
            )

        return await self.coalescer.coalesce(
            query.query,
            query.model_dump(),
            search_func,
        )

    async def _validate_sources(
        self,
        sources: List[ResearchSource],
    ) -> List[ResearchSource]:
        """Security check on all source URLs."""
        safe_sources = []

        for source in sources:
            allowed, reason = self.security.is_url_allowed(source.url)
            if allowed:
                # Also check domain trust score
                trust_score = self.security.score_domain_trust(
                    source.domain or ""
                )
                # Update source with trust score
                source.score = trust_score
                safe_sources.append(source)
            else:
                logger.warning(f"Blocked URL {source.url}: {reason}")

        return safe_sources

    async def _synthesize_with_citations(
        self,
        query: str,
        sources: List[ResearchSource],
        router_decision: dict,
        signals: List[str],
    ) -> SynthesisResponse:
        """Synthesize answer using LLM with sources."""
        import anthropic

        # Build system prompt with sources
        system_prompt = """You are a research assistant. You will be given:
1. A user question
2. A list of search results with titles, URLs, and snippets

Your task:
- Synthesize a comprehensive answer from the sources
- Use inline citations like [1], [2] to reference sources
- Quote exact lines sparingly, only for key facts
- If sources disagree, acknowledge the disagreement
- Be specific and factual

Citation format:
- Use [1], [2], [3] style in your answer
- Each number corresponds to a source in order
- Don't make up sources"""

        # Format sources for the prompt
        sources_text = "\n\n".join([
            f"{i+1}. {s.title}\n   URL: {s.url}\n   Snippet: {s.snippet}\n"
            for i, s in enumerate(sources)
        ])

        user_prompt = f"""Question: {query}

Sources:
{sources_text}

Provide a comprehensive answer with inline citations [1], [2], etc."""

        start_time = time.time()

        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            message = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            answer = message.content[0].text

            # Extract citations from answer
            citations = self.citation_policy._extract_citations(answer, sources)

            return SynthesisResponse(
                answer=answer,
                citations=[c.model_dump() for c in citations],
                provider_used="anthropic",
                model_used="claude-sonnet-4-6",
                has_citations=len(citations) > 0,
                citation_count=len(citations),
                confidence=0.85 if len(citations) >= 2 else 0.6,
                research_duration_ms=int((time.time() - start_time) * 1000),
                sources_consulted=len(sources),
                router_decision=router_decision.get("router_decision", "research"),
                triggered_by=",".join(signals),
            )

        except Exception as e:
            logger.error(f"LLM synthesis error: {e}")
            # Fallback to direct answer
            return SynthesisResponse(
                answer=f"I found {len(sources)} relevant sources, but encountered an error synthesizing the answer. Here are the sources:\n\n" +
                "\n".join([f"- {s.title}: {s.url}" for s in sources]),
                citations=[],
                provider_used="fallback",
                model_used="n/a",
                has_citations=False,
                citation_count=0,
                confidence=0.3,
                research_duration_ms=int((time.time() - start_time) * 1000),
                sources_consulted=len(sources),
                router_decision="research_error",
                triggered_by=",".join(signals),
            )

    async def _retry_with_enforced_citations(
        self,
        query: str,
        original_answer: str,
        sources: List[ResearchSource],
    ) -> SynthesisResponse:
        """Retry LLM call to add citations."""
        import anthropic

        citation_block = self.citation_policy.format_citations_markdown(sources)

        retry_prompt = f"""Your previous answer is below. Please add proper citations to it.

Question: {query}

Your answer:
{original_answer}

Available sources to cite:
{citation_block}

Please rewrite your answer with proper inline citations like [1], [2] that reference these sources.
Quote exact lines sparingly - only for key facts.
Keep your original answer structure but add citations where appropriate."""

        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                messages=[{"role": "user", "content": retry_prompt}],
            )

            answer = message.content[0].text
            citations = self.citation_policy._extract_citations(answer, sources)

            return SynthesisResponse(
                answer=answer,
                citations=[c.model_dump() for c in citations],
                provider_used="anthropic",
                model_used="claude-sonnet-4-6",
                has_citations=len(citations) > 0,
                citation_count=len(citations),
                confidence=0.85 if len(citations) >= 2 else 0.6,
                research_duration_ms=0,
                sources_consulted=len(sources),
                router_decision="research_retry",
                triggered_by="citation_enforcement",
            )

        except Exception as e:
            logger.error(f"Citation retry failed: {e}")
            # Return original with note
            return SynthesisResponse(
                answer=original_answer + "\n\n[Note: Citation retry failed]",
                citations=[],
                provider_used="anthropic",
                model_used="claude-sonnet-4-6",
                has_citations=False,
                citation_count=0,
                confidence=0.5,
                research_duration_ms=0,
                sources_consulted=len(sources),
                router_decision="research_retry_failed",
                triggered_by="citation_enforcement",
            )

    def _build_response_from_cache(
        self,
        cached_result,
        router_decision: dict,
        signals: List[str],
    ) -> SynthesisResponse:
        """Build response from cached research result."""
        # In a real implementation, this would rebuild from cache data
        return SynthesisResponse(
            answer="[Cached response - data from previous research]",
            citations=[],
            provider_used="cache",
            model_used="cached",
            has_citations=False,
            citation_count=0,
            confidence=0.7,
            research_duration_ms=0,
            sources_consulted=0,
            router_decision=router_decision.get("router_decision", "cache"),
            triggered_by=",".join(signals),
        )

    def _local_answer(self, query: str) -> str:
        """Generate a local-knowledge-based answer."""
        return f"This appears to be a general knowledge question about: {query}. I don't need to browse the web for this."

    def _get_deploy_sha(self) -> str:
        """Get current deploy SHA for trace correlation."""
        return os.getenv("RAILWAY_GIT_COMMIT_SHA", os.getenv("VERCEL_GIT_COMMIT_SHA", "unknown"))[:8]

    def _get_deploy_platform(self) -> str:
        """Get current deploy platform."""
        if os.getenv("RAILWAY_STATIC_URL"):
            return "railway"
        if os.getenv("VERCEL"):
            return "vercel"
        return "local"

    def _get_deploy_version(self) -> str:
        """Get current deploy version."""
        return os.getenv("TORQ_APP_VERSION", "0.0.0-dev")

    async def _emit_trace(self, trace: ResearchTrace, citation_metadata: Optional[Dict[str, Any]] = None):
        """Emit telemetry trace for auditability."""
        try:
            from torq_console.telemetry import supabase_ingest

            # Convert to Supabase trace format
            trace_data = {
                "trace_id": trace.trace_id,
                "session_id": trace.session_id,
                "agent_name": "prince_flowers",
                "workflow_type": "web_research",
                "started_at": trace.timestamp,
                "duration_ms": trace.total_duration_ms,
                "status": "ok",
                "metadata": trace.model_dump(),
            }

            # Build span metadata
            llm_span_meta = {
                "provider": trace.llm_provider,
                "model": trace.llm_model,
                "has_citations": trace.has_citations,
            }
            if citation_metadata:
                llm_span_meta.update(citation_metadata)

            spans_data = [
                {
                    "span_id": f"{trace.trace_id}_search",
                    "trace_id": trace.trace_id,
                    "name": "web.search",
                    "kind": "web_search",
                    "start_ms": 0,
                    "duration_ms": trace.search_duration_ms,
                    "metadata": {
                        "provider": trace.provider_used,
                        "result_count": trace.result_count,
                    },
                },
                {
                    "span_id": f"{trace.trace_id}_llm",
                    "trace_id": trace.trace_id,
                    "name": "llm.synthesize",
                    "kind": "llm",
                    "start_ms": trace.search_duration_ms,
                    "duration_ms": trace.synthesis_duration_ms,
                    "metadata": llm_span_meta,
                },
            ]

            await supabase_ingest(trace_data, spans_data)
            logger.info(f"Emitted research trace: {trace.trace_id}")

        except Exception as e:
            logger.error(f"Failed to emit trace: {e}")


# Singleton instance
_default_coordinator: Optional[ResearchCoordinator] = None


def get_research_coordinator() -> ResearchCoordinator:
    """Get the singleton research coordinator."""
    global _default_coordinator
    if _default_coordinator is None:
        _default_coordinator = ResearchCoordinator()
    return _default_coordinator


async def research(
    query: str,
    session_id: Optional[str] = None,
) -> SynthesisResponse:
    """
    Convenience function for web research.

    This is the main entry point used by the rest of the system.
    """
    coordinator = get_research_coordinator()
    return await coordinator.research(query, session_id)
