"""
Integration test for TORQ Console indexer components.

Tests embeddings, vector_store, and semantic_search together.
"""

import logging
import tempfile
import shutil
from pathlib import Path
import numpy as np

from torq_console.indexer.embeddings import EmbeddingGenerator, SimpleEmbeddingGenerator
from torq_console.indexer.vector_store import VectorStore
from torq_console.indexer.semantic_search import SemanticSearch, PerformanceMetrics

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_embeddings():
    """Test embedding generation and similarity computation."""
    logger.info("=== Testing EmbeddingGenerator ===")

    gen = EmbeddingGenerator()

    # Test batch embedding
    texts = [
        "def calculate_sum(a, b): return a + b",
        "class DataProcessor: handles data processing",
        "async def fetch_data(): retrieves remote data"
    ]

    embeddings = gen.generate_embeddings(texts, show_progress=False)
    logger.info(f"Generated {len(embeddings)} embeddings with shape {embeddings.shape}")
    assert embeddings.shape == (3, 384), "Embeddings shape mismatch"

    # Test single embedding
    single = gen.generate_single_embedding(texts[0])
    logger.info(f"Single embedding shape: {single.shape}")
    assert single.shape == (384,), "Single embedding shape mismatch"

    # Test similarity computation
    sim = gen.compute_similarity(embeddings[0], embeddings[1], metric='cosine')
    logger.info(f"Cosine similarity between text 0 and 1: {sim:.4f}")
    assert -1 <= sim <= 1, "Cosine similarity out of range"

    # Test batch similarity
    batch_sims = gen.batch_similarity(embeddings[0], embeddings, metric='cosine')
    logger.info(f"Batch similarities: {batch_sims}")
    assert len(batch_sims) == 3, "Batch similarity count mismatch"

    # Test code formatting
    structure = {
        'type': 'function',
        'name': 'calculate_sum',
        'docstring': 'Calculates the sum of two numbers',
        'file': 'utils.py',
        'code': 'def calculate_sum(a, b):\n    return a + b'
    }
    formatted = gen.format_code_for_embedding(structure)
    logger.info(f"Formatted code: {formatted[:100]}...")
    assert 'function' in formatted and 'calculate_sum' in formatted

    logger.info("EmbeddingGenerator tests PASSED\n")


def test_simple_embeddings():
    """Test simple fallback embedding generator."""
    logger.info("=== Testing SimpleEmbeddingGenerator ===")

    gen = SimpleEmbeddingGenerator(embedding_dim=384)

    texts = [
        "function to process data",
        "class for database operations",
        "utility for error handling"
    ]

    embeddings = gen.generate_embeddings(texts)
    logger.info(f"Generated simple embeddings with shape {embeddings.shape}")
    assert embeddings.shape[0] == 3, "Simple embeddings count mismatch"
    assert embeddings.shape[1] == 384, "Simple embeddings dimension mismatch"

    logger.info("SimpleEmbeddingGenerator tests PASSED\n")


def test_vector_store():
    """Test FAISS vector store operations."""
    logger.info("=== Testing VectorStore ===")

    store = VectorStore(dimension=384)

    # Add vectors
    embeddings = np.random.randn(10, 384).astype('float32')
    metadata = [{'id': i, 'name': f'doc_{i}', 'type': 'function'} for i in range(10)]
    store.add_vectors(embeddings, metadata)

    stats = store.get_stats()
    logger.info(f"Store stats after adding: {stats}")
    assert stats['total_vectors'] == 10, "Vector count mismatch"

    # Search
    query = np.random.randn(384).astype('float32')
    results = store.search(query, k=5)
    logger.info(f"Search returned {len(results)} results")
    assert len(results) == 5, "Search result count mismatch"

    # Test thread-safety with concurrent searches
    import concurrent.futures

    def search_task(i):
        query = np.random.randn(384).astype('float32')
        return store.search(query, k=3)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(search_task, i) for i in range(10)]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            assert len(result) == 3, "Concurrent search result count mismatch"

    logger.info("Thread-safe concurrent searches PASSED")

    # Test save/load
    with tempfile.TemporaryDirectory() as tmpdir:
        store.save(tmpdir)
        logger.info(f"Saved store to {tmpdir}")

        new_store = VectorStore(dimension=384)
        new_store.load(tmpdir)
        new_stats = new_store.get_stats()
        logger.info(f"Loaded store stats: {new_stats}")
        assert new_stats['total_vectors'] == 10, "Loaded vector count mismatch"

    # Test remove_vectors
    store.remove_vectors([0, 1, 2])
    stats = store.get_stats()
    logger.info(f"Stats after removal: {stats}")
    assert stats['total_vectors'] == 7, "Vector count after removal mismatch"

    logger.info("VectorStore tests PASSED\n")


