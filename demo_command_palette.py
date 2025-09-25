#!/usr/bin/env python3
"""
Demo script for TORQ CONSOLE Command Palette System v0.70.0 - Phase 4

This script demonstrates the integration of all phases:
- Phase 1: ContextManager
- Phase 2: InlineEditor
- Phase 3: ChatManager
- Phase 4: CommandPalette

Shows the command palette system working with fuzzy search,
keyboard shortcuts, and integration with all existing systems.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any

# Mock implementations for demo
class MockConfig:
    def __init__(self):
        self.ai_model = "claude-sonnet-4"
        self.workspace_path = Path("E:\\TORQ-CONSOLE")
        self.debug = True

class MockContextManager:
    async def get_context_summary(self) -> Dict[str, Any]:
        return {
            "active_contexts": 3,
            "tree_sitter_available": True
        }

    async def clear_context(self):
        print("✓ Context cleared")

class MockInlineEditor:
    def get_edit_statistics(self) -> Dict[str, Any]:
        return {
            "ghost_suggestions": 5,
            "total_edits": 12
        }

class MockChatManager:
    def __init__(self):
        self.active_tab_id = "tab-123"
        self.active_tabs = {
            "tab-123": MockChatTab()
        }

    async def create_new_tab(self, **kwargs):
        print("✓ Created new chat tab")
        return MockChatTab()

    async def initialize(self):
        print("✓ ChatManager initialized")

class MockChatTab:
    def __init__(self):
        self.id = "tab-123"
        self.title = "Demo Chat"
        self.model = "claude-sonnet-4"
        self.messages = []

async def demo_command_palette():
    """Demonstrate the command palette system integration."""
    print("🚀 TORQ CONSOLE v0.70.0 - Phase 4 Command Palette Demo")
    print("=" * 60)

    # Mock dependencies
    config = MockConfig()
    context_manager = MockContextManager()
    chat_manager = MockChatManager()
    inline_editor = MockInlineEditor()

    # Import and initialize command palette
    try:
        from torq_console.ui.command_palette import CommandPalette

        print("\n📋 Initializing Command Palette...")
        command_palette = CommandPalette(
            config=config,
            context_manager=context_manager,
            chat_manager=chat_manager,
            inline_editor=inline_editor
        )

        await command_palette.initialize()
        print("✓ Command Palette initialized successfully")

        # Show statistics
        stats = await command_palette.get_palette_statistics()
        print(f"\n📊 Command Palette Statistics:")
        print(f"   Total Commands: {stats.get('total_commands', 0)}")
        print(f"   Categories: {list(stats.get('categories', {}).keys())}")
        print(f"   Shortcuts: {stats.get('shortcuts', 0)}")
        print(f"   Favorites: {stats.get('favorites', 0)}")

        # Demo 1: Open command palette and search
        print(f"\n🔍 Demo 1: Opening Command Palette")
        palette_data = await command_palette.open_palette()
        if palette_data["success"]:
            print(f"✓ Command palette opened with {len(palette_data['results'])} commands")

            # Show sample commands
            print(f"\n📋 Available Commands (first 5):")
            for i, result in enumerate(palette_data["results"][:5]):
                cmd = result["command"]
                shortcuts = " | ".join([s["key"] for s in cmd.get("shortcuts", [])])
                print(f"   {i+1}. {cmd['title']} ({cmd['category']})")
                print(f"      📝 {cmd['description']}")
                if shortcuts:
                    print(f"      ⌨️  {shortcuts}")
                print()

        # Demo 2: Fuzzy search
        print(f"\n🔍 Demo 2: Fuzzy Search - 'chat'")
        search_results = await command_palette.search_commands("chat")
        print(f"✓ Found {len(search_results)} commands matching 'chat':")
        for result in search_results[:3]:
            cmd = result.command
            print(f"   • {cmd.title} (score: {result.score:.2f})")

        # Demo 3: Execute commands
        print(f"\n⚡ Demo 3: Executing Commands")

        # Execute a chat command
        execution = await command_palette.execute_command("chat.new_tab")
        if execution.success:
            print(f"✓ Executed 'New Chat Tab' in {execution.duration_ms}ms")
        else:
            print(f"❌ Failed to execute: {execution.error}")

        # Execute a context command
        execution = await command_palette.execute_command("context.clear_all")
        if execution.success:
            print(f"✓ Executed 'Clear Context' in {execution.duration_ms}ms")
        else:
            print(f"❌ Failed to execute: {execution.error}")

        # Demo 4: Keyboard shortcuts
        print(f"\n⌨️  Demo 4: Keyboard Shortcut Integration")

        # Simulate Ctrl+Shift+P
        shortcut_execution = await command_palette.execute_shortcut("ctrl+shift+p")
        if shortcut_execution:
            print(f"✓ Ctrl+Shift+P executed: {shortcut_execution.command_id}")
        else:
            print("❌ No command found for Ctrl+Shift+P")

        # Simulate Ctrl+K
        shortcut_execution = await command_palette.execute_shortcut("ctrl+k")
        if shortcut_execution:
            print(f"✓ Ctrl+K executed: {shortcut_execution.command_id}")
        else:
            print("❌ No command found for Ctrl+K")

        # Demo 5: Context-aware commands
        print(f"\n🎯 Demo 5: Context-Aware Commands")

        # Show commands available in current context
        context_summary = await context_manager.get_context_summary()
        print(f"Current context: {context_summary}")

        # Search for AI commands (should be available when code is selected)
        ai_results = await command_palette.search_commands("ai")
        print(f"✓ Found {len(ai_results)} AI commands")
        for result in ai_results[:2]:
            cmd = result.command
            print(f"   • {cmd.title}: {cmd.description}")

        # Demo 6: Integration showcase
        print(f"\n🔗 Demo 6: Integration with All Phases")
        print(f"✓ Phase 1 (ContextManager): {context_summary['active_contexts']} active contexts")
        print(f"✓ Phase 2 (InlineEditor): {inline_editor.get_edit_statistics()['ghost_suggestions']} ghost suggestions")
        print(f"✓ Phase 3 (ChatManager): Chat system with active tab '{chat_manager.active_tab_id}'")
        print(f"✓ Phase 4 (CommandPalette): {stats.get('total_commands', 0)} commands registered")

        # Demo 7: TypeScript interfaces for frontend
        print(f"\n💻 Demo 7: TypeScript Interface Generation")
        print(f"The frontend uses these TypeScript interfaces:")
        print(f"""
interface CommandResult {{
  command: Command;
  score: number;
  match_positions: [number, number][];
  match_type: 'title' | 'description' | 'tag' | 'category';
}}

interface Command {{
  id: string;
  title: string;
  category: string;
  type: string;
  description: string;
  icon: string;
  shortcuts: CommandShortcut[];
  is_favorite: boolean;
  tags: string[];
}}

interface CommandShortcut {{
  key: string;
  mac?: string;
  when?: WhenClause[];
}}
        """)

        # Close command palette
        close_result = await command_palette.close_palette()
        if close_result["success"]:
            print(f"✓ Command palette closed")

        print(f"\n🎉 Demo completed successfully!")
        print(f"Command Palette Phase 4 is fully integrated with:")
        print(f"   • Fuzzy search with intelligent ranking")
        print(f"   • Context-aware command filtering")
        print(f"   • Windows keyboard shortcuts (Ctrl+Shift+P)")
        print(f"   • Integration with ContextManager, ChatManager, InlineEditor")
        print(f"   • Extensible command registration system")
        print(f"   • Professional VSCode-like UI design")

        # Cleanup
        await command_palette.shutdown()
        print(f"✓ Command palette shut down cleanly")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print(f"Make sure the command_palette.py file is in the correct location")
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

async def demo_frontend_integration():
    """Demonstrate frontend integration points."""
    print(f"\n🌐 Frontend Integration Demo")
    print(f"=" * 40)

    # Show how the frontend would interact with the command palette
    frontend_api_calls = [
        "GET /api/command-palette/commands",
        "POST /api/command-palette/search",
        "POST /api/command-palette/execute",
        "GET /api/command-palette/recent",
        "GET /api/command-palette/favorites",
        "GET /api/command-palette/stats"
    ]

    print(f"Available API endpoints:")
    for endpoint in frontend_api_calls:
        print(f"   • {endpoint}")

    print(f"\nKeyboard shortcuts implemented:")
    shortcuts = [
        "Ctrl+Shift+P - Open Command Palette",
        "Ctrl+K - Inline Edit",
        "Ctrl+T - New Chat Tab",
        "Ctrl+W - Close Chat Tab",
        "Alt+Enter - Quick Question",
        "Ctrl+. - Code Actions"
    ]

    for shortcut in shortcuts:
        print(f"   • {shortcut}")

    print(f"\nAlpine.js integration points:")
    alpine_features = [
        "showCommandPalette - Controls visibility",
        "commandPaletteQuery - Search input binding",
        "filteredCommandResults - Search results",
        "commandSelectedIndex - Keyboard navigation",
        "executeCommand() - Command execution",
        "handleCommandPaletteKeys() - Keyboard handling"
    ]

    for feature in alpine_features:
        print(f"   • {feature}")

if __name__ == "__main__":
    asyncio.run(demo_command_palette())
    asyncio.run(demo_frontend_integration())