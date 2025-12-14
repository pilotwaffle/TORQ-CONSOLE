"""
Test negative cases - commands should fail appropriately
"""

import pytest
import subprocess
import os
from pathlib import Path
from tests.capability import CapabilityTest

class TestNegativeCases(CapabilityTest):
    """Test that commands fail correctly with proper error messages"""

    @pytest.mark.capability
    def test_eval_requires_set(self):
        """Test evaluation command requires --set parameter"""
        capability_id = "eval_requires_set"

        capability = next(c for c in self.contract["capabilities"] if c["id"] == capability_id)

        # Run command without --set
        result = subprocess.run(
            "torq eval",
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )

        assert result.returncode == capability["verify"]["exit_code"]

        # Check for error message
        error_output = result.stderr or result.stdout
        for required in capability["verify"]["error_contains"]:
            assert required in error_output, f"Expected error message not found: {required}"

    @pytest.mark.capability
    def test_eval_invalid_set(self):
        """Test evaluation rejects invalid set names"""
        capability_id = "eval_invalid_set"

        capability = next(c for c in self.contract["capabilities"] if c["id"] == capability_id)

        # Run command with invalid set
        result = subprocess.run(
            "torq eval --set nonexistent",
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )

        assert result.returncode == capability["verify"]["exit_code"]

        # Check for error message
        error_output = result.stderr or result.stdout
        for required in capability["verify"]["error_contains"]:
            assert required in error_output, f"Expected error message not found: {required}"