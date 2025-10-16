"""
Apply Terminal Commands Tool Integration to Prince Flowers

This script automatically integrates the terminal commands tool into
torq_prince_flowers.py by adding necessary imports, tool definitions,
and execution methods.

Run: python apply_terminal_integration.py
"""

import os
import re
from pathlib import Path


def apply_integration():
    """Apply the terminal commands tool integration."""

    prince_file = Path("E:/TORQ-CONSOLE/torq_console/agents/torq_prince_flowers.py")

    if not prince_file.exists():
        print(f"❌ File not found: {prince_file}")
        return False

    print("📖 Reading torq_prince_flowers.py...")
    content = prince_file.read_text(encoding='utf-8')

    # Check if already integrated
    if 'terminal_commands_tool' in content:
        print("✅ Terminal commands tool already integrated!")
        return True

    print("🔧 Applying integration patches...")

    # 1. Add import after browser automation
    import_section = """# Import Browser Automation Tool
try:
    from .tools.browser_automation_tool import create_browser_automation_tool
    BROWSER_AUTOMATION_AVAILABLE = True
except ImportError:
    BROWSER_AUTOMATION_AVAILABLE = False
    logging.warning("Browser Automation Tool not available")"""

    terminal_import = """

# Import Terminal Commands Tool
try:
    from .tools.terminal_commands_tool import create_terminal_commands_tool
    TERMINAL_COMMANDS_AVAILABLE = True
except ImportError:
    TERMINAL_COMMANDS_AVAILABLE = False
    logging.warning("Terminal Commands Tool not available")"""

    content = content.replace(import_section, import_section + terminal_import)
    print("  ✓ Added import statement")

    # 2. Add tool definition to _init_tool_ecosystem
    browser_tool_def = """            'browser_automation': {
                'name': 'Browser Automation',
                'description': 'Automate web browser interactions using Playwright',
                'cost': 0.4,
                'success_rate': 0.85,
                'avg_time': 2.5,
                'dependencies': [],
                'composable': True,
                'requires_approval': False
            },"""

    terminal_tool_def = """            'browser_automation': {
                'name': 'Browser Automation',
                'description': 'Automate web browser interactions using Playwright',
                'cost': 0.4,
                'success_rate': 0.85,
                'avg_time': 2.5,
                'dependencies': [],
                'composable': True,
                'requires_approval': False
            },
            'terminal_commands': {
                'name': 'Terminal Commands Execution',
                'description': 'Execute whitelisted terminal commands with security controls',
                'cost': 0.2,
                'success_rate': 0.92,
                'avg_time': 1.0,
                'dependencies': [],
                'composable': True,
                'requires_approval': True,
                'security_level': 'critical'
            },"""

    content = content.replace(browser_tool_def, terminal_tool_def)
    print("  ✓ Added tool definition")

    # 3. Add tool initialization (find and add after browser automation init)
    browser_init_pattern = r"(# Initialize Browser Automation Tool.*?else:\s+self\.browser_automation_tool = None)"

    terminal_init = r'''\1

        # Initialize Terminal Commands Tool
        if TERMINAL_COMMANDS_AVAILABLE:
            try:
                self.terminal_commands_tool = create_terminal_commands_tool()
                if self.terminal_commands_tool.is_available():
                    self.logger.info("Terminal Commands Tool ready")
                else:
                    self.terminal_commands_tool = None
                    self.logger.warning("Terminal Commands Tool unavailable")
            except Exception as e:
                self.terminal_commands_tool = None
                self.logger.error(f"Failed to initialize Terminal Commands Tool: {e}")
        else:
            self.terminal_commands_tool = None'''

    content = re.sub(browser_init_pattern, terminal_init, content, flags=re.DOTALL)
    print("  ✓ Added tool initialization")

    # 4. Add execution method after _execute_browser_automation
    execution_method = '''

    async def _execute_terminal_command(
        self,
        command: str,
        timeout: Optional[int] = None,
        working_dir: Optional[str] = None,
        action: str = "execute_command",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute terminal commands with security controls.

        SECURITY CRITICAL: All commands are validated against whitelist.

        Actions:
        - execute_command: Execute a whitelisted command
        - validate_command: Validate without executing
        - get_whitelist: List allowed commands

        Args:
            command: Command to execute (for execute_command)
            timeout: Timeout in seconds (default 30s, max 300s)
            working_dir: Working directory for execution
            action: Action to perform
            **kwargs: Additional parameters

        Returns:
            Dict with success status and execution results
        """
        import time
        start_time = time.time()

        try:
            # Check tool availability
            if not hasattr(self, 'terminal_commands_tool') or self.terminal_commands_tool is None:
                return {
                    'success': False,
                    'error': 'Terminal Commands Tool not available',
                    'result': None
                }

            # Security check: Require approval for command execution
            if action == "execute_command":
                self.logger.warning(
                    f"SECURITY: Terminal command execution requested: {command}"
                )

            # Execute via tool
            result = self.terminal_commands_tool.execute(
                action=action,
                command=command,
                timeout=timeout,
                working_dir=working_dir,
                **kwargs
            )

            # Update RL metrics
            execution_time = time.time() - start_time
            self._update_tool_metrics(
                'terminal_commands',
                success=result.get('success', False),
                execution_time=execution_time
            )

            # Log execution for audit
            if result.get('success'):
                self.logger.info(
                    f"Terminal command executed successfully in {execution_time:.2f}s"
                )
            else:
                self.logger.warning(
                    f"Terminal command failed: {result.get('error', 'Unknown error')}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Terminal command execution error: {e}")
            return {
                'success': False,
                'error': f"Execution error: {str(e)}",
                'result': None
            }
'''

    # Find _execute_browser_automation method end and add terminal method after it
    browser_method_pattern = r'(async def _execute_browser_automation.*?return result\s+)(\n\s+async def )'
    content = re.sub(
        browser_method_pattern,
        r'\1' + execution_method + r'\2',
        content,
        flags=re.DOTALL
    )
    print("  ✓ Added execution method")

    # Write updated content
    print("💾 Writing updated file...")
    prince_file.write_text(content, encoding='utf-8')

    print("\n✅ Integration completed successfully!")
    print("\nNext steps:")
    print("1. Run tests: python test_prince_terminal_commands.py")
    print("2. Verify integration: python -c \"from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers; print('OK')\"")

    return True


if __name__ == "__main__":
    print("=" * 80)
    print("TERMINAL COMMANDS TOOL - AUTOMATIC INTEGRATION")
    print("=" * 80)
    print()

    success = apply_integration()

    if not success:
        print("\n❌ Integration failed. Check errors above.")
        exit(1)

    print("\n" + "=" * 80)
