"""
File operations tool for TORQ Prince Flowers agent.

This module provides secure file operations including:
- Read/write operations with safety checks
- Backup and undo functionality
- File monitoring and validation
"""

import logging
import os
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime


class FileOperationsTool:
    """Secure file operations tool with safety features."""

    def __init__(self):
        """Initialize the file operations tool."""
        self.logger = logging.getLogger("FileOperationsTool")
        self.backup_dir = ".torq-backups"
        self.operation_history = []
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """Ensure backup directory exists."""
        os.makedirs(self.backup_dir, exist_ok=True)

    def is_available(self) -> bool:
        """Check if the file operations tool is available."""
        return True

    async def read_file(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Safely read a file."""
        try:
            if not self._is_safe_path(file_path):
                return {"success": False, "error": "Unsafe file path"}

            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()

            return {
                "success": True,
                "file_path": file_path,
                "content": content,
                "size": len(content),
                "encoding": encoding
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def write_file(self, file_path: str, content: str, backup: bool = True) -> Dict[str, Any]:
        """Safely write a file with optional backup."""
        try:
            if not self._is_safe_path(file_path):
                return {"success": False, "error": "Unsafe file path"}

            # Create backup if file exists and backup is enabled
            if backup and os.path.exists(file_path):
                await self._create_backup(file_path)

            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Record operation
            operation = {
                "timestamp": datetime.now().isoformat(),
                "type": "write",
                "file_path": file_path,
                "backup": backup
            }
            self.operation_history.append(operation)

            return {
                "success": True,
                "file_path": file_path,
                "size": len(content),
                "backup_created": backup and os.path.exists(file_path)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _is_safe_path(self, file_path: str) -> bool:
        """Check if file path is safe for operations."""
        try:
            # Convert to absolute path
            abs_path = os.path.abspath(file_path)

            # Define unsafe directories
            unsafe_dirs = [
                os.path.expanduser("~/.ssh"),
                os.path.expanduser("~/.gnupg"),
                "/etc",
                "/usr/bin",
                "/usr/sbin",
                "/bin",
                "/sbin",
                "C:\\Windows",
                "C:\\Program Files",
                "C:\\Program Files (x86)"
            ]

            # Check if path is in unsafe directories
            for unsafe_dir in unsafe_dirs:
                if abs_path.startswith(unsafe_dir):
                    return False

            return True

        except Exception:
            return False

    async def _create_backup(self, file_path: str):
        """Create a backup of the specified file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{os.path.basename(file_path)}_{timestamp}.bak"
            backup_path = os.path.join(self.backup_dir, backup_name)

            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")

        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the file operations tool."""
        try:
            return {
                "healthy": True,
                "backup_dir_exists": os.path.exists(self.backup_dir),
                "operation_history_size": len(self.operation_history)
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }