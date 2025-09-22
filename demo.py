#!/usr/bin/env python3
"""
Demo script showing TORQ CONSOLE core functionality.
"""

import sys
import json
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_configuration():
    """Demonstrate configuration management."""
    print("\n🔧 Configuration Management Demo")
    print("-" * 40)
    
    from torq_console.core.config import TorqConfig, AIModelConfig, MCPEndpoint
    
    # Create default configuration
    config = TorqConfig()
    print(f"📁 Project root: {config.project_root}")
    print(f"💾 Cache directory: {config.cache_dir}")
    print(f"🤖 Default AI model: {config.default_model}")
    print(f"🔇 Telemetry disabled: {not config.telemetry_enabled}")
    
    # Add custom MCP endpoint
    custom_endpoint = MCPEndpoint(
        name="custom_server",
        url="mcp://custom.example.com",
        auth_type="bearer",
        token="secret_token"
    )
    config.mcp_endpoints.append(custom_endpoint)
    
    print(f"🔌 Added custom MCP endpoint: {custom_endpoint.name}")
    
    # Add custom AI model
    custom_model = AIModelConfig(
        provider="ollama",
        model="codellama:13b",
        base_url="http://localhost:11434"
    )
    config.ai_models.append(custom_model)
    
    print(f"🧠 Added custom AI model: {custom_model.provider}:{custom_model.model}")
    
    # Save and load configuration
    config_file = Path("/tmp/torq_demo_config.json")
    config.save(config_file)
    print(f"💾 Saved configuration to: {config_file}")
    
    # Load configuration
    loaded_config = TorqConfig.load(config_file)
    print(f"📂 Loaded configuration with {len(loaded_config.mcp_endpoints)} MCP endpoints")
    
    return config

def demo_mcp_client():
    """Demonstrate MCP client functionality."""
    print("\n🔌 MCP Client Demo")
    print("-" * 40)
    
    from torq_console.mcp.client import MCPClient, MCPTool, JSONRPCRequest
    
    # Create JSON-RPC request
    protocol = JSONRPCRequest()
    
    requests = [
        protocol.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            "clientInfo": {"name": "torq-console", "version": "0.60.0"}
        }),
        protocol.request("tools/list", {}),
        protocol.request("tools/call", {
            "name": "github_search",
            "arguments": {"query": "python MCP", "type": "repositories"}
        })
    ]
    
    for i, request in enumerate(requests, 1):
        print(f"📤 Request {i}: {json.loads(request)['method']}")
    
    # Create MCP client
    client = MCPClient("mcp://github.example.com", "gh_token_123")
    print(f"🔗 Created MCP client for: {client.endpoint_url}")
    
    # Create example tools
    tools = [
        MCPTool(
            name="github_search",
            description="Search GitHub repositories",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "type": {"type": "string", "enum": ["repositories", "issues", "users"]}
                }
            }
        ),
        MCPTool(
            name="postgres_query", 
            description="Execute PostgreSQL queries",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "database": {"type": "string"}
                }
            }
        )
    ]
    
    for tool in tools:
        print(f"🛠️  Available tool: {tool.name} - {tool.description}")
    
    return client

def demo_git_manager():
    """Demonstrate Git manager functionality."""
    print("\n📂 Git Manager Demo") 
    print("-" * 40)
    
    from torq_console.utils.git import GitManager
    
    # Create Git manager for current project
    git_manager = GitManager(project_root)
    
    # Initialize Git repository access
    async def git_demo():
        await git_manager.initialize()
        
        if git_manager.is_repo():
            print(f"📁 Git repository detected")
            print(f"🌿 Current branch: {git_manager.current_branch()}")
            
            # Get file information
            tracked_files = git_manager.get_tracked_files()
            modified_files = git_manager.get_modified_files()
            untracked_files = git_manager.get_untracked_files()
            
            print(f"📄 Tracked files: {len(tracked_files)}")
            print(f"✏️  Modified files: {len(modified_files)}")
            print(f"❓ Untracked files: {len(untracked_files)}")
            
            # Show some tracked files
            if tracked_files:
                print("📋 Recent tracked files:")
                for file_path in tracked_files[:5]:
                    rel_path = file_path.relative_to(project_root)
                    print(f"   • {rel_path}")
                if len(tracked_files) > 5:
                    print(f"   ... and {len(tracked_files) - 5} more")
                    
        else:
            print("❌ No Git repository found")
    
    # Run async demo
    asyncio.run(git_demo())
    
    return git_manager

def demo_project_overview():
    """Show project overview."""
    print("\n🚀 TORQ CONSOLE Project Overview")
    print("=" * 50)
    
    from torq_console import __version__, __author__, __license__
    
    print(f"📦 Version: {__version__}")
    print(f"👤 Author: {__author__}")
    print(f"📜 License: {__license__}")
    
    # Count lines of code
    total_lines = 0
    python_files = list(project_root.rglob("*.py"))
    
    for py_file in python_files:
        if ".git" not in str(py_file) and "__pycache__" not in str(py_file):
            try:
                lines = len(py_file.read_text().splitlines())
                total_lines += lines
            except:
                pass
    
    print(f"📊 Python files: {len(python_files)}")
    print(f"📏 Lines of code: ~{total_lines}")
    
    # Show main modules
    modules = [
        ("Core", "Configuration, main console, logging"),
        ("MCP", "Model Context Protocol client and manager"),
        ("UI", "Interactive shell and web interface"),
        ("Utils", "Git manager, AI integration"),
        ("Plugins", "Extensible plugin system"),
    ]
    
    print("\n📁 Main Modules:")
    for module, description in modules:
        print(f"   🔹 {module}: {description}")

def main():
    """Run the demo."""
    try:
        demo_project_overview()
        
        config = demo_configuration()
        client = demo_mcp_client() 
        git_manager = demo_git_manager()
        
        print("\n✨ Demo completed successfully!")
        print("\n🎯 Next Steps:")
        print("   1. Install full dependencies: pip install -e .")
        print("   2. Run: torq --help")
        print("   3. Try interactive mode: torq --interactive")
        print("   4. Connect to MCP: torq --mcp-connect mcp://your-server")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())