"""
TORQ CONSOLE Context Management System v0.70.0.

Advanced context management with @-symbol parsing, multi-retriever architecture,
Tree-sitter integration, and memory-efficient caching for enhanced AI pair programming.
"""

import asyncio
import logging
import re
import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor
import weakref
import os

try:
    import tree_sitter
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    tree_sitter = None
    Language = None
    Parser = None

from .config import TorqConfig
from .logger import setup_logger
from .executor_pool import get_executor


@dataclass
class ContextMatch:
    """Represents a context match with metadata."""
    pattern: str
    match_type: str  # 'files', 'code', 'docs', 'git', 'folder'
    content: str
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheEntry:
    """Cache entry with TTL and access tracking."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: int = 3600
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() - self.created_at > timedelta(seconds=self.ttl_seconds)

    def touch(self) -> None:
        """Update access tracking."""
        self.last_accessed = datetime.now()
        self.access_count += 1


class LRUCache:
    """Memory-efficient LRU cache with TTL support."""

    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_memory = 0
        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.cache:
            return None

        entry = self.cache[key]
        if entry.is_expired():
            self._remove_entry(key)
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        entry.touch()
        return entry.value

    def put(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Put value in cache."""
        size_bytes = self._estimate_size(value)

        # Remove existing entry if present
        if key in self.cache:
            self._remove_entry(key)

        # Create new entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=ttl_seconds,
            size_bytes=size_bytes
        )

        # Ensure we have space
        self._ensure_capacity(size_bytes)

        # Add to cache
        self.cache[key] = entry
        self.current_memory += size_bytes

    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache."""
        if key in self.cache:
            entry = self.cache.pop(key)
            self.current_memory -= entry.size_bytes

    def _ensure_capacity(self, new_size: int) -> None:
        """Ensure cache has capacity for new entry."""
        # Remove expired entries first
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            self._remove_entry(key)

        # Remove LRU entries if needed
        while (len(self.cache) >= self.max_size or
               self.current_memory + new_size > self.max_memory_bytes):
            if not self.cache:
                break
            lru_key = next(iter(self.cache))
            self._remove_entry(lru_key)

    def _estimate_size(self, value: Any, seen: Optional[set] = None) -> int:
        """
        Accurately estimate memory size of value using sys.getsizeof.

        Recursively estimates size for containers to prevent underestimation.
        Uses memoization (seen set) to avoid counting shared objects twice.
        """
        if seen is None:
            seen = set()

        # Avoid counting same object multiple times
        obj_id = id(value)
        if obj_id in seen:
            return 0
        seen.add(obj_id)

        try:
            size = sys.getsizeof(value)

            # Recursively estimate container sizes
            if isinstance(value, dict):
                size += sum(self._estimate_size(k, seen) + self._estimate_size(v, seen)
                           for k, v in value.items())
            elif isinstance(value, (list, tuple, set, frozenset)):
                size += sum(self._estimate_size(item, seen) for item in value)
            elif hasattr(value, '__dict__'):
                # Objects with __dict__ (custom classes)
                size += self._estimate_size(value.__dict__, seen)
            elif hasattr(value, '__slots__'):
                # Objects with __slots__
                size += sum(self._estimate_size(getattr(value, slot, None), seen)
                           for slot in value.__slots__ if hasattr(value, slot))

            return size

        except Exception as e:
            # Fallback to conservative estimate
            self.logger.debug(f"Error estimating size: {e}")
            return 1024  # Default size estimate

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.current_memory = 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_accesses = sum(entry.access_count for entry in self.cache.values())
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "memory_used_mb": self.current_memory / (1024 * 1024),
            "memory_limit_mb": self.max_memory_bytes / (1024 * 1024),
            "total_accesses": total_accesses,
            "expired_entries": sum(1 for entry in self.cache.values() if entry.is_expired())
        }


class TreeSitterParser:
    """Tree-sitter integration for code parsing."""

    def __init__(self):
        self.parsers: Dict[str, Parser] = {}
        self.languages: Dict[str, Language] = {}
        self.logger = logging.getLogger(__name__)
        self.available = TREE_SITTER_AVAILABLE

        if self.available:
            self._initialize_languages()

    def _initialize_languages(self) -> None:
        """Initialize Tree-sitter languages."""
        if not TREE_SITTER_AVAILABLE:
            return

        # Language extensions mapping
        self.language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'tsx',
            '.jsx': 'javascript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'c_sharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'bash',
            '.fish': 'bash',
            '.html': 'html',
            '.xml': 'xml',
            '.css': 'css',
            '.scss': 'css',
            '.sass': 'css',
            '.less': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.md': 'markdown',
            '.sql': 'sql'
        }

        # Try to load available languages
        self._load_available_languages()

    def _load_available_languages(self) -> None:
        """Load available Tree-sitter languages."""
        # This would typically load pre-compiled language files
        # For now, we'll simulate availability
        available_langs = ['python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'go', 'rust']

        for lang in available_langs:
            try:
                # In a real implementation, you'd load the actual language
                # self.languages[lang] = Language(f"path/to/{lang}.so")
                # self.parsers[lang] = Parser()
                # self.parsers[lang].set_language(self.languages[lang])
                pass
            except Exception as e:
                self.logger.debug(f"Could not load Tree-sitter language {lang}: {e}")

    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse file using Tree-sitter."""
        if not self.available:
            return None

        try:
            ext = file_path.suffix.lower()
            lang = self.language_map.get(ext)

            if not lang or lang not in self.parsers:
                return None

            with open(file_path, 'rb') as f:
                source_code = f.read()

            # Parse with Tree-sitter
            parser = self.parsers[lang]
            tree = parser.parse(source_code)

            return {
                'language': lang,
                'tree': tree,
                'source': source_code.decode('utf-8', errors='ignore'),
                'symbols': self._extract_symbols(tree, source_code),
                'imports': self._extract_imports(tree, source_code, lang),
                'functions': self._extract_functions(tree, source_code, lang),
                'classes': self._extract_classes(tree, source_code, lang)
            }

        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return None

    def _extract_symbols(self, tree: Any, source: bytes) -> List[Dict[str, Any]]:
        """Extract symbols from parse tree."""
        # This would implement symbol extraction logic
        return []

    def _extract_imports(self, tree: Any, source: bytes, language: str) -> List[str]:
        """Extract import statements."""
        # This would implement import extraction logic
        return []

    def _extract_functions(self, tree: Any, source: bytes, language: str) -> List[Dict[str, Any]]:
        """Extract function definitions."""
        # This would implement function extraction logic
        return []

    def _extract_classes(self, tree: Any, source: bytes, language: str) -> List[Dict[str, Any]]:
        """Extract class definitions."""
        # This would implement class extraction logic
        return []


