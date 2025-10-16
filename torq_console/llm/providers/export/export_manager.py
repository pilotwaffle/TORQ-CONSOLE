"""
Export Manager

Central manager for all export operations.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .markdown_exporter import MarkdownExporter
from .csv_exporter import CSVExporter
from .json_exporter import JSONExporter
from .pdf_exporter import PDFExporter


class ExportManager:
    """
    Central manager for exporting research results to various formats.

    Supported formats:
    - Markdown (.md)
    - CSV (.csv)
    - JSON (.json)
    - PDF (.pdf) - requires weasyprint or reportlab
    """

    def __init__(self):
        """Initialize the export manager."""
        self.logger = logging.getLogger(__name__)

        # Initialize exporters
        self.markdown_exporter = MarkdownExporter()
        self.csv_exporter = CSVExporter()
        self.json_exporter = JSONExporter()
        self.pdf_exporter = PDFExporter()

        self.logger.info("[EXPORT] Export manager initialized")

    def export(
        self,
        results: Dict[str, Any],
        output_path: str,
        format: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Export results to specified format.

        Args:
            results: Research results dictionary
            output_path: Path to output file
            format: Export format (auto-detected from extension if None)
            **kwargs: Format-specific options

        Returns:
            True if export successful, False otherwise
        """
        # Auto-detect format from extension
        if format is None:
            format = Path(output_path).suffix.lower().lstrip('.')

        # Route to appropriate exporter
        if format in ['md', 'markdown']:
            return self.export_to_markdown(results, output_path, **kwargs)
        elif format == 'csv':
            return self.export_to_csv(results, output_path, **kwargs)
        elif format == 'json':
            return self.export_to_json(results, output_path, **kwargs)
        elif format == 'pdf':
            return self.export_to_pdf(results, output_path, **kwargs)
        else:
            self.logger.error(f"[EXPORT] Unsupported format: {format}")
            return False

    def export_to_markdown(
        self,
        results: Dict[str, Any],
        output_path: str,
        include_metadata: bool = True,
        include_sources: bool = True,
        include_insights: bool = True
    ) -> bool:
        """
        Export to Markdown format.

        Args:
            results: Research results
            output_path: Output file path
            include_metadata: Include metadata section
            include_sources: Include source list
            include_insights: Include key insights

        Returns:
            True if successful
        """
        return self.markdown_exporter.export(
            results,
            output_path,
            include_metadata,
            include_sources,
            include_insights
        )

    def export_to_csv(
        self,
        results: Dict[str, Any],
        output_path: str,
        mode: str = 'sources'
    ) -> bool:
        """
        Export to CSV format.

        Args:
            results: Research results
            output_path: Output file path
            mode: 'sources' or 'insights'

        Returns:
            True if successful
        """
        return self.csv_exporter.export(results, output_path, mode)

    def export_to_json(
        self,
        results: Dict[str, Any],
        output_path: str,
        pretty: bool = True,
        include_metadata: bool = True
    ) -> bool:
        """
        Export to JSON format.

        Args:
            results: Research results
            output_path: Output file path
            pretty: Use pretty printing
            include_metadata: Include export metadata

        Returns:
            True if successful
        """
        return self.json_exporter.export(
            results,
            output_path,
            pretty,
            include_metadata
        )

    def export_to_pdf(
        self,
        results: Dict[str, Any],
        output_path: str,
        method: str = 'auto'
    ) -> bool:
        """
        Export to PDF format.

        Args:
            results: Research results
            output_path: Output file path
            method: PDF generation method ('auto', 'weasyprint', 'reportlab')

        Returns:
            True if successful
        """
        return self.pdf_exporter.export(results, output_path, method)

    def export_all(
        self,
        results: Dict[str, Any],
        base_path: str,
        formats: Optional[list] = None
    ) -> Dict[str, bool]:
        """
        Export to multiple formats at once.

        Args:
            results: Research results
            base_path: Base path without extension
            formats: List of formats to export (default: all)

        Returns:
            Dictionary mapping format to success status
        """
        if formats is None:
            formats = ['markdown', 'csv', 'json', 'pdf']

        results_dict = {}

        for format in formats:
            if format in ['md', 'markdown']:
                output_path = f"{base_path}.md"
                results_dict['markdown'] = self.export_to_markdown(results, output_path)

            elif format == 'csv':
                # Export both sources and insights
                sources_ok, insights_ok = self.csv_exporter.export_both(results, base_path)
                results_dict['csv_sources'] = sources_ok
                results_dict['csv_insights'] = insights_ok

            elif format == 'json':
                output_path = f"{base_path}.json"
                results_dict['json'] = self.export_to_json(results, output_path)

            elif format == 'pdf':
                output_path = f"{base_path}.pdf"
                results_dict['pdf'] = self.export_to_pdf(results, output_path)

        return results_dict

    def get_supported_formats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about supported formats.

        Returns:
            Dictionary with format information
        """
        return {
            'markdown': {
                'extension': '.md',
                'description': 'Human-readable formatted text',
                'available': True,
                'features': ['metadata', 'sources', 'insights', 'citations']
            },
            'csv': {
                'extension': '.csv',
                'description': 'Spreadsheet-compatible tabular data',
                'available': True,
                'features': ['sources_table', 'insights_table', 'confidence_scores']
            },
            'json': {
                'extension': '.json',
                'description': 'Machine-readable structured data',
                'available': True,
                'features': ['complete_data', 'programmatic_access', 'metadata']
            },
            'pdf': {
                'extension': '.pdf',
                'description': 'Professional document format',
                'available': self.pdf_exporter.is_available(),
                'features': ['formatted_layout', 'print_ready'],
                'requires': 'weasyprint or reportlab'
            }
        }

    def export_to_string(
        self,
        results: Dict[str, Any],
        format: str = 'markdown'
    ) -> Optional[str]:
        """
        Export to string without saving to file.

        Args:
            results: Research results
            format: Export format

        Returns:
            Exported content as string, or None if failed
        """
        try:
            if format in ['md', 'markdown']:
                return self.markdown_exporter.export_to_string(results)
            elif format == 'json':
                return self.json_exporter.export_to_string(results)
            else:
                self.logger.warning(f"[EXPORT] String export not supported for format: {format}")
                return None

        except Exception as e:
            self.logger.error(f"[EXPORT] String export failed: {e}")
            return None
