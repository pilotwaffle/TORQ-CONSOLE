"""
Reddit Search Plugin

Searches Reddit posts and comments for relevant discussions.
Uses Reddit's JSON API (no authentication required for read-only access).
"""

import aiohttp
from typing import List
from ..base import SearchPlugin, PluginMetadata, SearchResult


class RedditSearchPlugin(SearchPlugin):
    """
    Search Reddit for posts and discussions.

    Features:
    - Search across all subreddits
    - Filter by relevance or recency
    - Extract post titles, content, and scores
    - No API key required
    """

    def __init__(self):
        """Initialize the Reddit search plugin."""
        super().__init__()

        self.metadata = PluginMetadata(
            name="reddit",
            version="1.0.0",
            description="Search Reddit posts and comments for discussions",
            author="TORQ Team",
            supports_news=False,
            supports_academic=False,
            supports_general=True,
            requires_api_key=False,
            max_requests_per_minute=30,  # Reddit's rate limit
            max_requests_per_hour=1000,
            homepage="https://www.reddit.com",
            tags=["social", "discussions", "community"]
        )

        self.base_url = "https://www.reddit.com"
        self.user_agent = "TORQ Console Search Plugin/1.0"

    async def search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "general"
    ) -> List[SearchResult]:
        """
        Search Reddit for posts matching the query.

        Args:
            query: Search query
            max_results: Maximum number of results (max 100)
            search_type: Type of search (only 'general' supported)

        Returns:
            List of SearchResult objects
        """
        results = []

        try:
            # Build search URL
            search_url = f"{self.base_url}/search.json"
            params = {
                'q': query,
                'limit': min(max_results, 100),  # Reddit max is 100
                'sort': 'relevance',  # or 'new', 'top'
                'type': 'link'  # Search posts, not comments
            }

            headers = {
                'User-Agent': self.user_agent
            }

            # Make request
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Parse results
                        posts = data.get('data', {}).get('children', [])

                        for post_data in posts:
                            post = post_data.get('data', {})

                            # Extract post information
                            title = post.get('title', '')
                            selftext = post.get('selftext', '')[:300]  # First 300 chars
                            url = f"{self.base_url}{post.get('permalink', '')}"
                            subreddit = post.get('subreddit', '')
                            author = post.get('author', '')
                            score = post.get('score', 0)
                            num_comments = post.get('num_comments', 0)

                            # Create snippet from selftext or title
                            snippet = selftext if selftext else title

                            # Create search result
                            result = SearchResult(
                                title=title,
                                snippet=snippet,
                                url=url,
                                source=f"reddit://r/{subreddit}",
                                author=author,
                                score=float(score),
                                metadata={
                                    'subreddit': subreddit,
                                    'comments': num_comments,
                                    'upvotes': score
                                }
                            )

                            results.append(result)

                    else:
                        self.logger.error(f"Reddit API error: HTTP {response.status}")

        except Exception as e:
            self.logger.error(f"Reddit search failed: {e}")

        return results

    async def initialize(self) -> bool:
        """Initialize the plugin."""
        self.logger.info("[REDDIT_PLUGIN] Reddit search plugin initialized")
        return await super().initialize()
