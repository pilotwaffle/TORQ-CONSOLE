#!/usr/bin/env python3
"""
Minimal TORQ Console CLI
Bypasses Marvin import issues for basic functionality
"""

import sys
import os
from pathlib import Path

# Add torq_console to path
sys.path.insert(0, str(Path(__file__).parent))

def show_banner():
    """Show TORQ Console banner"""
    print("""
    ____ ____ ____ ____ ____ ____
    ||T |||O |||R |||Q |||C |||O |
    ||__|||__|||__|||__|||__|||__|
    |/__\\|/__\\|/__\\|/__\\|/__\\|/__\\

    TORQ Console - Advanced AI Pair Programmer
    Version 0.70.0
    ==========================================
    """)

def show_help():
    """Show help information"""
    print("""
TORQ Console Commands:

Basic Usage:
  torq-cli <command> [options]

Available Commands:
  status      - Show TORQ Console status
  test        - Run basic tests
  docs        - Open documentation
  web         - Start web interface (if available)

Environment Variables:
  OPENAI_API_KEY      - OpenAI API key
  ANTHROPIC_API_KEY   - Anthropic API key
  MARVIN_API_KEY      - Marvin API key (if using Marvin features)

For full functionality, use: python -m torq_console.cli
    """)

def show_status():
    """Show system status"""
    print("\nSystem Status:")
    print("-" * 40)

    # Check Python
    print(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Check core modules
    core_modules = ['click', 'rich', 'pydantic', 'anthropic', 'openai']
    for module in core_modules:
        try:
            __import__(module)
            print(f"{module}: OK")
        except ImportError:
            print(f"{module}: MISSING")

    # Check TORQ modules
    print("\nTORQ Modules:")
    torq_modules = ['core', 'llm', 'ui', 'utils', 'agents']
    for module in torq_modules:
        path = Path(f"torq_console/{module}")
        if path.exists():
            print(f"{module}: EXISTS")
        else:
            print(f"{module}: MISSING")

    # Check documentation
    print("\nDocumentation:")
    docs = ['README.md', 'CLAUDE.md', 'SECURITY.md', 'CONTRIBUTING.md']
    for doc in docs:
        if Path(doc).exists():
            print(f"{doc}: EXISTS")
        else:
            print(f"{doc}: MISSING")

def run_tests():
    """Run basic tests"""
    print("\nRunning Basic Tests...")
    print("-" * 40)

    # Import test
    try:
        # Try to import basic modules without Marvin
        from torq_console.utils import advanced_web_search
        from torq_console.llm import manager
        print("Core imports: OK")
    except Exception as e:
        print(f"Core imports: FAILED - {e}")

    # File structure test
    required_files = [
        "torq_console/__init__.py",
        "torq_console/core/console.py",
        "torq_console/llm/manager.py",
        "README.md"
    ]

    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)

    if missing:
        print(f"Missing files: {len(missing)}")
        for file in missing:
            print(f"  - {file}")
    else:
        print("Required files: ALL PRESENT")

def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        show_banner()
        show_help()
        return

    command = sys.argv[1].lower()

    if command == 'help' or command == '-h' or command == '--help':
        show_help()
    elif command == 'status':
        show_status()
    elif command == 'test':
        run_tests()
    elif command == 'docs':
        if Path('README.md').exists():
            print("Opening README.md...")
            os.startfile('README.md')
        else:
            print("README.md not found")
    else:
        print(f"Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()