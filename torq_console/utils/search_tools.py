"""
Search Tools for TORQ Console - Claude Code Compatible Grep Tool.

Implements Grep functionality with Python regex and ripgrep fallback.
Compatible with Claude Code's search patterns and output formats.
"""

import asyncio
import re
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Iterator, NamedTuple
from dataclasses import dataclass


@dataclass
class GrepMatch:
    """Represents a single grep match with file and line information."""
    file_path: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int
    match_text: str


class GrepTool:
    """
    Powerful search tool built on Python regex with ripgrep fallback.

    Compatible with Claude Code's Grep tool interface and features.
    Supports full regex syntax, file filtering, and multiple output modes.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ripgrep_available = self._check_ripgrep()

    def _check_ripgrep(self) -> bool:
        """Check if ripgrep is available on the system."""
        try:
            result = subprocess.run(['rg', '--version'],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def search(
        self,
        pattern: str,
        path: Optional[str] = None,
        glob: Optional[str] = None,
        file_type: Optional[str] = None,
        case_insensitive: bool = False,
        whole_word: bool = False,
        output_mode: str = "files_with_matches",
        context_before: int = 0,
        context_after: int = 0,
        max_count: Optional[int] = None,
        show_line_numbers: bool = True,
        multiline: bool = False,
        head_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search file contents using regex patterns.

        Args:
            pattern: Regular expression pattern to search for
            path: File or directory to search in (defaults to current directory)
            glob: Glob pattern to filter files (e.g., "*.js", "*.{ts,tsx}")
            file_type: File type to search (js, py, rust, go, java, etc.)
            case_insensitive: Case insensitive search
            whole_word: Match whole words only
            output_mode: "content" shows lines, "files_with_matches" shows paths, "count" shows counts
            context_before: Lines to show before each match
            context_after: Lines to show after each match
            max_count: Maximum number of matches per file
            show_line_numbers: Show line numbers in output
            multiline: Enable multiline mode where . matches newlines
            head_limit: Limit output to first N results

        Returns:
            Dict with search results in Claude Code compatible format
        """
        try:
            # Use ripgrep if available and not multiline mode
            if self.ripgrep_available and not multiline:
                return await asyncio.to_thread(
                    self._search_with_ripgrep,
                    pattern, path, glob, file_type, case_insensitive, whole_word,
                    output_mode, context_before, context_after, max_count,
                    show_line_numbers, head_limit
                )
            else:
                return await asyncio.to_thread(
                    self._search_with_python,
                    pattern, path, glob, file_type, case_insensitive, whole_word,
                    output_mode, context_before, context_after, max_count,
                    show_line_numbers, multiline, head_limit
                )

        except Exception as e:
            self.logger.error(f"Grep search failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': [],
                'total_matches': 0,
                'files_searched': 0
            }

    def _search_with_ripgrep(
        self,
        pattern: str,
        path: Optional[str] = None,
        glob: Optional[str] = None,
        file_type: Optional[str] = None,
        case_insensitive: bool = False,
        whole_word: bool = False,
        output_mode: str = "files_with_matches",
        context_before: int = 0,
        context_after: int = 0,
        max_count: Optional[int] = None,
        show_line_numbers: bool = True,
        head_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Search using ripgrep (rg command)."""

        start_time = time.time()
        cmd = ['rg']

        # Add flags based on parameters
        if case_insensitive:
            cmd.append('-i')
        if whole_word:
            cmd.append('-w')
        if show_line_numbers:
            cmd.append('-n')

        # Context options
        if context_before > 0:
            cmd.extend(['-B', str(context_before)])
        if context_after > 0:
            cmd.extend(['-A', str(context_after)])
        if context_before > 0 and context_after > 0:
            cmd = ['rg', '-C', str(max(context_before, context_after))]

        # Output mode
        if output_mode == "files_with_matches":
            cmd.append('-l')
        elif output_mode == "count":
            cmd.append('-c')

        # File filtering
        if glob:
            cmd.extend(['--glob', glob])
        if file_type:
            cmd.extend(['-t', file_type])

        # Max count
        if max_count:
            cmd.extend(['-m', str(max_count)])

        # Add pattern and path
        cmd.append(pattern)
        if path:
            cmd.append(path)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            search_time = time.time() - start_time

            if result.returncode not in [0, 1]:  # 1 means no matches found
                raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)

            # Parse output
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []

            if head_limit:
                lines = lines[:head_limit]

            return {
                'success': True,
                'results': lines,
                'total_matches': len(lines),
                'files_searched': 'unknown',
                'search_time_ms': round(search_time * 1000, 2),
                'engine': 'ripgrep',
                'pattern': pattern,
                'output_mode': output_mode
            }

        except subprocess.CalledProcessError as e:
            raise Exception(f"Ripgrep failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("Search timed out")

    def _search_with_python(
        self,
        pattern: str,
        path: Optional[str] = None,
        glob: Optional[str] = None,
        file_type: Optional[str] = None,
        case_insensitive: bool = False,
        whole_word: bool = False,
        output_mode: str = "files_with_matches",
        context_before: int = 0,
        context_after: int = 0,
        max_count: Optional[int] = None,
        show_line_numbers: bool = True,
        multiline: bool = False,
        head_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Search using Python regex (fallback implementation)."""

        start_time = time.time()

        # Set default path
        if path is None:
            path = os.getcwd()

        # Prepare regex flags
        flags = re.MULTILINE
        if case_insensitive:
            flags |= re.IGNORECASE
        if multiline:
            flags |= re.DOTALL

        # Prepare pattern
        if whole_word:
            pattern = r'\b' + pattern + r'\b'

        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            raise Exception(f"Invalid regex pattern: {e}")

        # Get files to search
        files_to_search = self._get_files_to_search(path, glob, file_type)

        results = []
        files_searched = 0
        total_matches = 0

        for file_path in files_to_search:
            if head_limit and len(results) >= head_limit:
                break

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                files_searched += 1
                matches = list(regex.finditer(content))

                if not matches:
                    continue

                file_matches = 0
                if output_mode == "files_with_matches":
                    results.append(file_path)
                    total_matches += len(matches)
                elif output_mode == "count":
                    results.append(f"{file_path}:{len(matches)}")
                    total_matches += len(matches)
                elif output_mode == "content":
                    lines = content.split('\n')
                    for match in matches:
                        if max_count and file_matches >= max_count:
                            break

                        # Find line number
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = lines[line_num - 1]

                        # Build result with context
                        result_lines = []

                        # Context before
                        for i in range(max(0, line_num - context_before - 1), line_num - 1):
                            prefix = f"{i+1}-" if show_line_numbers else ""
                            result_lines.append(f"{prefix}{lines[i]}")

                        # Main match line
                        prefix = f"{line_num}:" if show_line_numbers else ""
                        result_lines.append(f"{prefix}{line_content}")

                        # Context after
                        for i in range(line_num, min(len(lines), line_num + context_after)):
                            prefix = f"{i+1}-" if show_line_numbers else ""
                            result_lines.append(f"{prefix}{lines[i]}")

                        if result_lines:
                            results.append(f"{file_path}:\n" + "\n".join(result_lines))

                        file_matches += 1
                        total_matches += 1

            except (IOError, OSError, UnicodeDecodeError) as e:
                self.logger.warning(f"Could not search file {file_path}: {e}")
                continue

        search_time = time.time() - start_time

        return {
            'success': True,
            'results': results,
            'total_matches': total_matches,
            'files_searched': files_searched,
            'search_time_ms': round(search_time * 1000, 2),
            'engine': 'python_regex',
            'pattern': pattern,
            'output_mode': output_mode
        }

    def _get_files_to_search(
        self,
        path: str,
        glob_pattern: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> List[str]:
        """Get list of files to search based on path and filters."""

        files = []
        base_path = Path(path)

        if base_path.is_file():
            return [str(base_path)]

        # Define file type extensions
        type_extensions = {
            'py': ['.py'],
            'js': ['.js', '.jsx'],
            'ts': ['.ts', '.tsx'],
            'java': ['.java'],
            'go': ['.go'],
            'rust': ['.rs'],
            'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
            'c': ['.c', '.h'],
            'php': ['.php'],
            'rb': ['.rb'],
            'cs': ['.cs'],
            'html': ['.html', '.htm'],
            'css': ['.css'],
            'json': ['.json'],
            'xml': ['.xml'],
            'yaml': ['.yaml', '.yml'],
            'md': ['.md', '.markdown'],
            'txt': ['.txt']
        }

        # Walk through directory
        for root, dirs, filenames in os.walk(base_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for filename in filenames:
                # Skip hidden files
                if filename.startswith('.'):
                    continue

                file_path = Path(root) / filename

                # Apply file type filter
                if file_type:
                    extensions = type_extensions.get(file_type, [])
                    if extensions and not any(filename.endswith(ext) for ext in extensions):
                        continue

                # Apply glob filter (basic implementation)
                if glob_pattern:
                    import fnmatch
                    if not fnmatch.fnmatch(filename, glob_pattern):
                        continue

                files.append(str(file_path))

        return files


# Export main tool
grep_tool = GrepTool()

async def grep_search(
    pattern: str,
    path: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for grep search.
    Compatible with Claude Code's Grep tool interface.
    """
    return await grep_tool.search(pattern, path, **kwargs)