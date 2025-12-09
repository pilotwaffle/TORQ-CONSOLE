"""
Anthropic LLM Provider for TORQ Console
Provides integration with Anthropic's Claude models
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
import anthropic
from anthropic import AsyncAnthropic

class AnthropicProvider:
    """Anthropic Claude LLM Provider"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize Anthropic provider"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url or os.getenv("ANTHROPIC_BASE_URL")
        self.client = AsyncAnthropic(api_key=self.api_key, base_url=self.base_url)
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs
    ) -> str:
        """Generate text using Claude"""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or 4096,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                stream=stream,
                **kwargs
            )

            if stream:
                return response
            else:
                return response.content[0].text

        except Exception as e:
            raise Exception(f"Anthropic generation failed: {str(e)}")

    async def embed(
        self,
        text: str,
        model: str = "claude-3-sonnet-20240229"
    ) -> List[float]:
        """
        Note: Claude models don't natively support embeddings.
        This would require integration with Anthropic's embedding API or
        using a different service.
        """
        # For now, return a placeholder or use OpenAI for embeddings
        from .openai import get_openai_provider
        provider = get_openai_provider()
        return await provider.embed(text)

    def get_available_models(self) -> List[str]:
        """Get list of available Claude models"""
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]

    async def test_connection(self) -> bool:
        """Test if the connection to Anthropic works"""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except:
            return False

    async def count_tokens(self, text: str) -> int:
        """Count tokens in text using Claude's tokenization"""
        try:
            # Claude has a different tokenization approach
            # Approximate: 1 token ≈ 4 characters for Claude
            return len(text) // 4
        except:
            # Fallback estimation
            return len(text.split())

# Provider instance
_anthropic_provider: Optional[AnthropicProvider] = None

def get_anthropic_provider() -> AnthropicProvider:
    """Get or create Anthropic provider instance"""
    global _anthropic_provider
    if _anthropic_provider is None:
        _anthropic_provider = AnthropicProvider()
    return _anthropic_provider

async def generate_with_claude(
    prompt: str,
    **kwargs
) -> str:
    """Convenience function to generate text with Claude"""
    provider = get_anthropic_provider()
    return await provider.generate(prompt, **kwargs)

async def embed_with_anthropic(
    text: str,
    model: str = "text-embedding-3-small"
) -> List[float]:
    """Convenience function to generate embeddings (uses OpenAI backend)"""
    provider = get_anthropic_provider()
    return await provider.embed(text, model)