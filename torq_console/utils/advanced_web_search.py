"""
Advanced Web Search Engine for TORQ Console - Multi-Provider Search.

Provides enhanced web search capabilities with multiple search engines,
result ranking, filtering, and semantic search integration.
"""

import asyncio
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import hashlib
import time

import httpx


class SearchEngine(Enum):
    """Supported search engines."""
    DUCKDUCKGO = "duckduckgo"
    SEARX = "searx"
    BRAVE = "brave"
    BING = "bing"
    GOOGLE_CUSTOM = "google_custom"


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str
    engine: str
    rank: int = 0
    relevance_score: float = 0.0
    date_published: Optional[datetime] = None
    domain: str = ""
    image_url: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.domain and self.url:
            try:
                from urllib.parse import urlparse
                self.domain = urlparse(self.url).netloc
            except:
                self.domain = ""


@dataclass
class SearchQuery:
    """Represents a search query with parameters."""
    query: str
    engines: List[SearchEngine] = None
    max_results: int = 10
    language: str = "en"
    region: str = "us"
    time_range: Optional[str] = None  # day, week, month, year
    safe_search: str = "moderate"  # strict, moderate, off
    result_type: str = "general"  # general, images, videos, news

    def __post_init__(self):
        if self.engines is None:
            self.engines = [SearchEngine.DUCKDUCKGO]


