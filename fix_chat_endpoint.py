#!/usr/bin/env python3
"""
Quick fix for the missing /api/chat endpoint by ensuring proper model registration
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def fix_web_ui_chat_endpoint():
    """Fix the missing /api/chat endpoint issue in web.py"""

    web_py_path = Path("torq_console/ui/web.py")

    if not web_py_path.exists():
        print(f"ERROR: {web_py_path} not found!")
        return False

    # Read the current content
    with open(web_py_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # The issue is likely that DirectChatRequest is not properly imported or defined
    # Let's move the DirectChatRequest model definition before the route setup

    # Find the current location of DirectChatRequest
    lines = content.split('\n')

    # Find where DirectChatRequest is currently defined
    directchat_start = -1
    directchat_end = -1

    for i, line in enumerate(lines):
        if 'class DirectChatRequest(BaseModel):' in line:
            directchat_start = i
            # Find the end of this class
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('\t'):
                    directchat_end = j
                    break
            break

    if directchat_start == -1:
        print("ERROR: DirectChatRequest class not found!")
        return False

    print(f"Found DirectChatRequest at lines {directchat_start} to {directchat_end}")

    # Extract the DirectChatRequest class
    directchat_class = lines[directchat_start:directchat_end]

    # Remove it from its current location
    lines = lines[:directchat_start] + lines[directchat_end:]

    # Find where to insert it (after imports, before WebUI class)
    insert_pos = -1
    for i, line in enumerate(lines):
        if 'class WebUI:' in line:
            insert_pos = i
            break

    if insert_pos == -1:
        print("ERROR: WebUI class not found!")
        return False

    print(f"Inserting DirectChatRequest before WebUI class at line {insert_pos}")

    # Insert DirectChatRequest before WebUI class
    lines = lines[:insert_pos] + [''] + directchat_class + [''] + lines[insert_pos:]

    # Now also fix the route definition to not use quotes around DirectChatRequest
    for i, line in enumerate(lines):
        if 'async def direct_chat(request: "DirectChatRequest"):' in line:
            lines[i] = line.replace('"DirectChatRequest"', 'DirectChatRequest')
            print(f"Fixed route definition at line {i}")
            break

    # Write the fixed content back
    fixed_content = '\n'.join(lines)

    # Backup the original file
    backup_path = web_py_path.with_suffix('.py.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Backup created: {backup_path}")

    # Write the fixed version
    with open(web_py_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print("SUCCESS: Fixed /api/chat endpoint registration issue!")
    print("The DirectChatRequest model has been moved before the WebUI class definition.")
    print("Please restart the TORQ Console server to apply the fix.")
    return True

def main():
    print("TORQ Console /api/chat Endpoint Fix")
    print("=" * 50)

    if fix_web_ui_chat_endpoint():
        print("\nNext steps:")
        print("1. Kill the current TORQ server")
        print("2. Restart with: python start_torq_with_fixes.py")
        print("3. Test the /api/chat endpoint")
    else:
        print("\nFIX FAILED - Manual intervention required")

if __name__ == "__main__":
    main()