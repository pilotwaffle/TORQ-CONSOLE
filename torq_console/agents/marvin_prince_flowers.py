"""
Enhanced Prince Flowers Agent with Marvin Integration

Marvin-powered conversational agent with structured outputs,
intelligent context management, and multi-modal capabilities.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import marvin

from torq_console.marvin_integration import (
    TorqMarvinIntegration,
    create_general_agent,
    IntentClassification,
    ComplexityLevel,
)


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    timestamp: str
    user_message: str
    agent_response: str
    intent: Optional[IntentClassification] = None
    context_used: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    """Current state of the Prince Flowers agent."""
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    active_tasks: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)


class MarvinPrinceFlowers:
    """
    Enhanced Prince Flowers conversational agent powered by Marvin.

    Provides intelligent conversation handling with:
    - Structured output generation
    - Context-aware responses
    - Multi-turn conversation tracking
    - Task management integration
    - Personality and tone adaptation
    """

    def __init__(
        self,
        model: Optional[str] = None,
        personality: str = "helpful and professional"
    ):
        """
        Initialize enhanced Prince Flowers agent.

        Args:
            model: Optional LLM model override
            personality: Agent personality description
        """
        self.logger = logging.getLogger("TORQ.Agents.PrinceFlowers")
        self.marvin = TorqMarvinIntegration(model=model)

        # Create Marvin agent with custom personality
        self.agent = self._create_marvin_agent(personality)

        # Agent state
        self.state = AgentState()

        # Performance metrics
        self.metrics = {
            'total_interactions': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'average_response_quality': 0.0
        }

        self.logger.info("Initialized Enhanced Prince Flowers Agent")

    def _create_marvin_agent(self, personality: str) -> marvin.Agent:
        """Create Marvin agent with Prince Flowers personality."""
        instructions = f"""
You are Prince Flowers, an advanced AI assistant specializing in software development
and project management within the TORQ Console environment.

Your personality: {personality}

Your core capabilities:
- Software development assistance (code writing, debugging, architecture)
- Project planning and task management
- Specification analysis and improvement
- Technical research and documentation
- General programming questions and guidance
- Web search and information retrieval

Your approach:
- Be concise but thorough
- Provide actionable advice
- Ask clarifying questions when needed
- Reference TORQ Console features when relevant
- Maintain conversation context
- Adapt your responses to the user's expertise level

Your tone:
- Professional but approachable
- Clear and direct
- Encouraging and supportive
- Technical when appropriate

CRITICAL: Search vs Code Generation
- When users ask to "search", "find", "look up", or "get information about" something,
  they want you to PERFORM THE SEARCH and provide results
- DO NOT generate code/applications for search tools unless explicitly requested
- Examples:
  ✓ "search prince celebration 2026" → Perform web search and provide results
  ✓ "use perplexity to search X" → Perform web search for X (not generate Perplexity code)
  ✗ "search latest AI news" → DO NOT generate a TypeScript search application
  ✓ "write code that uses the Perplexity API" → Generate code (explicit code request)

