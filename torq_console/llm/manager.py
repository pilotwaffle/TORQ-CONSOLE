"""
LLM Manager for TORQ CONSOLE.

Central orchestration layer that manages multiple LLM providers and routes queries
to the appropriate provider based on the request type and available models.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional, Union
import logging

from .providers.deepseek import DeepSeekProvider
from .providers.claude import ClaudeProvider


class LLMManager:
    """Central manager for all LLM providers and operations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM Manager with provider configuration.

        Args:
            config: Configuration dictionary for providers
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize providers
        self.providers = {}
        self.default_provider = 'claude'  # Use Claude as default for best quality
        self.search_provider = 'deepseek'  # Use DeepSeek for fast searches

        # Initialize providers
        self._init_claude()
        self._init_deepseek()

        # Provider aliases for backward compatibility
        self.provider_aliases = {
            'claude': 'claude',
            'claude-sonnet': 'claude',
            'sonnet': 'claude',
            'deepseek': 'deepseek',
            'deepseek-chat': 'deepseek',
            'llama': 'deepseek',
            'default': self.default_provider,
            'search': self.search_provider
        }

        self.logger.info(f"LLM Manager initialized with providers: {list(self.providers.keys())}")

    def _init_claude(self):
        """Initialize Claude provider."""
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            model = self.config.get('claude_model', 'claude-sonnet-4-20250514')

            provider = ClaudeProvider(api_key=api_key, model=model)
            self.providers['claude'] = provider

            if provider.is_configured():
                self.logger.info(f"Claude provider configured successfully with model: {model}")
            else:
                self.logger.warning("Claude provider not properly configured (missing API key)")

        except Exception as e:
            self.logger.error(f"Failed to initialize Claude provider: {e}")

    def _init_deepseek(self):
        """Initialize DeepSeek provider."""
        try:
            # Try to get from environment or use a placeholder
            api_key = os.getenv('DEEPSEEK_API_KEY')
            base_url = "https://api.deepseek.com"

            provider = DeepSeekProvider(api_key=api_key, base_url=base_url)
            self.providers['deepseek'] = provider

            if provider.is_configured():
                self.logger.info("DeepSeek provider configured successfully")
            else:
                self.logger.warning("DeepSeek provider not properly configured (missing API key)")

        except Exception as e:
            self.logger.error(f"Failed to initialize DeepSeek provider: {e}")

    def get_provider(self, name: str) -> Optional[Any]:
        """Get a provider by name or alias."""
        # Resolve alias
        resolved_name = self.provider_aliases.get(name, name)

        provider = self.providers.get(resolved_name)
        if not provider:
            self.logger.warning(f"Provider '{name}' not found, using default: {self.default_provider}")
            provider = self.providers.get(self.default_provider)

        return provider

    async def query(self, provider_name: str, prompt: str, **kwargs) -> str:
        """
        Execute a query using the specified provider.

        Args:
            provider_name: Name of the provider to use
            prompt: The query prompt
            **kwargs: Additional parameters for the provider

        Returns:
            The response string
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return f"Error: Provider '{provider_name}' not available"

        try:
            response = await provider.query(prompt, **kwargs)
            return response
        except Exception as e:
            self.logger.error(f"Query failed with provider {provider_name}: {e}")
            return f"I apologize, but I encountered an error: {e}"

    async def chat(
        self,
        provider_name: str,
        messages: List[Dict[str, str]],
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Execute a chat using the specified provider.

        Args:
            provider_name: Name of the provider to use
            messages: Conversation history
            system_message: Optional system message
            **kwargs: Additional parameters

        Returns:
            The response string
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return f"Error: Provider '{provider_name}' not available"

        try:
            response = await provider.chat(messages, system_message, **kwargs)
            return response
        except Exception as e:
            self.logger.error(f"Chat failed with provider {provider_name}: {e}")
            return f"I apologize, but I encountered an error: {e}"

    async def search_query(self, query: str, provider_name: Optional[str] = None) -> str:
        """
        Handle search-like queries with enhanced AI assistance.

        Args:
            query: The search query
            provider_name: Optional provider to use (defaults to best available)

        Returns:
            AI-generated response to the search query
        """
        # Choose the best provider for search queries
        if not provider_name:
            provider_name = self.default_provider

        provider = self.get_provider(provider_name)
        if not provider:
            return f"Error: No suitable provider available for search queries"

        try:
            # Use the provider's search_and_answer method if available
            if hasattr(provider, 'search_and_answer'):
                response = await provider.search_and_answer(query)
            else:
                # Fallback to regular query
                enhanced_prompt = f"""Please help answer this query: {query}

