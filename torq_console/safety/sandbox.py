"""
Sandbox Manager for Tool Isolation

Provides secure execution environment for tools with resource limits and isolation
"""

import os
import tempfile
import subprocess
import shutil
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging
import psutil
import signal
import time
import json

from .models import SandboxConfig, ToolRequest, RiskLevel

logger = logging.getLogger(__name__)


class SandboxManager:
    """Manages sandboxed execution environment for tools"""

    def __init__(self, default_config: Optional[SandboxConfig] = None):
        """
        Initialize sandbox manager

        Args:
            default_config: Default sandbox configuration
        """
        self.default_config = default_config or SandboxConfig()
        self.active_sandboxes: Dict[str, Dict[str, Any]] = {}
        self.temp_dir = Path(tempfile.mkdtemp(prefix="torq_sandbox_"))

        # Ensure temp directory exists
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Platform-specific setup
        self.system = platform.system().lower()
        self._setup_platform_specific()

    def _setup_platform_specific(self):
        """Setup platform-specific sandbox capabilities"""
        if self.system == "linux":
            self._setup_linux_sandbox()
        elif self.system == "darwin":  # macOS
            self._setup_macos_sandbox()
        elif self.system == "windows":
            self._setup_windows_sandbox()

    def _setup_linux_sandbox(self):
        """Setup Linux-specific sandbox features"""
        # Check if we have required capabilities
        try:
            # Check for unprivileged user namespaces
            result = subprocess.run(
                ["unshare", "--user", "--pid", "--fork", "true"],
                capture_output=True,
                timeout=5
            )
            self.has_user_namespaces = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.has_user_namespaces = False
            logger.warning("User namespaces not available, sandbox will be limited")

    def _setup_macos_sandbox(self):
        """Setup macOS-specific sandbox features"""
        # macOS has sandbox-exec built-in
        self.has_sandbox_exec = shutil.which("sandbox-exec") is not None
        if not self.has_sandbox_exec:
            logger.warning("sandbox-exec not available, sandbox will be limited")

    def _setup_windows_sandbox(self):
        """Setup Windows-specific sandbox features"""
        # Windows sandboxing is more limited
        self.has_windows_isolation = False
        logger.info("Windows sandbox: using file system isolation only")

    def create_sandbox(
        self,
        request: ToolRequest,
        config: Optional[SandboxConfig] = None
    ) -> Dict[str, Any]:
        """
        Create a sandbox for tool execution

        Args:
            request: Tool request
            config: Sandbox configuration

        Returns:
            Sandbox information dictionary
        """
        sandbox_config = config or self.default_config
        sandbox_id = f"sandbox_{request.request_id}"

        # Create sandbox directory
        sandbox_dir = self.temp_dir / sandbox_id
        sandbox_dir.mkdir(parents=True, exist_ok=True)

        # Create working directory
        if sandbox_config.working_directory:
            work_dir = sandbox_dir / "work"
            work_dir.mkdir(exist_ok=True)
        else:
            work_dir = sandbox_dir

        # Create temp directory
        temp_dir = sandbox_dir / "tmp"
        temp_dir.mkdir(exist_ok=True)

        sandbox_info = {
            "id": sandbox_id,
            "request_id": request.request_id,
            "tool_name": request.tool_name,
            "directory": str(sandbox_dir),
            "working_directory": str(work_dir),
            "temp_directory": str(temp_dir),
            "config": sandbox_config.dict(),
            "created_at": time.time(),
            "processes": [],
            "resources": {
                "memory_peak": 0,
                "cpu_time": 0,
                "disk_usage": 0
            }
        }

        # Store sandbox info
        self.active_sandboxes[sandbox_id] = sandbox_info

        logger.info(f"Created sandbox {sandbox_id} for tool {request.tool_name}")
        return sandbox_info

    def execute_in_sandbox(
        self,
        sandbox_id: str,
        command: Union[str, List[str]],
        env_vars: Optional[Dict[str, str]] = None,
        input_data: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a command in the sandbox

        Args:
            sandbox_id: Sandbox identifier
            command: Command to execute (string or list)
            env_vars: Environment variables to set
            input_data: Input data for the process
            timeout: Execution timeout in seconds

        Returns:
            Execution result dictionary
        """
        if sandbox_id not in self.active_sandboxes:
            raise ValueError(f"Sandbox not found: {sandbox_id}")

        sandbox_info = self.active_sandboxes[sandbox_id]
        config = SandboxConfig(**sandbox_info["config"])

        # Prepare command
        if isinstance(command, str):
            cmd_list = command.split()
        else:
            cmd_list = command

        # Prepare environment
        env = os.environ.copy()
        env.update(env_vars or {})

        # Filter environment variables
        if config.allowed_environment_vars:
            env = {k: v for k, v in env.items() if k in config.allowed_environment_vars}

        # Remove forbidden environment variables
        for forbidden in config.forbidden_environment_vars:
            env.pop(forbidden, None)

        # Set sandbox-specific environment
        env["SANDBOX_ID"] = sandbox_id
        env["SANDBOX_DIR"] = sandbox_info["directory"]
        env["SANDBOX_WORK_DIR"] = sandbox_info["working_directory"]
        env["SANDBOX_TEMP_DIR"] = sandbox_info["temp_directory"]

        # Prepare execution command based on platform
        exec_cmd = self._prepare_execution_command(cmd_list, config, sandbox_info)

        try:
            # Monitor resources before execution
            initial_memory = self._get_memory_usage()
            start_time = time.time()

            # Execute the command
            process = subprocess.Popen(
                exec_cmd,
                env=env,
                cwd=sandbox_info["working_directory"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=None if self.system == "windows" else os.setsid
            )

            # Store process info
            process_info = {
                "pid": process.pid,
                "command": " ".join(exec_cmd),
                "start_time": start_time,
                "status": "running"
            }
            sandbox_info["processes"].append(process_info)

            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(input=input_data, timeout=timeout)
                return_code = process.returncode
                process_info["status"] = "completed"
            except subprocess.TimeoutExpired:
                # Kill process and all children
                self._kill_process_tree(process.pid)
                stdout, stderr = process.communicate()
                return_code = -1
                process_info["status"] = "timeout"
                logger.warning(f"Process {process.pid} timed out in sandbox {sandbox_id}")

            # Calculate resource usage
            execution_time = time.time() - start_time
            memory_peak = self._get_memory_usage() - initial_memory
            disk_usage = self._get_disk_usage(sandbox_info["directory"])

            # Update resource tracking
            sandbox_info["resources"]["memory_peak"] = max(
                sandbox_info["resources"]["memory_peak"], memory_peak
            )
            sandbox_info["resources"]["cpu_time"] += execution_time
            sandbox_info["resources"]["disk_usage"] = disk_usage

            # Check resource limits
            violations = self._check_resource_limits(sandbox_info["resources"], config)

            result = {
                "success": return_code == 0,
                "return_code": return_code,
                "stdout": stdout,
                "stderr": stderr,
                "execution_time": execution_time,
                "resource_usage": sandbox_info["resources"],
                "violations": violations,
                "sandbox_id": sandbox_id
            }

            logger.info(f"Command executed in sandbox {sandbox_id}, return_code={return_code}")
            return result

        except Exception as e:
            logger.error(f"Error executing command in sandbox {sandbox_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "sandbox_id": sandbox_id,
                "violations": [{"type": "execution_error", "message": str(e)}]
            }

    def _prepare_execution_command(
        self,
        command: List[str],
        config: SandboxConfig,
        sandbox_info: Dict[str, Any]
    ) -> List[str]:
        """Prepare platform-specific execution command"""
        if self.system == "linux" and self.has_user_namespaces and config.filesystem_isolated:
            # Use unshare for filesystem isolation
            return [
                "unshare",
                "--mount",
                "--pid",
                "--fork",
                "--root", sandbox_info["directory"],
                "--wd", sandbox_info["working_directory"]
            ] + command

        elif self.system == "darwin" and self.has_sandbox_exec and config.filesystem_isolated:
            # Use macOS sandbox-exec
            # Create a temporary sandbox profile
            profile_path = self._create_macos_sandbox_profile(sandbox_info, config)
            return [
                "sandbox-exec",
                "-f", profile_path
            ] + command

        else:
            # Basic execution without additional isolation
            return command

    def _create_macos_sandbox_profile(self, sandbox_info: Dict[str, Any], config: SandboxConfig) -> str:
        """Create macOS sandbox profile"""
        profile_path = Path(sandbox_info["temp_directory"]) / "sandbox.sb"

        profile = f"""
(version 1)
(deny default)
(allow file-read* (subpath "{sandbox_info['directory']}"))
(allow file-write* (subpath "{sandbox_info['temp_directory']}"))
(allow process-exec (literal "/bin/sh"))
(allow process-exec (literal "/usr/bin/python3"))
"""

        # Add network access if allowed
        if not config.network_isolated:
            profile += '(allow network*)\n'

        # Add additional allowed executables
        if config.allowed_executables:
            for exe in config.allowed_executables:
                profile += f'(allow process-exec (literal "{exe}"))\n'

        profile_path.write_text(profile)
        return str(profile_path)

    def _kill_process_tree(self, pid: int):
        """Kill a process and all its children"""
        try:
            if self.system == "windows":
                # Windows process termination
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
            else:
                # Unix process termination
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                time.sleep(1)
                os.killpg(os.getpgid(pid), signal.SIGKILL)
        except Exception as e:
            logger.warning(f"Error killing process tree {pid}: {e}")

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            return psutil.Process().memory_info().rss / 1024 / 1024
        except:
            return 0.0

    def _get_disk_usage(self, path: str) -> float:
        """Get disk usage for path in MB"""
        try:
            return sum(f.stat().st_size for f in Path(path).rglob('*') if f.is_file()) / 1024 / 1024
        except:
            return 0.0

    def _check_resource_limits(self, resources: Dict[str, Any], config: SandboxConfig) -> List[Dict[str, Any]]:
        """Check if resource limits are exceeded"""
        violations = []

        if config.max_memory_mb and resources["memory_peak"] > config.max_memory_mb:
            violations.append({
                "type": "memory_limit",
                "limit": config.max_memory_mb,
                "actual": resources["memory_peak"],
                "unit": "MB"
            })

        if config.max_cpu_time_seconds and resources["cpu_time"] > config.max_cpu_time_seconds:
            violations.append({
                "type": "cpu_time_limit",
                "limit": config.max_cpu_time_seconds,
                "actual": resources["cpu_time"],
                "unit": "seconds"
            })

        # Check custom resource limits
        for limit_name, limit_value in config.resource_limits.items():
            if limit_name in resources and resources[limit_name] > limit_value:
                violations.append({
                    "type": "custom_limit",
                    "limit_name": limit_name,
                    "limit": limit_value,
                    "actual": resources[limit_name]
                })

        return violations

    def cleanup_sandbox(self, sandbox_id: str) -> bool:
        """
        Clean up a sandbox

        Args:
            sandbox_id: Sandbox identifier

        Returns:
            True if cleanup was successful
        """
        if sandbox_id not in self.active_sandboxes:
            logger.warning(f"Sandbox not found for cleanup: {sandbox_id}")
            return False

        sandbox_info = self.active_sandboxes[sandbox_id]

        try:
            # Kill any remaining processes
            for process_info in sandbox_info["processes"]:
                if process_info["status"] == "running":
                    self._kill_process_tree(process_info["pid"])

            # Remove sandbox directory
            sandbox_path = Path(sandbox_info["directory"])
            if sandbox_path.exists():
                shutil.rmtree(sandbox_path, ignore_errors=True)

            # Remove from active sandboxes
            del self.active_sandboxes[sandbox_id]

            logger.info(f"Cleaned up sandbox {sandbox_id}")
            return True

        except Exception as e:
            logger.error(f"Error cleaning up sandbox {sandbox_id}: {e}")
            return False

    def cleanup_all_sandboxes(self):
        """Clean up all active sandboxes"""
        sandbox_ids = list(self.active_sandboxes.keys())
        for sandbox_id in sandbox_ids:
            self.cleanup_sandbox(sandbox_id)

    def get_sandbox_status(self, sandbox_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a sandbox"""
        return self.active_sandboxes.get(sandbox_id)

    def list_active_sandboxes(self) -> List[str]:
        """List all active sandbox IDs"""
        return list(self.active_sandboxes.keys())

    def __del__(self):
        """Cleanup when manager is destroyed"""
        try:
            self.cleanup_all_sandboxes()
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass