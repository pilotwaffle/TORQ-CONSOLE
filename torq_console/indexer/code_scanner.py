"""
Code Scanner - File discovery and parsing with .gitignore support.

Scans codebases recursively, respects .gitignore patterns, and extracts
code structures (functions, classes, docstrings) for indexing.
"""

import os
import ast
import pathlib
from typing import List, Dict, Set, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CodeScanner:
    """Scans codebase and extracts code structures for indexing."""

    # File extensions to index
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.cpp', '.c', '.h', '.hpp',
        '.go', '.rs', '.rb', '.php', '.swift',
        '.kt', '.scala', '.r', '.m', '.sh'
    }

    # Directories to always ignore
    IGNORE_DIRS = {
        '__pycache__', 'node_modules', '.git', '.venv', 'venv',
        'env', 'build', 'dist', '.pytest_cache', '.mypy_cache',
        'target', 'bin', 'obj', '.idea', '.vscode'
    }

    def __init__(self, root_path: str):
        """
        Initialize code scanner.

        Args:
            root_path: Root directory to scan
        """
        self.root_path = Path(root_path)
        self.gitignore_patterns = self._load_gitignore()
        self.files_scanned = 0
        self.functions_found = 0
        self.classes_found = 0

    def _load_gitignore(self) -> Set[str]:
        """Load and parse .gitignore patterns."""
        patterns = set()
        gitignore_path = self.root_path / '.gitignore'

        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.add(line)
            except Exception as e:
                logger.warning(f"Failed to load .gitignore: {e}")

        return patterns

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored based on patterns."""
        # Check ignore directories
        for part in path.parts:
            if part in self.IGNORE_DIRS:
                return True

        # Check gitignore patterns (simple implementation)
        rel_path = str(path.relative_to(self.root_path))
        for pattern in self.gitignore_patterns:
            if pattern in rel_path:
                return True

        return False

    def scan_files(self) -> List[Dict]:
        """
        Scan all code files in the codebase.

        Returns:
            List of file metadata dicts
        """
        files = []

        for file_path in self.root_path.rglob('*'):
            if not file_path.is_file():
                continue

            if file_path.suffix not in self.CODE_EXTENSIONS:
                continue

            if self._should_ignore(file_path):
                continue

            try:
                files.append({
                    'path': str(file_path),
                    'relative_path': str(file_path.relative_to(self.root_path)),
                    'extension': file_path.suffix,
                    'size': file_path.stat().st_size
                })
                self.files_scanned += 1
            except Exception as e:
                logger.debug(f"Skipping {file_path}: {e}")

        logger.info(f"Scanned {self.files_scanned} code files")
        return files

    def extract_python_structures(self, file_path: str) -> List[Dict]:
        """
        Extract functions and classes from Python file.

        Args:
            file_path: Path to Python file

        Returns:
            List of code structure dicts
        """
        structures = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    doc = ast.get_docstring(node) or ""
                    structures.append({
                        'type': 'function',
                        'name': node.name,
                        'file': file_path,
                        'line': node.lineno,
                        'docstring': doc,
                        'code': ast.unparse(node) if hasattr(ast, 'unparse') else ''
                    })
                    self.functions_found += 1

                elif isinstance(node, ast.ClassDef):
                    doc = ast.get_docstring(node) or ""
                    structures.append({
                        'type': 'class',
                        'name': node.name,
                        'file': file_path,
                        'line': node.lineno,
                        'docstring': doc,
                        'code': ast.unparse(node) if hasattr(ast, 'unparse') else ''
                    })
                    self.classes_found += 1

        except Exception as e:
            logger.debug(f"Failed to parse {file_path}: {e}")

        return structures

    def scan_codebase(self) -> List[Dict]:
        """
        Scan entire codebase and extract all structures.

        Returns:
            List of all code structures (files, functions, classes)
        """
        all_structures = []

        # Add file-level structures
        files = self.scan_files()
        all_structures.extend(files)

        # Extract Python structures
        python_files = [f for f in files if f['extension'] == '.py']
        for file_info in python_files:
            structures = self.extract_python_structures(file_info['path'])
            all_structures.extend(structures)

        logger.info(
            f"Extracted {self.functions_found} functions and "
            f"{self.classes_found} classes from {len(python_files)} Python files"
        )

        return all_structures

    def get_file_content(self, file_path: str, max_lines: int = 500) -> str:
        """
        Get file content for indexing.

        Args:
            file_path: Path to file
            max_lines: Maximum lines to read

        Returns:
            File content string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [f.readline() for _ in range(max_lines)]
                return ''.join(lines)
        except Exception as e:
            logger.debug(f"Failed to read {file_path}: {e}")
            return ""

    def get_stats(self) -> Dict:
        """Get scanning statistics."""
        return {
            'files_scanned': self.files_scanned,
            'functions_found': self.functions_found,
            'classes_found': self.classes_found
        }
