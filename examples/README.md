# TORQ CONSOLE Examples

This directory contains examples and tutorials for using TORQ CONSOLE.

## Basic Usage

### 1. Configuration
```python
from torq_console.core.config import TorqConfig

# Create default configuration
config = TorqConfig()

# Save configuration
config.save()

# Load configuration
config = TorqConfig.load()
```

### 2. MCP Integration
```python
from torq_console.mcp.client import MCPClient

# Connect to MCP server
client = MCPClient("mcp://github", "your_token")
await client.connect()

# Call a tool
result = await client.call_tool("search_repositories", {
    "query": "python AI",
    "language": "python"
})
```

### 3. Command Line Interface
```bash
# Start interactive mode
torq --interactive

# Connect to MCP endpoint
torq --mcp-connect mcp://your-server.com

# Enable voice commands
torq --voice-shortcuts

# Start ideation mode
torq --ideate

# Process specific files
torq file1.py file2.py
```

## Advanced Examples

See the `examples/` directory for more detailed examples and tutorials.