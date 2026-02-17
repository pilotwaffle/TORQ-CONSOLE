#!/usr/bin/env python3
"""
TORQ SearchMaster Agent - Specialized Search Intelligence

A dedicated search agent that handles comprehensive information retrieval
across multiple domains and sources. Feeds high-quality results to other
agents like Prince Flowers.

Architecture:
- Multi-API support (Crypto, General, News, Academic)
- Intelligent source selection based on query type
- Result ranking and deduplication
- Structured output for downstream agents

Author: TORQ Console Team
Version: 1.0.0
"""

import asyncio
import aiohttp
import logging
import os
import re
from typing import Dict, List, Any, Optional, Tuple, Union, Protocol
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json


# Output Modes for different user personas
class OutputMode(Enum):
    """Output formatting modes for different use cases"""
    SIMPLE = "simple"      # Casual users - just the answer (1-3 lines)
    STANDARD = "standard"  # Default - balanced detail (10-20 lines)
    DETAILED = "detailed"  # Analysts - full verification + markdown tables
    TECHNICAL = "technical" # Developers - JSON + debug info


# Output Formatter Protocol
class OutputFormatter(Protocol):
    """Interface for output formatters"""
    def format(self, report: 'SearchReport', agent: 'TORQSearchMaster') -> Union[str, Dict]:
        """Format search report according to mode"""
        ...


@dataclass
class SearchResult:
    """Structured search result"""
    title: str
    snippet: str
    url: str
    source: str  # API source (CoinGecko, Tavily, etc.)
    relevance_score: float
    published_date: Optional[str] = None
    full_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_structured_data: bool = False
    is_ai_synthesis: bool = False
    verification_status: str = "unverified"  # "verified" | "partial" | "unverified"
    corroborating_sources: List[str] = None  # Sources that confirm this claim

    def __post_init__(self):
        """Initialize corroborating_sources if None"""
        if self.corroborating_sources is None:
            self.corroborating_sources = []


@dataclass
class SearchReport:
    """Complete search report for downstream agents with validation"""
    query: str
    query_type: str  # crypto, news, general, academic
    total_results: int
    results: List[SearchResult]
    sources_used: List[str]
    search_duration: float
    timestamp: str
    confidence: float
    summary: Optional[str] = None
    # Enhanced validation fields
    confidence_level: str = "unverified"  # "verified" | "partial" | "unverified"
    overall_confidence: float = 0.0  # 0.0 - 1.0 based on corroboration
    limitations: List[str] = None  # API failures, data gaps
    next_steps: List[str] = None  # Suggested follow-up actions
    verification_details: Dict[str, Any] = None  # Detailed corroboration info

    def __post_init__(self):
        """Initialize lists if None"""
        if self.limitations is None:
            self.limitations = []
        if self.next_steps is None:
            self.next_steps = []
        if self.verification_details is None:
            self.verification_details = {}


