"""
SearchMaster Output Formatters

Provides 4 output modes for different user personas:
- SIMPLE: Casual users (1-3 lines)
- STANDARD: Default balanced (10-20 lines)
- DETAILED: Analysts (full verification + tables)
- TECHNICAL: Developers (JSON + debug)
"""

import json
import re
from typing import Dict, List, Any, Union
from datetime import datetime


class SimpleFormatter:
    """Format for casual users - just the answer"""

    def format(self, report, agent=None) -> str:
        """Single line when possible, max 3 lines"""
        if not report.results:
            return f"No results found for: {report.query}"

        top = report.results[0]

        # Confidence indicator
        if report.confidence_level == "verified":
            indicator = "[OK]"
        elif report.confidence_level == "partial":
            indicator = "[PARTIAL]"
        else:
            indicator = "[UNVERIFIED]"

        # Single result: one line
        if len(report.results) == 1:
            snippet = top.snippet[:100].replace('\n', ' ')
            return f"{indicator} {snippet} | Source: {top.source}"

        # Multiple results: top 3 with bullets
        lines = [f"Found {len(report.results)} results ({report.confidence_level}):"]
        for i, result in enumerate(report.results[:3], 1):
            snippet = result.snippet[:60].replace('\n', ' ')
            lines.append(f"  {i}. {snippet}... ({result.source})")

        return '\n'.join(lines)


class StandardFormatter:
    """Format for default users - balanced detail"""

    def format(self, report, agent=None) -> str:
        """10-20 lines with key information"""
        lines = []

        # Header
        lines.append(f"Query: {report.query}")
        lines.append(f"Confidence: {report.confidence_level.title()} ({report.overall_confidence:.0%})")
        lines.append(f"Sources: {', '.join(report.sources_used)}")
        lines.append(f"Duration: {report.search_duration:.2f}s")
        lines.append("")

        # Results
        if not report.results:
            lines.append("No results found.")
        else:
            lines.append(f"Top Results ({len(report.results)} found):")
            for i, result in enumerate(report.results[:5], 1):
                lines.append(f"{i}. {result.title}")
                lines.append(f"   Source: {result.source} | Status: {result.verification_status.title()}")
                snippet = result.snippet[:150].replace('\n', ' ')
                lines.append(f"   {snippet}...")
                lines.append("")

        # Next steps (if available)
        if report.next_steps:
            lines.append("Suggested Next Steps:")
            for step in report.next_steps[:3]:
                lines.append(f"  - {step}")

        return '\n'.join(lines)


class DetailedFormatter:
    """Format for analysts - full verification + tables"""

    def format(self, report, agent=None) -> str:
        """Complete markdown output with tables"""
        lines = []

        # Header
        lines.append(f"## Search Results: {report.query}")
        lines.append("")
        lines.append("**Metadata:**")
        lines.append(f"- Category: {report.query_type}")
        lines.append(f"- Confidence: {report.confidence_level.title()} ({report.overall_confidence:.2f})")
        lines.append(f"- Sources: {', '.join(report.sources_used)}")
        lines.append(f"- Duration: {report.search_duration:.2f}s")
        lines.append(f"- Timestamp: {report.timestamp}")
        lines.append("")

        # Verification details
        if report.verification_details:
            lines.append("**Verification:**")
            lines.append(f"- Verified claims: {report.verification_details.get('verified_claims', 0)}")
            lines.append(f"- Partial claims: {report.verification_details.get('partial_claims', 0)}")
            lines.append(f"- Unverified claims: {report.verification_details.get('unverified_claims', 0)}")
            lines.append("")

        # Results table
        if report.results:
            if len(report.results) >= 3:
                lines.append("**Results:**")
                lines.append("")
                lines.append(self._format_table(report.results))
            else:
                lines.append("**Results:**")
                lines.append("")
                for i, result in enumerate(report.results, 1):
                    lines.append(f"{i}. **{result.title}**")
                    lines.append(f"   - Source: {result.source}")
                    lines.append(f"   - Verification: {result.verification_status.title()}")
                    lines.append(f"   - Relevance: {result.relevance_score:.2f}")
                    if result.published_date:
                        lines.append(f"   - Date: {result.published_date[:10]}")
                    lines.append("")

        # Limitations
        lines.append("**Limitations:**")
        if report.limitations:
            for lim in report.limitations:
                lines.append(f"- {lim}")
        else:
            lines.append("- None (all APIs responded successfully)")
        lines.append("")

        # Next steps
        lines.append("**Next Steps:**")
        for step in report.next_steps or ["No suggestions"]:
            lines.append(f"- {step}")

        return '\n'.join(lines)

    def _format_table(self, results: List) -> str:
        """Generate markdown table"""
        lines = []

        # Header
        lines.append("| Title | Source | Verification | Relevance |")
        lines.append("| --- | --- | --- | --- |")

        # Rows
        for result in results[:10]:
            title = result.title[:50] + "..." if len(result.title) > 50 else result.title
            title = title.replace('|', '\\|')  # Escape pipes

            lines.append(
                f"| {title} "
                f"| {result.source} "
                f"| {result.verification_status.title()} "
                f"| {result.relevance_score:.2f} |"
            )

        return '\n'.join(lines)


class TechnicalFormatter:
    """Format for developers - JSON + debug info"""

    def format(self, report, agent=None) -> Dict:
        """Return JSON with debug information"""
        # Convert dataclasses to dicts
        results_data = []
        for r in report.results:
            result_dict = {
                'title': r.title,
                'snippet': r.snippet,
                'url': r.url,
                'source': r.source,
                'relevance_score': r.relevance_score,
                'published_date': r.published_date,
                'verification_status': r.verification_status,
                'corroborating_sources': r.corroborating_sources,
                'is_structured_data': r.is_structured_data,
                'is_ai_synthesis': r.is_ai_synthesis,
                'metadata': r.metadata
            }
            results_data.append(result_dict)

        # Build complete JSON
        output = {
            'query': report.query,
            'query_type': report.query_type,
            'confidence_level': report.confidence_level,
            'overall_confidence': report.overall_confidence,
            'total_results': report.total_results,
            'sources_used': report.sources_used,
            'search_duration': report.search_duration,
            'timestamp': report.timestamp,
            'results': results_data,
            'verification_details': report.verification_details,
            'limitations': report.limitations,
            'next_steps': report.next_steps,
        }

        # Add debug info if agent available
        if agent:
            output['debug'] = {
                'failed_apis': agent.failed_apis,
                'api_errors': agent.api_errors,
                'search_sources_available': {k: v for k, v in agent.search_sources.items() if v},
                'config': {
                    'recency_days': agent.default_recency_days,
                    'require_corroboration': agent.require_corroboration,
                    'min_sources_for_verification': agent.min_sources_for_verification
                }
            }

        return output


# Formatter factory
def get_formatter(mode):
    """Get formatter instance for given mode"""
    from . import torq_search_master  # Avoid circular import

    if mode == torq_search_master.OutputMode.SIMPLE:
        return SimpleFormatter()
    elif mode == torq_search_master.OutputMode.STANDARD:
        return StandardFormatter()
    elif mode == torq_search_master.OutputMode.DETAILED:
        return DetailedFormatter()
    elif mode == torq_search_master.OutputMode.TECHNICAL:
        return TechnicalFormatter()
    else:
        return StandardFormatter()  # Default
