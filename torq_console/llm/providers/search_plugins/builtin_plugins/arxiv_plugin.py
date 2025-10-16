"""
ArXiv Search Plugin

Searches arXiv.org for academic papers and preprints.
Uses the arXiv API for searching scientific publications.
"""

import aiohttp
import xml.etree.ElementTree as ET
from typing import List
from ..base import SearchPlugin, PluginMetadata, SearchResult


class ArXivSearchPlugin(SearchPlugin):
    """
    Search arXiv for academic papers and preprints.

    Features:
    - Search across all arXiv categories
    - Get paper abstracts, authors, and metadata
    - Filter by category, date
    - No API key required
    """

    def __init__(self):
        """Initialize the arXiv search plugin."""
        super().__init__()

        self.metadata = PluginMetadata(
            name="arxiv",
            version="1.0.0",
            description="Search arXiv for academic papers and scientific preprints",
            author="TORQ Team",
            supports_news=False,
            supports_academic=True,
            supports_general=True,
            requires_api_key=False,
            max_requests_per_minute=3,  # ArXiv rate limit (3 sec delay between requests)
            max_requests_per_hour=100,
            homepage="https://arxiv.org",
            documentation="https://arxiv.org/help/api",
            tags=["academic", "research", "papers", "science"]
        )

        self.api_url = "http://export.arxiv.org/api/query"

    async def search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "academic"
    ) -> List[SearchResult]:
        """
        Search arXiv for papers.

        Args:
            query: Search query
            max_results: Maximum number of results
            search_type: Type of search (academic recommended)

        Returns:
            List of SearchResult objects
        """
        results = []

        try:
            # Build search parameters
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': min(max_results, 100),
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }

            # Make request
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params) as response:
                    if response.status == 200:
                        xml_content = await response.text()

                        # Parse XML response
                        root = ET.fromstring(xml_content)

                        # Define namespace
                        ns = {
                            'atom': 'http://www.w3.org/2005/Atom',
                            'arxiv': 'http://arxiv.org/schemas/atom'
                        }

                        # Parse entries
                        for entry in root.findall('atom:entry', ns):
                            # Extract paper information
                            title_elem = entry.find('atom:title', ns)
                            title = title_elem.text.strip() if title_elem is not None else ''

                            summary_elem = entry.find('atom:summary', ns)
                            abstract = summary_elem.text.strip()[:300] if summary_elem is not None else ''

                            link_elem = entry.find('atom:id', ns)
                            url = link_elem.text.strip() if link_elem is not None else ''

                            published_elem = entry.find('atom:published', ns)
                            published = published_elem.text if published_elem is not None else ''

                            # Extract authors
                            authors = []
                            for author_elem in entry.findall('atom:author', ns):
                                name_elem = author_elem.find('atom:name', ns)
                                if name_elem is not None:
                                    authors.append(name_elem.text.strip())

                            author_str = ', '.join(authors[:3])  # First 3 authors
                            if len(authors) > 3:
                                author_str += f' et al. ({len(authors)} authors)'

                            # Extract category
                            category_elem = entry.find('arxiv:primary_category', ns)
                            category = ''
                            if category_elem is not None:
                                category = category_elem.get('term', '')

                            # Create search result
                            result = SearchResult(
                                title=title,
                                snippet=abstract,
                                url=url,
                                source=f"arxiv:{category}",
                                author=author_str,
                                date_published=published,
                                metadata={
                                    'category': category,
                                    'authors': authors,
                                    'published': published
                                }
                            )

                            results.append(result)

                    else:
                        self.logger.error(f"ArXiv API error: HTTP {response.status}")

        except Exception as e:
            self.logger.error(f"ArXiv search failed: {e}")

        return results

    async def initialize(self) -> bool:
        """Initialize the plugin."""
        self.logger.info("[ARXIV_PLUGIN] ArXiv search plugin initialized")
        return await super().initialize()
