"""
Enhanced Prince Flowers Agent with Action-Oriented Learning

This version of Prince Flowers integrates the action learning system to
make better decisions about when to act versus when to ask questions.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from torq_console.agents.marvin_prince_flowers import (
    MarvinPrinceFlowers,
    ConversationTurn,
    AgentState
)
from torq_console.agents.action_learning import (
    get_action_learning,
    ActionDecision,
    ActionOrientedLearning
)
from torq_console.agents.marvin_memory import (
    get_agent_memory,
    InteractionType
)


class EnhancedPrinceFlowers(MarvinPrinceFlowers):
    """
    Enhanced Prince Flowers with action-oriented learning.

    Improvements over base MarvinPrinceFlowers:
    - Analyzes requests to determine if action or clarification is needed
    - Learns from feedback to improve future action decisions
    - More decisive on research/ideation requests
    - Tracks action patterns and improves over time
    """

    def __init__(
        self,
        model: Optional[str] = None,
        personality: str = "helpful, professional, and action-oriented"
    ):
        """
        Initialize enhanced Prince Flowers agent.

        Args:
            model: Optional LLM model override
            personality: Agent personality description
        """
        # Initialize base agent
        super().__init__(model=model, personality=personality)

        # Add action learning system
        self.action_learning = get_action_learning()
        self.agent_memory = get_agent_memory()

        # Override agent instructions to be more action-oriented
        self.agent.instructions = self._get_enhanced_instructions()

        self.logger.info("Initialized Enhanced Prince Flowers with Action Learning")

    def _get_enhanced_instructions(self) -> str:
        """Get enhanced instructions with action-oriented guidance."""
        return """
You are Prince Flowers, an advanced AI assistant specializing in software development
and project management within the TORQ Console environment.

Your personality: Helpful, professional, and action-oriented - you ACT first, ask later.

# CRITICAL ACTION-ORIENTED PRINCIPLES

## 1. IMMEDIATE ACTION for Research/Ideation Requests
When users say:
- "search for X"
- "find X"
- "look up X"
- "get information about X"
- "under ideation: X"
- "explore X"
- "what are the top X"
- "show me X"
- "list X"

**DO THIS:** Immediately perform the search/research using available tools (WebSearch, etc.)
**DO NOT:** Ask how they want you to build a search tool
**DO NOT:** Offer multiple implementation options
**DO NOT:** Ask for clarification unless the request is genuinely ambiguous

### Examples of CORRECT Behavior:
❌ User: "search for top viral TikTok videos"
   YOU: "I can help! Would you like me to: 1) Use WebSearch, 2) Build a TypeScript tool, or 3)..."

✅ User: "search for top viral TikTok videos"
   YOU: *Immediately uses WebSearch tool and returns results*

❌ User: "under ideation: find best React libraries"
   YOU: "Let me clarify - do you want me to search for them or build a tool that..."

✅ User: "under ideation: find best React libraries"
   YOU: *Immediately searches and returns list of best React libraries*

## 2. ASK CLARIFICATION for Build/Implementation Requests
When users say:
- "build a tool to X"
- "create an application for X"
- "implement a system that X"
- "develop X"

**DO THIS:** Ask targeted clarifying questions about requirements
**REASON:** Building requires understanding architecture, constraints, and preferences

### Example:
✅ User: "build a tool to search TikTok"
   YOU: "I'll help build that. Quick questions: 1) What data do you need (views, likes, comments)?
   2) Scheduled or on-demand? 3) Output format (JSON, CSV, dashboard)?"

## 3. Your Decision Framework

When you receive a request, immediately classify it:

**Type A: Information Retrieval** → IMMEDIATE ACTION
- Keywords: search, find, look up, get, show, list, what are, under ideation, explore
- Action: Use WebSearch, Read files, Query databases
- NO clarification needed (unless genuinely ambiguous)

**Type B: Building/Implementation** → ASK CLARIFICATION
- Keywords: build, create, develop, implement, design, generate
- Action: Ask 2-3 targeted questions about requirements
- Then proceed with implementation

**Type C: Genuinely Ambiguous** → PROVIDE OPTIONS
- When intent is truly unclear
- Rare cases only
- Offer 2-3 concrete options

## 4. Learning from Feedback

You have access to past interactions where users gave feedback.
Pay attention to patterns:
- If users said "just do it" → they wanted action, not options
- If users said "I wanted X not Y" → they expected different action type
- Adjust your future responses based on these patterns

## 5. Core Capabilities

- Software development assistance (code writing, debugging, architecture)
- Project planning and task management
- Specification analysis and improvement
- Technical research and documentation ✨ (ACTION-ORIENTED)
- Web search and information retrieval ✨ (ACTION-ORIENTED)
- General programming questions and guidance

## 6. Your Tone

- Professional but approachable
- **Decisive and action-oriented** ✨ (NEW)
- Clear and direct
- Encouraging and supportive
- Technical when appropriate
- **Proactive, not passive** ✨ (NEW)

## 7. When You Make Mistakes

If you offer options when user wanted action:
- Learn from the feedback
- Next time, recognize similar patterns and ACT
- Update your internal decision-making

If you act when user wanted discussion:
- Note the pattern
- Next time, ask first for similar requests
- Balance action with collaboration

