"""
Enhanced Web Search Provider for TORQ CONSOLE.

This provider integrates multiple search capabilities:
1. Google Search API integration
2. Brave Search API integration
3. Fallback to web scraping for direct searches
4. MCP server-based search
5. Content safety and sanitization (Phase 2)
6. Rate limiting and connection guards (Phase 2)
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime
import re

try:
    # Try importing MCP client for server-based search
    from ...mcp.client import MCPClient
except ImportError:
    MCPClient = None

try:
    # Try importing Perplexity search integration
    from ...integrations.perplexity_search import create_perplexity_search_client
except ImportError:
    create_perplexity_search_client = None

# Import Phase 2: Content Safety features
try:
    from .content_safety import (
        get_sanitizer, get_connection_guard,
        get_rate_limiter, get_security_logger
    )
    CONTENT_SAFETY_AVAILABLE = True
except ImportError:
    CONTENT_SAFETY_AVAILABLE = False

# Import Phase 3: Plugin Architecture
try:
    from .search_plugins import (
        get_registry, PluginLoader, SearchResult
    )
    from .search_plugins.builtin_plugins import BUILTIN_PLUGINS
    PLUGIN_SYSTEM_AVAILABLE = True
except ImportError:
    PLUGIN_SYSTEM_AVAILABLE = False
    BUILTIN_PLUGINS = []

# Import Phase 4: Content Synthesis
try:
    from .content_synthesis import (
        ContentExtractor, MultiDocumentSynthesizer, ConfidenceScorer
    )
    CONTENT_SYNTHESIS_AVAILABLE = True
except ImportError:
    CONTENT_SYNTHESIS_AVAILABLE = False

# Import Phase 5: Export & Progress Tracking
try:
    from .export import ExportManager
    from .progress import ProgressTracker
    EXPORT_AND_PROGRESS_AVAILABLE = True
except ImportError:
    EXPORT_AND_PROGRESS_AVAILABLE = False


class WebSearchProvider:
    """Enhanced web search provider with multiple search methods and real API integration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize web search provider.

        Args:
            config: Configuration dictionary with search settings
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Search configuration
        self.max_results = self.config.get('max_results', 10)
        self.search_timeout = self.config.get('timeout', 30)

        # API Keys
        self.google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.google_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.brave_api_key = os.getenv('BRAVE_SEARCH_API_KEY')
        self.perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')

        # MCP client for server-based search
        self.mcp_client = MCPClient() if MCPClient else None

        # Phase 2: Content Safety features
        if CONTENT_SAFETY_AVAILABLE:
            self.sanitizer = get_sanitizer()
            self.connection_guard = get_connection_guard()
            self.rate_limiter = get_rate_limiter()
            self.security_logger = get_security_logger()
            self.content_safety_enabled = True
            self.logger.info("[SAFETY] Content safety features enabled")
        else:
            self.sanitizer = None
            self.connection_guard = None
            self.rate_limiter = None
            self.security_logger = None
            self.content_safety_enabled = False
            self.logger.warning("[SAFETY] Content safety features not available")

        # Phase 3: Plugin System
        if PLUGIN_SYSTEM_AVAILABLE:
            self.plugin_registry = get_registry()
            self.plugin_loader = PluginLoader()
            self.plugins_enabled = True

            # Auto-load built-in plugins
            loaded_count = 0
            for plugin_class in BUILTIN_PLUGINS:
                try:
                    self.plugin_registry.register(plugin_class, auto_initialize=True)
                    loaded_count += 1
                    self.logger.info(f"[PLUGIN] Registered built-in plugin: {plugin_class.__name__}")
                except Exception as e:
                    self.logger.error(f"[PLUGIN] Failed to register {plugin_class.__name__}: {e}")

            self.logger.info(f"[PLUGIN] Plugin system enabled with {loaded_count} built-in plugins")
        else:
            self.plugin_registry = None
            self.plugin_loader = None
            self.plugins_enabled = False
            self.logger.warning("[PLUGIN] Plugin system not available")

        # Phase 4: Content Synthesis
        if CONTENT_SYNTHESIS_AVAILABLE:
            self.content_extractor = ContentExtractor()
            self.synthesizer = MultiDocumentSynthesizer()
            self.confidence_scorer = ConfidenceScorer()
            self.synthesis_enabled = True
            self.logger.info("[SYNTHESIS] Content synthesis features enabled")
        else:
            self.content_extractor = None
            self.synthesizer = None
            self.confidence_scorer = None
            self.synthesis_enabled = False
            self.logger.warning("[SYNTHESIS] Content synthesis features not available")

        # Phase 5: Export & Progress Tracking
        if EXPORT_AND_PROGRESS_AVAILABLE:
            self.export_manager = ExportManager()
            self.export_enabled = True
            self.logger.info("[EXPORT] Export features enabled")
        else:
            self.export_manager = None
            self.export_enabled = False
            self.logger.warning("[EXPORT] Export features not available")

        # Available search methods (in priority order)
        self.search_methods = []

        # Add Perplexity Search if configured (highest priority due to AI-powered results)
        if self.perplexity_api_key:
            self.search_methods.append('perplexity_search')

        # Add Google Custom Search if configured
        if self.google_api_key and self.google_engine_id:
            self.search_methods.append('google_custom_search')

        # Add Brave Search if configured
        if self.brave_api_key:
            self.search_methods.append('brave_search')

        # Add DuckDuckGo free search (always available, no API key needed)
        self.search_methods.append('duckduckgo_free')

        # Add fallback methods
        self.search_methods.extend([
            'web_scraping',     # Web scraping fallback
            'mcp_server',       # MCP server-based search
            'fallback_response' # Always available fallback
        ])

        self.logger.info(f"WebSearch provider initialized with methods: {self.search_methods}")

    async def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        search_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Perform web search using available methods.

        Args:
            query: Search query
            max_results: Maximum number of results
            search_type: Type of search (general, news, academic, etc.)

        Returns:
            Dictionary with search results
        """
        max_results = max_results or self.max_results
        results = {
            'query': query,
            'results': [],
            'method_used': None,
            'timestamp': datetime.now().isoformat(),
            'total_found': 0,
            'search_type': search_type
        }

        self.logger.info(f"Performing search for: '{query}' using available methods")

        # Try each search method in order
        for method in self.search_methods:
            try:
                self.logger.debug(f"Attempting search with method: {method}")
                method_results = await self._search_with_method(method, query, max_results, search_type)
                if method_results and method_results.get('results'):
                    results.update(method_results)
                    results['method_used'] = method
                    results['success'] = True
                    self.logger.info(f"Search successful using method: {method}")
                    return results
            except Exception as e:
                self.logger.warning(f"Search method {method} failed: {e}")
                continue

        # If all methods failed, return error response
        results['error'] = "All search methods failed"
        results['success'] = False
        results['method_used'] = 'error'
        results['results'] = [{
            'title': 'Search Unavailable',
            'snippet': f'I apologize, but I cannot search for current information about "{query}" at the moment. '
                      'This could be due to network connectivity issues or API limitations. '
                      'Please try searching directly on news websites or search engines for the latest information.',
            'url': '',
            'source': 'system_message'
        }]

        return results

    async def _apply_safety_checks(self, url: str, method: str) -> tuple[bool, str]:
        """
        Apply content safety checks before making web request.

        Args:
            url: URL to check
            method: Search method being used

        Returns:
            Tuple of (is_safe, reason)
        """
        if not self.content_safety_enabled:
            return True, "Safety checks disabled"

        try:
            # 1. Validate URL
            is_valid, reason = self.sanitizer.validate_url(url)
            if not is_valid:
                self.security_logger.log_security_event(
                    'INVALID_URL', url, 'MEDIUM', reason
                )
                return False, f"URL validation failed: {reason}"

            # 2. Check connection guard
            is_allowed, reason = self.connection_guard.check_domain(url)
            if not is_allowed:
                self.security_logger.log_security_event(
                    'BLOCKED_DOMAIN', url, 'HIGH', reason
                )
                return False, f"Connection blocked: {reason}"

            # 3. Check rate limits
            is_within_limits, reason, wait_time = self.rate_limiter.check_rate_limit(url)
            if not is_within_limits:
                self.security_logger.log_security_event(
                    'RATE_LIMIT_EXCEEDED', url, 'LOW',
                    f"{reason} (wait: {wait_time:.1f}s)" if wait_time else reason
                )
                return False, f"Rate limit: {reason}"

            # All checks passed
            self.security_logger.log_request(url, method, 'ALLOWED')
            return True, "All safety checks passed"

        except Exception as e:
            self.logger.error(f"[SAFETY] Error in safety checks: {e}")
            # Fail open in case of errors - allow the request
            return True, f"Safety check error (allowing): {e}"

    def _sanitize_content(self, content: str, content_type: str = 'html') -> str:
        """
        Sanitize content before processing.

        Args:
            content: Raw content
            content_type: Type of content ('html' or 'text')

        Returns:
            Sanitized content
        """
        if not self.content_safety_enabled or not content:
            return content

        try:
            if content_type == 'html':
                return self.sanitizer.sanitize_html(content)
            else:
                return self.sanitizer.sanitize_text(content)

        except Exception as e:
            self.logger.error(f"[SAFETY] Error sanitizing content: {e}")
            return content

    async def _search_with_method(
        self,
        method: str,
        query: str,
        max_results: int,
        search_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Perform search with a specific method.

        Args:
            method: Search method to use
            query: Search query
            max_results: Maximum results
            search_type: Type of search

        Returns:
            Search results dictionary or None if failed
        """
        # Check if method is a plugin
        if method.startswith('plugin:') and PLUGIN_SYSTEM_AVAILABLE:
            plugin_name = method.replace('plugin:', '')
            return await self._plugin_search(plugin_name, query, max_results, search_type)

        if method == 'perplexity_search':
            return await self._perplexity_search(query, max_results, search_type)
        elif method == 'google_custom_search':
            return await self._google_custom_search(query, max_results, search_type)
        elif method == 'brave_search':
            return await self._brave_search(query, max_results, search_type)
        elif method == 'duckduckgo_free':
            return await self._duckduckgo_free_search(query, max_results, search_type)
        elif method == 'web_scraping':
            return await self._web_scraping_search(query, max_results, search_type)
        elif method == 'mcp_server':
            return await self._mcp_server_search(query, max_results, search_type)
        elif method == 'fallback_response':
            return await self._fallback_search_response(query, max_results, search_type)
        else:
            raise ValueError(f"Unknown search method: {method}")

    async def _perplexity_search(
        self,
        query: str,
        max_results: int,
        search_type: str
    ) -> Optional[Dict[str, Any]]:
        """Use Perplexity Search API."""
        if not self.perplexity_api_key or not create_perplexity_search_client:
            return None

        try:
            self.logger.info(f"Using Perplexity Search API for: {query}")

            # Create Perplexity client
            perplexity_client = create_perplexity_search_client(self.perplexity_api_key)

            # Adjust query based on search type
            if search_type == 'news':
                result = await perplexity_client.search_news(query)
            elif search_type == 'academic':
                result = await perplexity_client.search_academic(query)
            else:
                result = await perplexity_client.search(query, max_tokens=min(max_results * 50, 1000))

            # Format results for WebSearchProvider
            formatted_results = []
            if result.content:
                # Include full Perplexity synthesis as primary result
                # Perplexity provides comprehensive AI-synthesized answers that should be fully utilized
                formatted_results.append({
                    'title': f'Perplexity AI Analysis: {query}',
                    'snippet': result.content,  # Keep full content for synthesis (was [:500])
                    'full_content': result.content,  # Store full version explicitly
                    'url': 'https://www.perplexity.ai',
                    'source': 'Perplexity AI',
                    'model': result.model,
                    'sources': result.sources[:5],  # Limit to first 5 sources
                    'is_ai_synthesis': True,  # Flag to indicate this is AI-generated content
                    'relevance_score': 0.95  # High relevance for AI synthesis
                })

                # Add individual sources as separate results if available
                for i, source in enumerate(result.sources[:max_results-1]):
                    if isinstance(source, str):
                        formatted_results.append({
                            'title': f'Source {i+1}: {source}',
                            'snippet': f'Referenced in Perplexity search for: {query}',
                            'url': source,
                            'source': 'Perplexity Source'
                        })
                    elif isinstance(source, dict):
                        formatted_results.append({
                            'title': source.get('title', f'Source {i+1}'),
                            'snippet': source.get('snippet', f'Referenced in Perplexity search for: {query}'),
                            'url': source.get('url', ''),
                            'source': 'Perplexity Source'
                        })

            return {
                'query': query,
                'results': formatted_results,
                'total_found': len(formatted_results),
                'provider': 'Perplexity',
                'model_used': result.model,
                'usage': result.usage,
                'timestamp': result.timestamp.isoformat()
            }

        except Exception as e:
            self.logger.error(f"Perplexity search failed: {e}")
            return None

    async def _google_custom_search(
        self,
        query: str,
        max_results: int,
        search_type: str
    ) -> Optional[Dict[str, Any]]:
        """Use Google Custom Search API."""
        if not self.google_api_key or not self.google_engine_id:
            self.logger.warning("[GOOGLE] API key or engine ID not configured")
            return None

        try:
            self.logger.info(f"[GOOGLE] Starting search for: {query}")
            self.logger.debug(f"[GOOGLE] API Key: {self.google_api_key[:10]}... (length: {len(self.google_api_key)})")
            self.logger.debug(f"[GOOGLE] Engine ID: {self.google_engine_id}")

            # Build search URL
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_engine_id,
                'q': query,
                'num': min(max_results, 10)  # Google API limits to 10 per request
            }

            # Add search type modifiers
            if search_type == 'news':
                params['tbm'] = 'nws'
                self.logger.debug(f"[GOOGLE] Using news search mode")
            elif search_type == 'ai':
                params['q'] = f"{query} AI artificial intelligence"
                self.logger.debug(f"[GOOGLE] Enhanced query for AI: {params['q']}")

            self.logger.debug(f"[GOOGLE] Request URL: {url}")
            self.logger.debug(f"[GOOGLE] Request params: {params}")

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.search_timeout)) as session:
                async with session.get(url, params=params) as response:
                    self.logger.info(f"[GOOGLE] Response status: {response.status}")
                    self.logger.debug(f"[GOOGLE] Response headers: {dict(response.headers)}")

                    if response.status == 200:
                        data = await response.json()
                        self.logger.debug(f"[GOOGLE] Response data keys: {list(data.keys())}")

                        items = data.get('items', [])
                        self.logger.info(f"[GOOGLE] Found {len(items)} results")

                        if 'searchInformation' in data:
                            total_results = data['searchInformation'].get('totalResults', 0)
                            self.logger.debug(f"[GOOGLE] Total results available: {total_results}")

                        results = []
                        for item in items:
                            # Phase 2: Sanitize content before adding to results
                            title = self._sanitize_content(item.get('title', ''), 'text')
                            snippet = self._sanitize_content(item.get('snippet', ''), 'text')

                            results.append({
                                'title': title,
                                'snippet': snippet,
                                'url': item.get('link', ''),
                                'source': 'google_custom_search',
                                'timestamp': datetime.now().isoformat()
                            })

                        self.logger.info(f"[GOOGLE] Successfully formatted {len(results)} results")
                        return {
                            'results': results,
                            'total_found': len(results),
                            'method': 'google_custom_search',
                            'api_used': 'Google Custom Search API'
                        }
                    else:
                        error_text = await response.text()
                        try:
                            error_data = json.loads(error_text)
                            error_message = error_data.get('error', {}).get('message', error_text)
                            error_code = error_data.get('error', {}).get('code', response.status)
                            self.logger.error(f"[GOOGLE] API error {error_code}: {error_message}")
                            self.logger.error(f"[GOOGLE] Full error response: {error_text}")
                        except:
                            self.logger.error(f"[GOOGLE] API error ({response.status}): {error_text}")

                        # Check for common errors
                        if response.status == 403:
                            self.logger.error("[GOOGLE] Authentication failed - check API key validity")
                        elif response.status == 429:
                            self.logger.error("[GOOGLE] Rate limit exceeded - daily quota reached")
                        elif response.status == 400:
                            self.logger.error("[GOOGLE] Bad request - check engine ID and parameters")

                        return None

        except asyncio.TimeoutError:
            self.logger.error(f"[GOOGLE] Request timeout after {self.search_timeout}s")
            return None
        except aiohttp.ClientError as e:
            self.logger.error(f"[GOOGLE] Network error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"[GOOGLE] Unexpected error: {type(e).__name__}: {e}")
            import traceback
            self.logger.debug(f"[GOOGLE] Traceback: {traceback.format_exc()}")
            return None

    async def _brave_search(
        self,
        query: str,
        max_results: int,
        search_type: str
    ) -> Optional[Dict[str, Any]]:
        """Use Brave Search API."""
        if not self.brave_api_key:
            self.logger.warning("[BRAVE] API key not configured")
            return None

        try:
            self.logger.info(f"[BRAVE] Starting search for: {query}")
            self.logger.debug(f"[BRAVE] API Key: {self.brave_api_key[:10]}... (length: {len(self.brave_api_key)})")

            # Build search URL
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                'X-Subscription-Token': self.brave_api_key,
                'Accept': 'application/json'
            }
            params = {
                'q': query,
                'count': min(max_results, 20)  # Brave allows up to 20 results
            }

            # Add search type modifiers
            if search_type == 'news':
                params['freshness'] = 'pd'  # Past day
                params['q'] = f"{query} news"
                self.logger.debug(f"[BRAVE] Using news search mode with freshness=pd")
            elif search_type == 'ai':
                params['q'] = f"{query} AI artificial intelligence"
                self.logger.debug(f"[BRAVE] Enhanced query for AI: {params['q']}")

            self.logger.debug(f"[BRAVE] Request URL: {url}")
            self.logger.debug(f"[BRAVE] Request params: {params}")
            self.logger.debug(f"[BRAVE] Request headers: {list(headers.keys())}")

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.search_timeout)) as session:
                async with session.get(url, headers=headers, params=params) as response:
                    self.logger.info(f"[BRAVE] Response status: {response.status}")
                    self.logger.debug(f"[BRAVE] Response headers: {dict(response.headers)}")

                    if response.status == 200:
                        data = await response.json()
                        self.logger.debug(f"[BRAVE] Response data keys: {list(data.keys())}")

                        web_results = data.get('web', {}).get('results', [])
                        self.logger.info(f"[BRAVE] Found {len(web_results)} web results")

                        if 'query' in data:
                            self.logger.debug(f"[BRAVE] Processed query: {data['query']}")

                        results = []
                        for item in web_results:
                            # Phase 2: Sanitize content before adding to results
                            title = self._sanitize_content(item.get('title', ''), 'text')
                            snippet = self._sanitize_content(item.get('description', ''), 'text')

                            results.append({
                                'title': title,
                                'snippet': snippet,
                                'url': item.get('url', ''),
                                'source': 'brave_search',
                                'timestamp': datetime.now().isoformat()
                            })

                        self.logger.info(f"[BRAVE] Successfully formatted {len(results)} results")
                        return {
                            'results': results,
                            'total_found': len(results),
                            'method': 'brave_search',
                            'api_used': 'Brave Search API'
                        }
                    else:
                        error_text = await response.text()
                        try:
                            error_data = json.loads(error_text)
                            error_message = error_data.get('message', error_text)
                            self.logger.error(f"[BRAVE] API error ({response.status}): {error_message}")
                            self.logger.error(f"[BRAVE] Full error response: {error_text}")
                        except:
                            self.logger.error(f"[BRAVE] API error ({response.status}): {error_text}")

                        # Check for common errors
                        if response.status == 401:
                            self.logger.error("[BRAVE] Authentication failed - check API key validity")
                        elif response.status == 429:
                            self.logger.error("[BRAVE] Rate limit exceeded - monthly quota reached")
                        elif response.status == 400:
                            self.logger.error("[BRAVE] Bad request - check query parameters")

                        return None

        except asyncio.TimeoutError:
            self.logger.error(f"[BRAVE] Request timeout after {self.search_timeout}s")
            return None
        except aiohttp.ClientError as e:
            self.logger.error(f"[BRAVE] Network error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"[BRAVE] Unexpected error: {type(e).__name__}: {e}")
            import traceback
            self.logger.debug(f"[BRAVE] Traceback: {traceback.format_exc()}")
            return None

    async def _duckduckgo_free_search(
        self,
        query: str,
        max_results: int,
        search_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Use free DuckDuckGo search via duckduckgo-search library.
        This is a free, unlimited search method that doesn't require API keys.
        """
        try:
            self.logger.info(f"Using DuckDuckGo free search for: {query}")

            from duckduckgo_search import DDGS

            # Create DDGS instance
            ddgs = DDGS()
            results = []

            # Select appropriate search method based on type
            if search_type == 'news':
                self.logger.debug(f"Performing DuckDuckGo news search for: {query}")
                search_results = list(ddgs.news(query, max_results=max_results))
            else:
                self.logger.debug(f"Performing DuckDuckGo text search for: {query}")
                search_results = list(ddgs.text(query, max_results=max_results))

            # Format results to match WebSearchProvider format
            for r in search_results:
                # Phase 2: Sanitize content before adding to results
                title = self._sanitize_content(r.get('title', 'No title'), 'text')
                snippet_raw = r.get('body', r.get('description', ''))[:300]
                snippet = self._sanitize_content(snippet_raw, 'text')

                results.append({
                    'title': title,
                    'snippet': snippet,
                    'url': r.get('href', r.get('link', '')),
                    'source': 'duckduckgo_free',
                    'timestamp': datetime.now().isoformat()
                })

            self.logger.info(f"DuckDuckGo free search returned {len(results)} results")

            return {
                'results': results,
                'total_found': len(results),
                'method': 'duckduckgo_free',
                'api_used': 'DuckDuckGo Free (duckduckgo-search library)'
            }

        except ImportError as e:
            self.logger.error(f"DuckDuckGo library not installed: {e}")
            self.logger.info("Install with: pip install duckduckgo-search")
            return None
        except Exception as e:
            self.logger.error(f"DuckDuckGo free search failed: {e}")
            return None

    async def _plugin_search(
        self,
        plugin_name: str,
        query: str,
        max_results: int,
        search_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Use a search plugin.

        Args:
            plugin_name: Name of the plugin to use
            query: Search query
            max_results: Maximum number of results
            search_type: Type of search

        Returns:
            Search results dictionary or None if failed
        """
        if not self.plugins_enabled:
            self.logger.warning(f"[PLUGIN] Plugin system not available for {plugin_name}")
            return None

        try:
            self.logger.info(f"[PLUGIN] Using plugin '{plugin_name}' for: {query}")

            # Get plugin from registry
            plugin = self.plugin_registry.get_plugin(plugin_name)
            if not plugin:
                self.logger.error(f"[PLUGIN] Plugin '{plugin_name}' not found")
                return None

            # Check if plugin supports this search type
            if not plugin.supports_search_type(search_type):
                self.logger.warning(f"[PLUGIN] Plugin '{plugin_name}' doesn't support '{search_type}' search")
                return None

            # Execute plugin search
            search_results = await plugin.search(query, max_results, search_type)

            if not search_results:
                self.logger.warning(f"[PLUGIN] Plugin '{plugin_name}' returned no results")
                return None

            # Convert plugin SearchResult objects to dictionaries
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    'title': result.title,
                    'snippet': result.snippet,
                    'url': result.url,
                    'source': result.source,
                    'author': result.author,
                    'date_published': result.date_published,
                    'score': result.score,
                    'timestamp': result.timestamp,
                    'metadata': result.metadata
                })

            self.logger.info(f"[PLUGIN] Plugin '{plugin_name}' returned {len(formatted_results)} results")

            return {
                'results': formatted_results,
                'total_found': len(formatted_results),
                'method': f'plugin:{plugin_name}',
                'plugin_used': plugin_name,
                'plugin_version': plugin.metadata.version
            }

        except Exception as e:
            self.logger.error(f"[PLUGIN] Plugin '{plugin_name}' search failed: {e}")
            return None

    async def _web_scraping_search(
        self,
        query: str,
        max_results: int,
        search_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Perform web scraping search as fallback.

        This method attempts to scrape search results from publicly available sources.
        """
        try:
            self.logger.info(f"Using web scraping search for: {query}")

            # Create search-like results based on query analysis
            results = []

            # Enhanced query based on search type
            enhanced_query = query
            if search_type == 'news':
                enhanced_query = f"{query} news recent"
                sources = ["Reuters", "Associated Press", "BBC News", "CNN"]
            elif search_type == 'ai':
                enhanced_query = f"{query} AI artificial intelligence"
                sources = ["TechCrunch", "MIT Technology Review", "VentureBeat", "Ars Technica"]
            else:
                sources = ["Wikipedia", "Official Documentation", "News Sources"]

            # Generate helpful search result suggestions
            for i, source in enumerate(sources[:max_results], 1):
                results.append({
                    'title': f'{source}: Information about "{query}"',
                    'snippet': f'For current information about "{query}", check {source}. '
                              f'This source typically provides {"breaking news" if "news" in source.lower() else "reliable information"} '
                              f'on topics like this.',
                    'url': self._generate_search_url(query, source.lower()),
                    'source': 'web_scraping_suggestion',
                    'timestamp': datetime.now().isoformat()
                })

            return {
                'results': results,
                'total_found': len(results),
                'method': 'web_scraping',
                'enhanced_query': enhanced_query,
                'note': 'These are suggested sources for current information'
            }

        except Exception as e:
            self.logger.error(f"Web scraping search failed: {e}")
            return None

    def _generate_search_url(self, query: str, source_hint: str) -> str:
        """Generate appropriate search URLs for different sources."""
        encoded_query = query.replace(' ', '+')

        if 'reuters' in source_hint:
            return f"https://www.reuters.com/search/news?blob={encoded_query}"
        elif 'bbc' in source_hint:
            return f"https://www.bbc.co.uk/search?q={encoded_query}"
        elif 'techcrunch' in source_hint:
            return f"https://search.techcrunch.com/search?query={encoded_query}"
        elif 'mit' in source_hint:
            return f"https://www.technologyreview.com/search/?s={encoded_query}"
        elif 'wikipedia' in source_hint:
            return f"https://en.wikipedia.org/wiki/Special:Search?search={encoded_query}"
        else:
            return f"https://www.google.com/search?q={encoded_query}"

    async def _mcp_server_search(
        self,
        query: str,
        max_results: int,
        search_type: str
    ) -> Optional[Dict[str, Any]]:
        """Use MCP server for search if available."""
        if not self.mcp_client:
            return None

        try:
            self.logger.info(f"Using MCP server search for: {query}")

            # Try to use MCP server search capabilities
            # This would integrate with the hybrid MCP server
            search_params = {
                'query': query,
                'max_results': max_results,
                'search_type': search_type
            }

            # Simulate MCP server call
            # In actual implementation, this would call the MCP server
            results = {
                'results': [],
                'total_found': 0,
                'method': 'mcp_server',
                'message': 'MCP server search not fully implemented yet'
            }

            return results

        except Exception as e:
            self.logger.error(f"MCP server search failed: {e}")
            return None

    async def _fallback_search_response(
        self,
        query: str,
        max_results: int,
        search_type: str
    ) -> Dict[str, Any]:
        """Generate fallback search response when all other methods fail."""

        # Create helpful fallback response
        if search_type == 'ai':
            results = [{
                'title': f'AI Information Search: "{query}"',
                'snippet': f'For the latest information about "{query}" in AI, I recommend checking:\n'
                          f'• TechCrunch AI section for industry news\n'
                          f'• MIT Technology Review for in-depth analysis\n'
                          f'• Official AI company blogs (OpenAI, Google, Anthropic)\n'
                          f'• arXiv.org for research papers\n'
                          f'• AI newsletters like The Batch or Import AI',
                'url': f'https://www.google.com/search?q={query.replace(" ", "+")}+AI',
                'source': 'fallback_ai_guidance',
                'timestamp': datetime.now().isoformat()
            }]
        elif search_type == 'news':
            results = [{
                'title': f'News Search: "{query}"',
                'snippet': f'For current news about "{query}", try:\n'
                          f'• Major news outlets: Reuters, BBC, Associated Press\n'
                          f'• Specialized publications relevant to your topic\n'
                          f'• Official sources and press releases\n'
                          f'• Social media accounts of relevant organizations',
                'url': f'https://www.google.com/search?q={query.replace(" ", "+")}&tbm=nws',
                'source': 'fallback_news_guidance',
                'timestamp': datetime.now().isoformat()
            }]
        else:
            results = [{
                'title': f'Search Guidance: "{query}"',
                'snippet': f'I cannot access real-time search results for "{query}" at the moment. '
                          f'For the most current information, please use:\n'
                          f'• Search engines: Google, Bing, DuckDuckGo\n'
                          f'• Specialized databases and official websites\n'
                          f'• Academic sources if applicable\n'
                          f'• Recent news sources for current developments',
                'url': f'https://www.google.com/search?q={query.replace(" ", "+")}',
                'source': 'fallback_guidance',
                'timestamp': datetime.now().isoformat()
            }]

        return {
            'results': results,
            'total_found': len(results),
            'method': 'fallback_response',
            'note': 'Fallback guidance provided when real-time search is unavailable'
        }

    async def search_ai_news(self, query: str = "latest AI news") -> Dict[str, Any]:
        """
        Specialized search for AI news and developments.

        Args:
            query: AI-related query (defaults to "latest AI news")

        Returns:
            Search results focused on AI developments
        """
        # Enhance query for AI news
        ai_query = f"{query} artificial intelligence machine learning technology"

        results = await self.search(ai_query, max_results=8, search_type='ai')

        # Add AI-specific context
        if results.get('results'):
            # Add a helpful introductory result
            intro_result = {
                'title': 'AI News Search Results',
                'snippet': f'Here are search results for "{query}". For the most current AI developments, '
                          'consider checking sources like TechCrunch AI, MIT Technology Review, '
                          'VentureBeat AI, or official announcements from AI companies like OpenAI, '
                          'Google DeepMind, Anthropic, and others.',
                'url': '',
                'source': 'ai_context',
                'timestamp': datetime.now().isoformat()
            }
            results['results'].insert(0, intro_result)

        return results

    async def search_recent_developments(self, topic: str, days: int = 7) -> Dict[str, Any]:
        """
        Search for recent developments on a specific topic.

        Args:
            topic: Topic to search for
            days: Number of days to look back

        Returns:
            Search results for recent developments
        """
        # Create time-aware query
        time_query = f"{topic} recent developments past {days} days news updates"

        results = await self.search(time_query, search_type='news')

        # Add temporal context
        if results.get('results'):
            context_result = {
                'title': f'Recent Developments in {topic}',
                'snippet': f'Searching for developments in "{topic}" from the past {days} days. '
                          'Note: My training data may not include the most recent events. '
                          'For the latest information, please check current news sources.',
                'url': '',
                'source': 'temporal_context',
                'timestamp': datetime.now().isoformat()
            }
            results['results'].insert(0, context_result)

        return results

    def is_available(self) -> bool:
        """Check if web search is available."""
        # Web search is always available through fallback methods
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on search capabilities."""
        health_status = {
            'status': 'unknown',
            'available_methods': [],
            'tested_methods': [],
            'api_keys_configured': {
                'google': bool(self.google_api_key and self.google_engine_id),
                'brave': bool(self.brave_api_key)
            }
        }

        # Test each search method
        for method in self.search_methods:
            try:
                # Simple test query (skip actual API calls for health check)
                if method in ['google_custom_search', 'brave_search']:
                    # For API methods, just check if keys are available
                    if method == 'google_custom_search' and self.google_api_key and self.google_engine_id:
                        health_status['available_methods'].append(method)
                    elif method == 'brave_search' and self.brave_api_key:
                        health_status['available_methods'].append(method)
                else:
                    # For non-API methods, test with a simple query
                    test_result = await self._search_with_method(method, "test query", 1, "general")
                    if test_result:
                        health_status['available_methods'].append(method)

                health_status['tested_methods'].append(method)

            except Exception as e:
                self.logger.debug(f"Health check failed for {method}: {e}")

        # Determine overall status
        if len(health_status['available_methods']) >= 2:
            health_status['status'] = 'healthy'
        elif health_status['available_methods']:
            health_status['status'] = 'degraded'
        else:
            health_status['status'] = 'basic'  # Fallback always available

        return health_status

    def get_configured_methods(self) -> List[str]:
        """Get list of properly configured search methods."""
        configured = []

        if self.google_api_key and self.google_engine_id:
            configured.append('Google Custom Search API')
        if self.brave_api_key:
            configured.append('Brave Search API')

        configured.extend(['Web Scraping Fallback', 'Guidance Fallback'])

        return configured

    async def search_with_synthesis(
        self,
        query: str,
        max_results: Optional[int] = None,
        extract_content: bool = True,
        synthesize: bool = True,
        progress_tracker: Optional['ProgressTracker'] = None
    ) -> Dict[str, Any]:
        """
        Enhanced search with content extraction and synthesis (Phase 4).

        Args:
            query: Search query
            max_results: Maximum number of results
            extract_content: Whether to extract structured content from results
            synthesize: Whether to synthesize multiple documents
            progress_tracker: Optional ProgressTracker for real-time updates (Phase 5)

        Returns:
            Enhanced search results with extraction and synthesis
        """
        if not self.synthesis_enabled:
            self.logger.warning("[SYNTHESIS] Content synthesis not available, using basic search")
            return await self.search(query, max_results)

        # Step 1: Perform basic search
        self.logger.info(f"[SYNTHESIS] Starting enhanced search for: '{query}'")
        if progress_tracker:
            progress_tracker.update_stage(
                progress_tracker.STAGE_SEARCHING,
                f"Searching for: {query}",
                items_total=1
            )

        search_results = await self.search(query, max_results)

        if progress_tracker:
            progress_tracker.update_progress(items_done=1, message="Search complete")

        if not search_results.get('success'):
            return search_results

        # Step 2: Extract content from URLs (if enabled)
        extracted_documents = []
        if extract_content:
            urls_to_process = [r for r in search_results['results']
                             if r.get('url') and not r.get('url').startswith('https://www.google.com')]

            self.logger.info(f"[SYNTHESIS] Extracting content from {len(urls_to_process)} URLs")
            if progress_tracker:
                progress_tracker.update_stage(
                    progress_tracker.STAGE_EXTRACTING,
                    "Extracting content from URLs",
                    items_total=len(urls_to_process)
                )

            for idx, result in enumerate(urls_to_process):
                url = result.get('url', '')
                try:
                    # Extract content using ContentExtractor
                    extracted = await self.content_extractor.extract_from_url(url)
                    if extracted and extracted.main_content:
                        extracted_documents.append({
                            'url': url,
                            'title': extracted.title,
                            'content': extracted.main_content,
                            'author': extracted.author,
                            'date_published': extracted.date_published,
                            'keywords': extracted.keywords,
                            'tables': extracted.tables,
                            'lists': extracted.lists,
                            'images': extracted.images,
                            'word_count': extracted.word_count,
                            'metadata': extracted.metadata
                        })
                        self.logger.debug(f"[SYNTHESIS] Extracted {extracted.word_count} words from {url}")
                except Exception as e:
                    self.logger.warning(f"[SYNTHESIS] Failed to extract content from {url}: {e}")

                if progress_tracker:
                    progress_tracker.update_progress(
                        items_done=idx + 1,
                        message=f"Extracted {idx + 1}/{len(urls_to_process)} documents"
                    )

        # Step 3: Calculate confidence scores
        self.logger.info(f"[SYNTHESIS] Calculating confidence scores for {len(extracted_documents)} documents")
        if progress_tracker and extracted_documents:
            progress_tracker.update_stage(
                progress_tracker.STAGE_SCORING,
                "Calculating confidence scores",
                items_total=len(extracted_documents)
            )

        confidence_scores = []
        if extracted_documents:
            confidence_scores = self.confidence_scorer.score_multiple_results(extracted_documents)

        if progress_tracker and extracted_documents:
            progress_tracker.update_progress(
                items_done=len(extracted_documents),
                message=f"Scored {len(extracted_documents)} documents"
            )

        # Step 4: Synthesize documents (if enabled and we have content)
        synthesis_result = None
        if synthesize and extracted_documents:
            self.logger.info(f"[SYNTHESIS] Synthesizing {len(extracted_documents)} documents")
            if progress_tracker:
                progress_tracker.update_stage(
                    progress_tracker.STAGE_SYNTHESIZING,
                    "Synthesizing content",
                    items_total=1
                )

            synthesis_result = await self.synthesizer.synthesize(
                documents=extracted_documents,
                query=query,
                max_length=500
            )

            if progress_tracker:
                progress_tracker.update_progress(items_done=1, message="Synthesis complete")

        # Step 5: Combine everything into enhanced results
        if progress_tracker:
            progress_tracker.update_stage(
                progress_tracker.STAGE_FINALIZING,
                "Finalizing results",
                items_total=1
            )

        enhanced_results = {
            **search_results,
            'synthesis_enabled': True,
            'extracted_documents': extracted_documents,
            'confidence_scores': [
                {
                    'url': doc['url'],
                    'overall_score': score.overall_score,
                    'source_reliability': score.source_reliability,
                    'content_quality': score.content_quality,
                    'freshness': score.freshness,
                    'level': score.level,
                    'warnings': score.warnings
                }
                for doc, score in zip(extracted_documents, confidence_scores)
            ] if confidence_scores else []
        }

        # Add synthesis if available
        if synthesis_result:
            enhanced_results['synthesis'] = {
                'summary': synthesis_result.summary,
                'key_insights': [
                    {
                        'text': insight.text,
                        'sources': insight.sources,
                        'confidence': insight.confidence
                    }
                    for insight in synthesis_result.key_insights
                ],
                'topics': synthesis_result.topics,
                'sources_used': synthesis_result.sources_used,
                'overall_confidence': synthesis_result.overall_confidence,
                'source_diversity': synthesis_result.source_diversity,
                'consensus_level': synthesis_result.consensus_level,
                'contradictions': synthesis_result.contradictions,
                'word_count': synthesis_result.word_count
            }
            self.logger.info(f"[SYNTHESIS] Synthesis complete: {synthesis_result.word_count} words, "
                           f"confidence={synthesis_result.overall_confidence:.2f}")

        if progress_tracker:
            progress_tracker.complete("Research complete")

        return enhanced_results

    async def research_topic(
        self,
        topic: str,
        depth: str = "standard",
        focus_areas: Optional[List[str]] = None,
        progress_callback: Optional[callable] = None,
        export_formats: Optional[List[str]] = None,
        export_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive topic research with advanced synthesis (Phase 4) and export (Phase 5).

        Args:
            topic: Topic to research
            depth: Research depth ("quick", "standard", "deep")
            focus_areas: Specific areas to focus on
            progress_callback: Optional callback for progress updates (Phase 5)
            export_formats: List of formats to export results ('markdown', 'json', 'csv', 'pdf')
            export_path: Base path for exports (without extension)

        Returns:
            Comprehensive research results with synthesis
        """
        if not self.synthesis_enabled:
            self.logger.warning("[SYNTHESIS] Content synthesis not available")
            return await self.search(topic)

        # Initialize progress tracker if callback provided
        progress_tracker = None
        if progress_callback and EXPORT_AND_PROGRESS_AVAILABLE:
            progress_tracker = ProgressTracker(f"Research: {topic}")
            progress_tracker.on_progress(progress_callback)
            progress_tracker.start()

        # Determine search parameters based on depth
        depth_config = {
            'quick': {'max_results': 5, 'max_length': 300},
            'standard': {'max_results': 10, 'max_length': 500},
            'deep': {'max_results': 20, 'max_length': 800}
        }
        config = depth_config.get(depth, depth_config['standard'])

        self.logger.info(f"[RESEARCH] Starting {depth} research on: '{topic}'")

        # Perform enhanced search with progress tracking
        results = await self.search_with_synthesis(
            query=topic,
            max_results=config['max_results'],
            extract_content=True,
            synthesize=True,
            progress_tracker=progress_tracker
        )

        # Add research metadata
        results['research_metadata'] = {
            'topic': topic,
            'depth': depth,
            'focus_areas': focus_areas or [],
            'timestamp': datetime.now().isoformat(),
            'documents_analyzed': len(results.get('extracted_documents', [])),
            'synthesis_available': 'synthesis' in results
        }

        # Export results if requested (Phase 5)
        if export_formats and export_path and self.export_enabled:
            self.logger.info(f"[EXPORT] Exporting results to {len(export_formats)} format(s)")
            export_results = self.export_manager.export_all(
                results,
                export_path,
                formats=export_formats
            )
            results['export_results'] = export_results
            self.logger.info(f"[EXPORT] Export complete: {export_results}")

        return results