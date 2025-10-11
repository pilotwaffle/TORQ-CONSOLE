# TORQ SearchMaster Agent

## Overview

**SearchMaster** is a specialized search intelligence agent designed to handle comprehensive information retrieval across ANY topic. It acts as a dedicated search service that feeds high-quality, multi-source results to other agents like Prince Flowers.

## Architecture

```
User Query
    ↓
Prince Flowers (Orchestrator)
    ↓
SearchMaster Agent (Specialized Search)
    ↓
├─ CoinGecko API (Crypto Data)
├─ Tavily AI (AI-Powered Search)
├─ Perplexity AI (Synthesis)
├─ Brave Search (General Web)
├─ Google Custom Search (Fallback)
└─ Specialized APIs (News, Academic, etc.)
    ↓
Ranked, Deduplicated Results
    ↓
Prince Flowers (Synthesis & Response)
    ↓
User
```

## Key Features

### 1. Multi-API Support
- **Cryptocurrency**: CoinGecko, CoinMarketCap
- **AI Search**: Tavily, Perplexity
- **General Web**: Brave, Google Custom Search
- **News**: NewsAPI, domain-specific sources
- **Academic**: Semantic Scholar, arXiv (planned)

### 2. Intelligent Query Routing
- Automatic query type detection (crypto, news, general, academic, tech)
- Confidence scoring for query classification
- Optimal source selection based on query type

### 3. Result Quality
- Parallel multi-source fetching
- Deduplication by URL
- Relevance scoring and ranking
- Structured data prioritization

### 4. Comprehensive Output
- `SearchReport` dataclass with full metadata
- Individual `SearchResult` objects with:
  - Title, snippet, URL
  - Source attribution
  - Relevance scores
  - Structured data flags
  - Full content (when available)
  - Metadata (price data, citations, etc.)

## Usage

### Basic Search

```python
from torq_console.agents.torq_search_master import create_search_master

# Create agent
search_master = create_search_master()

# Perform search
report = await search_master.search(
    query="CKB Nervos Network news",
    max_results=10,
    include_summary=True
)

# Access results
print(f"Found {report.total_results} results")
print(f"Sources: {report.sources_used}")

for result in report.results:
    print(f"{result.title} - {result.source}")
    print(f"  {result.snippet[:200]}")
```

### Integration with Prince Flowers

```python
async def prince_search_with_searchmaster(self, query: str) -> Dict:
    """Use SearchMaster for comprehensive search, then synthesize"""

    # 1. Delegate search to SearchMaster
    search_master = create_search_master()
    search_report = await search_master.search(
        query=query,
        max_results=10,
        include_summary=True
    )

    # 2. Use search results for synthesis
    if not search_report.results:
        return await self._fallback_response(query)

    # 3. Synthesize response using SearchMaster's results
    synthesis_context = {
        'search_results': [asdict(r) for r in search_report.results],
        'sources_used': search_report.sources_used,
        'query_type': search_report.query_type,
        'summary': search_report.summary
    }

    response = await self._synthesize_with_llm(query, synthesis_context)

    return {
        'response': response,
        'sources': search_report.sources_used,
        'result_count': search_report.total_results,
        'duration': search_report.search_duration
    }
```

### Query Type Detection

SearchMaster automatically detects query types:

```python
# Crypto query
report = await search_master.search("Bitcoin price analysis")
# query_type='crypto', uses CoinGecko + Tavily

# News query
report = await search_master.search("latest AI developments")
# query_type='news', uses Tavily + Perplexity + Brave (news mode)

# General query
report = await search_master.search("Python async patterns")
# query_type='general', uses Tavily or best available

# Force specific type
report = await search_master.search(
    "machine learning",
    query_type='academic'
)
# Uses academic sources
```

## Configuration

### Environment Variables

```bash
# Cryptocurrency APIs
COINGECKO_API_KEY=your_key_here

# AI Search APIs
TAVILY_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here

# General Search APIs
BRAVE_SEARCH_API_KEY=your_key_here
GOOGLE_SEARCH_API_KEY=your_key_here
GOOGLE_SEARCH_ENGINE_ID=your_engine_id_here
```

