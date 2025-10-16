"""
CSV Exporter

Exports research results to CSV format for analysis in spreadsheet applications.
"""

import csv
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime


class CSVExporter:
    """Export research results to CSV format."""

    def __init__(self):
        """Initialize the CSV exporter."""
        self.logger = logging.getLogger(__name__)

    def export(
        self,
        results: Dict[str, Any],
        output_path: str,
        mode: str = 'sources'  # 'sources' or 'insights'
    ) -> bool:
        """
        Export results to CSV file.

        Args:
            results: Research results dictionary
            output_path: Path to output CSV file
            mode: Export mode - 'sources' for source list or 'insights' for key insights

        Returns:
            True if export successful, False otherwise
        """
        try:
            if mode == 'sources':
                self._export_sources(results, output_path)
            elif mode == 'insights':
                self._export_insights(results, output_path)
            else:
                raise ValueError(f"Invalid mode: {mode}")

            self.logger.info(f"[CSV] Exported to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"[CSV] Export failed: {e}")
            return False

    def _export_sources(self, results: Dict[str, Any], output_path: str):
        """Export sources to CSV."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Get sources
        sources = []
        if 'extracted_documents' in results:
            sources = results['extracted_documents']
        elif 'results' in results:
            sources = results['results']

        # Get confidence scores
        confidence_scores = results.get('confidence_scores', [])

        # Prepare rows
        rows = []
        for i, source in enumerate(sources):
            row = {
                'Index': i + 1,
                'Title': source.get('title', 'Untitled'),
                'URL': source.get('url', ''),
                'Author': source.get('author', ''),
                'Published': source.get('date_published', ''),
                'Word_Count': source.get('word_count', 0)
            }

            # Add confidence scores if available
            if i < len(confidence_scores):
                score_data = confidence_scores[i]
                row.update({
                    'Confidence_Overall': score_data.get('overall_score', 0),
                    'Confidence_Level': score_data.get('level', ''),
                    'Source_Reliability': score_data.get('source_reliability', 0),
                    'Content_Quality': score_data.get('content_quality', 0),
                    'Freshness': score_data.get('freshness', 0)
                })

            rows.append(row)

        # Write CSV
        if rows:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

    def _export_insights(self, results: Dict[str, Any], output_path: str):
        """Export key insights to CSV."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        synthesis = results.get('synthesis', {})
        insights = synthesis.get('key_insights', [])

        # Prepare rows
        rows = []
        for i, insight in enumerate(insights, 1):
            sources = insight.get('sources', [])
            row = {
                'Index': i,
                'Insight': insight.get('text', ''),
                'Confidence': insight.get('confidence', 0),
                'Source_Count': len(sources),
                'Sources': '; '.join(sources) if sources else ''
            }
            rows.append(row)

        # Write CSV
        if rows:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

    def export_both(self, results: Dict[str, Any], base_path: str) -> tuple[bool, bool]:
        """
        Export both sources and insights to separate CSV files.

        Args:
            results: Research results
            base_path: Base path (without extension)

        Returns:
            Tuple of (sources_success, insights_success)
        """
        sources_path = f"{base_path}_sources.csv"
        insights_path = f"{base_path}_insights.csv"

        sources_ok = self.export(results, sources_path, mode='sources')
        insights_ok = self.export(results, insights_path, mode='insights')

        return sources_ok, insights_ok
