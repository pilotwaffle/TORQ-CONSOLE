"""
Research Agent - Unified research and information gathering capability.

Consolidates all research-focused agents (web search, data analysis,
information extraction, etc.) into a single, powerful research agent.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from .base_agent import BaseAgent, AgentCapability, AgentContext, AgentResult
from .interfaces import IResearchAgent, SearchScope, ResearchQuery
from .capabilities import ResearchCapability, CapabilityFactory
from ..registry import register_agent


class ResearchAgent(BaseAgent, IResearchAgent):
    """
    Unified research agent that consolidates all research-focused functionality.

    Replaces multiple scattered research agents:
    - Web search agents
    - Data analysis agents
    - Information extraction agents
    - Research specialist agents
    - WebSearch integration agents

    Features:
    - Multiple search scopes (web, local, codebase, documentation)
    - Information extraction and summarization
    - Source verification and quality assessment
    - Research result caching
    - Advanced search filtering
    """

    def __init__(
        self,
        llm_provider=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize research agent."""
        super().__init__(
            agent_id="research_agent",
            agent_name="Research Agent",
            capabilities=[
                AgentCapability.RESEARCH,
                AgentCapability.WEB_SEARCH,
                AgentCapability.DATA_ANALYSIS,
                AgentCapability.RESEARCH
            ],
            llm_provider=llm_provider,
            config=config
        )

        # Initialize research capabilities
        self._capabilities: Dict[str, Any] = {}
        self._init_capabilities()

        # Research state and caching
        self._research_cache: Dict[str, Dict[str, Any]] = {}
        self._max_cache_size = self.config.get("max_cache_size", 100)
        self._cache_ttl = self.config.get("cache_ttl", 3600)  # 1 hour

        # Search configuration
        self._max_results = self.config.get("max_results", 10)
        self._default_scope = self.config.get("default_scope", SearchScope.WEB)
        self._quality_threshold = self.config.get("quality_threshold", 0.7)

        # Source management
        self._trusted_sources = self.config.get("trusted_sources", [])
        self._blocked_sources = self.config.get("blocked_sources", [])

        self.logger.info("ResearchAgent initialized with multiple research capabilities")

    def _init_capabilities(self) -> None:
        """Initialize research capabilities."""
        capability_configs = self.config.get("capability_configs", {})

        # Initialize research capability
        if AgentCapability.RESEARCH in CapabilityFactory.get_available_capabilities():
            self._capabilities[AgentCapability.RESEARCH] = (
                CapabilityFactory.create_capability(
                    AgentCapability.RESEARCH,
                    capability_configs.get(AgentCapability.RESEARCH, {})
                )
            )
            self.logger.debug("Initialized research capability")

    async def _execute_request(
        self,
        request: str,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute research request."""
        # Create research query
        research_query = ResearchQuery(
            query=request,
            scope=self._default_scope,
            max_results=self._max_results
        )

        # Execute search
        return await self.search(research_query, context)

    async def search(
        self,
        query: ResearchQuery,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Perform a search operation."""
        # Check cache first
        cache_key = self._generate_cache_key(query)
        cached_result = self._get_from_cache(cache_key)

        if cached_result:
            self.logger.debug(f"Using cached result for query: {query.query}")
            cached_result.metadata["from_cache"] = True
            return cached_result

        start_time = asyncio.get_event_loop().time()

        try:
            # Validate query
            if not await self._validate_query(query):
                return AgentResult(
                    success=False,
                    content="Invalid research query. Please check your search terms and parameters.",
                    error="Invalid query"
                )

            # Perform search based on scope
            raw_results = await self._perform_search_by_scope(query)

            # Process and filter results
            processed_results = await self._process_search_results(raw_results, query)

            # Quality assessment
            quality_results = await self._assess_result_quality(processed_results)

            # Generate summary
            summary = await self._generate_search_summary(query, quality_results)

            # Extract insights
            insights = await self._extract_insights(quality_results, "search")

            execution_time = asyncio.get_event_loop().time() - start_time

            result = AgentResult(
                success=True,
                content=summary,
                confidence=self._calculate_overall_confidence(quality_results),
                execution_time=execution_time,
                metadata={
                    "query": query.query,
                    "scope": query.scope,
                    "results_count": len(quality_results),
                    "insights": insights,
                    "sources": [r.get("source", "unknown") for r in quality_results],
                    "quality_scores": [r.get("quality_score", 0.0) for r in quality_results]
                }
            )

            # Cache the result
            self._add_to_cache(cache_key, result)

            return result

        except Exception as e:
            self.logger.error(f"Search error: {e}", exc_info=True)
            return AgentResult(
                success=False,
                content="I encountered an error while performing the search.",
                error=str(e)
            )

    async def _validate_query(self, query: ResearchQuery) -> bool:
        """Validate research query."""
        if not query.query or len(query.query.strip()) < 2:
            return False

        if query.max_results < 1 or query.max_results > 100:
            return False

        # Check for blocked terms
        blocked_terms = self.config.get("blocked_terms", [])
        query_lower = query.query.lower()
        for term in blocked_terms:
            if term.lower() in query_lower:
                return False

        return True

    async def _perform_search_by_scope(self, query: ResearchQuery) -> List[Dict[str, Any]]:
        """Perform search based on scope."""
        if AgentCapability.RESEARCH in self._capabilities:
            return await self._capabilities[AgentCapability.RESEARCH].execute(
                query=query.query,
                scope=query.scope,
                max_results=query.max_results,
                context=None  # Context not needed for capability
            )
        else:
            # Fallback implementation
            return await self._fallback_search(query)

    async def _fallback_search(self, query: ResearchQuery) -> List[Dict[str, Any]]:
        """Fallback search implementation."""
        # This would integrate with actual search APIs in a real implementation
        mock_results = [
            {
                "title": f"Search result {i+1} for '{query.query}'",
                "content": f"This is a mock search result content for: {query.query}",
                "url": f"https://example.com/result{i+1}",
                "source": "mock_search_engine",
                "relevance": 0.9 - (i * 0.1),
                "timestamp": asyncio.get_event_loop().time()
            }
            for i in range(min(query.max_results, 5))
        ]

        return mock_results

    async def _process_search_results(
        self,
        raw_results: List[Dict[str, Any]],
        query: ResearchQuery
    ) -> List[Dict[str, Any]]:
        """Process and filter search results."""
        processed_results = []

        for result in raw_results:
            # Filter by trusted/blocked sources
            source = result.get("source", "")
            if self._blocked_sources and source in self._blocked_sources:
                continue

            # Apply additional processing
            processed_result = {
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "url": result.get("url", ""),
                "source": source,
                "relevance": result.get("relevance", 0.5),
                "timestamp": result.get("timestamp", 0),
                "metadata": result.get("metadata", {})
            }

            # Apply content filters if specified
            if query.filters:
                if self._passes_filters(processed_result, query.filters):
                    processed_results.append(processed_result)
            else:
                processed_results.append(processed_result)

        return processed_results

    def _passes_filters(self, result: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if result passes all filters."""
        # Time range filter
        if "time_range" in filters:
            time_range = filters["time_range"]
            if result["timestamp"] < time_range[0] or result["timestamp"] > time_range[1]:
                return False

        # Source filter
        if "sources" in filters and result["source"] not in filters["sources"]:
            return False

        # Relevance threshold
        if "min_relevance" in filters and result["relevance"] < filters["min_relevance"]:
            return False

        return True

    async def _assess_result_quality(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assess quality of search results."""
        quality_results = []

        for result in results:
            quality_score = await self._calculate_quality_score(result)
            result["quality_score"] = quality_score

            # Filter by quality threshold
            if quality_score >= self._quality_threshold:
                quality_results.append(result)

        # Sort by quality score
        quality_results.sort(key=lambda x: x["quality_score"], reverse=True)

        return quality_results

    async def _calculate_quality_score(self, result: Dict[str, Any]) -> float:
        """Calculate quality score for a result."""
        score = 0.0

        # Relevance score (40% weight)
        score += result.get("relevance", 0.0) * 0.4

        # Source trustworthiness (30% weight)
        source = result.get("source", "")
        if self._trusted_sources and source in self._trusted_sources:
            score += 0.3
        elif source in ["github", "stackoverflow", "documentation"]:
            score += 0.2
        else:
            score += 0.1

        # Content quality (20% weight)
        content = result.get("content", "")
        if len(content) > 100:  # Substantial content
            score += 0.2
        elif len(content) > 50:
            score += 0.1

        # Title clarity (10% weight)
        title = result.get("title", "")
        if title and len(title) > 10:
            score += 0.1

        return min(score, 1.0)  # Cap at 1.0

    async def _generate_search_summary(
        self,
        query: ResearchQuery,
        results: List[Dict[str, Any]]
    ) -> str:
        """Generate summary of search results."""
        if not results:
            return f"No results found for query: '{query.query}'"

        summary_parts = [
            f"Found {len(results)} high-quality results for '{query.query}':\n"
        ]

        for i, result in enumerate(results[:5], 1):  # Top 5 results
            summary_parts.append(
                f"{i}. **{result['title']}**\n"
                f"   {result['content'][:200]}{'...' if len(result['content']) > 200 else ''}\n"
                f"   Source: {result['source']} (Quality: {result['quality_score']:.2f})\n"
                f"   URL: {result['url']}\n"
            )

        if len(results) > 5:
            summary_parts.append(f"\n... and {len(results) - 5} more results")

        return "\n".join(summary_parts)

    async def summarize_results(
        self,
        results: List[Dict[str, Any]],
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """Summarize search results."""
        if not results:
            return "No results to summarize"

        if focus_areas:
            # Filter results by focus areas
            filtered_results = []
            for result in results:
                content_lower = result.get("content", "").lower()
                title_lower = result.get("title", "").lower()
                if any(area.lower() in content_lower or area.lower() in title_lower for area in focus_areas):
                    filtered_results.append(result)
            results = filtered_results

        # Generate summary
        return await self._generate_search_summary(
            ResearchQuery(query="summary", scope=SearchScope.WEB),
            results
        )

    async def extract_insights(
        self,
        data: Union[str, List[Dict[str, Any]]],
        insights_type: str = "general"
    ) -> List[str]:
        """Extract insights from data."""
        if isinstance(data, str):
            # Extract insights from text
            return await self._extract_text_insights(data, insights_type)
        elif isinstance(data, list):
            # Extract insights from structured data
            return await self._extract_structured_insights(data, insights_type)
        else:
            return []

    async def _extract_text_insights(self, text: str, insights_type: str) -> List[str]:
        """Extract insights from text data."""
        insights = []

        if insights_type == "search":
            # Search-specific insights
            if "error" in text.lower() or "problem" in text.lower():
                insights.append("Content mentions potential issues or problems")

            if "solution" in text.lower() or "fix" in text.lower():
                insights.append("Content provides solutions or fixes")

            if "tutorial" in text.lower() or "guide" in text.lower():
                insights.append("Content appears to be educational or instructional")

        elif insights_type == "trends":
            # Trend analysis insights
            words = text.lower().split()
            common_words = {}
            for word in words:
                if len(word) > 4:  # Filter out short words
                    common_words[word] = common_words.get(word, 0) + 1

            top_words = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:3]
            for word, count in top_words:
                insights.append(f"Frequent topic: '{word}' ({count} mentions)")

        else:
            # General insights
            if len(text) > 1000:
                insights.append("Comprehensive content with detailed information")
            elif len(text) > 500:
                insights.append("Moderately detailed content")
            else:
                insights.append("Brief or summary content")

        return insights

    async def _extract_structured_insights(
        self,
        data: List[Dict[str, Any]],
        insights_type: str
    ) -> List[str]:
        """Extract insights from structured data."""
        insights = []

        if insights_type == "search":
            # Search results insights
            sources = {}
            for item in data:
                source = item.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1

            if sources:
                top_source = max(sources.items(), key=lambda x: x[1])
                insights.append(f"Most common source: {top_source[0]} ({top_source[1]} results)")

            # Average quality
            quality_scores = [item.get("quality_score", 0) for item in data if "quality_score" in item]
            if quality_scores:
                avg_quality = sum(quality_scores) / len(quality_scores)
                insights.append(f"Average result quality: {avg_quality:.2f}")

        return insights

    def _calculate_overall_confidence(self, results: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in search results."""
        if not results:
            return 0.0

        # Weight by quality scores
        total_weight = 0.0
        weighted_confidence = 0.0

        for result in results:
            quality = result.get("quality_score", 0.5)
            relevance = result.get("relevance", 0.5)
            confidence = (quality + relevance) / 2

            weighted_confidence += confidence * quality
            total_weight += quality

        if total_weight > 0:
            return weighted_confidence / total_weight

        return sum(r.get("quality_score", 0.5) for r in results) / len(results)

    def _generate_cache_key(self, query: ResearchQuery) -> str:
        """Generate cache key for query."""
        import hashlib
        key_data = f"{query.query}:{query.scope}:{query.max_results}:{query.filters}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[AgentResult]:
        """Get result from cache if available and not expired."""
        if cache_key not in self._research_cache:
            return None

        cached_item = self._research_cache[cache_key]
        current_time = asyncio.get_event_loop().time()

        if current_time - cached_item["timestamp"] > self._cache_ttl:
            # Cache expired
            del self._research_cache[cache_key]
            return None

        return cached_item["result"]

    def _add_to_cache(self, cache_key: str, result: AgentResult) -> None:
        """Add result to cache."""
        self._research_cache[cache_key] = {
            "result": result,
            "timestamp": asyncio.get_event_loop().time()
        }

        # Maintain cache size limit
        if len(self._research_cache) > self._max_cache_size:
            # Remove oldest entries
            oldest_keys = sorted(
                self._research_cache.keys(),
                key=lambda k: self._research_cache[k]["timestamp"]
            )[:len(self._research_cache) - self._max_cache_size]

            for key in oldest_keys:
                del self._research_cache[key]

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = asyncio.get_event_loop().time()
        expired_count = sum(
            1 for item in self._research_cache.values()
            if current_time - item["timestamp"] > self._cache_ttl
        )

        return {
            "total_cached": len(self._research_cache),
            "expired": expired_count,
            "active": len(self._research_cache) - expired_count,
            "max_size": self._max_cache_size,
            "ttl": self._cache_ttl
        }

    async def _health_check_impl(self) -> bool:
        """Agent-specific health check."""
        try:
            # Test a simple search
            test_query = ResearchQuery(
                query="health check test",
                scope=SearchScope.WEB,
                max_results=1
            )

            result = await self.search(test_query)
            return result.success

        except Exception as e:
            self.logger.error(f"Research agent health check failed: {e}")
            return False

    async def _reset_impl(self) -> None:
        """Reset agent-specific state."""
        # Clear cache
        self._research_cache.clear()

        # Reset capabilities
        for capability in self._capabilities.values():
            if hasattr(capability, 'reset'):
                try:
                    if asyncio.iscoroutinefunction(capability.reset):
                        await capability.reset()
                    else:
                        capability.reset()
                except Exception as e:
                    self.logger.error(f"Failed to reset capability: {e}")

    def get_agent_info(self) -> Dict[str, Any]:
        """Get detailed agent information."""
        base_info = super().get_agent_info() if hasattr(super(), 'get_agent_info') else {}

        research_info = {
            "cache_stats": self.get_cache_stats(),
            "available_capabilities": list(self._capabilities.keys()),
            "max_results": self._max_results,
            "default_scope": self._default_scope,
            "quality_threshold": self._quality_threshold,
            "trusted_sources_count": len(self._trusted_sources),
            "blocked_sources_count": len(self._blocked_sources)
        }

        if base_info:
            base_info.update(research_info)
            return base_info

        return research_info


# Register the agent
register_agent(
    ResearchAgent,
    "research_agent",
    "Research Agent",
    [
        AgentCapability.RESEARCH,
        AgentCapability.WEB_SEARCH,
        AgentCapability.DATA_ANALYSIS
    ],
    config={
        "max_results": 10,
        "max_cache_size": 100,
        "cache_ttl": 3600,
        "default_scope": "web",
        "quality_threshold": 0.7,
        "trusted_sources": ["github", "stackoverflow", "documentation"],
        "blocked_sources": [],
        "blocked_terms": ["spam", "illegal"]
    },
    metadata={
        "description": "Unified research agent that consolidates all research-focused functionality",
        "replaces": [
            "web_search_agents",
            "data_analysis_agents",
            "research_specialists",
            "information_extraction_agents"
        ],
        "features": [
            "Multiple search scopes",
            "Result quality assessment",
            "Research caching",
            "Source filtering",
            "Insight extraction"
        ]
    }
)