If this is asking for recent information (like news, current events, etc.), please:
1. Acknowledge that you may not have the most current information
2. Provide any relevant background information you do have
3. Suggest ways to find current information
4. Be helpful while being honest about your limitations

If this is a general question, please answer it as helpfully as possible."""

                response = await provider.query(enhanced_prompt)

            return response

        except Exception as e:
            self.logger.error(f"Search query failed: {e}")
            return f"I apologize, but I encountered an error while processing your search: {e}"

    async def ai_news_query(self, query: str) -> str:
        """
        Handle AI news queries with specialized prompting.

        Args:
            query: The AI news query

        Returns:
            Formatted AI news response
        """
        system_message = """You are an AI assistant specializing in artificial intelligence news and developments.

When asked about AI news:
1. Acknowledge your knowledge cutoff date
2. Provide relevant context about recent AI developments that you're aware of
3. Mention major AI companies and their typical areas of focus
4. Suggest reliable sources for current AI news
5. Be informative but honest about temporal limitations

Format your response clearly with sections if appropriate."""

        enhanced_query = f"""The user is asking about: {query}

Please provide:
- Any relevant AI developments you're aware of
- Context about major AI companies and trends
- Suggestions for finding the most current AI news
- General insights about the AI field related to their query"""

        provider = self.get_provider(self.default_provider)
        if not provider:
            return "Error: No AI provider available"

        try:
            if hasattr(provider, 'chat'):
                messages = [{"role": "user", "content": enhanced_query}]
                response = await provider.chat(messages, system_message)
            else:
                response = await provider.query(f"{system_message}\n\n{enhanced_query}")

            return response

        except Exception as e:
            self.logger.error(f"AI news query failed: {e}")
            return f"I apologize, but I encountered an error while fetching AI news: {e}"

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health checks on all providers.

        Returns:
            Dictionary with health status of each provider
        """
        results = {}

        for name, provider in self.providers.items():
            try:
                if hasattr(provider, 'health_check'):
                    health = await provider.health_check()
                    results[name] = health
                else:
                    # Basic health check
                    test_response = await provider.query("Test")
                    results[name] = {
                        'status': 'healthy' if test_response else 'unhealthy',
                        'configured': hasattr(provider, 'is_configured') and provider.is_configured()
                    }
            except Exception as e:
                results[name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }

        return results

    def list_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available providers and their status.

        Returns:
            Dictionary with provider information
        """
        provider_info = {}

        for name, provider in self.providers.items():
            info = {
                'name': name,
                'class': provider.__class__.__name__,
                'configured': hasattr(provider, 'is_configured') and provider.is_configured(),
                'default': name == self.default_provider
            }

            # Add provider-specific info
            if hasattr(provider, 'default_model'):
                info['default_model'] = provider.default_model

            provider_info[name] = info

        return provider_info

    async def switch_default_provider(self, provider_name: str) -> bool:
        """
        Switch the default provider.

        Args:
            provider_name: Name of the provider to set as default

        Returns:
            True if successful, False otherwise
        """
        provider = self.get_provider(provider_name)
        if provider and provider_name in self.providers:
            self.default_provider = provider_name
            self.logger.info(f"Switched default provider to: {provider_name}")
            return True
        else:
            self.logger.warning(f"Cannot switch to provider '{provider_name}' - not available")
            return False