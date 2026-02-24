"""
Citation Enforcement and Policy

Ensures research-mode responses include proper citations.
Implements "citation-required" policy for research queries.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from .schema import ResearchSource, SynthesisResponse
from .canonicalizer import (
    canonicalize_citations,
    normalize_url,
    normalize_sources,
    format_citations_markdown as canonical_format_markdown,
    validate_citation_format,
    CanonicalCitation,
)

logger = logging.getLogger(__name__)


class CitationExtractor(BaseModel):
    """Extracted citation from text."""
    index: int
    title: str
    url: str
    context: str
    confidence: float = 1.0


class CitationPolicy:
    """
    Enforces citation requirements for research responses.

    Policy:
    - Research mode requires min_sources >= 2
    - Citations must be in consistent format
    - Missing citations trigger auto-retry
    - Uses canonicalization for deterministic output
    """

    # Citation patterns to detect
    CITATION_PATTERNS = [
        r"\[(\d+)\]",  # [1], [2]
        r"\[source\s*[\d:]+\]",  # [source:1], [source 1]
        r"\(source:\s*[\d]+\)",  # (source: 1)
        r"according to\s+[^\n]+?\(https?:|[^\n]{0,100}\.com",  # "according to X (url"
        r"per\s+[^\n]{1,50}\(https?:",  # "per X (https://"
        r"\[([^\]]+)\]\((https?:)",  # [Title](url)
        r"sources?:\s*\[?[^\n]{1,100}\]?\(https?:",  # sources: [Title](url)
    ]

    def __init__(
        self,
        min_sources: int = 2,
        require_consistent_format: bool = True,
        auto_retry: bool = True,
        enable_canonicalization: bool = True,
    ):
        self.min_sources = min_sources
        self.require_consistent_format = require_consistent_format
        self.auto_retry = auto_retry
        self.enable_canonicalization = enable_canonicalization

    def check_citations(
        self,
        answer: str,
        sources: List[ResearchSource],
    ) -> Dict[str, Any]:
        """
        Check if answer meets citation requirements.

        Returns:
            {
                "has_citations": bool,
                "citation_count": int,
                "meets_minimum": bool,
                "format_consistent": bool,
                "extracted_citations": List[Citation],
                "missing_sources": List[str],
                "validation": {...},  # From validate_citation_format
            }
        """
        citations = self._extract_citations(answer, sources)

        # Validate format using canonicalizer
        validation = validate_citation_format(answer, sources)

        return {
            "has_citations": len(citations) > 0,
            "citation_count": len(citations),
            "meets_minimum": len(citations) >= self.min_sources,
            "format_consistent": validation["is_valid"] and len(validation["errors"]) == 0,
            "extracted_citations": [c.model_dump() for c in citations],
            "missing_sources": self._get_missing_sources(citations, sources),
            "validation": validation,
        }

    def _extract_citations(
        self,
        answer: str,
        sources: List[ResearchSource],
    ) -> List[CitationExtractor]:
        """Extract citations from answer text."""
        citations = []

        # Try to match [1], [2] style citations
        number_pattern = re.compile(r"\[(\d+)\]")
        numbers = number_pattern.findall(answer)

        for idx, num in enumerate(numbers, start=1):
            source_idx = int(num) - 1
            if 0 <= source_idx < len(sources):
                citations.append(CitationExtractor(
                    index=idx,
                    title=sources[source_idx].title,
                    url=sources[source_idx].url,
                    context=self._extract_context(answer, sources[source_idx].url),
                    confidence=1.0,
                ))

        # Try to find URL citations directly
        url_pattern = re.compile(r"\(https?:[^\)]+\)")
        for match in url_pattern.finditer(answer):
            url = match.group(0)[1:-1]  # Remove parentheses
            citations.append(CitationExtractor(
                index=len(citations) + 1,
                title="Unknown",
                url=url,
                context=self._extract_context(answer, url),
                confidence=0.8,
            ))

        return citations

    def _extract_context(self, answer: str, url: str) -> str:
        """Extract the context around a citation in the answer."""
        # Find the URL or reference in the text
        if url in answer:
            idx = answer.find(url)
            # Get 100 chars before and after
            start = max(0, idx - 100)
            end = min(len(answer), idx + 100)
            return answer[start:end].replace("\n", " ")
        return ""

    def _check_format_consistency(self, citations: List) -> bool:
        """Check if citations are in a consistent format."""
        if not citations:
            return False
        # For now, just check we have citations
        return True

    def _get_missing_sources(
        self,
        citations: List,
        sources: List[ResearchSource],
    ) -> List[str]:
        """Identify sources that were referenced but not properly cited."""
        cited_urls = {c.url for c in citations}
        missing = []

        for source in sources:
            if source.url not in cited_urls:
                missing.append(source.title)

        return missing

    def format_citations_markdown(self, sources: List[ResearchSource]) -> str:
        """Format citations as markdown for inclusion in answer.

        Uses canonicalized format for deterministic output.
        """
        if not sources:
            return ""

        # Normalize sources first for stable ordering
        normalized = normalize_sources(sources)
        return canonical_format_markdown(normalized)

    def canonicalize_response(
        self,
        answer: str,
        sources: List[ResearchSource],
        trust_scores: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Canonicalize citations in a response.

        This makes output deterministic by:
        1. Normalizing URLs and deduplicating sources
        2. Stable sorting by trust score, date, title
        3. Assigning stable [n] IDs
        4. Rewriting answer to match canonical numbering

        Returns canonicalization result with updated answer and sources.
        """
        if not self.enable_canonicalization:
            return {
                "answer": answer,
                "sources": sources,
                "citations": [],
                "mapping": {},
                "duplicates_removed": 0,
            }

        return canonicalize_citations(answer, sources, trust_scores)

    def should_retry(self, check_result: Dict[str, Any]) -> bool:
        """Determine if citation enforcement should trigger a retry."""
        if not self.auto_retry:
            return False

        # Retry if citations missing below minimum
        if not check_result["meets_minimum"]:
            return True

        # Retry if format is inconsistent and we have citations
        validation = check_result.get("validation", {})
        if validation.get("errors"):
            return True

        if check_result["has_citations"] and not check_result["format_consistent"]:
            return True

        return False

    async def retry_with_citations(
        self,
        original_query: str,
        original_answer: str,
        sources: List[ResearchSource],
        llm_provider,
    ) -> str:
        """
        Retry LLM call to add missing citations.

        Prompt the model to add citations to its existing answer.
        """
        citation_block = self.format_citations_markdown(sources)

        retry_prompt = f"""Your previous answer is below. Please add proper citations to it.

Original question: {original_query}

Your answer:
{original_answer}

Available sources to cite:
{citation_block}

Please rewrite your answer with proper inline citations like [1], [2] that reference these sources.
Quote exact lines sparingly - only for key facts.
Keep your original answer structure but add citations where appropriate."""

        try:
            response = await llm_provider.query(retry_prompt)
            return response
        except Exception as e:
            logger.error(f"Citation retry failed: {e}")
            return original_answer  # Return original on failure


