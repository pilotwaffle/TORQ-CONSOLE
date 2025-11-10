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
from .providers.ollama import OllamaProvider
from .providers.glm import GLMProvider

# Session 3: Make llama_cpp optional
try:
    from .providers.llama_cpp_provider import LlamaCppProvider
    LLAMA_CPP_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    LLAMA_CPP_AVAILABLE = False
    LlamaCppProvider = None

# Session 3: Semantic Search Integration
from torq_console.indexer.semantic_search import SemanticSearch


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
        self.local_provider = 'ollama'  # Use Ollama for local inference

        # Initialize providers
        self._init_claude()
        self._init_deepseek()
        self._init_ollama()
        self._init_llama_cpp()
        self._init_glm()

        # Session 3: Initialize codebase indexer (optional)
        self.semantic_search = None
        self._init_codebase_indexer()

        # Provider aliases for backward compatibility
        self.provider_aliases = {
            'claude': 'claude',
            'claude-sonnet': 'claude',
            'sonnet': 'claude',
            'deepseek': 'deepseek',
            'deepseek-chat': 'deepseek',
            'glm': 'glm',
            'glm-4.6': 'glm',
            'glm-4': 'glm',
            'ollama': 'ollama',
            'local': 'ollama',
            'llama': 'ollama',
            'mistral': 'ollama',
            'llama_cpp': 'llama_cpp_quality',
            'llama_cpp_fast': 'llama_cpp_fast',
            'llama_cpp_quality': 'llama_cpp_quality',
            'fast': 'llama_cpp_fast',
            'quality': 'llama_cpp_quality',
            'default': self.default_provider,
            'search': self.search_provider,
            'local_llm': self.local_provider
        }

        self.logger.info(f"LLM Manager initialized with providers: {list(self.providers.keys())}")

    def _init_claude(self):
        """Initialize Claude provider."""
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            model = self.config.get('claude_model', 'claude-sonnet-4-20250514')

            # Pass config dict instead of individual parameters
            provider = ClaudeProvider(config={'api_key': api_key, 'model': model})
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

    def _init_ollama(self):
        """Initialize Ollama local LLM provider."""
        try:
            # Get configuration from config or use defaults
            base_url = self.config.get('ollama_base_url', 'http://localhost:11434')
            default_model = self.config.get('ollama_model', 'deepseek-r1:7b')

            self.logger.debug(f"Initializing Ollama provider with base_url={base_url}, model={default_model}")

            provider = OllamaProvider(base_url=base_url, default_model=default_model)
            self.providers['ollama'] = provider

            # Ollama is always "configured" as it's local - it will fail gracefully if not running
            self.logger.info(f"Ollama provider initialized successfully (endpoint: {base_url}, model: {default_model})")

        except ImportError as e:
            self.logger.error(f"Failed to import Ollama provider module: {e}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Ollama provider: {e}", exc_info=True)

    def _init_llama_cpp(self):
        """Initialize llama.cpp local LLM provider for fast inference."""
        try:
            # Check if llama_cpp is available
            if not LLAMA_CPP_AVAILABLE or LlamaCppProvider is None:
                self.logger.info("llama-cpp-python not available - skipping llama.cpp initialization")
                self.logger.info("To enable GPU acceleration, ensure CUDA DLLs are in PATH when launching")
                return

            # Get model path from config or environment
            model_path = self.config.get('llama_cpp_model_path', os.getenv('LLAMA_CPP_MODEL_PATH'))

            if not model_path:
                self.logger.warning("llama.cpp model path not configured - skipping initialization")
                self.logger.info("To enable llama.cpp, set LLAMA_CPP_MODEL_PATH in .env or config")
                return

            # Get configuration parameters
            n_ctx = self.config.get('llama_cpp_n_ctx', int(os.getenv('LLAMA_CPP_N_CTX', '2048')))
            n_gpu_layers = self.config.get('llama_cpp_n_gpu_layers', int(os.getenv('LLAMA_CPP_N_GPU_LAYERS', '0')))
            n_threads = self.config.get('llama_cpp_n_threads', os.getenv('LLAMA_CPP_N_THREADS'))

            if n_threads:
                n_threads = int(n_threads)

            self.logger.debug(f"Initializing llama.cpp provider with model={model_path}, n_ctx={n_ctx}, n_gpu_layers={n_gpu_layers}")

            provider = LlamaCppProvider(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                n_threads=n_threads,
                verbose=False
            )

            # Register two tiers: fast and quality (same instance, different method calls)
            self.providers['llama_cpp_fast'] = provider
            self.providers['llama_cpp_quality'] = provider

            self.logger.info(f"llama.cpp provider initialized (model: {model_path}, ctx: {n_ctx}, GPU layers: {n_gpu_layers})")

        except ImportError as e:
            self.logger.warning(f"llama-cpp-python not installed: {e}")
            self.logger.info("Install with: pip install llama-cpp-python")
        except Exception as e:
            self.logger.error(f"Failed to initialize llama.cpp provider: {e}", exc_info=True)

    def _init_glm(self):
        """Initialize GLM-4.6 provider from Z.AI."""
        try:
            # Try to get from environment
            api_key = os.getenv('GLM_API_KEY')
            model = self.config.get('glm_model', 'glm-4.6')

            provider = GLMProvider(api_key=api_key, model=model)
            self.providers['glm'] = provider

            if provider.is_configured():
                self.logger.info(f"GLM provider configured successfully with model: {model}")
            else:
                self.logger.warning("GLM provider not properly configured (missing GLM_API_KEY)")
                self.logger.info("To enable GLM-4.6, set GLM_API_KEY in .env or environment")

        except Exception as e:
            self.logger.error(f"Failed to initialize GLM provider: {e}")

    def _init_codebase_indexer(self):
        """
        Initialize codebase semantic search indexer (Session 3).

        This is optional and controlled by ENABLE_CODEBASE_INDEXING in .env.
        """
        try:
            # Check if codebase indexing is enabled
            enable_indexing = self.config.get('enable_codebase_indexing', False)

            # Also check environment variable
            if not enable_indexing:
                enable_indexing = os.getenv('ENABLE_CODEBASE_INDEXING', 'false').lower() == 'true'

            if not enable_indexing:
                self.logger.debug("Codebase indexing disabled (set ENABLE_CODEBASE_INDEXING=true to enable)")
                return

            # Get codebase path from config or environment
            codebase_path = self.config.get('codebase_path', os.getenv('CODEBASE_PATH', os.getcwd()))

            self.logger.info(f"Initializing codebase indexer for: {codebase_path}")

            # Initialize semantic search with auto-indexing disabled (will index on first search)
            self.semantic_search = SemanticSearch(
                codebase_path=codebase_path,
                auto_index=False
            )

            self.logger.info(f"Codebase indexer initialized successfully for {codebase_path}")

        except Exception as e:
            self.logger.warning(f"Failed to initialize codebase indexer: {e}")
            self.semantic_search = None

    def search_codebase(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search codebase for relevant code structures.

        Args:
            query: Natural language search query
            k: Number of results to return (default: 5)

        Returns:
            List of matching code structures with relevance scores

        Example:
            >>> results = manager.search_codebase("user authentication function", k=5)
            >>> for result in results:
            ...     print(f"{result['name']} - {result['relevance_score']:.2f}")
        """
        if self.semantic_search is None:
            self.logger.debug("Codebase indexer not available")
            return []

        try:
            # Index on first search if not already indexed
            if not self.semantic_search.indexed:
                self.logger.info("Indexing codebase on first search...")
                self.semantic_search.index_codebase()

            results = self.semantic_search.search(query, k=k)
            self.logger.debug(f"Codebase search returned {len(results)} results for query: {query}")
            return results

        except Exception as e:
            self.logger.error(f"Codebase search failed: {e}")
            return []

    def enrich_with_codebase_context(self, query: str, max_context: int = 2000) -> str:
        """
        Enrich user query with relevant codebase context.

        Searches the codebase for relevant code structures and prepends them
        as context to the user's query. This enables the LLM to provide
        more accurate, codebase-aware responses.

        Args:
            query: User's natural language query
            max_context: Maximum context length in characters (default: 2000)

        Returns:
            Enhanced query with codebase context prepended, or original query
            if indexer is unavailable

        Example:
            >>> enriched = manager.enrich_with_codebase_context(
            ...     "How does authentication work?",
            ...     max_context=2000
            ... )
            >>> response = await manager.query('claude', enriched)
        """
        if self.semantic_search is None:
            self.logger.debug("Codebase indexer not available, returning original query")
            return query

        try:
            # Search for relevant code
            results = self.search_codebase(query, k=5)

            if not results:
                self.logger.debug("No codebase context found for query")
                return query

            # Format context for LLM
            context = self.semantic_search.format_context_for_llm(results, max_context)

            if context:
                enriched_query = f"{context}\n\nUser Query: {query}"
                self.logger.info(
                    f"Enriched query with {len(results)} code snippets "
                    f"({len(context)} chars of context)"
                )
                return enriched_query

            return query

        except Exception as e:
            self.logger.error(f"Failed to enrich query with codebase context: {e}")
            return query

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

    def _should_use_fast_tier(self, messages: List[Dict]) -> bool:
        """
        Determine if query should use fast llama.cpp tier.

        Criteria:
        - Total message content < 200 tokens
        - Simple query patterns (search, find, list, classify, yes/no)
        - No complex reasoning required

        Args:
            messages: List of message dicts

        Returns:
            True if fast tier should be used
        """
        # Calculate approximate token count
        total_chars = sum(len(str(msg.get('content', ''))) for msg in messages)
        approx_tokens = total_chars / 4  # Rough estimate: 1 token = 4 chars

        if approx_tokens > 200:
            return False

        # Check for simple query patterns
        last_message = messages[-1].get('content', '').lower() if messages else ''
        simple_patterns = ['search', 'find', 'list', 'classify', 'is ', 'does ', 'can ', 'what is', 'who is']

        if any(pattern in last_message for pattern in simple_patterns):
            return True

        return False

    def _should_use_balanced_tier(self, messages: List[Dict]) -> bool:
        """
        Determine if query should use balanced llama.cpp tier.

        Criteria:
        - Total message content 200-1000 tokens
        - Medium complexity (synthesis, summarization)
        - Not mission-critical

        Args:
            messages: List of message dicts

        Returns:
            True if balanced tier should be used
        """
        total_chars = sum(len(str(msg.get('content', ''))) for msg in messages)
        approx_tokens = total_chars / 4

        if 200 <= approx_tokens <= 1000:
            return True

        return False

    async def chat_with_routing(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Intelligent routing based on query complexity.

        Routing Logic:
        1. Fast tier (llama.cpp): Simple queries <200 tokens (target: 1-3s)
        2. Balanced tier (llama.cpp): Medium queries 200-1000 tokens (target: 8-15s)
        3. Standard tier (Ollama/DeepSeek): Complex queries >1000 tokens (20-40s)
        4. Premium tier (Claude): Mission-critical or fallback

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters

        Returns:
            Response string
        """
        # Check if fast tier available and appropriate
        if 'llama_cpp_fast' in self.providers and self._should_use_fast_tier(messages):
            try:
                self.logger.info("Routing to fast tier (llama.cpp)")
                provider = self.providers['llama_cpp_fast']
                return await provider.complete_fast(messages, **kwargs)
            except Exception as e:
                self.logger.warning(f"Fast tier failed: {e}, falling back...")

        # Check if balanced tier available and appropriate
        if 'llama_cpp_quality' in self.providers and self._should_use_balanced_tier(messages):
            try:
                self.logger.info("Routing to balanced tier (llama.cpp)")
                provider = self.providers['llama_cpp_quality']
                return await provider.complete_quality(messages, **kwargs)
            except Exception as e:
                self.logger.warning(f"Balanced tier failed: {e}, falling back...")

        # Fall back to existing chat method (Ollama/DeepSeek/Claude)
        self.logger.info("Routing to standard tier (Ollama/DeepSeek/Claude)")

        # Use existing provider selection logic
        if 'deepseek' in self.providers:
            provider_name = 'deepseek'
        elif 'ollama' in self.providers:
            provider_name = 'ollama'
        elif 'claude' in self.providers:
            provider_name = 'claude'
        else:
            raise ValueError("No LLM providers available")

        return await self.chat(provider_name=provider_name, messages=messages, **kwargs)