### Optional Configuration

```python
config = {
    'timeout': 30,  # Request timeout
    'max_parallel_searches': 5,  # Max concurrent searches
    'enable_caching': True,  # Cache results
    'cache_ttl': 3600  # Cache time-to-live (seconds)
}

search_master = create_search_master(config)
```

## Search Report Structure

```python
@dataclass
class SearchReport:
    query: str                    # Original query
    query_type: str               # Detected type (crypto, news, etc.)
    total_results: int            # Number of results
    results: List[SearchResult]   # Ranked search results
    sources_used: List[str]       # APIs used
    search_duration: float        # Time taken (seconds)
    timestamp: str                # ISO timestamp
    confidence: float             # Query classification confidence
    summary: str                  # AI-generated summary

@dataclass
class SearchResult:
    title: str                    # Result title
    snippet: str                  # Short excerpt
    url: str                      # Source URL
    source: str                   # API source name
    relevance_score: float        # 0.0 - 1.0
    published_date: Optional[str] # Publication date
    full_content: Optional[str]   # Full article (if available)
    metadata: Optional[Dict]      # Additional data
    is_structured_data: bool      # Structured (e.g., CoinGecko data)
    is_ai_synthesis: bool         # AI-generated content
```

## Example: CKB Cryptocurrency Query

### Input
```python
report = await search_master.search("CKB Nervos Network news since July 2025")
```

### Output
```python
SearchReport(
    query="CKB Nervos Network news since July 2025",
    query_type="crypto",
    total_results=8,
    sources_used=["coingecko", "tavily", "perplexity"],
    search_duration=2.45,
    confidence=0.95,
    results=[
        SearchResult(
            title="CKB (Nervos Network) Market Data",
            snippet="Price: $0.007797 | 24h Change: +0.28% | Market Cap: $367,950,000 | Volume: $29,950,000",
            url="https://nervos.org",
            source="CoinGecko API",
            relevance_score=1.0,
            is_structured_data=True,
            metadata={
                'price_usd': 0.007797,
                'market_cap': 367950000,
                'categories': ['Layer 1', 'DeFi'],
                'description': "Nervos is a layered blockchain..."
            }
        ),
        SearchResult(
            title="RGB++ Layer 2 Ecosystem Surpasses 400 dApps",
            snippet="Nervos Network's RGB++ Layer 2 has grown to over 400 decentralized applications...",
            url="https://cointelegraph.com/...",
            source="Tavily AI",
            relevance_score=0.95
        ),
        SearchResult(
            title="CKCON 2025 Conference Announced for Q3",
            snippet="Nervos Foundation announces CKCON 2025, the annual developer conference...",
            url="https://nervos.org/news/ckcon2025",
            source="Tavily AI",
            relevance_score=0.92
        ),
        SearchResult(
            title="CKB v0.201.0 Release Notes",
            snippet="Major protocol upgrade brings performance improvements and new features...",
            url="https://github.com/nervosnetwork/ckb/releases",
            source="Tavily AI",
            relevance_score=0.90
        ),
        # ... more results
    ],
    summary="Found 8 results for CKB Nervos Network including:\n"
            "- Structured Data: Current price $0.007797, +0.28% 24h change\n"
            "- Ecosystem: RGB++ L2 with 400+ dApps, BBS Web5 app\n"
            "- Events: CKCON 2025 conference announced\n"
            "- Technical: CKB v0.201.0 released with improvements"
)
```

## Benefits Over Direct API Integration

### Before (Prince Flowers calling APIs directly)
```python
# Prince Flowers had to:
# 1. Manage API keys
# 2. Handle different API formats
# 3. Implement retry logic
# 4. Deduplicate results
# 5. Rank and filter
# 6. Error handling for each API
# => 200+ lines of search logic IN Prince Flowers
```

### After (Using SearchMaster)
```python
# Prince Flowers now:
search_report = await search_master.search(query)
response = await self.synthesize(query, search_report.results)
# => 2 lines, focus on synthesis not search infrastructure
```

## Performance

