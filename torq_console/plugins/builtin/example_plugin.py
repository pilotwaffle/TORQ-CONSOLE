"""
Example Plugin for TORQ Console

Demonstrates how to create a plugin with multiple capabilities.
"""

from torq_console.plugins.base import TORQPlugin, PluginMetadata, PluginHook, PluginCapability
from typing import Dict, Any, Optional, List


class ExamplePlugin(TORQPlugin):
    """Example plugin demonstrating TORQ Console plugin system."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="example",
            version="1.0.0",
            description="An example plugin demonstrating the plugin system",
            author="TORQ Console Team",
            dependencies=[],
            capabilities=[
                PluginCapability.COMMAND_EXTENSION
            ],
            hooks=[
                PluginHook.ON_COMMAND_EXECUTE,
                PluginHook.ON_CONSOLE_START
            ]
        )

    def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize the example plugin."""
        self.console = context.get("console")
        self.config = context.get("config", {})

        # Register custom command
        if hasattr(self.console, 'register_command'):
            self.console.register_command("example", self._example_command, "Run an example plugin command")

    def shutdown(self) -> None:
        """Cleanup when plugin is unloaded."""
        pass

    def get_hook_callbacks(self, hook: PluginHook) -> Optional[List[callable]]:
        """
        Return hook callbacks for this plugin.

        Args:
            hook: The hook being registered

        Returns:
            List of callbacks or None
        """
        if hook == PluginHook.ON_CONSOLE_START:
            return [self._on_console_start]
        if hook == PluginHook.ON_COMMAND_EXECUTE:
            return [self._on_command_execute]
        return None

    def _example_command(self, args: List[str]) -> str:
        """Handle the example command."""
        return f"""
Example Plugin Command
====================

This is a custom command provided by the example plugin.

Arguments received: {args}

Plugin capabilities:
- Command extension
- Hook integration
- Metadata support

For more information on creating plugins, see the plugin documentation.
        """

    def _on_console_start(self, context: Dict[str, Any]) -> None:
        """Called when TORQ Console starts."""
        print(f"[Example Plugin] TORQ Console starting with example plugin v{self.metadata.version}")

    def _on_command_execute(self, command: str, args: List[str], result: Any) -> None:
        """Called when any command is executed."""
        # Just log it, don't modify behavior
        pass


def get_plugin() -> ExamplePlugin:
    """Plugin entry point."""
    return ExamplePlugin()
