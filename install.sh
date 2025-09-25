#!/bin/bash
# TORQ CONSOLE Installation Script

echo "🚀 Installing TORQ CONSOLE..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Install in development mode
pip install -e .

# Install optional dependencies
echo "Installing optional dependencies..."
pip install SpeechRecognition pyttsx3 pyaudio openai-whisper pygments pillow

echo "✅ TORQ CONSOLE installation complete!"
echo ""
echo "🎯 Quick Start:"
echo "  torq --help                    # Show help"
echo "  torq --interactive             # Start interactive mode"
echo "  torq --web                     # Launch web UI"
echo "  torq edit 'your message'       # AI-assisted editing"
echo ""
echo "🔗 Connect your existing MCP infrastructure:"
echo "  torq mcp --endpoint http://localhost:3100  # Hybrid MCP Server"
echo "  torq mcp --endpoint http://localhost:3101  # N8N Proxy Server"
echo ""
echo "📖 Documentation: https://github.com/pilotwaffle/TORQ-CONSOLE"