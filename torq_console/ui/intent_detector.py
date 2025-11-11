"""
Self-Correcting Intent Detection System with Learning Capability

This module provides intelligent intent detection that learns from mistakes
and self-corrects routing decisions for optimal query handling.
"""

import json
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

# Import advanced learning system
try:
    from .learning_system import get_learning_system
    LEARNING_SYSTEM_AVAILABLE = True
except ImportError:
    LEARNING_SYSTEM_AVAILABLE = False


@dataclass
class IntentPattern:
    """Represents a learned intent pattern"""
    keywords: List[str]
    context_markers: List[str]
    confidence: float
    success_count: int
    failure_count: int
    last_updated: str


@dataclass
class IntentDecision:
    """Represents an intent detection decision"""
    intent_type: str  # 'research', 'content_creation', 'code_generation', 'general'
    confidence: float
    reasoning: str
    matched_patterns: List[str]


class SelfCorrectingIntentDetector:
    """
    Self-correcting intent detector that learns from routing errors and improves over time.

    Features:
    - Context-aware keyword detection
    - Pattern learning from feedback
    - Self-correction when wrong intent detected
    - Persistent learning across sessions
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.storage_path = storage_path or Path.home() / '.torq_console' / 'intent_learning.json'
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize patterns
        self.patterns: Dict[str, IntentPattern] = self._load_patterns()

        # Routing history for self-correction
        self.routing_history: List[Dict] = []

    def _load_patterns(self) -> Dict[str, IntentPattern]:
        """Load learned patterns from storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    return {
                        name: IntentPattern(**pattern_data)
                        for name, pattern_data in data.items()
                    }
            except Exception as e:
                self.logger.error(f"Failed to load intent patterns: {e}")

        # Return default patterns if loading fails or file doesn't exist
        return self._get_default_patterns()

    def _get_default_patterns(self) -> Dict[str, IntentPattern]:
        """Get default intent detection patterns"""
        return {
            'research_crypto': IntentPattern(
                keywords=['price', 'news', 'market', 'sentiment', 'analysis', 'data', 'information'],
                context_markers=['cryptocurrency', 'crypto', 'coin', 'token', 'shib', 'bitcoin', 'ethereum'],
                confidence=0.9,
                success_count=0,
                failure_count=0,
                last_updated=datetime.now().isoformat()
            ),
            'research_general': IntentPattern(
                keywords=['research', 'find', 'search', 'look up', 'information about', 'tell me about'],
                context_markers=['web for', 'online', 'internet', 'latest', 'current', 'recent'],
                confidence=0.85,
                success_count=0,
                failure_count=0,
                last_updated=datetime.now().isoformat()
            ),
            'content_creation': IntentPattern(
                keywords=['write', 'create a post', 'make a post', 'compose', 'draft', 'x.com post', 'tweet'],
                context_markers=['based on', 'using', 'from this', 'about', '150 words', 'summary'],
                confidence=0.9,
                success_count=0,
                failure_count=0,
                last_updated=datetime.now().isoformat()
            ),
            'code_generation': IntentPattern(
                keywords=['build an app', 'create application', 'develop software', 'implement system', 'code a'],
                context_markers=['typescript', 'python', 'nextjs', 'react', 'api', 'database', 'full stack'],
                confidence=0.85,
                success_count=0,
                failure_count=0,
                last_updated=datetime.now().isoformat()
            ),
        }

    def _save_patterns(self):
        """Save learned patterns to storage"""
        try:
            data = {name: asdict(pattern) for name, pattern in self.patterns.items()}
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Intent patterns saved to {self.storage_path}")
        except Exception as e:
            self.logger.error(f"Failed to save intent patterns: {e}")

    def detect_intent(self, query: str, tools: Optional[List[str]] = None) -> IntentDecision:
        """
        Detect the intent of a user query with confidence scoring.

        Args:
            query: The user's query text
            tools: Optional list of explicitly requested tools (e.g., ['web_search'])

        Returns:
            IntentDecision with type, confidence, and reasoning
        """
        query_lower = query.lower().strip()

        self.logger.info(f"[INTENT DETECTION] Analyzing: {query[:100]}...")

        # PRIORITY 1: Explicit tool requests override all other detection
        if tools and 'web_search' in tools:
            self.logger.info("[INTENT] Explicit web_search tool requested -> RESEARCH mode")
            return IntentDecision(
                intent_type='research',
                confidence=1.0,
                reasoning='Explicit web_search tool requested',
                matched_patterns=['explicit_tool_request']
            )

        # PRIORITY 2: Explicit Prince Flowers commands
        if query_lower.startswith('prince '):
            command_part = query_lower[7:].strip()

            # PRIORITY 2.5: Explicit Prince search/research commands
            if command_part.startswith('search') or command_part.startswith('research') or \
               command_part.startswith('find') or command_part.startswith('look up'):
                self.logger.info("[INTENT] Explicit Prince search/research command -> RESEARCH mode")
                return IntentDecision(
                    intent_type='research',
                    confidence=0.98,
                    reasoning='Explicit Prince Flowers search/research command detected',
                    matched_patterns=['prince_explicit_search']
                )

            # PRIORITY 2.6: Explicit Prince content creation commands
            content_triggers = ['create a post', 'write a post', 'make a post', 'compose a post',
                              'create post', 'write post', 'draft a post', 'draft post',
                              'create a tweet', 'write a tweet', 'compose a tweet']
            if any(trigger in command_part for trigger in content_triggers):
                self.logger.info("[INTENT] Explicit Prince content creation command -> CONTENT_CREATION mode")
                return IntentDecision(
                    intent_type='content_creation',
                    confidence=0.98,
                    reasoning='Explicit Prince Flowers content creation command detected',
                    matched_patterns=['prince_explicit_content']
                )

            # PRIORITY 2.7: General Prince search intent (fallback for less explicit commands)
            if any(keyword in command_part for keyword in ['search', 'find', 'research', 'look up']):
                self.logger.info("[INTENT] Prince search command -> RESEARCH mode")
                return IntentDecision(
                    intent_type='research',
                    confidence=0.95,
                    reasoning='Prince Flowers search command',
                    matched_patterns=['prince_search']
                )

        # PRIORITY 3: Pattern-based detection with context awareness
        scores = {}
        matched_patterns = {}

        # Check each pattern type
        for pattern_name, pattern in self.patterns.items():
            score = self._calculate_pattern_score(query_lower, pattern)
            if score > 0.1:  # Minimum threshold (lowered from 0.3 to catch "search" queries)
                scores[pattern_name] = score
                matched_patterns[pattern_name] = self._explain_match(query_lower, pattern)

        # Determine intent type based on highest scoring pattern
        if not scores:
            return IntentDecision(
                intent_type='general',
                confidence=0.5,
                reasoning='No strong pattern matches found',
                matched_patterns=[]
            )

        # Get highest scoring pattern
        best_pattern = max(scores.items(), key=lambda x: x[1])
        pattern_name, confidence = best_pattern

        # Map pattern name to intent type
        if 'research' in pattern_name:
            intent_type = 'research'
        elif 'content_creation' in pattern_name:
            intent_type = 'content_creation'
        elif 'code_generation' in pattern_name:
            intent_type = 'code_generation'
        else:
            intent_type = 'general'

        # ENHANCEMENT: Apply learning system confidence boost
        if LEARNING_SYSTEM_AVAILABLE:
            try:
                learning_system = get_learning_system()
                confidence_boost = learning_system.get_confidence_boost(intent_type, query)
                confidence = min(1.0, max(0.0, confidence + confidence_boost))
                if abs(confidence_boost) > 0.01:
                    self.logger.info(
                        f"[LEARNING BOOST] {intent_type}: {confidence_boost:+.3f} "
                        f"(final confidence: {confidence:.3f})"
                    )
            except Exception as e:
                self.logger.warning(f"Learning system boost failed: {e}")

        # Context-aware adjustments
        intent_type, confidence, reasoning = self._apply_context_rules(
            query_lower, intent_type, confidence, matched_patterns
        )

        decision = IntentDecision(
            intent_type=intent_type,
            confidence=confidence,
            reasoning=reasoning,
            matched_patterns=list(matched_patterns.keys())
        )

        # Log the decision
        self.logger.info(
            f"[INTENT DECISION] Type={decision.intent_type}, "
            f"Confidence={decision.confidence:.2f}, "
            f"Reasoning={decision.reasoning}"
        )

        # Store in history for potential self-correction
        self.routing_history.append({
            'timestamp': datetime.now().isoformat(),
            'query': query[:200],
            'decision': asdict(decision)
        })

        return decision

    def _calculate_pattern_score(self, query: str, pattern: IntentPattern) -> float:
        """Calculate how well a query matches a pattern"""
        score = 0.0

        # Check keyword matches
        keyword_matches = sum(1 for kw in pattern.keywords if kw in query)
        if keyword_matches > 0:
            score += (keyword_matches / len(pattern.keywords)) * 0.6

        # Check context marker matches
        context_matches = sum(1 for cm in pattern.context_markers if cm in query)
        if context_matches > 0:
            score += (context_matches / len(pattern.context_markers)) * 0.4

        # Apply confidence weighting
        score *= pattern.confidence

        # Apply learning weighting (favor patterns with better success rate)
        if pattern.success_count > 0 or pattern.failure_count > 0:
            success_rate = pattern.success_count / (pattern.success_count + pattern.failure_count)
            score *= (0.5 + 0.5 * success_rate)  # Scale between 0.5 and 1.0

        return min(score, 1.0)

    def _explain_match(self, query: str, pattern: IntentPattern) -> str:
        """Explain why a pattern matched"""
        matched_keywords = [kw for kw in pattern.keywords if kw in query]
        matched_contexts = [cm for cm in pattern.context_markers if cm in query]

        parts = []
        if matched_keywords:
            parts.append(f"keywords: {', '.join(matched_keywords[:3])}")
        if matched_contexts:
            parts.append(f"context: {', '.join(matched_contexts[:3])}")

        return '; '.join(parts)

    def _apply_context_rules(
        self,
        query: str,
        intent_type: str,
        confidence: float,
        matched_patterns: Dict[str, str]
    ) -> Tuple[str, float, str]:
        """
        Apply context-aware rules to refine intent detection.

        This is where the self-correction logic lives.
        """

        # RULE 1: "Research X" with crypto context = RESEARCH, not CODE_GENERATION
        if intent_type == 'code_generation':
            crypto_terms = ['cryptocurrency', 'crypto', 'coin', 'token', 'bitcoin', 'ethereum', 'shib', 'price', 'market']
            info_terms = ['research', 'find', 'price', 'news', 'information', 'data', 'analysis']

            has_crypto_context = any(term in query for term in crypto_terms)
            has_info_request = any(term in query for term in info_terms)

            if has_crypto_context and has_info_request:
                self.logger.warning(
                    f"[SELF-CORRECTION] Detected code_generation but crypto+info context present. "
                    f"Correcting to RESEARCH mode."
                )
                return 'research', 0.9, 'Self-corrected: crypto information request, not code generation'

        # RULE 2: "Create/Write post about X" = CONTENT_CREATION, not CODE_GENERATION
        if intent_type == 'code_generation':
            # Enhanced content indicators with more specific patterns
            content_indicators = ['post', 'tweet', 'x.com', '150 words', 'compose', 'draft']
            content_verbs = ['write a', 'create a', 'make a', 'compose a', 'draft a']
            content_nouns = ['post', 'tweet', 'article', 'caption', 'message', 'content']

            # Check for content creation patterns
            has_content_intent = any(ind in query for ind in content_indicators)
            has_content_verb_noun = any(
                verb in query and noun in query
                for verb in content_verbs
                for noun in content_nouns
            )

            if has_content_intent or has_content_verb_noun:
                # Additional check: ensure it's not actually asking for code
                code_indicators = ['application', 'system', 'backend', 'frontend', 'api', 'database', 'service']
                has_code_context = any(ind in query for ind in code_indicators)

                # Only correct to content_creation if no strong code indicators
                if not has_code_context:
                    self.logger.warning(
                        f"[SELF-CORRECTION] Detected code_generation but content creation markers present. "
                        f"Correcting to CONTENT_CREATION mode."
                    )
                    return 'content_creation', 0.9, 'Self-corrected: content creation, not application building'

        # RULE 3: "Build X app" or "Create X application" with tech stack = CODE_GENERATION
        if intent_type in ['research', 'general']:
            build_verbs = ['build', 'develop', 'implement', 'create', 'make']
            app_nouns = ['app', 'application', 'system', 'software', 'platform', 'service']
            tech_terms = ['typescript', 'python', 'nextjs', 'react', 'api', 'database', 'backend', 'frontend']

            has_build_verb = any(verb in query for verb in build_verbs)
            has_app_noun = any(noun in query for noun in app_nouns)
            has_tech_stack = any(tech in query for tech in tech_terms)

            if has_build_verb and (has_app_noun or has_tech_stack):
                self.logger.info(
                    f"[CONTEXT RULE] Detected application building intent with tech stack. "
                    f"Upgrading to CODE_GENERATION mode."
                )
                return 'code_generation', 0.85, 'Application building with technical context detected'

        # No corrections needed
        reasoning = f"Pattern-based detection: {', '.join(matched_patterns.keys())}"
        return intent_type, confidence, reasoning

    def report_routing_success(self, query: str, intent_type: str):
        """Report that a routing decision was correct"""
        self.logger.info(f"[LEARNING] Routing SUCCESS for intent: {intent_type}")

        # Update pattern success counts
        for pattern_name in self.patterns:
            if intent_type in pattern_name:
                self.patterns[pattern_name].success_count += 1
                self.patterns[pattern_name].last_updated = datetime.now().isoformat()

        self._save_patterns()

    def report_routing_failure(self, query: str, detected_intent: str, correct_intent: str):
        """Report that a routing decision was wrong and learn from it"""
        self.logger.warning(
            f"[LEARNING] Routing FAILURE - Detected: {detected_intent}, "
            f"Should be: {correct_intent}"
        )

        # Update pattern failure counts for detected intent
        for pattern_name in self.patterns:
            if detected_intent in pattern_name:
                self.patterns[pattern_name].failure_count += 1
                self.patterns[pattern_name].confidence *= 0.95  # Reduce confidence
                self.patterns[pattern_name].last_updated = datetime.now().isoformat()

        # Update pattern success counts for correct intent
        for pattern_name in self.patterns:
            if correct_intent in pattern_name:
                self.patterns[pattern_name].success_count += 1
                self.patterns[pattern_name].confidence = min(
                    1.0,
                    self.patterns[pattern_name].confidence * 1.05
                )  # Increase confidence
                self.patterns[pattern_name].last_updated = datetime.now().isoformat()

        self._save_patterns()

    def get_learning_stats(self) -> Dict:
        """Get statistics about the learning system"""
        stats = {
            'total_patterns': len(self.patterns),
            'patterns': {}
        }

        for name, pattern in self.patterns.items():
            total_cases = pattern.success_count + pattern.failure_count
            success_rate = (
                pattern.success_count / total_cases if total_cases > 0 else 0.0
            )

            stats['patterns'][name] = {
                'confidence': pattern.confidence,
                'success_count': pattern.success_count,
                'failure_count': pattern.failure_count,
                'success_rate': success_rate,
                'last_updated': pattern.last_updated
            }

        return stats


# Global singleton instance
_intent_detector: Optional[SelfCorrectingIntentDetector] = None


def get_intent_detector() -> SelfCorrectingIntentDetector:
    """Get or create the global intent detector instance"""
    global _intent_detector
    if _intent_detector is None:
        _intent_detector = SelfCorrectingIntentDetector()
    return _intent_detector
