"""
Git management utilities for TORQ CONSOLE.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging


class GitManager:
    """Git operations manager for TORQ CONSOLE."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.logger = logging.getLogger(__name__)

    async def get_status(self) -> Dict[str, Any]:
        """Get git status."""
        try:
            result = await asyncio.create_subprocess_exec(
                "git", "status", "--porcelain",
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                return {"error": stderr.decode()}

            status_lines = stdout.decode().strip().split('\n')
            status = {
                "modified": [],
                "added": [],
                "deleted": [],
                "untracked": []
            }

            for line in status_lines:
                if not line:
                    continue

                file_status = line[:2]
                file_path = line[3:]

                if 'M' in file_status:
                    status["modified"].append(file_path)
                elif 'A' in file_status:
                    status["added"].append(file_path)
                elif 'D' in file_status:
                    status["deleted"].append(file_path)
                elif '??' in file_status:
                    status["untracked"].append(file_path)

            return status

        except Exception as e:
            self.logger.error(f"Git status error: {e}")
            return {"error": str(e)}

    async def get_file_status(self, file_path: Path) -> Optional[str]:
        """Get status for a specific file."""
        try:
            status = await self.get_status()
            if "error" in status:
                return None

            rel_path = str(file_path.relative_to(self.repo_path))

            for status_type, files in status.items():
                if rel_path in files:
                    return status_type

            return None

        except Exception as e:
            self.logger.error(f"File status error: {e}")
            return None

    async def get_recent_files(self, limit: int = 10) -> List[str]:
        """Get recently modified files."""
        try:
            result = await asyncio.create_subprocess_exec(
                "git", "log", "--name-only", "--pretty=format:", f"-{limit}",
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                return []

            files = set()
            for line in stdout.decode().strip().split('\n'):
                if line and not line.startswith(' '):
                    files.add(line)

            return list(files)[:limit]

        except Exception as e:
            self.logger.error(f"Recent files error: {e}")
            return []

    async def get_repo_structure(self) -> Dict[str, Any]:
        """Get repository structure."""
        try:
            result = await asyncio.create_subprocess_exec(
                "find", ".", "-type", "f", "-not", "-path", "./.git/*",
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                return {"error": stderr.decode()}

            files = stdout.decode().strip().split('\n')
            return {
                "files": [f[2:] for f in files if f],  # Remove './' prefix
                "total": len(files)
            }

        except Exception as e:
            self.logger.error(f"Repo structure error: {e}")
            return {"error": str(e)}

    async def get_visual_diff(self, tool: str = "git") -> str:
        """Get visual diff."""
        from .visual_diff import VisualDiffEngine
        diff_engine = VisualDiffEngine()
        return await diff_engine.get_diff(tool=tool)

    async def commit(self, message: str, files: Optional[List[str]] = None) -> bool:
        """Commit changes."""
        try:
            # Add files
            if files:
                for file in files:
                    await asyncio.create_subprocess_exec(
                        "git", "add", file,
                        cwd=self.repo_path
                    )
            else:
                await asyncio.create_subprocess_exec(
                    "git", "add", ".",
                    cwd=self.repo_path
                )

            # Commit
            result = await asyncio.create_subprocess_exec(
                "git", "commit", "-m", message,
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()
            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"Commit error: {e}")
            return False

    async def auto_commit(self, message: str) -> bool:
        """Auto-commit with TORQ template."""
        commit_message = f"TORQ: {message}\n\n🤖 Generated with TORQ CONSOLE\nCo-Authored-By: Claude <noreply@anthropic.com>"
        return await self.commit(commit_message)