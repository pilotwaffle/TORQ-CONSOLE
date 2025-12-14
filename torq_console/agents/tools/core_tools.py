"""
Core Tools Module - Consolidated File Operations and Terminal Commands

This module consolidates file_operations_tool.py and terminal_commands_tool.py
into a unified core tools interface with shared patterns and infrastructure.

Provides fundamental system interaction capabilities:
- Safe file operations with backup/undo functionality
- Secure terminal command execution with whitelisting
- Common error handling and validation
- Shared logging and audit infrastructure

Author: TORQ Console Development Team
Version: 2.0.0 (Consolidated)
"""

import logging
import os
import shutil
import json
import subprocess
import shlex
import re
import hashlib
from typing import Dict, Any, Optional, List, Set, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


# Configure logging
logger = logging.getLogger(__name__)
audit_logger = logging.getLogger("torq.security.core")


class ToolStatus(Enum):
    """Tool availability and health status."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    ERROR = "error"


@dataclass
class ToolResult:
    """Standardized result structure across all tools."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class BaseCoreTool(ABC):
    """Base class for core tools with common functionality."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"torq.tools.{name}")
        self._status = ToolStatus.UNAVAILABLE

    @property
    def status(self) -> ToolStatus:
        """Get current tool status."""
        return self._status

    def _set_status(self, status: ToolStatus, error: Optional[str] = None):
        """Update tool status."""
        self._status = status
        if error:
            self.logger.error(f"Tool {self.name} status set to {status.value}: {error}")
        else:
            self.logger.info(f"Tool {self.name} status set to {status.value}")

    @abstractmethod
    async def check_health(self) -> ToolResult:
        """Check tool health and availability."""
        pass

    @abstractmethod
    async def execute(self, action: str, **kwargs) -> ToolResult:
        """Execute tool action."""
        pass


class SecurityError(Exception):
    """Base security exception."""
    pass


class CommandNotWhitelistedError(SecurityError):
    """Raised when attempting to execute a non-whitelisted command."""
    pass


class DangerousCommandError(SecurityError):
    """Raised when attempting to execute an explicitly blocked command."""
    pass


class FileOperationsError(Exception):
    """File operations related errors."""
    pass


class SecureFileManager:
    """Manages secure file operations with backup and undo capabilities."""

    def __init__(self, backup_dir: Optional[Path] = None, max_backups: int = 10):
        self.backup_dir = backup_dir or Path("E:/file_operations_backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = max_backups
        self.history_file = self.backup_dir / "operation_history.json"
        self.operation_history = self._load_history()

        # Security constraints
        self.allowed_extensions = {'.txt', '.py', '.js', '.html', '.css', '.json', '.md', '.yaml', '.yml'}
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.restricted_paths = {
            Path('C:\\Windows'), Path('C:\\Program Files'),
            Path('C:\\Program Files (x86)'), Path('/etc'), Path('/usr/bin')
        }

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load operation history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load history file: {e}")
        return []

    def _save_history(self):
        """Save operation history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.operation_history[-100:], f, indent=2, default=str)  # Keep last 100
        except Exception as e:
            logger.error(f"Could not save history file: {e}")

    def _validate_path(self, path: Path) -> bool:
        """Validate path for security constraints."""
        try:
            # Check if path is within restricted directories
            for restricted in self.restricted_paths:
                if path.is_relative_to(restricted):
                    return False

            # Check file extension if it's a file
            if path.is_file() and path.suffix.lower() not in self.allowed_extensions:
                return False

            # Check file size
            if path.exists() and path.stat().st_size > self.max_file_size:
                return False

            return True
        except Exception:
            return False

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create backup of file before modification."""
        if not file_path.exists():
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name

            shutil.copy2(file_path, backup_path)

            # Record operation
            self.operation_history.append({
                'timestamp': timestamp,
                'operation': 'backup',
                'file_path': str(file_path),
                'backup_path': str(backup_path),
                'hash': self._calculate_hash(file_path)
            })
            self._save_history()

            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return None

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    async def read_file(self, file_path: Union[str, Path]) -> ToolResult:
        """Safely read file contents."""
        try:
            path = Path(file_path)

            # Validate path
            if not self._validate_path(path):
                return ToolResult(
                    success=False,
                    error=f"Path validation failed for: {path}"
                )

            # Create backup before reading
            backup_path = self._create_backup(path)

            content = path.read_text(encoding='utf-8')

            return ToolResult(
                success=True,
                data=content,
                metadata={
                    'file_path': str(path),
                    'backup_path': str(backup_path) if backup_path else None,
                    'size': len(content),
                    'hash': self._calculate_hash(path)
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to read file {file_path}: {str(e)}"
            )

    async def write_file(self, file_path: Union[str, Path], content: str, create_backup: bool = True) -> ToolResult:
        """Safely write content to file with backup."""
        try:
            path = Path(file_path)

            # Validate path
            if not self._validate_path(path):
                return ToolResult(
                    success=False,
                    error=f"Path validation failed for: {path}"
                )

            # Create backup if file exists
            backup_path = None
            if path.exists() and create_backup:
                backup_path = self._create_backup(path)

            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            path.write_text(content, encoding='utf-8')

            # Record operation
            self.operation_history.append({
                'timestamp': datetime.now().isoformat(),
                'operation': 'write',
                'file_path': str(path),
                'backup_path': str(backup_path) if backup_path else None,
                'content_size': len(content),
                'hash': self._calculate_hash(path)
            })
            self._save_history()

            return ToolResult(
                success=True,
                data={'file_path': str(path), 'bytes_written': len(content)},
                metadata={
                    'backup_path': str(backup_path) if backup_path else None,
                    'previous_backup': backup_path is not None
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to write file {file_path}: {str(e)}"
            )

    async def list_directory(self, dir_path: Union[str, Path], pattern: str = "*") -> ToolResult:
        """List directory contents with optional pattern matching."""
        try:
            path = Path(dir_path)

            # Validate path
            if not self._validate_path(path):
                return ToolResult(
                    success=False,
                    error=f"Path validation failed for: {path}"
                )

            if not path.exists() or not path.is_dir():
                return ToolResult(
                    success=False,
                    error=f"Directory does not exist: {path}"
                )

            files = []
            for item in path.glob(pattern):
                if self._validate_path(item):
                    files.append({
                        'name': item.name,
                        'path': str(item),
                        'type': 'directory' if item.is_dir() else 'file',
                        'size': item.stat().st_size if item.is_file() else 0,
                        'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })

            return ToolResult(
                success=True,
                data=files,
                metadata={'directory': str(path), 'pattern': pattern, 'count': len(files)}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to list directory {dir_path}: {str(e)}"
            )


class SecureCommandExecutor:
    """Manages secure command execution with comprehensive security controls."""

    def __init__(self):
        # Define allowed commands (whitelist approach)
        self.allowed_commands = {
            # File operations
            'ls', 'dir', 'cat', 'type', 'head', 'tail', 'wc', 'grep', 'find',
            # Development tools
            'python', 'python3', 'pip', 'pip3', 'node', 'npm', 'yarn', 'git',
            # System info
            'ps', 'top', 'htop', 'df', 'du', 'free', 'uname', 'whoami',
            # Network tools (read-only)
            'ping', 'curl', 'wget', 'nslookup', 'dig',
            # Build tools
            'make', 'cmake', 'gcc', 'g++', 'clang', 'cargo', 'go', 'java', 'javac',
            # Text processing
            'sed', 'awk', 'sort', 'uniq', 'cut', 'tr',
            # Archive tools
            'tar', 'zip', 'unzip', 'gzip', 'gunzip'
        }

        # Dangerous commands (blacklist)
        self.dangerous_commands = {
            'rm', 'rmdir', 'del', 'delete', 'format', 'fdisk', 'mkfs',
            'shutdown', 'reboot', 'halt', 'poweroff',
            'passwd', 'su', 'sudo', 'chmod', 'chown',
            'iptables', 'ufw', 'firewall',
            'crontab', 'at', 'batch',
            'dd', 'shred', 'wipe',
            'systemctl', 'service', 'init'
        }

        # Command options that are dangerous
        self.dangerous_options = {
            '-rf', '-fr', '--recursive', '--force',
            '--no-preserve-root', '-f /', 'rm -rf /'
        }

        # Working directory constraints
        self.allowed_working_dirs = {
            Path.home(),
            Path.cwd(),
            Path('E:/'),
            Path('/tmp'),
            Path('./')
        }

    def _sanitize_command(self, command: str, args: List[str]) -> tuple[str, List[str]]:
        """Sanitize command and arguments."""
        # Extract base command
        base_cmd = command.split()[-1] if ' ' in command else command

        # Check against dangerous commands
        if base_cmd in self.dangerous_commands:
            raise DangerousCommandError(f"Command '{base_cmd}' is blocked for security reasons")

        # Check against whitelist
        if base_cmd not in self.allowed_commands:
            raise CommandNotWhitelistedError(f"Command '{base_cmd}' is not in the allowed commands list")

        # Check for dangerous options
        dangerous_found = []
        for arg in args:
            for dangerous_opt in self.dangerous_options:
                if dangerous_opt in arg.lower():
                    dangerous_found.append(dangerous_opt)

        if dangerous_found:
            raise DangerousCommandError(f"Dangerous options detected: {dangerous_found}")

        # Check for command injection attempts
        dangerous_patterns = [
            r'[;&|`$()]',  # Shell metacharacters
            r'\$\(',       # Command substitution
            r'`.*`',       # Backticks
            r'&&', r'\|\|', # Command chaining
            r'>', r'>>', r'<'  # I/O redirection
        ]

        combined_input = command + ' ' + ' '.join(args)
        for pattern in dangerous_patterns:
            if re.search(pattern, combined_input):
                raise DangerousCommandError(f"Potential command injection detected: {pattern}")

        return base_cmd, args

    def _validate_working_directory(self, cwd: Optional[Path]) -> Path:
        """Validate working directory."""
        if cwd is None:
            return Path.cwd()

        # Check if working directory is allowed
        for allowed_dir in self.allowed_working_dirs:
            if cwd.is_relative_to(allowed_dir):
                return cwd

        raise SecurityError(f"Working directory {cwd} is not allowed")

    async def execute_command(
        self,
        command: str,
        args: List[str] = None,
        cwd: Optional[Union[str, Path]] = None,
        timeout: int = 30,
        env: Optional[Dict[str, str]] = None
    ) -> ToolResult:
        """Execute command with security controls."""
        try:
            args = args or []
            working_dir = self._validate_working_directory(Path(cwd) if cwd else None)

            # Sanitize command and arguments
            safe_cmd, safe_args = self._sanitize_command(command, args)

            # Log execution attempt
            audit_logger.info(f"Executing command: {safe_cmd} {' '.join(safe_args)} in {working_dir}")

            # Prepare environment (remove dangerous env vars)
            clean_env = os.environ.copy()
            if env:
                clean_env.update(env)

            # Remove potentially dangerous environment variables
            dangerous_env_vars = ['PATH', 'LD_PRELOAD', 'LD_LIBRARY_PATH']
            for var in dangerous_env_vars:
                if var in clean_env and var not in (env or {}):
                    del clean_env[var]

            # Execute command
            result = subprocess.run(
                [safe_cmd] + safe_args,
                cwd=working_dir,
                env=clean_env,
                timeout=timeout,
                capture_output=True,
                text=True,
                shell=False  # Critical: No shell interpretation
            )

            # Log execution result
            audit_logger.info(
                f"Command completed: {safe_cmd} {' '.join(safe_args)} "
                f"-> Exit code: {result.returncode}"
            )

            return ToolResult(
                success=result.returncode == 0,
                data={
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'exit_code': result.returncode,
                    'command': safe_cmd,
                    'args': safe_args,
                    'working_directory': str(working_dir)
                },
                metadata={
                    'timeout': timeout,
                    'execution_time': None,  # Could add timing if needed
                    'security_validated': True
                }
            )

        except subprocess.TimeoutExpired as e:
            audit_logger.warning(f"Command timed out: {command}")
            return ToolResult(
                success=False,
                error=f"Command timed out after {timeout} seconds: {str(e)}"
            )

        except (SecurityError, DangerousCommandError, CommandNotWhitelistedError) as e:
            audit_logger.error(f"Security violation: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Security violation: {str(e)}"
            )

        except Exception as e:
            audit_logger.error(f"Command execution failed: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Command execution failed: {str(e)}"
            )


class CoreToolsManager:
    """Main manager for all core tools functionality."""

    def __init__(self):
        self.file_manager = SecureFileManager()
        self.command_executor = SecureCommandExecutor()
        self.logger = logging.getLogger(__name__)

    async def check_health(self) -> ToolResult:
        """Check health of all core tools."""
        health_status = {}

        # Check file operations
        try:
            test_file = self.file_manager.backup_dir / '.health_check'
            test_file.write_text('test')
            test_file.unlink()
            health_status['file_operations'] = 'available'
        except Exception as e:
            health_status['file_operations'] = f'error: {str(e)}'

        # Check command execution
        try:
            result = await self.command_executor.execute_command('echo', ['test'])
            health_status['command_execution'] = 'available' if result.success else f'error: {result.error}'
        except Exception as e:
            health_status['command_execution'] = f'error: {str(e)}'

        overall_healthy = all('available' in status for status in health_status.values())

        return ToolResult(
            success=overall_healthy,
            data=health_status,
            metadata={'component': 'core_tools'}
        )

    async def execute_file_operation(self, operation: str, **kwargs) -> ToolResult:
        """Execute file operation."""
        if operation == 'read':
            return await self.file_manager.read_file(kwargs.get('file_path'))
        elif operation == 'write':
            return await self.file_manager.write_file(
                kwargs.get('file_path'),
                kwargs.get('content'),
                kwargs.get('create_backup', True)
            )
        elif operation == 'list':
            return await self.file_manager.list_directory(
                kwargs.get('dir_path'),
                kwargs.get('pattern', '*')
            )
        else:
            return ToolResult(
                success=False,
                error=f"Unknown file operation: {operation}"
            )

    async def execute_command(self, command: str, **kwargs) -> ToolResult:
        """Execute command with security controls."""
        return await self.command_executor.execute_command(
            command,
            kwargs.get('args', []),
            kwargs.get('cwd'),
            kwargs.get('timeout', 30),
            kwargs.get('env')
        )


# Factory function for easy initialization
def create_core_tools_manager() -> CoreToolsManager:
    """Create and return a core tools manager instance."""
    return CoreToolsManager()


# Export main classes and functions
__all__ = [
    'CoreToolsManager',
    'SecureFileManager',
    'SecureCommandExecutor',
    'BaseCoreTool',
    'ToolResult',
    'ToolStatus',
    'SecurityError',
    'CommandNotWhitelistedError',
    'DangerousCommandError',
    'FileOperationsError',
    'create_core_tools_manager'
]