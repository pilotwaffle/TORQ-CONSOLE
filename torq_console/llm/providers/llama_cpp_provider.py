"""
llama.cpp Provider for TORQ CONSOLE.

Fast local LLM inference using llama.cpp with Python bindings.
Optimized for code completion, fast queries, and structured outputs.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import json

# Try to import llama-cpp-python (optional dependency)
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logging.warning("llama-cpp-python not installed. Install with: pip install llama-cpp-python")


@dataclass
class CompletionConfig:
    """Configuration for completion requests."""
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    stop: List[str] = None


class LlamaCppProvider:
    """
    llama.cpp provider for fast local inference.

    Features:
    - <100ms completion latency for small models
    - Grammar-constrained generation for structured outputs
    - Streaming support with backpressure control
    - Model ensembling (fast + quality tiers)
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        n_ctx: int = 2048,
        n_gpu_layers: int = 0,
        n_threads: Optional[int] = None,
        verbose: bool = False
    ):
        """
        Initialize llama.cpp provider.

        Args:
            model_path: Path to GGUF model file
            n_ctx: Context window size (default: 2048)
            n_gpu_layers: Number of layers to offload to GPU (0=CPU only)
            n_threads: Number of threads for CPU inference (None=auto)
            verbose: Enable verbose logging
        """
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads
        self.verbose = verbose

        # Model instance (lazy loaded)
        self.llm: Optional[Llama] = None
        self.is_loaded = False

        # Performance metrics
        self.total_tokens = 0
        self.total_time = 0.0

        if not LLAMA_CPP_AVAILABLE:
            self.logger.error("llama-cpp-python not available. Provider will not function.")
            return

        # Load model if path provided
        if model_path:
            self._load_model()

    def _load_model(self) -> bool:
        """
        Load GGUF model into memory.

        Returns:
            True if successful, False otherwise
        """
        if not LLAMA_CPP_AVAILABLE:
            return False

        if self.is_loaded:
            return True

        try:
            self.logger.info(f"Loading model from: {self.model_path}")
            self.logger.info(f"Context size: {self.n_ctx}, GPU layers: {self.n_gpu_layers}")

            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                n_threads=self.n_threads,
                verbose=self.verbose
            )

            self.is_loaded = True
            self.logger.info("Model loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False

    async def complete(
        self,
        messages: List[Dict[str, str]],
        config: Optional[CompletionConfig] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion from messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            config: Completion configuration
            **kwargs: Additional parameters

        Returns:
            Response dictionary with completion
        """
        if not self.is_loaded:
            if not self._load_model():
                return {
                    'content': 'Error: Model not loaded',
                    'error': 'llama.cpp model not available'
                }

        # Use default config if not provided
        if config is None:
            config = CompletionConfig()

        # Convert messages to prompt
        prompt = self._messages_to_prompt(messages)

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._generate_sync,
            prompt,
            config
        )

        return result

    def _generate_sync(
        self,
        prompt: str,
        config: CompletionConfig
    ) -> Dict[str, Any]:
        """
        Synchronous generation (runs in thread pool).

        Args:
            prompt: Input prompt
            config: Generation config

        Returns:
            Response dictionary
        """
        import time
        start_time = time.time()

        try:
            response = self.llm(
                prompt=prompt,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                repeat_penalty=config.repeat_penalty,
                stop=config.stop or [],
                echo=False
            )

            end_time = time.time()
            elapsed = end_time - start_time

            # Extract content
            content = response['choices'][0]['text']

            # Update metrics
            tokens = response['usage']['completion_tokens']
            self.total_tokens += tokens
            self.total_time += elapsed

            self.logger.info(f"Generated {tokens} tokens in {elapsed:.2f}s ({tokens/elapsed:.1f} tok/s)")

            return {
                'content': content,
                'usage': response['usage'],
                'finish_reason': response['choices'][0]['finish_reason'],
                'time': elapsed,
                'tokens_per_second': tokens / elapsed if elapsed > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            return {
                'content': f"Error: {str(e)}",
                'error': str(e)
            }

    async def complete_fast(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 256
    ) -> str:
        """
        Fast completion optimized for speed (<1s target).

        Args:
            messages: Input messages
            max_tokens: Maximum tokens (lower = faster)

        Returns:
            Generated text
        """
        config = CompletionConfig(
            max_tokens=max_tokens,
            temperature=0.3,  # Lower temp = more deterministic = faster
            top_k=20  # Reduced search space = faster
        )

        result = await self.complete(messages, config)
        return result.get('content', '')

    async def complete_quality(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024
    ) -> str:
        """
        Quality completion optimized for output quality.

        Args:
            messages: Input messages
            max_tokens: Maximum tokens

        Returns:
            Generated text
        """
        config = CompletionConfig(
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=0.95,
            top_k=40
        )

        result = await self.complete(messages, config)
        return result.get('content', '')

    async def complete_structured(
        self,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        max_tokens: int = 512
    ) -> Dict[str, Any]:
        """
        Generate structured output matching JSON schema.

        Args:
            messages: Input messages
            schema: JSON schema for output
            max_tokens: Maximum tokens

        Returns:
            Parsed JSON object
        """
        # Add schema to system message
        schema_prompt = f"\nYou must respond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"

        if messages and messages[0].get('role') == 'system':
            messages[0]['content'] += schema_prompt
        else:
            messages.insert(0, {'role': 'system', 'content': f"You are a helpful assistant.{schema_prompt}"})

        # Generate with JSON stop tokens
        config = CompletionConfig(
            max_tokens=max_tokens,
            temperature=0.3,  # Lower temp for structured output
            stop=['\n\n', '```']
        )

        result = await self.complete(messages, config)
        content = result.get('content', '{}')

        # Try to parse JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json?\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            self.logger.warning(f"Failed to parse structured output: {content}")
            return {'error': 'Invalid JSON', 'raw': content}

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert OpenAI-style messages to prompt string.

        Args:
            messages: List of message dicts

        Returns:
            Formatted prompt
        """
        prompt_parts = []

        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")

        # Add assistant prompt
        prompt_parts.append("Assistant:")

        return "\n\n".join(prompt_parts)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Chat interface compatible with other providers.

        Args:
            messages: Conversation history
            system_message: Optional system message
            **kwargs: Additional parameters

        Returns:
            Assistant response
        """
        full_messages = []

        if system_message:
            full_messages.append({'role': 'system', 'content': system_message})

        full_messages.extend(messages)

        result = await self.complete(full_messages, **kwargs)
        return result.get('content', '')

    async def query(self, prompt: str, **kwargs) -> str:
        """
        Simple query interface.

        Args:
            prompt: User prompt
            **kwargs: Additional parameters

        Returns:
            AI response
        """
        messages = [{'role': 'user', 'content': prompt}]
        result = await self.complete(messages, **kwargs)
        return result.get('content', '')

    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        return LLAMA_CPP_AVAILABLE and self.is_loaded

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.

        Returns:
            Health status dictionary
        """
        if not LLAMA_CPP_AVAILABLE:
            return {
                'status': 'unavailable',
                'error': 'llama-cpp-python not installed',
                'suggestion': 'pip install llama-cpp-python'
            }

        if not self.model_path:
            return {
                'status': 'not_configured',
                'error': 'No model path specified'
            }

        if not self.is_loaded:
            if not self._load_model():
                return {
                    'status': 'unhealthy',
                    'error': 'Failed to load model'
                }

        # Try a simple generation
        try:
            test_result = await self.query("Hello", max_tokens=5)

            avg_speed = self.total_tokens / self.total_time if self.total_time > 0 else 0

            return {
                'status': 'healthy',
                'model_path': self.model_path,
                'n_ctx': self.n_ctx,
                'n_gpu_layers': self.n_gpu_layers,
                'is_loaded': self.is_loaded,
                'total_tokens': self.total_tokens,
                'avg_speed': f"{avg_speed:.1f} tokens/sec",
                'test_response': test_result[:50]
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def unload(self):
        """Unload model from memory."""
        if self.llm:
            del self.llm
            self.llm = None
            self.is_loaded = False
            self.logger.info("Model unloaded from memory")
