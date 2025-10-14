"""
Terminal Commands Tool for Prince Flowers Agent

SECURITY-CRITICAL MODULE: This tool provides controlled terminal command execution
with comprehensive security controls. ALL commands must be whitelisted.

Security Features:
- Whitelist-only command execution
- Input sanitization (injection prevention)
- No shell interpretation (shell=False)
- Timeout enforcement
- Working directory validation
- Comprehensive audit logging

Author: Prince Flowers Team
Version: 1.0.0
Security Level: CRITICAL
"""

import logging
import subprocess
import shlex
import os
import re
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Security audit logger (separate from application logs)
audit_logger = logging.getLogger("torq.security.terminal")
audit_logger.setLevel(logging.INFO)


class SecurityViolationError(Exception):
    """Raised when a security policy is violated."""
    pass


class CommandNotWhitelistedError(SecurityViolationError):
    """Raised when attempting to execute a non-whitelisted command."""
    pass


class DangerousCommandError(SecurityViolationError):
    """Raised when attempting to execute an explicitly blocked command."""
    pass


class InvalidWorkingDirectoryError(SecurityViolationError):
    """Raised when working directory is invalid or restricted."""
    pass


class TerminalCommandsTool:
    """
    Secure terminal command execution tool with whitelist-based security.

    This tool provides controlled access to terminal commands with multiple
    security layers to prevent command injection, privilege escalation, and
    resource exhaustion attacks.

    Security Model:
    1. Whitelist-only: Only pre-approved commands can execute
    2. Input sanitization: Dangerous characters are detected and blocked
    3. No shell: Uses subprocess with shell=False to prevent shell injection
    4. Resource limits: Enforces timeouts and working directory restrictions
    5. Audit logging: All command attempts are logged for security review

    Example:
        tool = TerminalCommandsTool()
        result = tool.execute(
            action="execute_command",
            command="ls -la",
            timeout=30
        )
    """

    # Whitelist of safe commands (read-only operations)
    SAFE_COMMANDS: Dict[str, Optional[List[str]]] = {
        # File viewing (read-only)
        'ls': None,      # None means all arguments allowed
        'dir': None,
        'cat': None,
        'head': None,
        'tail': None,
        'file': None,
        'wc': None,
        'pwd': None,
        'tree': None,

        # Search operations
        'grep': None,
        'find': None,
        'which': None,
        'where': None,  # Windows equivalent of which

        # Git operations (read-only)
        'git': ['status', 'log', 'diff', 'branch', 'show', 'remote', 'config'],

        # Package info (read-only)
        'npm': ['list', 'view', 'info', 'ls'],
        'pip': ['list', 'show', 'freeze'],

        # System info (read-only)
        'whoami': None,
        'hostname': None,
        'date': None,
        'uptime': None,
        'echo': None,
        'env': None,
        'printenv': None,

        # Python (controlled - no arbitrary code execution without validation)
        'python': ['-m', '--version', '--help'],
        'python3': ['-m', '--version', '--help'],
    }

    # Explicitly blocked commands (destructive or dangerous)
    BLOCKED_COMMANDS: Set[str] = {
        # File deletion/modification
        'rm', 'rmdir', 'del', 'erase', 'format', 'dd',

        # Permission changes
        'chmod', 'chown', 'chgrp', 'icacls', 'takeown',

        # Privilege escalation
        'sudo', 'su', 'runas',

        # Process control
        'kill', 'pkill', 'killall', 'taskkill',

        # Network access
        'wget', 'curl', 'nc', 'netcat', 'telnet', 'ssh', 'ftp',

        # Shell access
        'sh', 'bash', 'zsh', 'fish', 'csh', 'tcsh', 'ksh',
        'cmd', 'powershell', 'pwsh',

        # System modification
        'shutdown', 'reboot', 'init', 'systemctl', 'service',

        # Compilation/execution
        'gcc', 'g++', 'make', 'cmake', 'exec', 'eval',
    }

    # Dangerous characters for input sanitization detection
    DANGEROUS_CHARS: Set[str] = {
        ';', '|', '&', '>', '<', '`', '$', '\n', '\r', '||', '&&', '>>',
    }

    # Restricted system directories (cannot be working directory)
    RESTRICTED_DIRS: Set[str] = {
        '/etc', '/sys', '/proc', '/dev', '/boot',
        'C:\\Windows', 'C:\\Windows\\System32', 'C:\\Program Files',
    }

    # Maximum timeout in seconds
    MAX_TIMEOUT: int = 300  # 5 minutes
    DEFAULT_TIMEOUT: int = 30  # 30 seconds

    def __init__(self) -> None:
        """
        Initialize the terminal commands tool with security configuration.

        Sets up audit logging and validates security configuration.
        """
        self.name = "terminal_commands"
        self.description = (
            "Execute whitelisted terminal commands with comprehensive security controls. "
            "Only read-only and safe commands are permitted."
        )

        # Log initialization
        audit_logger.info(
            "TerminalCommandsTool initialized",
            extra={
                "timestamp": datetime.utcnow().isoformat(),
                "whitelisted_commands": len(self.SAFE_COMMANDS),
                "blocked_commands": len(self.BLOCKED_COMMANDS),
            }
        )

        logger.info(f"Initialized {self.name} tool with {len(self.SAFE_COMMANDS)} whitelisted commands")

    def is_available(self) -> bool:
        """
        Check if the tool is properly configured and available.

        Returns:
            bool: True if tool is available and configured correctly
        """
        try:
            # Verify whitelist is not empty
            if not self.SAFE_COMMANDS:
                logger.error("Whitelist is empty - tool unavailable")
                return False

            # Verify blocked list is not empty
            if not self.BLOCKED_COMMANDS:
                logger.error("Blocked list is empty - tool unavailable")
                return False

            # Verify subprocess is available
            subprocess.run(['echo', 'test'], capture_output=True, timeout=1, shell=False)

            return True
        except Exception as e:
            logger.error(f"Tool availability check failed: {e}")
            return False

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method supporting multiple actions.

        Actions:
        - execute_command: Execute a whitelisted command
        - validate_command: Validate a command without executing
        - get_whitelist: Return the list of whitelisted commands

        Args:
            action (str): Action to perform
            **kwargs: Action-specific parameters

        Returns:
            Dict[str, Any]: Result dictionary with 'success', 'result', 'error'

        Raises:
            SecurityViolationError: If security policy is violated
        """
        action = kwargs.get('action', 'execute_command')

        try:
            if action == 'execute_command':
                return self._execute_command(**kwargs)
            elif action == 'validate_command':
                return self._validate_command(**kwargs)
            elif action == 'get_whitelist':
                return self._get_whitelist()
            else:
                return {
                    'success': False,
                    'error': f"Unknown action: {action}",
                    'result': None
                }
        except SecurityViolationError as e:
            audit_logger.warning(
                f"Security violation: {e}",
                extra={
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": action,
                    "kwargs": str(kwargs),
                }
            )
            return {
                'success': False,
                'error': f"Security violation: {str(e)}",
                'result': None
            }
        except Exception as e:
            logger.error(f"Unexpected error in execute: {e}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'result': None
            }

    def _execute_command(
        self,
        command: str,
        timeout: Optional[int] = None,
        working_dir: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a whitelisted terminal command with security controls.

        Security Checks:
        1. Validate command against whitelist
        2. Check for blocked commands
        3. Sanitize input for dangerous characters
        4. Validate working directory
        5. Enforce timeout limits
        6. Execute with shell=False
        7. Audit log the attempt

        Args:
            command (str): Command to execute
            timeout (Optional[int]): Timeout in seconds (default: 30s, max: 300s)
            working_dir (Optional[str]): Working directory for command execution
            **kwargs: Additional parameters (ignored)

        Returns:
            Dict[str, Any]: Result with stdout, stderr, exit_code, success

        Raises:
            CommandNotWhitelistedError: If command is not whitelisted
            DangerousCommandError: If command is explicitly blocked
            InvalidWorkingDirectoryError: If working directory is invalid
        """
        # Audit log the attempt
        audit_logger.info(
            f"Command execution attempt: {command}",
            extra={
                "timestamp": datetime.utcnow().isoformat(),
                "command": command,
                "working_dir": working_dir,
                "timeout": timeout,
            }
        )

        # Step 1: Parse command
        try:
            command_parts = shlex.split(command)
        except ValueError as e:
            raise SecurityViolationError(f"Invalid command syntax: {e}")

        if not command_parts:
            raise SecurityViolationError("Empty command")

        base_command = command_parts[0].lower()
        command_args = command_parts[1:] if len(command_parts) > 1 else []

        # Step 2: Check if command is explicitly blocked
        if base_command in self.BLOCKED_COMMANDS:
            raise DangerousCommandError(
                f"Command '{base_command}' is explicitly blocked for security reasons"
            )

        # Step 3: Validate against whitelist
        if base_command not in self.SAFE_COMMANDS:
            raise CommandNotWhitelistedError(
                f"Command '{base_command}' is not in the whitelist"
            )

        # Step 4: Validate subcommands if whitelist specifies allowed subcommands
        allowed_subcommands = self.SAFE_COMMANDS[base_command]
        if allowed_subcommands is not None:
            if not command_args:
                raise SecurityViolationError(
                    f"Command '{base_command}' requires a subcommand: {allowed_subcommands}"
                )

            subcommand = command_args[0]
            if subcommand not in allowed_subcommands:
                raise SecurityViolationError(
                    f"Subcommand '{subcommand}' not allowed for '{base_command}'. "
                    f"Allowed: {allowed_subcommands}"
                )

        # Step 5: Detect dangerous characters (command injection attempt)
        for dangerous_char in self.DANGEROUS_CHARS:
            if dangerous_char in command:
                raise SecurityViolationError(
                    f"Dangerous character detected: '{dangerous_char}'. "
                    f"Command injection attempt blocked."
                )

        # Step 6: Validate working directory
        if working_dir:
            working_dir = self._validate_working_directory(working_dir)
        else:
            working_dir = os.getcwd()

        # Step 7: Validate and enforce timeout
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT
        elif timeout > self.MAX_TIMEOUT:
            logger.warning(f"Timeout {timeout}s exceeds maximum {self.MAX_TIMEOUT}s, capping")
            timeout = self.MAX_TIMEOUT
        elif timeout <= 0:
            raise SecurityViolationError(f"Invalid timeout: {timeout}")

        # Step 8: Execute command with shell=False (security critical)
        try:
            logger.info(f"Executing command: {command_parts} (timeout: {timeout}s)")

            result = subprocess.run(
                command_parts,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir,
                shell=False,  # SECURITY CRITICAL: Never use shell=True
            )

            # Log successful execution
            audit_logger.info(
                f"Command executed successfully: {command}",
                extra={
                    "timestamp": datetime.utcnow().isoformat(),
                    "command": command,
                    "exit_code": result.returncode,
                    "success": result.returncode == 0,
                }
            )

            return {
                'success': result.returncode == 0,
                'command': command,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_code': result.returncode,
                'result': result.stdout if result.returncode == 0 else None,
                'error': result.stderr if result.returncode != 0 else None,
            }

        except subprocess.TimeoutExpired:
            audit_logger.warning(
                f"Command timeout: {command}",
                extra={
                    "timestamp": datetime.utcnow().isoformat(),
                    "command": command,
                    "timeout": timeout,
                }
            )
            return {
                'success': False,
                'command': command,
                'error': f"Command timed out after {timeout} seconds",
                'stdout': '',
                'stderr': '',
                'exit_code': -1,
                'result': None,
            }

        except FileNotFoundError:
            return {
                'success': False,
                'command': command,
                'error': f"Command not found: {base_command}",
                'stdout': '',
                'stderr': '',
                'exit_code': -1,
                'result': None,
            }

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                'success': False,
                'command': command,
                'error': f"Execution error: {str(e)}",
                'stdout': '',
                'stderr': '',
                'exit_code': -1,
                'result': None,
            }

    def _validate_working_directory(self, working_dir: str) -> str:
        """
        Validate that working directory is safe and accessible.

        Security checks:
        - Directory exists
        - Not a restricted system directory
        - Is actually a directory (not a file)

        Args:
            working_dir (str): Directory path to validate

        Returns:
            str: Validated absolute path

        Raises:
            InvalidWorkingDirectoryError: If directory is invalid or restricted
        """
        try:
            path = Path(working_dir).resolve()

            # Check if exists
            if not path.exists():
                raise InvalidWorkingDirectoryError(
                    f"Working directory does not exist: {working_dir}"
                )

            # Check if is directory
            if not path.is_dir():
                raise InvalidWorkingDirectoryError(
                    f"Path is not a directory: {working_dir}"
                )

            # Check if in restricted directories
            path_str = str(path)
            for restricted in self.RESTRICTED_DIRS:
                if path_str.startswith(restricted):
                    raise InvalidWorkingDirectoryError(
                        f"Access to restricted directory denied: {restricted}"
                    )

            return str(path)

        except (OSError, RuntimeError) as e:
            raise InvalidWorkingDirectoryError(
                f"Invalid working directory: {e}"
            )

    def _validate_command(
        self,
        command: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Validate a command without executing it.

        Useful for checking if a command would be allowed before execution.

        Args:
            command (str): Command to validate
            **kwargs: Additional parameters (ignored)

        Returns:
            Dict[str, Any]: Validation result with 'valid', 'reason'
        """
        try:
            # Parse command
            command_parts = shlex.split(command)
            if not command_parts:
                return {
                    'success': True,
                    'valid': False,
                    'reason': 'Empty command',
                    'result': None,
                }

            base_command = command_parts[0].lower()
            command_args = command_parts[1:] if len(command_parts) > 1 else []

            # Check blocked list
            if base_command in self.BLOCKED_COMMANDS:
                return {
                    'success': True,
                    'valid': False,
                    'reason': f"Command '{base_command}' is explicitly blocked",
                    'result': None,
                }

            # Check whitelist
            if base_command not in self.SAFE_COMMANDS:
                return {
                    'success': True,
                    'valid': False,
                    'reason': f"Command '{base_command}' is not whitelisted",
                    'result': None,
                }

            # Check subcommands
            allowed_subcommands = self.SAFE_COMMANDS[base_command]
            if allowed_subcommands is not None:
                if not command_args:
                    return {
                        'success': True,
                        'valid': False,
                        'reason': f"Command requires subcommand: {allowed_subcommands}",
                        'result': None,
                    }

                subcommand = command_args[0]
                if subcommand not in allowed_subcommands:
                    return {
                        'success': True,
                        'valid': False,
                        'reason': f"Subcommand '{subcommand}' not allowed",
                        'result': None,
                    }

            # Check dangerous characters
            for dangerous_char in self.DANGEROUS_CHARS:
                if dangerous_char in command:
                    return {
                        'success': True,
                        'valid': False,
                        'reason': f"Dangerous character detected: '{dangerous_char}'",
                        'result': None,
                    }

            # Command is valid
            return {
                'success': True,
                'valid': True,
                'reason': 'Command is whitelisted and safe',
                'result': {
                    'base_command': base_command,
                    'args': command_args,
                }
            }

        except Exception as e:
            return {
                'success': False,
                'valid': False,
                'reason': f"Validation error: {str(e)}",
                'result': None,
            }

    def _get_whitelist(self) -> Dict[str, Any]:
        """
        Return the list of whitelisted commands.

        Returns:
            Dict[str, Any]: Whitelist information
        """
        return {
            'success': True,
            'result': {
                'whitelisted_commands': dict(self.SAFE_COMMANDS),
                'blocked_commands': list(self.BLOCKED_COMMANDS),
                'total_whitelisted': len(self.SAFE_COMMANDS),
                'total_blocked': len(self.BLOCKED_COMMANDS),
            },
            'error': None,
        }


def create_terminal_commands_tool() -> TerminalCommandsTool:
    """
    Factory function to create a TerminalCommandsTool instance.

    Returns:
        TerminalCommandsTool: Configured terminal commands tool
    """
    return TerminalCommandsTool()
