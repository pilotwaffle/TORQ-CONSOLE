"""
GLM-4.6 powered Prince Flowers Agent for TORQ Console.

This agent uses ZhipuAI's GLM-4.6 model for conversational AI,
code generation, and technical assistance.
"""
import logging
import os
from typing import Optional, Dict, Any, List
from torq_console.llm.glm_client import GLMClient, get_glm_client

logger = logging.getLogger("TORQ.Agents.GLMPrinceFlowers")


class GLMPrinceFlowersAgent:
    """
    Prince Flowers conversational agent powered by GLM-4.6.

    Provides:
    - Natural language conversations
    - Code generation and explanation
    - Technical problem solving
    - Multi-turn conversation tracking
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-4.6",
        system_prompt: Optional[str] = None
    ):
        """
        Initialize GLM Prince Flowers agent.

        Args:
            api_key: Optional GLM API key override
            model: Model to use (default: glm-4.6 - 200K context, superior coding)
            system_prompt: Optional system prompt override
        """
        self.client = get_glm_client(api_key=api_key, model=model)
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []

        # Default system prompt
        self.system_prompt = system_prompt or """You are Prince Flowers, an advanced AI assistant specializing in software development and technical problem-solving.

Your capabilities include:
- Writing clean, efficient, and well-documented code in multiple programming languages
- Debugging and fixing code issues
- Explaining complex technical concepts clearly
- Providing architectural guidance and best practices
- Assisting with algorithm design and optimization

You are helpful, professional, and focused on providing practical solutions. When writing code, always include:
- Clear comments and docstrings
- Type hints where applicable
- Error handling
- Usage examples

Your responses should be concise yet comprehensive, prioritizing actionable information."""

        logger.info(f"Initialized GLM Prince Flowers agent with model: {model}")

    async def chat(
        self,
        message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4000,
        use_web_search: bool = False
    ) -> str:
        """
        Send a message to the agent and get a response.

        Args:
            message: User message
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            use_web_search: Whether to enable web search

        Returns:
            Agent response text
        """
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": message
            })

            # Prepare messages with system prompt
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history
            ]

            # Get response from GLM
            if use_web_search:
                response_text = self.client.chat_with_web_search(
                    messages=messages,
                    temperature=temperature
                )
            else:
                response_text = self.client.chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })

            logger.info(f"GLM Prince Flowers generated response ({len(response_text)} chars)")
            return response_text

        except Exception as e:
            logger.error(f"Error in GLM Prince Flowers chat: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"

    async def generate_code(
        self,
        requirements: str,
        language: str = "python",
        temperature: float = 0.3
    ) -> str:
        """
        Generate code based on requirements.

        Args:
            requirements: Code requirements description
            language: Programming language
            temperature: Sampling temperature (lower for more deterministic code)

        Returns:
            Generated code
        """
        prompt = f"""Generate {language} code for the following requirements:

{requirements}

Requirements:
- Include clear comments and docstrings
- Add type hints where applicable
- Include error handling
- Provide a usage example

Please provide clean, production-ready code."""

        return await self.chat(prompt, temperature=temperature)

    async def explain_code(
        self,
        code: str,
        language: str = "python"
    ) -> str:
        """
        Explain what code does.

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            Explanation text
        """
        prompt = f"""Explain the following {language} code:

```{language}
{code}
```

Please provide:
1. A high-level overview of what the code does
2. Explanation of key components and logic
3. Any potential issues or improvements
4. Time and space complexity if applicable"""

        return await self.chat(prompt, temperature=0.5)

    async def debug_code(
        self,
        code: str,
        error_message: str,
        language: str = "python"
    ) -> str:
        """
        Debug code and suggest fixes.

        Args:
            code: Buggy code
            error_message: Error message or description
            language: Programming language

        Returns:
            Debug analysis and fix suggestions
        """
        prompt = f"""Debug the following {language} code:

```{language}
{code}
```

Error: {error_message}

Please provide:
1. Root cause analysis
2. Fixed version of the code
3. Explanation of the fix
4. Prevention tips"""

        return await self.chat(prompt, temperature=0.4)

    async def research_with_web_search(
        self,
        query: str
    ) -> str:
        """
        Research a topic using web search.

        Args:
            query: Research query

        Returns:
            Research results with sources
        """
        return await self.chat(query, use_web_search=True)

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Cleared GLM Prince Flowers conversation history")

    def get_history_length(self) -> int:
        """Get number of messages in history."""
        return len(self.conversation_history)

    def set_system_prompt(self, prompt: str):
        """Update system prompt."""
        self.system_prompt = prompt
        logger.info("Updated GLM Prince Flowers system prompt")


# Global agent instance
_glm_agent: Optional[GLMPrinceFlowersAgent] = None


def get_glm_prince_flowers(
    api_key: Optional[str] = None,
    model: str = "glm-4.6"
) -> GLMPrinceFlowersAgent:
    """
    Get global GLM Prince Flowers agent instance (singleton).

    Args:
        api_key: Optional API key override
        model: Model to use (default: glm-4.6)

    Returns:
        GLMPrinceFlowersAgent instance
    """
    global _glm_agent

    if _glm_agent is None or api_key:
        _glm_agent = GLMPrinceFlowersAgent(api_key=api_key, model=model)

    return _glm_agent
