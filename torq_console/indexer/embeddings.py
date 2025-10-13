"""
Embedding Generator - Creates semantic embeddings using Sentence-BERT.

Generates 384-dimensional embeddings for code structures using the
all-MiniLM-L6-v2 model, optimized for fast inference.
"""

import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate semantic embeddings for code search."""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embedding generator.

        Args:
            model_name: Sentence-BERT model to use
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2

    def _load_model(self):
        """Lazy load the Sentence-BERT model."""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                logger.info("Embedding model loaded successfully")
            except ImportError:
                logger.error("sentence-transformers not installed")
                raise ImportError(
                    "Install with: pip install sentence-transformers"
                )
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise

    def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed
            batch_size: Batch size for processing
            show_progress: Show progress bar

        Returns:
            NumPy array of embeddings (N x embedding_dim)
        """
        if not texts:
            return np.array([])

        self._load_model()

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    def generate_single_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            NumPy array of embedding (embedding_dim,)
        """
        return self.generate_embeddings([text], batch_size=1)[0]

    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
        metric: str = 'cosine'
    ) -> float:
        """
        Compute similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            metric: Similarity metric ('cosine', 'l2', 'dot')

        Returns:
            Similarity score (higher is more similar)
        """
        # Ensure correct shape
        if embedding1.ndim == 1:
            embedding1 = embedding1.reshape(1, -1)
        if embedding2.ndim == 1:
            embedding2 = embedding2.reshape(1, -1)

        if metric == 'cosine':
            # Cosine similarity: [-1, 1], higher is more similar
            dot_product = np.dot(embedding1, embedding2.T)[0, 0]
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            return float(dot_product / (norm1 * norm2 + 1e-8))
        elif metric == 'dot':
            # Dot product similarity
            return float(np.dot(embedding1, embedding2.T)[0, 0])
        elif metric == 'l2':
            # L2 distance converted to similarity (lower distance = higher similarity)
            distance = np.linalg.norm(embedding1 - embedding2)
            return float(1.0 / (1.0 + distance))
        else:
            raise ValueError(f"Unknown metric: {metric}")

    def batch_similarity(
        self,
        query_embedding: np.ndarray,
        embeddings: np.ndarray,
        metric: str = 'cosine'
    ) -> np.ndarray:
        """
        Compute similarity between query and multiple embeddings.

        Args:
            query_embedding: Query embedding vector (embedding_dim,)
            embeddings: Array of embeddings (N x embedding_dim)
            metric: Similarity metric ('cosine', 'l2', 'dot')

        Returns:
            Array of similarity scores (N,)
        """
        if embeddings.shape[0] == 0:
            return np.array([])

        # Ensure correct shape
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        if metric == 'cosine':
            # Batch cosine similarity
            dot_products = np.dot(embeddings, query_embedding.T).flatten()
            query_norm = np.linalg.norm(query_embedding)
            embeddings_norms = np.linalg.norm(embeddings, axis=1)
            return dot_products / (embeddings_norms * query_norm + 1e-8)
        elif metric == 'dot':
            # Batch dot product
            return np.dot(embeddings, query_embedding.T).flatten()
        elif metric == 'l2':
            # Batch L2 distance to similarity
            distances = np.linalg.norm(embeddings - query_embedding, axis=1)
            return 1.0 / (1.0 + distances)
        else:
            raise ValueError(f"Unknown metric: {metric}")

    def format_code_for_embedding(self, structure: dict) -> str:
        """
        Format code structure for embedding generation.

        Args:
            structure: Code structure dict from CodeScanner

        Returns:
            Formatted string for embedding
        """
        parts = []

        # Add type and name
        if 'type' in structure:
            parts.append(f"[{structure['type']}]")
        if 'name' in structure:
            parts.append(structure['name'])

        # Add docstring if available
        if 'docstring' in structure and structure['docstring']:
            parts.append(structure['docstring'])

        # Add file path context
        if 'file' in structure:
            parts.append(f"File: {structure['file']}")
        elif 'relative_path' in structure:
            parts.append(f"File: {structure['relative_path']}")

        # Add code preview for functions/classes
        if 'code' in structure and structure['code']:
            code_preview = structure['code'][:500]  # Limit to 500 chars
            parts.append(f"Code: {code_preview}")

        return " | ".join(parts)

    def get_model_info(self) -> dict:
        """Get embedding model information."""
        self._load_model()
        return {
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
            'max_seq_length': self.model.max_seq_length if self.model else None
        }


class SimpleEmbeddingGenerator:
    """
    Simple fallback embedding generator using TF-IDF.

    Used when Sentence-BERT is unavailable or for testing.
    """

    def __init__(self, embedding_dim: int = 384):
        """
        Initialize simple embedding generator.

        Args:
            embedding_dim: Dimension of output embeddings
        """
        self.embedding_dim = embedding_dim
        self.vectorizer = None
        self.fitted = False
        logger.info("Using simple TF-IDF embedding generator (fallback mode)")

    def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Generate simple TF-IDF based embeddings.

        Args:
            texts: List of text strings to embed
            batch_size: Ignored (for compatibility)
            show_progress: Ignored (for compatibility)

        Returns:
            NumPy array of embeddings (N x embedding_dim)
        """
        if not texts:
            return np.array([])

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import TruncatedSVD
        except ImportError:
            logger.error("scikit-learn not installed for fallback embeddings")
            # Return random embeddings as last resort
            logger.warning("Using random embeddings (install scikit-learn for better fallback)")
            return np.random.randn(len(texts), self.embedding_dim).astype('float32')

        # Fit vectorizer on first use
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(max_features=min(1000, len(texts) * 10))
            self.svd = TruncatedSVD(n_components=min(self.embedding_dim, len(texts) - 1))

            # Fit on texts
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            embeddings = self.svd.fit_transform(tfidf_matrix)

            # Pad to target dimension if needed
            if embeddings.shape[1] < self.embedding_dim:
                padding = np.zeros((embeddings.shape[0], self.embedding_dim - embeddings.shape[1]))
                embeddings = np.hstack([embeddings, padding])

            self.fitted = True
            logger.info(f"Generated {len(embeddings)} simple embeddings")
            return embeddings.astype('float32')
        else:
            # Transform new texts
            tfidf_matrix = self.vectorizer.transform(texts)
            embeddings = self.svd.transform(tfidf_matrix)

            # Pad to target dimension if needed
            if embeddings.shape[1] < self.embedding_dim:
                padding = np.zeros((embeddings.shape[0], self.embedding_dim - embeddings.shape[1]))
                embeddings = np.hstack([embeddings, padding])

            return embeddings.astype('float32')

    def generate_single_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            NumPy array of embedding (embedding_dim,)
        """
        return self.generate_embeddings([text], batch_size=1)[0]

    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
        metric: str = 'cosine'
    ) -> float:
        """Compute similarity between two embeddings (same as EmbeddingGenerator)."""
        # Delegate to main implementation
        gen = EmbeddingGenerator()
        return gen.compute_similarity(embedding1, embedding2, metric)

    def batch_similarity(
        self,
        query_embedding: np.ndarray,
        embeddings: np.ndarray,
        metric: str = 'cosine'
    ) -> np.ndarray:
        """Compute batch similarity (same as EmbeddingGenerator)."""
        # Delegate to main implementation
        gen = EmbeddingGenerator()
        return gen.batch_similarity(query_embedding, embeddings, metric)

    def format_code_for_embedding(self, structure: dict) -> str:
        """Format code structure (same as EmbeddingGenerator)."""
        gen = EmbeddingGenerator()
        return gen.format_code_for_embedding(structure)

    def get_model_info(self) -> dict:
        """Get embedding model information."""
        return {
            'model_name': 'simple-tfidf',
            'embedding_dim': self.embedding_dim,
            'fitted': self.fitted
        }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Test main generator
    gen = EmbeddingGenerator()
    texts = [
        "def calculate_sum(a, b): return a + b",
        "class DataProcessor: handles data processing tasks"
    ]

    embeddings = gen.generate_embeddings(texts, show_progress=False)
    logger.info(f"Generated embeddings shape: {embeddings.shape}")

    # Test similarity
    sim = gen.compute_similarity(embeddings[0], embeddings[1])
    logger.info(f"Similarity between texts: {sim:.4f}")

    # Test fallback generator
    simple_gen = SimpleEmbeddingGenerator()
    simple_embeddings = simple_gen.generate_embeddings(texts)
    logger.info(f"Simple embeddings shape: {simple_embeddings.shape}")
