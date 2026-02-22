"""
Ollama Local LLM Provider for TORQ CONSOLE.

This module implements local LLM integration via Ollama with:
- OpenAI-compatible API format
- Local inference (no API costs)
- Support for multiple models (DeepSeek, Llama, Mistral, etc.)
- Streaming response support
- Automatic model management
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
import logging
import aiohttp
from datetime import datetime

# Import typed exceptions for proper error classification
from torq_console.ui.web_ai_fix import AIResponseError, AITimeoutError, ProviderError


def _is_policy_violation(msg: str) -> bool:
    """
    Detect if an error message represents a content policy/safety violation.

    These should be terminal (no fallback) to prevent circumventing safety filters.
    This is primarily for Ollama instances running guard models or middleware.
    """
    s = (msg or "").lower()
    markers = [
        "content policy",
        "safety",
        "violates",
        "policy violation",
        "against our policies",
        "safety guidelines",
        "inappropriate content"
    ]
    return any(m in s for m in markers)


class OllamaProvider:
    """Ollama local LLM provider with OpenAI-compatible interface."""

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "deepseek-r1:7b"):
        """
        Initialize Ollama provider.

        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            default_model: Default model to use
        """
        self.base_url = base_url.rstrip('/')
        self.default_model = default_model
        self.logger = logging.getLogger(__name__)

        # Default configuration (optimized for local inference)
        self.default_max_tokens = 2048  # Balanced for quality and speed
        self.default_temperature = 0.7

        # Connection pooling session (reuse for better performance)
        self.session = None

        self.logger.info(f"Ollama provider initialized with base URL: {base_url}")
        self.logger.info(f"Default model: {default_model}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create persistent session for connection pooling."""
        if self.session is None or self.session.closed:
            # Create persistent session with extended timeouts for local inference
            timeout = aiohttp.ClientTimeout(
                total=300,     # Total timeout - 5 minutes for large models
                connect=10,    # Connection timeout
                sock_read=180  # Socket read timeout - 3 minutes for inference
            )
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _make_request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        timeout: int = 180
    ) -> Dict[str, Any]:
        """Make an HTTP request to Ollama API with performance monitoring."""
        import time

        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json"
        }

        try:
            # Add timing diagnostics
            start_time = time.time()

            # Use persistent session for connection pooling
            session = await self._get_session()
            async with session.post(url, json=data, headers=headers) as response:
                response_data = await response.json()

                end_time = time.time()
                response_time = end_time - start_time

                if response.status == 200:
                    self.logger.info(f"Ollama API response time: {response_time:.2f}s")
                    return response_data
                else:
                    error_msg = response_data.get('error', f'HTTP {response.status}')
                    raise ProviderError(f"Ollama API error: {error_msg}", code=str(response.status))

        except asyncio.TimeoutError as e:
            self.logger.error(f"Ollama request timed out: {e}")
            raise AITimeoutError("Ollama request timed out") from e
        except aiohttp.ClientError as e:
            self.logger.error(f"Ollama network error: {e}")
            raise ProviderError(f"Ollama network error: {e}", code="network_error") from e
        except (AIResponseError, AITimeoutError, ProviderError):
            # Re-raise our typed exceptions
            raise
        except Exception as e:
            self.logger.error(f"Ollama adapter exception: {e}")
            raise ProviderError(f"Ollama adapter exception: {e}", code="adapter_error") from e

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion using Ollama API.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name (default: deepseek-v3.2-exp)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to use streaming (not yet implemented)
            **kwargs: Additional API parameters

        Returns:
            Response dictionary with completion
        """

        # Convert OpenAI-style messages to Ollama format
        prompt = self._convert_messages_to_prompt(messages)

        # Prepare request data
        data = {
            "model": model or self.default_model,
            "prompt": prompt,
            "stream": False,  # Ollama uses stream parameter directly
            "options": {
                "num_predict": max_tokens or self.default_max_tokens,
                "temperature": temperature or self.default_temperature,
            }
        }

        # Add any additional Ollama-specific options
        if kwargs:
            data["options"].update(kwargs)

        try:
            self.logger.debug(f"Making completion request with {len(messages)} messages to model: {model or self.default_model}")
            response = await self._make_request("/api/generate", data)

            # Extract content from response
            if response.get('response'):
                return {
                    'content': response['response'],
                    'model': response.get('model', model),
                    'usage': {
                        'prompt_tokens': response.get('prompt_eval_count', 0),
                        'completion_tokens': response.get('eval_count', 0),
                        'total_tokens': response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
                    },
                    'finish_reason': 'stop' if response.get('done') else 'length',
                    'raw_response': response
                }

            # Fallback if response structure is unexpected
            return {
                'content': str(response),
                'model': model,
                'usage': {},
                'finish_reason': 'unknown',
                'raw_response': response
            }

        except asyncio.TimeoutError as e:
            self.logger.error(f"Ollama completion timeout: {e}")
            raise AITimeoutError("Ollama completion timed out") from e
        except Exception as e:
            message = str(e) or "Unknown Ollama error"

            # If you ever get policy blocks from an upstream guard, make them terminal
            if _is_policy_violation(message):
                self.logger.error(f"Ollama policy violation: {message}")
                raise AIResponseError(
                    f"Ollama content policy violation: {message}",
                    error_category="ai_error"
                ) from e

            # Otherwise treat as provider-side failure
            self.logger.error(f"Ollama completion error: {message}")
            raise ProviderError(
                f"Ollama provider error: {message}",
                code="ollama_error"
            ) from e

    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to a single prompt for Ollama."""
        prompt_parts = []

        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant:")  # Prompt for the model to continue
        return "\n\n".join(prompt_parts)

    async def query(self, prompt: str, **kwargs) -> str:
        """
        Simple query interface for single prompts.

        Args:
            prompt: The user prompt
            **kwargs: Additional completion parameters

        Returns:
            The AI response as a string
        """
        messages = [{"role": "user", "content": prompt}]
        result = await self.complete(messages, **kwargs)
        return result.get('content', '')

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Chat interface with optional system message.

        Args:
            messages: Conversation history
            system_message: Optional system message
            **kwargs: Additional completion parameters

        Returns:
            The AI response as a string
        """
        full_messages = []

        if system_message:
            full_messages.append({"role": "system", "content": system_message})

        full_messages.extend(messages)

        result = await self.complete(full_messages, **kwargs)
        return result.get('content', '')

    async def search_and_answer(self, query: str, context: str = "") -> str:
        """
        Answer a query with optional context for search-like functionality.

        Args:
            query: The search query or question
            context: Additional context for the response

        Returns:
            The AI response
        """
        system_prompt = """You are an AI assistant helping to answer questions and search queries.
        When answering:
        1. Be accurate and informative
        2. If you don't have current information, say so
        3. Provide helpful suggestions for finding current information
        4. Format your response clearly"""

        user_prompt = f"Query: {query}"
        if context:
            user_prompt += f"\n\nAdditional context: {context}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = await self.complete(messages)
        return result.get('content', '')

    def is_configured(self) -> bool:
        """Check if the provider is properly configured (Ollama should be running)."""
        # For Ollama, we just need the service to be running
        # We'll do a quick health check
        return True  # Assume configured, will fail gracefully if not

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the Ollama API."""
        try:
            # Check if Ollama service is running
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    models_data = await response.json()
                    models = [m.get('name') for m in models_data.get('models', [])]

                    return {
                        'status': 'healthy',
                        'service': 'running',
                        'available_models': models,
                        'default_model': self.default_model,
                        'endpoint': self.base_url
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'error': f'HTTP {response.status}',
                        'endpoint': self.base_url
                    }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'endpoint': self.base_url,
                'suggestion': 'Make sure Ollama is installed and running (ollama serve)'
            }

    async def list_models(self) -> List[str]:
        """List available models in Ollama."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    models_data = await response.json()
                    return [m.get('name') for m in models_data.get('models', [])]
                return []
        except Exception as e:
            self.logger.error(f"Failed to list models: {e}")
            return []

    async def pull_model(self, model_name: str) -> bool:
        """
        Pull/download a model from Ollama library.

        Args:
            model_name: Name of the model to pull

        Returns:
            True if successful, False otherwise
        """
        try:
            data = {"name": model_name}
            response = await self._make_request("/api/pull", data)
            return response.get('status') == 'success'
        except Exception as e:
            self.logger.error(f"Failed to pull model {model_name}: {e}")
            return False

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    def __del__(self):
        """Cleanup when provider is destroyed."""
        if self.session and not self.session.closed:
            asyncio.create_task(self.session.close())