class CitationFormatter:
    """Formats citations in various styles."""

    @staticmethod
    def markdown(sources: List[ResearchSource]) -> str:
        """Format as markdown footnotes.

        Uses canonicalization for deterministic output.
        """
        normalized = normalize_sources(sources)
        return canonical_format_markdown(normalized)

    @staticmethod
    def inline(sources: List[ResearchSource]) -> str:
        """Format as inline citations in brackets."""
        return " ".join([f"[{i+1}]" for i in range(len(sources))])

    @staticmethod
    def json_format(sources: List[ResearchSource]) -> str:
        """Format as JSON for structured output."""
        import json
        return json.dumps([
            {"title": s.title, "url": s.url, "published_at": s.published_at}
            for s in sources
        ], indent=2)

    @staticmethod
    def canonical(
        answer: str,
        sources: List[ResearchSource],
        trust_scores: Optional[Dict[str, float]] = None,
    ) -> str:
        """
        Return answer with canonicalized citations.

        This is the recommended format for production use.
        """
        result = canonicalize_citations(answer, sources, trust_scores)
        return result["answer"]


def create_citation_policy(**kwargs) -> CitationPolicy:
    """Factory to create a citation policy instance."""
    return CitationPolicy(**kwargs)


# Singleton
_default_policy: Optional[CitationPolicy] = None


def get_citation_policy() -> CitationPolicy:
    """Get the default citation policy."""
    global _default_policy
    if _default_policy is None:
        _default_policy = CitationPolicy()
    return _default_policy


# Export canonicalization helpers
__all__ = [
    "CitationPolicy",
    "CitationFormatter",
    "CitationExtractor",
    "get_citation_policy",
    "create_citation_policy",
    "canonicalize_citations",
    "normalize_url",
    "normalize_sources",
    "validate_citation_format",
    "CanonicalCitation",
]
