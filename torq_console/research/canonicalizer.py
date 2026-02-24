"""
Citation Canonicalization

Makes citation formatting deterministic by:
1. Normalizing URLs (lowercase, strip tracking params, dedupe)
2. Stable sorting (trust score, date, title, URL)
3. Assigning stable [n] IDs
4. Rewriting LLM output to match canonical format

This prevents test flakiness and ensures consistent output.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qs
from pydantic import BaseModel

from .schema import ResearchSource

logger = logging.getLogger(__name__)


# URL tracking parameters to strip
TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'fbclid', 'gclid', 'msclkid', 'ref', 'source', 'feature',
    'si', 'sfnsn', 'sni', 'scid',
}


class CanonicalCitation(BaseModel):
    """A canonicalized citation with stable ordering."""
    index: int  # Stable [n] ID
    title: str
    url: str  # Normalized URL
    original_url: str  # For reference
    domain: str
    snippet: Optional[str] = None
    published_at: Optional[str] = None
    trust_score: float = 0.5
    confidence: float = 1.0


def normalize_url(url: str) -> str:
    """
    Normalize URL for deduplication.

    1. Lowercase scheme, host, and path
    2. Strip tracking parameters (utm_*, fbclid, gclid, etc.)
    3. Remove trailing slash (except root)
    4. Sort remaining query parameters
    """
    try:
        parsed = urlparse(url)

        # Lowercase scheme and netloc
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Lowercase path for case-insensitive comparison
        # (URLs are technically case-sensitive for path, but we want to dedupe)
        path = parsed.path.lower()

        # Parse and filter query params
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        filtered_params = {
            k: v for k, v in query_params.items()
            if k not in TRACKING_PARAMS
        }

        # Rebuild query string with sorted params
        query_str = "&".join(
            f"{k}={'&'.join(v) if len(v) > 1 else v[0]}"
            for k, v in sorted(filtered_params.items())
        )

        # Remove trailing slash from path (except for root)
        if path.endswith('/') and len(path) > 1:
            path = path[:-1]

        # Rebuild URL
        normalized = urlunparse((
            scheme,
            netloc,
            path,
            parsed.params,
            query_str,
            ''  # Strip fragment too (often for tracking)
        ))

        return normalized
    except Exception as e:
        logger.warning(f"Failed to normalize URL {url}: {e}")
        return url


def normalize_sources(
    sources: List[ResearchSource],
    trust_scores: Optional[Dict[str, float]] = None,
) -> List[ResearchSource]:
    """
    Normalize and deduplicate sources.

    Returns a stable, deduplicated list sorted by:
    1. Trust score (descending)
    2. Published date (descending if present)
    3. Title (ascending)
    4. URL (ascending)
    """
    if not sources:
        return []

    # Track seen URLs and choose best instance
    seen_urls: Dict[str, ResearchSource] = {}
    source_trust: Dict[str, float] = trust_scores or {}

    for source in sources:
        # Normalize URL
        normalized_url = normalize_url(source.url)
        domain = urlparse(normalized_url).netloc or source.domain or ""

        # Get or compute trust score
        trust = source_trust.get(domain, source.score or 0.5)

        # Update source with normalized data
        normalized_source = ResearchSource(
            title=source.title,
            url=normalized_url,
            snippet=source.snippet,
            published_at=source.published_at,
            score=trust,
            provider=source.provider,
            domain=domain,
            is_news=source.is_news,
            is_primary=source.is_primary,
        )

        # Keep highest-trust instance of each URL
        if normalized_url not in seen_urls or trust > seen_urls[normalized_url].score:
            seen_urls[normalized_url] = normalized_source

    # Sort by stable criteria
    def sort_key(source: ResearchSource) -> Tuple:
        # Primary: trust score (descending)
        # Secondary: published date (descending, present first)
        # Tertiary: title (ascending)
        # Fallback: URL (ascending)
        return (
            -source.score,  # Negative for descending
            0 if source.published_at else 1,  # Present dates first
            -(int(source.published_at[:4]) if source.published_at else 9999),  # Newer first
            source.title.lower() if source.title else "",
            source.url.lower(),
        )

    deduped = list(seen_urls.values())
    deduped.sort(key=sort_key)

    return deduped


def extract_llm_citations(answer: str) -> List[Tuple[int, str]]:
    """
    Extract citation markers from LLM answer.

    Returns list of (position, marker) tuples.
    Supports:
    - [1], [2] numeric references
    - (source: 1) style
    - Sources: [1][2] style
    """
    citations = []

    # Pattern for [1], [2] style
    for match in re.finditer(r'\[(\d+)\]', answer):
        position = match.start()
        number = int(match.group(1))
        citations.append((position, f"[{number}]", number))

    # Pattern for (source: 1) style
    for match in re.finditer(r'\(source:\s*(\d+)\)', answer, re.IGNORECASE):
        position = match.start()
        number = int(match.group(1))
        citations.append((position, f"(source: {number})", number))

    # Pattern for source references in text
    for match in re.finditer(r'sources?:\s*\[([\d\s,]+)\]', answer, re.IGNORECASE):
        position = match.start()
        numbers = [int(n) for n in re.findall(r'\d+', match.group(1))]
        for number in numbers:
            citations.append((position, f"source reference {number}", number))

    # Sort by position
    citations.sort(key=lambda x: x[0])

    return citations


def rewrite_citations_in_answer(
    answer: str,
    sources: List[ResearchSource],
    old_to_new_mapping: Dict[int, int],
) -> str:
    """
    Rewrite citation markers in answer to match canonical numbering.

    Args:
        answer: LLM-generated answer with [n] markers
        sources: Canonicalized source list (new order)
        old_to_new_mapping: Map from old citation numbers to new indices

    Returns:
        Answer with rewritten [n] markers
    """
    if not old_to_new_mapping:
        # No mapping provided, try to infer from existing markers
        existing_numbers = set(int(m.group(1)) for m in re.finditer(r'\[(\d+)\]', answer))
        old_to_new_mapping = {old: idx + 1 for idx, old in enumerate(sorted(existing_numbers))}

    # Replace each citation marker
    result = answer

    # Replace [1], [2] style
    def replace_numeric(match):
        old_num = int(match.group(1))
        new_num = old_to_new_mapping.get(old_num, old_num)
        return f"[{new_num}]"

    result = re.sub(r'\[(\d+)\]', replace_numeric, result)

    # Replace (source: 1) style
    def replace_source_style(match):
        old_num = int(match.group(1))
        new_num = old_to_new_mapping.get(old_num, old_num)
        return f"[{new_num}]"

    result = re.sub(r'\(source:\s*(\d+)\)', replace_source_style, result, flags=re.IGNORECASE)

    return result


def canonicalize_citations(
    answer: str,
    sources: List[ResearchSource],
    trust_scores: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Full canonicalization pipeline.

    1. Normalize and deduplicate sources
    2. Assign stable [n] IDs
    3. Rewrite answer to use canonical IDs
    4. Return canonical citation list

    Returns:
        {
            "answer": str,  # Rewritten answer
            "sources": List[ResearchSource],  # Canonicalized sources
            "citations": List[CanonicalCitation],  # Structured citations
            "mapping": Dict[int, int],  # old_id -> new_id mapping
            "duplicates_removed": int,
        }
    """
    original_count = len(sources)

    # Step 1: Normalize and deduplicate
    normalized_sources = normalize_sources(sources, trust_scores)
    duplicates_removed = original_count - len(normalized_sources)

    # Step 2: Build citation list with stable IDs
    canonical_citations = []
    for idx, source in enumerate(normalized_sources, start=1):
        canonical_citations.append(CanonicalCitation(
            index=idx,
            title=source.title,
            url=source.url,
            original_url=source.url,
            domain=source.domain or urlparse(source.url).netloc,
            snippet=source.snippet,
            published_at=source.published_at,
            trust_score=source.score or 0.5,
            confidence=1.0,
        ))

    # Step 3: Create mapping from old positions to new IDs
    # Try to map based on URL similarity
    old_to_new_mapping = {}
    url_to_new_id = {source.url: idx for idx, source in enumerate(normalized_sources, start=1)}

    for old_idx, old_source in enumerate(sources, start=1):
        old_url_normalized = normalize_url(old_source.url)
        if old_url_normalized in url_to_new_id:
            old_to_new_mapping[old_idx] = url_to_new_id[old_url_normalized]
        else:
            # Keep original position as fallback
            old_to_new_mapping[old_idx] = old_idx

    # Step 4: Rewrite answer
    rewritten_answer = rewrite_citations_in_answer(answer, normalized_sources, old_to_new_mapping)

    return {
        "answer": rewritten_answer,
        "sources": normalized_sources,
        "citations": canonical_citations,
        "mapping": old_to_new_mapping,
        "duplicates_removed": duplicates_removed,
    }


