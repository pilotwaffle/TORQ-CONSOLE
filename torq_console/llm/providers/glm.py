"""
GLM-4.6 Provider for TORQ Console LLM Manager.

Integrates Z.AI's GLM-4.6 model into the unified LLM provider system,
making it accessible via the LLM Manager and UI dropdown.
"""

import os
import logging
from typing import Optional, Dict, Any, List

from .base import LLMProvider
from ..glm_client import GLMClient


logger = logging.getLogger("TORQ.LLM.Providers.GLM")


class GLMProvider(LLMProvider):
    """
    Z.AI GLM-4.6 provider for TORQ Console.

    Provides unified interface to GLM-4.6 through the LLM Manager,
    enabling access via UI dropdown, query routing, and API endpoints.

    Features:
    - 200K token context window
    - 128K max output tokens
    - Superior coding performance (par with Claude Sonnet 4)
    - 30% more efficient token consumption vs GLM-4.5
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-4.6",
        base_url: str = "https://api.z.ai/api/paas/v4/"
    ):
        """
        Initialize GLM provider.

        Args:
            api_key: Z.AI API key (defaults to GLM_API_KEY env var)
            model: Model to use (default: glm-4.6)
            base_url: API base URL
        """
        self.api_key = api_key or os.getenv("GLM_API_KEY")
        self.model = model
        self.base_url = base_url

        # Initialize GLM client
        self.client = GLMClient(
            api_key=self.api_key,
            model=self.model,
            base_url=self.base_url
        )

        logger.info(f"GLM provider initialized with model: {model}")

    def is_configured(self) -> bool:
        """
        Check if provider is properly configured.

        Returns:
            True if GLM_API_KEY is set
        """
        return self.api_key is not None

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """
        Generate response using GLM-4.6.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters

        Returns:
            Response content or generator for streaming
        """
        if not self.is_configured():
            raise ValueError(
                "GLM provider not configured. Please set GLM_API_KEY environment variable."
            )

        try:
            response = self.client.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )

            return response

        except Exception as e:
            logger.error(f"GLM generation error: {e}")
            raise

    async def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Simple chat interface.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Response text
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return await self.generate(messages, temperature, max_tokens, **kwargs)

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the GLM-4.6 model.

        Returns:
            Dict with model information
        """
        return {
            "name": "GLM-4.6",
            "provider": "Z.AI",
            "model_id": self.model,
            "context_window": 200000,  # 200K tokens
            "max_output": 128000,      # 128K tokens
            "capabilities": [
                "chat",
                "code_generation",
                "code_explanation",
                "debugging",
                "large_context",
                "streaming"
            ],
            "strengths": [
                "Superior coding performance",
                "Large context window (200K)",
                "30% more efficient than GLM-4.5",
                "Par with Claude Sonnet 4"
            ],
            "use_cases": [
                "Complex code generation",
                "Large file analysis",
                "Multi-file refactoring",
                "Cost-sensitive coding tasks"
            ]
        }

    def __str__(self) -> str:
        """String representation."""
        configured = "configured" if self.is_configured() else "not configured"
        return f"GLMProvider(model={self.model}, {configured})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"GLMProvider(api_key={'***' if self.api_key else None}, "
            f"model={self.model}, base_url={self.base_url})"
        )
