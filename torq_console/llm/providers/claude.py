"""
Claude Provider for TORQ Console.

Provides integration with Anthropic Claude models including Sonnet 4.5.
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from anthropic import Anthropic, AsyncAnthropic

from .base import BaseLLMProvider


class ClaudeProvider(BaseLLMProvider):
    """Provider for Anthropic Claude models."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Claude provider.

        Args:
            config: Configuration dict with 'api_key' and 'model' keys
        """
        super().__init__(config)

        # Extract parameters from config or environment
        self.api_key = self.config.get('api_key') if self.config else os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            self.api_key = os.getenv('ANTHROPIC_API_KEY')

        self.model = self.config.get('model', 'claude-sonnet-4-20250514') if self.config else 'claude-sonnet-4-20250514'
        self.logger = logging.getLogger(__name__)

        # Initialize Anthropic client
        if self.api_key:
            self.client = AsyncAnthropic(api_key=self.api_key)
            self.logger.info(f"Claude provider initialized with model: {self.model}")
        else:
            self.client = None
            self.logger.warning("Claude provider initialized without API key")

    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        return bool(self.api_key and self.client)

    async def query(self, prompt: str, **kwargs) -> str:
        """
        Execute a simple query.

        Args:
            prompt: The query prompt
            **kwargs: Additional parameters (temperature, max_tokens, system_prompt, etc.)

        Returns:
            The response string
        """
        if not self.is_configured():
            return "Error: Claude provider not configured (missing API key)"

        try:
            # Build message with optional system prompt
            system_prompt = kwargs.get('system_prompt') or kwargs.get('system', None)
            messages = [{"role": "user", "content": prompt}]

            # Extract parameters
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 4096)

            # Call Claude API
            # Strong system prompt to prevent code generation for non-code requests
            default_system = """You are Prince Flowers, a helpful AI assistant. CRITICAL RULES:
1. NEVER generate code unless the user explicitly asks you to "write code", "create an app", "build", "implement", or "generate code"
2. If asked about predictions, outlooks, forecasts, or future prices: provide a conversational analysis with caveats about uncertainty. DO NOT generate forecasting applications or code.
3. Answer questions directly and conversationally
4. Be helpful but concise"""

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else default_system,
                messages=messages
            )

            # Extract text from response
            return response.content[0].text

        except Exception as e:
            self.logger.error(f"Claude query error: {e}")
            return f"Error querying Claude: {str(e)}"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Execute a multi-turn chat.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_message: Optional system message
            **kwargs: Additional parameters

        Returns:
            The response string
        """
        if not self.is_configured():
            return "Error: Claude provider not configured (missing API key)"

        try:
            # Extract parameters
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 4096)
            thinking_budget = kwargs.get('thinking_budget', 10000)  # Extended thinking tokens

            # Format messages for Claude
            formatted_messages = []
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')

                # Claude only accepts 'user' and 'assistant' roles
                if role in ['user', 'assistant']:
                    formatted_messages.append({
                        "role": role,
                        "content": content
                    })

            # Call Claude API
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                thinking={
                    "type": "enabled",
                    "budget_tokens": thinking_budget
                },
                system=system_message if system_message else "You are Claude, a helpful AI assistant specialized in coding, reasoning, and problem-solving.",
                messages=formatted_messages
            )

            # Extract text from response
            return response.content[0].text

        except Exception as e:
            self.logger.error(f"Claude chat error: {e}")
            return f"Error in Claude chat: {str(e)}"

    async def code_generation(
        self,
        task_description: str,
        language: str = "python",
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate code using Claude's strong coding capabilities.

        Args:
            task_description: What the code should do
            language: Programming language
            context: Additional context (existing code, requirements, etc.)
            **kwargs: Additional parameters

        Returns:
            Generated code
        """
        # Build specialized prompt for code generation
        prompt = f"""Generate {language} code for the following task:

Task: {task_description}

{f"Context: {context}" if context else ""}

Please provide:
1. Clean, well-documented code
2. Error handling where appropriate
3. Best practices for {language}
4. Comments explaining key sections

Code:"""

        system_message = f"""You are an expert {language} developer. Generate high-quality,
production-ready code that follows best practices. Include comprehensive error handling,
type hints (where applicable), and clear documentation."""

        return await self.query(
            prompt,
            system=system_message,
            temperature=kwargs.get('temperature', 0.3),  # Lower temperature for code
            max_tokens=kwargs.get('max_tokens', 8000)
        )

    async def reasoning_task(
        self,
        query: str,
        reasoning_type: str = "analytical",
        **kwargs
    ) -> str:
        """
        Execute complex reasoning tasks using Claude's extended thinking.

        Args:
            query: The reasoning query
            reasoning_type: Type of reasoning (analytical, strategic, creative, technical)
            **kwargs: Additional parameters

        Returns:
            Reasoned response
        """
        reasoning_prompts = {
            "analytical": "Analyze this thoroughly, breaking down the problem systematically.",
            "strategic": "Think strategically about this, considering long-term implications.",
            "creative": "Approach this creatively, exploring multiple innovative solutions.",
            "technical": "Think through the technical details carefully and comprehensively."
        }

        system_message = f"""You are Claude with extended thinking capabilities.
{reasoning_prompts.get(reasoning_type, reasoning_prompts['analytical'])}

Take your time to reason through the problem step by step before providing your answer.
Use your thinking tokens to explore different approaches and validate your reasoning."""

        return await self.chat(
            messages=[{"role": "user", "content": query}],
            system_message=system_message,
            thinking_budget=kwargs.get('thinking_budget', 10000),
            temperature=kwargs.get('temperature', 0.8),
            max_tokens=kwargs.get('max_tokens', 8000)
        )

    async def search_and_answer(self, query: str, **kwargs) -> str:
        """
        Answer queries that may require research/knowledge.

        Args:
            query: The search query
            **kwargs: Additional parameters

        Returns:
            Comprehensive answer
        """
        system_message = """You are Claude, a knowledgeable AI assistant.
When answering queries, provide comprehensive, accurate information.
If you're unsure about recent events or specific facts, acknowledge that."""

        return await self.query(
            query,
            system=system_message,
            temperature=0.7,
            max_tokens=kwargs.get('max_tokens', 4096)
        )

    async def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from Claude (required by BaseLLMProvider).

        This is the main interface method that routing logic calls.

        Args:
            prompt: The input prompt
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        # Route to appropriate method based on context
        context = kwargs.get('context', {})
        mode = context.get('mode', 'general')

        if mode == 'build' or mode == 'code':
            # Code generation mode
            language = kwargs.get('language', 'python')
            return await self.code_generation(prompt, language=language, **kwargs)
        elif mode == 'reasoning':
            # Complex reasoning mode
            return await self.reasoning_task(prompt, **kwargs)
        else:
            # General query mode
            return await self.query(prompt, **kwargs)

    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a chat completion response (required by BaseLLMProvider).

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        system_message = kwargs.get('system', None)
        return await self.chat(messages, system_message=system_message, **kwargs)
