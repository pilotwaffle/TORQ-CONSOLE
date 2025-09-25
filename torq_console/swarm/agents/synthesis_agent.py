"""
Synthesis Agent for Swarm Intelligence System.
Combines information from multiple sources and creates coherent summaries.
"""

import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime


class SynthesisAgent:
    """Specialized agent for synthesizing information from multiple sources."""

    def __init__(self, llm_provider=None):
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(__name__)
        self.agent_id = "synthesis_agent"
        self.capabilities = ["information_synthesis", "summary_generation", "content_integration", "key_insights"]

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process synthesis task and create integrated response."""
        query = task.get('query', '')
        analyzed_results = task.get('analyzed_results', {})
        context = task.get('context', {})

        self.logger.info(f"SynthesisAgent synthesizing information for: {query}")

        # Synthesize the analyzed results
        synthesized_info = await self._synthesize_information(analyzed_results, query, context)

        return {
            'agent_id': self.agent_id,
            'query': query,
            'synthesized_info': synthesized_info,
            'context': context,
            'next_agent': 'response_agent',
            'timestamp': datetime.now().isoformat(),
            'handoff_reason': 'synthesis_complete_needs_formatting'
        }

    async def _synthesize_information(self, analyzed_results: Dict[str, Any], query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize analyzed results into coherent information."""
        filtered_results = analyzed_results.get('filtered_results', [])

        if not filtered_results:
            return {
                'key_insights': [],
                'summary': f"I wasn't able to find specific current information about '{query}'. This could be due to search limitations or the query requiring very recent data.",
                'sources_count': 0,
                'synthesis_method': 'empty_results'
            }

        # Extract key insights
        key_insights = await self._extract_key_insights(filtered_results, query)

        # Generate summary
        summary = await self._generate_summary(filtered_results, query, key_insights)

        # Identify sources
        sources = await self._identify_sources(filtered_results)

        return {
            'key_insights': key_insights,
            'summary': summary,
            'sources': sources,
            'sources_count': len(sources),
            'synthesis_method': 'multi_source_integration'
        }

    async def _extract_key_insights(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Extract key insights from search results."""
        insights = []

        for result in results[:3]:  # Focus on top 3 results
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            relevance_score = result.get('relevance_score', 0)

            insight = {
                'source': title,
                'content': snippet[:200] + '...' if len(snippet) > 200 else snippet,
                'relevance': relevance_score,
                'type': await self._classify_insight(snippet)
            }
            insights.append(insight)

        return insights

    async def _classify_insight(self, content: str) -> str:
        """Classify the type of insight based on content."""
        content_lower = content.lower()

        if any(word in content_lower for word in ['news', 'announced', 'today', 'recent']):
            return 'news_update'
        elif any(word in content_lower for word in ['research', 'study', 'paper', 'findings']):
            return 'research_finding'
        elif any(word in content_lower for word in ['trend', 'market', 'growth', 'industry']):
            return 'market_trend'
        elif any(word in content_lower for word in ['technology', 'innovation', 'breakthrough']):
            return 'technology_development'
        else:
            return 'general_information'

    async def _generate_summary(self, results: List[Dict[str, Any]], query: str, insights: List[Dict[str, Any]]) -> str:
        """Generate a coherent summary from the results."""
        if not results:
            return f"I wasn't able to find current information about '{query}'."

        # Create summary based on insights
        summary_parts = []

        # Introduction
        summary_parts.append(f"Based on my search for '{query}', here's what I found:")

        # Key findings
        if insights:
            summary_parts.append("\nKey findings:")
            for i, insight in enumerate(insights[:3], 1):
                insight_type = insight['type'].replace('_', ' ').title()
                content = insight['content']
                summary_parts.append(f"{i}. {insight_type}: {content}")

        # Context about limitations
        summary_parts.append(f"\nPlease note: This information is based on available search results. For the most current and comprehensive information about '{query}', I recommend checking official sources and recent publications directly.")

        return "\n".join(summary_parts)

    async def _identify_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify and organize sources from results."""
        sources = []

        for result in results:
            source = {
                'title': result.get('title', 'Unknown Title'),
                'url': result.get('url', ''),
                'relevance_score': result.get('relevance_score', 0),
                'analysis_notes': result.get('analysis_notes', ''),
                'source_type': result.get('source', 'web_search')
            }
            sources.append(source)

        return sources

    async def get_capabilities(self) -> List[str]:
        return self.capabilities

    async def get_status(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'capabilities': self.capabilities,
            'llm_provider_available': self.llm_provider is not None
        }