def format_citations_markdown(sources: List[ResearchSource]) -> str:
    """
    Format canonicalized citations as markdown.

    Uses stable order and normalized URLs.
    """
    if not sources:
        return ""

    lines = ["\n\n**Sources:**"]
    for idx, source in enumerate(sources, start=1):
        domain = source.domain or urlparse(source.url).netloc
        published = f" ({source.published_at})" if source.published_at else ""
        lines.append(f"{idx}. [{source.title}]({source.url}){published}")

    return "\n".join(lines)


def validate_citation_format(answer: str, sources: List[ResearchSource]) -> Dict[str, Any]:
    """
    Validate that answer follows canonical citation format.

    Returns:
        {
            "is_valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "citation_count": int,
            "expected_count": int,
        }
    """
    errors = []
    warnings = []

    # Check for citation markers
    markers = list(re.finditer(r'\[(\d+)\]', answer))
    citation_count = len(markers)

    # Extract citation numbers
    cited_numbers = set(int(m.group(1)) for m in markers)

    # Check that citations are sequential starting from 1
    if cited_numbers:
        max_cited = max(cited_numbers)
        expected_range = set(range(1, max_cited + 1))
        missing = expected_range - cited_numbers
        if missing:
            warnings.append(f"Missing citation numbers: {sorted(missing)}")

    # Check that all cited numbers have corresponding sources
    expected_count = len(sources)
    if cited_numbers and max(cited_numbers) > expected_count:
        errors.append(f"Citation [{max(cited_numbers)}] exceeds source count ({expected_count})")

    # Check for non-canonical formats
    if re.search(r'\(source:\s*\d+\)', answer, re.IGNORECASE):
        warnings.append("Non-canonical citation format: (source: N) - use [N]")

    if re.search(r'\(\d+\)', answer):
        warnings.append("Non-canonical citation format: (N) - use [N]")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "citation_count": citation_count,
        "expected_count": expected_count,
    }


