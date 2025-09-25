"""
File Tools for TORQ Console - Claude Code Compatible Tools.

Implements Glob functionality for fast file pattern matching.
Compatible with Claude Code's file search patterns.
"""

import asyncio
import glob
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import os
import time


class GlobTool:
    """
    Fast file pattern matching tool compatible with Claude Code.

    Supports glob patterns like "**/*.js" or "src/**/*.ts"
    Returns matching file paths sorted by modification time.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def search_files(
        self,
        pattern: str,
        path: Optional[str] = None,
        recursive: bool = True,
        sort_by_mtime: bool = True,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "**/*.py", "*.js")
            path: Directory to search in (defaults to current working directory)
            recursive: Enable recursive search
            sort_by_mtime: Sort results by modification time (newest first)
            limit: Maximum number of results to return

        Returns:
            Dict with success status, files list, and metadata
        """
        try:
            # Use asyncio.to_thread for I/O operations
            result = await asyncio.to_thread(
                self._search_files_sync,
                pattern, path, recursive, sort_by_mtime, limit
            )
            return result

        except Exception as e:
            self.logger.error(f"Glob search failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'files': [],
                'count': 0
            }

    def _search_files_sync(
        self,
        pattern: str,
        path: Optional[str] = None,
        recursive: bool = True,
        sort_by_mtime: bool = True,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Synchronous file search implementation."""

        # Set default path
        if path is None:
            path = os.getcwd()

        # Normalize path using pathlib for cross-platform compatibility
        base_path = Path(path)
        if not base_path.exists():
            return {
                'success': False,
                'error': f"Path does not exist: {path}",
                'files': [],
                'count': 0
            }

        # Build full search pattern
        if recursive and not pattern.startswith('**/'):
            # Add recursive prefix if not present
            if '/' in pattern:
                search_pattern = str(base_path / pattern)
            else:
                search_pattern = str(base_path / '**' / pattern)
        else:
            search_pattern = str(base_path / pattern)

        # Perform glob search
        start_time = time.time()
        matches = glob.glob(search_pattern, recursive=recursive)

        # Filter out directories, keep only files
        files = []
        for match in matches:
            if os.path.isfile(match):
                # Convert to absolute path and normalize
                abs_path = os.path.abspath(match)
                files.append(abs_path)

        # Sort by modification time if requested
        if sort_by_mtime:
            files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        else:
            files.sort()  # Alphabetical sort

        # Apply limit if specified
        if limit and len(files) > limit:
            files = files[:limit]

        search_time = time.time() - start_time

        # Return results in Claude Code compatible format
        return {
            'success': True,
            'files': files,
            'count': len(files),
            'pattern': pattern,
            'search_path': str(base_path),
            'search_time_ms': round(search_time * 1000, 2),
            'recursive': recursive,
            'sorted_by_mtime': sort_by_mtime
        }


class PathUtils:
    """Path utilities for cross-platform file operations."""

    @staticmethod
    def normalize_path(path: Union[str, Path]) -> Path:
        """Normalize path for cross-platform compatibility."""
        return Path(path).resolve()

    @staticmethod
    def get_relative_path(path: Union[str, Path], base: Union[str, Path]) -> Path:
        """Get relative path from base directory."""
        return Path(path).relative_to(Path(base))

    @staticmethod
    def is_safe_path(path: Union[str, Path], base: Union[str, Path]) -> bool:
        """Check if path is safe (doesn't escape base directory)."""
        try:
            Path(path).resolve().relative_to(Path(base).resolve())
            return True
        except ValueError:
            return False


# Export main tools
glob_tool = GlobTool()

async def glob_search(
    pattern: str,
    path: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for glob search.
    Compatible with Claude Code's Glob tool interface.
    """
    return await glob_tool.search_files(pattern, path, **kwargs)


# Example usage patterns for Claude Code compatibility:
# await glob_search("**/*.py")          # All Python files recursively
# await glob_search("*.js", "src/")     # All JS files in src/
# await glob_search("**/*.{ts,tsx}")    # All TypeScript files (requires shell expansion)