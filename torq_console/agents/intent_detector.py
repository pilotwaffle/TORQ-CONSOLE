"""
Production-ready semantic intent detection for Prince Flowers.

Replaces keyword matching with Sentence Transformer-based semantic similarity
to route user queries to the appropriate tool with confidence scoring.

Usage:
    detector = create_intent_detector()
    result = await detector.detect("Create a sunset image")
    if result.confidence >= 0.6:
        route_to_tool(result.tool_name)

Author: Claude Code (Python Expert Agent)
Date: 2025-10-13
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# Tool descriptions optimized for semantic similarity matching
# Focused, concise descriptions for better embedding distinctiveness
TOOL_DESCRIPTIONS = {
    "web_search": (
        "Search the internet and find information online. Look up facts, research topics, "
        "find data, get current information from websites and search engines."
    ),
    "image_generation": (
        "Create images, pictures, photos, artwork, and visual content from text descriptions. "
        "Generate graphics, illustrations, and visualizations."
    ),
    "social_media": (
        "Post and share content to Twitter, Facebook, Instagram, LinkedIn, and other social networks. "
        "Publish updates, tweets, and social media messages."
    ),
    "landing_page_generator": (
        "Create professional landing pages and website HTML from descriptions. Build marketing pages, "
        "product pages, portfolio sites, and web pages with custom styling and layouts."
    ),
    "file_operations": (
        "Read, write, edit, and manage files and documents. Handle text files, configuration files, "
        "data files, and file system operations."
    ),
    "code_generation": (
        "Write and generate code, scripts, and programs in Python, JavaScript, TypeScript, and other "
        "programming languages. Create functions and algorithms."
    ),
    "code_analyzer": (
        "Analyze and explain what code does. Answer questions about functions, understand program behavior, "
        "review code quality, and explain how existing code works."
    ),
    "n8n_workflow": (
        "Create workflow automation and integrations with n8n. Build automation pipelines, "
        "connect services, and orchestrate automated tasks."
    ),
    "browser_automation": (
        "Automate web browsers by clicking buttons, filling forms, navigating pages, and scraping data. "
        "Control browser actions and test web applications."
    ),
    "terminal_commands": (
        "Execute system commands, shell scripts, and terminal operations. Run npm, build scripts, "
        "test commands, install commands, and other command-line tools."
    ),
    "mcp_client": (
        "Connect to Model Context Protocol (MCP) servers and external tools. Access remote capabilities "
        "and integrate with MCP-enabled services."
    ),
    "multi_tool_composition": (
        "Orchestrate and chain multiple tools together in workflows. Execute complex multi-step tasks "
        "by combining different capabilities in sequence or parallel."
    ),
}


@dataclass
class IntentResult:
    """Result of intent detection with metadata.

    Attributes:
        tool_name: Name of detected tool (None if below threshold)
        confidence: Similarity score [0.0, 1.0]
        latency_ms: Detection time in milliseconds
        method: Detection method used (always "embedding")
        top_3: Top 3 candidates with scores [(tool, score), ...]
        cached: Whether result came from cache
    """
    tool_name: Optional[str]
    confidence: float
    latency_ms: float
    method: str = "embedding"
    top_3: List[Tuple[str, float]] = field(default_factory=list)
    cached: bool = False

    def __repr__(self) -> str:
        """Human-readable representation."""
        cache_str = " (cached)" if self.cached else ""
        return (
            f"IntentResult(tool={self.tool_name}, "
            f"confidence={self.confidence:.3f}, "
            f"latency={self.latency_ms:.2f}ms{cache_str})"
        )


class IntentDetector:
    """
    Semantic intent detection using Sentence Transformers.

    Replaces keyword matching with semantic similarity for routing
    user queries to appropriate tools. Uses cosine similarity between
    query embeddings and pre-computed tool description embeddings.

    Features:
        - Async-safe lazy loading (no blocking)
        - LRU caching for repeated queries
        - Confidence thresholding with fallback
        - Performance monitoring (latency, cache hits)
        - Zero-shot detection (no training required)

    Example:
        >>> detector = IntentDetector()
        >>> result = await detector.detect("Create a sunset image")
        >>> print(result.tool_name, result.confidence)
        image_generation 0.823
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        threshold: float = 0.6,
        cache_size: int = 1000,
        tools: Optional[Dict[str, str]] = None,
    ):
        """Initialize intent detector with configuration.

        Args:
            model_name: Sentence transformer model name
            threshold: Minimum confidence score for tool selection
            cache_size: LRU cache size for query results
            tools: Custom tool descriptions (defaults to TOOL_DESCRIPTIONS)
        """
        self.model_name = model_name
        self.threshold = threshold
        self.cache_size = cache_size
        self.tools = tools or TOOL_DESCRIPTIONS

        # Lazy-loaded components
        self._model = None
        self._tool_embeddings = None
        self._tool_names = None
        self._load_lock = asyncio.Lock()

        # Performance tracking
        self._stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "total_latency_ms": 0.0,
            "min_latency_ms": float("inf"),
            "max_latency_ms": 0.0,
            "above_threshold": 0,
            "below_threshold": 0,
        }

        logger.info(
            f"IntentDetector initialized: model={model_name}, "
            f"threshold={threshold}, cache_size={cache_size}, "
            f"tools={len(self.tools)}"
        )

    async def _ensure_loaded(self) -> None:
        """Lazy load model and tool embeddings with async safety.

        Uses asyncio.Lock to prevent multiple simultaneous loads.
        Model loading runs in thread pool to avoid blocking event loop.
        """
        if self._model is not None:
            return

        async with self._load_lock:
            # Double-check after acquiring lock
            if self._model is not None:
                return

            logger.info(f"Loading Sentence Transformer model: {self.model_name}")
            start = time.perf_counter()

            # Load model in thread pool to avoid blocking
            self._model = await asyncio.to_thread(self._load_model_sync)

            # Compute tool embeddings
            self._tool_names = list(self.tools.keys())
            tool_descriptions = [self.tools[name] for name in self._tool_names]
            self._tool_embeddings = await asyncio.to_thread(
                self._model.encode,
                tool_descriptions,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                f"Model loaded successfully in {elapsed:.2f}ms. "
                f"Tool embeddings shape: {self._tool_embeddings.shape}"
            )

    def _load_model_sync(self):
        """Load model synchronously (called from thread pool).

        Returns:
            Loaded SentenceTransformer model
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            logger.error(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
            raise ImportError(
                "sentence-transformers required for intent detection"
            ) from e

        return SentenceTransformer(self.model_name)

    @lru_cache(maxsize=1000)
    def _get_cached_result(self, query: str, threshold: float) -> Tuple[str, float, List[Tuple[str, float]]]:
        """LRU cache wrapper for detection results.

        This method exists only for caching. Actual detection happens
        in _detect_sync(). We cache based on (query, threshold) tuple.

        Note: This is called from detect() after model is loaded.
        """
        # This will be populated by detect() after _detect_sync()
        # The actual caching happens at the function call level
        pass

    def _detect_sync(
        self,
        query: str,
        threshold: float
    ) -> Tuple[Optional[str], float, List[Tuple[str, float]]]:
        """Synchronous detection logic (called from thread pool).

        Args:
            query: User query text
            threshold: Confidence threshold

        Returns:
            Tuple of (tool_name, confidence, top_3_results)
        """
        # Encode query
        query_embedding = self._model.encode(
            [query],
            convert_to_numpy=True,
            show_progress_bar=False,
        )[0]

        # Compute cosine similarities
        similarities = self._cosine_similarity(query_embedding, self._tool_embeddings)

        # Get top 3 results
        top_indices = np.argsort(similarities)[-3:][::-1]
        top_3 = [(self._tool_names[i], float(similarities[i])) for i in top_indices]

        # Select best if above threshold
        best_idx = top_indices[0]
        best_score = similarities[best_idx]
        best_tool = self._tool_names[best_idx] if best_score >= threshold else None

        return best_tool, float(best_score), top_3

    @staticmethod
    def _cosine_similarity(vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between vector and matrix rows.

        Args:
            vec: 1D vector
            matrix: 2D matrix (rows are vectors)

        Returns:
            1D array of similarities
        """
        vec_norm = vec / (np.linalg.norm(vec) + 1e-8)
        matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8)
        return np.dot(matrix_norm, vec_norm)

    async def detect(
        self,
        query: str,
        threshold: Optional[float] = None
    ) -> IntentResult:
        """Detect intent from natural language query.

        Args:
            query: User query text
            threshold: Override default confidence threshold

        Returns:
            IntentResult with detection metadata

        Example:
            >>> result = await detector.detect("Post this to Twitter")
            >>> print(result.tool_name)
            social_media
        """
        start = time.perf_counter()
        threshold = threshold if threshold is not None else self.threshold

        # Ensure model is loaded
        await self._ensure_loaded()

        # Check cache first
        cache_key = (query.strip().lower(), threshold)
        cached_result = None
        try:
            # Check if result is cached by attempting to retrieve
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                tool_name, confidence, top_3 = cached_result
                latency_ms = (time.perf_counter() - start) * 1000
                self._update_stats(latency_ms, confidence >= threshold, True)
                return IntentResult(
                    tool_name=tool_name,
                    confidence=confidence,
                    latency_ms=latency_ms,
                    top_3=top_3,
                    cached=True,
                )
        except Exception:
            # Cache miss or error, proceed with detection
            pass

        # Run detection in thread pool to avoid blocking
        tool_name, confidence, top_3 = await asyncio.to_thread(
            self._detect_sync,
            query,
            threshold
        )

        # Update cache
        self._add_to_cache(cache_key, (tool_name, confidence, top_3))

        # Calculate latency and update stats
        latency_ms = (time.perf_counter() - start) * 1000
        self._update_stats(latency_ms, confidence >= threshold, False)

        logger.debug(
            f"Detected intent: query='{query[:50]}...', "
            f"tool={tool_name}, confidence={confidence:.3f}, "
            f"latency={latency_ms:.2f}ms"
        )

        return IntentResult(
            tool_name=tool_name,
            confidence=confidence,
            latency_ms=latency_ms,
            top_3=top_3,
            cached=False,
        )

    def _get_from_cache(self, key: Tuple[str, float]) -> Optional[Tuple]:
        """Retrieve result from cache.

        Args:
            key: Cache key (query, threshold)

        Returns:
            Cached result or None
        """
        # Implement simple dict-based cache with size limit
        if not hasattr(self, "_cache"):
            self._cache = {}
            self._cache_order = []

        if key in self._cache:
            return self._cache[key]
        return None

    def _add_to_cache(self, key: Tuple[str, float], value: Tuple) -> None:
        """Add result to cache with LRU eviction.

        Args:
            key: Cache key
            value: Result to cache
        """
        if not hasattr(self, "_cache"):
            self._cache = {}
            self._cache_order = []

        # Add to cache
        if key not in self._cache:
            self._cache[key] = value
            self._cache_order.append(key)

            # Evict oldest if over size limit
            if len(self._cache) > self.cache_size:
                oldest = self._cache_order.pop(0)
                del self._cache[oldest]

    def _update_stats(
        self,
        latency_ms: float,
        above_threshold: bool,
        cached: bool
    ) -> None:
        """Update performance statistics.

        Args:
            latency_ms: Query latency
            above_threshold: Whether confidence was above threshold
            cached: Whether result was cached
        """
        self._stats["total_queries"] += 1
        if cached:
            self._stats["cache_hits"] += 1
        self._stats["total_latency_ms"] += latency_ms
        self._stats["min_latency_ms"] = min(self._stats["min_latency_ms"], latency_ms)
        self._stats["max_latency_ms"] = max(self._stats["max_latency_ms"], latency_ms)

        if above_threshold:
            self._stats["above_threshold"] += 1
        else:
            self._stats["below_threshold"] += 1

    def get_stats(self) -> Dict:
        """Get performance statistics.

        Returns:
            Dictionary with performance metrics

        Example:
            >>> stats = detector.get_stats()
            >>> print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
        """
        total = self._stats["total_queries"]
        if total == 0:
            return {
                "total_queries": 0,
                "cache_hit_rate": 0.0,
                "avg_latency_ms": 0.0,
                "min_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "above_threshold_rate": 0.0,
            }

        return {
            "total_queries": total,
            "cache_hits": self._stats["cache_hits"],
            "cache_hit_rate": self._stats["cache_hits"] / total,
            "avg_latency_ms": self._stats["total_latency_ms"] / total,
            "min_latency_ms": self._stats["min_latency_ms"],
            "max_latency_ms": self._stats["max_latency_ms"],
            "above_threshold": self._stats["above_threshold"],
            "below_threshold": self._stats["below_threshold"],
            "above_threshold_rate": self._stats["above_threshold"] / total,
        }

    def reset_stats(self) -> None:
        """Reset performance statistics."""
        self._stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "total_latency_ms": 0.0,
            "min_latency_ms": float("inf"),
            "max_latency_ms": 0.0,
            "above_threshold": 0,
            "below_threshold": 0,
        }
        logger.info("Statistics reset")

    def clear_cache(self) -> None:
        """Clear query result cache."""
        if hasattr(self, "_cache"):
            self._cache.clear()
            self._cache_order.clear()
        logger.info("Cache cleared")


