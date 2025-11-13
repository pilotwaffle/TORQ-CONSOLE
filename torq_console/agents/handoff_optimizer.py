"""
Phase 1: Advanced Handoff Optimization System.

Addresses remaining gaps from initial handoff fixes:
- Memory → Planning: 46% → 85% target
- Overall preservation: 58.9% → 70% target
- Information loss: 40% → <30% target

New features:
1. Semantic context preservation (similarity-based)
2. Increased context limits (2000 chars)
3. Smart context compression (entity preservation)
4. Adaptive handoff parameters
5. Context quality scoring

Phase A.2: Async/await support for integration with async agent system
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import re

# Logger for error handling
logger = logging.getLogger(__name__)


@dataclass
class SemanticContext:
    """Enhanced context with semantic preservation."""
    key_entities: Set[str]
    key_concepts: Set[str]
    relationships: List[tuple]
    importance_scores: Dict[str, float]
    compressed_content: str
    original_length: int
    compression_ratio: float


class EntityExtractor:
    """Extract key entities from text for preservation."""

    def __init__(self):
        # Common entity patterns
        self.tech_terms = {
            'oauth', 'jwt', 'api', 'rest', 'graphql', 'microservices',
            'postgresql', 'mongodb', 'redis', 'kafka', 'docker', 'kubernetes',
            'react', 'vue', 'angular', 'python', 'javascript', 'typescript',
            'aws', 'azure', 'gcp', 'authentication', 'authorization', 'token'
        }

        self.pattern_keywords = {
            'pattern', 'architecture', 'design', 'implementation', 'strategy',
            'algorithm', 'optimization', 'performance', 'security', 'scalability'
        }

    def extract_entities(self, text: str) -> Set[str]:
        """Extract key entities from text."""
        entities = set()

        # Convert to lowercase for matching
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))

        # Extract tech terms
        entities.update(words & self.tech_terms)

        # Extract pattern keywords
        entities.update(words & self.pattern_keywords)

        # Extract capitalized terms (likely proper nouns/technologies)
        capitalized = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
        entities.update(term.lower() for term in capitalized if len(term) > 2)

        # Extract acronyms (2-5 caps)
        acronyms = re.findall(r'\b[A-Z]{2,5}\b', text)
        entities.update(term.lower() for term in acronyms)

        return entities

    def extract_key_concepts(self, text: str) -> Set[str]:
        """Extract key concepts and phrases."""
        concepts = set()

        # Extract common technical phrases (2-3 words)
        text_lower = text.lower()

        # Bigrams
        words = text_lower.split()
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            # Keep if contains tech terms or patterns
            if any(term in bigram for term in self.tech_terms | self.pattern_keywords):
                concepts.add(bigram)

        # Trigrams with common patterns
        for i in range(len(words) - 2):
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            if any(term in trigram for term in self.tech_terms):
                concepts.add(trigram)

        return concepts


class SmartContextCompressor:
    """Intelligently compress context while preserving key information."""

    def __init__(self):
        self.entity_extractor = EntityExtractor()

    def compress_context(
        self,
        content: str,
        target_length: int = 2000,
        preserve_entities: bool = True
    ) -> SemanticContext:
        """
        Compress context intelligently.

        Args:
            content: Original content
            target_length: Target length in characters
            preserve_entities: Whether to preserve key entities

        Returns:
            SemanticContext with compressed content and metadata
        """
        # Phase A.3: Input validation
        if not content:
            logger.warning("compress_context: Empty content provided")
            return SemanticContext(
                key_entities=set(),
                key_concepts=set(),
                relationships=[],
                importance_scores={},
                compressed_content="",
                original_length=0,
                compression_ratio=1.0
            )

        if target_length <= 0:
            logger.error(f"compress_context: Invalid target_length: {target_length}")
            target_length = 2000  # Fallback to default

        try:
            original_length = len(content)

            if original_length <= target_length:
            # No compression needed
            return SemanticContext(
                key_entities=self.entity_extractor.extract_entities(content),
                key_concepts=self.entity_extractor.extract_key_concepts(content),
                relationships=[],
                importance_scores={},
                compressed_content=content,
                original_length=original_length,
                compression_ratio=1.0
            )

        # Extract entities and concepts
        entities = self.entity_extractor.extract_entities(content)
        concepts = self.entity_extractor.extract_key_concepts(content)

        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Score sentences by importance
        sentence_scores = []
        for sentence in sentences:
            score = self._score_sentence(sentence, entities, concepts)
            sentence_scores.append((sentence, score))

        # Sort by importance
        sentence_scores.sort(key=lambda x: x[1], reverse=True)

        # Select sentences until target length
        compressed = []
        current_length = 0

        for sentence, score in sentence_scores:
            sentence_length = len(sentence) + 2  # +2 for punctuation and space
            if current_length + sentence_length <= target_length:
                compressed.append((sentence, score))
                current_length += sentence_length
            elif current_length < target_length * 0.8:  # Fill at least 80%
                # Truncate sentence if needed
                remaining = target_length - current_length - 3  # -3 for "..."
                if remaining > 50:  # Only if meaningful
                    compressed.append((sentence[:remaining] + "...", score))
                    break

            # Reconstruct in original order (approximately)
            compressed_text = ". ".join(sent for sent, _ in compressed) + "."

            # Phase A.3: Safe division with zero check
            compression_ratio = len(compressed_text) / original_length if original_length > 0 else 1.0

            return SemanticContext(
                key_entities=entities,
                key_concepts=concepts,
                relationships=self._extract_relationships(entities, concepts, content),
                importance_scores={sent: score for sent, score in compressed},
                compressed_content=compressed_text,
                original_length=original_length,
                compression_ratio=compression_ratio
            )

        except Exception as e:
            # Phase A.3: Error handling with fallback
            logger.error(f"compress_context failed: {e}", exc_info=True)
            # Return original content (no compression)
            return SemanticContext(
                key_entities=set(),
                key_concepts=set(),
                relationships=[],
                importance_scores={},
                compressed_content=content[:target_length],  # Simple truncation fallback
                original_length=len(content),
                compression_ratio=target_length / len(content) if len(content) > 0 else 1.0
            )

    def _score_sentence(
        self,
        sentence: str,
        entities: Set[str],
        concepts: Set[str]
    ) -> float:
        """Score sentence importance."""
        score = 0.0
        sentence_lower = sentence.lower()

        # Count entity mentions (high value)
        for entity in entities:
            if entity in sentence_lower:
                score += 2.0

        # Count concept mentions (medium value)
        for concept in concepts:
            if concept in sentence_lower:
                score += 1.0

        # Boost for question/imperative sentences
        if '?' in sentence or sentence.strip().startswith(('How', 'What', 'Why', 'When')):
            score += 1.0

        # Boost for technical specifications
        if any(word in sentence_lower for word in ['must', 'should', 'require', 'implement']):
            score += 0.5

        # Normalize by length (avoid favoring long sentences)
        words = len(sentence.split())
        if words > 0:
            score = score / (words ** 0.5)  # Square root to moderate the effect

        return score

    def _extract_relationships(
        self,
        entities: Set[str],
        concepts: Set[str],
        content: str
    ) -> List[tuple]:
        """Extract relationships between entities."""
        relationships = []

        # Simple relationship extraction: entities co-occurring in concepts
        for concept in concepts:
            concept_entities = [e for e in entities if e in concept]
            if len(concept_entities) >= 2:
                # All pairs in this concept are related
                for i, e1 in enumerate(concept_entities):
                    for e2 in concept_entities[i+1:]:
                        relationships.append((e1, e2, concept))

        return relationships


class AdaptiveHandoffOptimizer:
    """
    Adaptive handoff optimization based on query complexity.

    Features:
    - Dynamic context sizing
    - Query complexity analysis
    - Adaptive preservation strategies
    """

    def __init__(self):
        self.compressor = SmartContextCompressor()
        self.entity_extractor = EntityExtractor()

    async def optimize_memory_context_async(
        self,
        memories: List[Dict[str, Any]],
        query: str,
        max_length: int = 2000
    ) -> Dict[str, Any]:
        """
        Async version of optimize_memory_context for use in async agent systems.

        Args:
            memories: List of memory objects
            query: Current query
            max_length: Maximum context length

        Returns:
            Optimized context dictionary
        """
        # Run CPU-bound optimization in thread pool to avoid blocking event loop
        return await asyncio.to_thread(
            self.optimize_memory_context,
            memories,
            query,
            max_length
        )

    def optimize_memory_context(
        self,
        memories: List[Dict[str, Any]],
        query: str,
        max_length: int = 2000
    ) -> Dict[str, Any]:
        """
        Optimize memory context for Memory → Planning handoff.

        Args:
            memories: List of memory objects
            query: Current query
            max_length: Maximum context length

        Returns:
            Optimized context dictionary
        """
        # Phase A.3: Input validation
        if not memories:
            logger.warning("optimize_memory_context: No memories provided")
            return {
                'memories': [],
                'total_length': 0,
                'query_complexity': 0.0,
                'optimization_applied': False,
                'context_utilization': 0.0
            }

        if not query:
            logger.warning("optimize_memory_context: Empty query provided")
            query = ""  # Use empty string for processing

        if max_length <= 0:
            logger.error(f"optimize_memory_context: Invalid max_length: {max_length}")
            max_length = 2000  # Fallback to default

        try:
            # Analyze query complexity
            query_complexity = self._analyze_query_complexity(query)

        # Adjust context size based on complexity
        if query_complexity > 0.7:  # Complex query
            context_length = max_length
        elif query_complexity > 0.4:  # Medium query
            context_length = int(max_length * 0.7)
        else:  # Simple query
            context_length = int(max_length * 0.5)

        # Extract query entities for relevance filtering
        query_entities = self.entity_extractor.extract_entities(query)
        query_concepts = self.entity_extractor.extract_key_concepts(query)

        # Re-rank memories by relevance to query
        ranked_memories = self._rank_memories_by_relevance(
            memories,
            query_entities,
            query_concepts
        )

        # Compress and combine
        optimized_memories = []
        total_length = 0

        for memory in ranked_memories:
            content = memory.get('content', '')

            # Compress if needed
            if total_length + len(content) > context_length:
                remaining = context_length - total_length
                if remaining > 100:  # Only if meaningful space left
                    semantic_ctx = self.compressor.compress_context(content, remaining)
                    optimized_memories.append({
                        'content': semantic_ctx.compressed_content,
                        'entities': semantic_ctx.key_entities,
                        'concepts': semantic_ctx.key_concepts,
                        'compressed': True,
                        'original_length': semantic_ctx.original_length,
                        'compression_ratio': semantic_ctx.compression_ratio
                    })
                    total_length += len(semantic_ctx.compressed_content)
                break
            else:
                # Keep as-is
                optimized_memories.append({
                    'content': content,
                    'entities': self.entity_extractor.extract_entities(content),
                    'concepts': self.entity_extractor.extract_key_concepts(content),
                    'compressed': False
                })
                total_length += len(content)

            # Phase A.3: Safe division for context utilization
            context_utilization = (
                total_length / context_length
                if context_length > 0 else 0.0
            )

            return {
                'memories': optimized_memories,
                'total_length': total_length,
                'query_complexity': query_complexity,
                'optimization_applied': True,
                'context_utilization': context_utilization
            }

        except Exception as e:
            # Phase A.3: Error handling with fallback
            logger.error(f"optimize_memory_context failed: {e}", exc_info=True)
            # Return unoptimized memories as fallback
            return {
                'memories': memories[:5],  # Simple fallback: first 5 memories
                'total_length': sum(len(m.get('content', '')) for m in memories[:5]),
                'query_complexity': 0.5,
                'optimization_applied': False,
                'context_utilization': 0.5,
                'error': str(e)
            }

    def _analyze_query_complexity(self, query: str) -> float:
        """Analyze query complexity (0-1 scale)."""
        complexity_score = 0.0

        # Length-based (longer queries are often more complex)
        words = query.split()
        word_count = len(words)
        if word_count > 30:
            complexity_score += 0.3
        elif word_count > 15:
            complexity_score += 0.2
        elif word_count > 8:
            complexity_score += 0.1

        # Technical term density
        entities = self.entity_extractor.extract_entities(query)
        if word_count > 0:
            tech_density = len(entities) / word_count
            complexity_score += min(tech_density * 0.4, 0.3)

        # Multi-part indicators
        multi_part_keywords = ['and', 'also', 'then', 'additionally', 'furthermore']
        multi_parts = sum(1 for kw in multi_part_keywords if kw in query.lower())
        complexity_score += min(multi_parts * 0.1, 0.2)

        # Complex action verbs
        complex_actions = ['implement', 'design', 'build', 'create', 'develop', 'compare', 'analyze']
        action_count = sum(1 for action in complex_actions if action in query.lower())
        complexity_score += min(action_count * 0.1, 0.2)

        return min(complexity_score, 1.0)

    def _rank_memories_by_relevance(
        self,
        memories: List[Dict[str, Any]],
        query_entities: Set[str],
        query_concepts: Set[str]
    ) -> List[Dict[str, Any]]:
        """Rank memories by relevance to query."""
        scored_memories = []

        for memory in memories:
            content = memory.get('content', '')

            # Extract memory entities/concepts
            mem_entities = self.entity_extractor.extract_entities(content)
            mem_concepts = self.entity_extractor.extract_key_concepts(content)

            # Calculate relevance score
            entity_overlap = len(query_entities & mem_entities)
            concept_overlap = len(query_concepts & mem_concepts)

            relevance = entity_overlap * 2.0 + concept_overlap * 1.0

            # Boost by similarity score if available
            if 'similarity' in memory:
                relevance *= (1.0 + memory['similarity'])

            scored_memories.append((memory, relevance))

        # Sort by relevance
        scored_memories.sort(key=lambda x: x[1], reverse=True)

        return [mem for mem, _ in scored_memories]

    def calculate_preservation_quality(
        self,
        original_content: str,
        preserved_content: str
    ) -> float:
        """
        Calculate quality of information preservation.

        Returns:
            Quality score (0-1)
        """
        # Phase A.3: Input validation
        if not original_content or not preserved_content:
            logger.warning("calculate_preservation_quality: Empty content provided")
            return 0.0 if not preserved_content else 1.0

        try:
            # Extract entities from both
            orig_entities = self.entity_extractor.extract_entities(original_content)
            pres_entities = self.entity_extractor.extract_entities(preserved_content)

            # Extract concepts
            orig_concepts = self.entity_extractor.extract_key_concepts(original_content)
            pres_concepts = self.entity_extractor.extract_key_concepts(preserved_content)

            # Calculate preservation scores with safe division
            entity_preservation = (
                len(pres_entities & orig_entities) / len(orig_entities)
                if orig_entities else 1.0  # Perfect if no entities to preserve
            )
            concept_preservation = (
                len(pres_concepts & orig_concepts) / len(orig_concepts)
                if orig_concepts else 1.0  # Perfect if no concepts to preserve
            )

            # Length ratio (penalize too much compression) with safe division
            length_ratio = (
                len(preserved_content) / len(original_content)
                if len(original_content) > 0 else 1.0
            )
            length_score = min(length_ratio / 0.5, 1.0)  # Target at least 50% of original length

            # Weighted average
            quality = (
                entity_preservation * 0.5 +  # Entities are most important
                concept_preservation * 0.3 +  # Concepts are important
                length_score * 0.2  # Length is less important
            )

            return min(quality, 1.0)

        except Exception as e:
            # Phase A.3: Error handling
            logger.error(f"calculate_preservation_quality failed: {e}", exc_info=True)
            return 0.5  # Default to medium quality on error


# Global optimizer instance
_handoff_optimizer: Optional[AdaptiveHandoffOptimizer] = None


def get_handoff_optimizer() -> AdaptiveHandoffOptimizer:
    """Get or create global handoff optimizer."""
    global _handoff_optimizer
    if _handoff_optimizer is None:
        _handoff_optimizer = AdaptiveHandoffOptimizer()
    return _handoff_optimizer
