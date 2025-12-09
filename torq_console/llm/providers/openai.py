"""
OpenAI LLM Provider for TORQ Console
Provides integration with OpenAI's language models
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
import openai
from openai import AsyncOpenAI
import anthropic

class OpenAIProvider:
    """OpenAI LLM Provider"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize OpenAI provider"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs
    ) -> str:
        """Generate text using OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream,
                **kwargs
            )

            if stream:
                return response
            else:
                return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"OpenAI generation failed: {str(e)}")

    async def embed(
        self,
        text: str,
        model: str = "text-embedding-3-small"
    ) -> List[float]:
        """Generate embeddings using OpenAI"""
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"OpenAI embedding failed: {str(e)}")

    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "text-embedding-3-small",
            "text-embedding-3-large"
        ]

    async def test_connection(self) -> bool:
        """Test if the connection to OpenAI works"""
        try:
            await self.client.models.list()
            return True
        except:
            return False

# Provider instance
_openai_provider: Optional[OpenAIProvider] = None

def get_openai_provider() -> OpenAIProvider:
    """Get or create OpenAI provider instance"""
    global _openai_provider
    if _openai_provider is None:
        _openai_provider = OpenAIProvider()
    return _openai_provider

async def generate_with_openai(
    prompt: str,
    **kwargs
) -> str:
    """Convenience function to generate text with OpenAI"""
    provider = get_openai_provider()
    return await provider.generate(prompt, **kwargs)

async def embed_with_openai(
    text: str,
    model: str = "text-embedding-3-small"
) -> List[float]:
    """Convenience function to generate embeddings with OpenAI"""
    provider = get_openai_provider()
    return await provider.embed(text, model)