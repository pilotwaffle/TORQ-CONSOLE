"""
GLM-4.6 (Z.AI) LLM Client Integration for TORQ Console.

This module provides integration with Z.AI's GLM-4.6 model,
supporting chat completions, streaming, and various advanced features.

GLM-4.6 Features:
- 200K token context window
- 128K max output tokens
- Superior coding performance (par with Claude Sonnet 4)
- Advanced reasoning with integrated tool use
- 30% more efficient token consumption vs GLM-4.5
"""
import os
import logging
from typing import Optional, Dict, Any, List, AsyncIterator
from openai import OpenAI

logger = logging.getLogger("TORQ.LLM.GLM")


class GLMClient:
    """
    Z.AI GLM-4.6 client for TORQ Console.

    Uses OpenAI-compatible API for GLM-4.6:
    - Chat completions
    - Streaming responses
    - Function calling
    - Tool use during inference
    - Code generation excellence
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-4.6",
        base_url: str = "https://api.z.ai/api/paas/v4/"
    ):
        """
        Initialize GLM client.

        Args:
            api_key: Z.AI API key (defaults to GLM_API_KEY env var)
            model: Model to use (default: glm-4.6)
            base_url: API base URL (default: https://api.z.ai/api/paas/v4/)
        """
        self.api_key = api_key or os.getenv("GLM_API_KEY")
        if not self.api_key:
            logger.warning("GLM_API_KEY not set. GLM client may not function properly.")

        self.model = model
        self.base_url = base_url

        # Use OpenAI SDK for Z.AI API compatibility
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        ) if self.api_key else None

        logger.info(f"GLM client initialized with model: {model} at {base_url}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """
        Send chat completion request to GLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters for the API

        Returns:
            Response object or generator for streaming
        """
        if not self.client:
            raise ValueError("GLM client not initialized. Please provide GLM_API_KEY.")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )

            if stream:
                return response

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"GLM API error: {e}")
            raise

    async def chat_async(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """
        Async chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters for the API

        Returns:
            Response object or async generator for streaming
        """
        # ZhipuAI SDK may not have native async support, so we'll use sync for now
        # In production, consider using aiohttp or httpx for true async
        return self.chat(messages, temperature, max_tokens, stream, **kwargs)

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat completion response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API

        Yields:
            Chunks of the response text
        """
        if not self.client:
            raise ValueError("GLM client not initialized. Please provide GLM_API_KEY.")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"GLM streaming error: {e}")
            raise

    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
        **kwargs
    ) -> Any:
        """
        Chat with function/tool calling support.

        Args:
            messages: List of message dicts
            tools: List of tool definitions
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Response with potential tool calls
        """
        if not self.client:
            raise ValueError("GLM client not initialized. Please provide GLM_API_KEY.")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                temperature=temperature,
                **kwargs
            )

            return response

        except Exception as e:
            logger.error(f"GLM tool calling error: {e}")
            raise

    def chat_with_web_search(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Chat with web search enabled.

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Response text with web search augmentation
        """
        # GLM-4 supports web_search tool
        tools = [{
            "type": "web_search",
            "web_search": {
                "enable": True
            }
        }]

        response = self.chat_with_tools(messages, tools, temperature, **kwargs)
        return response.choices[0].message.content

    def get_embeddings(
        self,
        texts: List[str],
        model: str = "embedding-2"
    ) -> List[List[float]]:
        """
        Get text embeddings (if supported by Z.AI endpoint).

        Args:
            texts: List of texts to embed
            model: Embedding model to use

        Returns:
            List of embedding vectors
        """
        if not self.client:
            raise ValueError("GLM client not initialized. Please provide GLM_API_KEY.")

        try:
            # Note: Check Z.AI docs for embedding endpoint availability
            response = self.client.embeddings.create(
                model=model,
                input=texts
            )

            return [item.embedding for item in response.data]

        except Exception as e:
            logger.warning(f"GLM embeddings may not be available: {e}")
            raise


# Global GLM client instance
_glm_client: Optional[GLMClient] = None


def get_glm_client(
    api_key: Optional[str] = None,
    model: str = "glm-4-plus"
) -> GLMClient:
    """
    Get global GLM client instance (singleton).

    Args:
        api_key: Optional API key override
        model: Model to use

    Returns:
        GLMClient instance
    """
    global _glm_client

    if _glm_client is None or api_key:
        _glm_client = GLMClient(api_key=api_key, model=model)

    return _glm_client