class AdvancedWebSearchEngine:
    """
    Advanced multi-provider web search engine with ranking and filtering.

    Features:
    - Multiple search engine support (DuckDuckGo, Brave, Bing, etc.)
    - Result ranking and deduplication
    - Semantic search and relevance scoring
    - Search result caching and optimization
    - Rate limiting and error handling
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # HTTP client with proper headers
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )

        # Search engine configurations
        self.engine_configs = {
            SearchEngine.DUCKDUCKGO: {
                'base_url': 'https://api.duckduckgo.com/',
                'rate_limit': 1.0,  # seconds between requests
                'enabled': True
            },
            SearchEngine.SEARX: {
                'base_url': 'https://searx.org/',
                'rate_limit': 0.5,
                'enabled': True
            },
            SearchEngine.BRAVE: {
                'base_url': 'https://search.brave.com/',
                'rate_limit': 1.5,
                'enabled': False  # Requires API key
            }
        }

        # Result caching
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)

        # Rate limiting
        self.last_requests = {}

    async def search(
        self,
        query: Union[str, SearchQuery],
        engines: Optional[List[str]] = None,
        max_results: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform multi-engine web search with result aggregation.

        Args:
            query: Search query string or SearchQuery object
            engines: List of search engines to use
            max_results: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            Dict with aggregated search results
        """
        start_time = time.time()

        # Convert string query to SearchQuery object
        if isinstance(query, str):
            search_query = SearchQuery(
                query=query,
                engines=[SearchEngine(engine) for engine in (engines or ["duckduckgo"])],
                max_results=max_results,
                **kwargs
            )
        else:
            search_query = query

        try:
            # Check cache first
            cache_key = self._get_cache_key(search_query)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return cached_result

            # Execute searches across multiple engines
            search_tasks = []
            for engine in search_query.engines:
                if self.engine_configs.get(engine, {}).get('enabled', False):
                    task = self._search_single_engine(engine, search_query)
                    search_tasks.append(task)

            if not search_tasks:
                return {
                    'success': False,
                    'error': 'No enabled search engines available',
                    'query': search_query.query,
                    'results': []
                }

            # Execute all searches concurrently
            engine_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # Process and aggregate results
            all_results = []
            engines_used = []
            engines_failed = []

            for i, result in enumerate(engine_results):
                engine = search_query.engines[i]
                if isinstance(result, Exception):
                    self.logger.warning(f"Search failed for {engine.value}: {result}")
                    engines_failed.append(engine.value)
                elif result and result.get('success'):
                    all_results.extend(result['results'])
                    engines_used.append(engine.value)
                else:
                    engines_failed.append(engine.value)

            # Rank and deduplicate results
            ranked_results = await self._rank_and_deduplicate(all_results, search_query)

            # Limit results
            final_results = ranked_results[:search_query.max_results]

            processing_time = time.time() - start_time

            result = {
                'success': True,
                'query': search_query.query,
                'engines_used': engines_used,
                'engines_failed': engines_failed,
                'total_results_found': len(all_results),
                'results_returned': len(final_results),
                'processing_time_ms': round(processing_time * 1000, 2),
                'results': [self._format_result(r) for r in final_results],
                'metadata': {
                    'search_engines': engines_used,
                    'language': search_query.language,
                    'region': search_query.region,
                    'safe_search': search_query.safe_search
                }
            }

            # Cache the result
            self._cache_result(cache_key, result)

            return result

        except Exception as e:
            self.logger.error(f"Advanced search failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': search_query.query if hasattr(search_query, 'query') else str(query),
                'results': [],
                'processing_time_ms': round((time.time() - start_time) * 1000, 2)
            }

    async def _search_single_engine(self, engine: SearchEngine, query: SearchQuery) -> Dict[str, Any]:
        """Search using a single search engine."""

        # Rate limiting
        await self._rate_limit(engine)

        try:
            if engine == SearchEngine.DUCKDUCKGO:
                return await self._search_duckduckgo(query)
            elif engine == SearchEngine.SEARX:
                return await self._search_searx(query)
            elif engine == SearchEngine.BRAVE:
                return await self._search_brave(query)
            else:
                return {'success': False, 'error': f'Engine {engine.value} not implemented'}

        except Exception as e:
            self.logger.error(f"Search failed for {engine.value}: {e}")
            return {'success': False, 'error': str(e)}

    async def _search_duckduckgo(self, query: SearchQuery) -> Dict[str, Any]:
        """Search using DuckDuckGo Instant Answer API."""
        try:
            # DuckDuckGo Instant Answer API
            params = {
                'q': query.query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }

            response = await self.client.get('https://api.duckduckgo.com/', params=params)
            data = response.json()

            results = []

            # Process instant answer
            if data.get('Answer'):
                results.append(SearchResult(
                    title=f"Direct Answer: {query.query}",
                    url=data.get('AnswerURL', ''),
                    snippet=data['Answer'],
                    engine='duckduckgo',
                    relevance_score=1.0
                ))

            # Process abstract
            if data.get('Abstract'):
                results.append(SearchResult(
                    title=data.get('Heading', 'Abstract'),
                    url=data.get('AbstractURL', ''),
                    snippet=data['Abstract'],
                    engine='duckduckgo',
                    relevance_score=0.9
                ))

            # Process related topics
            for topic in data.get('RelatedTopics', [])[:5]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append(SearchResult(
                        title=topic.get('Result', '').split(' - ')[0] if ' - ' in topic.get('Result', '') else 'Related',
                        url=topic.get('FirstURL', ''),
                        snippet=topic['Text'],
                        engine='duckduckgo',
                        relevance_score=0.7
                    ))

            return {
                'success': True,
                'engine': 'duckduckgo',
                'results': results
            }

        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _search_searx(self, query: SearchQuery) -> Dict[str, Any]:
        """Search using SearX meta-search engine."""
        try:
            # Try a few public SearX instances
            searx_instances = [
                'https://searx.org',
                'https://search.sapti.me',
                'https://searx.be'
            ]

            for instance in searx_instances:
                try:
                    params = {
                        'q': query.query,
                        'format': 'json',
                        'language': query.language,
                        'safesearch': '1' if query.safe_search == 'strict' else '0'
                    }

                    response = await self.client.get(f'{instance}/search', params=params)
                    if response.status_code == 200:
                        data = response.json()

                        results = []
                        for item in data.get('results', [])[:query.max_results]:
                            results.append(SearchResult(
                                title=item.get('title', ''),
                                url=item.get('url', ''),
                                snippet=item.get('content', ''),
                                engine='searx',
                                relevance_score=0.8
                            ))

                        return {
                            'success': True,
                            'engine': 'searx',
                            'results': results
                        }

                except Exception as e:
                    self.logger.debug(f"SearX instance {instance} failed: {e}")
                    continue

            return {'success': False, 'error': 'All SearX instances failed'}

        except Exception as e:
            self.logger.error(f"SearX search failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _search_brave(self, query: SearchQuery) -> Dict[str, Any]:
        """Search using Brave Search API (requires API key)."""
        # This would require Brave Search API key
        # Implementation placeholder
        return {'success': False, 'error': 'Brave Search requires API key configuration'}

    async def _rank_and_deduplicate(self, results: List[SearchResult], query: SearchQuery) -> List[SearchResult]:
        """Rank results by relevance and remove duplicates."""

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []

        for result in results:
            if result.url and result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        # Calculate relevance scores
        query_terms = set(query.query.lower().split())

        for result in unique_results:
            # Base score from engine
            score = result.relevance_score

            # Title relevance
            title_terms = set(result.title.lower().split())
            title_overlap = len(query_terms.intersection(title_terms))
            score += title_overlap * 0.3

            # Snippet relevance
            snippet_terms = set(result.snippet.lower().split())
            snippet_overlap = len(query_terms.intersection(snippet_terms))
            score += snippet_overlap * 0.2

            # Domain authority (simple heuristic)
            if any(domain in result.domain for domain in ['wikipedia.org', 'github.com', 'stackoverflow.com']):
                score += 0.2

            result.relevance_score = score

        # Sort by relevance score (descending)
        ranked_results = sorted(unique_results, key=lambda x: x.relevance_score, reverse=True)

        return ranked_results

    def _format_result(self, result: SearchResult) -> Dict[str, Any]:
        """Format search result for API response."""
        return {
            'title': result.title,
            'url': result.url,
            'snippet': result.snippet,
            'domain': result.domain,
            'engine': result.engine,
            'relevance_score': round(result.relevance_score, 3),
            'metadata': result.metadata
        }

    async def _rate_limit(self, engine: SearchEngine):
        """Implement rate limiting for search engines."""
        config = self.engine_configs.get(engine, {})
        rate_limit = config.get('rate_limit', 1.0)

        now = time.time()
        last_request = self.last_requests.get(engine, 0)

        time_since_last = now - last_request
        if time_since_last < rate_limit:
            sleep_time = rate_limit - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_requests[engine] = time.time()

    def _get_cache_key(self, query: SearchQuery) -> str:
        """Generate cache key for search query."""
        query_data = {
            'query': query.query,
            'engines': [e.value for e in query.engines],
            'max_results': query.max_results,
            'language': query.language,
            'region': query.region
        }
        content = json.dumps(query_data, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached search result if still valid."""
        if cache_key not in self.cache:
            return None

        cached_entry = self.cache[cache_key]
        cache_time = cached_entry.get('cached_at')

        if not cache_time or datetime.now() - cache_time > self.cache_ttl:
            del self.cache[cache_key]
            return None

        result = cached_entry['result'].copy()
        result['from_cache'] = True
        return result

    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache search result."""
        self.cache[cache_key] = {
            'result': result,
            'cached_at': datetime.now()
        }

        # Clean old cache entries
        self._cleanup_cache()

    def _cleanup_cache(self):
        """Remove expired cache entries."""
        cutoff_time = datetime.now() - self.cache_ttl
        expired_keys = []

        for key, entry in self.cache.items():
            if entry.get('cached_at', datetime.min) < cutoff_time:
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

    async def semantic_search(
        self,
        query: str,
        context: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Perform semantic search with context understanding.

        Args:
            query: Search query
            context: Optional context to improve search relevance
            max_results: Maximum results to return

        Returns:
            Semantic search results with relevance scoring
        """
        # Enhanced query construction with context
        enhanced_query = query
        if context:
            # Simple context integration - could be enhanced with NLP
            context_terms = re.findall(r'\b\w+\b', context.lower())
            query_terms = re.findall(r'\b\w+\b', query.lower())

            # Add relevant context terms that aren't already in query
            relevant_context = [term for term in context_terms
                             if term not in query_terms and len(term) > 3][:3]

            if relevant_context:
                enhanced_query = f"{query} {' '.join(relevant_context)}"

        search_query = SearchQuery(
            query=enhanced_query,
            engines=[SearchEngine.DUCKDUCKGO, SearchEngine.SEARX],
            max_results=max_results * 2  # Get more results for better filtering
        )

        result = await self.search(search_query)

        if not result['success']:
            return result

        # Re-rank results based on semantic relevance
        if context:
            context_terms = set(re.findall(r'\b\w+\b', context.lower()))

            for item in result['results']:
                # Boost results that contain context terms
                content_terms = set(re.findall(r'\b\w+\b',
                                             (item['title'] + ' ' + item['snippet']).lower()))
                context_overlap = len(context_terms.intersection(content_terms))

                # Adjust relevance score based on context
                item['relevance_score'] += context_overlap * 0.1

            # Re-sort by updated relevance scores
            result['results'] = sorted(result['results'],
                                     key=lambda x: x['relevance_score'],
                                     reverse=True)

        # Limit to requested results
        result['results'] = result['results'][:max_results]
        result['results_returned'] = len(result['results'])
        result['search_type'] = 'semantic'

        return result

    async def close(self):
        """Clean up resources."""
        await self.client.aclose()


# Export advanced search engine
advanced_search_engine = AdvancedWebSearchEngine()

async def advanced_web_search(
    query: str,
    engines: Optional[List[str]] = None,
    max_results: int = 10,
    **kwargs
) -> Dict[str, Any]:
    """
    Claude Code compatible advanced web search function.

    Args:
        query: Search query string
        engines: List of search engines to use
        max_results: Maximum number of results
        **kwargs: Additional search parameters

    Returns:
        Advanced search results with multi-engine aggregation
    """
    return await advanced_search_engine.search(query, engines, max_results, **kwargs)

async def semantic_web_search(
    query: str,
    context: Optional[str] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Claude Code compatible semantic web search function.

    Args:
        query: Search query
        context: Optional context for relevance
        max_results: Maximum results to return

    Returns:
        Semantic search results with context-aware ranking
    """
    return await advanced_search_engine.semantic_search(query, context, max_results)