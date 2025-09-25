"""
LLM (Large Language Model) integration module for TORQ CONSOLE.

This module provides:
- Unified interface for multiple LLM providers (DeepSeek, OpenAI, etc.)
- Web search integration capabilities
- Multi-agent swarm intelligence coordination
- Context-aware response generation
"""

from .manager import LLMManager
from .providers.deepseek import DeepSeekProvider

__all__ = ['LLMManager', 'DeepSeekProvider']
__version__ = '1.0.0'