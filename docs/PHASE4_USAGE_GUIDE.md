# Phase 4: Content Synthesis - Usage Guide

## Overview

Phase 4 adds advanced content processing capabilities to TORQ Console's web search system:

- **ContentExtractor**: Extracts structured content (tables, lists, images) from HTML
- **ConfidenceScorer**: Calculates reliability scores for search results
- **MultiDocumentSynthesizer**: Synthesizes multiple documents with citations

## Quick Start

### Basic Enhanced Search

```python
from torq_console.llm.providers.websearch import WebSearchProvider

# Initialize provider
provider = WebSearchProvider()

# Perform search with synthesis
results = await provider.search_with_synthesis(
    query="machine learning trends 2025",
    max_results=10,
    extract_content=True,
    synthesize=True
)

# Access synthesized content
print(results['synthesis']['summary'])
print(f"Confidence: {results['synthesis']['overall_confidence']:.2f}")
print(f"Sources analyzed: {len(results['extracted_documents'])}")
```

### Comprehensive Research

```python
# Deep research on a topic
research = await provider.research_topic(
    topic="quantum computing advances",
    depth="deep",  # Options: "quick", "standard", "deep"
    focus_areas=["quantum algorithms", "error correction"]
)

# Access research results
for insight in research['synthesis']['key_insights']:
    print(f"- {insight['text']}")
    print(f"  Sources: {', '.join(insight['sources'])}")
    print(f"  Confidence: {insight['confidence']:.2f}")
```

## Component Details

### ContentExtractor

Extracts structured content from web pages.

```python
from torq_console.llm.providers.content_synthesis import ContentExtractor

extractor = ContentExtractor()

# Extract from HTML string
content = extractor.extract_from_html(html_string, url)

# Extract from URL
content = await extractor.extract_from_url("https://example.com/article")

# Access extracted data
print(f"Title: {content.title}")
print(f"Author: {content.author}")
print(f"Word count: {content.word_count}")

# Structured content
for table in content.tables:
    print(f"Table: {table.caption}")
    print(f"Headers: {table.headers}")
    print(f"Rows: {len(table.rows)}")

for lst in content.lists:
    print(f"{lst.list_type} list with {len(lst.items)} items")

for img in content.images:
    print(f"Image: {img.url}")
    print(f"Alt text: {img.alt_text}")
    print(f"Caption: {img.caption}")
```

### ConfidenceScorer

Calculates reliability scores based on multiple factors.

```python
from torq_console.llm.providers.content_synthesis import ConfidenceScorer

scorer = ConfidenceScorer()

# Score a single result
score = scorer.score_result(
    url="https://arxiv.org/paper/12345",
    title="Research Paper on ML",
    content="Paper content...",
    date_published="2025-01-10T00:00:00Z",
    author="Dr. Jane Smith",
    citations=50
)

print(f"Overall Score: {score.overall_score:.2f}")
print(f"Confidence Level: {score.level}")  # high, medium, or low
print(f"Source Reliability: {score.source_reliability:.2f}")
print(f"Content Quality: {score.content_quality:.2f}")
print(f"Freshness: {score.freshness:.2f}")

# Score multiple results with cross-source consistency
results = [...]  # List of result dictionaries
scores = scorer.score_multiple_results(results)

# Aggregate scores
aggregate = scorer.aggregate_scores(scores)
print(f"Average confidence: {aggregate.overall_score:.2f}")
```

#### Confidence Scoring Factors

1. **Source Reliability (30%)**
   - Trusted domains (arxiv.org, nature.com, etc.): 0.90-0.98
   - Educational (.edu): 0.85
   - Government (.gov): 0.90
   - Unknown domains: 0.50

2. **Content Quality (25%)**
   - Title quality (length, completeness)
   - Content length and structure
   - Metadata completeness

3. **Freshness (15%)**
   - < 1 week: 1.0
   - < 1 month: 0.90
   - < 3 months: 0.75
   - < 1 year: 0.60
   - Older: declining score

4. **Citation Score (15%)**
   - 100+ citations: 1.0
   - 50+ citations: 0.90
   - 20+ citations: 0.80
   - No citations: 0.40

5. **Consistency (15%)**
   - Calculated across multiple sources
   - Higher when sources agree

### MultiDocumentSynthesizer

Synthesizes content from multiple documents with citations.

```python
from torq_console.llm.providers.content_synthesis import MultiDocumentSynthesizer

synthesizer = MultiDocumentSynthesizer()

# Prepare documents
documents = [
    {
        'url': 'https://example.com/doc1',
        'title': 'Document 1',
        'content': 'Content of document 1...',
        'keywords': ['keyword1', 'keyword2']
    },
    # ... more documents
]

# Synthesize
result = await synthesizer.synthesize(
    documents=documents,
    query="machine learning",
    max_length=500,
    focus_areas=['algorithms', 'applications']
)

# Access synthesis results
print(result.summary)
print(f"Key insights: {len(result.key_insights)}")
print(f"Topics covered: {', '.join(result.topics)}")
print(f"Overall confidence: {result.overall_confidence:.2f}")
print(f"Source diversity: {result.source_diversity:.2f}")
print(f"Consensus level: {result.consensus_level:.2f}")

# Contradictions detected
for contradiction in result.contradictions:
    print(f"Potential contradiction: {contradiction['text']}")

# Consensus points
for consensus in result.consensus_points:
    print(f"Consensus: {consensus.text}")
    print(f"  Supported by: {len(consensus.sources)} sources")
```

