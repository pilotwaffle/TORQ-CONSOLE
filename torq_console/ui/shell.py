"""
Interactive shell interface for TORQ CONSOLE.
"""

import asyncio
from typing import Optional
import logging


class InteractiveShell:
    """Interactive shell for TORQ CONSOLE."""

    def __init__(self, console):
        self.console = console
        self.logger = logging.getLogger(__name__)

    async def run(self):
        """Run the interactive shell."""
        self.logger.info("Starting interactive shell...")

        print("TORQ CONSOLE Interactive Shell")
        print("Type 'help' for commands, 'exit' to quit")
        print("Prince Flowers Enhanced Agent integrated - try 'prince help'")

        while True:
            try:
                command = input("torq> ").strip()

                if command.lower() in ['exit', 'quit']:
                    break
                elif command.lower() == 'help':
                    self.show_help()
                elif command:
                    await self.process_command(command)

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                break

    def show_help(self):
        """Show help information."""
        help_text = """
TORQ CONSOLE Commands:

**General Commands:**
  help              - Show this help
  status            - Show repository status
  diff              - Show visual diff
  edit <message>    - Start AI-assisted editing
  connect <endpoint> - Connect MCP server
  session           - Show session info
  exit/quit         - Exit shell

**Prince Flowers Enhanced Agent:**
  prince <query>          - Query the enhanced agentic RL agent
  prince search <topic>   - Search for information with web capabilities
  prince status          - Show agent performance metrics
  prince health          - Check agent system health
  prince capabilities    - Show detailed capabilities
  prince help           - Show Prince Flowers specific help
  @prince <query>       - Alternative command format

**Examples:**
  prince search latest AI developments
  prince analyze machine learning trends
  @prince what is agentic reinforcement learning
  prince status

Type any query after 'prince' to interact with the enhanced agent!
        """
        print(help_text)

    async def process_command(self, command: str):
        """Process a shell command."""
        # Route to the console's command processor
        try:
            result = await self.console.process_command(command)
            # Result is already displayed by the console's rich formatting
            # Only print result if it's not already formatted
            if not command.lower().startswith('prince ') and not command.lower().startswith('@prince '):
                if result and result not in ["Edit succeeded", "Edit failed"]:
                    print(result)
        except Exception as e:
            print(f"Error processing command: {e}")
            self.logger.error(f"Shell command error: {e}")

    async def process_command_legacy(self, command: str):
        """Legacy command processing - keeping for reference."""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == 'status':
            status = await self.console.git_manager.get_status()
            print(f"Repository status: {status}")
        elif cmd == 'diff':
            diff = await self.console.get_visual_diff()
            print(diff)
        elif cmd == 'edit' and len(parts) > 1:
            message = ' '.join(parts[1:])
            success = await self.console.edit_files(message=message)
            print(f"Edit {'succeeded' if success else 'failed'}")
        elif cmd == 'session':
            info = self.console.get_session_info()
            print(f"Session info: {info}")
        elif cmd == 'connect' and len(parts) > 1:
            endpoint = parts[1]
            success = await self.console.connect_mcp(endpoint)
            print(f"MCP connection {'succeeded' if success else 'failed'}")
        else:
            print(f"Unknown command: {command}")
            print("Type 'help' for available commands")