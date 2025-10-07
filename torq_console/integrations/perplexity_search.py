#!/usr/bin/env python3
"""
Perplexity Search API Integration for TORQ Console
Provides access to Perplexity's advanced search capabilities
"""

import os
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class PerplexitySearchResult:
    """Structure for Perplexity search results"""
    content: str
    sources: List[str]
    query: str
    model: str
    usage: Dict[str, Any]
    timestamp: datetime

class PerplexitySearchAPI:
    """
    Perplexity Search API Integration

    Provides access to Perplexity's search capabilities through their API
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if not self.api_key:
            logger.warning("Perplexity API key not found. Set PERPLEXITY_API_KEY environment variable.")

    async def search(self,
                    query: str,
                    model: str = "sonar",
                    max_tokens: int = 1000,
                    temperature: float = 0.2,
                    top_p: float = 0.9,
                    search_domain_filter: Optional[List[str]] = None,
                    return_images: bool = False,
                    return_related_questions: bool = True,
                    search_recency_filter: Optional[str] = None) -> PerplexitySearchResult:
        """
        Perform a search using Perplexity API

        Args:
            query: Search query
            model: Model to use (e.g., 'llama-3.1-sonar-small-128k-online')
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            search_domain_filter: List of domains to search within
            return_images: Whether to return images
            return_related_questions: Whether to return related questions
            search_recency_filter: Filter by recency ('month', 'week', 'day')

        Returns:
            PerplexitySearchResult with search results and metadata
        """

        if not self.api_key:
            raise ValueError("Perplexity API key is required")

        # Construct the messages for Perplexity API
        messages = [
            {
                "role": "system",
                "content": "You are a helpful research assistant. Provide comprehensive, accurate information with proper citations."
            },
            {
                "role": "user",
                "content": query
            }
        ]

        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "return_citations": True,
            "search_domain_filter": search_domain_filter,
            "return_images": return_images,
            "return_related_questions": return_related_questions,
            "search_recency_filter": search_recency_filter
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        return self._parse_response(data, query, model)
                    else:
                        error_text = await response.text()
                        logger.error(f"Perplexity API error {response.status}: {error_text}")
                        raise Exception(f"Perplexity API error: {response.status} - {error_text}")

        except asyncio.TimeoutError:
            logger.error("Perplexity API request timed out")
            raise Exception("Perplexity API request timed out")
        except Exception as e:
            logger.error(f"Error calling Perplexity API: {e}")
            raise

    def _parse_response(self, data: Dict[str, Any], query: str, model: str) -> PerplexitySearchResult:
        """Parse Perplexity API response"""

        try:
            # Extract main content
            content = data['choices'][0]['message']['content']

            # Extract citations/sources
            sources = []
            if 'citations' in data:
                sources = data['citations']
            elif 'choices' in data and len(data['choices']) > 0:
                choice = data['choices'][0]
                if 'citations' in choice:
                    sources = choice['citations']

            # Extract usage information
            usage = data.get('usage', {})

            return PerplexitySearchResult(
                content=content,
                sources=sources,
                query=query,
                model=model,
                usage=usage,
                timestamp=datetime.now()
            )

        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing Perplexity response: {e}")
            raise Exception(f"Invalid response format from Perplexity API: {e}")

    async def search_with_domain_filter(self, query: str, domains: List[str]) -> PerplexitySearchResult:
        """Search within specific domains"""
        return await self.search(query, search_domain_filter=domains)

    async def search_recent(self, query: str, recency: str = "month") -> PerplexitySearchResult:
        """Search for recent information"""
        return await self.search(query, search_recency_filter=recency)

    async def search_academic(self, query: str) -> PerplexitySearchResult:
        """Search academic sources"""
        academic_domains = [
            "arxiv.org",
            "scholar.google.com",
            "pubmed.ncbi.nlm.nih.gov",
            "ieee.org",
            "acm.org"
        ]
        return await self.search(query, search_domain_filter=academic_domains)

    async def search_news(self, query: str) -> PerplexitySearchResult:
        """Search news sources"""
        news_domains = [
            "reuters.com",
            "bbc.com",
            "cnn.com",
            "npr.org",
            "apnews.com"
        ]
        return await self.search(query, search_domain_filter=news_domains, search_recency_filter="week")

    def format_result_for_display(self, result: PerplexitySearchResult) -> Dict[str, Any]:
        """Format search result for display in TORQ Console"""

        formatted_sources = []
        for i, source in enumerate(result.sources[:10], 1):  # Limit to 10 sources
            if isinstance(source, str):
                formatted_sources.append(f"{i}. {source}")
            elif isinstance(source, dict):
                url = source.get('url', 'Unknown source')
                title = source.get('title', url)
                formatted_sources.append(f"{i}. [{title}]({url})")

        return {
            "query": result.query,
            "content": result.content,
            "sources": formatted_sources,
            "model": result.model,
            "usage": result.usage,
            "timestamp": result.timestamp.isoformat(),
            "source_count": len(result.sources),
            "provider": "Perplexity"
        }

# Factory function for easy integration
def create_perplexity_search_client(api_key: Optional[str] = None) -> PerplexitySearchAPI:
    """Create a Perplexity Search API client"""
    return PerplexitySearchAPI(api_key)

# Test function
async def test_perplexity_search():
    """Test Perplexity search functionality"""
    try:
        client = create_perplexity_search_client()
        result = await client.search("What are the latest developments in AI coding assistants?")

        print("Perplexity Search Test Results:")
        print(f"Query: {result.query}")
        print(f"Content length: {len(result.content)} characters")
        print(f"Sources found: {len(result.sources)}")
        print(f"Model used: {result.model}")
        print(f"Usage: {result.usage}")

        return True

    except Exception as e:
        print(f"Perplexity search test failed: {e}")
        return False

if __name__ == "__main__":
    # Run test
    asyncio.run(test_perplexity_search())