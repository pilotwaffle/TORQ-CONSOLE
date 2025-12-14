#!/usr/bin/env python3
"""
TORQ Console - Rich Terminal UI with Google Antigravity Theme
"""

import asyncio
import sys
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import time

# Rich imports
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.text import Text
from rich.prompt import Prompt
from rich.rule import Rule
from rich.live import Live
from rich.align import Align
from rich.padding import Padding
from rich.box import ROUNDED, DOUBLE, HEAVY
from rich.status import Status
from rich.syntax import Syntax
from rich.tree import Tree
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.measure import Measurement

# TORQ imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from torq_console.core.config import TorqConfig
from torq_console.core.console import TorqConsole

# TORQ Brand Colors
TORQ_COLORS = {
    "primary": "#FF6B35",      # Orange
    "secondary": "#1E3A5F",    # Dark Blue
    "accent": "#FFD23F",       # Yellow
    "success": "#00D9FF",      # Light Blue
    "warning": "#FFB347",      # Light Orange
    "error": "#FF6B6B",        # Light Red
    "background": "#0A0E27",   # Very Dark Blue
    "surface": "#1A1F3A",      # Dark surface
    "text": "#E0E0E0",         # Light Gray
    "text_dim": "#A0A0A0",     # Dimmed Gray
}