def create_intent_detector(
    model_name: str = "all-MiniLM-L6-v2",
    threshold: float = 0.25,
    cache_size: int = 1000,
    tools: Optional[Dict[str, str]] = None,
) -> IntentDetector:
    """Factory function to create configured intent detector.

    Args:
        model_name: Sentence transformer model (default: all-MiniLM-L6-v2)
        threshold: Confidence threshold (default: 0.25, optimized for natural language)
        cache_size: LRU cache size (default: 1000)
        tools: Custom tool descriptions (default: TOOL_DESCRIPTIONS)

    Returns:
        Configured IntentDetector instance

    Example:
        >>> detector = create_intent_detector(threshold=0.3)
        >>> result = await detector.detect("Generate Python code")

    Note:
        Threshold of 0.25 provides good balance between precision and recall for
        natural language queries. Adjust higher (0.3-0.4) for stricter matching,
        or lower (0.15-0.25) for more lenient matching.
    """
    return IntentDetector(
        model_name=model_name,
        threshold=threshold,
        cache_size=cache_size,
        tools=tools,
    )


# Usage examples
if __name__ == "__main__":
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    async def main():
        """Example usage of IntentDetector."""
        print("=" * 60)
        print("Intent Detector - Usage Examples")
        print("=" * 60)

        # Create detector
        print("\n1. Creating intent detector...")
        detector = create_intent_detector(threshold=0.6)

        # Test queries
        test_queries = [
            "Can you make a picture of a sunset?",
            "Post this to Twitter",
            "Run npm install in the project directory",
            "Create a landing page for my new product",
            "Generate Python code to sort a list",
            "Connect to the database MCP server",
            "First create an image, then post it to social media",
        ]

        print(f"\n2. Testing {len(test_queries)} queries...")
        print("-" * 60)

        for query in test_queries:
            result = await detector.detect(query)
            print(f"\nQuery: {query}")
            print(f"Result: {result}")
            print(f"Top 3: {result.top_3}")

        # Test caching
        print("\n" + "=" * 60)
        print("3. Testing cache performance...")
        print("-" * 60)

        query = "Make a beautiful landscape photo"
        result1 = await detector.detect(query)
        print(f"First call: {result1}")

        result2 = await detector.detect(query)
        print(f"Second call (cached): {result2}")

        # Show statistics
        print("\n" + "=" * 60)
        print("4. Performance Statistics")
        print("-" * 60)
        stats = detector.get_stats()
        for key, value in stats.items():
            if "rate" in key:
                print(f"{key}: {value:.2%}")
            elif "latency" in key or "ms" in key:
                print(f"{key}: {value:.2f}ms")
            else:
                print(f"{key}: {value}")

        print("\n" + "=" * 60)
        print("Done!")
        print("=" * 60)

    # Run async main
    asyncio.run(main())
