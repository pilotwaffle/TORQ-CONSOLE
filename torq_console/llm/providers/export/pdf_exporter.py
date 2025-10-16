"""
PDF Exporter

Exports research results to PDF format via Markdown conversion.
"""

import logging
from typing import Dict, Any
from pathlib import Path


class PDFExporter:
    """Export research results to PDF format."""

    def __init__(self):
        """Initialize the PDF exporter."""
        self.logger = logging.getLogger(__name__)
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required dependencies are available."""
        self.markdown_available = False
        self.weasyprint_available = False
        self.reportlab_available = False

        try:
            import markdown
            self.markdown_available = True
        except ImportError:
            pass

        try:
            import weasyprint
            self.weasyprint_available = True
        except ImportError:
            pass

        try:
            import reportlab
            self.reportlab_available = True
        except ImportError:
            pass

    def export(
        self,
        results: Dict[str, Any],
        output_path: str,
        method: str = 'auto'  # 'auto', 'weasyprint', 'reportlab'
    ) -> bool:
        """
        Export results to PDF file.

        Args:
            results: Research results dictionary
            output_path: Path to output PDF file
            method: PDF generation method

        Returns:
            True if export successful, False otherwise
        """
        try:
            # Select method
            if method == 'auto':
                if self.weasyprint_available:
                    return self._export_with_weasyprint(results, output_path)
                elif self.reportlab_available:
                    return self._export_with_reportlab(results, output_path)
                else:
                    self.logger.warning("[PDF] No PDF library available. Install weasyprint or reportlab.")
                    return self._export_placeholder(results, output_path)
            elif method == 'weasyprint':
                return self._export_with_weasyprint(results, output_path)
            elif method == 'reportlab':
                return self._export_with_reportlab(results, output_path)
            else:
                raise ValueError(f"Invalid method: {method}")

        except Exception as e:
            self.logger.error(f"[PDF] Export failed: {e}")
            return False

    def _export_with_weasyprint(self, results: Dict[str, Any], output_path: str) -> bool:
        """Export using WeasyPrint (HTML/CSS to PDF)."""
        if not self.weasyprint_available:
            self.logger.error("[PDF] WeasyPrint not available")
            return False

        try:
            from weasyprint import HTML, CSS
            from .markdown_exporter import MarkdownExporter

            # Convert to Markdown first
            md_exporter = MarkdownExporter()
            markdown_content = md_exporter.export_to_string(results)

            # Convert Markdown to HTML
            if self.markdown_available:
                import markdown
                html_content = markdown.markdown(
                    markdown_content,
                    extensions=['tables', 'fenced_code', 'codehilite']
                )
            else:
                # Simple markdown conversion
                html_content = self._simple_markdown_to_html(markdown_content)

            # Wrap in HTML document with CSS
            full_html = self._wrap_html(html_content)

            # Generate PDF
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            HTML(string=full_html).write_pdf(output_path)

            self.logger.info(f"[PDF] Exported with WeasyPrint to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"[PDF] WeasyPrint export failed: {e}")
            return False

    def _export_with_reportlab(self, results: Dict[str, Any], output_path: str) -> bool:
        """Export using ReportLab (native PDF generation)."""
        if not self.reportlab_available:
            self.logger.error("[PDF] ReportLab not available")
            return False

        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib import colors

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Create PDF
            doc = SimpleDocTemplate(str(output_file), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            # Title
            title = Paragraph(f"<b>Research Report: {results.get('query', 'N/A')}</b>",
                            styles['Title'])
            story.append(title)
            story.append(Spacer(1, 0.2*inch))

            # Metadata
            timestamp = results.get('timestamp', 'N/A')
            story.append(Paragraph(f"<b>Generated:</b> {timestamp}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))

            # Summary
            if 'synthesis' in results:
                synthesis = results['synthesis']
                story.append(Paragraph("<b>Summary</b>", styles['Heading2']))
                story.append(Paragraph(synthesis.get('summary', ''), styles['Normal']))
                story.append(Spacer(1, 0.2*inch))

                # Metrics
                story.append(Paragraph(
                    f"Overall Confidence: {synthesis.get('overall_confidence', 0):.2f}",
                    styles['Normal']
                ))
                story.append(Spacer(1, 0.1*inch))

            # Sources
            if 'extracted_documents' in results:
                story.append(Paragraph("<b>Sources</b>", styles['Heading2']))
                for i, source in enumerate(results['extracted_documents'][:10], 1):
                    source_text = f"[{i}] {source.get('title', 'Untitled')}"
                    story.append(Paragraph(source_text, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))

            # Build PDF
            doc.build(story)

            self.logger.info(f"[PDF] Exported with ReportLab to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"[PDF] ReportLab export failed: {e}")
            return False

    def _export_placeholder(self, results: Dict[str, Any], output_path: str) -> bool:
        """Export a text file explaining PDF requirements."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Write info text instead
            info_path = output_file.with_suffix('.txt')
            info_text = f"""
TORQ Console - PDF Export

PDF export requires additional dependencies.
Please install one of the following:

Option 1 (Recommended):
    pip install weasyprint

Option 2:
    pip install reportlab

After installation, run the export again.

Research Query: {results.get('query', 'N/A')}
Timestamp: {results.get('timestamp', 'N/A')}

For now, the results have been saved as a text file.
Consider exporting to Markdown or JSON formats which don't require additional dependencies.
"""
            info_path.write_text(info_text, encoding='utf-8')

            self.logger.warning(f"[PDF] Saved info file to {info_path}. Install weasyprint or reportlab for PDF export.")
            return False

        except Exception as e:
            self.logger.error(f"[PDF] Failed to create placeholder: {e}")
            return False

    def _simple_markdown_to_html(self, markdown_text: str) -> str:
        """Simple markdown to HTML conversion (fallback)."""
        html = markdown_text
        html = html.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
        html = html.replace('## ', '<h2>').replace('\n', '</h2>\n')
        html = html.replace('**', '<b>', 1).replace('**', '</b>', 1)
        html = html.replace('- ', '<li>')
        html = html.replace('\n\n', '</p><p>')
        return f'<p>{html}</p>'

    def _wrap_html(self, html_content: str) -> str:
        """Wrap HTML content in a complete HTML document with CSS."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        pre {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

    def is_available(self) -> bool:
        """Check if PDF export is available."""
        return self.weasyprint_available or self.reportlab_available
