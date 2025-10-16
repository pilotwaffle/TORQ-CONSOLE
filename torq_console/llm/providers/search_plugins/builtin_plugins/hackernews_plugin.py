"""
Hacker News Search Plugin

Searches Hacker News for tech news and discussions using Algolia's HN Search API.
"""

import aiohttp
from typing import List
from ..base import SearchPlugin, PluginMetadata, SearchResult


class HackerNewsSearchPlugin(SearchPlugin):
    """
    Search Hacker News for tech news and discussions.

    Features:
    - Search stories, comments, and Ask HN posts
    - Filter by date, popularity
    - No API key required (uses Algolia HN Search)
    """

    def __init__(self):
        """Initialize the Hacker News search plugin."""
        super().__init__()

        self.metadata = PluginMetadata(
            name="hackernews",
            version="1.0.0",
            description="Search Hacker News for tech news and discussions",
            author="TORQ Team",
            supports_news=True,
            supports_academic=False,
            supports_general=True,
            requires_api_key=False,
            max_requests_per_minute=60,
            max_requests_per_hour=3000,
            homepage="https://news.ycombinator.com",
            documentation="https://hn.algolia.com/api",
            tags=["tech", "news", "startups", "programming"]
        )

        self.api_url = "https://hn.algolia.com/api/v1/search"

    async def search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "general"
    ) -> List[SearchResult]:
        """
        Search Hacker News.

        Args:
            query: Search query
            max_results: Maximum number of results
            search_type: Type of search (general or news)

        Returns:
            List of SearchResult objects
        """
        results = []

        try:
            # Build search parameters
            params = {
                'query': query,
                'tags': 'story',  # Only search stories (not comments)
                'hitsPerPage': min(max_results, 100)
            }

            # Make request
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Parse results
                        hits = data.get('hits', [])

                        for hit in hits:
                            # Extract story information
                            title = hit.get('title', '')
                            url = hit.get('url', '')

                            # If no external URL, use HN discussion URL
                            if not url:
                                object_id = hit.get('objectID', '')
                                url = f"https://news.ycombinator.com/item?id={object_id}"

                            author = hit.get('author', '')
                            points = hit.get('points', 0)
                            num_comments = hit.get('num_comments', 0)
                            created_at = hit.get('created_at', '')

                            # Create snippet from title and metadata
                            snippet = f"{points} points | {num_comments} comments"

                            # Create search result
                            result = SearchResult(
                                title=title,
                                snippet=snippet,
                                url=url,
                                source="hackernews",
                                author=author,
                                date_published=created_at,
                                score=float(points),
                                metadata={
                                    'points': points,
                                    'comments': num_comments,
                                    'story_id': hit.get('objectID', ''),
                                    'created_at': created_at
                                }
                            )

                            results.append(result)

                    else:
                        self.logger.error(f"HackerNews API error: HTTP {response.status}")

        except Exception as e:
            self.logger.error(f"HackerNews search failed: {e}")

        return results

    async def initialize(self) -> bool:
        """Initialize the plugin."""
        self.logger.info("[HACKERNEWS_PLUGIN] HackerNews search plugin initialized")
        return await super().initialize()