class TORQTerminalUI:
    """Rich Terminal UI for TORQ Console with Google Antigravity Theme"""

    def __init__(self):
        # Rich console with custom colors
        self.console = Console(
            color_system="truecolor",
            style=None,  # Remove background style that's causing issues
            file=None
        )

        # Initialize TORQ components
        self.console_initialized = False
        self.torq_console = None

        # UI state
        self.layout = Layout()
        self.message_history = []
        self.current_prompt = ""

        # Create theme styles
        self.create_styles()

    def create_styles(self):
        """Create Rich styles for TORQ theme"""
        self.styles = {
            "title": f"bold {TORQ_COLORS['primary']}",
            "subtitle": f"{TORQ_COLORS['secondary']}",
            "accent": f"bold {TORQ_COLORS['accent']}",
            "success": f"bold {TORQ_COLORS['success']}",
            "warning": f"bold {TORQ_COLORS['warning']}",
            "error": f"bold {TORQ_COLORS['error']}",
            "dim": TORQ_COLORS['text_dim'],
            "text": TORQ_COLORS['text'],
            "panel": f"bg {TORQ_COLORS['surface']} {TORQ_COLORS['text']}",
            "border": TORQ_COLORS['primary'],
            "prompt": f"{TORQ_COLORS['accent']}",
            "message.user": f"{TORQ_COLORS['text']}",
            "message.assistant": f"{TORQ_COLORS['success']}",
            "message.system": f"{TORQ_COLORS['warning']}",
        }

    async def initialize(self):
        """Initialize TORQ Console and UI"""
        # Show loading screen
        self.show_loading_screen()

        # Initialize TORQ
        config = TorqConfig()
        self.torq_console = TorqConsole(config)
        await self.torq_console.initialize_async()
        self.console_initialized = True

        # Hide loading screen
        self.console.clear()

        # Show welcome message
        self.show_welcome()

    def show_loading_screen(self):
        """Show loading animation"""
        with self.console.status(
            "[bold magenta]Initializing TORQ Console...[/bold magenta]",
            spinner="dots12",
            spinner_style="magenta"
        ) as status:
            tasks = [
                "Loading AI models...",
                "Initializing agents...",
                "Connecting to MCP servers...",
                "Loading Prince Flowers agent...",
                "Preparing environment...",
            ]

            for task in tasks:
                time.sleep(0.5)
                status.update(f"[bold cyan]{task}[/bold cyan]")

    def show_welcome(self):
        """Show welcome message"""
        welcome_text = f"""
[{self.styles['title']}]+======================================================================+
|                                                                      |
|  [bold {TORQ_COLORS['primary']}]TORQ Console[/bold {TORQ_COLORS['primary']}] - [bold {TORQ_COLORS['secondary']}]AI-Powered Development[/bold {TORQ_COLORS['secondary']}]    |
|                                                                      |
|  [dim]Google Antigravity Theme • Advanced AI • Multi-Model[/dim]      |
|                                                                      |
+======================================================================+

[{self.styles['subtitle']}]Features Available:[/{self.styles['subtitle']}]"""

        self.console.print(welcome_text)

        features = Table.grid(padding=1)
        features.add_column(justify="left", style=self.styles['text'])
        features.add_row(f"• [bold {TORQ_COLORS['success']}][+][/bold {TORQ_COLORS['success']}] [bold]Claude Sonnet 4[/bold] - Advanced reasoning")
        features.add_row(f"• [bold {TORQ_COLORS['success']}][+][/bold {TORQ_COLORS['success']}] [bold]DeepSeek[/bold] - Code generation")
        features.add_row(f"• [bold {TORQ_COLORS['success']}][+][/bold {TORQ_COLORS['success']}] [bold]Ollama[/bold] - Local models")
        features.add_row(f"• [bold {TORQ_COLORS['success']}][+][/bold {TORQ_COLORS['success']}] [bold]Prince Flowers Agent[/bold] - Enhanced assistant")
        features.add_row(f"• [bold {TORQ_COLORS['success']}][+][/bold {TORQ_COLORS['success']}] [bold]MCP Integration[/bold] - Tool ecosystem")
        features.add_row(f"• [bold {TORQ_COLORS['success']}][+][/bold {TORQ_COLORS['success']}] [bold]Spec Kit[/bold] - Specification management")

        self.console.print(Padding(features, (1, 2)))
        self.console.print("-" * 70, style=TORQ_COLORS['primary'])

    def create_main_layout(self):
        """Create the main UI layout"""
        layout = Layout()

        # Create sections
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )

        layout["main"].split_row(
            Layout(name="sidebar", size=30),
            Layout(name="chat"),
            Layout(name="context", size=40)
        )

        return layout

    def render_header(self):
        """Render header panel"""
        header_content = Table.grid(padding=0)
        header_content.add_column(justify="left")
        header_content.add_column(justify="right")

        # Left side - Logo and title
        title = Text()
        title.append("T", style=f"bold {TORQ_COLORS['primary']}")
        title.append("O", style=f"bold {TORQ_COLORS['secondary']}")
        title.append("R", style=f"bold {TORQ_COLORS['accent']}")
        title.append("Q ", style="bold")
        title.append("Console", style=f"bold {TORQ_COLORS['text_dim']}")

        header_content.add_row(title, self.get_time())

        return Panel(
            header_content,
            style=f"bg {TORQ_COLORS['surface']}",
            border_style=TORQ_COLORS['primary'],
            box=ROUNDED
        )

    def render_sidebar(self):
        """Render sidebar with tools and info"""
        sidebar = Table.grid(padding=1)
        sidebar.add_column(justify="left")

        # Model Status
        sidebar.add_row(Text("[AI] AI Models", style=f"bold {TORQ_COLORS['accent']}"))
        models = [
            ("Claude", TORQ_COLORS['success'], "[+"),
            ("DeepSeek", TORQ_COLORS['success'], "[+"),
            ("Ollama", TORQ_COLORS['success'], "[+"),
            ("Prince Flowers", TORQ_COLORS['warning'], "[+"),
        ]
        for model, color, status in models:
            sidebar.add_row(f"  {status} [{color}]{model}[/{color}]")

        sidebar.add_row("")

        # Quick Commands
        sidebar.add_row(Text("[QUICK] Quick Actions", style=f"bold {TORQ_COLORS['accent']}"))
        actions = [
            ("[F1] Help", "dim"),
            ("[F2] Models", "dim"),
            ("[F3] Files", "dim"),
            ("[F4] Settings", "dim"),
        ]
        for action, style in actions:
            sidebar.add_row(f"  {action}")

        sidebar.add_row("")

        # Stats
        sidebar.add_row(Text("[STATS] Session Stats", style=f"bold {TORQ_COLORS['accent']}"))
        sidebar.add_row(f"  Messages: {len(self.message_history)}")
        sidebar.add_row(f"  Tokens: ~{len(self.message_history) * 100}")

        return Panel(
            sidebar,
            title="[bold]Tools[/bold]",
            style=f"bg {TORQ_COLORS['surface']}",
            border_style=TORQ_COLORS['primary'],
            box=ROUNDED
        )

    def render_chat(self):
        """Render chat messages"""
        chat_content = Table.grid(padding=1)
        chat_content.add_column(justify="left", style=self.styles['text'])

        # Add message history
        for msg in self.message_history[-10:]:  # Show last 10 messages
            if msg["role"] == "user":
                prefix = "[USER]"
                style = self.styles['message.user']
            elif msg["role"] == "assistant":
                prefix = "[AI]"
                style = self.styles['message.assistant']
            else:
                prefix = "[SYS]"
                style = self.styles['message.system']

            # Truncate long messages
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            chat_content.add_row(f"{prefix} [{style}]{content}[/{style}]")

        if not self.message_history:
            chat_content.add_row(
                f"[{self.styles['dim']}]No messages yet. Start chatting with TORQ![/{self.styles['dim']}]"
            )

        return Panel(
            Align.left(chat_content),
            title="[bold]Chat[/bold]",
            style=f"bg {TORQ_COLORS['surface']}",
            border_style=TORQ_COLORS['primary'],
            box=ROUNDED,
            padding=(1, 2)
        )

    def render_context(self):
        """Render context panel"""
        context = Table.grid(padding=1)
        context.add_column(justify="left")

        # Active Context
        context.add_row(Text("[FOLDER] Current Context", style=f"bold {TORQ_COLORS['accent']}"))
        context.add_row(f"  Project: TORQ-CONSOLE")
        context.add_row(f"  Path: E:\\TORQ-CONSOLE")
        context.add_row("")

        # Available Commands
        context.add_row(Text("[CHAT] Recent Commands", style=f"bold {TORQ_COLORS['accent']}"))
        recent_commands = [
            "help - Show all commands",
            "models - List available AI models",
            "prince - Chat with Prince Flowers",
            "files - Browse project files",
            "specs - Manage specifications",
        ]
        for cmd in recent_commands:
            context.add_row(f"  [dim]{cmd}[/dim]")

        return Panel(
            context,
            title="[bold]Context[/bold]",
            style=f"bg {TORQ_COLORS['surface']}",
            border_style=TORQ_COLORS['primary'],
            box=ROUNDED
        )

    def render_footer(self):
        """Render footer with input prompt"""
        footer_content = Table.grid(padding=0)
        footer_content.add_column(justify="left")

        # Input prompt
        prompt_text = Text()
        prompt_text.append("TORQ", style=f"bold {TORQ_COLORS['primary']}")
        prompt_text.append(">", style=self.styles['prompt'])
        prompt_text.append(f" {self.current_prompt}", style=self.styles['text'])

        footer_content.add_row(prompt_text)

        # Help hint
        footer_content.add_row(f"[{self.styles['dim']}]Type 'help' for commands • ESC to exit[/dim]")

        return Panel(
            footer_content,
            style=f"bg {TORQ_COLORS['surface']}",
            border_style=TORQ_COLORS['primary'],
            box=ROUNDED
        )

    def get_time(self):
        """Get current time string"""
        return datetime.now().strftime("%H:%M:%S")

    def render(self):
        """Render the full UI"""
        self.layout = self.create_main_layout()
        self.layout["header"].update(self.render_header())
        self.layout["sidebar"].update(self.render_sidebar())
        self.layout["chat"].update(self.render_chat())
        self.layout["context"].update(self.render_context())
        self.layout["footer"].update(self.render_footer())

        return self.layout

    async def run_interactive(self):
        """Run interactive terminal UI"""
        # Initialize
        await self.initialize()

        # Main loop
        while True:
            # Render UI
            self.console.clear()
            self.console.print(self.render())

            # Get input
            try:
                user_input = Prompt.ask(
                    f"[{self.styles['prompt']}]TORQ>[/{self.styles['prompt']}]",
                    console=self.console,
                    default="",
                    show_default=False
                )

                if user_input.lower() in ['exit', 'quit']:
                    self.console.print(f"\n[{self.styles['warning']}]Goodbye! Thanks for using TORQ Console.[/{self.styles['warning']}]")
                    break

                if user_input.strip():
                    # Add user message
                    self.message_history.append({
                        "role": "user",
                        "content": user_input,
                        "timestamp": datetime.now()
                    })

                    # Process command
                    await self.process_command(user_input)

            except KeyboardInterrupt:
                self.console.print(f"\n[{self.styles['warning']}]Use 'exit' to quit[/]")
                continue
            except EOFError:
                break

    async def process_command(self, command: str):
        """Process user command"""
        command = command.strip()

        # Special commands
        if command.lower() == 'help':
            await self.show_help()
        elif command.lower() == 'clear':
            self.message_history.clear()
        elif command.lower() == 'prince':
            await self.chat_with_prince()
        elif command.lower() in ['models', 'list models']:
            await self.show_models()
        else:
            # Use TORQ console to process
            try:
                result = await self.torq_console.process_command(command)

                # Add assistant response
                self.message_history.append({
                    "role": "assistant",
                    "content": str(result)[:500],  # Limit length
                    "timestamp": datetime.now()
                })

            except Exception as e:
                self.message_history.append({
                    "role": "system",
                    "content": f"Error: {str(e)}",
                    "timestamp": datetime.now()
                })

    async def show_help(self):
        """Show help information"""
        help_text = Table.grid(padding=1)
        help_text.add_column(justify="left", style=self.styles['text'])

        help_text.add_row(f"[{self.styles['accent']}]Available Commands:[/{self.styles['accent']}]")
        help_text.add_row("")
        help_text.add_row(f"  [bold]help[/bold] - Show this help message")
        help_text.add_row(f"  [bold]models[/bold] - List available AI models")
        help_text.add_row(f"  [bold]prince[/bold] - Chat with Prince Flowers agent")
        help_text.add_row(f"  [bold]files[/bold] - Browse project files")
        help_text.add_row(f"  [bold]specs[/bold] - Manage specifications")
        help_text.add_row(f"  [bold]clear[/bold] - Clear chat history")
        help_text.add_row(f"  [bold]exit[/bold] - Exit TORQ Console")
        help_text.add_row("")
        help_text.add_row(f"[{self.styles['accent']}]AI Chat:[/{self.styles['accent']}]")
        help_text.add_row("  Just type your question and press Enter!")
        help_text.add_row("")
        help_text.add_row(f"[{self.styles['dim']}]Prince Flowers agent can help with:[/{self.styles['dim']}]")
        help_text.add_row("  • Code generation and review")
        help_text.add_row("  • Architecture design")
        help_text.add_row("  • Debugging assistance")
        help_text.add_row("  • Learning and explanations")

        self.message_history.append({
            "role": "system",
            "content": str(help_text),
            "timestamp": datetime.now()
        })

    async def show_models(self):
        """Show available models"""
        models_info = f"""
[{self.styles['accent']}]Available AI Models:[/{self.styles['accent']}]

• [bold {TORQ_COLORS['success']}]Claude Sonnet 4[/bold {TORQ_COLORS['success']}] - Advanced reasoning and analysis
• [bold {TORQ_COLORS['success']}]DeepSeek[/bold {TORQ_COLORS['success']}] - Excellent for code generation
• [bold {TORQ_COLORS['success']}]Ollama Models[/bold {TORQ_COLORS['success']}] - Local models (deepseek-r1:7b)
• [bold {TORQ_COLORS['success']}]GLM-4.6[/bold {TORQ_COLORS['success']}] - Multimodal capabilities
• [bold {TORQ_COLORS['warning']}]Prince Flowers v2[/bold {TORQ_COLORS['warning']}] - Enhanced with memory and meta-learning

[{self.styles['dim']}]All models are ready to use! Just start chatting.[/{self.styles['dim']}]"""

        self.message_history.append({
            "role": "assistant",
            "content": models_info,
            "timestamp": datetime.now()
        })

    async def chat_with_prince(self):
        """Start chat with Prince Flowers"""
        welcome_msg = f"""
[{self.styles['accent']}][AI] Prince Flowers Agent Ready![/{self.styles['accent']}]

[{self.styles['text']}]Hello! I'm Prince Flowers, your AI programming assistant. I can help you with:[/{self.styles['text']}]

• Writing and reviewing code
• Debugging issues
• Designing architecture
• Explaining concepts
• Generating documentation

[{self.styles['text']}]What would you like to work on today?[/{self.styles['text']}]"""

        self.message_history.append({
            "role": "assistant",
            "content": welcome_msg,
            "timestamp": datetime.now()
        })

        # Set special mode for Prince Flowers chat
        self.current_prompt = "prince> "

async def main():
    """Main entry point for TORQ Terminal UI"""
    ui = TORQTerminalUI()
    await ui.run_interactive()

if __name__ == "__main__":
    asyncio.run(main())