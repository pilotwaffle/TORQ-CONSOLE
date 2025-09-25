"""
Enhanced Visual Diff System for TORQ CONSOLE.

Provides beautiful, Claude Code-compatible visual diffs using multiple tools
including git-delta, bat syntax highlighting, and custom rendering.
"""

import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import shutil

from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text


class VisualDiffEngine:
    """
    Enhanced visual diff engine that provides multiple rendering options
    optimized for Claude Code workflows.
    """

    def __init__(self):
        self.console = Console()
        self.logger = logging.getLogger(__name__)

        # Tool availability
        self.tools = {
            "delta": self._check_delta(),
            "bat": self._check_bat(),
            "diff": True,  # Always available
            "git": self._check_git()
        }

        self.logger.info(f"Visual diff tools available: {[k for k, v in self.tools.items() if v]}")

    def _check_delta(self) -> bool:
        """Check if git-delta is available."""
        try:
            result = subprocess.run(["delta", "--version"],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_bat(self) -> bool:
        """Check if bat is available."""
        try:
            result = subprocess.run(["bat", "--version"],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Try batcat as well (Ubuntu package name)
            try:
                result = subprocess.run(["batcat", "--version"],
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False

    def _check_git(self) -> bool:
        """Check if git is available."""
        try:
            result = subprocess.run(["git", "--version"],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    async def get_diff(self,
                      file_path: Optional[Path] = None,
                      content_before: Optional[str] = None,
                      content_after: Optional[str] = None,
                      tool: str = "auto",
                      context: int = 3,
                      side_by_side: bool = False) -> str:
        """
        Generate enhanced visual diff using specified tool.

        Args:
            file_path: Path to file for git diff
            content_before: Before content for direct comparison
            content_after: After content for direct comparison
            tool: Diff tool to use ('auto', 'delta', 'bat', 'git', 'rich')
            context: Number of context lines
            side_by_side: Show side-by-side diff

        Returns:
            Formatted diff string
        """
        try:
            # Auto-select best available tool
            if tool == "auto":
                tool = self._select_best_tool(side_by_side)

            # Handle different diff sources
            if file_path:
                return await self._get_git_diff(file_path, tool, context, side_by_side)
            elif content_before is not None and content_after is not None:
                return await self._get_content_diff(content_before, content_after,
                                                  tool, context, side_by_side, file_path)
            else:
                return await self._get_repo_diff(tool, context, side_by_side)

        except Exception as e:
            self.logger.error(f"Diff generation error: {e}")
            return f"Error generating diff: {e}"

    def _select_best_tool(self, side_by_side: bool = False) -> str:
        """Select the best available diff tool."""
        if side_by_side and self.tools.get("delta"):
            return "delta"
        elif self.tools.get("delta"):
            return "delta"
        elif self.tools.get("bat"):
            return "bat"
        elif self.tools.get("git"):
            return "git"
        else:
            return "rich"

    async def _get_git_diff(self, file_path: Path, tool: str,
                           context: int, side_by_side: bool) -> str:
        """Get git diff for a specific file."""
        try:
            # Generate git diff
            cmd = ["git", "diff", f"--unified={context}", str(file_path)]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=file_path.parent if file_path.exists() else Path.cwd()
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                return f"Git diff error: {stderr.decode()}"

            raw_diff = stdout.decode()

            # Apply tool-specific formatting
            return await self._format_diff(raw_diff, tool, side_by_side, file_path)

        except Exception as e:
            self.logger.error(f"Git diff error: {e}")
            return f"Error: {e}"

    async def _get_content_diff(self, content_before: str, content_after: str,
                               tool: str, context: int, side_by_side: bool,
                               file_path: Optional[Path] = None) -> str:
        """Get diff between two content strings."""
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.before', delete=False) as f1:
                f1.write(content_before)
                f1.flush()
                temp_before = Path(f1.name)

            with tempfile.NamedTemporaryFile(mode='w', suffix='.after', delete=False) as f2:
                f2.write(content_after)
                f2.flush()
                temp_after = Path(f2.name)

            try:
                # Generate diff
                cmd = ["diff", f"--unified={context}", str(temp_before), str(temp_after)]
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await result.communicate()
                raw_diff = stdout.decode()

                # Apply tool-specific formatting
                return await self._format_diff(raw_diff, tool, side_by_side, file_path)

            finally:
                # Cleanup
                temp_before.unlink(missing_ok=True)
                temp_after.unlink(missing_ok=True)

        except Exception as e:
            self.logger.error(f"Content diff error: {e}")
            return f"Error: {e}"

    async def _get_repo_diff(self, tool: str, context: int, side_by_side: bool) -> str:
        """Get diff for entire repository."""
        try:
            cmd = ["git", "diff", f"--unified={context}"]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.cwd()
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                return f"Git diff error: {stderr.decode()}"

            raw_diff = stdout.decode()
            return await self._format_diff(raw_diff, tool, side_by_side)

        except Exception as e:
            self.logger.error(f"Repo diff error: {e}")
            return f"Error: {e}"

    async def _format_diff(self, raw_diff: str, tool: str, side_by_side: bool,
                          file_path: Optional[Path] = None) -> str:
        """Format diff using specified tool."""
        if not raw_diff.strip():
            return "No changes detected."

        try:
            if tool == "delta" and self.tools["delta"]:
                return await self._format_with_delta(raw_diff, side_by_side)
            elif tool == "bat" and self.tools["bat"]:
                return await self._format_with_bat(raw_diff, file_path)
            elif tool == "git":
                return await self._format_with_git(raw_diff)
            elif tool == "rich":
                return await self._format_with_rich(raw_diff, file_path)
            else:
                return raw_diff

        except Exception as e:
            self.logger.error(f"Diff formatting error with {tool}: {e}")
            return raw_diff  # Fallback to raw diff

    async def _format_with_delta(self, raw_diff: str, side_by_side: bool) -> str:
        """Format diff using git-delta."""
        try:
            # Determine delta command
            bat_cmd = "bat" if shutil.which("bat") else "batcat"

            cmd = ["delta"]
            if side_by_side:
                cmd.extend(["--side-by-side", "--width", "120"])

            # Add syntax highlighting
            cmd.extend([
                "--syntax-theme", "Dracula",
                "--line-numbers",
                "--navigate"
            ])

            result = await asyncio.create_subprocess_exec(
                *cmd,
                input=raw_diff.encode(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                return stdout.decode()
            else:
                self.logger.warning(f"Delta formatting failed: {stderr.decode()}")
                return raw_diff

        except Exception as e:
            self.logger.error(f"Delta formatting error: {e}")
            return raw_diff

    async def _format_with_bat(self, raw_diff: str, file_path: Optional[Path]) -> str:
        """Format diff using bat syntax highlighter."""
        try:
            # Determine bat command
            bat_cmd = "bat" if shutil.which("bat") else "batcat"

            cmd = [bat_cmd, "--style", "numbers,changes", "--color", "always"]

            # Try to detect language from file extension
            if file_path:
                cmd.extend(["--language", self._detect_language(file_path)])

            result = await asyncio.create_subprocess_exec(
                *cmd,
                input=raw_diff.encode(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                return stdout.decode()
            else:
                self.logger.warning(f"Bat formatting failed: {stderr.decode()}")
                return raw_diff

        except Exception as e:
            self.logger.error(f"Bat formatting error: {e}")
            return raw_diff

    async def _format_with_git(self, raw_diff: str) -> str:
        """Format diff using git's built-in coloring."""
        try:
            cmd = ["git", "diff", "--color=always", "--no-index", "/dev/null", "-"]

            result = await asyncio.create_subprocess_exec(
                *cmd,
                input=raw_diff.encode(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()
            return stdout.decode() if result.returncode in [0, 1] else raw_diff

        except Exception as e:
            self.logger.error(f"Git formatting error: {e}")
            return raw_diff

    async def _format_with_rich(self, raw_diff: str, file_path: Optional[Path]) -> str:
        """Format diff using Rich library."""
        try:
            # Detect language for syntax highlighting
            language = self._detect_language(file_path) if file_path else "diff"

            # Create syntax-highlighted diff
            syntax = Syntax(raw_diff, language, theme="monokai", line_numbers=True)

            # Capture Rich output
            with self.console.capture() as capture:
                self.console.print(syntax)

            return capture.get()

        except Exception as e:
            self.logger.error(f"Rich formatting error: {e}")
            return raw_diff

    def _detect_language(self, file_path: Optional[Path]) -> str:
        """Detect programming language from file extension."""
        if not file_path:
            return "text"

        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".sh": "bash",
            ".ps1": "powershell",
            ".sql": "sql",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".md": "markdown",
            ".dockerfile": "dockerfile",
            ".toml": "toml",
            ".ini": "ini",
            ".conf": "ini"
        }

        suffix = file_path.suffix.lower()
        return extension_map.get(suffix, "text")

    async def get_file_preview(self, file_path: Path,
                              tool: str = "auto",
                              max_lines: int = 50) -> str:
        """Get syntax-highlighted file preview."""
        try:
            if not file_path.exists():
                return f"File not found: {file_path}"

            content = file_path.read_text()
            lines = content.split('\n')

            # Truncate if too long
            if len(lines) > max_lines:
                content = '\n'.join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"

            # Auto-select tool
            if tool == "auto":
                tool = "bat" if self.tools["bat"] else "rich"

            if tool == "bat" and self.tools["bat"]:
                return await self._format_file_with_bat(content, file_path)
            elif tool == "rich":
                return await self._format_file_with_rich(content, file_path)
            else:
                return content

        except Exception as e:
            self.logger.error(f"File preview error: {e}")
            return f"Error reading file: {e}"

    async def _format_file_with_bat(self, content: str, file_path: Path) -> str:
        """Format file content using bat."""
        try:
            bat_cmd = "bat" if shutil.which("bat") else "batcat"

            cmd = [
                bat_cmd,
                "--style", "numbers,header",
                "--color", "always",
                "--language", self._detect_language(file_path),
                "--file-name", str(file_path)
            ]

            result = await asyncio.create_subprocess_exec(
                *cmd,
                input=content.encode(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()
            return stdout.decode() if result.returncode == 0 else content

        except Exception as e:
            self.logger.error(f"Bat file formatting error: {e}")
            return content

    async def _format_file_with_rich(self, content: str, file_path: Path) -> str:
        """Format file content using Rich."""
        try:
            language = self._detect_language(file_path)
            syntax = Syntax(content, language, theme="monokai",
                          line_numbers=True, code_width=120)

            # Create panel with file info
            panel = Panel(
                syntax,
                title=f"📄 {file_path.name}",
                subtitle=f"Language: {language}",
                border_style="blue"
            )

            with self.console.capture() as capture:
                self.console.print(panel)

            return capture.get()

        except Exception as e:
            self.logger.error(f"Rich file formatting error: {e}")
            return content

    def get_available_tools(self) -> Dict[str, bool]:
        """Get dictionary of available diff tools."""
        return self.tools.copy()

    async def install_recommendations(self) -> List[str]:
        """Get installation recommendations for missing tools."""
        recommendations = []

        if not self.tools["delta"]:
            recommendations.append(
                "Install git-delta for enhanced diffs:\n"
                "  cargo install git-delta\n"
                "  # or\n"
                "  brew install git-delta"
            )

        if not self.tools["bat"]:
            recommendations.append(
                "Install bat for syntax highlighting:\n"
                "  cargo install bat\n"
                "  # or\n"
                "  brew install bat\n"
                "  # or\n"
                "  apt install bat"
            )

        return recommendations