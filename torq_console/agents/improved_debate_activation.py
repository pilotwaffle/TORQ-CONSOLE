"""
Improved Multi-Agent Debate Activation System.

Implements research-based activation strategies:
- Keyword-based triggers (comparison, decision, analysis)
- Query complexity classification
- Intent detection (debate-worthy vs simple queries)
- Sequential/parallel protocol selection
- Judge/voting system integration

Based on latest multi-agent debate research:
- Sequential protocols for iterative refinement
- Parallel protocols for diverse perspectives
- Judge systems for solution selection
- Reasoning chain audit and critique
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DebateProtocol(Enum):
    """Debate protocol types."""
    NONE = "none"  # No debate needed
    SEQUENTIAL = "sequential"  # Iterative refinement
    PARALLEL = "parallel"  # Diverse perspectives
    JUDGE = "judge"  # With judge/voting
    CRITIQUE = "critique"  # Reasoning chain audit


@dataclass
class DebateActivationDecision:
    """Decision about whether to activate debate."""
    should_activate: bool
    protocol: DebateProtocol
    confidence: float  # 0-1
    reasoning: str
    query_complexity: float  # 0-1
    debate_worthiness: float  # 0-1


class ImprovedDebateActivation:
    """
    Improved debate activation with research-based triggers.

    Features:
    - Keyword-based activation (comparison, decision, analysis)
    - Query complexity assessment
    - Intent classification
    - Protocol selection (sequential vs parallel vs judge)
    - Confidence scoring
    """

    def __init__(self):
        self.logger = logging.getLogger('ImprovedDebateActivation')

        # Keyword categories
        self.comparison_keywords = [
            'vs', 'versus', 'compare', 'comparison', 'better', 'best', 'worse', 'worst',
            'advantage', 'disadvantage', 'pros', 'cons', 'trade-off', 'tradeoff',
            'difference', 'similar', 'alternatively', 'instead'
        ]

        self.decision_keywords = [
            'should', 'would', 'could', 'is it', 'what if', 'which', 'choose',
            'decide', 'recommend', 'suggest', 'advise', 'option', 'alternative',
            'whether', 'when to', 'how to decide', 'worth it'
        ]

        self.analysis_keywords = [
            'analyze', 'analysis', 'evaluate', 'assessment', 'review', 'examine',
            'investigate', 'explore', 'consider', 'think about', 'opinion',
            'perspective', 'viewpoint', 'approach', 'strategy'
        ]

        self.reasoning_keywords = [
            'why', 'because', 'reason', 'rationale', 'justify', 'explain',
            'understand', 'logic', 'argument', 'case for', 'case against'
        ]

        # Debate-worthy patterns
        self.debate_patterns = [
            'what are the',
            'how do i',
            'best way to',
            'should i use',
            'is it better',
            'what\'s better',
            'which is',
            'pros and cons',
            'advantages and disadvantages'
        ]

        self.logger.info("Improved Debate Activation initialized")

    async def should_activate_debate(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DebateActivationDecision:
        """
        Determine if multi-agent debate should be activated.

        Args:
            query: User query
            context: Optional context (previous conversation, etc.)

        Returns:
            DebateActivationDecision with activation decision and protocol
        """
        query_lower = query.lower()

        # Calculate query features
        word_count = len(query.split())
        has_comparison = any(kw in query_lower for kw in self.comparison_keywords)
        has_decision = any(kw in query_lower for kw in self.decision_keywords)
        has_analysis = any(kw in query_lower for kw in self.analysis_keywords)
        has_reasoning = any(kw in query_lower for kw in self.reasoning_keywords)
        has_debate_pattern = any(pattern in query_lower for pattern in self.debate_patterns)

        # Check for questions
        is_question = '?' in query

        # Calculate complexity
        complexity = self._calculate_complexity(
            word_count, has_comparison, has_decision, has_analysis,
            has_reasoning, has_debate_pattern, is_question
        )

        # Calculate debate worthiness
        worthiness = self._calculate_worthiness(
            has_comparison, has_decision, has_analysis, has_reasoning,
            has_debate_pattern, is_question, word_count
        )

        # Decide activation
        should_activate = worthiness >= 0.5  # Lower threshold than before

        if not should_activate:
            return DebateActivationDecision(
                should_activate=False,
                protocol=DebateProtocol.NONE,
                confidence=1.0 - worthiness,
                reasoning="Query is straightforward and doesn't benefit from debate",
                query_complexity=complexity,
                debate_worthiness=worthiness
            )

        # Select protocol
        protocol = self._select_protocol(
            has_comparison, has_decision, has_analysis,
            has_reasoning, complexity
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            protocol, has_comparison, has_decision, has_analysis,
            has_reasoning, has_debate_pattern
        )

        return DebateActivationDecision(
            should_activate=True,
            protocol=protocol,
            confidence=worthiness,
            reasoning=reasoning,
            query_complexity=complexity,
            debate_worthiness=worthiness
        )

    def _calculate_complexity(
        self,
        word_count: int,
        has_comparison: bool,
        has_decision: bool,
        has_analysis: bool,
        has_reasoning: bool,
        has_debate_pattern: bool,
        is_question: bool
    ) -> float:
        """Calculate query complexity (0-1)."""
        complexity = 0.0

        # Word count contribution (0-0.3)
        if word_count > 20:
            complexity += 0.3
        elif word_count > 12:
            complexity += 0.2
        elif word_count > 8:
            complexity += 0.1

        # Keyword contributions (0.1 each)
        if has_comparison:
            complexity += 0.15
        if has_decision:
            complexity += 0.15
        if has_analysis:
            complexity += 0.15
        if has_reasoning:
            complexity += 0.10

        # Pattern and question (0.05 each)
        if has_debate_pattern:
            complexity += 0.10
        if is_question:
            complexity += 0.05

        return min(complexity, 1.0)

    def _calculate_worthiness(
        self,
        has_comparison: bool,
        has_decision: bool,
        has_analysis: bool,
        has_reasoning: bool,
        has_debate_pattern: bool,
        is_question: bool,
        word_count: int
    ) -> float:
        """Calculate debate worthiness (0-1)."""
        worthiness = 0.0

        # Strong indicators (higher weights for clear debate signals)
        if has_comparison:
            worthiness += 0.35  # Increased from 0.3
        if has_decision:
            worthiness += 0.30  # Increased from 0.25

        # Medium indicators (0.15 each)
        if has_analysis:
            worthiness += 0.15
        if has_reasoning:
            worthiness += 0.15

        # Weak indicators
        if has_debate_pattern:
            worthiness += 0.10
        if is_question:
            worthiness += 0.10  # Increased from 0.05

        # Length bonus (debate needs substance)
        if word_count >= 8:
            worthiness += 0.15  # Increased from 0.1
        elif word_count >= 6:
            worthiness += 0.10  # Increased from 0.05

        return min(worthiness, 1.0)

    def _select_protocol(
        self,
        has_comparison: bool,
        has_decision: bool,
        has_analysis: bool,
        has_reasoning: bool,
        complexity: float
    ) -> DebateProtocol:
        """Select appropriate debate protocol."""
        # High complexity + comparison -> Judge system
        if complexity > 0.7 and has_comparison:
            return DebateProtocol.JUDGE

        # Decision queries -> Sequential refinement
        if has_decision:
            return DebateProtocol.SEQUENTIAL

        # Analysis queries -> Parallel perspectives
        if has_analysis:
            return DebateProtocol.PARALLEL

        # Reasoning queries -> Critique protocol
        if has_reasoning:
            return DebateProtocol.CRITIQUE

        # Default: sequential for iterative improvement
        return DebateProtocol.SEQUENTIAL

    def _generate_reasoning(
        self,
        protocol: DebateProtocol,
        has_comparison: bool,
        has_decision: bool,
        has_analysis: bool,
        has_reasoning: bool,
        has_debate_pattern: bool
    ) -> str:
        """Generate explanation for activation decision."""
        reasons = []

        if has_comparison:
            reasons.append("comparison of alternatives")
        if has_decision:
            reasons.append("decision-making required")
        if has_analysis:
            reasons.append("analytical evaluation needed")
        if has_reasoning:
            reasons.append("reasoning and justification")
        if has_debate_pattern:
            reasons.append("debate-worthy pattern detected")

        if not reasons:
            return f"Complex query benefits from {protocol.value} debate"

        return f"{protocol.value.capitalize()} debate activated for: {', '.join(reasons)}"

    def get_activation_stats(self) -> Dict[str, Any]:
        """Get activation statistics."""
        # TODO: Track activation history for statistics
        return {
            "comparison_keywords": len(self.comparison_keywords),
            "decision_keywords": len(self.decision_keywords),
            "analysis_keywords": len(self.analysis_keywords),
            "reasoning_keywords": len(self.reasoning_keywords),
            "debate_patterns": len(self.debate_patterns),
            "activation_threshold": 0.5
        }


# Global instance
_improved_debate_activation: Optional[ImprovedDebateActivation] = None


def get_improved_debate_activation() -> ImprovedDebateActivation:
    """Get or create global improved debate activation."""
    global _improved_debate_activation

    if _improved_debate_activation is None:
        _improved_debate_activation = ImprovedDebateActivation()

    return _improved_debate_activation
