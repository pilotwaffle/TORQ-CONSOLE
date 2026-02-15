"""
Advanced Learning System for TORQ Console AI

Implements industry best practices for self-correcting AI:
- Reflection and iterative improvement (ruvnet)
- Multi-dimensional interaction tracking (OpenAI community)
- Short/long-term memory systems (EvoAgentX)
- Emotional context and intent analysis
- Self-evolving pattern recognition

This system makes the AI genuinely learn from mistakes and improve over time.
"""

import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import math


@dataclass
class InteractionRecord:
    """Records a single interaction with context"""
    timestamp: str
    query: str
    detected_intent: str
    actual_intent: Optional[str]  # User correction if wrong
    confidence: float
    success: bool
    user_feedback: Optional[str]  # "helpful", "wrong_intent", "incomplete", etc.
    emotional_context: Optional[str]  # "frustrated", "satisfied", "confused"
    session_id: str
    response_time: float
    tokens_used: int


@dataclass
class ReflectionSummary:
    """Result of reflecting on past interactions"""
    period: str  # "hourly", "daily", "weekly"
    total_interactions: int
    success_rate: float
    common_errors: List[Dict[str, Any]]
    improvement_suggestions: List[str]
    pattern_adjustments: Dict[str, float]
    timestamp: str


@dataclass
class LongTermMemory:
    """Persistent knowledge accumulated over time"""
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    successful_patterns: Dict[str, List[str]] = field(default_factory=dict)
    failed_patterns: Dict[str, List[str]] = field(default_factory=dict)
    domain_expertise: Dict[str, float] = field(default_factory=dict)  # confidence by domain
    correction_history: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: str = ""


