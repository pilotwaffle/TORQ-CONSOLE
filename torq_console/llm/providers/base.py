"""
Base LLM provider interface for TORQ Console.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import asyncio


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.model_name = self.config.get('model_name', 'default')
        self.api_key = self.config.get('api_key')

    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a chat completion response."""
        pass

    @property
    def name(self) -> str:
        """Return the provider name."""
        return self.__class__.__name__.replace('Provider', '').lower()

    def is_available(self) -> bool:
        """Check if the provider is available."""
        return self.api_key is not None

    async def validate_connection(self) -> bool:
        """Validate connection to the LLM service."""
        try:
            response = await self.generate_response("test", max_tokens=10)
            return response is not None
        except Exception:
            return False

    @abstractmethod
    async def query(self, prompt: str, **kwargs) -> str:
        """Simple query interface for single prompts."""
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        """Return provider capabilities."""
        return {
            'chat_completion': True,
            'text_generation': True,
            'streaming': False,
            'max_tokens': self.config.get('max_tokens', 4096)
        }


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""

    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a mock response."""
        return f"Mock response to: {prompt[:50]}..."

    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a mock chat completion."""
        last_message = messages[-1] if messages else {"content": ""}
        return f"Mock chat response to: {last_message.get('content', '')[:50]}..."

    async def query(self, prompt: str, **kwargs) -> str:
        """Simple mock query interface."""
        return f"Mock response to query: {prompt[:50]}..."

    def get_capabilities(self) -> Dict[str, Any]:
        """Return mock capabilities."""
        return {
            'chat_completion': True,
            'text_generation': True,
            'streaming': False,
            'max_tokens': 1000,
            'mock_provider': True
        }