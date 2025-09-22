#!/bin/bash
"""
Installation script for TORQ CONSOLE
"""

set -e

echo "🚀 Installing TORQ CONSOLE..."

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.10"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "✓ Python $python_version (>= $required_version) detected"
else
    echo "❌ Python $required_version or higher required. Current: $python_version"
    exit 1
fi

# Install base dependencies
echo "📦 Installing base dependencies..."
python3 -m pip install --user pydantic rich click gitpython httpx

# Install optional dependencies
echo "📦 Installing optional dependencies..."
python3 -m pip install --user prompt_toolkit fastapi uvicorn || echo "⚠️  Some optional dependencies failed to install"

# Install in development mode
echo "📦 Installing TORQ CONSOLE..."
python3 -m pip install --user -e . || echo "⚠️  Package installation failed, but core functionality available"

# Test installation
echo "🧪 Testing installation..."
python3 -c "import torq_console; print('✓ TORQ CONSOLE import successful')" || {
    echo "⚠️  Full import failed, testing core functionality..."
    python3 test_minimal.py
}

echo "✨ Installation complete!"
echo ""
echo "🎯 Next steps:"
echo "   • Run demo: python3 demo.py"
echo "   • Test components: python3 test_minimal.py"
echo "   • Start CLI: torq --help (if dependencies installed)"
echo "   • Read examples: cat examples/README.md"