# REMEMBER

**The user's time is valuable.**
- Don't make them clarify obvious research requests
- Don't ask how to implement searches when they want search results
- Don't offer "multiple approaches" for simple information retrieval
- DO take decisive action on clear requests
- DO ask questions for complex implementation tasks
- DO learn from every interaction

**You are here to DO, not just discuss.**
"""

    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Enhanced chat with action-oriented decision making.

        Args:
            message: User message
            context: Optional context information

        Returns:
            Agent response
        """
        # Analyze the request to determine action
        action_analysis = self.action_learning.analyze_request(message)

        self.logger.info(
            f"Action analysis: {action_analysis['recommended_action'].value} "
            f"(confidence: {action_analysis['confidence']:.2f})"
        )

        # Add action context
        enhanced_context = context or {}
        enhanced_context['action_analysis'] = action_analysis

        # Store interaction ID for potential feedback
        self._current_interaction_id = None

        # Call base chat method
        response = await super().chat(message, enhanced_context)

        # Record the interaction in memory
        interaction_id = self.agent_memory.record_interaction(
            user_input=message,
            agent_response=response,
            agent_name="prince_flowers_enhanced",
            interaction_type=self._classify_interaction_type(message),
            success=True,
            metadata={
                'action_analysis': {
                    'recommended_action': action_analysis['recommended_action'].value,
                    'confidence': action_analysis['confidence'],
                    'reasoning': action_analysis['reasoning']
                }
            }
        )

        self._current_interaction_id = interaction_id

        return response

    def _classify_interaction_type(self, message: str) -> InteractionType:
        """Classify the interaction type for memory storage."""
        message_lower = message.lower()

        if any(word in message_lower for word in ['search', 'find', 'look up', 'explore', 'ideation']):
            return InteractionType.QUERY

        if any(word in message_lower for word in ['generate', 'create', 'write']):
            return InteractionType.CODE_GENERATION

        if any(word in message_lower for word in ['debug', 'fix', 'error']):
            return InteractionType.DEBUG

        if any(word in message_lower for word in ['document', 'explain', 'describe']):
            return InteractionType.DOCUMENTATION

        return InteractionType.GENERAL_CHAT

    def record_user_feedback(
        self,
        expected_action: ActionDecision,
        feedback_score: float,
        feedback_comment: Optional[str] = None
    ):
        """
        Record user feedback about the agent's response.

        Args:
            expected_action: What action the user expected
            feedback_score: Score from 0.0 (bad) to 1.0 (good)
            feedback_comment: Optional comment
        """
        if not hasattr(self, '_current_interaction_id') or not self._current_interaction_id:
            self.logger.warning("No current interaction to record feedback for")
            return

        # Add feedback score to interaction
        self.agent_memory.add_feedback(self._current_interaction_id, feedback_score)

        # Get the last conversation turn
        if self.state.conversation_history:
            last_turn = self.state.conversation_history[-1]

            # Learn from the feedback
            action_analysis = last_turn.context_used.get('action_analysis', {})
            agent_action = ActionDecision(
                action_analysis.get('recommended_action', 'provide_options')
            ) if action_analysis else ActionDecision.PROVIDE_OPTIONS

            self.action_learning.learn_from_feedback(
                user_request=last_turn.user_message,
                agent_action=agent_action,
                user_expected=expected_action,
                feedback_score=feedback_score
            )

            self.logger.info(
                f"Recorded feedback: {feedback_score:.2f} "
                f"(expected: {expected_action.value}, got: {agent_action.value})"
            )

            if feedback_comment:
                self.logger.info(f"User comment: {feedback_comment}")

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about learning and performance."""
        # Get action learning summary
        action_summary = self.action_learning.get_learning_summary()

        # Get memory snapshot
        memory_snapshot = self.agent_memory.get_memory_snapshot()

        # Get agent metrics
        agent_metrics = self.get_metrics()

        return {
            'action_learning': action_summary,
            'memory': {
                'total_interactions': memory_snapshot.total_interactions,
                'success_rate': memory_snapshot.success_rate,
                'average_feedback': memory_snapshot.average_feedback,
                'learned_patterns': len(memory_snapshot.learned_patterns)
            },
            'agent_performance': {
                'total_interactions': agent_metrics['total_interactions'],
                'success_rate': agent_metrics['success_rate'],
                'conversation_turns': agent_metrics['conversation_turns']
            }
        }


def create_enhanced_prince_flowers(
    model: Optional[str] = None,
    personality: str = "helpful, professional, and action-oriented"
) -> EnhancedPrinceFlowers:
    """
    Create an enhanced Prince Flowers agent with action learning.

    Args:
        model: Optional LLM model override
        personality: Agent personality description

    Returns:
        EnhancedPrinceFlowers instance
    """
    return EnhancedPrinceFlowers(model=model, personality=personality)


# Convenience function to apply the TikTok lesson
def apply_tiktok_lesson():
    """
    Apply the lesson learned from the TikTok search feedback.

    Call this once to permanently teach Prince Flowers to immediately
    search when users say "under ideation: search for X".
    """
    from torq_console.agents.action_learning import record_tiktok_feedback_lesson
    record_tiktok_feedback_lesson()
