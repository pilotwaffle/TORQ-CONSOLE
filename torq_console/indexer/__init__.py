"""
Codebase Indexer Module for TORQ Console.

Provides semantic code search capabilities using:
- File scanning with .gitignore support
- Code parsing and extraction
- Sentence-BERT embeddings
- FAISS vector store
- <500ms semantic search
"""

from .code_scanner import CodeScanner
from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore
from .semantic_search import SemanticSearch

__all__ = [
    'CodeScanner',
    'EmbeddingGenerator',
    'VectorStore',
    'SemanticSearch'
]
