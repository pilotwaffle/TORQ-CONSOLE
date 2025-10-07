#!/usr/bin/env python3
"""
Test Enhanced MCP Integration for TORQ Console
Tests the complete MCP integration including manager, commands, and console integration
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'torq_console'))

from torq_console.mcp.enhanced_integration import EnhancedMCPIntegration
from torq_console.core.config import TorqConfig


async def test_enhanced_mcp_integration():
    """Test the enhanced MCP integration functionality"""
    print("Testing Enhanced MCP Integration for TORQ Console")
    print("=" * 60)

    # Test 1: Initialize Enhanced MCP Integration
    print("\n1. Testing Enhanced MCP Integration Initialization...")
    try:
        enhanced_mcp = EnhancedMCPIntegration()
        await enhanced_mcp.initialize()
        print("PASS Enhanced MCP Integration initialized successfully")
    except Exception as e:
        print(f"FAIL Failed to initialize: {e}")
        return

    # Test 2: Test Command Interface
    print("\n2. Testing MCP Command Interface...")
    try:
        # Test help command
        help_result = await enhanced_mcp.handle_mcp_command("help", [])
        print(f"PASS Help command result: {len(help_result)} characters")

        # Test list servers command
        list_result = await enhanced_mcp.handle_mcp_command("list", [])
        print(f"PASS List servers command result: {len(list_result)} characters")

        # Test status command
        status_result = await enhanced_mcp.handle_mcp_command("status", [])
        print(f"PASS Status command result: {len(status_result)} characters")

    except Exception as e:
        print(f"FAIL Command interface test failed: {e}")

    # Test 3: Test Server Management
    print("\n3. Testing Server Management...")
    try:
        # Add a test server
        enhanced_mcp.add_server("test_server", {
            "type": "stdio",
            "command": "echo",
            "args": ["test"]
        })
        print("PASS Added test server successfully")

        # List configured servers
        servers = enhanced_mcp.get_configured_servers()
        print(f"PASS Configured servers: {list(servers.keys())}")

        # Remove test server
        enhanced_mcp.remove_server("test_server")
        print("PASS Removed test server successfully")

    except Exception as e:
        print(f"FAIL Server management test failed: {e}")

    # Test 4: Test Integration Info
    print("\n4. Testing Integration Information...")
    try:
        info = enhanced_mcp.get_integration_info()
        print(f"PASS Integration info:")
        print(f"   - Initialized: {info['initialized']}")
        print(f"   - Enhanced servers: {info['enhanced_servers']}")
        print(f"   - Active connections: {info['active_enhanced_connections']}")
        print(f"   - Legacy connections: {info['legacy_connections']}")

    except Exception as e:
        print(f"FAIL Integration info test failed: {e}")

    # Test 5: Test Health Check
    print("\n5. Testing Health Check...")
    try:
        health = await enhanced_mcp.health_check()
        print(f"PASS Health check completed: {len(health)} components checked")

    except Exception as e:
        print(f"FAIL Health check test failed: {e}")

    # Test 6: Test Default Server Templates
    print("\n6. Testing Default Server Templates...")
    try:
        # Test adding popular server types
        server_types = ["github", "filesystem", "postgres", "sqlite"]

        for server_type in server_types:
            try:
                result = await enhanced_mcp.handle_mcp_command("add", [f"test_{server_type}", server_type])
                if "PASS" in result:
                    print(f"PASS Successfully added {server_type} server template")
                    # Clean up
                    enhanced_mcp.remove_server(f"test_{server_type}")
                else:
                    print(f"WARNING  {server_type} server template: {result}")
            except Exception as e:
                print(f"FAIL Failed to add {server_type} server: {e}")

    except Exception as e:
        print(f"FAIL Server template test failed: {e}")

    # Cleanup
    print("\n7. Cleanup...")
    try:
        await enhanced_mcp.shutdown()
        print("PASS Enhanced MCP Integration shutdown completed")
    except Exception as e:
        print(f"FAIL Shutdown failed: {e}")

    print("\nSUCCESS Enhanced MCP Integration Test Completed!")
    print("\nNext Steps:")
    print("1. Test with TORQ Console: Use /mcp commands in the console")
    print("2. Test with Command Palette: Access MCP commands via Ctrl+Shift+P")
    print("3. Connect to real MCP servers and test functionality")
    print("4. Verify Claude Code compatibility")


async def test_torq_console_integration():
    """Test integration with TORQ Console"""
    print("\n" + "=" * 60)
    print("Testing Testing TORQ Console Integration")
    print("=" * 60)

    try:
        # Import TORQ Console components
        from torq_console.core.console import TorqConsole
        from torq_console.core.config import TorqConfig
        from pathlib import Path

        # Create a minimal config
        config = TorqConfig.create_default()

        # Initialize console
        console = TorqConsole(
            config=config,
            repo_path=Path.cwd(),
            model="test-model"
        )

        print("PASS TORQ Console initialized successfully")

        # Test async initialization
        await console.initialize_async()
        print("PASS Console async initialization completed")

        # Test MCP command handling
        test_commands = [
            "/mcp list",
            "/mcp status",
            "/mcp help"
        ]

        for cmd in test_commands:
            try:
                result = await console.process_command(cmd)
                print(f"PASS Command '{cmd}' executed: {len(result)} characters response")
            except Exception as e:
                print(f"FAIL Command '{cmd}' failed: {e}")

        # Test enhanced MCP access
        if hasattr(console, 'enhanced_mcp'):
            info = console.enhanced_mcp.get_integration_info()
            print(f"PASS Console has enhanced MCP integration: {info['initialized']}")
        else:
            print("FAIL Console missing enhanced MCP integration")

        print("PASS TORQ Console integration test completed successfully")

    except Exception as e:
        print(f"FAIL TORQ Console integration test failed: {e}")


if __name__ == "__main__":
    print("Starting Enhanced MCP Integration Tests...")
    asyncio.run(test_enhanced_mcp_integration())
    asyncio.run(test_torq_console_integration())
    print("\nCOMPLETE All tests completed! Check the output above for results.")