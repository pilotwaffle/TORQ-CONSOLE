"""
Web search tool for TORQ Prince Flowers agent.

This module provides advanced web search capabilities including:
- Multi-source search (Tavily, Brave, DuckDuckGo)
- Content extraction and validation
- Result ranking and synthesis
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime


class WebSearchTool:
    """
    Advanced web search tool for information gathering.

    This tool provides real web search using multiple APIs:
    - Tavily API (AI-optimized search)
    - Brave Search API (privacy-focused, 2000 free/month)
    - DuckDuckGo (fallback, no API key needed)
    """

    def __init__(self):
        """Initialize the web search tool."""
        self.logger = logging.getLogger("WebSearchTool")
        self.search_engines = ["tavily", "brave", "duckduckgo"]
        self.available_tools = ["web_search", "news_search"]

        # Try to import the enhanced web search implementation
        self._init_enhanced_search()

    def _init_enhanced_search(self):
        """Initialize the enhanced web search implementation."""
        try:
            from torq_console.agents.torq_prince_flowers.tools.websearch_enhanced import (
                EnhancedWebSearchTool
            )
            self.enhanced_tool = EnhancedWebSearchTool()
            self.enhanced_available = True
            self.logger.info("Enhanced web search enabled")
        except ImportError as e:
            self.enhanced_tool = None
            self.enhanced_available = False
            self.logger.warning(f"Enhanced web search not available: {e}")

    def is_available(self) -> bool:
        """Check if the web search tool is available."""
        return self.enhanced_available or True  # Always has fallback

    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        if self.enhanced_available:
            return self.enhanced_tool.get_available_tools()
        return self.available_tools

    async def search(
        self,
        query: str,
        engine: str = "auto",
        max_results: int = 10
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Perform web search for the given query.

        Args:
            query: Search query string
            engine: Search engine to use ('auto', 'tavily', 'brave', 'duckduckgo')
            max_results: Maximum number of results

        Returns:
            List of search results or dict with results metadata
        """
        if self.enhanced_available:
            # Use enhanced search tool
            results = await self.enhanced_tool.search(
                query=query,
                search_method=engine,
                max_results=max_results
            )
            # Return in the expected format (list for compatibility)
            return results

        # Fallback to mock results if enhanced not available
        return await self._fallback_search(query, engine, max_results)

    async def news_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform news-specific search.

        Args:
            query: News search query
            max_results: Maximum number of results

        Returns:
            News search results
        """
        if self.enhanced_available:
            return await self.enhanced_tool.news_search(query, max_results)

        # Fallback: add "news" to query
        return await self.search(f"{query} news", max_results=max_results)

    async def multi_source_search(
        self,
        query: str,
        engines: List[str] = None
    ) -> Dict[str, Any]:
        """Perform search across multiple sources."""
        if self.enhanced_available:
            return await self.enhanced_tool.multi_source_search(query, engines)

        # Fallback implementation
        if engines is None:
            engines = ["duckduckgo"]

        all_results = []
        source_stats = {}

        for engine in engines:
            result = await self.search(query, engine, max_results=5)
            if isinstance(result, list):
                all_results.extend(result)
                source_stats[engine] = len(result)

        return {
            "success": True,
            "query": query,
            "engines_used": engines,
            "results": all_results,
            "source_stats": source_stats,
            "total_results": len(all_results)
        }

    async def _fallback_search(
        self,
        query: str,
        engine: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Fallback search when enhanced tool is not available."""
        mock_results = [
            {
                "title": f"Result {i+1} for '{query}'",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"Web search is not fully configured. Please add Tavily or Brave API keys to .env file. This is a mock result for: {query}",
                "source": engine,
                "score": 1.0 - (i * 0.1)
            }
            for i in range(min(max_results, 3))
        ]
        return mock_results

    def _rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank search results by relevance."""
        return sorted(results, key=lambda x: x.get("score", x.get("relevance_score", 0)), reverse=True)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the web search tool."""
        if self.enhanced_available:
            return await self.enhanced_tool.health_check()

        return {
            "healthy": True,
            "search_engines": len(self.search_engines),
            "available_tools": self.available_tools,
            "enhanced_available": False,
            "note": "Using fallback mock search - configure API keys for real search"
        }
