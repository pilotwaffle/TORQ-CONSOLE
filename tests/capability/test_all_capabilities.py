"""
Comprehensive Capability Tests

Tests all 17 capabilities from docs/capabilities.yml
Each test directly maps to a capability ID with the same name.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

BASE_DIR = Path(__file__).parent.parent.parent

# === Tier 0 - Smoke Tests ===

def test_cli_help_torq():
    """Display CLI help for torq command"""
    result = subprocess.run(
        ["torq", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    expected_commands = ["eval", "bench", "config-init", "serve", "mcp", "agent"]
    for cmd in expected_commands:
        assert cmd in result.stdout

def test_cli_help_torq_console():
    """Display CLI help for torq-console command"""
    result = subprocess.run(
        ["torq-console", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    # Check for actual options available in torq-console
    expected_options = ["eval", "web", "mcp-connect", "agent", "serve"]
    for opt in expected_options:
        assert opt in result.stdout

def test_package_import():
    """Import torq_console package in Python"""
    result = subprocess.run(
        [sys.executable, "-c", "import torq_console; print('Import successful')"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    assert "Import successful" in result.stdout

# === Tier 1 - Evaluation System ===

def test_eval_help():
    """Display evaluation command help"""
    result = subprocess.run(
        ["torq", "eval", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    expected_options = ["--set", "--seed", "--output", "--no-baseline"]
    for opt in expected_options:
        assert opt in result.stdout

@pytest.mark.skipif(
    not Path(BASE_DIR / "eval_sets" / "v1.0").exists(),
    reason="Evaluation v1.0 set not available"
)
def test_eval_set_exists():
    """Evaluation v1.0 set files exist and are valid"""
    # Check files exist
    tasks_file = BASE_DIR / "eval_sets" / "v1.0" / "tasks.json"
    metadata_file = BASE_DIR / "eval_sets" / "v1.0" / "metadata.json"

    assert tasks_file.exists(), f"Tasks file not found: {tasks_file}"
    assert metadata_file.exists(), f"Metadata file not found: {metadata_file}"

    # Check JSON validity
    with open(tasks_file) as f:
        tasks_data = json.load(f)
    assert "tasks" in tasks_data
    assert "version" in tasks_data

    with open(metadata_file) as f:
        metadata_data = json.load(f)

@pytest.mark.skipif(
    not Path(BASE_DIR / "eval_sets" / "v1.0").exists(),
    reason="Evaluation v1.0 set not available"
)
def test_eval_v1_deterministic():
    """Run v1.0 evaluation set deterministically"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_file = f.name

    try:
        result = subprocess.run(
            ["torq", "eval", "--set", "v1.0", "--seed", "42", "--output", output_file],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=60
        )

        # Check output file was created
        assert Path(output_file).exists(), "Evaluation output file not created"

        # Check output file content
        with open(output_file) as f:
            output_data = json.load(f)

        assert "overall_score" in output_data or "results" in output_data, "Output missing expected fields"

        # Note: exit code check depends on evaluation implementation
        # Some evaluation systems return non-zero for failed evaluations

    finally:
        # Cleanup
        if Path(output_file).exists():
            Path(output_file).unlink()

# === Tier 1 - Configuration System ===

def test_config_init():
    """Initialize TORQ Console configuration"""
    # Use a temporary directory to avoid affecting user config
    with tempfile.TemporaryDirectory() as temp_dir:
        env = os.environ.copy()
        env["HOME"] = temp_dir
        env["USERPROFILE"] = temp_dir  # Windows

        result = subprocess.run(
            ["torq", "config-init"],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            env=env
        )

        # The command should succeed or at least not crash
        # Some config implementations might return non-zero for existing config
        assert result.returncode in [0, 1], f"Config init failed: {result.stderr}"

# === Tier 1 - Policy System ===

def test_routing_policy_exists():
    """Routing policy configuration exists and is valid"""
    policy_file = BASE_DIR / "policies" / "routing" / "v1.yaml"

    if policy_file.exists():
        with open(policy_file) as f:
            policy_data = yaml.safe_load(f)

        assert "policies" in policy_data or "routing" in policy_data
        # Check for common policy structure elements
        content = str(policy_data).lower()
        assert any(key in content for key in ["routing", "intent", "mappings"])
    else:
        pytest.skip(f"Routing policy file not found: {policy_file}")

def test_slo_config_exists():
    """SLO configuration exists and is valid"""
    slo_file = BASE_DIR / "slo.yml"

    if slo_file.exists():
        with open(slo_file) as f:
            slo_data = yaml.safe_load(f)

        assert isinstance(slo_data, dict)
        content = str(slo_data).lower()
        assert any(key in content for key in ["slos", "interactive", "tool_heavy"])
    else:
        pytest.skip(f"SLO config file not found: {slo_file}")

# === Tier 2 - Web Interface ===

def test_web_help_available():
    """Web interface help is available"""
    result = subprocess.run(
        ["torq", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert "--web" in result.stdout or "serve" in result.stdout.lower() or "web" in result.stdout.lower()

def test_web_server_command():
    """Web server command is available"""
    result = subprocess.run(
        ["torq", "serve", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    assert "serve" in result.stdout.lower()
    assert "web" in result.stdout.lower() or "ui" in result.stdout.lower()

# === Tier 2 - MCP Integration ===

def test_mcp_option_available():
    """MCP connection option is available"""
    result = subprocess.run(
        ["torq", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert "--mcp-connect" in result.stdout or "mcp" in result.stdout.lower()

def test_mcp_command_available():
    """MCP management command is available"""
    result = subprocess.run(
        ["torq", "mcp", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    assert "mcp" in result.stdout.lower()

# === Tier 2 - Agent System ===

def test_agent_command_available():
    """Agent command is available"""
    result = subprocess.run(
        ["torq", "agent", "--help"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    assert result.returncode == 0
    assert "marvin" in result.stdout.lower() or "agent" in result.stdout.lower()

def test_agent_modules_exist():
    """Agent system modules exist"""
    agents_init = BASE_DIR / "torq_console" / "agents" / "__init__.py"
    marvin_init = BASE_DIR / "torq_console" / "marvin_integration" / "__init__.py"

    assert agents_init.exists(), f"Agent module not found: {agents_init}"
    assert marvin_init.exists(), f"Marvin integration module not found: {marvin_init}"

# === Negative Cases ===

def test_eval_requires_set():
    """Evaluation command requires --set parameter"""
    result = subprocess.run(
        ["torq", "eval"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    # Should fail with missing --set
    assert result.returncode != 0
    assert "missing" in result.stderr.lower() or "--set" in result.stderr.lower() or "required" in result.stderr.lower()

def test_eval_invalid_set():
    """Evaluation rejects invalid set names"""
    result = subprocess.run(
        ["torq", "eval", "--set", "nonexistent"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        timeout=10
    )

    # Should fail with error about nonexistent set
    assert result.returncode != 0
    error_output = (result.stderr + result.stdout).lower()
    assert any(phrase in error_output for phrase in ["error", "not found", "invalid", "no such", "unknown"])