## Integration with WebSearchProvider

Phase 4 is fully integrated into the WebSearchProvider:

```python
provider = WebSearchProvider()

# Check if synthesis is available
if provider.synthesis_enabled:
    print("✓ Content synthesis enabled")
    print("✓ ContentExtractor available")
    print("✓ MultiDocumentSynthesizer available")
    print("✓ ConfidenceScorer available")
```

### Search Flow with Phase 4

1. **Basic Search** → Find relevant URLs
2. **Content Extraction** → Extract structured content from URLs
3. **Confidence Scoring** → Calculate reliability scores
4. **Multi-Document Synthesis** → Synthesize insights with citations

## Advanced Usage

### Custom Synthesis Parameters

```python
# Fine-tune synthesis
result = await synthesizer.synthesize(
    documents=docs,
    query="specific topic",
    max_length=800,  # Longer summary
    focus_areas=['methodology', 'results', 'implications']
)
```

### Filtering by Confidence

```python
# Get high-confidence results only
results = await provider.search_with_synthesis(query="...", max_results=20)

high_confidence = [
    doc for doc, score in zip(
        results['extracted_documents'],
        results['confidence_scores']
    )
    if score['level'] == 'high'
]

print(f"High-confidence sources: {len(high_confidence)}")
```

### Citation Tracking

```python
# Track citations for each insight
for insight in result.key_insights:
    print(f"\nInsight: {insight.text}")
    print(f"Confidence: {insight.confidence:.2f}")
    print("Cited sources:")
    for source_url in insight.sources:
        print(f"  - {source_url}")
```

## Testing

Run Phase 4 tests:

```bash
cd E:\TORQ-CONSOLE
python -m pytest tests/test_phase4_content_synthesis.py -v
```

All 24 tests should pass:
- 6 ContentExtractor tests
- 7 ConfidenceScorer tests
- 6 MultiDocumentSynthesizer tests
- 3 WebSearchProvider integration tests
- 2 Integration scenario tests

## Performance Considerations

### Content Extraction
- BeautifulSoup-based extraction (primary)
- Regex fallback for parsing failures
- Async-aware for multiple URLs

### Synthesis Speed
- Extractive approach (fast)
- No LLM required for synthesis
- Scales to 10-20 documents efficiently

### Memory Usage
- Caches extracted content
- Limits summary length
- Streams large documents

## Best Practices

1. **Use appropriate depth for research**
   - `quick`: 5 results, 300 words (2-3 seconds)
   - `standard`: 10 results, 500 words (5-7 seconds)
   - `deep`: 20 results, 800 words (10-15 seconds)

2. **Check confidence scores**
   - Filter out low-confidence results
   - Prefer `high` level sources
   - Review warnings in confidence scores

3. **Handle synthesis results**
   - Always check `synthesis_available` flag
   - Gracefully degrade to basic search if unavailable
   - Log synthesis metadata for debugging

4. **Optimize for your use case**
   - Set appropriate `max_length` for summaries
   - Use `focus_areas` for targeted research
   - Disable `extract_content` for quick searches

## Error Handling

```python
try:
    results = await provider.search_with_synthesis(
        query="...",
        extract_content=True,
        synthesize=True
    )

    if 'synthesis' in results:
        # Synthesis successful
        summary = results['synthesis']['summary']
    else:
        # Fall back to basic results
        basic_results = results['results']

except Exception as e:
    logger.error(f"Search failed: {e}")
    # Handle error
```

## Configuration

Phase 4 respects existing WebSearchProvider configuration:

```python
config = {
    'max_results': 15,
    'timeout': 45,
    # ... other search config
}

provider = WebSearchProvider(config)
```

## Dependencies

Phase 4 requires:
- `beautifulsoup4` (HTML parsing)
- `python-dateutil` (date parsing)
- `aiohttp` (async HTTP)

Install with:
```bash
pip install beautifulsoup4 python-dateutil aiohttp
```

## Next Steps: Phase 5

Phase 5 will add:
- Export to Markdown/PDF/CSV
- Real-time progress feedback
- Status updates during research
- Streaming synthesis results

## Support

For issues or questions:
- Check test files for examples
- Review source code documentation
- File an issue on GitHub

---

**Phase 4: Content Synthesis - Complete** ✅

All 24 tests passing | Full WebSearchProvider integration | Production-ready