class AtSymbolParser:
    """Parser for @-symbol patterns in TORQ CONSOLE."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Define @-symbol patterns
        self.patterns = {
            'files': re.compile(r'@files?\s+([^\s]+(?:\s+[^\s@]+)*)', re.IGNORECASE),
            'code': re.compile(r'@code\s+([^\s]+(?:\s+[^\s@]+)*)', re.IGNORECASE),
            'docs': re.compile(r'@docs?\s+([^\s]+(?:\s+[^\s@]+)*)', re.IGNORECASE),
            'git': re.compile(r'@git\s+([^\s]+(?:\s+[^\s@]+)*)', re.IGNORECASE),
            'folder': re.compile(r'@folders?\s+([^\s]+(?:\s+[^\s@]+)*)', re.IGNORECASE)
        }

    def parse(self, text: str) -> List[Tuple[str, str, str]]:
        """Parse @-symbols from text and return matches."""
        matches = []

        for pattern_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                full_match = match.group(0)
                args = match.group(1).strip()
                matches.append((pattern_type, args, full_match))

        return matches

    def extract_file_patterns(self, args: str) -> List[str]:
        """Extract file patterns from arguments."""
        # Handle quoted strings and glob patterns
        patterns = []
        current_pattern = ""
        in_quotes = False
        quote_char = None

        i = 0
        while i < len(args):
            char = args[i]

            if not in_quotes and char in ('"', "'"):
                in_quotes = True
                quote_char = char
            elif in_quotes and char == quote_char:
                in_quotes = False
                quote_char = None
                if current_pattern:
                    patterns.append(current_pattern)
                    current_pattern = ""
            elif in_quotes:
                current_pattern += char
            elif char.isspace():
                if current_pattern:
                    patterns.append(current_pattern)
                    current_pattern = ""
            else:
                current_pattern += char

            i += 1

        if current_pattern:
            patterns.append(current_pattern)

        return patterns


class KeywordRetriever:
    """
    Keyword-based context retrieval with inverted index.

    Uses an inverted index (keyword -> [(file, lines)]) for O(m + k) search
    instead of O(n * terms) file scanning.
    """

    def __init__(self, cache: LRUCache):
        self.cache = cache
        self.logger = logging.getLogger(__name__)
        self.executor = get_executor()

        # Inverted index: keyword -> {file_path: [line_numbers]}
        self.inverted_index: Dict[str, Dict[Path, List[int]]] = {}
        self.index_timestamp: Optional[datetime] = None
        self.index_lock = asyncio.Lock()
        # Rebuild index every 5 minutes or on first search
        self.index_ttl_seconds = 300

    async def _ensure_index_built(self, root_path: Path, file_patterns: List[str] = None) -> None:
        """Ensure inverted index is built and up-to-date."""
        async with self.index_lock:
            # Check if index needs rebuild
            if self.index_timestamp is None or \
               (datetime.now() - self.index_timestamp).total_seconds() > self.index_ttl_seconds:

                self.logger.info("Building inverted index...")
                start_time = datetime.now()

                files_to_index = await self._get_files_to_search(root_path, file_patterns)
                new_index: Dict[str, Dict[Path, List[int]]] = defaultdict(lambda: defaultdict(list))

                # Process files in batches
                for file_path in files_to_index[:500]:  # Index up to 500 files
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                line_lower = line.lower()
                                # Extract words and index them
                                words = re.findall(r'\b\w+\b', line_lower)
                                for word in words:
                                    if len(word) > 2:  # Skip very short words
                                        new_index[word][file_path].append(line_num)
                    except Exception:
                        continue  # Skip problematic files

                self.inverted_index = dict(new_index)
                self.index_timestamp = datetime.now()

                elapsed = (datetime.now() - start_time).total_seconds()
                self.logger.info(f"Inverted index built in {elapsed:.2f}s "
                               f"({len(self.inverted_index)} keywords, {len(files_to_index)} files)")

    async def search(self, query: str, root_path: Path, file_patterns: List[str] = None) -> List[ContextMatch]:
        """Search for keyword matches using inverted index."""
        cache_key = f"keyword:{hashlib.md5(f'{query}:{root_path}:{file_patterns}'.encode()).hexdigest()}"

        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result

        matches = []
        search_terms = self._extract_keywords(query)

        if not search_terms:
            return matches

        try:
            # Ensure index is built
            await self._ensure_index_built(root_path, file_patterns)

            # Use inverted index for O(m + k) lookup instead of O(n * terms) scan
            candidate_files: Dict[Path, Set[int]] = defaultdict(set)

            for term in search_terms:
                term_lower = term.lower()
                if term_lower in self.inverted_index:
                    for file_path, line_numbers in self.inverted_index[term_lower].items():
                        candidate_files[file_path].update(line_numbers)

            # Read only the relevant lines from candidate files
            for file_path, line_numbers in candidate_files.items():
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        for line_num in sorted(line_numbers)[:10]:  # Top 10 lines per file
                            if 0 < line_num <= len(lines):
                                line_content = lines[line_num - 1].strip()
                                # Calculate relevance score
                                score = sum(1 for term in search_terms if term.lower() in line_content.lower())
                                if score > 0:
                                    matches.append(ContextMatch(
                                        pattern=query,
                                        match_type='keyword',
                                        content=line_content,
                                        file_path=file_path,
                                        line_number=line_num,
                                        score=float(score) / len(search_terms)
                                    ))
                except Exception:
                    continue

            # Sort by relevance score
            matches.sort(key=lambda x: x.score, reverse=True)

            # Cache results
            self.cache.put(cache_key, matches[:50], ttl_seconds=1800)  # 30 minutes

        except Exception as e:
            self.logger.error(f"Keyword search error: {e}")

        return matches[:50]  # Return top 50 matches

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query."""
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}

        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]

        return keywords

    async def _get_files_to_search(self, root_path: Path, patterns: List[str] = None) -> List[Path]:
        """Get list of files to search."""
        files = []

        if patterns:
            for pattern in patterns:
                files.extend(root_path.glob(pattern))
        else:
            # Default patterns for common file types
            default_patterns = ['**/*.py', '**/*.js', '**/*.ts', '**/*.java', '**/*.c', '**/*.cpp', '**/*.h', '**/*.hpp', '**/*.go', '**/*.rs', '**/*.rb', '**/*.php', '**/*.cs', '**/*.md', '**/*.txt', '**/*.json', '**/*.yaml', '**/*.yml', '**/*.toml', '**/*.xml', '**/*.html', '**/*.css', '**/*.scss', '**/*.sql']

            for pattern in default_patterns:
                try:
                    files.extend(root_path.glob(pattern))
                except Exception:
                    continue

        # Filter out binary files and large files
        text_files = []
        for file_path in files:
            if file_path.is_file() and self._is_text_file(file_path):
                try:
                    if file_path.stat().st_size < 1024 * 1024:  # 1MB limit
                        text_files.append(file_path)
                except Exception:
                    continue

        return text_files

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is a text file."""
        try:
            # Check by extension first
            text_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.sh', '.bash', '.zsh', '.fish', '.html', '.xml', '.css', '.scss', '.sass', '.less', '.json', '.yaml', '.yml', '.toml', '.md', '.txt', '.sql', '.ini', '.cfg', '.conf', '.log'}

            if file_path.suffix.lower() in text_extensions:
                return True

            # Check by reading first few bytes
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' not in chunk
        except Exception:
            return False

    def _search_file(self, file_path: Path, search_terms: List[str]) -> List[ContextMatch]:
        """Search a single file for keywords."""
        matches = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()
                score = 0
                found_terms = []

                for term in search_terms:
                    if term in line_lower:
                        score += line_lower.count(term)
                        found_terms.append(term)

                if score > 0:
                    match = ContextMatch(
                        pattern=f"keyword:{'+'.join(found_terms)}",
                        match_type='code',
                        content=line.strip(),
                        file_path=file_path,
                        line_number=line_num,
                        score=score,
                        metadata={'found_terms': found_terms}
                    )
                    matches.append(match)

        except Exception as e:
            self.logger.debug(f"Error searching file {file_path}: {e}")

        return matches


class SemanticRetriever:
    """Semantic context retrieval using embeddings."""

    def __init__(self, cache: LRUCache):
        self.cache = cache
        self.logger = logging.getLogger(__name__)
        self.enabled = False  # Disabled by default, requires additional dependencies

    async def search(self, query: str, root_path: Path, file_patterns: List[str] = None) -> List[ContextMatch]:
        """Search for semantic matches."""
        if not self.enabled:
            return []

        # Placeholder for semantic search implementation
        # This would require embedding models and vector search
        return []


class GraphTraversalRetriever:
    """Graph-based context retrieval using code relationships."""

    def __init__(self, cache: LRUCache, tree_parser: TreeSitterParser):
        self.cache = cache
        self.tree_parser = tree_parser
        self.logger = logging.getLogger(__name__)

    async def search(self, query: str, root_path: Path, file_patterns: List[str] = None) -> List[ContextMatch]:
        """Search using graph traversal of code relationships."""
        cache_key = f"graph:{hashlib.md5(f'{query}:{root_path}'.encode()).hexdigest()}"

        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result

        matches = []

        try:
            # Build code dependency graph
            graph = await self._build_dependency_graph(root_path, file_patterns)

            # Find related nodes based on query
            related_nodes = self._find_related_nodes(graph, query)

            # Convert nodes to context matches
            for node in related_nodes:
                match = ContextMatch(
                    pattern=f"graph:{node['type']}",
                    match_type='code',
                    content=node['content'],
                    file_path=Path(node['file']),
                    line_number=node.get('line'),
                    score=node['relevance'],
                    metadata=node.get('metadata', {})
                )
                matches.append(match)

            # Cache results
            self.cache.put(cache_key, matches, ttl_seconds=3600)

        except Exception as e:
            self.logger.error(f"Graph traversal error: {e}")

        return matches

    async def _build_dependency_graph(self, root_path: Path, patterns: List[str] = None) -> Dict[str, Any]:
        """Build dependency graph from code structure."""
        graph = {
            'nodes': {},
            'edges': []
        }

        # This would implement graph building logic
        # For now, return empty graph
        return graph

    def _find_related_nodes(self, graph: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Find nodes related to query using graph traversal."""
        # This would implement graph search algorithms
        return []


