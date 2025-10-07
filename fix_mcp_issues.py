#!/usr/bin/env python3
"""
Fix MCP Unicode and Windows command execution issues
"""
import re
import os

def fix_unicode_issues():
    """Fix Unicode emoji issues in MCP commands"""
    mcp_commands_file = "torq_console/mcp/mcp_commands.py"

    if not os.path.exists(mcp_commands_file):
        print(f"File not found: {mcp_commands_file}")
        return

    with open(mcp_commands_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix Unicode emojis
    replacements = [
        ('✅', 'PASS'),
        ('❌', 'FAIL'),
        ('🟢', 'ONLINE'),
        ('🔴', 'OFFLINE'),
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    with open(mcp_commands_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Fixed Unicode issues in {mcp_commands_file}")

def fix_windows_command_execution():
    """Fix Windows npx command execution"""
    mcp_manager_file = "torq_console/mcp/mcp_manager.py"

    if not os.path.exists(mcp_manager_file):
        print(f"File not found: {mcp_manager_file}")
        return

    with open(mcp_manager_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add Windows command handling
    old_code = '''        try:
            if server_config['type'] == 'stdio':
                # Start stdio server process
                process = await asyncio.create_subprocess_exec(
                    server_config['command'],
                    *server_config['args'],
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ, **server_config.get('env', {})}
                )'''

    new_code = '''        try:
            if server_config['type'] == 'stdio':
                # Handle Windows command execution
                command = server_config['command']
                if os.name == 'nt' and command == 'npx':
                    command = 'npx.cmd'

                # Start stdio server process
                process = await asyncio.create_subprocess_exec(
                    command,
                    *server_config['args'],
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ, **server_config.get('env', {})}
                )'''

    if old_code in content:
        content = content.replace(old_code, new_code)

        with open(mcp_manager_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Fixed Windows command execution in {mcp_manager_file}")
    else:
        print(f"Target code not found in {mcp_manager_file}")

if __name__ == "__main__":
    print("Fixing MCP Unicode and Windows command execution issues...")
    fix_unicode_issues()
    fix_windows_command_execution()
    print("COMPLETE Fixes applied!")