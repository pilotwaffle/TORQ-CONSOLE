"""
Simple capability tests - no complex imports
"""

import pytest
import subprocess
import sys
import os
from pathlib import Path
import json
import yaml

BASE_DIR = Path(__file__).parent.parent

def test_cli_help_torq():
    """Test 'torq --help' displays required options"""
    result = subprocess.run(
        "torq --help",
        shell=True,
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Check for key commands
    required = ["eval", "bench", "config-init", "serve", "mcp", "agent"]
    for req in required:
        assert req in result.stdout, f"Missing required content: {req}"

def test_cli_help_torq_console():
    """Test 'torq-console --help' displays required options"""
    result = subprocess.run(
        "torq-console --help",
        shell=True,
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Check for key options
    required = ["--web", "--mcp-connect", "eval", "telemetry"]
    for req in required:
        assert req in result.stdout, f"Missing required content: {req}"

def test_eval_help():
    """Test evaluation help displays required options"""
    result = subprocess.run(
        "torq eval --help",
        shell=True,
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Check for required options
    required = ["--set", "--seed", "--output", "--no-baseline"]
    for req in required:
        assert req in result.stdout, f"Missing required content: {req}"

def test_contract_file_exists():
    """Test capability contract file exists"""
    contract_path = BASE_DIR / "docs" / "capabilities.yml"
    assert contract_path.exists(), f"Contract file not found at {contract_path}"

def test_contract_is_valid_yaml():
    """Test contract file is valid YAML"""
    contract_path = BASE_DIR / "docs" / "capabilities.yml"
    with open(contract_path) as f:
        content = f.read()

    # Should not raise exception
    data = yaml.safe_load(content)
    assert isinstance(data, dict), "Contract should be a dictionary"

def test_eval_set_files_exist():
    """Test evaluation set files exist"""
    required_files = [
        "eval_sets/v1.0/tasks.json",
        "eval_sets/v1.0/metadata.json"
    ]

    for file_path in required_files:
        full_path = BASE_DIR / file_path
        assert full_path.exists(), f"Required file not found: {file_path}"

def test_eval_set_is_valid_json():
    """Test evaluation set JSON is valid"""
    eval_path = BASE_DIR / "eval_sets/v1.0" / "tasks.json"
    with open(eval_path) as f:
        content = f.read()

    # Should not raise exception
    data = json.loads(content)
    assert "tasks" in data, "Missing 'tasks' field in evaluation set"

def test_eval_v1_has_tasks():
    """Test v1.0 evaluation has tasks"""
    eval_path = BASE_DIR / "eval_sets/v1.0" / "tasks.json"
    with open(eval_path) as f:
        data = json.load(f)

    tasks = data.get("tasks", [])
    assert len(tasks) > 0, "No tasks found in evaluation set"
    assert len(tasks) == 10, f"Expected 10 tasks, found {len(tasks)}"

def test_policy_file_exists():
    """Test routing policy exists"""
    policy_path = BASE_DIR / "policies" / "routing" / "v1.yaml"
    assert policy_path.exists(), f"Policy file not found: {policy_path}"

def test_slo_file_exists():
    """Test SLO configuration exists"""
    slo_path = BASE_DIR / "slo.yml"
    assert slo_path.exists(), f"SLO file not found: {slo_path}"

def test_package_import():
    """Test torq_console can be imported"""
    result = subprocess.run(
        [sys.executable, "-c", "import torq_console; print('Import successful')"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0, f"Import failed: {result.stderr}"
    assert "Import successful" in result.stdout

def test_eval_requires_set_parameter():
    """Test evaluation command requires --set parameter"""
    result = subprocess.run(
        "torq eval",
        shell=True,
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 2, "Command should fail without --set"
    error_output = result.stderr or result.stdout
    assert "Missing option" in error_output or "--set" in error_output

def test_eval_rejects_invalid_set():
    """Test evaluation rejects invalid set names"""
    result = subprocess.run(
        "torq eval --set nonexistent",
        shell=True,
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        timeout=10
    )

    assert result.returncode == 1, "Command should fail with invalid set"
    error_output = result.stderr or result.stdout
    assert "Error" in error_output or "not found" in error_output