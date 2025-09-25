"""
Analysis Agent for Swarm Intelligence System.
Processes and filters search results.
"""

import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime


class AnalysisAgent:
    """Specialized agent for analyzing and filtering search results."""

    def __init__(self, llm_provider=None):
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(__name__)
        self.agent_id = "analysis_agent"
        self.capabilities = ["result_filtering", "relevance_scoring", "content_analysis", "fact_checking"]

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process analysis task and return filtered results."""
        query = task.get('query', '')
        results = task.get('results', {})
        context = task.get('context', {})

        self.logger.info(f"AnalysisAgent analyzing results for: {query}")

        # Analyze search results
        analyzed_results = await self._analyze_search_results(results, query, context)

        return {
            'agent_id': self.agent_id,
            'query': query,
            'analyzed_results': analyzed_results,
            'context': context,
            'next_agent': 'synthesis_agent',
            'timestamp': datetime.now().isoformat(),
            'handoff_reason': 'analysis_complete_needs_synthesis'
        }

    async def _analyze_search_results(self, results: Dict[str, Any], query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and filter search results."""
        search_results = results.get('search_results', {})
        raw_results = search_results.get('results', [])

        if not raw_results:
            return {
                'filtered_results': [],
                'analysis_summary': 'No results to analyze',
                'relevance_scores': {}
            }

        # Filter and score results
        filtered_results = []
        relevance_scores = {}

        for i, result in enumerate(raw_results):
            score = await self._calculate_relevance_score(result, query)
            relevance_scores[i] = score

            # Only include results above threshold
            if score >= 0.3:  # 30% relevance threshold
                filtered_results.append({
                    **result,
                    'relevance_score': score,
                    'analysis_notes': await self._generate_analysis_notes(result, query)
                })

        # Sort by relevance
        filtered_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        return {
            'filtered_results': filtered_results[:5],  # Top 5 results
            'total_analyzed': len(raw_results),
            'total_relevant': len(filtered_results),
            'analysis_summary': f"Analyzed {len(raw_results)} results, found {len(filtered_results)} relevant items",
            'relevance_scores': relevance_scores
        }

    async def _calculate_relevance_score(self, result: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for a search result."""
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        query_terms = query.lower().split()

        score = 0.0
        total_terms = len(query_terms)

        if total_terms == 0:
            return 0.5  # Default score for empty query

        # Check title matches
        title_matches = sum(1 for term in query_terms if term in title)
        score += (title_matches / total_terms) * 0.6  # Title weight: 60%

        # Check snippet matches
        snippet_matches = sum(1 for term in query_terms if term in snippet)
        score += (snippet_matches / total_terms) * 0.4  # Snippet weight: 40%

        return min(score, 1.0)  # Cap at 1.0

    async def _generate_analysis_notes(self, result: Dict[str, Any], query: str) -> str:
        """Generate analysis notes for a result."""
        title = result.get('title', '')
        snippet = result.get('snippet', '')

        # Simple analysis
        notes = []
        if 'news' in snippet.lower() or 'today' in snippet.lower():
            notes.append("Recent/News content")
        if 'official' in snippet.lower() or 'announcement' in snippet.lower():
            notes.append("Official source")
        if any(term in snippet.lower() for term in ['research', 'study', 'paper']):
            notes.append("Research/Academic content")

        return "; ".join(notes) if notes else "General content"

    async def get_capabilities(self) -> List[str]:
        return self.capabilities

    async def get_status(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'capabilities': self.capabilities,
            'llm_provider_available': self.llm_provider is not None
        }