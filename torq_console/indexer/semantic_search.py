"""
Semantic Search API - High-level interface for code search.

Provides <500ms semantic search over entire codebase with automatic
context formatting for LLM integration.
"""

import logging
import time
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict

from .code_scanner import CodeScanner
from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for semantic search operations."""

    # Indexing metrics
    total_files_scanned: int = 0
    total_functions_found: int = 0
    total_classes_found: int = 0
    total_structures_indexed: int = 0
    indexing_time_seconds: float = 0.0
    embedding_generation_time_seconds: float = 0.0
    index_build_time_seconds: float = 0.0

    # Search metrics
    total_searches: int = 0
    total_search_time_seconds: float = 0.0
    average_search_time_ms: float = 0.0
    fastest_search_ms: float = float('inf')
    slowest_search_ms: float = 0.0
    search_times_ms: List[float] = field(default_factory=list)

    # Query metrics
    queries_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    results_by_k: Dict[int, int] = field(default_factory=lambda: defaultdict(int))

    def update_search_time(self, time_ms: float, k: int = 10, filter_type: Optional[str] = None):
        """Update search time metrics."""
        self.total_searches += 1
        self.total_search_time_seconds += time_ms / 1000.0
        self.search_times_ms.append(time_ms)
        self.fastest_search_ms = min(self.fastest_search_ms, time_ms)
        self.slowest_search_ms = max(self.slowest_search_ms, time_ms)

        # Update average
        if self.total_searches > 0:
            self.average_search_time_ms = (
                self.total_search_time_seconds * 1000.0 / self.total_searches
            )

        # Track query patterns
        if filter_type:
            self.queries_by_type[filter_type] += 1
        self.results_by_k[k] += 1

    def get_percentile(self, percentile: float) -> float:
        """Get percentile of search times."""
        if not self.search_times_ms:
            return 0.0
        sorted_times = sorted(self.search_times_ms)
        idx = int(len(sorted_times) * percentile / 100.0)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            'indexing': {
                'total_files_scanned': self.total_files_scanned,
                'total_functions_found': self.total_functions_found,
                'total_classes_found': self.total_classes_found,
                'total_structures_indexed': self.total_structures_indexed,
                'indexing_time_seconds': round(self.indexing_time_seconds, 2),
                'embedding_generation_time_seconds': round(self.embedding_generation_time_seconds, 2),
                'index_build_time_seconds': round(self.index_build_time_seconds, 2)
            },
            'search': {
                'total_searches': self.total_searches,
                'total_search_time_seconds': round(self.total_search_time_seconds, 4),
                'average_search_time_ms': round(self.average_search_time_ms, 2),
                'fastest_search_ms': round(self.fastest_search_ms, 2) if self.fastest_search_ms != float('inf') else 0.0,
                'slowest_search_ms': round(self.slowest_search_ms, 2),
                'p50_search_ms': round(self.get_percentile(50), 2),
                'p95_search_ms': round(self.get_percentile(95), 2),
                'p99_search_ms': round(self.get_percentile(99), 2),
                'under_500ms_percent': round(
                    sum(1 for t in self.search_times_ms if t < 500) / max(len(self.search_times_ms), 1) * 100,
                    2
                )
            },
            'query_patterns': {
                'queries_by_type': dict(self.queries_by_type),
                'results_by_k': dict(self.results_by_k)
            }
        }


class SemanticSearch:
    """High-level semantic code search API with performance tracking."""

    def __init__(
        self,
        codebase_path: str,
        index_path: Optional[str] = None,
        auto_index: bool = True
    ):
        """
        Initialize semantic search.

        Args:
            codebase_path: Path to codebase root
            index_path: Path to save/load index (default: codebase_path/.torq-index)
            auto_index: Automatically index codebase on init
        """
        self.codebase_path = Path(codebase_path)
        self.index_path = Path(index_path) if index_path else self.codebase_path / '.torq-index'

        # Initialize components
        self.scanner = CodeScanner(str(self.codebase_path))
        self.embedder = EmbeddingGenerator()
        self.vector_store = VectorStore(dimension=self.embedder.embedding_dim)

        self.indexed = False
        self.index_time = None

        # Performance metrics
        self.metrics = PerformanceMetrics()

        # Try to load existing index
        if self.index_path.exists():
            self._load_index()

        # Auto-index if requested and not loaded
        if auto_index and not self.indexed:
            self.index_codebase()

    def index_codebase(self, force: bool = False):
        """
        Index the entire codebase.

        Args:
            force: Force re-indexing even if index exists
        """
        if self.indexed and not force:
            logger.info("Codebase already indexed")
            return

        logger.info(f"Starting codebase indexing: {self.codebase_path}")
        start_time = time.time()

        # Scan codebase
        scan_start = time.time()
        structures = self.scanner.scan_codebase()
        scan_time = time.time() - scan_start
        logger.info(f"Scanned {len(structures)} code structures in {scan_time:.2f}s")

        if not structures:
            logger.warning("No code structures found to index")
            return

        # Format for embedding
        texts = [
            self.embedder.format_code_for_embedding(s)
            for s in structures
        ]

        # Generate embeddings (batch processing)
        logger.info("Generating embeddings...")
        embed_start = time.time()
        embeddings = self.embedder.generate_embeddings(
            texts,
            batch_size=100,
            show_progress=True
        )
        embed_time = time.time() - embed_start
        logger.info(f"Generated embeddings in {embed_time:.2f}s")

        # Add to vector store
        logger.info("Building vector index...")
        index_start = time.time()
        self.vector_store.add_vectors(embeddings, structures)
        index_time = time.time() - index_start
        logger.info(f"Built index in {index_time:.2f}s")

        # Save index
        self._save_index()

        self.indexed = True
        self.index_time = time.time() - start_time

        # Update metrics
        scanner_stats = self.scanner.get_stats()
        self.metrics.total_files_scanned = scanner_stats['files_scanned']
        self.metrics.total_functions_found = scanner_stats['functions_found']
        self.metrics.total_classes_found = scanner_stats['classes_found']
        self.metrics.total_structures_indexed = len(structures)
        self.metrics.indexing_time_seconds = self.index_time
        self.metrics.embedding_generation_time_seconds = embed_time
        self.metrics.index_build_time_seconds = index_time

        logger.info(
            f"Indexing complete in {self.index_time:.2f}s: "
            f"{scanner_stats['files_scanned']} files, "
            f"{scanner_stats['functions_found']} functions, "
            f"{scanner_stats['classes_found']} classes"
        )

    def search(
        self,
        query: str,
        k: int = 10,
        filter_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Semantic search over codebase.

        Args:
            query: Natural language search query
            k: Number of results to return
            filter_type: Filter by type ('function', 'class', 'file')

        Returns:
            List of matching code structures with relevance scores
        """
        if not self.indexed:
            logger.warning("Codebase not indexed yet")
            return []

        start_time = time.time()

        # Generate query embedding
        query_embedding = self.embedder.generate_single_embedding(query)

        # Search vector store
        results = self.vector_store.search(query_embedding, k=k*2)  # Get extra for filtering

        # Filter by type if requested
        if filter_type:
            results = [
                (doc, dist) for doc, dist in results
                if doc.get('type') == filter_type
            ]

        # Limit to k results
        results = results[:k]

        # Format results with relevance scores
        formatted_results = []
        for doc, distance in results:
            # Convert L2 distance to similarity score (0-1, higher is better)
            similarity = 1.0 / (1.0 + distance)

            result = {
                **doc,
                'relevance_score': similarity,
                'distance': distance
            }
            formatted_results.append(result)

        search_time = (time.time() - start_time) * 1000  # Convert to ms

        # Update metrics
        self.metrics.update_search_time(search_time, k, filter_type)

        logger.info(
            f"Search completed in {search_time:.2f}ms "
            f"({len(formatted_results)} results)"
        )

        return formatted_results

    def format_context_for_llm(
        self,
        search_results: List[Dict],
        max_context_length: int = 2000
    ) -> str:
        """
        Format search results as context for LLM.

        Args:
            search_results: Results from search()
            max_context_length: Maximum context length in characters

        Returns:
            Formatted context string
        """
        if not search_results:
            return ""

        context_parts = ["# Relevant Code Context\n"]
        current_length = len(context_parts[0])

        for result in search_results:
            # Format result
            parts = []

            if 'type' in result:
                parts.append(f"## [{result['type'].title()}]")

            if 'name' in result:
                parts.append(f"**{result['name']}**")

            if 'file' in result:
                parts.append(f"\nFile: `{result['file']}`")
            elif 'relative_path' in result:
                parts.append(f"\nFile: `{result['relative_path']}`")

            if 'line' in result:
                parts.append(f" (Line {result['line']})")

            if 'docstring' in result and result['docstring']:
                parts.append(f"\nDocstring: {result['docstring'][:200]}")

            if 'relevance_score' in result:
                parts.append(f"\nRelevance: {result['relevance_score']:.2f}")

            parts.append("\n---\n")

            result_text = " ".join(parts)

            # Check length
            if current_length + len(result_text) > max_context_length:
                break

            context_parts.append(result_text)
            current_length += len(result_text)

        return "\n".join(context_parts)

    def get_stats(self) -> Dict:
        """Get indexer statistics."""
        scanner_stats = self.scanner.get_stats()
        vector_stats = self.vector_store.get_stats()

        return {
            **scanner_stats,
            **vector_stats,
            'indexed': self.indexed,
            'index_time': self.index_time,
            'index_path': str(self.index_path)
        }

    def get_performance_metrics(self) -> Dict:
        """Get detailed performance metrics."""
        return self.metrics.to_dict()

    def reset_metrics(self):
        """Reset performance metrics."""
        self.metrics = PerformanceMetrics()
        logger.info("Performance metrics reset")

    def _save_index(self):
        """Save index to disk."""
        try:
            self.vector_store.save(str(self.index_path))
            logger.info(f"Index saved to {self.index_path}")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def _load_index(self):
        """Load index from disk."""
        try:
            self.vector_store.load(str(self.index_path))
            self.indexed = True
            logger.info(f"Index loaded from {self.index_path}")
        except Exception as e:
            logger.warning(f"Failed to load index: {e}")
            self.indexed = False


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Initialize semantic search
    search = SemanticSearch(
        codebase_path="E:\\TORQ-CONSOLE",
        auto_index=False
    )

    # Index codebase
    logger.info("Indexing codebase...")
    search.index_codebase()

    # Perform searches
    queries = [
        "user authentication function",
        "database connection class",
        "error handling utilities"
    ]

    for query in queries:
        logger.info(f"\nSearching: {query}")
        results = search.search(query, k=5)

        logger.info(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            logger.info(
                f"  {i}. {result.get('type', 'unknown')}: {result.get('name', 'unnamed')} "
                f"(relevance: {result.get('relevance_score', 0):.3f})"
            )

        # Format for LLM
        context = search.format_context_for_llm(results, max_context_length=1000)
        logger.info(f"\nLLM Context ({len(context)} chars):\n{context[:200]}...")

    # Show performance metrics
    logger.info("\n=== Performance Metrics ===")
    metrics = search.get_performance_metrics()
    logger.info(f"Indexing metrics: {metrics['indexing']}")
    logger.info(f"Search metrics: {metrics['search']}")
    logger.info(f"Query patterns: {metrics['query_patterns']}")

    # Get stats
    stats = search.get_stats()
    logger.info(f"\nStats: {stats}")
