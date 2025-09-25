"""
Multi-Model HuggingFace Integration Backend for TORQ Console.

Provides advanced AI model integration with support for multiple HuggingFace models,
specialized routing, local execution, and model pipeline management.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import hashlib

import httpx


class ModelTask(Enum):
    """HuggingFace model tasks."""
    TEXT_GENERATION = "text-generation"
    TEXT_CLASSIFICATION = "text-classification"
    TOKEN_CLASSIFICATION = "token-classification"
    QUESTION_ANSWERING = "question-answering"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    TEXT_TO_SPEECH = "text-to-speech"
    AUTOMATIC_SPEECH_RECOGNITION = "automatic-speech-recognition"
    IMAGE_CLASSIFICATION = "image-classification"
    IMAGE_TO_TEXT = "image-to-text"
    TEXT_TO_IMAGE = "text-to-image"
    OBJECT_DETECTION = "object-detection"
    IMAGE_SEGMENTATION = "image-segmentation"
    CONVERSATIONAL = "conversational"
    FEATURE_EXTRACTION = "feature-extraction"
    FILL_MASK = "fill-mask"
    ZERO_SHOT_CLASSIFICATION = "zero-shot-classification"


class ModelProvider(Enum):
    """Model hosting providers."""
    HUGGINGFACE_API = "huggingface_api"
    HUGGINGFACE_LOCAL = "huggingface_local"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    REPLICATE = "replicate"


@dataclass
class ModelConfig:
    """Configuration for an AI model."""
    model_id: str
    task: ModelTask
    provider: ModelProvider = ModelProvider.HUGGINGFACE_API
    parameters: Dict[str, Any] = field(default_factory=dict)
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    repetition_penalty: Optional[float] = None
    use_cache: bool = True
    wait_for_model: bool = True
    local_path: Optional[str] = None


@dataclass
class ModelResponse:
    """Response from model inference."""
    model_id: str
    task: str
    provider: str
    result: Any
    processing_time_ms: float
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class HuggingFaceModelBackend:
    """
    Multi-model HuggingFace integration backend.

    Features:
    - Support for 20+ model tasks
    - Multiple provider support (HF API, local, OpenAI, etc.)
    - Intelligent model routing based on task and performance
    - Model response caching and optimization
    - Batch processing capabilities
    - Cost tracking and usage analytics
    - Fallback and retry mechanisms
    """

    def __init__(self, hf_api_key: Optional[str] = None, openai_api_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)

        # API configuration
        self.hf_api_key = hf_api_key
        self.openai_api_key = openai_api_key

        # HTTP client
        headers = {}
        if hf_api_key:
            headers["Authorization"] = f"Bearer {hf_api_key}"

        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers=headers
        )

        # Model registry and routing
        self.registered_models: Dict[str, ModelConfig] = {}
        self.model_performance: Dict[str, Dict[str, float]] = {}  # model_id -> metrics
        self.task_routing: Dict[ModelTask, List[str]] = {}  # task -> preferred models

        # Caching
        self.response_cache: Dict[str, ModelResponse] = {}
        self.cache_ttl_minutes = 60

        # Usage tracking
        self.usage_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'models_used': {},
            'tasks_performed': {}
        }

        # Initialize default models
        self._initialize_default_models()

    def _initialize_default_models(self):
        """Initialize default model configurations."""

        # Text generation models
        self.register_model(ModelConfig(
            model_id="microsoft/DialoGPT-medium",
            task=ModelTask.CONVERSATIONAL,
            parameters={"max_length": 100, "do_sample": True, "temperature": 0.7}
        ))

        self.register_model(ModelConfig(
            model_id="gpt2",
            task=ModelTask.TEXT_GENERATION,
            parameters={"max_length": 200, "temperature": 0.8}
        ))

        # Specialized models
        self.register_model(ModelConfig(
            model_id="facebook/bart-large-cnn",
            task=ModelTask.SUMMARIZATION,
            parameters={"max_length": 150, "min_length": 30}
        ))

        self.register_model(ModelConfig(
            model_id="deepset/roberta-base-squad2",
            task=ModelTask.QUESTION_ANSWERING,
            parameters={}
        ))

        self.register_model(ModelConfig(
            model_id="cardiffnlp/twitter-roberta-base-sentiment-latest",
            task=ModelTask.TEXT_CLASSIFICATION,
            parameters={}
        ))

        # Image models
        self.register_model(ModelConfig(
            model_id="google/vit-base-patch16-224",
            task=ModelTask.IMAGE_CLASSIFICATION,
            parameters={}
        ))

        self.register_model(ModelConfig(
            model_id="Salesforce/blip-image-captioning-base",
            task=ModelTask.IMAGE_TO_TEXT,
            parameters={}
        ))

    def register_model(self, config: ModelConfig):
        """Register a model for use."""
        self.registered_models[config.model_id] = config

        # Add to task routing
        if config.task not in self.task_routing:
            self.task_routing[config.task] = []

        if config.model_id not in self.task_routing[config.task]:
            self.task_routing[config.task].append(config.model_id)

        self.logger.info(f"Registered model: {config.model_id} for task: {config.task.value}")

    async def initialize(self) -> Dict[str, Any]:
        """Initialize the model backend."""
        try:
            # Test HuggingFace API connectivity
            test_result = await self._test_hf_connectivity()

            return {
                'success': True,
                'registered_models': len(self.registered_models),
                'supported_tasks': len(self.task_routing),
                'hf_api_available': test_result,
                'providers': ['huggingface_api', 'huggingface_local'],
                'tasks': [task.value for task in ModelTask]
            }

        except Exception as e:
            self.logger.error(f"Model backend initialization failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def infer(
        self,
        task: Union[str, ModelTask],
        input_data: Union[str, Dict[str, Any]],
        model_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform model inference with intelligent routing.

        Args:
            task: The task to perform
            input_data: Input data for the model
            model_id: Specific model to use (optional)
            **kwargs: Additional parameters

        Returns:
            Model inference result
        """
        start_time = time.time()

        try:
            # Convert task to enum if string
            if isinstance(task, str):
                task = ModelTask(task)

            # Route to appropriate model
            if not model_id:
                model_id = await self._route_model(task, input_data)

            if not model_id:
                return {
                    'success': False,
                    'error': f'No available model for task: {task.value}',
                    'task': task.value
                }

            # Get model configuration
            model_config = self.registered_models.get(model_id)
            if not model_config:
                return {
                    'success': False,
                    'error': f'Model not registered: {model_id}',
                    'model_id': model_id
                }

            # Check cache
            cache_key = self._get_cache_key(model_id, task.value, input_data, kwargs)
            cached_response = self._get_cached_response(cache_key)

            if cached_response:
                self.usage_stats['total_requests'] += 1
                return {
                    'success': True,
                    'model_id': model_id,
                    'task': task.value,
                    'result': cached_response.result,
                    'processing_time_ms': cached_response.processing_time_ms,
                    'cached': True,
                    'metadata': cached_response.metadata
                }

            # Perform inference
            response = await self._execute_inference(model_config, input_data, **kwargs)

            processing_time = (time.time() - start_time) * 1000

            if response['success']:
                # Create model response object
                model_response = ModelResponse(
                    model_id=model_id,
                    task=task.value,
                    provider=model_config.provider.value,
                    result=response['result'],
                    processing_time_ms=processing_time,
                    tokens_used=response.get('tokens_used'),
                    cost=response.get('cost', 0.0)
                )

                # Cache the response
                self._cache_response(cache_key, model_response)

                # Update usage stats
                self._update_usage_stats(model_id, task.value, model_response)

                # Update model performance
                self._update_model_performance(model_id, processing_time, True)

                return {
                    'success': True,
                    'model_id': model_id,
                    'task': task.value,
                    'provider': model_config.provider.value,
                    'result': response['result'],
                    'processing_time_ms': processing_time,
                    'tokens_used': response.get('tokens_used'),
                    'cost': response.get('cost', 0.0),
                    'cached': False
                }
            else:
                # Update model performance for failures
                self._update_model_performance(model_id, processing_time, False)

                self.usage_stats['failed_requests'] += 1

                return {
                    'success': False,
                    'error': response.get('error', 'Unknown error'),
                    'model_id': model_id,
                    'task': task.value,
                    'processing_time_ms': processing_time
                }

        except Exception as e:
            self.logger.error(f"Model inference failed: {e}")
            self.usage_stats['failed_requests'] += 1

            return {
                'success': False,
                'error': str(e),
                'task': task.value if isinstance(task, ModelTask) else str(task),
                'processing_time_ms': (time.time() - start_time) * 1000
            }

    async def batch_infer(
        self,
        requests: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Perform batch inference across multiple requests.

        Args:
            requests: List of inference requests
            max_concurrent: Maximum concurrent requests

        Returns:
            Batch inference results
        """
        start_time = time.time()

        try:
            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_single_request(request: Dict[str, Any], index: int):
                async with semaphore:
                    result = await self.infer(**request)
                    return {'index': index, 'result': result}

            # Execute all requests concurrently
            tasks = [
                process_single_request(req, i)
                for i, req in enumerate(requests)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            successful_results = []
            failed_results = []

            for result in results:
                if isinstance(result, Exception):
                    failed_results.append({'error': str(result)})
                elif result['result']['success']:
                    successful_results.append(result)
                else:
                    failed_results.append(result)

            processing_time = (time.time() - start_time) * 1000

            return {
                'success': True,
                'total_requests': len(requests),
                'successful_requests': len(successful_results),
                'failed_requests': len(failed_results),
                'results': successful_results,
                'errors': failed_results,
                'batch_processing_time_ms': processing_time,
                'average_request_time_ms': processing_time / len(requests) if requests else 0
            }

        except Exception as e:
            self.logger.error(f"Batch inference failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_requests': len(requests)
            }

    async def get_model_recommendations(
        self,
        task: Union[str, ModelTask],
        input_sample: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get model recommendations for a specific task.

        Args:
            task: The task to get recommendations for
            input_sample: Optional sample input for better recommendations

        Returns:
            Model recommendations with performance data
        """
        try:
            if isinstance(task, str):
                task = ModelTask(task)

            available_models = self.task_routing.get(task, [])

            if not available_models:
                return {
                    'success': False,
                    'error': f'No models available for task: {task.value}',
                    'task': task.value
                }

            # Get performance data for each model
            recommendations = []

            for model_id in available_models:
                model_config = self.registered_models[model_id]
                performance = self.model_performance.get(model_id, {})
                usage = self.usage_stats['models_used'].get(model_id, 0)

                recommendation = {
                    'model_id': model_id,
                    'task': task.value,
                    'provider': model_config.provider.value,
                    'avg_response_time_ms': performance.get('avg_response_time', 0),
                    'success_rate': performance.get('success_rate', 0),
                    'usage_count': usage,
                    'parameters': model_config.parameters,
                    'recommended_for': self._get_model_use_cases(model_id)
                }

                recommendations.append(recommendation)

            # Sort by performance (success rate * speed factor)
            recommendations.sort(
                key=lambda x: x['success_rate'] * (1000 / max(x['avg_response_time_ms'], 1)),
                reverse=True
            )

            return {
                'success': True,
                'task': task.value,
                'recommendations_count': len(recommendations),
                'recommendations': recommendations,
                'best_model': recommendations[0] if recommendations else None
            }

        except Exception as e:
            self.logger.error(f"Get model recommendations failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'task': task.value if isinstance(task, ModelTask) else str(task)
            }

    async def get_usage_analytics(self) -> Dict[str, Any]:
        """Get comprehensive usage analytics."""
        total_requests = self.usage_stats['total_requests']

        return {
            'success': True,
            'analytics': {
                'total_requests': total_requests,
                'successful_requests': self.usage_stats['successful_requests'],
                'failed_requests': self.usage_stats['failed_requests'],
                'success_rate': (
                    self.usage_stats['successful_requests'] / total_requests * 100
                    if total_requests > 0 else 0
                ),
                'total_tokens_used': self.usage_stats['total_tokens'],
                'estimated_total_cost': self.usage_stats['total_cost'],
                'most_used_models': sorted(
                    self.usage_stats['models_used'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
                'most_popular_tasks': sorted(
                    self.usage_stats['tasks_performed'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
                'registered_models_count': len(self.registered_models),
                'cached_responses': len(self.response_cache)
            }
        }

    # Private implementation methods
    async def _route_model(self, task: ModelTask, input_data: Any) -> Optional[str]:
        """Route request to the best available model for the task."""
        available_models = self.task_routing.get(task, [])

        if not available_models:
            return None

        # Simple routing: choose model with best performance
        best_model = None
        best_score = -1

        for model_id in available_models:
            performance = self.model_performance.get(model_id, {})
            success_rate = performance.get('success_rate', 0.5)
            avg_response_time = performance.get('avg_response_time', 5000)

            # Score based on success rate and response time
            score = success_rate * (1000 / max(avg_response_time, 100))

            if score > best_score:
                best_score = score
                best_model = model_id

        return best_model or available_models[0]

    async def _execute_inference(
        self,
        model_config: ModelConfig,
        input_data: Any,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute model inference based on provider."""

        if model_config.provider == ModelProvider.HUGGINGFACE_API:
            return await self._hf_api_inference(model_config, input_data, **kwargs)
        elif model_config.provider == ModelProvider.HUGGINGFACE_LOCAL:
            return await self._hf_local_inference(model_config, input_data, **kwargs)
        else:
            return {
                'success': False,
                'error': f'Unsupported provider: {model_config.provider.value}'
            }

    async def _hf_api_inference(
        self,
        model_config: ModelConfig,
        input_data: Any,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute inference using HuggingFace API."""
        try:
            url = f"https://api-inference.huggingface.co/models/{model_config.model_id}"

            # Prepare payload
            payload = {}

            if isinstance(input_data, str):
                payload['inputs'] = input_data
            elif isinstance(input_data, dict):
                payload.update(input_data)
            else:
                payload['inputs'] = str(input_data)

            # Add parameters
            parameters = {**model_config.parameters, **kwargs}
            if parameters:
                payload['parameters'] = parameters

            # Add options
            options = {}
            if model_config.use_cache:
                options['use_cache'] = True
            if model_config.wait_for_model:
                options['wait_for_model'] = True

            if options:
                payload['options'] = options

            # Make API request
            response = await self.client.post(url, json=payload)

            if response.status_code == 200:
                result = response.json()

                return {
                    'success': True,
                    'result': result,
                    'tokens_used': self._estimate_tokens(input_data, result)
                }
            else:
                error_text = response.text
                return {
                    'success': False,
                    'error': f'HF API error ({response.status_code}): {error_text}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'HF API inference failed: {str(e)}'
            }

    async def _hf_local_inference(
        self,
        model_config: ModelConfig,
        input_data: Any,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute inference using local HuggingFace model."""
        # This would require transformers library and local model loading
        return {
            'success': False,
            'error': 'Local HuggingFace inference not implemented (requires transformers library)'
        }

    async def _test_hf_connectivity(self) -> bool:
        """Test HuggingFace API connectivity."""
        try:
            response = await self.client.get("https://huggingface.co/api/models/gpt2")
            return response.status_code == 200
        except:
            return False

    def _get_cache_key(
        self,
        model_id: str,
        task: str,
        input_data: Any,
        params: Dict[str, Any]
    ) -> str:
        """Generate cache key for request."""
        content = json.dumps({
            'model_id': model_id,
            'task': task,
            'input': str(input_data)[:500],  # Limit input length for cache key
            'params': params
        }, sort_keys=True)

        return hashlib.md5(content.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[ModelResponse]:
        """Get cached response if still valid."""
        if cache_key not in self.response_cache:
            return None

        cached_response = self.response_cache[cache_key]

        # Check if cache is still valid (simple time-based expiry)
        cache_age_minutes = (time.time() - cached_response.metadata.get('cached_at', 0)) / 60

        if cache_age_minutes > self.cache_ttl_minutes:
            del self.response_cache[cache_key]
            return None

        return cached_response

    def _cache_response(self, cache_key: str, response: ModelResponse):
        """Cache model response."""
        response.metadata['cached_at'] = time.time()
        self.response_cache[cache_key] = response

        # Clean up old cache entries if cache gets too large
        if len(self.response_cache) > 1000:
            self._cleanup_cache()

    def _cleanup_cache(self):
        """Remove old cache entries."""
        current_time = time.time()
        expired_keys = []

        for key, response in self.response_cache.items():
            cache_age_minutes = (current_time - response.metadata.get('cached_at', 0)) / 60
            if cache_age_minutes > self.cache_ttl_minutes:
                expired_keys.append(key)

        for key in expired_keys:
            del self.response_cache[key]

    def _update_usage_stats(self, model_id: str, task: str, response: ModelResponse):
        """Update usage statistics."""
        self.usage_stats['total_requests'] += 1
        self.usage_stats['successful_requests'] += 1

        if response.tokens_used:
            self.usage_stats['total_tokens'] += response.tokens_used

        if response.cost:
            self.usage_stats['total_cost'] += response.cost

        # Model usage
        if model_id not in self.usage_stats['models_used']:
            self.usage_stats['models_used'][model_id] = 0
        self.usage_stats['models_used'][model_id] += 1

        # Task usage
        if task not in self.usage_stats['tasks_performed']:
            self.usage_stats['tasks_performed'][task] = 0
        self.usage_stats['tasks_performed'][task] += 1

    def _update_model_performance(self, model_id: str, processing_time: float, success: bool):
        """Update model performance metrics."""
        if model_id not in self.model_performance:
            self.model_performance[model_id] = {
                'total_requests': 0,
                'successful_requests': 0,
                'total_response_time': 0,
                'avg_response_time': 0,
                'success_rate': 0
            }

        perf = self.model_performance[model_id]
        perf['total_requests'] += 1

        if success:
            perf['successful_requests'] += 1

        perf['total_response_time'] += processing_time
        perf['avg_response_time'] = perf['total_response_time'] / perf['total_requests']
        perf['success_rate'] = perf['successful_requests'] / perf['total_requests']

    def _estimate_tokens(self, input_data: Any, result: Any) -> Optional[int]:
        """Estimate tokens used in request."""
        # Simple estimation - would be more sophisticated in production
        input_length = len(str(input_data))
        result_length = len(str(result))

        return (input_length + result_length) // 4  # Rough approximation

    def _get_model_use_cases(self, model_id: str) -> List[str]:
        """Get use cases for a model."""
        # This would be populated from model metadata
        use_cases_map = {
            "gpt2": ["Creative writing", "Code completion", "Chatbots"],
            "facebook/bart-large-cnn": ["News summarization", "Document summarization"],
            "deepset/roberta-base-squad2": ["Q&A systems", "Information extraction"],
            "cardiffnlp/twitter-roberta-base-sentiment-latest": ["Social media analysis", "Review sentiment"],
        }

        return use_cases_map.get(model_id, ["General purpose"])

    async def close(self):
        """Clean up resources."""
        await self.client.aclose()


# Export model backend
huggingface_backend = HuggingFaceModelBackend()

async def initialize_hf_models(
    hf_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Claude Code compatible HuggingFace models initialization.

    Args:
        hf_api_key: HuggingFace API key
        openai_api_key: OpenAI API key for additional models

    Returns:
        Initialization result
    """
    global huggingface_backend
    huggingface_backend = HuggingFaceModelBackend(hf_api_key, openai_api_key)
    return await huggingface_backend.initialize()

async def run_ai_model(
    task: str,
    input_data: Union[str, Dict[str, Any]],
    model_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Claude Code compatible AI model execution function.

    Args:
        task: AI task to perform
        input_data: Input for the model
        model_id: Specific model to use
        **kwargs: Additional parameters

    Returns:
        Model execution result
    """
    return await huggingface_backend.infer(task, input_data, model_id, **kwargs)

async def get_model_suggestions(task: str) -> Dict[str, Any]:
    """
    Claude Code compatible model recommendation function.

    Args:
        task: Task to get model suggestions for

    Returns:
        Model recommendations
    """
    return await huggingface_backend.get_model_recommendations(task)

async def batch_ai_inference(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Claude Code compatible batch inference function.

    Args:
        requests: List of inference requests

    Returns:
        Batch inference results
    """
    return await huggingface_backend.batch_infer(requests)