### Parallel Execution
- Multiple APIs queried simultaneously
- Total time = slowest API (not sum of all)
- Example: CoinGecko (0.5s) + Tavily (2.0s) + Perplexity (1.5s) = 2.0s total

### Caching (Planned)
- Cache results for 1 hour
- Reduce API calls by 80% for repeat queries
- Smart cache invalidation for time-sensitive queries

## Testing

### Run Test Suite

```bash
cd E:\TORQ-CONSOLE
python -m torq_console.agents.torq_search_master
```

### Test Output

```
================================================================================
Testing: CKB Nervos Network news
Expected type: crypto
================================================================================

Query Type: crypto (confidence: 0.95)
Duration: 2.45s
Results: 8
Sources: coingecko, tavily, perplexity

Top Result:
  Title: CKB (Nervos Network) Market Data
  Source: CoinGecko API
  Snippet: Price: $0.007797 | 24h Change: +0.28% | Market Cap: $367,950,000...

Summary:
Found 8 results for 'CKB Nervos Network news':

Structured Data:
  • CKB (Nervos Network) Market Data
    Price: $0.007797 | 24h Change: +0.28% | Market Cap: $367,950,000

Top Results:
  1. RGB++ Layer 2 Ecosystem Surpasses 400 dApps
     Source: Tavily AI
     Nervos Network's RGB++ Layer 2 has grown to over 400 decentralized...
  2. CKCON 2025 Conference Announced for Q3
     Source: Tavily AI
     Nervos Foundation announces CKCON 2025, the annual developer...
```

## Roadmap

### Phase 1: Core Functionality ✅
- [x] Multi-API support (CoinGecko, Tavily, Perplexity, Brave, Google)
- [x] Query type detection
- [x] Result deduplication and ranking
- [x] SearchReport structure

### Phase 2: Enhanced Integration (Current)
- [ ] Prince Flowers integration
- [ ] Result caching
- [ ] Rate limiting
- [ ] Usage analytics

### Phase 3: Advanced Features (Planned)
- [ ] Semantic Scholar integration
- [ ] arXiv paper search
- [ ] NewsAPI integration
- [ ] CoinMarketCap support
- [ ] Custom domain search
- [ ] Multi-language support

### Phase 4: Intelligence (Future)
- [ ] Learning from feedback
- [ ] Query expansion
- [ ] Result quality scoring
- [ ] Personalized ranking
- [ ] Trend detection

## API Costs

| API | Free Tier | Cost After | SearchMaster Usage |
|-----|-----------|------------|-------------------|
| **CoinGecko** | 30 calls/min | $129/mo | ~200/mo (within free) |
| **Tavily** | 1,000/mo | $0.008/req | ~500/mo (within free) |
| **Perplexity** | Paid only | $5/mo | Fallback only |
| **Brave** | 2,000/mo | $5/mo | ~200/mo (within free) |
| **Google** | 100/day | $5/1000 | Fallback only |

**Total estimated cost: ~$5/month** (same as current Perplexity-only)

## Troubleshooting

### No Results Returned

```python
# Check available sources
search_master = create_search_master()
print(search_master.search_sources)
# {'coingecko': True, 'tavily': False, 'perplexity': True, ...}

# Ensure at least one API key is configured
```

### Slow Performance

```python
# Limit concurrent searches
config = {'max_parallel_searches': 3}
search_master = create_search_master(config)

# Reduce max_results
report = await search_master.search(query, max_results=5)
```

### API Rate Limits

```python
# SearchMaster handles rate limits gracefully
# Failed APIs are skipped, others continue
# Check sources_used to see which APIs succeeded
```

## Contributing

To add a new search source:

1. Implement `async def _search_<source>(self, query: str) -> Dict[str, Any]`
2. Add API key to `__init__`
3. Add to `search_sources` dict
4. Update `_build_search_tasks()` routing logic
5. Add tests

Example:
```python
async def _search_newsapi(self, query: str) -> Dict[str, Any]:
    """Search using NewsAPI"""
    # Implementation here
    return {'results': [...], 'source': 'newsapi'}
```

## License

Part of TORQ Console v0.70.0+