class AdvancedLearningSystem:
    """
    Advanced learning system implementing industry best practices.

    Features:
    1. Reflection: Analyzes past performance to improve
    2. Multi-dimensional tracking: Context, emotion, intent
    3. Memory: Short-term (session) and long-term (persistent)
    4. Self-evolution: Automatically adjusts patterns
    5. Human-in-the-loop: Incorporates user feedback
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.storage_path = storage_path or Path.home() / '.torq_console' / 'learning_system'
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Short-term memory (current session)
        self.short_term_memory: List[InteractionRecord] = []
        self.current_session_id = self._generate_session_id()

        # Long-term memory (persistent)
        self.long_term_memory = self._load_long_term_memory()

        # Reflection cache
        self.last_reflection: Optional[ReflectionSummary] = None
        self.reflection_interval = 3600  # Reflect every hour

        # Learning parameters
        self.learning_rate = 0.1  # How quickly patterns adapt
        self.confidence_threshold = 0.7  # Minimum confidence for decisions
        self.reflection_threshold = 10  # Minimum interactions before reflection

    def _generate_session_id(self) -> str:
        """Generate unique session identifier"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _load_long_term_memory(self) -> LongTermMemory:
        """Load persistent long-term memory"""
        memory_file = self.storage_path / 'long_term_memory.json'
        if memory_file.exists():
            try:
                with open(memory_file, 'r') as f:
                    data = json.load(f)
                    return LongTermMemory(**data)
            except Exception as e:
                self.logger.error(f"Failed to load long-term memory: {e}")

        return LongTermMemory(last_updated=datetime.now().isoformat())

    def _save_long_term_memory(self):
        """Save long-term memory to disk"""
        try:
            memory_file = self.storage_path / 'long_term_memory.json'
            with open(memory_file, 'w') as f:
                json.dump(asdict(self.long_term_memory), f, indent=2)
            self.logger.info("Long-term memory saved")
        except Exception as e:
            self.logger.error(f"Failed to save long-term memory: {e}")

    def record_interaction(
        self,
        query: str,
        detected_intent: str,
        confidence: float,
        success: bool,
        actual_intent: Optional[str] = None,
        user_feedback: Optional[str] = None,
        response_time: float = 0.0,
        tokens_used: int = 0
    ):
        """
        Record an interaction for learning.

        This implements multi-dimensional tracking from OpenAI community insights.
        """
        # Detect emotional context from query
        emotional_context = self._analyze_emotional_context(query)

        record = InteractionRecord(
            timestamp=datetime.now().isoformat(),
            query=query[:500],  # Truncate for storage
            detected_intent=detected_intent,
            actual_intent=actual_intent,
            confidence=confidence,
            success=success,
            user_feedback=user_feedback,
            emotional_context=emotional_context,
            session_id=self.current_session_id,
            response_time=response_time,
            tokens_used=tokens_used
        )

        # Add to short-term memory
        self.short_term_memory.append(record)

        # Update long-term memory if there was a correction
        if actual_intent and actual_intent != detected_intent:
            self._update_long_term_memory_from_correction(record)

        # Save interaction to disk
        self._save_interaction_record(record)

        # Trigger reflection if threshold reached
        if len(self.short_term_memory) >= self.reflection_threshold:
            self._trigger_reflection()

        self.logger.info(
            f"[LEARNING] Recorded: {detected_intent} "
            f"(success={success}, feedback={user_feedback})"
        )

    def _analyze_emotional_context(self, query: str) -> Optional[str]:
        """
        Analyze emotional context from query text.

        Implements emotion tracking from OpenAI community insights.
        """
        query_lower = query.lower()

        # Frustration indicators
        if any(word in query_lower for word in ['why', 'still', 'again', 'keep', 'frustrated', 'annoying']):
            return 'frustrated'

        # Satisfaction indicators
        if any(word in query_lower for word in ['thanks', 'perfect', 'great', 'excellent', 'helpful']):
            return 'satisfied'

        # Confusion indicators
        if any(word in query_lower for word in ['confused', 'understand', 'what', 'how', 'unclear']):
            return 'confused'

        # Urgent indicators
        if any(word in query_lower for word in ['urgent', 'asap', 'quickly', 'immediately', 'now']):
            return 'urgent'

        return 'neutral'

    def _update_long_term_memory_from_correction(self, record: InteractionRecord):
        """
        Update long-term memory when user corrects an intent.

        Implements continuous learning from feedback.
        """
        if not record.actual_intent:
            return

        # Record the correction
        correction = {
            'timestamp': record.timestamp,
            'query_sample': record.query[:100],
            'detected': record.detected_intent,
            'actual': record.actual_intent,
            'confidence': record.confidence
        }
        self.long_term_memory.correction_history.append(correction)

        # Update failed patterns for detected intent
        query_keywords = self._extract_keywords(record.query)
        if record.detected_intent not in self.long_term_memory.failed_patterns:
            self.long_term_memory.failed_patterns[record.detected_intent] = []
        self.long_term_memory.failed_patterns[record.detected_intent].extend(query_keywords[:3])

        # Update successful patterns for actual intent
        if record.actual_intent not in self.long_term_memory.successful_patterns:
            self.long_term_memory.successful_patterns[record.actual_intent] = []
        self.long_term_memory.successful_patterns[record.actual_intent].extend(query_keywords[:3])

        # Adjust domain expertise
        self._adjust_domain_expertise(record)

        self.long_term_memory.last_updated = datetime.now().isoformat()
        self._save_long_term_memory()

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Simple keyword extraction (can be enhanced with NLP)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'for', 'to', 'of'}
        words = text.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        return keywords[:10]  # Top 10 keywords

    def _adjust_domain_expertise(self, record: InteractionRecord):
        """
        Adjust domain expertise scores based on performance.

        Implements domain-specific learning.
        """
        # Infer domain from query keywords
        domains = self._infer_domains(record.query)

        for domain in domains:
            current_score = self.long_term_memory.domain_expertise.get(domain, 0.5)

            if record.success:
                # Increase expertise on success
                new_score = min(1.0, current_score + self.learning_rate * 0.1)
            else:
                # Decrease expertise on failure
                new_score = max(0.0, current_score - self.learning_rate * 0.2)

            self.long_term_memory.domain_expertise[domain] = new_score

    def _infer_domains(self, query: str) -> List[str]:
        """Infer relevant domains from query"""
        query_lower = query.lower()
        domains = []

        if any(word in query_lower for word in ['crypto', 'coin', 'bitcoin', 'shib', 'price']):
            domains.append('cryptocurrency')

        if any(word in query_lower for word in ['post', 'tweet', 'x.com', 'content', 'write']):
            domains.append('content_creation')

        if any(word in query_lower for word in ['code', 'app', 'build', 'develop', 'api', 'typescript']):
            domains.append('software_development')

        if any(word in query_lower for word in ['search', 'research', 'find', 'information']):
            domains.append('information_retrieval')

        return domains if domains else ['general']

    def _save_interaction_record(self, record: InteractionRecord):
        """Save individual interaction record"""
        try:
            interactions_file = self.storage_path / 'interactions.jsonl'
            with open(interactions_file, 'a') as f:
                f.write(json.dumps(asdict(record)) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to save interaction record: {e}")

    def _trigger_reflection(self):
        """
        Trigger reflection process to learn from recent interactions.

        Implements reflection mechanism from ruvnet's insights.
        """
        self.logger.info("[REFLECTION] Analyzing recent interactions...")

        # Analyze short-term memory
        total_interactions = len(self.short_term_memory)
        successful = sum(1 for r in self.short_term_memory if r.success)
        success_rate = successful / total_interactions if total_interactions > 0 else 0.0

        # Identify common errors
        common_errors = self._identify_common_errors()

        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            success_rate, common_errors
        )

        # Calculate pattern adjustments
        pattern_adjustments = self._calculate_pattern_adjustments()

        # Create reflection summary
        reflection = ReflectionSummary(
            period="session",
            total_interactions=total_interactions,
            success_rate=success_rate,
            common_errors=common_errors,
            improvement_suggestions=improvement_suggestions,
            pattern_adjustments=pattern_adjustments,
            timestamp=datetime.now().isoformat()
        )

        self.last_reflection = reflection
        self._save_reflection(reflection)

        # Apply pattern adjustments
        self._apply_pattern_adjustments(pattern_adjustments)

        # Clear short-term memory after reflection
        self.short_term_memory = []

        self.logger.info(
            f"[REFLECTION] Complete: Success rate {success_rate:.2%}, "
            f"{len(improvement_suggestions)} suggestions"
        )

    def _identify_common_errors(self) -> List[Dict[str, Any]]:
        """Identify most common error patterns"""
        error_counts = defaultdict(int)

        for record in self.short_term_memory:
            if not record.success and record.actual_intent:
                error_key = f"{record.detected_intent}→{record.actual_intent}"
                error_counts[error_key] += 1

        # Sort by frequency
        common_errors = [
            {
                'error_type': error_key,
                'count': count,
                'percentage': count / len(self.short_term_memory) * 100
            }
            for error_key, count in sorted(
                error_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]  # Top 5 errors
        ]

        return common_errors

    def _generate_improvement_suggestions(
        self, success_rate: float, common_errors: List[Dict]
    ) -> List[str]:
        """Generate actionable improvement suggestions"""
        suggestions = []

        # Success rate-based suggestions
        if success_rate < 0.7:
            suggestions.append(
                "Consider increasing confidence threshold to reduce incorrect routing"
            )

        if success_rate < 0.5:
            suggestions.append(
                "Critical: Review and refine intent detection patterns immediately"
            )

        # Error-specific suggestions
        for error in common_errors:
            if error['percentage'] > 20:
                error_type = error['error_type']
                suggestions.append(
                    f"High-frequency error: {error_type} - Add disambiguation rules"
                )

        # Emotional context suggestions
        frustrated_count = sum(
            1 for r in self.short_term_memory
            if r.emotional_context == 'frustrated'
        )
        if frustrated_count > len(self.short_term_memory) * 0.3:
            suggestions.append(
                "User frustration detected - Improve response clarity and add helpful hints"
            )

        return suggestions

    def _calculate_pattern_adjustments(self) -> Dict[str, float]:
        """Calculate how patterns should be adjusted based on performance"""
        adjustments = {}

        intent_performance = defaultdict(lambda: {'success': 0, 'failure': 0})

        for record in self.short_term_memory:
            intent = record.detected_intent
            if record.success:
                intent_performance[intent]['success'] += 1
            else:
                intent_performance[intent]['failure'] += 1

        for intent, stats in intent_performance.items():
            total = stats['success'] + stats['failure']
            success_rate = stats['success'] / total if total > 0 else 0.5

            # Calculate adjustment factor
            if success_rate > 0.8:
                adjustment = +self.learning_rate  # Increase confidence
            elif success_rate < 0.5:
                adjustment = -self.learning_rate  # Decrease confidence
            else:
                adjustment = 0.0  # No change

            adjustments[intent] = adjustment

        return adjustments

    def _apply_pattern_adjustments(self, adjustments: Dict[str, float]):
        """Apply calculated pattern adjustments to improve future performance"""
        # This would integrate with the intent detector to adjust pattern confidence
        # For now, we log the adjustments
        for intent, adjustment in adjustments.items():
            self.logger.info(
                f"[PATTERN ADJUSTMENT] {intent}: {adjustment:+.3f}"
            )

    def _save_reflection(self, reflection: ReflectionSummary):
        """Save reflection summary"""
        try:
            reflections_file = self.storage_path / 'reflections.jsonl'
            with open(reflections_file, 'a') as f:
                f.write(json.dumps(asdict(reflection)) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to save reflection: {e}")

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics"""
        return {
            'current_session': {
                'session_id': self.current_session_id,
                'interactions': len(self.short_term_memory),
                'success_rate': self._calculate_session_success_rate()
            },
            'long_term_memory': {
                'corrections': len(self.long_term_memory.correction_history),
                'domain_expertise': self.long_term_memory.domain_expertise,
                'last_updated': self.long_term_memory.last_updated
            },
            'last_reflection': asdict(self.last_reflection) if self.last_reflection else None
        }

    def _calculate_session_success_rate(self) -> float:
        """Calculate success rate for current session"""
        if not self.short_term_memory:
            return 0.0
        successful = sum(1 for r in self.short_term_memory if r.success)
        return successful / len(self.short_term_memory)

    def get_confidence_boost(self, intent: str, query: str) -> float:
        """
        Get confidence boost for an intent based on learned patterns.

        This allows the system to self-evolve its decision-making.
        """
        boost = 0.0

        # Check domain expertise
        domains = self._infer_domains(query)
        for domain in domains:
            expertise = self.long_term_memory.domain_expertise.get(domain, 0.5)
            if expertise > 0.7:
                boost += 0.1  # Boost confidence in strong domains

        # Check successful patterns
        keywords = self._extract_keywords(query)
        successful_patterns = self.long_term_memory.successful_patterns.get(intent, [])
        matching_patterns = sum(1 for kw in keywords if kw in successful_patterns)
        if matching_patterns > 0:
            boost += min(0.2, matching_patterns * 0.05)

        # Check failed patterns (negative boost)
        failed_patterns = self.long_term_memory.failed_patterns.get(intent, [])
        matching_failures = sum(1 for kw in keywords if kw in failed_patterns)
        if matching_failures > 0:
            boost -= min(0.2, matching_failures * 0.05)

        return boost


# Global singleton
_learning_system: Optional[AdvancedLearningSystem] = None


def get_learning_system() -> AdvancedLearningSystem:
    """Get or create the global learning system instance"""
    global _learning_system
    if _learning_system is None:
        _learning_system = AdvancedLearningSystem()
    return _learning_system
