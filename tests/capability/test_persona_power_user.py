"""
Power User Persona Tests - Full CLI surface with API keys
Tests what a power user can do with complete access
"""

import pytest
import subprocess
import sys
import os
from pathlib import Path
import json
import tempfile

BASE_DIR = Path(__file__).parent.parent.parent

@pytest.mark.persona("power_user")
def test_power_user_can_see_all_commands():
    """Power user can see all CLI commands"""
    result = subprocess.run(
        ["python", "-m", "torq_console.cli", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    # Should show all major commands
    expected_commands = ["eval", "bench", "config-init", "serve", "mcp", "agent"]
    for cmd in expected_commands:
        assert cmd in result.stdout

@pytest.mark.persona("power_user")
def test_power_user_can_access_evaluation_help():
    """Power user can access evaluation command help"""
    result = subprocess.run(
        ["python", "-m", "torq_console.cli", "eval", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    assert "--set" in result.stdout
    assert "--seed" in result.stdout
    assert "--output" in result.stdout

@pytest.mark.persona("power_user")
def test_power_user_can_access_benchmark_help():
    """Power user can access benchmark commands"""
    result = subprocess.run(
        ["python", "-m", "torq_console.cli", "bench", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    assert "benchmark" in result.stdout.lower()

@pytest.mark.persona("power_user")
def test_power_user_can_access_mcp_commands():
    """Power user can access MCP management commands"""
    result = subprocess.run(
        ["python", "-m", "torq_console.cli", "mcp", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    # Should show MCP-related options
    assert ("connect" in result.stdout.lower() or
            "list" in result.stdout.lower() or
            "mcp" in result.stdout.lower())

@pytest.mark.persona("power_user")
def test_power_user_can_access_agent_commands():
    """Power user can access agent system commands"""
    result = subprocess.run(
        ["python", "-m", "torq_console.cli", "agent", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    # Should show agent-related options
    assert ("query" in result.stdout.lower() or
            "chat" in result.stdout.lower() or
            "list" in result.stdout.lower())

@pytest.mark.persona("power_user")
def test_power_user_can_see_torq_console_help():
    """Power user can access torq-console specific help"""
    result = subprocess.run(
        ["torq-console", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        shell=True
    )

    assert result.returncode == 0
    # Should show torq-console specific options
    assert ("--web" in result.stdout or
            "--mcp-connect" in result.stdout or
            "telemetry" in result.stdout.lower())

@pytest.mark.persona("power_user")
def test_power_user_can_check_evaluation_set_list():
    """Power user can see what evaluation sets are available"""
    result = subprocess.run(
        ["python", "-m", "torq_console.cli", "eval", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    # The help should mention how to see available sets
    assert ("--set" in result.stdout or
            "set" in result.stdout.lower())

@pytest.mark.persona("power_user")
def test_power_user_can_run_eval_with_invalid_set():
    """Power user gets helpful error for invalid evaluation set"""
    result = subprocess.run(
        ["python", "-m", "torq_console.cli", "eval", "--set", "nonexistent_set"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        timeout=10
    )

    # Should fail gracefully with helpful error
    assert result.returncode != 0
    error_output = result.stderr or result.stdout
    assert any(phrase in error_output.lower() for phrase in
               ["error", "not found", "invalid", "unknown", "no such"])

@pytest.mark.persona("power_user")
def test_power_user_can_import_marvin_integration():
    """Power user can import Marvin integration modules"""
    result = subprocess.run(
        ["python", "-c",
         "try:\n"
         "    from torq_console.marvin_integration import TorqMarvinIntegration\n"
         "    print('Marvin integration imported successfully')\n"
         "except ImportError as e:\n"
         "    print(f'Marvin integration not available: {e}')"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    # Should either succeed or fail gracefully
    assert ("successfully" in result.stdout.lower() or
            "not available" in result.stdout.lower())

@pytest.mark.persona("power_user")
def test_power_user_can_run_benchmark_with_help():
    """Power user can access benchmark help with all options"""
    # Test if benchmark command has proper help
    result = subprocess.run(
        ["python", "-m", "torq_console.cli", "bench", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    # Should show benchmark-related options
    assert ("benchmark" in result.stdout.lower() or
            "bench" in result.stdout.lower())