"""
File monitoring utilities for TORQ CONSOLE.
"""

import asyncio
from pathlib import Path
from typing import Callable, Optional
import logging


class FileMonitor:
    """File system monitor for TORQ CONSOLE."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.callbacks = []

    def add_callback(self, callback: Callable):
        """Add a callback for file changes."""
        self.callbacks.append(callback)

    async def start(self):
        """Start monitoring files."""
        self.running = True
        self.logger.info(f"Started file monitoring for {self.repo_path}")

    async def stop(self):
        """Stop monitoring files."""
        self.running = False
        self.logger.info("Stopped file monitoring")