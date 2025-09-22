#!/usr/bin/env python3
"""
Minimal test runner that tests core functionality without complex dependencies.
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_core_config():
    """Test core configuration."""
    try:
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
        
        # Test serialization
        config_dict = config.to_dict()
        print(f"✓ Config serialization: {len(config_dict)} keys")
        
        # Test loading from dict
        config2 = TorqConfig.from_dict(config_dict)
        print(f"✓ Config deserialization: {config2.project_root}")
        
        return True
        
    except Exception as e:
        print(f"✗ Core config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_client():
    """Test MCP client creation."""
    try:
        from torq_console.mcp.client import MCPClient, MCPTool, JSONRPCRequest
        
        # Test JSON-RPC request builder
        protocol = JSONRPCRequest()
        request = protocol.request("test_method", {"param": "value"})
        request_data = json.loads(request)
        print(f"✓ JSON-RPC request: {request_data['method']}")
        
        # Test MCP client creation
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
        import traceback
        traceback.print_exc()
        return False

def test_git_manager():
    """Test Git manager."""
    try:
        from torq_console.utils.git import GitManager
        
        git_manager = GitManager(project_root)
        print("✓ Git manager created")
        
        # Test basic initialization without async
        # Skip async parts for now due to missing dependencies
        
        return True
        
    except Exception as e:
        print(f"✗ Git manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_project_structure():
    """Test project structure."""
    try:
        expected_dirs = [
            "torq_console",
            "torq_console/core",
            "torq_console/mcp", 
            "torq_console/ui",
            "torq_console/utils",
            "torq_console/plugins",
        ]
        
        expected_files = [
            "pyproject.toml",
            "README.md",
            "LICENSE",
            ".gitignore",
            "torq_console/__init__.py",
            "torq_console/cli.py",
            "torq_console/core/config.py",
            "torq_console/core/console.py",
            "torq_console/core/logger.py",
            "torq_console/mcp/client.py",
            "torq_console/mcp/manager.py",
            "torq_console/utils/git.py",
            "torq_console/utils/ai.py",
        ]
        
        missing_dirs = []
        missing_files = []
        
        for directory in expected_dirs:
            dir_path = project_root / directory
            if not dir_path.exists():
                missing_dirs.append(directory)
        
        for file_path in expected_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_dirs:
            print(f"✗ Missing directories: {missing_dirs}")
            return False
        
        if missing_files:
            print(f"✗ Missing files: {missing_files}")
            return False
        
        print(f"✓ Project structure complete: {len(expected_dirs)} dirs, {len(expected_files)} files")
        return True
        
    except Exception as e:
        print(f"✗ Project structure test failed: {e}")
        return False

def test_readme_content():
    """Test README content."""
    try:
        readme_path = project_root / "README.md"
        content = readme_path.read_text()
        
        required_sections = [
            "# TORQ CONSOLE",
            "## 🚀 Why TORQ CONSOLE?",
            "## ✨ Key Features",
            "### 🟢 P0 – MCP Core",
            "### 🟡 P1 – Intuitiveness & Ideation", 
            "### 🔵 P2 – Polish",
            "## 🔧 Tech Stack",
            "## 📌 Status",
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"✗ Missing README sections: {missing_sections}")
            return False
        
        print(f"✓ README content complete: {len(required_sections)} sections")
        return True
        
    except Exception as e:
        print(f"✗ README test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 TORQ CONSOLE - Minimal Component Tests")
    print("=" * 50)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("README Content", test_readme_content),
        ("Core Config", test_core_config),
        ("MCP Client", test_mcp_client),
        ("Git Manager", test_git_manager),
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