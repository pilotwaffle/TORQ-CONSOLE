"""
Pytest configuration for Layer 12 tests.
"""

import pytest


def pytest_configure(config):
    """Configure pytest for Layer 12 tests."""
    import sys
    sys.path.insert(0, "E:/TORQ-CONSOLE")


# Configure pytest-asyncio to run async tests without explicit event loop
pytest_plugins = ("pytest_asyncio",)
