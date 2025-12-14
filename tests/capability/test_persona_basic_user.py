"""
Basic User Persona Tests - No API keys required
Tests what a basic user can do without any external API keys
"""

import pytest
import subprocess
import sys
import os
from pathlib import Path
import json

BASE_DIR = Path(__file__).parent.parent.parent

@pytest.mark.persona("basic_user")
def test_basic_user_can_see_help():
    """Basic user can see CLI help without API keys"""
    result = subprocess.run(
        ["python", "-m", "torq_console.cli", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        env={**os.environ, "ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": ""}
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "torq" in result.stdout.lower()

@pytest.mark.persona("basic_user")
def test_basic_user_can_initialize_config():
    """Basic user can initialize configuration"""
    result = subprocess.run(
        ["python", "-m", "torq_console.cli", "config-init"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        env={**os.environ, "ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": ""}
    )

    # Should succeed or give helpful error about existing config
    assert result.returncode == 0 or "already exists" in result.stdout or "exists" in result.stdout

@pytest.mark.persona("basic_user")
def test_basic_user_can_run_help_subcommands():
    """Basic user can run help on subcommands"""
    subcommands = ["eval", "bench", "config-init", "serve"]

    for subcmd in subcommands:
        result = subprocess.run(
            ["python", "-m", "torq_console.cli", subcmd, "--help"],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            env={**os.environ, "ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": ""}
        )

        assert result.returncode == 0, f"Failed for subcommand {subcmd}: {result.stderr}"
        assert "usage:" in result.stdout.lower()

@pytest.mark.persona("basic_user")
def test_basic_user_can_check_evaluation_sets():
    """Basic user can see available evaluation sets"""
    result = subprocess.run(
        ["python", "-m", "torq_console.cli", "eval", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        env={**os.environ, "ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": ""}
    )

    assert result.returncode == 0
    assert "--set" in result.stdout

@pytest.mark.persona("basic_user")
def test_basic_user_cannot_run_eval_without_set():
    """Basic user cannot run eval without required parameters"""
    result = subprocess.run(
        ["python", "-m", "torq_console.cli", "eval"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        env={**os.environ, "ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": ""}
    )

    # Should fail gracefully
    assert result.returncode != 0
    assert ("missing" in result.stderr.lower() or
            "required" in result.stderr.lower() or
            "--set" in result.stderr)

@pytest.mark.persona("basic_user")
def test_basic_user_can_access_web_help():
    """Basic user can see web server help"""
    result = subprocess.run(
        ["python", "-m", "torq_console.cli", "serve", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        env={**os.environ, "ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": ""}
    )

    assert result.returncode == 0
    assert ("--port" in result.stdout or
            "--host" in result.stdout or
            "serve" in result.stdout.lower())

@pytest.mark.persona("basic_user")
def test_basic_user_without_marvin_still_works():
    """Basic user can use TORQ even without Marvin API keys"""
    # Test that the CLI loads and shows help without crashing
    result = subprocess.run(
        ["python", "-c", "import torq_console; print('TORQ Console imported successfully')"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        env={**os.environ, "ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": "", "MARVIN_API_KEY": ""}
    )

    assert result.returncode == 0
    assert "successfully" in result.stdout.lower()