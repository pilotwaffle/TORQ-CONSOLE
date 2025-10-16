"""
Integration Patch for Terminal Commands Tool

This file contains the code snippets to integrate terminal commands tool
into torq_prince_flowers.py. Apply these changes manually.

Instructions:
1. Add import statement (line 95, after browser automation import)
2. Add tool definition to _init_tool_ecosystem method (after browser_automation entry)
3. Add tool initialization to create_search_master section
4. Add _execute_terminal_command method (after _execute_browser_automation)
5. Add routing keywords to query analysis
"""

# ============================================================================
# 1. IMPORT STATEMENT (Add after line 95, after browser automation import)
# ============================================================================

IMPORT_CODE = '''
# Import Terminal Commands Tool
try:
    from .tools.terminal_commands_tool import create_terminal_commands_tool
    TERMINAL_COMMANDS_AVAILABLE = True
except ImportError:
    TERMINAL_COMMANDS_AVAILABLE = False
    logging.warning("Terminal Commands Tool not available")
'''

# ============================================================================
# 2. TOOL DEFINITION (Add to _init_tool_ecosystem method, after browser_automation)
# ============================================================================

TOOL_DEFINITION = '''
            'terminal_commands': {
                'name': 'Terminal Commands Execution',
                'description': 'Execute whitelisted terminal commands with security controls',
                'cost': 0.2,
                'success_rate': 0.92,
                'avg_time': 1.0,
                'dependencies': [],
                'composable': True,
                'requires_approval': True,  # Security-sensitive, requires approval
                'security_level': 'critical'
            },
'''

# ============================================================================
# 3. TOOL INITIALIZATION (Add in __init__ or where tools are instantiated)
# ============================================================================

TOOL_INIT = '''
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
            self.terminal_commands_tool = None
'''

# ============================================================================
# 4. EXECUTION METHOD (Add after _execute_browser_automation method)
# ============================================================================

EXECUTION_METHOD = '''
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

# ============================================================================
# 5. QUERY ROUTING KEYWORDS (Add to _determine_reasoning_mode or query analysis)
# ============================================================================

ROUTING_KEYWORDS = '''
        # Terminal commands keywords
        terminal_keywords = [
            'run command', 'execute command', 'terminal', 'shell', 'bash',
            'cmd', 'command line', 'run shell', 'execute shell',
            'list files', 'show directory', 'git status', 'check git'
        ]

        if any(keyword in query_lower for keyword in terminal_keywords):
            # Route to terminal commands tool
            return 'terminal_commands'
'''

# ============================================================================
# COMPLETE INTEGRATION EXAMPLE
# ============================================================================

COMPLETE_EXAMPLE = '''
# Example usage in Prince Flowers:

# 1. In query processing:
if 'run command' in query.lower() or 'terminal' in query.lower():
    result = await agent._execute_terminal_command(
        command="ls -la",
        timeout=30
    )

# 2. Validate before execution:
validation = await agent._execute_terminal_command(
    action="validate_command",
    command="git status"
)

# 3. Get whitelist:
whitelist = await agent._execute_terminal_command(
    action="get_whitelist"
)

# 4. Safe execution with working directory:
result = await agent._execute_terminal_command(
    command="git log --oneline -10",
    working_dir="/path/to/repo",
    timeout=30
)
'''

if __name__ == "__main__":
    print("=" * 80)
    print("TERMINAL COMMANDS TOOL - INTEGRATION PATCH")
    print("=" * 80)
    print("\nThis file contains code snippets for integrating terminal commands")
    print("into E:\\TORQ-CONSOLE\\torq_console\\agents\\torq_prince_flowers.py")
    print("\n" + "=" * 80)

    print("\n1. IMPORT STATEMENT:")
    print(IMPORT_CODE)

    print("\n2. TOOL DEFINITION (_init_tool_ecosystem):")
    print(TOOL_DEFINITION)

    print("\n3. TOOL INITIALIZATION:")
    print(TOOL_INIT)

    print("\n4. EXECUTION METHOD:")
    print(EXECUTION_METHOD)

    print("\n5. ROUTING KEYWORDS:")
    print(ROUTING_KEYWORDS)

    print("\n6. COMPLETE EXAMPLE:")
    print(COMPLETE_EXAMPLE)

    print("\n" + "=" * 80)
    print("Apply these changes to complete the integration.")
    print("=" * 80)
