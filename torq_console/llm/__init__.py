"""
LLM (Large Language Model) integration module for TORQ CONSOLE.

This module provides:
- Unified interface for multiple LLM providers (Claude, DeepSeek, OpenAI, Ollama, GLM)
- Web search integration capabilities
- Multi-agent swarm intelligence coordination
- Context-aware response generation
"""

from .manager import LLMManager
from .providers.base import BaseLLMProvider, MockLLMProvider
from .providers.claude import ClaudeProvider
from .providers.deepseek import DeepSeekProvider
from .providers.ollama import OllamaProvider
from .providers.glm import GLMProvider

__all__ = [
    'LLMManager',
    'BaseLLMProvider',
    'MockLLMProvider',
    'ClaudeProvider',
    'DeepSeekProvider',
    'OllamaProvider',
    'GLMProvider'
]
__version__ = '2.0.0'