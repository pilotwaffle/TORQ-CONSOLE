"""
Test that the capability contract parses correctly
"""

import pytest
import sys
import yaml
from pathlib import Path

class TestContractParses:
    """Test the capability contract file is valid"""

    def test_contract_file_exists(self):
        """Test capability contract file exists"""
        contract_path = Path(__file__).parent.parent.parent / "docs" / "capabilities.yml"
        assert contract_path.exists(), f"Contract file not found at {contract_path}"

    def test_contract_is_valid_yaml(self):
        """Test contract file is valid YAML"""
        contract_path = Path(__file__).parent.parent.parent / "docs" / "capabilities.yml"
        with open(contract_path) as f:
            content = f.read()

        # Should not raise exception
        data = yaml.safe_load(content)
        assert isinstance(data, dict), "Contract should be a dictionary"

    def test_contract_has_required_sections(self):
        """Test contract has required sections"""
        contract_path = Path(__file__).parent.parent.parent / "docs" / "capabilities.yml"
        with open(contract_path) as f:
            contract = yaml.safe_load(f)

        # Check required top-level keys
        required_keys = ["version", "personas", "capabilities"]
        for key in required_keys:
            assert key in contract, f"Missing required key: {key}"

    def test_capabilities_have_required_fields(self):
        """Test each capability has required fields"""
        contract_path = Path(__file__).parent.parent.parent / "docs" / "capabilities.yml"
        with open(contract_path) as f:
            contract = yaml.safe_load(f)

        for capability in contract["capabilities"]:
            # Each capability should have these fields
            required_fields = ["id", "personas", "category", "description", "verify"]
            for field in required_fields:
                assert field in capability, f"Capability {capability.get('id', 'unknown')} missing field: {field}"

            # Verify field is not empty
            assert capability["id"], "Capability ID cannot be empty"
            assert capability["personas"], "Capability personas cannot be empty"
            assert capability["verify"], "Capability verify section cannot be empty"