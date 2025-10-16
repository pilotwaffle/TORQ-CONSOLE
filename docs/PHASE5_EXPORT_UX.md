# Phase 5: Export & UX - Specification

## Overview

Phase 5 adds export capabilities and real-time user experience improvements to TORQ Console's web research system.

## Goals

1. **Export Functionality**: Save research results in multiple formats
2. **Real-time Progress Feedback**: Show search and synthesis progress
3. **Status Updates**: Provide granular status during long-running operations

## Components

### 1. Export System

#### ExportManager
Central class for managing all export operations.

**Features:**
- Export to Markdown (.md)
- Export to PDF (.pdf)
- Export to CSV (.csv)
- Export to JSON (.json)
- Template-based formatting
- Metadata inclusion

**API:**
```python
export_manager = ExportManager()

# Export synthesis results
export_manager.export_to_markdown(results, "research_report.md")
export_manager.export_to_pdf(results, "research_report.pdf")
export_manager.export_to_csv(results, "research_data.csv")
export_manager.export_to_json(results, "research_data.json")
```

#### Export Formats

**Markdown:**
- Formatted summary with citations
- Table of contents
- Source list with confidence scores
- Key insights with bullet points
- Contradictions section
- Metadata footer

**PDF:**
- Professional layout
- Syntax highlighting for code
- Tables and images
- Headers and footers
- Page numbers
- Generated via markdown → PDF conversion

**CSV:**
- Tabular data of sources
- Confidence scores
- Metadata columns
- Easy import to Excel/Google Sheets

**JSON:**
- Complete data structure
- Machine-readable format
- All metadata preserved
- For programmatic access

### 2. Progress Tracking System

#### ProgressTracker
Real-time progress monitoring for long-running operations.

**Features:**
- Operation stages tracking
- Progress percentage
- Time estimation
- Status messages
- Event callbacks

**API:**
```python
tracker = ProgressTracker()

# Register callback for updates
tracker.on_progress(lambda status: print(f"{status.percent}%: {status.message}"))

# Use with search
results = await provider.search_with_synthesis(
    query="...",
    progress_tracker=tracker
)
```

**Progress Stages:**
1. Searching (0-20%)
2. Extracting content (20-50%)
3. Calculating confidence (50-70%)
4. Synthesizing documents (70-95%)
5. Finalizing results (95-100%)

#### StatusReporter
Provides granular status updates during research.

**Features:**
- Current operation description
- Time elapsed
- Items processed
- ETA (Estimated Time to Arrival)
- Detailed substeps

**API:**
```python
reporter = StatusReporter()

# Get current status
status = reporter.get_status()
print(f"Operation: {status.operation}")
print(f"Progress: {status.items_done}/{status.items_total}")
print(f"ETA: {status.eta_seconds}s")
```

### 3. Streaming Results

#### StreamingResultHandler
Stream results as they become available instead of waiting for completion.

**Features:**
- Incremental result delivery
- Async iteration
- Memory efficient
- Early cancellation support

**API:**
```python
handler = StreamingResultHandler()

async for partial_result in provider.research_topic_streaming(
    topic="...",
    handler=handler
):
    print(f"Got result: {partial_result['title']}")
    # Process incrementally
```

## Implementation Plan

### Phase 5.1: Export System (Day 1)
- [ ] Create `export` module directory
- [ ] Implement `ExportManager` class
- [ ] Add Markdown export with templates
- [ ] Add CSV export for tabular data
- [ ] Add JSON export for raw data
- [ ] Add PDF export (markdown → PDF)

### Phase 5.2: Progress Tracking (Day 1)
- [ ] Create `ProgressTracker` class
- [ ] Implement progress callbacks
- [ ] Add progress stages to search flow
- [ ] Create `StatusReporter` class
- [ ] Add detailed status updates

### Phase 5.3: Streaming Results (Day 2)
- [ ] Implement `StreamingResultHandler`
- [ ] Add `search_with_synthesis_streaming()`
- [ ] Add `research_topic_streaming()`
- [ ] Support async iteration

