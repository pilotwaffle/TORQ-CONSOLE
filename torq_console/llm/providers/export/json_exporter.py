"""
JSON Exporter

Exports research results to JSON format for programmatic access.
"""

import json
import logging
from typing import Dict, Any
from pathlib import Path
from datetime import datetime


class JSONExporter:
    """Export research results to JSON format."""

    def __init__(self):
        """Initialize the JSON exporter."""
        self.logger = logging.getLogger(__name__)

    def export(
        self,
        results: Dict[str, Any],
        output_path: str,
        pretty: bool = True,
        include_metadata: bool = True
    ) -> bool:
        """
        Export results to JSON file.

        Args:
            results: Research results dictionary
            output_path: Path to output JSON file
            pretty: Use pretty printing with indentation
            include_metadata: Include export metadata

        Returns:
            True if export successful, False otherwise
        """
        try:
            # Prepare data
            export_data = self._prepare_export_data(results, include_metadata)

            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(export_data, f, ensure_ascii=False)

            self.logger.info(f"[JSON] Exported to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"[JSON] Export failed: {e}")
            return False

    def _prepare_export_data(
        self,
        results: Dict[str, Any],
        include_metadata: bool
    ) -> Dict[str, Any]:
        """Prepare data for JSON export."""
        export_data = {}

        # Add export metadata
        if include_metadata:
            export_data['export_metadata'] = {
                'exported_at': datetime.now().isoformat(),
                'exporter': 'TORQ Console Phase 5',
                'version': '1.0.0'
            }

        # Add research metadata
        export_data['research_metadata'] = {
            'query': results.get('query', ''),
            'timestamp': results.get('timestamp', ''),
            'method_used': results.get('method_used', ''),
            'synthesis_enabled': results.get('synthesis_enabled', False)
        }

        # Add synthesis results if available
        if 'synthesis' in results:
            export_data['synthesis'] = self._serialize_synthesis(results['synthesis'])

        # Add sources
        if 'extracted_documents' in results:
            export_data['sources'] = self._serialize_sources(
                results['extracted_documents'],
                results.get('confidence_scores', [])
            )
        elif 'results' in results:
            export_data['sources'] = results['results']

        # Add confidence scores
        if 'confidence_scores' in results:
            export_data['confidence_scores'] = results['confidence_scores']

        return export_data

    def _serialize_synthesis(self, synthesis: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize synthesis data."""
        return {
            'summary': synthesis.get('summary', ''),
            'key_insights': synthesis.get('key_insights', []),
            'topics': synthesis.get('topics', []),
            'overall_confidence': synthesis.get('overall_confidence', 0),
            'source_diversity': synthesis.get('source_diversity', 0),
            'consensus_level': synthesis.get('consensus_level', 0),
            'contradictions': synthesis.get('contradictions', []),
            'word_count': synthesis.get('word_count', 0),
            'sources_used': synthesis.get('sources_used', [])
        }

    def _serialize_sources(
        self,
        sources: list,
        confidence_scores: list
    ) -> list:
        """Serialize source data with confidence scores."""
        serialized = []

        for i, source in enumerate(sources):
            source_data = {
                'title': source.get('title', ''),
                'url': source.get('url', ''),
                'author': source.get('author', ''),
                'date_published': source.get('date_published', ''),
                'content_preview': source.get('content', '')[:500] if source.get('content') else '',
                'word_count': source.get('word_count', 0),
                'keywords': source.get('keywords', [])
            }

            # Add confidence score if available
            if i < len(confidence_scores):
                source_data['confidence'] = confidence_scores[i]

            serialized.append(source_data)

        return serialized

    def export_to_string(self, results: Dict[str, Any], pretty: bool = True) -> str:
        """Export to JSON string without saving to file."""
        export_data = self._prepare_export_data(results, include_metadata=True)

        if pretty:
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(export_data, ensure_ascii=False)
