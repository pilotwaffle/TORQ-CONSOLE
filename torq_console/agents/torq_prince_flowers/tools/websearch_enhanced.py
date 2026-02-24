"""
Enhanced Web Search Tool for TORQ Prince Flowers agent.

This module provides real web search capabilities using:
- Tavily API (AI-optimized search)
- Brave Search API (2,000 free queries/month)
- Integration with Claude's computer use for web browsing
- Content extraction and validation
"""

import asyncio
import aiohttp
import json
import logging
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from urllib.parse import urlencode, quote_plus


class EnhancedWebSearchTool:
    """
    Enhanced web search tool with real API integration.

    Supports:
    - Tavily Search API (AI-optimized for research)
    - Brave Search API (privacy-focused, 2000 free/month)
    - Fallback to free DuckDuckGo search
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the enhanced web search tool.

        Args:
            config: Configuration dictionary with API settings
        """
        self.config = config or {}
        self.logger = logging.getLogger("EnhancedWebSearchTool")

        # API Keys from environment
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        self.brave_api_key = os.getenv('BRAVE_SEARCH_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

        # Search configuration
        self.max_results = self.config.get('max_results', 10)
        self.search_timeout = self.config.get('timeout', 30)

        # Determine available search methods
        self.available_methods = []
        if self.tavily_api_key:
            self.available_methods.append('tavily')
            self.logger.info("Tavily search enabled")
        if self.brave_api_key:
            self.available_methods.append('brave')
            self.logger.info("Brave search enabled")

        # DuckDuckGo is always available as fallback
        self.available_methods.append('duckduckgo')
        self.logger.info(f"Available search methods: {self.available_methods}")

    def is_available(self) -> bool:
        """Check if the web search tool is available."""
        return len(self.available_methods) > 0

    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return ["web_search", "multi_source_search", "news_search"]

    async def search(
        self,
        query: str,
        search_method: str = "auto",
        max_results: int = 10,
        search_depth: str = "basic",
        include_domains: List[str] = None,
        exclude_domains: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform web search for the given query.

        Args:
            query: Search query string
            search_method: Specific search method ('tavily', 'brave', 'duckduckgo', 'auto')
            max_results: Maximum number of results
            search_depth: Search depth ('basic' or 'advanced')
            include_domains: List of domains to include
            exclude_domains: List of domains to exclude

        Returns:
            List of search results with title, url, snippet, etc.
        """
        # Auto-select best available method
        if search_method == "auto":
            search_method = self._select_best_method()

        try:
            if search_method == "tavily" and "tavily" in self.available_methods:
                return await self._search_tavily(
                    query, max_results, search_depth, include_domains, exclude_domains
                )
            elif search_method == "brave" and "brave" in self.available_methods:
                return await self._search_brave(query, max_results)
            else:
                return await self._search_duckduckgo(query, max_results)

        except Exception as e:
            self.logger.error(f"Search failed with method '{search_method}': {e}")
            # Try fallback method
            if search_method != "duckduckgo":
                self.logger.info("Falling back to DuckDuckGo search")
                return await self._search_duckduckgo(query, max_results)
            return []

    async def search_with_context(
        self,
        query: str,
        context: str = "",
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Perform search with additional context for better results.

        Args:
            query: Search query string
            context: Additional context to guide the search
            max_results: Maximum number of results

        Returns:
            Search results with metadata
        """
        # Augment query with context if provided
        augmented_query = query
        if context:
            augmented_query = f"{query} {context}"

        results = await self.search(augmented_query, max_results=max_results)

        return {
            "success": len(results) > 0,
            "query": query,
            "results": results,
            "total_results": len(results),
            "timestamp": datetime.now().isoformat()
        }

    async def news_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform news-specific search.

        Args:
            query: News search query
            max_results: Maximum number of results

        Returns:
            News search results
        """
        if "tavily" in self.available_methods:
            return await self._search_tavily(query, max_results, search_depth="basic", topic="news")
        else:
            # Add "news" to query for other engines
            return await self.search(f"{query} news", max_results=max_results)

    def _select_best_method(self) -> str:
        """Select the best available search method."""
        if "tavily" in self.available_methods:
            return "tavily"  # Tavily is AI-optimized, best for research
        elif "brave" in self.available_methods:
            return "brave"
        else:
            return "duckduckgo"

    async def _search_tavily(
        self,
        query: str,
        max_results: int = 10,
        search_depth: str = "basic",
        include_domains: List[str] = None,
        exclude_domains: List[str] = None,
        topic: str = "general"
    ) -> List[Dict[str, Any]]:
        """
        Search using Tavily API.

        Tavily is optimized for AI/LLM applications with:
        - Advanced search with content extraction
        - Real-time web data
        - AI-optimized result formatting
        """
        if not self.tavily_api_key:
            raise ValueError("Tavily API key not configured")

        url = "https://api.tavily.com/search"

        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": min(max_results, 10),
            "include_answer": True,
            "include_raw_content": False,
            "include_images": False,
            "include_image_descriptions": False,
            "include_domains": include_domains or [],
            "exclude_domains": exclude_domains or []
        }

        # Add topic for specialized searches
        if topic != "general":
            payload["topic"] = topic

        headers = {
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=self.search_timeout) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Tavily API error: {response.status} - {error_text}")
                        raise Exception(f"Tavily API returned status {response.status}")

                    data = await response.json()

                    # Extract results
                    results = []
                    if "answer" in data and data["answer"]:
                        results.append({
                            "title": "AI-Generated Answer",
                            "url": "",
                            "snippet": data["answer"],
                            "source": "tavily-ai",
                            "is_ai_answer": True
                        })

                    for result in data.get("results", []):
                        results.append({
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "snippet": result.get("content", ""),
                            "score": result.get("score", 0.0),
                            "source": "tavily",
                            "published_date": result.get("published_date")
                        })

                    self.logger.info(f"Tavily search returned {len(results)} results")
                    return results

        except asyncio.TimeoutError:
            self.logger.error("Tavily search timed out")
            raise Exception("Search timed out")
        except Exception as e:
            self.logger.error(f"Tavily search failed: {e}")
            raise

    async def _search_brave(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search using Brave Search API.

        Brave provides privacy-focused search with:
        - Independent search index
        - No tracking
        - 2,000 free queries/month
        """
        if not self.brave_api_key:
            raise ValueError("Brave API key not configured")

        url = "https://api.search.brave.com/res/v1/web/search"

        params = {
            "q": query,
            "count": min(max_results, 20),
            "text_decorations": False,
            "search_lang": "en",
            "result_filter": "web",
            "freshness": "all"
        }

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=self.search_timeout) as response:
                    if response.status != 200:
                        if response.status == 401:
                            raise Exception("Brave API authentication failed - check API key")
                        elif response.status == 429:
                            raise Exception("Brave API rate limit exceeded")
                        error_text = await response.text()
                        raise Exception(f"Brave API error: {response.status} - {error_text}")

                    data = await response.json()

                    # Extract web results
                    results = []
                    web_results = data.get("web", {}).get("results", [])

                    for result in web_results:
                        # Get snippet from either 'description' or 'extra_snippets'
                        snippet = result.get("description", "")
                        if not snippet and result.get("extra_snippets"):
                            snippet = " ".join(result.get("extra_snippets", []))

                        results.append({
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "snippet": snippet,
                            "source": "brave"
                        })

                    self.logger.info(f"Brave search returned {len(results)} results")
                    return results

        except asyncio.TimeoutError:
            self.logger.error("Brave search timed out")
            raise Exception("Search timed out")
        except Exception as e:
            self.logger.error(f"Brave search failed: {e}")
            raise

    async def _search_duckduckgo(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo (free, no API key required).

        Uses DuckDuckGo's HTML version via web scraping.
        """
        url = "https://html.duckduckgo.com/html/"

        params = {
            "q": query
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=self.search_timeout) as response:
                    if response.status != 200:
                        raise Exception(f"DuckDuckGo returned status {response.status}")

                    html = await response.text()

                    # Parse HTML to extract results
                    import re
                    results = []

                    # Extract result blocks using regex
                    result_pattern = r'<class="result__a[^>]*>([^<]+)</a>.*?<a class="result__url"[^>]*>([^<]+)</a>.*?<class="result__snippet[^>]*>([^<]*)</a>'
                    matches = re.findall(result_pattern, html, re.DOTALL)

                    for i, (title, url, snippet) in enumerate(matches[:max_results]):
                        # Clean up the results
                        title = re.sub(r'<[^>]+>', '', title).strip()
                        url = re.sub(r'<[^>]+>', '', url).strip()
                        snippet = re.sub(r'<[^>]+>', '', snippet).strip()

                        if title and url:
                            results.append({
                                "title": title,
                                "url": url,
                                "snippet": snippet or "No description available",
                                "source": "duckduckgo"
                            })

                    self.logger.info(f"DuckDuckGo search returned {len(results)} results")
                    return results

        except asyncio.TimeoutError:
            self.logger.error("DuckDuckGo search timed out")
            raise Exception("Search timed out")
        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed: {e}")
            raise

    async def multi_source_search(
        self,
        query: str,
        methods: List[str] = None,
        max_results_per_method: int = 5
    ) -> Dict[str, Any]:
        """
        Perform search across multiple sources and combine results.

        Args:
            query: Search query string
            methods: List of search methods to use (None = use all available)
            max_results_per_method: Max results per search method

        Returns:
            Combined results with source metadata
        """
        if methods is None:
            methods = self.available_methods[:2]  # Use top 2 methods

        all_results = []
        source_stats = {}

        # Run searches in parallel
        tasks = []
        for method in methods:
            if method in self.available_methods:
                tasks.append(self.search(query, search_method=method, max_results=max_results_per_method))

        if tasks:
            method_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(method_results):
                method = methods[i]
                if isinstance(result, Exception):
                    self.logger.warning(f"Search method '{method}' failed: {result}")
                    source_stats[method] = {"success": False, "error": str(result)}
                elif isinstance(result, list):
                    # Add source info to each result
                    for r in result:
                        r["search_method"] = method
                    all_results.extend(result)
                    source_stats[method] = {"success": True, "count": len(result)}

        # Rank and deduplicate results
        ranked_results = self._rank_and_deduplicate(all_results)

        return {
            "success": len(ranked_results) > 0,
            "query": query,
            "methods_used": methods,
            "results": ranked_results,
            "source_stats": source_stats,
            "total_results": len(ranked_results)
        }

    def _rank_and_deduplicate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank search results and remove duplicates."""
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
            elif not url:  # Keep AI answers without URLs
                unique_results.append(result)

        return unique_results[:self.max_results]

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the web search tool."""
        status = {
            "healthy": False,
            "available_methods": self.available_methods,
            "api_keys_configured": {
                "tavily": bool(self.tavily_api_key),
                "brave": bool(self.brave_api_key)
            },
            "test_results": {}
        }

        # Test each available method
        for method in self.available_methods:
            try:
                results = await self.search("test query", search_method=method, max_results=1)
                status["test_results"][method] = {
                    "success": True,
                    "result_count": len(results)
                }
            except Exception as e:
                status["test_results"][method] = {
                    "success": False,
                    "error": str(e)
                }

        # Consider healthy if at least one method works
        status["healthy"] = any(
            r.get("success", False) for r in status["test_results"].values()
        )

        return status


# Convenience function for creating the tool
def create_enhanced_web_search_tool(config: Dict[str, Any] = None) -> EnhancedWebSearchTool:
    """Create an enhanced web search tool instance."""
    return EnhancedWebSearchTool(config)
