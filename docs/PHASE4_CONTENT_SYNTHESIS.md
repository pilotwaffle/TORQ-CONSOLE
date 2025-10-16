# Phase 4: Enhanced Content Synthesis & Export

**Status:** 🚧 **IN PROGRESS**

**Version:** 1.0.0

**Start Date:** October 14, 2025

---

## Overview

Phase 4 implements advanced content processing capabilities for TORQ Console's web research system, enabling intelligent content extraction, multi-document synthesis, citation tracking, and flexible export options.

### Goals

1. **Enhanced Content Extraction** - Extract clean, structured content from web pages
2. **Multi-Document Synthesis** - Combine insights from multiple sources intelligently
3. **Citation Graphs** - Track and visualize source relationships
4. **Export Functionality** - Export research to Markdown, PDF, CSV formats

---

## Architecture

```
WebSearchProvider
  ↓
Search Results (Phases 1-3)
  ↓
Phase 4: Content Synthesis
  ├── ContentExtractor (Extract clean content from URLs)
  ├── DocumentSynthesizer (Combine multiple documents)
  ├── CitationGraph (Track source relationships)
  └── Exporters (Markdown, PDF, CSV)
  ↓
Synthesized Research Output
```

---

## Components

### 1. ContentExtractor

**Purpose:** Extract clean, readable content from web pages

**Features:**
- HTML parsing and cleaning
- Main content extraction (remove ads, navigation, etc.)
- Metadata extraction (title, author, date, keywords)
- Image and media detection
- Code block preservation
- Table extraction
- Link extraction and validation

**API:**
```python
from torq_console.llm.providers.content_synthesis import ContentExtractor

extractor = ContentExtractor()

# Extract from URL
content = await extractor.extract_from_url("https://example.com/article")

# Extract from HTML
content = extractor.extract_from_html(html_string, base_url="https://example.com")

# Result structure
{
    'title': 'Article Title',
    'author': 'John Doe',
    'date_published': '2025-10-14',
    'content': 'Clean article text...',
    'metadata': {...},
    'links': [...],
    'images': [...],
    'code_blocks': [...],
    'tables': [...]
}
```

### 2. DocumentSynthesizer

**Purpose:** Combine insights from multiple documents into coherent summaries

**Features:**
- Multi-document summarization
- Topic extraction and clustering
- Key insights identification
- Duplicate content removal
- Contradictions detection
- Consensus building
- Source attribution

**API:**
```python
from torq_console.llm.providers.content_synthesis import DocumentSynthesizer

synthesizer = DocumentSynthesizer()

# Synthesize multiple documents
documents = [doc1, doc2, doc3]  # From ContentExtractor
synthesis = await synthesizer.synthesize(
    documents,
    query="What are the latest AI developments?",
    max_length=500
)

# Result structure
{
    'summary': 'Synthesized overview...',
    'key_insights': ['Insight 1', 'Insight 2', ...],
    'topics': ['AI', 'Machine Learning', ...],
    'sources_used': [{'title': '...', 'url': '...', 'relevance': 0.95}, ...],
    'contradictions': [...],
    'consensus_points': [...]
}
```

### 3. CitationGraph

**Purpose:** Track and visualize relationships between sources

**Features:**
- Source dependency tracking
- Citation relationship mapping
- Authority scoring
- Source clustering
- Visual graph generation
- Export to graph formats (DOT, JSON)

**API:**
```python
from torq_console.llm.providers.content_synthesis import CitationGraph

graph = CitationGraph()

# Add sources
graph.add_source("https://paper1.com", metadata={...})
graph.add_source("https://paper2.com", metadata={...})

# Add citations
graph.add_citation("https://paper2.com", "https://paper1.com")

# Analyze
authority_scores = graph.calculate_authority_scores()
clusters = graph.find_clusters()

# Export
graph.export_dot("citations.dot")
graph.export_json("citations.json")
```

### 4. Export System

**Purpose:** Export research results to various formats

**Exporters:**
- **MarkdownExporter** - Export to Markdown with citations
- **PDFExporter** - Generate PDF reports
- **CSVExporter** - Export data tables
- **HTMLExporter** - Generate HTML reports
- **JSONExporter** - Export structured data

**API:**
```python
from torq_console.llm.providers.content_synthesis import (
    MarkdownExporter, PDFExporter, CSVExporter
)

# Export to Markdown
md_exporter = MarkdownExporter()
md_exporter.export(synthesis_result, "research_report.md")

# Export to PDF
pdf_exporter = PDFExporter()
pdf_exporter.export(synthesis_result, "research_report.pdf")

# Export to CSV (for data extraction)
csv_exporter = CSVExporter()
csv_exporter.export(search_results, "results.csv")
```

---

## Integration with WebSearchProvider

```python
from torq_console.llm.providers.websearch import WebSearchProvider

provider = WebSearchProvider()

# Search with content extraction
results = await provider.search_with_synthesis(
    query="quantum computing advances",
    max_results=10,
    extract_content=True,  # Extract full content
    synthesize=True,       # Generate synthesis
    export_format="markdown"  # Export to markdown
)

# Results include:
{
    'search_results': [...],  # Original search results
    'extracted_content': [...],  # Full content from URLs
    'synthesis': {...},  # Multi-document synthesis
    'citation_graph': {...},  # Source relationships
    'exported_file': 'research_report.md'
}
```

