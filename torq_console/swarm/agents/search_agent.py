"""
Search Agent for Swarm Intelligence System.

This agent specializes in information retrieval and web searching.
It handles different types of queries and coordinates with search providers.
"""

import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime


class SearchAgent:
    """Specialized agent for search operations."""

    def __init__(self, web_search_provider=None, llm_provider=None):
        """
        Initialize SearchAgent.

        Args:
            web_search_provider: WebSearch provider instance
            llm_provider: LLM provider for query enhancement
        """
        self.web_search_provider = web_search_provider
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(__name__)

        # Agent specialization
        self.agent_id = "search_agent"
        self.capabilities = [
            "web_search",
            "query_enhancement",
            "information_retrieval",
            "context_gathering"
        ]

        # Search history for context
        self.search_history = []
        self.max_history = 10

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a search task and return results.

        Args:
            task: Task dictionary with query and parameters

        Returns:
            Task results with search data and next agent handoff
        """
        task_type = task.get('type', 'general_search')
        query = task.get('query', '')
        context = task.get('context', {})

        self.logger.info(f"SearchAgent processing {task_type} task: {query}")

        # Route to appropriate search method
        if task_type == 'ai_news_search':
            results = await self._search_ai_news(query, context)
        elif task_type == 'recent_developments':
            results = await self._search_recent_developments(query, context)
        elif task_type == 'general_search':
            results = await self._general_search(query, context)
        else:
            results = await self._fallback_search(query, context)

        # Update search history
        self._update_search_history(query, results)

        # Prepare handoff to AnalysisAgent
        return {
            'agent_id': self.agent_id,
            'task_type': task_type,
            'query': query,
            'results': results,
            'context': context,
            'next_agent': 'analysis_agent',
            'timestamp': datetime.now().isoformat(),
            'handoff_reason': 'search_complete_needs_analysis'
        }

    async def _search_ai_news(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search for AI-related news and developments."""
        enhanced_query = await self._enhance_ai_query(query)

        if self.web_search_provider:
            try:
                search_results = await self.web_search_provider.search_ai_news(enhanced_query)
                return {
                    'source': 'web_search',
                    'enhanced_query': enhanced_query,
                    'search_results': search_results,
                    'success': True
                }
            except Exception as e:
                self.logger.error(f"AI news search failed: {e}")
                return await self._fallback_ai_response(query, str(e))
        else:
            return await self._fallback_ai_response(query, "No web search provider available")

    async def _search_recent_developments(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search for recent developments on a topic."""
        days_back = context.get('days_back', 7)

        if self.web_search_provider:
            try:
                search_results = await self.web_search_provider.search_recent_developments(query, days_back)
                return {
                    'source': 'web_search',
                    'search_results': search_results,
                    'days_back': days_back,
                    'success': True
                }
            except Exception as e:
                self.logger.error(f"Recent developments search failed: {e}")
                return await self._fallback_response(query, str(e))
        else:
            return await self._fallback_response(query, "No web search provider available")

    async def _general_search(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform general web search."""
        if self.web_search_provider:
            try:
                search_results = await self.web_search_provider.search(query)
                return {
                    'source': 'web_search',
                    'search_results': search_results,
                    'success': True
                }
            except Exception as e:
                self.logger.error(f"General search failed: {e}")
                return await self._fallback_response(query, str(e))
        else:
            return await self._fallback_response(query, "No web search provider available")

    async def _fallback_search(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback search method when others fail."""
        return await self._fallback_response(query, "Unknown search type")

    async def _enhance_ai_query(self, query: str) -> str:
        """Enhance AI-related queries with relevant terms."""
        ai_terms = [
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "AI technology",
            "neural networks"
        ]

        # Simple enhancement - add AI context if not present
        query_lower = query.lower()
        if not any(term in query_lower for term in ai_terms):
            query = f"{query} artificial intelligence AI technology"

        return query

    async def _fallback_ai_response(self, query: str, error: str) -> Dict[str, Any]:
        """Generate fallback response for AI queries."""
        return {
            'source': 'fallback',
            'success': False,
            'error': error,
            'search_results': {
                'query': query,
                'results': [
                    {
                        'title': 'AI News Search Assistance',
                        'snippet': f'I encountered an issue while searching for "{query}". '
                                  'For the latest AI news, I recommend checking these reliable sources:\n\n'
                                  '• TechCrunch AI: Latest AI and machine learning developments\n'
                                  '• MIT Technology Review: In-depth AI analysis and research\n'
                                  '• OpenAI Blog: Updates from OpenAI\n'
                                  '• Google AI Blog: Google DeepMind developments\n'
                                  '• Anthropic: Claude and AI safety research\n'
                                  '• VentureBeat AI: AI business and industry news\n\n'
                                  'Recent major developments in AI include advances in large language models, '
                                  'improvements in AI safety research, new applications in various industries, '
                                  'and ongoing discussions about AI regulation and governance.',
                        'url': '',
                        'source': 'assistant_guidance',
                        'timestamp': datetime.now().isoformat()
                    }
                ],
                'total_found': 1,
                'method_used': 'fallback'
            }
        }

    async def _fallback_response(self, query: str, error: str) -> Dict[str, Any]:
        """Generate general fallback response."""
        return {
            'source': 'fallback',
            'success': False,
            'error': error,
            'search_results': {
                'query': query,
                'results': [
                    {
                        'title': 'Search Assistance',
                        'snippet': f'I encountered an issue while searching for "{query}". '
                                  f'Error: {error}\n\n'
                                  'For the most current information, I recommend:\n'
                                  '• Checking official websites and news sources\n'
                                  '• Using search engines like Google or Bing\n'
                                  '• Looking at recent academic papers or reports\n'
                                  '• Consulting industry-specific databases',
                        'url': '',
                        'source': 'assistant_guidance',
                        'timestamp': datetime.now().isoformat()
                    }
                ],
                'total_found': 1,
                'method_used': 'fallback'
            }
        }

    def _update_search_history(self, query: str, results: Dict[str, Any]):
        """Update search history for context."""
        history_entry = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'success': results.get('success', False),
            'results_count': len(results.get('search_results', {}).get('results', []))
        }

        self.search_history.append(history_entry)

        # Trim history if too long
        if len(self.search_history) > self.max_history:
            self.search_history = self.search_history[-self.max_history:]

    async def get_capabilities(self) -> List[str]:
        """Return agent capabilities."""
        return self.capabilities

    async def get_status(self) -> Dict[str, Any]:
        """Return agent status."""
        return {
            'agent_id': self.agent_id,
            'capabilities': self.capabilities,
            'search_history_count': len(self.search_history),
            'web_search_available': self.web_search_provider is not None,
            'llm_provider_available': self.llm_provider is not None
        }