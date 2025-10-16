"""
Multi-Document Synthesizer

Synthesizes content from multiple sources with proper citations and confidence tracking.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter


@dataclass
class CitedStatement:
    """A statement with its source citations."""
    text: str
    sources: List[str]  # URLs of sources
    confidence: float  # 0.0 to 1.0


@dataclass
class SynthesisResult:
    """Result of multi-document synthesis."""
    summary: str
    key_insights: List[CitedStatement]
    topics: List[str]
    sources_used: List[Dict[str, Any]]

    # Quality metrics
    overall_confidence: float  # 0.0 to 1.0
    source_diversity: float  # 0.0 to 1.0 (how diverse the sources are)
    consensus_level: float  # 0.0 to 1.0 (how much sources agree)

    # Additional data
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    consensus_points: List[CitedStatement] = field(default_factory=list)
    word_count: int = 0

    # Metadata
    synthesized_at: str = field(default_factory=lambda: datetime.now().isoformat())
    synthesis_method: str = "extractive"

    metadata: Dict[str, Any] = field(default_factory=dict)


class MultiDocumentSynthesizer:
    """
    Synthesize content from multiple documents with citations.

    Features:
    - Extractive summarization (key sentences from sources)
    - Citation tracking
    - Consensus detection
    - Contradiction identification
    - Confidence scoring
    """

    def __init__(self):
        """Initialize the synthesizer."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("[SYNTHESIZER] Multi-document synthesizer initialized")

    async def synthesize(
        self,
        documents: List[Dict[str, Any]],
        query: str = "",
        max_length: int = 500,
        focus_areas: Optional[List[str]] = None
    ) -> SynthesisResult:
        """
        Synthesize multiple documents into a coherent summary.

        Args:
            documents: List of document dictionaries (from ContentExtractor)
            query: Original search query for context
            max_length: Maximum length of summary in words
            focus_areas: Specific areas to focus on (e.g., ['methods', 'results'])

        Returns:
            SynthesisResult with synthesized content
        """
        try:
            if not documents:
                return self._empty_synthesis()

            self.logger.info(f"[SYNTHESIZER] Synthesizing {len(documents)} documents")

            # Extract key information from each document
            all_sentences = []
            all_topics = []
            sources_used = []

            for doc in documents:
                content = doc.get('content', doc.get('main_content', ''))
                url = doc.get('url', '')
                title = doc.get('title', 'Untitled')

                if not content:
                    continue

                # Extract sentences
                sentences = self._extract_sentences(content)
                all_sentences.extend([
                    {'text': s, 'source': url, 'title': title}
                    for s in sentences
                ])

                # Extract topics/keywords
                topics = self._extract_topics(content, doc.get('keywords', []))
                all_topics.extend(topics)

                # Track source
                sources_used.append({
                    'url': url,
                    'title': title,
                    'relevance': 1.0,  # TODO: Calculate actual relevance
                    'word_count': len(content.split())
                })

            # Rank and select important sentences
            important_sentences = self._rank_sentences(
                all_sentences,
                query,
                max_sentences=15
            )

            # Group sentences by topic/source
            key_insights = self._group_insights(important_sentences)

            # Create summary
            summary = self._create_summary(important_sentences, max_length)

            # Identify most common topics
            topic_counts = Counter(all_topics)
            top_topics = [topic for topic, count in topic_counts.most_common(10)]

            # Calculate consensus
            consensus_points = self._find_consensus(all_sentences)

            # Detect contradictions
            contradictions = self._detect_contradictions(all_sentences)

            # Calculate metrics
            overall_confidence = self._calculate_confidence(documents, important_sentences)
            source_diversity = self._calculate_diversity(sources_used)
            consensus_level = self._calculate_consensus(all_sentences)

            return SynthesisResult(
                summary=summary,
                key_insights=key_insights[:10],  # Top 10 insights
                topics=top_topics,
                sources_used=sources_used,
                overall_confidence=overall_confidence,
                source_diversity=source_diversity,
                consensus_level=consensus_level,
                contradictions=contradictions,
                consensus_points=consensus_points[:5],  # Top 5 consensus points
                word_count=len(summary.split()),
                synthesis_method="extractive"
            )

        except Exception as e:
            self.logger.error(f"[SYNTHESIZER] Error synthesizing documents: {e}")
            return self._empty_synthesis()

    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        # Simple sentence splitting (could be enhanced with NLTK)
        import re

        # Split on sentence boundaries
        sentences = re.split(r'[.!?]+\s+', text)

        # Clean and filter
        sentences = [
            s.strip()
            for s in sentences
            if len(s.strip()) > 20 and len(s.strip()) < 300
        ]

        return sentences

    def _extract_topics(self, text: str, keywords: List[str]) -> List[str]:
        """Extract topics from text."""
        topics = []

        # Use provided keywords
        topics.extend(keywords)

        # Simple topic extraction using capitalized words and common tech terms
        import re
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        topics.extend(words)

        # Common technical terms
        tech_terms = [
            'AI', 'ML', 'algorithm', 'data', 'model', 'system', 'network',
            'learning', 'neural', 'quantum', 'cloud', 'API', 'software'
        ]

        for term in tech_terms:
            if term.lower() in text.lower():
                topics.append(term)

        return topics

    def _rank_sentences(
        self,
        sentences: List[Dict[str, Any]],
        query: str,
        max_sentences: int = 15
    ) -> List[Dict[str, Any]]:
        """Rank sentences by importance."""
        # Score each sentence
        for sent_info in sentences:
            score = 0.0
            text = sent_info['text'].lower()

            # Boost for query terms
            if query:
                query_terms = query.lower().split()
                for term in query_terms:
                    if term in text:
                        score += 2.0

            # Boost for sentence position (first sentences often important)
            score += 1.0

            # Boost for sentence length (not too short, not too long)
            word_count = len(text.split())
            if 15 <= word_count <= 50:
                score += 1.0

            # Boost for containing numbers or data
            if any(char.isdigit() for char in text):
                score += 0.5

            # Boost for containing key phrases
            key_phrases = ['research shows', 'study found', 'according to', 'results indicate']
            if any(phrase in text for phrase in key_phrases):
                score += 1.0

            sent_info['score'] = score

        # Sort by score and return top N
        sentences.sort(key=lambda x: x['score'], reverse=True)
        return sentences[:max_sentences]

    def _group_insights(self, sentences: List[Dict[str, Any]]) -> List[CitedStatement]:
        """Group sentences into insights with citations."""
        insights = []

        # Group sentences by similar topics or sources
        # For simplicity, we'll just create one insight per sentence with citation
        for sent_info in sentences:
            insights.append(CitedStatement(
                text=sent_info['text'],
                sources=[sent_info['source']],
                confidence=0.75  # Default confidence
            ))

        return insights

    def _create_summary(self, sentences: List[Dict[str, Any]], max_length: int) -> str:
        """Create a coherent summary from selected sentences."""
        summary_sentences = []
        current_length = 0

        for sent_info in sentences:
            sent_length = len(sent_info['text'].split())
            if current_length + sent_length <= max_length:
                summary_sentences.append(sent_info['text'])
                current_length += sent_length
            else:
                break

        return ' '.join(summary_sentences)

    def _find_consensus(self, sentences: List[Dict[str, Any]]) -> List[CitedStatement]:
        """Find points of consensus across sources."""
        # Simplified: Look for similar statements from multiple sources
        # In reality, this would use semantic similarity

        consensus = []

        # Group sentences by similar content (very simplified)
        # For now, just return empty list
        # TODO: Implement semantic similarity matching

        return consensus

    def _detect_contradictions(self, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect contradictions between sources."""
        # Simplified: Look for opposing statements
        # In reality, this would use NLP to detect semantic opposition

        contradictions = []

        # Look for contradiction indicators
        contradiction_markers = [
            'however', 'but', 'although', 'contrary', 'unlike',
            'on the other hand', 'in contrast'
        ]

        for sent_info in sentences:
            text = sent_info['text'].lower()
            if any(marker in text for marker in contradiction_markers):
                contradictions.append({
                    'text': sent_info['text'],
                    'source': sent_info['source'],
                    'type': 'potential_contradiction'
                })

        return contradictions[:5]  # Top 5 contradictions

    def _calculate_confidence(
        self,
        documents: List[Dict[str, Any]],
        sentences: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall confidence score."""
        # Based on number of sources and quality
        source_count = len(documents)

        if source_count >= 10:
            return 0.90
        elif source_count >= 5:
            return 0.80
        elif source_count >= 3:
            return 0.70
        else:
            return 0.60

    def _calculate_diversity(self, sources: List[Dict[str, Any]]) -> float:
        """Calculate source diversity."""
        if not sources:
            return 0.0

        # Check domain diversity
        from urllib.parse import urlparse
        domains = set()

        for source in sources:
            url = source.get('url', '')
            if url:
                domain = urlparse(url).netloc
                domains.add(domain)

        # Diversity = unique domains / total sources
        diversity = len(domains) / len(sources) if sources else 0.0
        return min(1.0, diversity * 1.2)  # Slight boost

    def _calculate_consensus(self, sentences: List[Dict[str, Any]]) -> float:
        """Calculate consensus level."""
        # Simplified: More sentences from different sources = higher consensus
        # In reality, would check semantic agreement

        if not sentences:
            return 0.0

        sources = set(s['source'] for s in sentences)

        if len(sources) >= 5:
            return 0.85
        elif len(sources) >= 3:
            return 0.70
        else:
            return 0.55

    def _empty_synthesis(self) -> SynthesisResult:
        """Return empty synthesis result."""
        return SynthesisResult(
            summary="No documents to synthesize.",
            key_insights=[],
            topics=[],
            sources_used=[],
            overall_confidence=0.0,
            source_diversity=0.0,
            consensus_level=0.0
        )