class ContextManager:
    """
    Advanced context management system for TORQ CONSOLE v0.70.0.

    Provides @-symbol parsing, multi-retriever architecture, Tree-sitter integration,
    and memory-efficient caching for enhanced AI pair programming.
    """

    def __init__(self, config: TorqConfig, root_path: Path = None):
        self.config = config
        self.root_path = root_path or Path.cwd()
        self.logger = setup_logger("context_manager")

        # Initialize components
        self.cache = LRUCache(max_size=1000, max_memory_mb=100)
        self.at_parser = AtSymbolParser()
        self.tree_parser = TreeSitterParser()

        # Initialize retrievers
        self.keyword_retriever = KeywordRetriever(self.cache)
        self.semantic_retriever = SemanticRetriever(self.cache)
        self.graph_retriever = GraphTraversalRetriever(self.cache, self.tree_parser)

        # Context state
        self.active_contexts: Dict[str, List[ContextMatch]] = {}
        self.context_history: List[Dict[str, Any]] = []

        # Use shared thread pool
        self.executor = get_executor()

        self.logger.info(f"ContextManager initialized at {self.root_path}")

    async def parse_and_retrieve(self, text: str, context_type: str = "mixed") -> Dict[str, List[ContextMatch]]:
        """
        Parse @-symbols and retrieve relevant context.

        Args:
            text: Input text containing @-symbols
            context_type: Type of context retrieval ("keyword", "semantic", "graph", "mixed")

        Returns:
            Dictionary mapping context types to matches
        """
        try:
            # Parse @-symbols
            at_matches = self.at_parser.parse(text)

            if not at_matches:
                # No @-symbols found, use general context retrieval
                return await self._retrieve_general_context(text, context_type)

            # Process each @-symbol match
            results = {}

            for match_type, args, full_match in at_matches:
                self.logger.debug(f"Processing @{match_type}: {args}")

                context_matches = await self._process_at_symbol(match_type, args, context_type)

                if match_type not in results:
                    results[match_type] = []
                results[match_type].extend(context_matches)

            # Store in active contexts
            context_id = self._generate_context_id(text)
            self.active_contexts[context_id] = results

            # Add to history
            self.context_history.append({
                'id': context_id,
                'text': text,
                'results': {k: len(v) for k, v in results.items()},
                'timestamp': datetime.now().isoformat()
            })

            return results

        except Exception as e:
            self.logger.error(f"Error in parse_and_retrieve: {e}")
            return {}

    async def _process_at_symbol(self, match_type: str, args: str, context_type: str) -> List[ContextMatch]:
        """Process a specific @-symbol match."""
        matches = []

        try:
            if match_type == 'files':
                patterns = self.at_parser.extract_file_patterns(args)
                matches = await self._retrieve_file_context(patterns, context_type)

            elif match_type == 'code':
                matches = await self._retrieve_code_context(args, context_type)

            elif match_type == 'docs':
                patterns = self.at_parser.extract_file_patterns(args)
                matches = await self._retrieve_docs_context(patterns, context_type)

            elif match_type == 'git':
                matches = await self._retrieve_git_context(args, context_type)

            elif match_type == 'folder':
                patterns = self.at_parser.extract_file_patterns(args)
                matches = await self._retrieve_folder_context(patterns, context_type)

        except Exception as e:
            self.logger.error(f"Error processing @{match_type}: {e}")

        return matches

    async def _retrieve_file_context(self, patterns: List[str], context_type: str) -> List[ContextMatch]:
        """Retrieve context for @files patterns."""
        all_matches = []

        for pattern in patterns:
            # Convert pattern to file paths
            try:
                if '*' in pattern or '?' in pattern:
                    # Glob pattern
                    files = list(self.root_path.glob(pattern))
                else:
                    # Direct file path
                    file_path = Path(pattern)
                    if not file_path.is_absolute():
                        file_path = self.root_path / file_path
                    files = [file_path] if file_path.exists() else []

                # Create context matches for each file
                for file_path in files:
                    if file_path.is_file():
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()

                            match = ContextMatch(
                                pattern=pattern,
                                match_type='files',
                                content=content,
                                file_path=file_path,
                                score=1.0,
                                metadata={'size': len(content), 'encoding': 'utf-8'}
                            )
                            all_matches.append(match)

                        except Exception as e:
                            self.logger.debug(f"Error reading file {file_path}: {e}")

            except Exception as e:
                self.logger.error(f"Error processing file pattern {pattern}: {e}")

        return all_matches

    async def _retrieve_code_context(self, query: str, context_type: str) -> List[ContextMatch]:
        """Retrieve context for @code queries."""
        matches = []

        # Use appropriate retriever based on context_type
        if context_type in ("keyword", "mixed"):
            keyword_matches = await self.keyword_retriever.search(query, self.root_path)
            matches.extend(keyword_matches)

        if context_type in ("semantic", "mixed"):
            semantic_matches = await self.semantic_retriever.search(query, self.root_path)
            matches.extend(semantic_matches)

        if context_type in ("graph", "mixed"):
            graph_matches = await self.graph_retriever.search(query, self.root_path)
            matches.extend(graph_matches)

        # Remove duplicates and sort by score
        unique_matches = self._deduplicate_matches(matches)
        unique_matches.sort(key=lambda x: x.score, reverse=True)

        return unique_matches[:20]  # Return top 20 matches

    async def _retrieve_docs_context(self, patterns: List[str], context_type: str) -> List[ContextMatch]:
        """Retrieve context for @docs patterns."""
        # Focus on documentation files
        doc_patterns = []
        for pattern in patterns:
            if not any(ext in pattern for ext in ['.md', '.txt', '.rst', '.doc']):
                # Add documentation extensions
                doc_patterns.extend([
                    f"{pattern}*.md",
                    f"{pattern}*.txt",
                    f"{pattern}*.rst",
                    f"*{pattern}*.md",
                    f"*{pattern}*.txt"
                ])
            else:
                doc_patterns.append(pattern)

        return await self._retrieve_file_context(doc_patterns, context_type)

    async def _retrieve_git_context(self, query: str, context_type: str) -> List[ContextMatch]:
        """Retrieve context for @git queries."""
        matches = []

        try:
            # Check if we're in a git repository
            git_dir = self.root_path / '.git'
            if not git_dir.exists():
                return matches

            # This would implement git-specific context retrieval
            # For now, return empty matches
            self.logger.debug(f"Git context retrieval for: {query}")

        except Exception as e:
            self.logger.error(f"Error in git context retrieval: {e}")

        return matches

    async def _retrieve_folder_context(self, patterns: List[str], context_type: str) -> List[ContextMatch]:
        """Retrieve context for @folder patterns."""
        matches = []

        for pattern in patterns:
            try:
                folder_path = Path(pattern)
                if not folder_path.is_absolute():
                    folder_path = self.root_path / folder_path

                if folder_path.exists() and folder_path.is_dir():
                    # Get all files in folder
                    file_patterns = [f"{folder_path}/**/*"]
                    folder_matches = await self._retrieve_file_context(file_patterns, context_type)
                    matches.extend(folder_matches)

            except Exception as e:
                self.logger.error(f"Error processing folder pattern {pattern}: {e}")

        return matches

    async def _retrieve_general_context(self, text: str, context_type: str) -> Dict[str, List[ContextMatch]]:
        """Retrieve general context when no @-symbols are present."""
        matches = await self._retrieve_code_context(text, context_type)
        return {'general': matches}

    def _deduplicate_matches(self, matches: List[ContextMatch]) -> List[ContextMatch]:
        """Remove duplicate matches based on file path and content."""
        seen = set()
        unique_matches = []

        for match in matches:
            key = (str(match.file_path), match.line_number, match.content[:100])
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)

        return unique_matches

    def _generate_context_id(self, text: str) -> str:
        """Generate unique context ID."""
        timestamp = datetime.now().isoformat()
        content = f"{text}:{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

    async def get_active_context(self, context_id: str) -> Optional[Dict[str, List[ContextMatch]]]:
        """Get active context by ID."""
        return self.active_contexts.get(context_id)

    async def clear_context(self, context_id: str = None) -> None:
        """Clear specific context or all contexts."""
        if context_id:
            self.active_contexts.pop(context_id, None)
        else:
            self.active_contexts.clear()

    async def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context state."""
        return {
            'active_contexts': len(self.active_contexts),
            'total_matches': sum(
                sum(len(matches) for matches in ctx.values())
                for ctx in self.active_contexts.values()
            ),
            'cache_stats': self.cache.stats(),
            'tree_sitter_available': self.tree_parser.available,
            'history_entries': len(self.context_history)
        }

    async def export_context(self, context_id: str, format: str = "json") -> Optional[str]:
        """Export context to specified format."""
        context = await self.get_active_context(context_id)
        if not context:
            return None

        try:
            if format == "json":
                # Convert to JSON-serializable format
                export_data = {}
                for ctx_type, matches in context.items():
                    export_data[ctx_type] = [
                        {
                            'pattern': match.pattern,
                            'match_type': match.match_type,
                            'content': match.content[:1000],  # Truncate for export
                            'file_path': str(match.file_path) if match.file_path else None,
                            'line_number': match.line_number,
                            'score': match.score,
                            'timestamp': match.timestamp.isoformat(),
                            'metadata': match.metadata
                        }
                        for match in matches
                    ]
                return json.dumps(export_data, indent=2)

        except Exception as e:
            self.logger.error(f"Error exporting context: {e}")
            return None

    async def shutdown(self) -> None:
        """Cleanup and shutdown context manager."""
        try:
            # Clear caches
            self.cache.clear()

            # Shutdown executor
            self.executor.shutdown(wait=True)

            # Clear active contexts
            self.active_contexts.clear()

            self.logger.info("ContextManager shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during ContextManager shutdown: {e}")

    def get_supported_patterns(self) -> Dict[str, List[str]]:
        """Get supported @-symbol patterns and their descriptions."""
        return {
            '@files': [
                '@files *.py',
                '@files src/**/*.ts',
                '@files "path with spaces/*.js"',
                '@files config.json settings.yaml'
            ],
            '@code': [
                '@code function authentication',
                '@code class UserManager',
                '@code async database operations',
                '@code error handling patterns'
            ],
            '@docs': [
                '@docs README',
                '@docs API documentation',
                '@docs *.md',
                '@docs user guide'
            ],
            '@git': [
                '@git recent changes',
                '@git modified files',
                '@git branch differences',
                '@git commit history'
            ],
            '@folder': [
                '@folder src/',
                '@folder tests/unit',
                '@folder docs/',
                '@folder config/'
            ]
        }