---

## Use Cases

### Research Paper Review
```python
# Search for papers on a topic
results = await provider.search("neural network optimization",
                               search_type="academic",
                               max_results=20)

# Extract full content
extractor = ContentExtractor()
papers = []
for result in results['results']:
    content = await extractor.extract_from_url(result['url'])
    papers.append(content)

# Synthesize findings
synthesizer = DocumentSynthesizer()
synthesis = await synthesizer.synthesize(
    papers,
    query="What are the latest optimization techniques?",
    focus_areas=['methods', 'results', 'conclusions']
)

# Export as PDF report
pdf_exporter = PDFExporter()
pdf_exporter.export(synthesis, "neural_network_optimization_review.pdf")
```

### Competitive Analysis
```python
# Search for competitor information
competitors = ["Company A", "Company B", "Company C"]
all_results = []

for competitor in competitors:
    results = await provider.search(f"{competitor} product features")
    all_results.extend(results['results'])

# Extract and synthesize
extractor = ContentExtractor()
docs = [await extractor.extract_from_url(r['url']) for r in all_results]

synthesizer = DocumentSynthesizer()
analysis = await synthesizer.synthesize(
    docs,
    query="Compare product features across competitors",
    comparison_mode=True
)

# Export as structured CSV
csv_exporter = CSVExporter()
csv_exporter.export(analysis, "competitive_analysis.csv")
```

### News Aggregation
```python
# Aggregate news on a topic
news_results = await provider.search("AI regulation 2025",
                                    search_type="news",
                                    max_results=30)

# Track citations and sources
graph = CitationGraph()
for result in news_results['results']:
    graph.add_source(result['url'], metadata=result)

# Generate synthesis with source tracking
synthesizer = DocumentSynthesizer()
synthesis = await synthesizer.synthesize_with_citations(
    news_results['results'],
    citation_graph=graph
)

# Export markdown with inline citations
md_exporter = MarkdownExporter(include_citations=True)
md_exporter.export(synthesis, "ai_regulation_summary.md")
```

---

## Implementation Plan

### Phase 4.1: Content Extraction (Week 1)
- [x] Design ContentExtractor architecture
- [ ] Implement HTML parsing and cleaning
- [ ] Implement metadata extraction
- [ ] Add content structure detection
- [ ] Create extraction tests

### Phase 4.2: Document Synthesis (Week 2)
- [ ] Design DocumentSynthesizer architecture
- [ ] Implement multi-document summarization
- [ ] Add topic extraction
- [ ] Implement deduplication
- [ ] Create synthesis tests

### Phase 4.3: Citation Tracking (Week 3)
- [ ] Design CitationGraph architecture
- [ ] Implement graph data structures
- [ ] Add authority scoring algorithms
- [ ] Implement clustering
- [ ] Create visualization

### Phase 4.4: Export System (Week 4)
- [ ] Implement MarkdownExporter
- [ ] Implement PDFExporter
- [ ] Implement CSVExporter
- [ ] Add export templates
- [ ] Create export tests

### Phase 4.5: Integration & Testing (Week 5)
- [ ] Integrate with WebSearchProvider
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Documentation
- [ ] Production deployment

---

## Technical Requirements

### Dependencies
```python
# Content extraction
beautifulsoup4>=4.12.0
lxml>=4.9.0
readability-lxml>=0.8.1
newspaper3k>=0.2.8

# Synthesis
transformers>=4.30.0  # For summarization
sentence-transformers>=2.2.0  # For similarity
spacy>=3.5.0  # For NLP

# Export
markdown>=3.4.0
reportlab>=4.0.0  # For PDF
pdfkit>=1.0.0  # Alternative PDF
jinja2>=3.1.0  # For templates

# Graph
networkx>=3.1.0
pygraphviz>=1.11  # For visualization
```

### Performance Targets
- Content extraction: <5s per page
- Synthesis: <10s for 10 documents
- Export: <3s per format
- Memory: <500MB for typical research session

---

## Security Considerations

### Content Extraction
- Sanitize all extracted HTML
- Validate URLs before fetching
- Implement timeout limits
- Rate limiting on external requests
- Sandbox untrusted content

### Data Privacy
- Don't store personal information
- Respect robots.txt
- Honor GDPR requirements
- Provide data export/deletion

### Export Security
- Sanitize file names
- Validate export paths
- Prevent path traversal
- Limit file sizes

---

## Next Steps

After Phase 4 completion:
- **Phase 5:** Real-time collaboration and sharing
- **Phase 6:** Machine learning-enhanced synthesis
- **Phase 7:** Multi-language support
- **Phase 8:** Advanced visualization

---

## Credits

**Implementation:** TORQ Console Development Team

**Phase:** 4 of 8 (Web Research Enhancement)

**Status:** 🚧 In Progress

---

*TORQ Console - Intelligent Research Synthesis*