def test_performance_metrics():
    """Test performance metrics tracking."""
    logger.info("=== Testing PerformanceMetrics ===")

    metrics = PerformanceMetrics()

    # Simulate some searches
    metrics.update_search_time(150.5, k=10, filter_type='function')
    metrics.update_search_time(200.3, k=5, filter_type='class')
    metrics.update_search_time(100.2, k=10, filter_type='function')
    metrics.update_search_time(450.8, k=20, filter_type=None)

    metrics_dict = metrics.to_dict()
    logger.info(f"Metrics: {metrics_dict}")

    assert metrics_dict['search']['total_searches'] == 4, "Search count mismatch"
    assert metrics_dict['search']['fastest_search_ms'] == 100.2, "Fastest search mismatch"
    assert metrics_dict['search']['slowest_search_ms'] == 450.8, "Slowest search mismatch"
    assert metrics_dict['search']['p50_search_ms'] > 0, "P50 calculation failed"
    assert metrics_dict['search']['under_500ms_percent'] == 100.0, "Under 500ms percentage wrong"

    logger.info("PerformanceMetrics tests PASSED\n")


def test_semantic_search_integration():
    """Test full semantic search integration."""
    logger.info("=== Testing SemanticSearch Integration ===")

    # Create temporary test codebase
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_code"
        test_dir.mkdir()

        # Create test files
        (test_dir / "utils.py").write_text("""
def calculate_sum(a, b):
    '''Calculate the sum of two numbers.'''
    return a + b

def calculate_product(a, b):
    '''Calculate the product of two numbers.'''
    return a * b
""")

        (test_dir / "database.py").write_text("""
class Database:
    '''Database connection manager.'''

    def connect(self):
        '''Connect to database.'''
        pass

    def disconnect(self):
        '''Disconnect from database.'''
        pass
""")

        # Initialize semantic search
        search = SemanticSearch(
            codebase_path=str(test_dir),
            auto_index=False
        )

        # Index codebase
        logger.info("Indexing test codebase...")
        search.index_codebase()

        stats = search.get_stats()
        logger.info(f"Indexing stats: {stats}")
        assert stats['indexed'], "Codebase not indexed"
        assert stats['files_scanned'] == 2, "File scan count mismatch"

        # Perform search
        results = search.search("calculate numbers", k=5)
        logger.info(f"Search results: {len(results)}")
        assert len(results) > 0, "No search results found"

        for i, result in enumerate(results, 1):
            logger.info(
                f"  {i}. {result.get('type')}: {result.get('name')} "
                f"(relevance: {result.get('relevance_score', 0):.3f})"
            )

        # Test filtering
        func_results = search.search("function", k=5, filter_type='function')
        logger.info(f"Function-only results: {len(func_results)}")
        for result in func_results:
            assert result.get('type') == 'function', "Filter type mismatch"

        # Test LLM context formatting
        context = search.format_context_for_llm(results, max_context_length=1000)
        logger.info(f"LLM context length: {len(context)} chars")
        assert len(context) > 0, "LLM context empty"
        assert "Relevant Code Context" in context, "LLM context format invalid"

        # Test performance metrics
        metrics = search.get_performance_metrics()
        logger.info(f"Performance metrics: {metrics}")
        assert metrics['search']['total_searches'] > 0, "No searches recorded"
        assert metrics['search']['average_search_time_ms'] > 0, "Search time not recorded"
        assert metrics['indexing']['total_structures_indexed'] > 0, "Structures not indexed"

        logger.info("SemanticSearch integration tests PASSED\n")


def main():
    """Run all tests."""
    logger.info("Starting TORQ Console Indexer Integration Tests\n")

    try:
        test_embeddings()
        test_simple_embeddings()
        test_vector_store()
        test_performance_metrics()
        test_semantic_search_integration()

        logger.info("=" * 60)
        logger.info("ALL TESTS PASSED!")
        logger.info("=" * 60)
        return 0
    except Exception as e:
        logger.error(f"TEST FAILED: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
