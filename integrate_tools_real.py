#!/usr/bin/env python3
"""
Integration script to add the final 3 tools to Prince Flowers agent.
"""
import os
import sys

def integrate_tools():
    """Integrate the 3 tools into Prince Flowers."""
    
    file_path = 'torq_console/agents/torq_prince_flowers.py'
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already integrated
    if 'TERMINAL_COMMANDS_AVAILABLE' in content:
        print("WARNING: Tools already integrated! Skipping...")
        return False
    
    # Step 1: Add imports after Browser Automation imports
    import_marker = 'logging.warning("Browser Automation Tool not available")\n\n\nclass ReasoningMode(Enum):'
    
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


class ReasoningMode(Enum):'''
    
    if import_marker in content:
        content = content.replace(import_marker, new_imports)
        print("Step 1: Added imports")
    else:
        print("ERROR: Could not find import marker")
        return False
    
    # Step 2: Add registry entries
    browser_automation_entry = """            'browser_automation': {
                'name': 'Browser Automation',
                'description': 'Automate web browser interactions using Playwright',
                'cost': 0.4,
                'success_rate': 0.85,
                'avg_time': 2.5,
                'dependencies': [],
                'composable': True,
                'requires_approval': False
            },"""
    
    new_entries = """            'browser_automation': {
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
                'description': 'Orchestrate complex workflows with multiple tools',
                'cost': 0.4,
                'success_rate': 0.92,
                'avg_time': 3.0,
                'dependencies': [],
                'composable': False,
                'requires_approval': False,
                'advanced': True
            },"""
    
    if browser_automation_entry in content:
        content = content.replace(browser_automation_entry, new_entries)
        print("Step 2: Added registry entries")
    else:
        print("ERROR: Could not find browser_automation entry")
        return False
    
    # Write the modified content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Step 3: File written successfully")
    print(f"New file size: {len(content)} characters")
    
    return True

if __name__ == '__main__':
    print("Starting integration...")
    success = integrate_tools()
    
    if success:
        print("\n=== Integration Steps 1 & 2 Complete ===")
        print("Added imports and registry entries")
        print("\nNote: Execute methods and routing need to be added manually.")
        print("See add_final_tools_patch.txt for complete instructions.")
        sys.exit(0)
    else:
        print("\n=== Integration Failed ===")
        sys.exit(1)
