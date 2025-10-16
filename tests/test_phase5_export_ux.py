"""
Extensive Tests for Phase 5: Export & UX

Tests all components of Phase 5:
- Export Manager (Markdown, CSV, JSON, PDF)
- Progress Tracker
- Integration with WebSearchProvider
"""

import pytest
import asyncio
import os
import json
import csv
from pathlib import Path
from datetime import datetime

from torq_console.llm.providers.export import (
    ExportManager, MarkdownExporter, CSVExporter, JSONExporter, PDFExporter
)
from torq_console.llm.providers.progress import ProgressTracker, ProgressStatus


# Sample test data
SAMPLE_RESULTS = {
    'query': 'machine learning trends',
    'timestamp': '2025-01-14T12:00:00',
    'method_used': 'google_custom_search',
    'synthesis_enabled': True,
    'results': [
        {
            'title': 'ML Trends 2025',
            'url': 'https://example.com/ml-trends',
            'snippet': 'Machine learning is evolving rapidly...',
            'source': 'example'
        }
    ],
    'extracted_documents': [
        {
            'url': 'https://example.com/doc1',
            'title': 'Machine Learning in 2025',
            'content': 'Deep learning and neural networks are transforming industries.',
            'author': 'Dr. Jane Smith',
            'date_published': '2025-01-10T00:00:00Z',
            'keywords': ['machine learning', 'AI'],
            'word_count': 500
        },
        {
            'url': 'https://example.com/doc2',
            'title': 'AI Research Advances',
            'content': 'Recent advances in reinforcement learning show promise.',
            'author': 'Prof. John Doe',
            'date_published': '2025-01-08T00:00:00Z',
            'keywords': ['AI', 'research'],
            'word_count': 450
        }
    ],
    'confidence_scores': [
        {
            'url': 'https://example.com/doc1',
            'overall_score': 0.85,
            'level': 'high',
            'source_reliability': 0.90,
            'content_quality': 0.88,
            'freshness': 0.95,
            'warnings': []
        },
        {
            'url': 'https://example.com/doc2',
            'overall_score': 0.82,
            'level': 'high',
            'source_reliability': 0.88,
            'content_quality': 0.85,
            'freshness': 0.93,
            'warnings': []
        }
    ],
    'synthesis': {
        'summary': 'Machine learning continues to advance with deep learning and reinforcement learning leading the way.',
        'key_insights': [
            {
                'text': 'Deep learning is transforming industries',
                'sources': ['https://example.com/doc1'],
                'confidence': 0.90
            },
            {
                'text': 'Reinforcement learning shows promise',
                'sources': ['https://example.com/doc2'],
                'confidence': 0.85
            }
        ],
        'topics': ['machine learning', 'deep learning', 'AI', 'reinforcement learning'],
        'overall_confidence': 0.85,
        'source_diversity': 0.80,
        'consensus_level': 0.75,
        'contradictions': [],
        'word_count': 95,
        'sources_used': [
            {'url': 'https://example.com/doc1', 'title': 'Machine Learning in 2025'},
            {'url': 'https://example.com/doc2', 'title': 'AI Research Advances'}
        ]
    }
}


