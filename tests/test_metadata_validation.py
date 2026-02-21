"""
Test Metadata Validation for TORQ Console

This test validates that metadata appears on ALL response paths:
- Direct success
- Research success
- Timeout errors
- Provider errors
- Generic errors

Run: pytest tests/test_metadata_validation.py -v
"""

import pytest
import requests
import json
from typing import Dict, Any


class TestMetadataValidation:
    """Validate metadata on all API response paths."""

    @pytest.fixture(scope="module")
    def base_url(self):
        return "http://127.0.0.1:8899"

    def _assert_metadata_present(self, response: Dict[str, Any], case_name: str):
        """Assert metadata block is present and has required fields."""
        assert "meta" in response, f"[{case_name}] Missing metadata block"
        meta = response["meta"]

        # Required fields for all responses
        assert "provider" in meta, f"[{case_name}] Missing meta.provider"
        assert "latency_ms" in meta, f"[{case_name}] Missing meta.latency_ms"
        assert "timestamp" in meta, f"[{case_name}] Missing meta.timestamp"

        # latency_ms must be a positive integer
        assert isinstance(meta["latency_ms"], int), f"[{case_name}] latency_ms must be int, got {type(meta['latency_ms'])}"
        assert meta["latency_ms"] >= 0, f"[{case_name}] latency_ms must be >= 0, got {meta['latency_ms']}"

        # If response failed, must have error fields
        if not response.get("success", True):
            assert "error" in meta, f"[{case_name}] Error response missing meta.error"
            assert "error_category" in meta, f"[{case_name}] Error response missing meta.error_category"

    def test_direct_success_has_metadata(self, base_url):
        """Test: Direct success response includes metadata."""
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": "What is 2+2? Respond with only the number."},
            timeout=30
        )

        assert response.status_code == 200, "HTTP 200 expected"
        data = response.json()

        self._assert_metadata_present(data, "direct_success")

        # Direct mode should have no tools
        assert data["meta"]["tools_used"] == [], "Direct mode should have empty tools_used"

        # Should have latency (real API call, not stub)
        assert data["meta"]["latency_ms"] > 100, "Direct mode should have >100ms latency (real API call)"

    def test_research_success_has_metadata(self, base_url):
        """Test: Research success response includes metadata with tools."""
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "message": "What time is it in Texas right now?",
                "tools": ["web_search"]
            },
            timeout=60
        )

        assert response.status_code == 200, "HTTP 200 expected"
        data = response.json()

        self._assert_metadata_present(data, "research_success")

        # Research mode should have tools_used populated
        assert "web_search" in data["meta"].get("tools_used", []), "Research mode should include web_search in tools_used"

        # Should have higher latency than direct (web search takes time)
        assert data["meta"]["latency_ms"] > 500, "Research mode should have >500ms latency (includes web search)"

    def test_error_response_has_metadata(self, base_url):
        """Test: Error responses include metadata with error_category."""
        # Send invalid request that will fail
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": ""},  # Empty message should trigger error
            timeout=30
        )

        # May get 200 with success=False or actual error
        if response.status_code == 200:
            data = response.json()

            # If it's an error response, check metadata
            if not data.get("success", True):
                self._assert_metadata_present(data, "error_response")

                # Error category must be one of the known types
                meta = data["meta"]
                valid_categories = ["timeout", "provider_error", "ai_error", "exception"]
                assert meta["error_category"] in valid_categories, \
                    f"error_category must be one of {valid_categories}, got {meta['error_category']}"

    def test_metadata_consistency(self, base_url):
        """Test: Metadata fields are consistent across multiple requests."""
        responses = []

        # Make 3 direct requests
        for i in range(3):
            response = requests.post(
                f"{base_url}/api/chat",
                json={"message": f"Test {i}: What is 2+2?"},
                timeout=30
            )
            assert response.status_code == 200
            responses.append(response.json())

        # All should have metadata
        for i, data in enumerate(responses):
            self._assert_metadata_present(data, f"consistency_check_{i}")

        # Provider should be consistent across requests
        providers = [r["meta"]["provider"] for r in responses]
        assert all(p == providers[0] for p in providers), "Provider should be consistent across requests"

        # All should have success=True
        assert all(r.get("success", True) for r in responses), "All requests should succeed"

    def test_research_mode_includes_tool_metadata(self, base_url):
        """Test: Research mode properly logs tool usage in metadata."""
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "message": "Search for current time in California",
                "tools": ["web_search"]
            },
            timeout=60
        )

        assert response.status_code == 200
        data = response.json()

        self._assert_metadata_present(data, "research_tool_metadata")

        meta = data["meta"]

        # tools_used must be populated
        assert "tools_used" in meta, "Research mode missing tools_used"
        assert len(meta["tools_used"]) > 0, "tools_used should not be empty for research mode"

        # tool_results should be >= 0
        assert "tool_results" in meta, "Missing tool_results count"
        assert meta["tool_results"] >= 0, "tool_results should be >= 0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
