#!/usr/bin/env python3
"""
Fix Unicode encoding issues in TORQ Console files
"""

import re
from pathlib import Path

def fix_unicode_in_file(file_path):
    """Replace Unicode characters with ASCII equivalents in a file"""

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace Unicode characters with ASCII equivalents
        replacements = {
            '✅': '[OK]',
            '⚠️': '[WARN]',
            '❌': '[ERROR]',
            '🔍': '[SEARCH]',
            '💬': '[CHAT]',
            '🚀': '[START]',
            '🤖': '[BOT]',
            '🌐': '[WEB]',
            '🎉': '[SUCCESS]',
            '💥': '[FAIL]',
            '🔧': '[FIX]',
            '📝': '[INFO]',
            '📊': '[STATUS]',
            '📋': '[LIST]',
            '📄': '[RESPONSE]',
        }

        original_content = content
        for unicode_char, ascii_replacement in replacements.items():
            content = content.replace(unicode_char, ascii_replacement)

        if content != original_content:
            # Backup the original
            backup_path = file_path.with_suffix(file_path.suffix + '.unicode_backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            print(f"Backup created: {backup_path}")

            # Write the fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"Fixed Unicode characters in: {file_path}")
            return True
        else:
            print(f"No Unicode characters found in: {file_path}")
            return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix Unicode issues in key TORQ Console files"""

    files_to_fix = [
        'torq_integration.py',
        'start_torq_with_fixes.py',
        'debug_route_registration.py',
        'test_direct_endpoint_simple.py'
    ]

    print("Fixing Unicode encoding issues...")
    print("=" * 40)

    for filename in files_to_fix:
        file_path = Path(filename)
        fix_unicode_in_file(file_path)
        print()

    print("Unicode fix complete!")
    print("You can now run the debug scripts without encoding errors.")

if __name__ == "__main__":
    main()