class TestMarkdownExporter:
    """Test Markdown export functionality."""

    def setup_method(self):
        """Initialize exporter for each test."""
        self.exporter = MarkdownExporter()
        self.test_dir = Path("E:/TORQ-CONSOLE/tests/temp_exports")
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test files."""
        if self.test_dir.exists():
            for file in self.test_dir.glob("*.md"):
                file.unlink()

    def test_export_basic(self):
        """Test basic markdown export."""
        output_path = self.test_dir / "test_basic.md"
        success = self.exporter.export(SAMPLE_RESULTS, str(output_path))

        assert success is True
        assert output_path.exists()

        # Read and verify content
        content = output_path.read_text(encoding='utf-8')
        assert "# Research Report" in content
        assert "machine learning trends" in content
        assert "Summary" in content

    def test_export_with_metadata(self):
        """Test export with metadata section."""
        output_path = self.test_dir / "test_metadata.md"
        success = self.exporter.export(
            SAMPLE_RESULTS,
            str(output_path),
            include_metadata=True
        )

        assert success is True
        content = output_path.read_text(encoding='utf-8')
        assert "**Generated:**" in content
        assert "**Query:**" in content
        assert "**Sources Analyzed:**" in content

    def test_export_with_insights(self):
        """Test export with key insights."""
        output_path = self.test_dir / "test_insights.md"
        success = self.exporter.export(
            SAMPLE_RESULTS,
            str(output_path),
            include_insights=True
        )

        assert success is True
        content = output_path.read_text(encoding='utf-8')
        assert "## Key Insights" in content
        assert "Deep learning is transforming industries" in content

    def test_export_with_sources(self):
        """Test export with source list."""
        output_path = self.test_dir / "test_sources.md"
        success = self.exporter.export(
            SAMPLE_RESULTS,
            str(output_path),
            include_sources=True
        )

        assert success is True
        content = output_path.read_text(encoding='utf-8')
        assert "## Sources" in content
        assert "[1]" in content
        assert "https://example.com/doc1" in content

    def test_export_to_string(self):
        """Test export to string without file."""
        markdown_text = self.exporter.export_to_string(SAMPLE_RESULTS)

        assert markdown_text
        assert "# Research Report" in markdown_text
        assert "Summary" in markdown_text


class TestCSVExporter:
    """Test CSV export functionality."""

    def setup_method(self):
        """Initialize exporter for each test."""
        self.exporter = CSVExporter()
        self.test_dir = Path("E:/TORQ-CONSOLE/tests/temp_exports")
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test files."""
        if self.test_dir.exists():
            for file in self.test_dir.glob("*.csv"):
                file.unlink()

    def test_export_sources(self):
        """Test export of sources to CSV."""
        output_path = self.test_dir / "test_sources.csv"
        success = self.exporter.export(
            SAMPLE_RESULTS,
            str(output_path),
            mode='sources'
        )

        assert success is True
        assert output_path.exists()

        # Read and verify CSV
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert 'Title' in rows[0]
        assert 'URL' in rows[0]
        assert 'Confidence_Overall' in rows[0]

    def test_export_insights(self):
        """Test export of insights to CSV."""
        output_path = self.test_dir / "test_insights.csv"
        success = self.exporter.export(
            SAMPLE_RESULTS,
            str(output_path),
            mode='insights'
        )

        assert success is True
        assert output_path.exists()

        # Read and verify CSV
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert 'Insight' in rows[0]
        assert 'Confidence' in rows[0]
        assert 'Source_Count' in rows[0]

    def test_export_both(self):
        """Test exporting both sources and insights."""
        base_path = str(self.test_dir / "test_both")
        sources_ok, insights_ok = self.exporter.export_both(SAMPLE_RESULTS, base_path)

        assert sources_ok is True
        assert insights_ok is True
        assert Path(f"{base_path}_sources.csv").exists()
        assert Path(f"{base_path}_insights.csv").exists()


class TestJSONExporter:
    """Test JSON export functionality."""

    def setup_method(self):
        """Initialize exporter for each test."""
        self.exporter = JSONExporter()
        self.test_dir = Path("E:/TORQ-CONSOLE/tests/temp_exports")
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test files."""
        if self.test_dir.exists():
            for file in self.test_dir.glob("*.json"):
                file.unlink()

    def test_export_pretty(self):
        """Test pretty-printed JSON export."""
        output_path = self.test_dir / "test_pretty.json"
        success = self.exporter.export(
            SAMPLE_RESULTS,
            str(output_path),
            pretty=True
        )

        assert success is True
        assert output_path.exists()

        # Read and verify JSON
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert 'research_metadata' in data
        assert 'synthesis' in data
        assert data['research_metadata']['query'] == 'machine learning trends'

    def test_export_compact(self):
        """Test compact JSON export."""
        output_path = self.test_dir / "test_compact.json"
        success = self.exporter.export(
            SAMPLE_RESULTS,
            str(output_path),
            pretty=False
        )

        assert success is True
        content = output_path.read_text(encoding='utf-8')

        # Compact format should have minimal whitespace
        assert '\n  ' not in content  # No indentation

    def test_export_with_metadata(self):
        """Test export includes metadata."""
        output_path = self.test_dir / "test_metadata.json"
        success = self.exporter.export(
            SAMPLE_RESULTS,
            str(output_path),
            include_metadata=True
        )

        assert success is True

        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert 'export_metadata' in data
        assert 'exported_at' in data['export_metadata']
        assert 'exporter' in data['export_metadata']

    def test_export_to_string(self):
        """Test export to JSON string."""
        json_text = self.exporter.export_to_string(SAMPLE_RESULTS)

        assert json_text
        data = json.loads(json_text)
        assert 'research_metadata' in data
        assert 'synthesis' in data


class TestPDFExporter:
    """Test PDF export functionality."""

    def setup_method(self):
        """Initialize exporter for each test."""
        self.exporter = PDFExporter()
        self.test_dir = Path("E:/TORQ-CONSOLE/tests/temp_exports")
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test files."""
        if self.test_dir.exists():
            for file in self.test_dir.glob("*.pdf"):
                file.unlink()
            for file in self.test_dir.glob("*.txt"):
                file.unlink()

    def test_pdf_availability(self):
        """Test PDF export availability check."""
        is_available = self.exporter.is_available()
        assert isinstance(is_available, bool)

    def test_export_placeholder_if_unavailable(self):
        """Test that placeholder is created if PDF libs unavailable."""
        output_path = self.test_dir / "test_placeholder.pdf"

        # This will create a .txt file if PDF libs not available
        success = self.exporter.export(SAMPLE_RESULTS, str(output_path))

        # Either PDF was created or placeholder .txt was created
        assert output_path.exists() or Path(str(output_path).replace('.pdf', '.txt')).exists()


