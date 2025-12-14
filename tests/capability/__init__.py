"""
Capability Tests - Verify all TORQ Console claims with evidence

These tests validate that every capability claimed in docs/capabilities.yml
actually works and produces verifiable artifacts.
"""

import pytest
import sys
import os
from pathlib import Path
import subprocess
import json
import yaml
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

CAPABILITY_CONTRACT = Path(__file__).parent.parent.parent / "docs" / "capabilities.yml"

class CapabilityTest:
    """Base class for capability tests"""

    @classmethod
    def setup_class(cls):
        """Load the capability contract"""
        with open(CAPABILITY_CONTRACT) as f:
            cls.contract = yaml.safe_load(f)

    def run_command(self, cmd, timeout=30, cwd=None):
        """Run command and return result"""
        if cwd is None:
            cwd = Path(__file__).parent.parent.parent

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
        full_path = Path(__file__).parent.parent.parent / path
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