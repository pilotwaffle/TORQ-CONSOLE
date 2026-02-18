"""
DeepSeek API Provider for TORQ CONSOLE.

This module implements the DeepSeek API integration with:
- OpenAI-compatible API format
- Proper error handling and retries
- Rate limiting and timeout management
- Streaming response support
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
import logging
import aiohttp
from datetime import datetime, timedelta

# Import typed exceptions for proper error classification
from torq_console.generation_meta import AIResponseError, AITimeoutError, ProviderError


def _is_policy_violation(error: Exception) -> bool:
    """
    Detect if a DeepSeek error represents a content policy/safety violation.

    These should be terminal (no fallback) to prevent circumventing safety filters.
    """
    error_str = str(error).lower()

    policy_markers = [
        "content policy",
        "safety",
        "against our policies",
        "policy violation",
        "inappropriate content",
        "safety guidelines",
        "violates content policy",
        "content moderation",
        "safety filter",
    ]

    return any(marker in error_str for marker in policy_markers)


class DeepSeekProvider:
    """DeepSeek API provider with OpenAI-compatible interface."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com"):
        """
        Initialize DeepSeek provider.

        Args:
            api_key: DeepSeek API key (if None, loads from DEEPSEEK_API_KEY env var)
            base_url: DeepSeek API base URL
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.base_url = base_url.rstrip('/')
        self.logger = logging.getLogger(__name__)

        # Rate limiting
        self.max_requests_per_minute = 60
        self.request_timestamps = []

        # Default configuration (optimized for speed)
        self.default_model = "deepseek-chat"
        self.default_max_tokens = 512  # Reduced from 4096 for faster responses
        self.default_temperature = 0.7

        # Connection pooling session (reuse for better performance)
        self.session = None

        # Validate API key
        if not self.api_key:
            self.logger.warning("No DeepSeek API key found. Set DEEPSEEK_API_KEY environment variable.")

        self.logger.info(f"DeepSeek provider initialized with base URL: {base_url}")

    async def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.now()
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if now - ts < timedelta(minutes=1)
        ]

        if len(self.request_timestamps) >= self.max_requests_per_minute:
            return False

        self.request_timestamps.append(now)
        return True

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create persistent session for connection pooling."""
        if self.session is None or self.session.closed:
            # Create persistent session with extended timeouts for complex synthesis
            timeout = aiohttp.ClientTimeout(
                total=120,     # Total timeout - increased for complex tasks
                connect=10,    # Connection timeout
                sock_read=90   # Socket read timeout - increased for LLM synthesis
            )
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _make_request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to DeepSeek API.

        Note: Internal retry logic removed - fallback layer handles retries.
        This method raises typed exceptions for proper error classification.
        """
        import time

        if not self.api_key:
            raise ProviderError("DeepSeek API key not configured", code="401")

        # Check rate limiting
        if not await self._check_rate_limit():
            raise ProviderError("Rate limit exceeded", code="429")

        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "TORQ-CONSOLE/0.70.0"
        }

        try:
            # Add timing diagnostics
            start_time = time.time()

            # Use persistent session for connection pooling
            session = await self._get_session()
            async with session.post(url, json=data, headers=headers) as response:
                # Read response before checking status
                response_text = await response.text()

                end_time = time.time()
                response_time = end_time - start_time

                if response.status == 200:
                    response_data = json.loads(response_text)
                    self.logger.info(f"DeepSeek API response time: {response_time:.2f}s")
                    return response_data
                else:
                    # Parse error from response
                    try:
                        response_data = json.loads(response_text)
                        error_msg = response_data.get('error', {}).get('message', response_text)
                    except json.JSONDecodeError:
                        error_msg = response_text

                    # Check for content policy violations first (terminal, no fallback)
                    if _is_policy_violation(error_msg):
                        self.logger.error(f"Content policy violation: {error_msg}")
                        raise AIResponseError(
                            f"Content policy violation: {error_msg}",
                            error_category="ai_error"
                        )

                    # Map HTTP status codes to appropriate error types
                    if response.status == 429:
                        self.logger.error(f"DeepSeek rate limited: {error_msg}")
                        raise ProviderError(f"Rate limited: {error_msg}", code="429")
                    elif response.status >= 500:
                        self.logger.error(f"DeepSeek server error: {error_msg}")
                        raise ProviderError(f"Server error: {error_msg}", code=str(response.status))
                    elif response.status in [400, 401, 403, 404]:
                        # 400 with policy already handled above
                        # 401, 403, 404 are provider errors
                        self.logger.error(f"DeepSeek provider error: {error_msg}")
                        raise ProviderError(f"Provider error: {error_msg}", code=str(response.status))
                    else:
                        self.logger.error(f"DeepSeek API error: {error_msg}")
                        raise ProviderError(f"API error: {error_msg}", code=str(response.status))

        except asyncio.TimeoutError:
            self.logger.error("DeepSeek request timed out")
            raise AITimeoutError("DeepSeek request timed out")
        except aiohttp.ClientError as e:
            self.logger.error(f"DeepSeek network error: {e}")
            raise ProviderError(f"Network error: {str(e)}", code="network_error")
        except (AIResponseError, AITimeoutError, ProviderError):
            # Re-raise our typed exceptions
            raise
        except Exception as e:
            self.logger.error(f"DeepSeek adapter exception: {e}")
            raise ProviderError(f"DeepSeek adapter exception: {str(e)}", code="adapter_error")

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
        Generate completion using DeepSeek API.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name (default: deepseek-chat)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to use streaming (not yet implemented)
            **kwargs: Additional API parameters

        Returns:
            Response dictionary with completion
        """

        # Prepare request data
        data = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature or self.default_temperature,
            "stream": stream,
            **kwargs
        }

        try:
            self.logger.debug(f"Making completion request with {len(messages)} messages")
            response = await self._make_request("/v1/chat/completions", data)

            # Extract content from response
            if response.get('choices') and len(response['choices']) > 0:
                choice = response['choices'][0]
                if choice.get('message') and choice['message'].get('content'):
                    return {
                        'content': choice['message']['content'],
                        'model': response.get('model', model),
                        'usage': response.get('usage', {}),
                        'finish_reason': choice.get('finish_reason'),
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

        except asyncio.TimeoutError:
            self.logger.error("DeepSeek completion timed out")
            raise AITimeoutError("DeepSeek request timed out")
        except (AIResponseError, AITimeoutError, ProviderError):
            # Re-raise our typed exceptions
            raise
        except Exception as e:
            self.logger.error(f"DeepSeek completion error: {e}")
            raise ProviderError(f"DeepSeek completion error: {str(e)}", code="completion_error")

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
        """Check if the provider is properly configured."""
        return bool(self.api_key)

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the DeepSeek API."""
        try:
            response = await self.query("Hello! Please respond with 'OK' if you're working correctly.")

            is_healthy = 'ok' in response.lower()

            return {
                'status': 'healthy' if is_healthy else 'degraded',
                'response_time': 'measured',  # We could add actual timing
                'api_key_configured': bool(self.api_key),
                'last_response': response[:100] + '...' if len(response) > 100 else response
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'api_key_configured': bool(self.api_key)
            }