When handling requests:
1. Understand the user's intent (search vs code generation vs conversation)
2. Consider conversation context
3. Provide structured, actionable responses
4. Suggest next steps or related actions
5. Offer to help with follow-up questions
"""

        return marvin.Agent(
            name="Prince Flowers",
            instructions=instructions,
            model=self.marvin.model
        )

    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Handle a chat message with context awareness.

        Args:
            message: User message
            context: Optional context information

        Returns:
            Agent response
        """
        try:
            self.metrics['total_interactions'] += 1

            # Classify intent
            intent = await self._classify_intent(message)

            # Build context for agent
            agent_context = self._build_context(context)

            # Generate response using Marvin
            response = await self._generate_response(
                message,
                agent_context,
                intent
            )

            # Store conversation turn
            turn = ConversationTurn(
                timestamp=datetime.now().isoformat(),
                user_message=message,
                agent_response=response,
                intent=intent,
                context_used=agent_context
            )

            self.state.conversation_history.append(turn)

            self.metrics['successful_responses'] += 1
            self.logger.info(f"Chat handled successfully (intent: {intent.value if intent else 'unknown'})")

            return response

        except Exception as e:
            self.metrics['failed_responses'] += 1
            self.logger.error(f"Failed to handle chat: {e}", exc_info=True)
            return self._fallback_response(message)

    async def _classify_intent(self, message: str) -> Optional[IntentClassification]:
        """Classify user message intent."""
        try:
            intent = self.marvin.classify(
                message,
                IntentClassification,
                instructions="Classify the intent of this user message"
            )
            return intent
        except Exception as e:
            self.logger.error(f"Intent classification failed: {e}")
            return None

    def _build_context(
        self,
        additional_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build comprehensive context for agent."""
        context = {
            'conversation_turns': len(self.state.conversation_history),
            'active_tasks': self.state.active_tasks[:5],  # Recent tasks
            'agent_state': {
                'has_history': len(self.state.conversation_history) > 0,
                'preferences': self.state.preferences
            }
        }

        # Add recent conversation context
        if self.state.conversation_history:
            recent_turns = self.state.conversation_history[-3:]
            context['recent_conversation'] = [
                {
                    'user': turn.user_message[:100],
                    'assistant': turn.agent_response[:100],
                    'intent': turn.intent.value if turn.intent else 'unknown'
                }
                for turn in recent_turns
            ]

        # Merge additional context
        if additional_context:
            context.update(additional_context)

        return context

    async def _generate_response(
        self,
        message: str,
        context: Dict[str, Any],
        intent: Optional[IntentClassification]
    ) -> str:
        """Generate response using Marvin agent."""
        # Build prompt with context
        prompt_parts = [message]

        # Add context hints
        if context.get('recent_conversation'):
            prompt_parts.insert(0, "[Conversation context available]")

        if context.get('active_tasks'):
            prompt_parts.append(f"[Active tasks: {len(context['active_tasks'])}]")

        full_prompt = "\n".join(prompt_parts)

        # Use Marvin's run for simple response
        response = self.marvin.run(
            full_prompt,
            result_type=str,
            context=context,
            agents=[self.agent]
        )

        return response

    def _fallback_response(self, message: str) -> str:
        """Generate fallback response when AI fails."""
        return (
            "I apologize, but I'm having trouble processing your request right now. "
            "This could be due to a temporary issue with the AI system. "
            "Please try rephrasing your question, or ask me something else."
        )

    async def handle_task_request(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle a task-oriented request with structured output.

        Args:
            task_description: Description of the task
            context: Optional context

        Returns:
            Structured task information
        """
        try:
            # Use Marvin to structure the task
            task_prompt = f"""
Analyze this task request and provide a structured response:

Task: {task_description}

Provide:
1. What needs to be done (clear, actionable)
2. Required steps (ordered list)
3. Estimated complexity
4. Potential challenges
5. Recommended approach
"""

            response = self.marvin.run(
                task_prompt,
                result_type=str,
                context=context
            )

            # Add to active tasks
            task_id = f"task_{len(self.state.active_tasks) + 1}"
            self.state.active_tasks.append(task_id)

            return {
                'task_id': task_id,
                'description': task_description,
                'analysis': response,
                'status': 'pending'
            }

        except Exception as e:
            self.logger.error(f"Failed to handle task request: {e}")
            return {
                'error': str(e),
                'description': task_description,
                'status': 'failed'
            }

    async def provide_code_assistance(
        self,
        code_request: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Provide code assistance with structured output.

        Args:
            code_request: What code is needed
            language: Programming language
            context: Optional context

        Returns:
            Dictionary with code and explanation
        """
        try:
            prompt = f"""
Provide code assistance for this request:

Request: {code_request}
Language: {language}

Provide:
1. The code solution
2. Brief explanation of how it works
3. Usage example
4. Potential improvements or alternatives
"""

            response = self.marvin.run(
                prompt,
                result_type=str,
                context=context
            )

            return {
                'request': code_request,
                'language': language,
                'response': response,
                'status': 'success'
            }

        except Exception as e:
            self.logger.error(f"Code assistance failed: {e}")
            return {
                'request': code_request,
                'error': str(e),
                'status': 'failed'
            }

    def update_preferences(self, preferences: Dict[str, Any]):
        """Update agent preferences."""
        self.state.preferences.update(preferences)
        self.logger.info(f"Updated preferences: {preferences}")

    def clear_history(self):
        """Clear conversation history."""
        self.state.conversation_history.clear()
        self.logger.info("Conversation history cleared")

    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation."""
        if not self.state.conversation_history:
            return "No conversation history"

        total_turns = len(self.state.conversation_history)
        intents = [
            turn.intent.value
            for turn in self.state.conversation_history
            if turn.intent
        ]

        intent_counts = {}
        for intent in intents:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

        summary = f"Conversation: {total_turns} turns"

        if intent_counts:
            top_intents = sorted(
                intent_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]

            intent_str = ", ".join(f"{intent} ({count})" for intent, count in top_intents)
            summary += f"\nTop intents: {intent_str}"

        return summary

    def get_state(self) -> AgentState:
        """Get current agent state."""
        return self.state

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        success_rate = 0.0
        if self.metrics['total_interactions'] > 0:
            success_rate = (
                self.metrics['successful_responses'] /
                self.metrics['total_interactions']
            )

        return {
            **self.metrics,
            'success_rate': round(success_rate, 3),
            'conversation_turns': len(self.state.conversation_history),
            'active_tasks_count': len(self.state.active_tasks),
            'marvin_metrics': self.marvin.get_metrics()
        }


# Factory function
def create_prince_flowers_agent(
    model: Optional[str] = None,
    personality: str = "helpful and professional"
) -> MarvinPrinceFlowers:
    """
    Create an enhanced Prince Flowers agent.

    Args:
        model: Optional LLM model override
        personality: Agent personality description

    Returns:
        MarvinPrinceFlowers instance
    """
    return MarvinPrinceFlowers(model=model, personality=personality)
