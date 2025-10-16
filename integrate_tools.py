"""
Script to integrate the final 3 tools into Prince Flowers agent.
"""

# Read the original file
with open('torq_console/agents/torq_prince_flowers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Add imports after line 95 (after Browser Automation imports)
imports_marker = "logging.warning(\"Browser Automation Tool not available\")\n\n\nclass ReasoningMode"
new_imports = '''logging.warning("Browser Automation Tool not available")

# Terminal Commands Tool - Phase 1.8
try:
    from .tools.terminal_commands_tool import create_terminal_commands_tool
    TERMINAL_COMMANDS_AVAILABLE = True
except ImportError:
    TERMINAL_COMMANDS_AVAILABLE = False
    logging.warning("Terminal Commands Tool not available")

# MCP Client Tool - Phase 1.9
try:
    from .tools.mcp_client_tool import create_mcp_client_tool
    MCP_CLIENT_AVAILABLE = True
except ImportError:
    MCP_CLIENT_AVAILABLE = False
    logging.warning("MCP Client Tool not available")

# Multi-Tool Composition Tool - Phase 1.10
try:
    from .tools.multi_tool_composition_tool import create_multi_tool_composition_tool
    MULTI_TOOL_COMPOSITION_AVAILABLE = True
except ImportError:
    MULTI_TOOL_COMPOSITION_AVAILABLE = False
    logging.warning("Multi-Tool Composition Tool not available")


class ReasoningMode'''

content = content.replace(imports_marker, new_imports)

# Step 2: Add registry entries in available_tools dictionary
# Find the browser_automation entry and add after it
browser_automation_block = '''            'browser_automation': {
                'name': 'Browser Automation',
                'description': 'Automate web browser interactions using Playwright',
                'cost': 0.4,
                'success_rate': 0.85,
                'avg_time': 2.5,
                'dependencies': [],
                'composable': True,
                'requires_approval': False
            },'''

new_tools_block = '''            'browser_automation': {
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
                'name': 'Terminal Commands',
                'description': 'Execute whitelisted terminal commands with security controls',
                'cost': 0.2,
                'success_rate': 0.95,
                'avg_time': 1.0,
                'dependencies': [],
                'composable': True,
                'requires_approval': True,
                'security_level': 'high'
            },
            'mcp_client': {
                'name': 'MCP Client Integration',
                'description': 'Connect to MCP servers and invoke their tools and resources',
                'cost': 0.3,
                'success_rate': 0.90,
                'avg_time': 2.0,
                'dependencies': [],
                'composable': True,
                'requires_approval': False
            },
            'multi_tool_composition': {
                'name': 'Multi-Tool Composition',
                'description': 'Orchestrate complex workflows with multiple tools (sequential, parallel, conditional, loop, map/reduce)',
                'cost': 0.4,
                'success_rate': 0.92,
                'avg_time': 3.0,
                'dependencies': [],
                'composable': False,
                'requires_approval': False,
                'advanced': True
            },'''

content = content.replace(browser_automation_block, new_tools_block)

print("✓ Step 1 & 2: Added imports and registry entries")

# Write the modified content
with open('torq_console/agents/torq_prince_flowers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ File written with imports and registry")
print(f"✓ New file size: {len(content)} characters")
