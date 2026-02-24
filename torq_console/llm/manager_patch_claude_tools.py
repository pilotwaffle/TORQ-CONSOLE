"""
Patch to LLM Manager for Claude Tool Use Provider support.

This patch adds initialization of the ClaudeToolUseProvider alongside
the standard Claude provider.

To apply this patch, import and call patch_manager() after initializing LLMManager,
or add the _init_claude_tool_use method to LLMManager and call it in __init__.
"""

import os
import logging
from typing import Dict, Any, Optional


def patch_manager(manager_instance) -> bool:
    """
    Patch an existing LLMManager instance to add Claude Tool Use support.

    Args:
        manager_instance: An LLMManager instance

    Returns:
        True if patching succeeded, False otherwise
    """
    try:
        from torq_console.llm.providers.claude_with_tools import ClaudeToolUseProvider

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            logging.warning("ANTHROPIC_API_KEY not set - skipping Claude Tool Use provider")
            return False

        model = manager_instance.config.get('claude_model', 'claude-sonnet-4-6')
        config = {
            'api_key': api_key,
            'model': model,
            'tool_use_enabled': True,
            'computer_use_enabled': False
        }

        provider = ClaudeToolUseProvider(config=config)

        # Register the provider
        manager_instance.providers['claude_tools'] = provider
        manager_instance.provider_aliases['claude_tools'] = 'claude_tools'
        manager_instance.provider_aliases['claude-with-tools'] = 'claude_tools'
        manager_instance.provider_aliases['research'] = 'claude_tools'

        logging.info(f"Claude Tool Use provider initialized with model: {model}")
        logging.info(f"Available tools: {provider.get_tool_status()['available_tools']}")

        return True

    except ImportError as e:
        logging.warning(f"Could not import ClaudeToolUseProvider: {e}")
        return False
    except Exception as e:
        logging.error(f"Failed to initialize Claude Tool Use provider: {e}")
        return False


def get_claude_tool_use_provider(manager_instance) -> Optional['ClaudeToolUseProvider']:
    """
    Get the Claude Tool Use provider from an LLMManager instance.

    Args:
        manager_instance: An LLMManager instance

    Returns:
        ClaudeToolUseProvider instance or None
    """
    return manager_instance.providers.get('claude_tools')
