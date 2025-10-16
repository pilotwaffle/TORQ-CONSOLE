"""
Confidence Scorer

Calculates confidence scores for search results and extracted content based on:
- Source reliability
- Content quality
- Freshness
- Citation count
- Consistency across sources
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlparse


@dataclass
class ConfidenceScore:
    """Container for confidence scoring results."""
    overall_score: float  # 0.0 to 1.0
    source_reliability: float  # 0.0 to 1.0
    content_quality: float  # 0.0 to 1.0
    freshness: float  # 0.0 to 1.0
    citation_score: float  # 0.0 to 1.0
    consistency_score: float  # 0.0 to 1.0

    # Detailed breakdown
    factors: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    # Confidence level
    level: str = field(init=False)  # 'high', 'medium', 'low'

    def __post_init__(self):
        """Calculate confidence level based on overall score."""
        if self.overall_score >= 0.75:
            self.level = 'high'
        elif self.overall_score >= 0.50:
            self.level = 'medium'
        else:
            self.level = 'low'


class ConfidenceScorer:
    """
    Calculate confidence scores for search results and content.

    Scoring factors:
    1. Source Reliability (30%) - Based on domain authority and known sources
    2. Content Quality (25%) - Based on content structure, length, metadata
    3. Freshness (15%) - Based on publication date
    4. Citation Score (15%) - Based on number of citations/references
    5. Consistency (15%) - Based on consistency across multiple sources
    """

    # Trusted domains with high reliability scores
    TRUSTED_DOMAINS = {
        # Academic
        'arxiv.org': 0.95,
        'nature.com': 0.98,
        'science.org': 0.98,
        'ieee.org': 0.95,
        'acm.org': 0.95,
        'scholar.google.com': 0.90,

        # News
        'reuters.com': 0.92,
        'apnews.com': 0.92,
        'bbc.com': 0.90,
        'nytimes.com': 0.88,
        'wsj.com': 0.88,
        'theguardian.com': 0.87,

        # Tech
        'techcrunch.com': 0.85,
        'wired.com': 0.85,
        'arstechnica.com': 0.87,
        'theverge.com': 0.83,

        # Developer/Tech Documentation
        'github.com': 0.90,
        'stackoverflow.com': 0.88,
        'developer.mozilla.org': 0.95,
        'docs.python.org': 0.95,

        # Social/Community (lower baseline)
        'reddit.com': 0.60,
        'news.ycombinator.com': 0.75,
        'medium.com': 0.65,

        # Wikipedia
        'wikipedia.org': 0.80
    }

    # Domain suffixes that indicate reliability
    RELIABLE_SUFFIXES = {
        '.edu': 0.85,  # Educational institutions
        '.gov': 0.90,  # Government sites
        '.org': 0.75   # Organizations (baseline)
    }

    def __init__(self):
        """Initialize the confidence scorer."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("[CONFIDENCE_SCORER] Confidence scorer initialized")

    def score_result(
        self,
        url: str,
        title: str = "",
        content: str = "",
        date_published: Optional[str] = None,
        author: Optional[str] = None,
        citations: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConfidenceScore:
        """
        Calculate confidence score for a single result.

        Args:
            url: Source URL
            title: Content title
            content: Main content text
            date_published: Publication date (ISO format)
            author: Author name
            citations: Number of citations/references
            metadata: Additional metadata

        Returns:
            ConfidenceScore object
        """
        metadata = metadata or {}
        warnings = []

        # 1. Source Reliability (30%)
        source_score = self._score_source_reliability(url, author, metadata, warnings)

        # 2. Content Quality (25%)
        quality_score = self._score_content_quality(title, content, metadata, warnings)

        # 3. Freshness (15%)
        freshness_score = self._score_freshness(date_published, warnings)

        # 4. Citation Score (15%)
        citation_score = self._score_citations(citations, metadata)

        # 5. Consistency (15%) - Can only be calculated across multiple sources
        consistency_score = 0.75  # Default neutral score for single result

        # Calculate overall score (weighted average)
        overall_score = (
            source_score * 0.30 +
            quality_score * 0.25 +
            freshness_score * 0.15 +
            citation_score * 0.15 +
            consistency_score * 0.15
        )

        return ConfidenceScore(
            overall_score=round(overall_score, 3),
            source_reliability=round(source_score, 3),
            content_quality=round(quality_score, 3),
            freshness=round(freshness_score, 3),
            citation_score=round(citation_score, 3),
            consistency_score=round(consistency_score, 3),
            factors={
                'url': url,
                'has_author': bool(author),
                'has_date': bool(date_published),
                'citation_count': citations,
                'word_count': len(content.split()) if content else 0
            },
            warnings=warnings
        )

    def score_multiple_results(
        self,
        results: List[Dict[str, Any]]
    ) -> List[ConfidenceScore]:
        """
        Score multiple results and calculate consistency across them.

        Args:
            results: List of result dictionaries

        Returns:
            List of ConfidenceScore objects
        """
        if not results:
            return []

        # Score each result individually first
        scores = []
        for result in results:
            score = self.score_result(
                url=result.get('url', ''),
                title=result.get('title', ''),
                content=result.get('content', ''),
                date_published=result.get('date_published'),
                author=result.get('author'),
                citations=result.get('citations', 0),
                metadata=result.get('metadata', {})
            )
            scores.append(score)

        # Calculate consistency across results
        consistency_score = self._calculate_cross_source_consistency(results)

        # Update consistency scores
        for score in scores:
            score.consistency_score = round(consistency_score, 3)
            # Recalculate overall score with updated consistency
            score.overall_score = round((
                score.source_reliability * 0.30 +
                score.content_quality * 0.25 +
                score.freshness * 0.15 +
                score.citation_score * 0.15 +
                score.consistency_score * 0.15
            ), 3)
            # Update level
            if score.overall_score >= 0.75:
                score.level = 'high'
            elif score.overall_score >= 0.50:
                score.level = 'medium'
            else:
                score.level = 'low'

        return scores

    def _score_source_reliability(
        self,
        url: str,
        author: Optional[str],
        metadata: Dict[str, Any],
        warnings: List[str]
    ) -> float:
        """Score source reliability based on domain and author."""
        try:
            domain = urlparse(url).netloc.lower()
            domain = domain.replace('www.', '')

            # Check trusted domains
            if domain in self.TRUSTED_DOMAINS:
                base_score = self.TRUSTED_DOMAINS[domain]
            else:
                # Check domain suffix
                base_score = 0.50  # Default for unknown domains
                for suffix, score in self.RELIABLE_SUFFIXES.items():
                    if domain.endswith(suffix):
                        base_score = score
                        break

            # Boost for having author
            if author:
                base_score = min(1.0, base_score + 0.05)

            # Penalty for suspicious domains
            if any(keyword in domain for keyword in ['blogspot', 'wordpress.com', 'tumblr']):
                base_score *= 0.85
                warnings.append("Personal blog domain - lower reliability")

            return min(1.0, base_score)

        except Exception as e:
            self.logger.warning(f"[CONFIDENCE_SCORER] Error scoring source: {e}")
            return 0.50

    def _score_content_quality(
        self,
        title: str,
        content: str,
        metadata: Dict[str, Any],
        warnings: List[str]
    ) -> float:
        """Score content quality based on structure and completeness."""
        score = 0.0

        # Title quality (0.3 points)
        if title:
            if len(title) > 10 and len(title) < 200:
                score += 0.3
            elif title:
                score += 0.15
                warnings.append("Title length unusual")

        # Content length (0.4 points)
        word_count = len(content.split()) if content else 0
        if word_count > 500:
            score += 0.4
        elif word_count > 200:
            score += 0.3
        elif word_count > 50:
            score += 0.15
        else:
            warnings.append("Very short content")

        # Metadata completeness (0.3 points)
        metadata_score = 0.0
        if metadata.get('description'):
            metadata_score += 0.1
        if metadata.get('keywords'):
            metadata_score += 0.1
        if metadata.get('author'):
            metadata_score += 0.1

        score += metadata_score

        return min(1.0, score)

    def _score_freshness(
        self,
        date_published: Optional[str],
        warnings: List[str]
    ) -> float:
        """Score freshness based on publication date."""
        if not date_published:
            warnings.append("No publication date available")
            return 0.50  # Neutral score if no date

        try:
            # Parse date (try multiple formats)
            from dateutil import parser
            pub_date = parser.parse(date_published)

            # Calculate age in days
            age_days = (datetime.now() - pub_date).days

            # Score based on age
            if age_days < 0:
                warnings.append("Future publication date detected")
                return 0.30
            elif age_days <= 7:
                return 1.0  # Very fresh (< 1 week)
            elif age_days <= 30:
                return 0.90  # Fresh (< 1 month)
            elif age_days <= 90:
                return 0.75  # Recent (< 3 months)
            elif age_days <= 365:
                return 0.60  # This year
            elif age_days <= 730:
                return 0.45  # Last 2 years
            else:
                warnings.append(f"Content is {age_days // 365} years old")
                return max(0.20, 1.0 - (age_days / 3650))  # Decay over 10 years

        except:
            warnings.append("Could not parse publication date")
            return 0.50

    def _score_citations(
        self,
        citation_count: int,
        metadata: Dict[str, Any]
    ) -> float:
        """Score based on citation/reference count."""
        if citation_count == 0:
            # Check metadata for references
            if 'references' in metadata or 'bibliography' in metadata:
                citation_count = len(metadata.get('references', []))

        # Score based on citation count (logarithmic scale)
        if citation_count >= 100:
            return 1.0
        elif citation_count >= 50:
            return 0.90
        elif citation_count >= 20:
            return 0.80
        elif citation_count >= 10:
            return 0.70
        elif citation_count >= 5:
            return 0.60
        elif citation_count >= 1:
            return 0.50
        else:
            return 0.40  # No citations

    def _calculate_cross_source_consistency(
        self,
        results: List[Dict[str, Any]]
    ) -> float:
        """Calculate consistency score across multiple sources."""
        if len(results) < 2:
            return 0.75  # Neutral score for single source

        # Simple consistency: More sources = higher confidence
        # In a real implementation, this would use NLP to compare content similarity

        source_count = len(results)

        if source_count >= 10:
            return 0.95
        elif source_count >= 5:
            return 0.85
        elif source_count >= 3:
            return 0.75
        else:
            return 0.65

    def aggregate_scores(self, scores: List[ConfidenceScore]) -> ConfidenceScore:
        """
        Aggregate multiple confidence scores into a single summary score.

        Args:
            scores: List of ConfidenceScore objects

        Returns:
            Aggregated ConfidenceScore
        """
        if not scores:
            return ConfidenceScore(
                overall_score=0.0,
                source_reliability=0.0,
                content_quality=0.0,
                freshness=0.0,
                citation_score=0.0,
                consistency_score=0.0
            )

        # Calculate averages
        avg_overall = sum(s.overall_score for s in scores) / len(scores)
        avg_source = sum(s.source_reliability for s in scores) / len(scores)
        avg_quality = sum(s.content_quality for s in scores) / len(scores)
        avg_freshness = sum(s.freshness for s in scores) / len(scores)
        avg_citation = sum(s.citation_score for s in scores) / len(scores)
        avg_consistency = sum(s.consistency_score for s in scores) / len(scores)

        # Collect all warnings
        all_warnings = []
        for score in scores:
            all_warnings.extend(score.warnings)

        return ConfidenceScore(
            overall_score=round(avg_overall, 3),
            source_reliability=round(avg_source, 3),
            content_quality=round(avg_quality, 3),
            freshness=round(avg_freshness, 3),
            citation_score=round(avg_citation, 3),
            consistency_score=round(avg_consistency, 3),
            factors={'source_count': len(scores)},
            warnings=list(set(all_warnings))  # Unique warnings
        )
