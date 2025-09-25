"""
Unicode-safe utilities for Windows compatibility.
"""

import sys
import unicodedata
from typing import Any


def safe_print(*args, **kwargs) -> None:
    """
    Print function that safely handles Unicode on Windows Command Prompt.

    Falls back to ASCII-safe alternatives when Unicode is not supported.
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Convert args to ASCII-safe versions
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_args.append(unicode_to_ascii(arg))
            else:
                safe_args.append(str(arg))
        print(*safe_args, **kwargs)


def unicode_to_ascii(text: str) -> str:
    """
    Convert Unicode text to ASCII-safe equivalent.

    Replaces common Unicode characters with ASCII alternatives.
    """
    replacements = {
        '🚀': '[ROCKET]',
        '🤖': '[AI]',
        '✅': '[OK]',
        '❌': '[FAIL]',
        '⚡': '[FAST]',
        '🎯': '[TARGET]',
        '📊': '[CHART]',
        '🔧': '[TOOL]',
        '💻': '[COMPUTER]',
        '📋': '[CLIPBOARD]',
        '🔍': '[SEARCH]',
        '📝': '[NOTE]',
        '⌨️': '[KEYBOARD]',
        '🎉': '[PARTY]',
        '🌐': '[GLOBE]',
        '🔗': '[LINK]',
        '📖': '[BOOK]'
    }

    result = text
    for unicode_char, ascii_replacement in replacements.items():
        result = result.replace(unicode_char, ascii_replacement)

    return result


def is_unicode_supported() -> bool:
    """
    Check if the current terminal supports Unicode output.
    """
    try:
        sys.stdout.write('✓')
        sys.stdout.flush()
        return True
    except UnicodeEncodeError:
        return False


def get_encoding_info() -> dict:
    """
    Get information about the current encoding setup.
    """
    return {
        'stdout_encoding': getattr(sys.stdout, 'encoding', 'unknown'),
        'default_encoding': sys.getdefaultencoding(),
        'unicode_supported': is_unicode_supported(),
        'platform': sys.platform
    }