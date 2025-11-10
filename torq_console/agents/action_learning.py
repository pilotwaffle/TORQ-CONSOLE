"""
Action-Oriented Learning Enhancement for Prince Flowers Agent

This module enhances the agent's ability to recognize when to take action
versus when to ask for clarification, based on user feedback and patterns.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from torq_console.agents.marvin_memory import (
    MarvinAgentMemory,
    get_agent_memory,
    InteractionType
)


class ActionDecision(str, Enum):
    """Types of action decisions the agent can make."""
    IMMEDIATE_ACTION = "immediate_action"  # Perform the action now
    ASK_CLARIFICATION = "ask_clarification"  # Ask questions first
    PROVIDE_OPTIONS = "provide_options"  # Offer multiple approaches


class RequestPattern(str, Enum):
    """Common request patterns that indicate user intent."""
    RESEARCH_REQUEST = "research"  # "search for", "find", "look up", "get info"
    IDEATION_REQUEST = "ideation"  # "under ideation", "brainstorm", "explore"
    BUILD_REQUEST = "build"  # "create", "build", "develop", "implement"
    EXPLAIN_REQUEST = "explain"  # "explain", "how does", "what is"
    DEBUG_REQUEST = "debug"  # "fix", "debug", "error", "not working"


@dataclass
class ActionPattern:
    """Learned pattern for when to take action vs ask questions."""
    pattern_name: str
    request_keywords: List[str]
    recommended_action: ActionDecision
    confidence: float  # 0.0 to 1.0
    examples: List[str]
    learned_from_feedback: bool = False


class ActionOrientedLearning:
    """
    Enhances agent learning to recognize when to act vs when to clarify.

    This system learns from user feedback to improve action decisions:
    - When to immediately perform searches/research
    - When to ask clarifying questions
    - When to provide multiple options
    """

    # Pre-defined action patterns based on best practices
    BUILT_IN_PATTERNS: List[ActionPattern] = [
        ActionPattern(
            pattern_name="research_immediate_action",
            request_keywords=[
                "search", "find", "look up", "get", "show me", "research",
                "what are", "list", "top", "best", "latest",
                "under ideation", "brainstorm", "explore ideas"
            ],
            recommended_action=ActionDecision.IMMEDIATE_ACTION,
            confidence=0.9,
            examples=[
                "search for top viral TikTok videos",
                "find the latest AI news",
                "research new updates coming to GLM-4.6",
                "under ideation: search for trending topics",
                "show me the best React libraries",
                "what are the top programming languages in 2025"
            ],
            learned_from_feedback=False
        ),
        ActionPattern(
            pattern_name="build_ask_clarification",
            request_keywords=[
                "build a tool", "create an application", "develop a system",
                "implement a service", "design a workflow"
            ],
            recommended_action=ActionDecision.ASK_CLARIFICATION,
            confidence=0.85,
            examples=[
                "build a tool to search TikTok",
                "create an application for monitoring",
                "develop a system to track metrics"
            ],
            learned_from_feedback=False
        ),
        ActionPattern(
            pattern_name="ambiguous_provide_options",
            request_keywords=[
                "help with", "advice on", "suggestions for",
                "thoughts on", "opinions about"
            ],
            recommended_action=ActionDecision.PROVIDE_OPTIONS,
            confidence=0.7,
            examples=[
                "help with choosing a database",
                "advice on architecture patterns",
                "suggestions for improving performance"
            ],
            learned_from_feedback=False
        )
    ]

    def __init__(self, memory: Optional[MarvinAgentMemory] = None):
        """
        Initialize action-oriented learning system.

        Args:
            memory: Optional memory instance (uses global if not provided)
        """
        self.logger = logging.getLogger("TORQ.Agents.ActionLearning")
        self.memory = memory or get_agent_memory()

        # Load or initialize action patterns
        self.action_patterns = self._load_action_patterns()

        self.logger.info(f"Initialized Action-Oriented Learning with {len(self.action_patterns)} patterns")

    def _load_action_patterns(self) -> List[ActionPattern]:
        """Load action patterns from memory or use built-in defaults."""
        patterns = list(self.BUILT_IN_PATTERNS)

        # Load learned patterns from memory
        learned = self.memory.get_patterns("action_decision")

        for pattern_data in learned:
            patterns.append(ActionPattern(
                pattern_name=pattern_data['data']['name'],
                request_keywords=pattern_data['data']['keywords'],
                recommended_action=ActionDecision(pattern_data['data']['action']),
                confidence=pattern_data['data']['confidence'],
                examples=pattern_data['data'].get('examples', []),
                learned_from_feedback=True
            ))

        return patterns

    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """
        Analyze a user request to determine recommended action.

        Args:
            user_request: User's request text

        Returns:
            Dict with recommended action and reasoning
        """
        request_lower = user_request.lower()

        # Find matching patterns
        matches = []
        for pattern in self.action_patterns:
            # Check if any keywords match
            keyword_matches = [
                keyword for keyword in pattern.request_keywords
                if keyword in request_lower
            ]

            if keyword_matches:
                match_score = len(keyword_matches) / len(pattern.request_keywords)
                matches.append({
                    'pattern': pattern,
                    'score': match_score * pattern.confidence,
                    'matched_keywords': keyword_matches
                })

        if not matches:
            return {
                'recommended_action': ActionDecision.PROVIDE_OPTIONS,
                'confidence': 0.5,
                'reasoning': 'No specific pattern matched - providing options is safest',
                'matched_patterns': []
            }

        # Sort by score
        matches.sort(key=lambda x: x['score'], reverse=True)
        best_match = matches[0]

        return {
            'recommended_action': best_match['pattern'].recommended_action,
            'confidence': best_match['score'],
            'reasoning': f"Matched pattern '{best_match['pattern'].pattern_name}' with keywords: {best_match['matched_keywords']}",
            'matched_patterns': [m['pattern'].pattern_name for m in matches[:3]],
            'pattern_examples': best_match['pattern'].examples
        }

    def learn_from_feedback(
        self,
        user_request: str,
        agent_action: ActionDecision,
        user_expected: ActionDecision,
        feedback_score: float
    ):
        """
        Learn from user feedback about action decisions.

        Args:
            user_request: The original user request
            agent_action: What action the agent took
            user_expected: What the user expected
            feedback_score: Feedback score (0.0 = bad, 1.0 = good)
        """
        if feedback_score < 0.5:  # Negative feedback
            # Learn from mistake
            request_lower = user_request.lower()

            # Extract potential keywords
            keywords = self._extract_keywords(request_lower)

            # Create or update pattern
            pattern_data = {
                'name': f'learned_from_feedback_{datetime.now().timestamp()}',
                'keywords': keywords,
                'action': user_expected.value,
                'confidence': 0.7,  # Start with moderate confidence
                'examples': [user_request],
                'learned_from': {
                    'agent_action': agent_action.value,
                    'user_expected': user_expected.value,
                    'feedback_score': feedback_score,
                    'timestamp': datetime.now().isoformat()
                }
            }

            # Store in memory
            self.memory.learn_pattern('action_decision', pattern_data)

            # Add to active patterns
            new_pattern = ActionPattern(
                pattern_name=pattern_data['name'],
                request_keywords=keywords,
                recommended_action=user_expected,
                confidence=0.7,
                examples=[user_request],
                learned_from_feedback=True
            )

            self.action_patterns.append(new_pattern)

            self.logger.info(
                f"Learned new action pattern from feedback: "
                f"{agent_action.value} → {user_expected.value}"
            )

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract potential keywords from request text."""
        # Common action verbs and phrases
        action_verbs = [
            'search', 'find', 'look up', 'get', 'show', 'list',
            'build', 'create', 'develop', 'implement', 'design',
            'explain', 'describe', 'how', 'what', 'why',
            'fix', 'debug', 'solve', 'troubleshoot'
        ]

        # Context phrases
        context_phrases = [
            'under ideation', 'brainstorm', 'explore',
            'top', 'best', 'latest', 'viral', 'trending'
        ]

        found_keywords = []

        for keyword in action_verbs + context_phrases:
            if keyword in text:
                found_keywords.append(keyword)

        return found_keywords[:10]  # Limit to 10 keywords

    def record_successful_action(
        self,
        user_request: str,
        action_taken: ActionDecision,
        feedback_score: float = 1.0
    ):
        """
        Record a successful action decision for reinforcement learning.

        Args:
            user_request: The user's request
            action_taken: Action that was taken
            feedback_score: Positive feedback score
        """
        # Analyze which pattern was matched
        analysis = self.analyze_request(user_request)

        if analysis['matched_patterns']:
            # Reinforce the matched pattern by updating confidence
            pattern_name = analysis['matched_patterns'][0]

            for pattern in self.action_patterns:
                if pattern.pattern_name == pattern_name and pattern.learned_from_feedback:
                    # Increase confidence slightly (up to 0.95 max)
                    pattern.confidence = min(0.95, pattern.confidence + 0.05)

                    self.logger.info(
                        f"Reinforced pattern '{pattern_name}' "
                        f"(confidence now: {pattern.confidence})"
                    )

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learned action patterns."""
        learned_patterns = [p for p in self.action_patterns if p.learned_from_feedback]
        built_in_patterns = [p for p in self.action_patterns if not p.learned_from_feedback]

        return {
            'total_patterns': len(self.action_patterns),
            'learned_patterns': len(learned_patterns),
            'built_in_patterns': len(built_in_patterns),
            'patterns_by_action': {
                'immediate_action': len([p for p in self.action_patterns
                                        if p.recommended_action == ActionDecision.IMMEDIATE_ACTION]),
                'ask_clarification': len([p for p in self.action_patterns
                                         if p.recommended_action == ActionDecision.ASK_CLARIFICATION]),
                'provide_options': len([p for p in self.action_patterns
                                       if p.recommended_action == ActionDecision.PROVIDE_OPTIONS])
            },
            'average_confidence': sum(p.confidence for p in self.action_patterns) / len(self.action_patterns) if self.action_patterns else 0.0
        }


# Global instance
_action_learning: Optional[ActionOrientedLearning] = None


def get_action_learning() -> ActionOrientedLearning:
    """
    Get global action-oriented learning instance (singleton).

    Returns:
        ActionOrientedLearning instance
    """
    global _action_learning

    if _action_learning is None:
        _action_learning = ActionOrientedLearning()

    return _action_learning


# Example usage and learning from the TikTok feedback
def record_tiktok_feedback_lesson():
    """
    Record the lesson learned from the TikTok viral video search feedback.

    This creates a permanent learning pattern so Prince Flowers knows
    to immediately search rather than ask how to build a tool.
    """
    learning = get_action_learning()

    # Record the feedback
    learning.learn_from_feedback(
        user_request="Under ideation: search for top 2 viral TikTok videos",
        agent_action=ActionDecision.PROVIDE_OPTIONS,  # What Prince did (offered options)
        user_expected=ActionDecision.IMMEDIATE_ACTION,  # What user wanted (just search)
        feedback_score=0.2  # Low score for this response
    )

    # Add specific pattern for "under ideation" + "search" phrases
    learning.memory.learn_pattern(
        'action_decision',
        {
            'name': 'ideation_research_immediate',
            'keywords': ['under ideation', 'search for', 'find', 'top'],
            'action': ActionDecision.IMMEDIATE_ACTION.value,
            'confidence': 0.95,
            'examples': [
                'Under ideation: search for top 2 viral TikTok videos',
                'Under ideation: find the best AI tools',
                'Brainstorming: search for trending topics'
            ],
            'lesson': 'When user says "under ideation" or similar brainstorming context with "search/find/look up", they want immediate results, not a discussion about building tools'
        }
    )

    logging.getLogger("TORQ.Agents.ActionLearning").info(
        "Recorded TikTok search feedback lesson - Prince will now immediately act on research requests"
    )
