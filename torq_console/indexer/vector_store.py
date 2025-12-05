"""
Vector Store - FAISS-based vector database for fast similarity search.

Provides <500ms semantic search over code embeddings using FAISS.
"""

import logging
import pickle
import threading
from typing import List, Dict, Tuple, Optional
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS vector database for semantic code search with thread-safety."""

    def __init__(self, dimension: int = 384):
        """
        Initialize vector store.

        Args:
            dimension: Embedding dimension (384 for all-MiniLM-L6-v2)
        """
        self.dimension = dimension
        self.index = None
        self.documents = []
        self._lock = threading.RLock()  # Thread-safe operations
        self._init_index()

    def _init_index(self):
        """Initialize FAISS index."""
        try:
            import faiss
            # Use IndexFlatL2 for exact search (fast for <100K vectors)
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"Initialized FAISS index (dimension={self.dimension})")
        except ImportError:
            logger.error("faiss-cpu not installed")
            raise ImportError("Install with: pip install faiss-cpu")

    def add_vectors(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict]
    ):
        """
        Add embeddings to the index (thread-safe).

        Args:
            embeddings: NumPy array of embeddings (N x dimension)
            metadata: List of metadata dicts for each embedding
        """
        if len(embeddings) == 0:
            logger.warning("No embeddings to add")
            return

        if len(embeddings) != len(metadata):
            raise ValueError("Embeddings and metadata must have same length")

        with self._lock:
            # Ensure correct dtype and shape
            embeddings = np.ascontiguousarray(embeddings.astype('float32'))

            # Add to FAISS index
            self.index.add(embeddings)
            self.documents.extend(metadata)

            logger.info(
                f"Added {len(embeddings)} vectors. "
                f"Total: {self.index.ntotal} vectors"
            )

    def remove_vectors(self, indices: List[int]):
        """
        Remove vectors by indices (thread-safe).

        Note: FAISS IndexFlatL2 doesn't support direct removal.
        This rebuilds the index without the specified indices.

        Args:
            indices: List of document indices to remove
        """
        with self._lock:
            if not indices:
                logger.warning("No indices to remove")
                return

            # Get current embeddings
            if self.index.ntotal == 0:
                logger.warning("Index is empty, nothing to remove")
                return

            # Create set of indices to remove for fast lookup
            remove_set = set(indices)

            # Filter documents and rebuild
            new_documents = []
            keep_indices = []

            for i, doc in enumerate(self.documents):
                if i not in remove_set:
                    new_documents.append(doc)
                    keep_indices.append(i)

            if not keep_indices:
                # All vectors removed, clear index
                self.clear()
                return

            # Reconstruct embeddings for kept documents
            # Note: This is inefficient for large indices
            # Consider using IndexIDMap for production use
            logger.warning(
                f"Removing {len(indices)} vectors requires index rebuild. "
                "Consider using IndexIDMap for frequent deletions."
            )

            # Get all vectors (FAISS-specific method)
            all_vectors = self.index.reconstruct_n(0, self.index.ntotal)
            kept_vectors = all_vectors[keep_indices]

            # Rebuild index
            self._init_index()
            self.documents = []

            # Re-add kept vectors
            if len(kept_vectors) > 0:
                self.add_vectors(kept_vectors, new_documents)

            logger.info(f"Removed {len(indices)} vectors")

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 10
    ) -> List[Tuple[Dict, float]]:
        """
        Search for top-K similar documents (thread-safe).

        Args:
            query_embedding: Query embedding (dimension,)
            k: Number of results to return

        Returns:
            List of (document_metadata, distance) tuples
        """
        with self._lock:
            if self.index.ntotal == 0:
                logger.warning("Index is empty")
                return []

            # Ensure correct shape and dtype
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)
            query_embedding = query_embedding.astype('float32')

            # Search
            k = min(k, self.index.ntotal)  # Can't retrieve more than we have
            distances, indices = self.index.search(query_embedding, k)

            # Format results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(self.documents):
                    results.append((self.documents[idx], float(dist)))

            return results

    def batch_search(
        self,
        query_embeddings: np.ndarray,
        k: int = 10
    ) -> List[List[Tuple[Dict, float]]]:
        """
        Batch search for multiple queries (thread-safe).

        Args:
            query_embeddings: Array of query embeddings (N x dimension)
            k: Number of results per query

        Returns:
            List of result lists, one per query
        """
        with self._lock:
            if self.index.ntotal == 0:
                logger.warning("Index is empty")
                return [[] for _ in range(len(query_embeddings))]

            # Ensure correct shape and dtype
            if query_embeddings.ndim == 1:
                query_embeddings = query_embeddings.reshape(1, -1)
            query_embeddings = query_embeddings.astype('float32')

            # Search
            k = min(k, self.index.ntotal)
            distances, indices = self.index.search(query_embeddings, k)

            # Format results
            all_results = []
            for query_dists, query_indices in zip(distances, indices):
                results = []
                for dist, idx in zip(query_dists, query_indices):
                    if idx < len(self.documents):
                        results.append((self.documents[idx], float(dist)))
                all_results.append(results)

            return all_results

    def save(self, path: str):
        """
        Save index and documents to disk (thread-safe).

        Args:
            path: Directory path to save to
        """
        with self._lock:
            try:
                import faiss
                save_path = Path(path)
                save_path.mkdir(parents=True, exist_ok=True)

                # Save FAISS index
                index_file = save_path / 'index.faiss'
                faiss.write_index(self.index, str(index_file))

                # Save documents
                docs_file = save_path / 'documents.pkl'
                with open(docs_file, 'wb') as f:
                    pickle.dump(self.documents, f)

                logger.info(f"Saved index to {path}")
            except Exception as e:
                logger.error(f"Failed to save index: {e}")
                raise

    def load(self, path: str):
        """
        Load index and documents from disk (thread-safe).

        Args:
            path: Directory path to load from
        """
        with self._lock:
            try:
                import faiss
                load_path = Path(path)

                # Load FAISS index
                index_file = load_path / 'index.faiss'
                if not index_file.exists():
                    raise FileNotFoundError(f"Index file not found: {index_file}")
                self.index = faiss.read_index(str(index_file))

                # Load documents with security check
                docs_file = load_path / 'documents.pkl'
                if not docs_file.exists():
                    raise FileNotFoundError(f"Documents file not found: {docs_file}")
                
                # Security check: Verify file permissions (Unix systems)
                if hasattr(docs_file, 'stat'):
                    file_stat = docs_file.stat()
                    import os
                    if os.name != 'nt' and (file_stat.st_mode & 0o002):  # world-writable
                        logger.warning(
                            f"Security Warning: {docs_file} is world-writable. "
                            "Refusing to load pickle file that could be tampered with."
                        )
                        raise PermissionError(f"Insecure file permissions on {docs_file}")
                
                # Load pickle file from trusted source
                with open(docs_file, 'rb') as f:
                    self.documents = pickle.load(f)

                logger.info(f"Loaded index from {path} ({self.index.ntotal} vectors)")
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
                raise

    def get_stats(self) -> Dict:
        """Get vector store statistics (thread-safe)."""
        with self._lock:
            return {
                'total_vectors': self.index.ntotal if self.index else 0,
                'dimension': self.dimension,
                'total_documents': len(self.documents)
            }

    def clear(self):
        """Clear all vectors and documents (thread-safe)."""
        with self._lock:
            self._init_index()
            self.documents = []
            logger.info("Cleared vector store")

    def get_document_by_index(self, index: int) -> Optional[Dict]:
        """
        Get document metadata by index (thread-safe).

        Args:
            index: Document index

        Returns:
            Document metadata or None if index out of range
        """
        with self._lock:
            if 0 <= index < len(self.documents):
                return self.documents[index]
            return None

    def get_all_documents(self) -> List[Dict]:
        """Get all document metadata (thread-safe)."""
        with self._lock:
            return self.documents.copy()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create vector store
    store = VectorStore(dimension=384)

    # Add some vectors
    embeddings = np.random.randn(10, 384).astype('float32')
    metadata = [{'id': i, 'name': f'doc_{i}'} for i in range(10)]
    store.add_vectors(embeddings, metadata)

    # Search
    query = np.random.randn(384).astype('float32')
    results = store.search(query, k=5)
    logger.info(f"Found {len(results)} results")

    # Get stats
    stats = store.get_stats()
    logger.info(f"Stats: {stats}")

    # Test thread safety (basic check)
    import concurrent.futures

    def search_task(i):
        query = np.random.randn(384).astype('float32')
        return store.search(query, k=3)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(search_task, i) for i in range(10)]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            logger.info(f"Concurrent search returned {len(result)} results")