### Phase 5.4: Integration (Day 2)
- [ ] Integrate with WebSearchProvider
- [ ] Add export methods to provider
- [ ] Add progress tracking to all searches
- [ ] Update UI for progress display

### Phase 5.5: Testing & Documentation (Day 3)
- [ ] Write comprehensive tests
- [ ] Test all export formats
- [ ] Test progress tracking
- [ ] Create usage documentation
- [ ] Add examples

## Technical Requirements

### Dependencies
- `markdown` - Markdown parsing
- `reportlab` or `weasyprint` - PDF generation
- `aiofiles` - Async file operations
- Built-in `csv` and `json` modules

### File Structure
```
torq_console/llm/providers/export/
├── __init__.py
├── export_manager.py       # Main export class
├── markdown_exporter.py    # Markdown export
├── pdf_exporter.py         # PDF export
├── csv_exporter.py         # CSV export
├── json_exporter.py        # JSON export
└── templates/              # Export templates
    ├── markdown_template.md
    └── pdf_styles.css

torq_console/llm/providers/progress/
├── __init__.py
├── progress_tracker.py     # Progress tracking
├── status_reporter.py      # Status reporting
└── streaming_handler.py    # Streaming results
```

## Export Format Examples

### Markdown Export Example

```markdown
# Research Report: Machine Learning Trends 2025

**Generated:** 2025-01-14 12:34:56
**Query:** machine learning trends 2025
**Sources Analyzed:** 10
**Overall Confidence:** 0.85 (High)

## Summary

[Synthesized summary with citations]

## Key Insights

1. **Insight text here** (Confidence: 0.92)
   - Sources: [1], [2], [3]

2. **Another insight** (Confidence: 0.88)
   - Sources: [4], [5]

## Topics Covered

- Machine Learning
- Deep Learning
- Neural Networks
- AI Ethics

## Sources

[1] **Title of Source 1** (Confidence: 0.95 - High)
    URL: https://example.com/source1
    Author: Dr. Jane Smith
    Published: 2025-01-10
    Reliability: 0.98 | Quality: 0.92 | Freshness: 1.0

[2] **Title of Source 2** (Confidence: 0.88 - High)
    ...

## Contradictions Detected

- Source 3 and Source 7 have conflicting information about...

---

*Generated by TORQ Console Phase 5: Export & UX*
```

### CSV Export Example

```csv
Title,URL,Author,Published,Confidence,Level,Reliability,Quality,Freshness,Citation_Score
"Source 1","https://example.com/1","Dr. Smith","2025-01-10",0.95,high,0.98,0.92,1.0,0.80
"Source 2","https://example.com/2","J. Doe","2025-01-08",0.88,high,0.90,0.85,0.95,0.75
...
```

## Progress Update Flow

```
[0%] Starting search for 'machine learning trends 2025'
[5%] Searching with Google Custom Search API...
[15%] Found 10 results
[20%] Extracting content from URL 1/10...
[25%] Extracting content from URL 2/10...
...
[50%] Content extraction complete
[55%] Calculating confidence scores...
[70%] Confidence scoring complete
[75%] Synthesizing documents...
[85%] Identifying key insights...
[90%] Detecting contradictions...
[95%] Finalizing results...
[100%] Research complete!

Total time: 12.5 seconds
Sources analyzed: 10
High-confidence sources: 8
```

## Performance Targets

- **Export Speed**: < 1 second for Markdown/CSV/JSON, < 3 seconds for PDF
- **Progress Updates**: Every 5% or significant operation
- **Streaming Latency**: < 500ms per result
- **Memory Usage**: Streaming to keep memory constant

## Success Criteria

- [ ] All export formats working correctly
- [ ] Real-time progress updates functional
- [ ] Streaming results implemented
- [ ] All tests passing (target: 20+ tests)
- [ ] Documentation complete with examples
- [ ] Integration with existing Phase 4 functionality

## Future Enhancements (Phase 6+)

- Export to Word (.docx)
- Export to HTML with interactive features
- Custom export templates
- Batch export for multiple queries
- Export presets (academic, business, technical)
- Integration with cloud storage (Google Drive, Dropbox)

---

**Phase 5: Export & UX** - Ready for Implementation
