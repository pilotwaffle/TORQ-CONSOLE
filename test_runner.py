#!/usr/bin/env python3
"""
Simple test runner for TORQ CONSOLE without requiring full installation.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """Test basic imports."""
    try:
        # Test core config
        from torq_console.core.config import TorqConfig, AIModelConfig, MCPEndpoint
        print("✓ Core config import successful")
        
        # Test basic configuration
        config = TorqConfig()
        print(f"✓ Created default config with project root: {config.project_root}")
        
        # Test MCP endpoint creation
        endpoint = MCPEndpoint(name="test", url="mcp://test")
        print(f"✓ Created MCP endpoint: {endpoint.name}")
        
        # Test AI model config
        ai_model = AIModelConfig(provider="openai", model="gpt-4o")
        print(f"✓ Created AI model config: {ai_model.provider}:{ai_model.model}")
        
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def test_git_manager():
    """Test Git manager."""
    try:
        from torq_console.utils.git import GitManager
        
        git_manager = GitManager(project_root)
        print("✓ Git manager created")
        
        # Test if current directory is a repo
        import asyncio
        asyncio.run(git_manager.initialize())
        is_repo = git_manager.is_repo()
        print(f"✓ Git repository check: {is_repo}")
        
        if is_repo:
            branch = git_manager.current_branch()
            print(f"✓ Current branch: {branch}")
        
        return True
        
    except Exception as e:
        print(f"✗ Git manager test failed: {e}")
        return False

def test_mcp_client():
    """Test MCP client creation."""
    try:
        from torq_console.mcp.client import MCPClient, MCPTool
        
        client = MCPClient("mcp://test", "dummy_token")
        print("✓ MCP client created")
        
        # Test tool creation
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object"}
        )
        print(f"✓ MCP tool created: {tool.name}")
        
        return True
        
    except Exception as e:
        print(f"✗ MCP client test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 TORQ CONSOLE - Basic Component Tests")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Git Manager", test_git_manager),
        ("MCP Client", test_mcp_client),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())