class TestExportManager:
    """Test unified export manager."""

    def setup_method(self):
        """Initialize manager for each test."""
        self.manager = ExportManager()
        self.test_dir = Path("E:/TORQ-CONSOLE/tests/temp_exports")
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test files."""
        if self.test_dir.exists():
            for file in self.test_dir.glob("*"):
                if file.is_file():
                    file.unlink()

    def test_auto_format_detection(self):
        """Test automatic format detection from extension."""
        # Markdown
        md_path = self.test_dir / "test.md"
        success = self.manager.export(SAMPLE_RESULTS, str(md_path))
        assert success is True
        assert md_path.exists()

        # JSON
        json_path = self.test_dir / "test.json"
        success = self.manager.export(SAMPLE_RESULTS, str(json_path))
        assert success is True
        assert json_path.exists()

        # CSV
        csv_path = self.test_dir / "test.csv"
        success = self.manager.export(SAMPLE_RESULTS, str(csv_path))
        assert success is True
        assert csv_path.exists()

    def test_explicit_format(self):
        """Test explicit format specification."""
        output_path = self.test_dir / "test_explicit.txt"
        success = self.manager.export(
            SAMPLE_RESULTS,
            str(output_path),
            format='markdown'
        )

        assert success is True
        assert output_path.exists()

    def test_export_all_formats(self):
        """Test exporting to all formats at once."""
        base_path = str(self.test_dir / "test_all")
        results = self.manager.export_all(
            SAMPLE_RESULTS,
            base_path,
            formats=['markdown', 'json', 'csv']
        )

        assert results['markdown'] is True
        assert results['json'] is True
        assert results['csv_sources'] is True

        # Verify files exist
        assert Path(f"{base_path}.md").exists()
        assert Path(f"{base_path}.json").exists()
        assert Path(f"{base_path}_sources.csv").exists()

    def test_get_supported_formats(self):
        """Test getting supported format information."""
        formats = self.manager.get_supported_formats()

        assert 'markdown' in formats
        assert 'csv' in formats
        assert 'json' in formats
        assert 'pdf' in formats

        # Check format details
        assert formats['markdown']['available'] is True
        assert 'extension' in formats['markdown']
        assert 'features' in formats['markdown']

    def test_export_to_string(self):
        """Test string export through manager."""
        # Markdown
        md_text = self.manager.export_to_string(SAMPLE_RESULTS, format='markdown')
        assert md_text
        assert "# Research Report" in md_text

        # JSON
        json_text = self.manager.export_to_string(SAMPLE_RESULTS, format='json')
        assert json_text
        data = json.loads(json_text)
        assert 'research_metadata' in data


class TestProgressTracker:
    """Test progress tracking functionality."""

    def test_basic_progress(self):
        """Test basic progress tracking."""
        tracker = ProgressTracker("Test Operation")
        tracker.start()

        # Update to searching stage
        tracker.update_stage(
            tracker.STAGE_SEARCHING,
            "Searching for results...",
            items_total=10
        )

        status = tracker.get_status()
        assert status.operation == "Test Operation"
        assert status.stage == tracker.STAGE_SEARCHING
        assert 0 <= status.percent <= 100

    def test_progress_callback(self):
        """Test progress callbacks."""
        tracker = ProgressTracker("Test Operation")

        # Track callback invocations
        callback_called = []

        def on_progress(status: ProgressStatus):
            callback_called.append(status.percent)

        tracker.on_progress(on_progress)
        tracker.start()
        tracker.update_stage(tracker.STAGE_SEARCHING, "Searching...")
        tracker.update_progress(message="Found 5 results")

        assert len(callback_called) >= 2  # At least 2 updates

    def test_stage_progression(self):
        """Test progression through multiple stages."""
        tracker = ProgressTracker("Research")
        tracker.start()

        # Progress through stages
        tracker.update_stage(tracker.STAGE_SEARCHING, "Searching...", items_total=10)
        status1 = tracker.get_status()

        tracker.update_stage(tracker.STAGE_EXTRACTING, "Extracting...", items_total=10)
        status2 = tracker.get_status()

        tracker.update_stage(tracker.STAGE_SYNTHESIZING, "Synthesizing...")
        status3 = tracker.get_status()

        # Each stage should increase progress
        assert status1.percent < status2.percent < status3.percent

    def test_eta_estimation(self):
        """Test ETA estimation."""
        tracker = ProgressTracker("Test")
        tracker.start()
        tracker.update_stage(tracker.STAGE_SEARCHING, "Searching...")

        # Simulate some progress
        import time
        time.sleep(0.1)
        tracker.update_progress()

        status = tracker.get_status()
        # ETA should be calculated or None
        assert status.eta_seconds is None or isinstance(status.eta_seconds, float)

    def test_completion(self):
        """Test marking operation as complete."""
        tracker = ProgressTracker("Test")
        tracker.start()
        tracker.update_stage(tracker.STAGE_SEARCHING, "Searching...")
        tracker.complete("All done!")

        status = tracker.get_status()
        assert status.percent == 100.0
        assert status.stage == "complete"

    def test_metadata(self):
        """Test progress metadata."""
        tracker = ProgressTracker("Test")
        tracker.set_metadata('custom_field', 'custom_value')

        status = tracker.get_status()
        assert 'custom_field' in status.metadata
        assert status.metadata['custom_field'] == 'custom_value'

    def test_progress_summary(self):
        """Test getting progress summary."""
        tracker = ProgressTracker("Test")
        tracker.start()
        tracker.update_stage(tracker.STAGE_SEARCHING, "Searching...")
        tracker.update_stage(tracker.STAGE_EXTRACTING, "Extracting...")

        summary = tracker.get_summary()
        assert 'operation' in summary
        assert 'percent' in summary
        assert 'stages_completed' in summary
        assert summary['stages_completed'] == 1  # One stage completed


class TestIntegration:
    """Integration tests for Phase 5."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path("E:/TORQ-CONSOLE/tests/temp_exports")
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Cleanup."""
        if self.test_dir.exists():
            for file in self.test_dir.glob("*"):
                if file.is_file():
                    file.unlink()

    def test_export_with_progress(self):
        """Test export operation with progress tracking."""
        manager = ExportManager()
        tracker = ProgressTracker("Export Operation")

        progress_updates = []

        def on_progress(status: ProgressStatus):
            progress_updates.append(status.percent)

        tracker.on_progress(on_progress)
        tracker.start()

        # Simulate export stages
        tracker.update_stage("preparing", "Preparing export...")

        output_path = self.test_dir / "test_with_progress.md"
        success = manager.export_to_markdown(SAMPLE_RESULTS, str(output_path))

        tracker.update_stage("writing", "Writing file...")
        tracker.complete("Export complete")

        assert success is True
        assert output_path.exists()
        assert len(progress_updates) >= 2

    def test_full_research_export_workflow(self):
        """Test complete workflow: research → export."""
        # Simulate research results
        results = SAMPLE_RESULTS

        # Export to all formats
        manager = ExportManager()
        base_path = str(self.test_dir / "full_workflow")

        export_results = manager.export_all(
            results,
            base_path,
            formats=['markdown', 'json', 'csv']
        )

        # Verify all exports succeeded
        assert all(export_results.values())

        # Verify all files exist
        assert Path(f"{base_path}.md").exists()
        assert Path(f"{base_path}.json").exists()
        assert Path(f"{base_path}_sources.csv").exists()


def run_all_tests():
    """Run all Phase 5 tests."""
    print("=" * 70)
    print("Running Phase 5: Export & UX Tests")
    print("=" * 70)

    pytest_args = [
        __file__,
        '-v',
        '--tb=short',
        '-s',
        '--color=yes'
    ]

    exit_code = pytest.main(pytest_args)

    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✓ All Phase 5 tests PASSED")
    else:
        print("✗ Some Phase 5 tests FAILED")
    print("=" * 70)

    return exit_code


if __name__ == '__main__':
    exit(run_all_tests())
