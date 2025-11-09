#!/usr/bin/env python3
"""
Simple script to fix Unicode characters in Zep setup guide.
"""

def fix_unicode():
    file_path = "E:/TORQ-CONSOLE/maxim_integration/zep_setup_guide.py"

    # Read the file with utf-8 encoding
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace Unicode characters with ASCII equivalents
    replacements = {
        '✓': '[OK]',
        '✗': '[ERROR]',
        '⚠️': '[WARNING]',
        '→': '->',
        '•': '-'
    }

    for unicode_char, replacement in replacements.items():
        content = content.replace(unicode_char, replacement)

    # Write back with utf-8 encoding
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Fixed Unicode characters in zep_setup_guide.py")

if __name__ == "__main__":
    fix_unicode()