class TORQSearchMaster:
    """
    SearchMaster Agent - Comprehensive Multi-Source Search Intelligence

    Capabilities:
    - Cryptocurrency data (CoinGecko, CoinMarketCap)
    - General web search (Tavily, Brave, Google)
    - News aggregation (Perplexity, NewsAPI)
    - Academic research (Semantic Scholar, arXiv)
    - Domain-specific search optimization
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize SearchMaster with multi-API support"""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # API Keys
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY')
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        self.perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        self.brave_api_key = os.getenv('BRAVE_SEARCH_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.google_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

        # Available search sources
        self.search_sources = self._initialize_search_sources()

        # Query type detection patterns
        self.query_patterns = {
            'crypto': ['cryptocurrency', 'crypto', 'coin', 'token', 'blockchain',
                      'bitcoin', 'ethereum', 'defi', 'nft', 'web3', 'ckb', 'nervos'],
            'news': ['news', 'latest', 'recent', 'update', 'announcement',
                    'breaking', 'today', 'yesterday', 'developments'],
            'academic': ['research', 'study', 'paper', 'journal', 'scientific',
                        'arxiv', 'doi', 'citation'],
            'tech': ['api', 'code', 'programming', 'software', 'framework',
                    'library', 'github', 'documentation']
        }

        # Enhanced validation configuration
        self.default_recency_days = self.config.get('recency_days', 30)  # 30-day default (expanded from 7 to reduce false negatives)
        self.require_corroboration = self.config.get('require_corroboration', True)
        self.min_sources_for_verification = self.config.get('min_sources', 2)

        # Track failed APIs during search
        self.failed_apis = []
        self.api_errors = {}

        self.logger.info(f"SearchMaster initialized with {len(self.search_sources)} sources")
        self.logger.info(f"Corroboration required: {self.require_corroboration} (min {self.min_sources_for_verification} sources)")
        self.logger.info(f"Default recency window: {self.default_recency_days} days (auto-disabled for ambiguous/technical queries)")

    def _initialize_search_sources(self) -> Dict[str, bool]:
        """Check which search sources are available"""
        sources = {
            'coingecko': bool(self.coingecko_api_key),
            'tavily': bool(self.tavily_api_key),
            'perplexity': bool(self.perplexity_api_key),
            'brave': bool(self.brave_api_key),
            'google': bool(self.google_api_key and self.google_engine_id),
            'fallback': True  # Always available
        }

        available = [k for k, v in sources.items() if v]
        self.logger.info(f"Available search sources: {available}")

        return sources

    def detect_query_type(self, query: str) -> Tuple[str, float]:
        """
        Detect query type and return confidence score

        Returns:
            Tuple of (query_type, confidence)
        """
        query_lower = query.lower()

        # Check each pattern type
        scores = {}
        for qtype, patterns in self.query_patterns.items():
            matches = sum(1 for p in patterns if p in query_lower)
            if matches > 0:
                scores[qtype] = matches / len(patterns)

        if not scores:
            return 'general', 0.5

        # Get highest scoring type
        best_type = max(scores.items(), key=lambda x: x[1])
        return best_type[0], best_type[1]

    async def search(
        self,
        query: str,
        max_results: int = 10,
        query_type: Optional[str] = None,
        include_summary: bool = True,
        recency_days: Optional[int] = None
    ) -> SearchReport:
        """
        Comprehensive search across multiple sources with validation

        Args:
            query: Search query
            max_results: Maximum results to return
            query_type: Force specific query type (auto-detect if None)
            include_summary: Generate AI summary of results
            recency_days: Filter results to last N days (default: 7 for news, None for others)

        Returns:
            SearchReport with validated, ranked, deduplicated results
        """
        start_time = asyncio.get_event_loop().time()

        # Reset failed API tracking
        self.failed_apis = []
        self.api_errors = {}

        # Detect query type if not specified
        if not query_type:
            query_type, confidence = self.detect_query_type(query)
            self.logger.info(f"Detected query type: {query_type} (confidence: {confidence:.2f})")
        else:
            confidence = 1.0

        # Set recency filter (default 30 days for news - expanded from 7 to reduce false negatives)
        # DISABLE auto-filter if:
        # 1. Query has explicit date requirement ('since', 'from', 'after', 'before')
        # 2. Query uses ambiguous date terms ('latest', 'recent', 'news') - let APIs handle it
        # 3. Query is technical/docs (not time-sensitive)
        has_explicit_date = any(keyword in query.lower() for keyword in [' since ', ' from ', ' after ', ' before '])
        has_ambiguous_date = any(keyword in query.lower() for keyword in ['latest', 'recent', 'news', 'update'])
        is_technical_query = any(keyword in query.lower() for keyword in ['api', 'docs', 'documentation', 'tutorial', '.cpp', '.py', '.js'])

        # Only apply auto-recency if query type is news AND no ambiguous date terms AND not technical
        if recency_days is None and query_type == 'news' and not has_explicit_date and not has_ambiguous_date and not is_technical_query:
            recency_days = 30  # Expanded from 7 days to 30 days to reduce false negatives
            self.logger.info(f"Applying default {recency_days}-day recency filter for news query")
        elif has_explicit_date:
            self.logger.info("Query has explicit date requirement - skipping auto-recency filter")
        elif has_ambiguous_date or is_technical_query:
            self.logger.info(f"Query has ambiguous date terms or is technical - skipping auto-recency filter")

        # Select optimal search sources for query type
        search_tasks = self._build_search_tasks(query, query_type, max_results)

        # Execute searches in parallel
        self.logger.info(f"Executing {len(search_tasks)} parallel searches for: {query[:100]}")
        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Process and merge results
        all_results = []
        sources_used = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = str(result)
                self.logger.warning(f"Search task {i} failed: {error_msg}")
                self.failed_apis.append(f"Task {i}")
                self.api_errors[f"task_{i}"] = error_msg
                continue

            if result and 'results' in result:
                all_results.extend(result['results'])
                if 'source' in result:
                    sources_used.append(result['source'])
            elif result and 'error' in result:
                # API returned error status
                api_name = result.get('source', 'unknown')
                error_msg = result.get('error', 'Unknown error')
                self.failed_apis.append(api_name)
                self.api_errors[api_name] = error_msg

        # Apply recency filter if specified
        if recency_days:
            all_results = self._apply_recency_filter(all_results, recency_days)
            self.logger.info(f"Applied {recency_days}-day recency filter")

        # Deduplicate and rank results
        final_results = self._deduplicate_and_rank(all_results, max_results)

        # Perform corroboration analysis
        verification_details = {}
        if self.require_corroboration and final_results:
            final_results, verification_details = self._validate_corroboration(final_results)

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            final_results, len(sources_used), len(self.failed_apis)
        )

        # Determine confidence level
        if overall_confidence >= 0.8:
            confidence_level = "verified"
        elif overall_confidence >= 0.5:
            confidence_level = "partial"
        else:
            confidence_level = "unverified"

        # Generate limitations report
        limitations = self._generate_limitations()

        # Generate next steps suggestions
        next_steps = self._generate_next_steps(
            query_type, len(final_results), len(sources_used), limitations
        )

        # Generate summary if requested
        summary = None
        if include_summary and final_results:
            summary = self._generate_summary(query, final_results)

        # Build search report
        duration = asyncio.get_event_loop().time() - start_time

        report = SearchReport(
            query=query,
            query_type=query_type,
            total_results=len(final_results),
            results=final_results,
            sources_used=sources_used,
            search_duration=duration,
            timestamp=datetime.now().isoformat(),
            confidence=confidence,
            summary=summary,
            confidence_level=confidence_level,
            overall_confidence=overall_confidence,
            limitations=limitations,
            next_steps=next_steps,
            verification_details=verification_details
        )

        self.logger.info(
            f"Search complete: {len(final_results)} results from {len(sources_used)} sources "
            f"in {duration:.2f}s | Confidence: {confidence_level} ({overall_confidence:.2f})"
        )

        return report

    def _build_search_tasks(
        self,
        query: str,
        query_type: str,
        max_results: int
    ) -> List[asyncio.Task]:
        """Build list of search tasks based on query type and available sources"""
        tasks = []

        # Crypto-specific queries
        if query_type == 'crypto':
            if self.search_sources['coingecko']:
                tasks.append(self._search_coingecko(query))
            if self.search_sources['tavily']:
                tasks.append(self._search_tavily(query, 'news'))

        # News queries
        elif query_type == 'news':
            if self.search_sources['tavily']:
                tasks.append(self._search_tavily(query, 'news'))
            if self.search_sources['perplexity']:
                tasks.append(self._search_perplexity(query, 'news'))
            if self.search_sources['brave']:
                tasks.append(self._search_brave(query, 'news'))

        # General queries - use multiple sources for better coverage
        else:
            if self.search_sources['tavily']:
                tasks.append(self._search_tavily(query, 'general'))
            if self.search_sources['perplexity']:
                tasks.append(self._search_perplexity(query, 'general'))
            if self.search_sources['brave']:
                tasks.append(self._search_brave(query, 'general'))

        return tasks

    async def _search_coingecko(self, query: str) -> Dict[str, Any]:
        """Search CoinGecko for cryptocurrency data"""
        try:
            self.logger.info(f"[CoinGecko] Searching for: {query}")

            # Extract crypto name/symbol
            crypto_name = self._extract_crypto_identifier(query)

            base_url = "https://api.coingecko.com/api/v3"
            headers = {}
            if self.coingecko_api_key:
                headers['x-cg-demo-api-key'] = self.coingecko_api_key

            async with aiohttp.ClientSession() as session:
                # Search for coin
                async with session.get(
                    f"{base_url}/search",
                    params={'query': crypto_name},
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return {'results': [], 'source': 'coingecko'}

                    search_data = await response.json()

                if not search_data.get('coins'):
                    return {'results': [], 'source': 'coingecko'}

                # Get detailed data for top match
                coin_id = search_data['coins'][0]['id']
                async with session.get(
                    f"{base_url}/coins/{coin_id}",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return {'results': [], 'source': 'coingecko'}

                    coin_data = await response.json()

            # Format as SearchResult
            price_data = coin_data['market_data']
            result = SearchResult(
                title=f"{coin_data['name']} ({coin_data['symbol'].upper()}) Market Data",
                snippet=(
                    f"Price: ${price_data['current_price']['usd']:,.6f} | "
                    f"24h Change: {price_data['price_change_percentage_24h']:.2f}% | "
                    f"Market Cap: ${price_data['market_cap']['usd']:,.0f} | "
                    f"Volume: ${price_data['total_volume']['usd']:,.0f} | "
                    f"Supply: {price_data['circulating_supply']:,.0f} {coin_data['symbol'].upper()}"
                ),
                url=coin_data['links']['homepage'][0] if coin_data['links']['homepage'] else '',
                source='CoinGecko API',
                relevance_score=1.0,
                is_structured_data=True,
                metadata={
                    'price_usd': price_data['current_price']['usd'],
                    'market_cap': price_data['market_cap']['usd'],
                    'volume_24h': price_data['total_volume']['usd'],
                    'price_change_24h': price_data['price_change_percentage_24h'],
                    'description': coin_data.get('description', {}).get('en', ''),
                    'categories': coin_data.get('categories', []),
                    'links': coin_data.get('links', {})
                }
            )

            self.logger.info(f"[CoinGecko] Found: {coin_data['name']} (${price_data['current_price']['usd']})")

            return {'results': [result], 'source': 'coingecko'}

        except Exception as e:
            self.logger.error(f"CoinGecko search failed: {e}")
            return {'results': [], 'source': 'coingecko'}

    async def _search_tavily(self, query: str, search_type: str) -> Dict[str, Any]:
        """Search using Tavily AI"""
        try:
            from tavily import TavilyClient

            self.logger.info(f"[Tavily] Searching for: {query} (type: {search_type})")

            # Initialize Tavily client
            client = TavilyClient(api_key=self.tavily_api_key)

            # Perform search
            response = client.search(
                query=query,
                search_depth="advanced" if search_type == 'news' else "basic",
                max_results=5
            )

            # Convert to SearchResults
            results = []
            for item in response.get('results', []):
                results.append(SearchResult(
                    title=item.get('title', ''),
                    snippet=item.get('content', ''),
                    url=item.get('url', ''),
                    source='Tavily AI',
                    relevance_score=item.get('score', 0.8),
                    published_date=item.get('published_date'),
                    metadata={
                        'raw_content': item.get('raw_content'),
                        'relevance_score': item.get('score')
                    }
                ))

            self.logger.info(f"[Tavily] Found {len(results)} results")
            return {'results': results, 'source': 'tavily'}

        except ImportError:
            self.logger.warning("[Tavily] Not implemented - install tavily-python package")
            return {'results': [], 'source': 'tavily'}
        except Exception as e:
            self.logger.error(f"Tavily search failed: {e}")
            return {'results': [], 'source': 'tavily'}

    async def _search_perplexity(self, query: str, search_type: str) -> Dict[str, Any]:
        """Search using Perplexity API"""
        try:
            self.logger.info(f"[Perplexity] Searching for: {query}")

            # Import existing Perplexity integration
            from ..integrations.perplexity_search import create_perplexity_search_client

            client = create_perplexity_search_client(self.perplexity_api_key)

            if search_type == 'news':
                result = await client.search_news(query)
            else:
                result = await client.search(query, max_tokens=1000)

            # Convert to SearchResult
            search_result = SearchResult(
                title=f"Perplexity AI Analysis: {query[:100]}",
                snippet=result.content,
                url='https://www.perplexity.ai',
                source='Perplexity AI',
                relevance_score=0.95,
                full_content=result.content,
                is_ai_synthesis=True,
                metadata={
                    'model': result.model,
                    'sources': result.sources,
                    'usage': result.usage
                }
            )

            return {'results': [search_result], 'source': 'perplexity'}

        except Exception as e:
            self.logger.error(f"Perplexity search failed: {e}")
            return {'results': [], 'source': 'perplexity'}

    async def _search_brave(self, query: str, search_type: str) -> Dict[str, Any]:
        """Search using Brave Search API"""
        try:
            self.logger.info(f"[Brave] Searching for: {query}")

            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                'X-Subscription-Token': self.brave_api_key,
                'Accept': 'application/json'
            }
            params = {
                'q': query,
                'count': 10
            }

            if search_type == 'news':
                params['freshness'] = 'pd'  # Past day

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        return {'results': [], 'source': 'brave'}

                    data = await response.json()

            # Convert to SearchResults
            results = []
            for item in data.get('web', {}).get('results', []):
                results.append(SearchResult(
                    title=item.get('title', ''),
                    snippet=item.get('description', ''),
                    url=item.get('url', ''),
                    source='Brave Search',
                    relevance_score=0.8,
                    published_date=item.get('age')
                ))

            return {'results': results, 'source': 'brave'}

        except Exception as e:
            self.logger.error(f"Brave search failed: {e}")
            return {'results': [], 'source': 'brave'}

    async def _search_google(self, query: str) -> Dict[str, Any]:
        """Search using Google Custom Search API"""
        try:
            self.logger.info(f"[Google] Searching for: {query}")

            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_engine_id,
                'q': query,
                'num': 10
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return {'results': [], 'source': 'google'}

                    data = await response.json()

            # Convert to SearchResults
            results = []
            for item in data.get('items', []):
                results.append(SearchResult(
                    title=item.get('title', ''),
                    snippet=item.get('snippet', ''),
                    url=item.get('link', ''),
                    source='Google Search',
                    relevance_score=0.85
                ))

            return {'results': results, 'source': 'google'}

        except Exception as e:
            self.logger.error(f"Google search failed: {e}")
            return {'results': [], 'source': 'google'}

    def _deduplicate_and_rank(
        self,
        results: List[SearchResult],
        max_results: int
    ) -> List[SearchResult]:
        """Deduplicate and rank search results"""

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []

        for result in results:
            if result.url and result.url in seen_urls:
                continue

            seen_urls.add(result.url)
            unique_results.append(result)

        # Sort by relevance score (descending)
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)

        # Boost structured data to top
        structured = [r for r in unique_results if r.is_structured_data]
        non_structured = [r for r in unique_results if not r.is_structured_data]

        # Return structured first, then others
        return (structured + non_structured)[:max_results]

    def _apply_recency_filter(
        self,
        results: List[SearchResult],
        recency_days: int
    ) -> List[SearchResult]:
        """Filter results to only those published within the last N days"""
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=recency_days)
        filtered_results = []

        for result in results:
            # If no published date, keep it (might be current data like CoinGecko)
            if not result.published_date:
                if result.is_structured_data:
                    filtered_results.append(result)
                continue

            try:
                # Parse various date formats
                pub_date = self._parse_date(result.published_date)
                if pub_date and pub_date >= cutoff_date:
                    filtered_results.append(result)
            except Exception as e:
                # If can't parse date, keep result
                self.logger.debug(f"Could not parse date '{result.published_date}': {e}")
                filtered_results.append(result)

        self.logger.info(
            f"Recency filter: {len(results)} -> {len(filtered_results)} results "
            f"(last {recency_days} days)"
        )

        return filtered_results

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string in various formats"""
        from dateutil import parser as date_parser

        try:
            return date_parser.parse(date_str)
        except:
            return None

    def _validate_corroboration(
        self,
        results: List[SearchResult]
    ) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """
        Validate facts through corroboration across multiple sources

        Requires at least 2 independent sources for verification.
        Flags single-source claims as "Unverified - Single Source"
        """
        # Extract factual claims from results
        claims_by_fact = {}  # fact_signature -> [result_indices]

        for i, result in enumerate(results):
            # Extract key facts from snippet
            facts = self._extract_factual_claims(result.snippet, result.metadata)

            for fact in facts:
                if fact not in claims_by_fact:
                    claims_by_fact[fact] = []
                claims_by_fact[fact].append((i, result.source))

        # Determine verification status for each result
        verification_summary = {
            'verified_claims': 0,
            'partial_claims': 0,
            'unverified_claims': 0,
            'claims_detail': {}
        }

        for i, result in enumerate(results):
            # Extract this result's facts
            result_facts = self._extract_factual_claims(result.snippet, result.metadata)

            # Count how many sources corroborate each fact
            corroborating_sources = set()
            verified_facts = 0
            partial_facts = 0
            unverified_facts = 0

            for fact in result_facts:
                sources_for_fact = set(src for idx, src in claims_by_fact.get(fact, []))
                num_sources = len(sources_for_fact)

                if num_sources >= self.min_sources_for_verification:
                    verified_facts += 1
                    corroborating_sources.update(sources_for_fact)
                elif num_sources > 1:
                    partial_facts += 1
                    corroborating_sources.update(sources_for_fact)
                else:
                    unverified_facts += 1

            # Determine overall verification status for this result
            if len(result_facts) == 0:
                # No extractable facts (maybe AI synthesis)
                result.verification_status = "partial"
            elif verified_facts == len(result_facts):
                result.verification_status = "verified"
                verification_summary['verified_claims'] += 1
            elif verified_facts + partial_facts >= len(result_facts) / 2:
                result.verification_status = "partial"
                verification_summary['partial_claims'] += 1
            else:
                result.verification_status = "unverified"
                verification_summary['unverified_claims'] += 1

            result.corroborating_sources = list(corroborating_sources)

        self.logger.info(
            f"Corroboration: {verification_summary['verified_claims']} verified, "
            f"{verification_summary['partial_claims']} partial, "
            f"{verification_summary['unverified_claims']} unverified"
        )

        return results, verification_summary

    def _extract_factual_claims(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[str]:
        """
        Extract verifiable factual claims from text

        Focuses on:
        - Numbers (prices, percentages, volumes)
        - Dates and timeframes
        - Named entities (people, orgs, places)
        - Specific events
        """
        claims = []

        # Extract price data
        price_pattern = r'\$[\d,]+\.?\d*'
        prices = re.findall(price_pattern, text)
        claims.extend([f"price:{p}" for p in prices])

        # Extract percentages
        percent_pattern = r'[\+\-]?\d+\.?\d*%'
        percentages = re.findall(percent_pattern, text)
        claims.extend([f"change:{p}" for p in percentages])

        # Extract large numbers (market cap, volume)
        large_num_pattern = r'\$[\d,]+[MBT]'
        large_nums = re.findall(large_num_pattern, text)
        claims.extend([f"volume:{n}" for n in large_nums])

        # Extract from metadata (structured data)
        if metadata:
            if 'price_usd' in metadata:
                claims.append(f"price:${metadata['price_usd']}")
            if 'price_change_24h' in metadata:
                claims.append(f"change:{metadata['price_change_24h']}%")
            if 'market_cap' in metadata:
                claims.append(f"marketcap:${metadata['market_cap']}")

        return claims

    def _calculate_overall_confidence(
        self,
        results: List[SearchResult],
        num_sources: int,
        num_failed: int
    ) -> float:
        """
        Calculate overall confidence score for the search

        Factors:
        - Number of sources used
        - Verification status of results
        - Failed API count
        - Presence of structured data
        """
        if not results:
            return 0.0

        # Base confidence from sources
        source_confidence = min(num_sources / 3.0, 1.0)  # Cap at 3+ sources

        # Verification confidence
        verified_count = sum(1 for r in results if r.verification_status == "verified")
        partial_count = sum(1 for r in results if r.verification_status == "partial")
        verification_confidence = (verified_count + 0.5 * partial_count) / len(results)

        # Structured data bonus
        structured_count = sum(1 for r in results if r.is_structured_data)
        structured_bonus = min(structured_count * 0.1, 0.2)

        # Penalty for failed APIs
        failure_penalty = num_failed * 0.1

        # Calculate weighted confidence
        overall = (
            0.4 * source_confidence +
            0.5 * verification_confidence +
            structured_bonus -
            failure_penalty
        )

        return max(0.0, min(1.0, overall))

    def _generate_limitations(self) -> List[str]:
        """Generate list of limitations encountered during search"""
        limitations = []

        if self.failed_apis:
            limitations.append(
                f"API failures: {', '.join(self.failed_apis)}"
            )

        for api, error in self.api_errors.items():
            limitations.append(f"{api}: {error}")

        if not self.search_sources['coingecko'] and not self.search_sources['tavily']:
            limitations.append("No cryptocurrency-specific APIs available")

        return limitations

    def _generate_next_steps(
        self,
        query_type: str,
        result_count: int,
        source_count: int,
        limitations: List[str]
    ) -> List[str]:
        """Generate actionable next steps based on search results"""
        next_steps = []

        # Low result count
        if result_count < 3:
            next_steps.append("Try broader search terms or synonyms")
            next_steps.append("Check spelling and query phrasing")

        # Limited sources
        if source_count < 2:
            next_steps.append("Configure additional API keys for better coverage")

        # Query type specific suggestions
        if query_type == 'crypto' and result_count > 0:
            next_steps.append("Check CoinMarketCap or CryptoCompare for additional data")

        if query_type == 'news' and result_count > 0:
            next_steps.append("Expand date range if recent results are limited")

        # API failures
        if limitations:
            next_steps.append("Retry query after fixing API connectivity issues")

        # General suggestions
        if result_count > 0:
            next_steps.append("Review source credibility and cross-reference claims")
            next_steps.append("Look for corroborating sources for single-source facts")

        return next_steps

    def format_as_markdown_table(
        self,
        results: List[SearchResult],
        columns: Optional[List[str]] = None
    ) -> str:
        """
        Format search results as a markdown table for easy comparison

        Args:
            results: Search results to format
            columns: Column names to include (default: title, source, verification, date)

        Returns:
            Markdown-formatted table string
        """
        if not results:
            return "No results to display"

        if len(results) < 3:
            # Don't use table for <3 results
            return self._format_as_list(results)

        # Default columns
        if not columns:
            columns = ['Title', 'Source', 'Verification', 'Date']

        # Build table header
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(['---' for _ in columns]) + " |"

        # Build table rows
        rows = []
        for result in results[:10]:  # Limit to 10 for readability
            row_data = []

            for col in columns:
                if col == 'Title':
                    # Truncate long titles
                    title = result.title[:50] + "..." if len(result.title) > 50 else result.title
                    row_data.append(title)
                elif col == 'Source':
                    row_data.append(result.source)
                elif col == 'Verification':
                    status = result.verification_status.title()
                    row_data.append(status)
                elif col == 'Date':
                    date = result.published_date or 'N/A'
                    if date and len(date) > 10:
                        date = date[:10]
                    row_data.append(date)
                elif col == 'Relevance':
                    row_data.append(f"{result.relevance_score:.2f}")
                else:
                    row_data.append('N/A')

            rows.append("| " + " | ".join(row_data) + " |")

        # Combine all parts
        table = [header, separator] + rows
        return "\n".join(table)

    def _format_as_list(self, results: List[SearchResult]) -> str:
        """Format results as a bulleted list (for <3 results)"""
        lines = []
        for i, result in enumerate(results, 1):
            lines.append(f"{i}. **{result.title}**")
            lines.append(f"   - Source: {result.source}")
            lines.append(f"   - Verification: {result.verification_status.title()}")
            if result.published_date:
                lines.append(f"   - Date: {result.published_date[:10]}")
            lines.append("")
        return "\n".join(lines)

    def _generate_summary(self, query: str, results: List[SearchResult]) -> str:
        """Generate a summary of search results"""
        if not results:
            return f"No results found for: {query}"

        # Build summary
        summary_parts = [
            f"Found {len(results)} results for '{query}':",
            ""
        ]

        # Structured data summary
        structured = [r for r in results if r.is_structured_data]
        if structured:
            summary_parts.append("Structured Data:")
            for r in structured[:3]:
                summary_parts.append(f"  • {r.title}")
                summary_parts.append(f"    {r.snippet[:200]}")
            summary_parts.append("")

        # Top results
        top_results = [r for r in results if not r.is_structured_data][:5]
        if top_results:
            summary_parts.append("Top Results:")
            for i, r in enumerate(top_results, 1):
                summary_parts.append(f"  {i}. {r.title}")
                summary_parts.append(f"     Source: {r.source}")
                summary_parts.append(f"     {r.snippet[:150]}...")

        return "\n".join(summary_parts)

    def _extract_crypto_identifier(self, query: str) -> str:
        """Extract cryptocurrency name/symbol from query"""
        # Common crypto symbols to check first (higher priority than word extraction)
        crypto_symbols = {
            'btc', 'bitcoin', 'xbt', 'eth', 'ethereum', 'ether', 'xrp', 'ripple',
            'sol', 'solana', 'ada', 'cardano', 'doge', 'dogecoin', 'dot', 'polkadot',
            'avax', 'avalanche', 'matic', 'polygon', 'link', 'chainlink', 'uni',
            'uniswap', 'ltc', 'litecoin', 'bch', 'bitcoin', 'cash', 'xlm', 'stellar',
            'algo', 'algorand', 'vet', 'vechain', 'ftm', 'fantom', 'near', 'amp',
            'comp', 'compound', 'mkr', 'maker', 'sushi', 'yfi', 'yearn', 'aave',
            'snx', 'synthetix', 'crv', 'curve', '1inch', 'ens', 'ethereum', 'name',
            'service', 'usdt', 'tether', 'usdc', 'usd', 'coin', 'busd', 'binance',
            'usd', 'dai', 'frax', 'ust', 'terrausd', 'luna', 'terra', 'atom',
            'cosmos', 'zec', 'zcash', 'dash', 'etc', 'ethereum', 'classic', 'zec'
        }

        query_lower = query.lower()

        # Check for crypto symbols first (most accurate)
        for symbol in sorted(crypto_symbols, key=len, reverse=True):  # Check longer symbols first
            if symbol in query_lower:
                return symbol

        # Remove action verbs and common words
        query_clean = re.sub(
            r'\b(research|search|find|get|look|up|check|what|is|the|current|latest|price|of|for|in|about|cryptocurrency|crypto|coin|token|news|market|value|worth|show|me|tell)\b',
            '',
            query_lower
        ).strip()

        # Remove extra whitespace and take first word
        words = query_clean.split()
        return words[0] if words else query

    def to_dict(self, report: SearchReport) -> Dict[str, Any]:
        """Convert SearchReport to dictionary"""
        return {
            'query': report.query,
            'query_type': report.query_type,
            'total_results': report.total_results,
            'results': [asdict(r) for r in report.results],
            'sources_used': report.sources_used,
            'search_duration': report.search_duration,
            'timestamp': report.timestamp,
            'confidence': report.confidence,
            'summary': report.summary
        }


# Factory function for easy integration
def create_search_master(config: Optional[Dict[str, Any]] = None) -> TORQSearchMaster:
    """Create a SearchMaster agent instance"""
    return TORQSearchMaster(config)


# Test function
async def test_search_master():
    """Test SearchMaster with various queries"""
    agent = create_search_master()

    test_queries = [
        ("CKB Nervos Network news", "crypto"),
        ("latest AI developments", "news"),
        ("Python async programming", "general")
    ]

    for query, expected_type in test_queries:
        print(f"\n{'='*80}")
        print(f"Testing: {query}")
        print(f"Expected type: {expected_type}")
        print('='*80)

        report = await agent.search(query, max_results=5)

        print(f"\nQuery Type: {report.query_type} (confidence: {report.confidence:.2f})")
        print(f"Duration: {report.search_duration:.2f}s")
        print(f"Results: {report.total_results}")
        print(f"Sources: {', '.join(report.sources_used)}")

        if report.results:
            print(f"\nTop Result:")
            top = report.results[0]
            print(f"  Title: {top.title}")
            print(f"  Source: {top.source}")
            print(f"  Snippet: {top.snippet[:200]}...")

        if report.summary:
            print(f"\nSummary:\n{report.summary}")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_search_master())
