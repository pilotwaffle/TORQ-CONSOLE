"""
AI model integration for TORQ CONSOLE.
"""

import logging
import os
from typing import Dict, Any, List, Optional, AsyncGenerator

import httpx
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from ..core.config import TorqConfig, AIModelConfig


logger = logging.getLogger(__name__)


class AIManager:
    """AI model manager for TORQ CONSOLE."""
    
    def __init__(self, config: TorqConfig):
        self.config = config
        self.clients: Dict[str, Any] = {}
        self.ready = False
        
    async def initialize(self) -> None:
        """Initialize AI model clients."""
        logger.info("Initializing AI models...")
        
        for model_config in self.config.ai_models:
            try:
                client = await self._create_client(model_config)
                if client:
                    self.clients[f"{model_config.provider}:{model_config.model}"] = {
                        "client": client,
                        "config": model_config,
                    }
            except Exception as e:
                logger.error(f"Failed to initialize {model_config.provider}:{model_config.model}: {e}")
        
        self.ready = len(self.clients) > 0
        logger.info(f"AI initialization complete. {len(self.clients)} models available.")
    
    async def _create_client(self, config: AIModelConfig) -> Optional[Any]:
        """Create AI client based on provider."""
        if config.provider == "openai":
            if not config.api_key:
                logger.warning(f"No API key for OpenAI model {config.model}")
                return None
            
            return AsyncOpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
            )
        
        elif config.provider == "anthropic":
            if not config.api_key:
                logger.warning(f"No API key for Anthropic model {config.model}")
                return None
            
            return AsyncAnthropic(
                api_key=config.api_key,
            )
        
        elif config.provider == "ollama":
            # Check if Ollama is available
            try:
                base_url = config.base_url or "http://localhost:11434"
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{base_url}/api/version")
                    if response.status_code == 200:
                        return AsyncOpenAI(
                            api_key="dummy",  # Ollama doesn't require API key
                            base_url=f"{base_url}/v1",
                        )
            except Exception as e:
                logger.warning(f"Ollama not available: {e}")
                return None
        
        logger.error(f"Unknown provider: {config.provider}")
        return None
    
    def is_ready(self) -> bool:
        """Check if AI manager is ready."""
        return self.ready
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models."""
        models = []
        for key, client_data in self.clients.items():
            provider, model = key.split(":", 1)
            models.append({
                "provider": provider,
                "model": model,
                "temperature": client_data["config"].temperature,
                "max_tokens": client_data["config"].max_tokens,
            })
        return models
    
    async def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """Generate AI completion."""
        if not self.ready:
            raise RuntimeError("AI manager not ready")
        
        # Use default model if not specified
        if not model:
            model = self.config.default_model
        
        # Find client for model
        client_data = None
        for key, data in self.clients.items():
            if key.endswith(f":{model}") or key == f"openai:{model}" or key == f"anthropic:{model}":
                client_data = data
                break
        
        if not client_data:
            raise ValueError(f"Model {model} not available")
        
        client = client_data["client"]
        config = client_data["config"]
        
        # Use config defaults if parameters not specified
        temperature = temperature or config.temperature
        max_tokens = max_tokens or config.max_tokens
        
        try:
            if config.provider == "openai" or config.provider == "ollama":
                return await self._openai_completion(
                    client, model, prompt, temperature, max_tokens, stream
                )
            elif config.provider == "anthropic":
                return await self._anthropic_completion(
                    client, model, prompt, temperature, max_tokens, stream
                )
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise
    
    async def _openai_completion(
        self,
        client: AsyncOpenAI,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> str | AsyncGenerator[str, None]:
        """Generate OpenAI completion."""
        messages = [{"role": "user", "content": prompt}]
        
        if stream:
            return self._openai_stream(client, model, messages, temperature, max_tokens)
        else:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
    
    async def _openai_stream(
        self,
        client: AsyncOpenAI,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """Stream OpenAI completion."""
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def _anthropic_completion(
        self,
        client: AsyncAnthropic,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> str | AsyncGenerator[str, None]:
        """Generate Anthropic completion."""
        if stream:
            return self._anthropic_stream(client, model, prompt, temperature, max_tokens)
        else:
            response = await client.messages.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.content[0].text
    
    async def _anthropic_stream(
        self,
        client: AsyncAnthropic,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """Stream Anthropic completion."""
        async with client.messages.stream(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            async for chunk in stream.text_stream:
                yield chunk
    
    async def analyze_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Analyze code using AI."""
        prompt = f"""Analyze the following {language} code and provide insights:

{code}

Please provide:
1. Code quality assessment
2. Potential issues or bugs
3. Suggestions for improvement
4. Security considerations
"""
        
        try:
            result = await self.generate_completion(prompt)
            return {
                "analysis": result,
                "language": language,
                "code_length": len(code),
            }
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return {"error": str(e)}
    
    async def suggest_improvements(self, file_content: str, file_path: str) -> Dict[str, Any]:
        """Suggest improvements for a file."""
        prompt = f"""Review the following code from {file_path} and suggest improvements:

{file_content}

Focus on:
1. Code structure and organization
2. Performance optimizations
3. Best practices
4. Readability improvements
"""
        
        try:
            result = await self.generate_completion(prompt)
            return {
                "suggestions": result,
                "file_path": file_path,
            }
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return {"error": str(e)}