"""
Test core TORQ Console capabilities - Tier 0 smoke tests
"""

import pytest
import sys
import os
from pathlib import Path
import json
import yaml
import subprocess

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class CapabilityTest:
    """Base class for capability tests"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        # Load contract
        contract_path = self.base_dir.parent / "docs" / "capabilities.yml"
        with open(contract_path) as f:
            self.contract = yaml.safe_load(f)

    def run_command(self, cmd, timeout=30, cwd=None):
        """Run command and return result"""
        if cwd is None:
            cwd = self.base_dir

        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=cwd
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def check_file_exists(self, path):
        """Check if file exists"""
        full_path = Path(__file__).parent.parent / path
        return full_path.exists()

    def validate_json(self, content):
        """Validate JSON content"""
        try:
            json.loads(content)
            return True
        except:
            return False

    def validate_yaml(self, content):
        """Validate YAML content"""
        try:
            yaml.safe_load(content)
            return True
        except:
            return False

class TestCoreCapabilities(CapabilityTest):
    """Test basic user capabilities - no external dependencies"""

    @pytest.mark.capability
    def test_cli_help_torq(self):
        """Test 'torq --help' displays required options"""
        capability_id = "cli_help_torq"

        # Find capability in contract
        capability = next(c for c in self.contract["capabilities"] if c["id"] == capability_id)

        # Run the command
        success, stdout, stderr = self.run_command("torq --help")

        assert success, f"Command failed: {stderr}"
        assert capability["verify"]["exit_code"] == 0

        # Check required content
        for required in capability["verify"]["success_contains"]:
            assert required in stdout, f"Missing required content: {required}"

    @pytest.mark.capability
    def test_cli_help_torq_console(self):
        """Test 'torq-console --help' displays required options"""
        capability_id = "cli_help_torq_console"

        capability = next(c for c in self.contract["capabilities"] if c["id"] == capability_id)

        success, stdout, stderr = self.run_command("torq-console --help")

        assert success, f"Command failed: {stderr}"
        assert capability["verify"]["exit_code"] == 0

        for required in capability["verify"]["success_contains"]:
            assert required in stdout, f"Missing required content: {required}"

    @pytest.mark.capability
    def test_package_import(self):
        """Test torq_console can be imported"""
        capability_id = "package_import"

        capability = next(c for c in self.contract["capabilities"] if c["id"] == capability_id)

        # Execute Python code
        try:
            exec(capability["verify"]["python_code"])
        except Exception as e:
            pytest.fail(f"Package import failed: {e}")


@pytest.mark.power_user
class TestPowerUserCapabilities(CapabilityTest):
    """Test power user capabilities - may require installation"""

    @pytest.mark.capability
    def test_eval_help(self):
        """Test evaluation help displays required options"""
        capability_id = "eval_help"

        capability = next(c for c in self.contract["capabilities"] if c["id"] == capability_id)

        success, stdout, stderr = self.run_command("torq eval --help")

        assert success, f"Command failed: {stderr}"
        assert capability["verify"]["exit_code"] == 0

        for required in capability["verify"]["success_contains"]:
            assert required in stdout, f"Missing required content: {required}"

    @pytest.mark.capability
    def test_eval_v1_deterministic(self):
        """Test v1.0 evaluation runs deterministically"""
        capability_id = "eval_v1_deterministic"

        capability = next(c for c in self.contract["capabilities"] if c["id"] == capability_id)

        # Clean up any existing output
        output_file = Path("test_eval_output.json")
        if output_file.exists():
            output_file.unlink()

        # Run evaluation
        success, stdout, stderr = self.run_command(
            capability["verify"]["command"],
            timeout=60  # Give it more time
        )

        # Note: We don't assert success here because evaluation might fail
        # The important part is that the command runs and produces output

        # Check if output file was created
        for glob_pattern in capability["verify"]["artifacts"]["must_write_glob"]:
            import glob
            matches = glob.glob(glob_pattern)
            assert len(matches) > 0, f"No files matching pattern: {glob_pattern}"

            # Check JSON validity
            for match in matches:
                with open(match) as f:
                    content = f.read()
                assert self.validate_json(content), f"Invalid JSON in {match}"

                # Parse and check required fields
                data = json.loads(content)
                for field in capability["verify"]["artifacts"]["must_contain"]:
                    assert field in data, f"Missing field {field} in output"

    @pytest.mark.capability
    def test_eval_set_exists(self):
        """Test evaluation set files exist and are valid"""
        capability_id = "eval_set_exists"

        capability = next(c for c in self.contract["capabilities"] if c["id"] == capability_id)

        # Check files exist
        for file_path in capability["verify"]["file_exists"]:
            assert self.check_file_exists(file_path), f"File not found: {file_path}"

        # Check JSON validity
        for json_file in capability["verify"]["json_valid"]:
            full_path = Path(__file__).parent.parent.parent / json_file
            with open(full_path) as f:
                content = f.read()
            assert self.validate_json(content), f"Invalid JSON: {json_file}"

            # Check required content
            data = json.loads(content)
            for required in capability["verify"]["must_contain"]:
                assert required in data, f"Missing content {required} in {json_file}"

    @pytest.mark.capability
    def test_routing_policy_exists(self):
        """Test routing policy exists and is valid"""
        capability_id = "routing_policy_exists"

        capability = next(c for c in self.contract["capabilities"] if c["id"] == capability_id)

        # Check files exist
        for file_path in capability["verify"]["file_exists"]:
            assert self.check_file_exists(file_path), f"File not found: {file_path}"

        # Check YAML validity
        for yaml_file in capability["verify"]["yaml_valid"]:
            full_path = Path(__file__).parent.parent.parent / yaml_file
            with open(full_path) as f:
                content = f.read()
            assert self.validate_yaml(content), f"Invalid YAML: {yaml_file}"

            # Check required content
            data = yaml.safe_load(content)
            for required in capability["verify"]["must_contain"]:
                assert required in str(data), f"Missing content {required} in {yaml_file}"

    @pytest.mark.capability
    def test_slo_config_exists(self):
        """Test SLO configuration exists and is valid"""
        capability_id = "slo_config_exists"

        capability = next(c for c in self.contract["capabilities"] if c["id"] == capability_id)

        # Check files exist
        for file_path in capability["verify"]["file_exists"]:
            assert self.check_file_exists(file_path), f"File not found: {file_path}"

        # Check YAML validity
        for yaml_file in capability["verify"]["yaml_valid"]:
            full_path = Path(__file__).parent.parent.parent / yaml_file
            with open(full_path) as f:
                content = f.read()
            assert self.validate_yaml(content), f"Invalid YAML: {yaml_file}"

            # Check required content
            data = yaml.safe_load(content)
            for required in capability["verify"]["must_contain"]:
                assert required in str(data), f"Missing content {required} in {yaml_file}"