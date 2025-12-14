"""
TORQ CONSOLE Command Palette System v0.70.0 - Phase 4

Advanced command palette system with VSCode-like functionality including:
- Command registration system with fuzzy search
- Context-aware command filtering using when-clauses
- Keyboard shortcut mapping (Ctrl+Shift+P for Windows)
- Command categories and grouping
- Dynamic command generation based on current state
- Integration with all existing systems (context, chat, inline editor)
- Command history and favorites
- Plugin-style command extensions

Features:
- Fuzzy search with intelligent ranking using difflib and custom scoring
- When-clause evaluation for context-aware command availability
- Command execution with parameter validation
- Built-in commands for all TORQ CONSOLE features
- Extensible architecture for future commands
- Command history tracking and favorites system
- Keyboard shortcut management and conflict detection
"""

import asyncio
import json
import logging
import re
import uuid
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable, Set, Tuple
from enum import Enum
import difflib
from concurrent.futures import ThreadPoolExecutor
import hashlib

from ..core.config import TorqConfig
from ..core.context_manager import ContextManager, ContextMatch
from ..core.executor_pool import get_executor
from ..core.chat_manager import ChatManager, ChatTab, MessageType
from .inline_editor import InlineEditor, EditMode, EditAction
from ..core.logger import setup_logger


class CommandCategory(Enum):
    """Command categories for organization."""
    GENERAL = "general"
    FILE = "file"
    EDIT = "edit"
    VIEW = "view"
    CHAT = "chat"
    CONTEXT = "context"
    GIT = "git"
    DEBUG = "debug"
    SETTINGS = "settings"
    AI = "ai"
    WORKSPACE = "workspace"
    TERMINAL = "terminal"
    MCP = "mcp"


class CommandType(Enum):
    """Types of commands."""
    ACTION = "action"
    TOGGLE = "toggle"
    INPUT = "input"
    SELECTION = "selection"
    MENU = "menu"


class WhenClauseOperator(Enum):
    """Operators for when-clause evaluation."""
    EQUALS = "=="
    NOT_EQUALS = "!="
    MATCHES = "=~"
    NOT_MATCHES = "!~"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


@dataclass
class WhenClause:
    """Represents a when-clause for context-aware commands."""
    variable: str
    operator: WhenClauseOperator
    value: Any = None

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the when-clause against current context."""
        try:
            ctx_value = context.get(self.variable)

            if self.operator == WhenClauseOperator.EXISTS:
                return self.variable in context
            elif self.operator == WhenClauseOperator.NOT_EXISTS:
                return self.variable not in context
            elif self.operator == WhenClauseOperator.EQUALS:
                return ctx_value == self.value
            elif self.operator == WhenClauseOperator.NOT_EQUALS:
                return ctx_value != self.value
            elif self.operator == WhenClauseOperator.IN:
                return ctx_value in self.value if self.value else False
            elif self.operator == WhenClauseOperator.NOT_IN:
                return ctx_value not in self.value if self.value else True
            elif self.operator == WhenClauseOperator.MATCHES:
                return bool(re.search(str(self.value), str(ctx_value))) if ctx_value else False
            elif self.operator == WhenClauseOperator.NOT_MATCHES:
                return not bool(re.search(str(self.value), str(ctx_value))) if ctx_value else True

            return False

        except Exception:
            return False


@dataclass
class CommandParameter:
    """Represents a command parameter."""
    name: str
    type: str  # "string", "number", "boolean", "selection", "file", "folder"
    description: str
    required: bool = True
    default: Any = None
    choices: Optional[List[str]] = None
    validation: Optional[str] = None  # Regex pattern for validation


@dataclass
class CommandShortcut:
    """Represents a keyboard shortcut."""
    key: str  # e.g., "ctrl+shift+p", "f1", "alt+enter"
    when: Optional[List[WhenClause]] = None
    mac: Optional[str] = None  # Mac-specific shortcut


@dataclass
class Command:
    """Represents a command in the palette."""
    id: str
    title: str
    category: CommandCategory
    type: CommandType
    description: str = ""
    icon: str = ""
    handler: Optional[Callable] = None
    when: Optional[List[WhenClause]] = None
    shortcuts: List[CommandShortcut] = field(default_factory=list)
    parameters: List[CommandParameter] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    last_used: Optional[datetime] = None
    is_favorite: bool = False
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category.value,
            "type": self.type.value,
            "description": self.description,
            "icon": self.icon,
            "when": [{"variable": w.variable, "operator": w.operator.value, "value": w.value}
                    for w in (self.when or [])],
            "shortcuts": [{"key": s.key, "mac": s.mac,
                          "when": [{"variable": w.variable, "operator": w.operator.value, "value": w.value}
                                  for w in (s.when or [])]}
                         for s in self.shortcuts],
            "parameters": [{"name": p.name, "type": p.type, "description": p.description,
                           "required": p.required, "default": p.default, "choices": p.choices,
                           "validation": p.validation} for p in self.parameters],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "is_favorite": self.is_favorite,
            "tags": self.tags
        }

    def is_available(self, context: Dict[str, Any]) -> bool:
        """Check if command is available in current context."""
        if not self.when:
            return True

        return all(clause.evaluate(context) for clause in self.when)

    def matches_shortcut(self, shortcut_key: str, context: Dict[str, Any]) -> bool:
        """Check if command matches a keyboard shortcut."""
        for shortcut in self.shortcuts:
            if shortcut.key.lower() == shortcut_key.lower():
                if not shortcut.when:
                    return True
                return all(clause.evaluate(context) for clause in shortcut.when)
        return False


@dataclass
class CommandExecution:
    """Represents a command execution result."""
    command_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FuzzySearchResult:
    """Represents a fuzzy search result."""
    command: Command
    score: float
    match_positions: List[Tuple[int, int]] = field(default_factory=list)
    match_type: str = "title"  # "title", "description", "tag", "category"


class FuzzySearchEngine:
    """Advanced fuzzy search engine for commands."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def search(self, commands: List[Command], query: str, context: Dict[str, Any]) -> List[FuzzySearchResult]:
        """Perform fuzzy search on commands."""
        if not query.strip():
            # Return all available commands sorted by usage
            available_commands = [cmd for cmd in commands if cmd.is_available(context)]
            return [FuzzySearchResult(cmd, 1.0) for cmd in
                   sorted(available_commands, key=lambda c: (c.usage_count, c.is_favorite), reverse=True)]

        query = query.lower().strip()
        results = []

        for command in commands:
            if not command.is_available(context):
                continue

            score, match_type, positions = self._calculate_match_score(command, query)
            if score > 0:
                results.append(FuzzySearchResult(
                    command=command,
                    score=score,
                    match_positions=positions,
                    match_type=match_type
                ))

        # Sort by score (descending), then by usage count and favorites
        results.sort(key=lambda r: (
            r.score,
            r.command.is_favorite,
            r.command.usage_count,
            -len(r.command.title)  # Prefer shorter titles for same score
        ), reverse=True)

        return results

    def _calculate_match_score(self, command: Command, query: str) -> Tuple[float, str, List[Tuple[int, int]]]:
        """Calculate match score for a command against query."""
        max_score = 0.0
        best_match_type = ""
        best_positions = []

        # Check title match
        title_score, title_positions = self._string_similarity(command.title.lower(), query)
        if title_score > max_score:
            max_score = title_score
            best_match_type = "title"
            best_positions = title_positions

        # Check description match (lower weight)
        desc_score, desc_positions = self._string_similarity(command.description.lower(), query)
        desc_score *= 0.7  # Lower weight for description matches
        if desc_score > max_score:
            max_score = desc_score
            best_match_type = "description"
            best_positions = desc_positions

        # Check category match
        category_score, cat_positions = self._string_similarity(command.category.value.lower(), query)
        category_score *= 0.5  # Lower weight for category matches
        if category_score > max_score:
            max_score = category_score
            best_match_type = "category"
            best_positions = cat_positions

        # Check tags match
        for tag in command.tags:
            tag_score, tag_positions = self._string_similarity(tag.lower(), query)
            tag_score *= 0.6  # Medium weight for tag matches
            if tag_score > max_score:
                max_score = tag_score
                best_match_type = "tag"
                best_positions = tag_positions

        # Boost score for favorites and frequently used commands
        if command.is_favorite:
            max_score *= 1.2
        if command.usage_count > 10:
            max_score *= 1.1

        # Apply minimum threshold
        if max_score < 0.1:
            max_score = 0.0

        return max_score, best_match_type, best_positions

    def _string_similarity(self, text: str, query: str) -> Tuple[float, List[Tuple[int, int]]]:
        """Calculate similarity between text and query."""
        if not text or not query:
            return 0.0, []

        # Exact match
        if query in text:
            start_idx = text.find(query)
            exact_score = 0.9 if text == query else 0.8
            return exact_score, [(start_idx, start_idx + len(query))]

        # Subsequence match
        subseq_score, positions = self._subsequence_match(text, query)
        if subseq_score > 0:
            return subseq_score, positions

        # Fuzzy match using difflib
        ratio = difflib.SequenceMatcher(None, text, query).ratio()
        if ratio > 0.3:
            return ratio * 0.6, []

        return 0.0, []

    def _subsequence_match(self, text: str, query: str) -> Tuple[float, List[Tuple[int, int]]]:
        """Check if query is a subsequence of text."""
        positions = []
        text_idx = 0
        query_idx = 0

        while text_idx < len(text) and query_idx < len(query):
            if text[text_idx] == query[query_idx]:
                positions.append((text_idx, text_idx + 1))
                query_idx += 1
            text_idx += 1

        if query_idx == len(query):
            # Calculate score based on how compact the match is
            if positions:
                span = positions[-1][1] - positions[0][0]
                compactness = len(query) / span
                return min(0.7, 0.3 + compactness * 0.4), positions

        return 0.0, []


class CommandHistory:
    """Manages command execution history."""

    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history: List[CommandExecution] = []
        self.command_usage: Dict[str, int] = defaultdict(int)
        self.last_used: Dict[str, datetime] = {}

    def add_execution(self, execution: CommandExecution) -> None:
        """Add a command execution to history."""
        self.history.append(execution)

        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        # Update usage statistics
        self.command_usage[execution.command_id] += 1
        self.last_used[execution.command_id] = execution.timestamp

    def get_recent_commands(self, limit: int = 10) -> List[str]:
        """Get recently executed command IDs."""
        recent = []
        seen = set()

        for execution in reversed(self.history):
            if execution.command_id not in seen and execution.success:
                recent.append(execution.command_id)
                seen.add(execution.command_id)
                if len(recent) >= limit:
                    break

        return recent

    def get_popular_commands(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most popular command IDs with usage counts."""
        return sorted(self.command_usage.items(), key=lambda x: x[1], reverse=True)[:limit]

    def get_command_stats(self, command_id: str) -> Dict[str, Any]:
        """Get statistics for a specific command."""
        executions = [e for e in self.history if e.command_id == command_id]

        if not executions:
            return {"usage_count": 0, "success_rate": 0.0, "avg_duration": 0.0}

        successful = [e for e in executions if e.success]
        success_rate = len(successful) / len(executions)
        avg_duration = sum(e.duration_ms for e in executions) / len(executions)

        return {
            "usage_count": len(executions),
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "last_used": self.last_used.get(command_id).isoformat() if command_id in self.last_used else None
        }


class CommandRegistry:
    """Registry for managing commands."""

    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.shortcuts: Dict[str, str] = {}  # shortcut -> command_id
        self.categories: Dict[CommandCategory, List[str]] = defaultdict(list)
        self.logger = logging.getLogger(__name__)

    def register_command(self, command: Command) -> bool:
        """Register a new command."""
        try:
            if command.id in self.commands:
                self.logger.warning(f"Command {command.id} already exists, overwriting")

            # Register command
            self.commands[command.id] = command
            self.categories[command.category].append(command.id)

            # Register shortcuts
            for shortcut in command.shortcuts:
                if shortcut.key in self.shortcuts:
                    existing_cmd = self.shortcuts[shortcut.key]
                    self.logger.warning(f"Shortcut {shortcut.key} conflicts between {command.id} and {existing_cmd}")

                self.shortcuts[shortcut.key] = command.id

            self.logger.debug(f"Registered command: {command.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error registering command {command.id}: {e}")
            return False

    def unregister_command(self, command_id: str) -> bool:
        """Unregister a command."""
        try:
            if command_id not in self.commands:
                return False

            command = self.commands[command_id]

            # Remove from registry
            del self.commands[command_id]

            # Remove from category
            if command_id in self.categories[command.category]:
                self.categories[command.category].remove(command_id)

            # Remove shortcuts
            shortcuts_to_remove = [k for k, v in self.shortcuts.items() if v == command_id]
            for shortcut in shortcuts_to_remove:
                del self.shortcuts[shortcut]

            self.logger.debug(f"Unregistered command: {command_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error unregistering command {command_id}: {e}")
            return False

    def get_command(self, command_id: str) -> Optional[Command]:
        """Get a command by ID."""
        return self.commands.get(command_id)

    def get_commands_by_category(self, category: CommandCategory) -> List[Command]:
        """Get all commands in a category."""
        command_ids = self.categories.get(category, [])
        return [self.commands[cmd_id] for cmd_id in command_ids if cmd_id in self.commands]

    def get_all_commands(self) -> List[Command]:
        """Get all registered commands."""
        return list(self.commands.values())

    def find_command_by_shortcut(self, shortcut: str, context: Dict[str, Any]) -> Optional[Command]:
        """Find command by keyboard shortcut."""
        command_id = self.shortcuts.get(shortcut.lower())
        if not command_id:
            return None

        command = self.commands.get(command_id)
        if command and command.matches_shortcut(shortcut, context):
            return command

        return None

    def get_shortcut_conflicts(self) -> Dict[str, List[str]]:
        """Get shortcut conflicts."""
        conflicts = defaultdict(list)

        for shortcut, command_id in self.shortcuts.items():
            conflicts[shortcut].append(command_id)

        return {k: v for k, v in conflicts.items() if len(v) > 1}


class CommandPalette:
    """
    Advanced command palette system for TORQ CONSOLE v0.70.0.

    Provides VSCode-like command palette functionality with fuzzy search,
    context-aware command filtering, keyboard shortcuts, and integration
    with all TORQ CONSOLE systems.
    """

    def __init__(self, config: TorqConfig, context_manager: ContextManager,
                 chat_manager: ChatManager, inline_editor: InlineEditor):
        self.config = config
        self.context_manager = context_manager
        self.chat_manager = chat_manager
        self.inline_editor = inline_editor
        self.logger = setup_logger("command_palette")

        # Core components
        self.registry = CommandRegistry()
        self.search_engine = FuzzySearchEngine()
        self.history = CommandHistory()

        # State management
        self.is_open = False
        self.current_query = ""
        self.selected_index = 0
        self.current_results: List[FuzzySearchResult] = []
        self.favorites: Set[str] = set()

        # Context tracking
        self.current_context: Dict[str, Any] = {}
        self.context_watchers: List[Callable] = []

        # Use shared thread pool for command execution
        self.executor = get_executor()
        self.executing_commands: Dict[str, asyncio.Task] = {}

        # Built-in command categories
        self.builtin_commands = {
            CommandCategory.GENERAL: self._register_general_commands,
            CommandCategory.FILE: self._register_file_commands,
            CommandCategory.EDIT: self._register_edit_commands,
            CommandCategory.VIEW: self._register_view_commands,
            CommandCategory.CHAT: self._register_chat_commands,
            CommandCategory.CONTEXT: self._register_context_commands,
            CommandCategory.AI: self._register_ai_commands,
            CommandCategory.WORKSPACE: self._register_workspace_commands,
            CommandCategory.MCP: self._register_mcp_commands,
        }

        self.logger.info("CommandPalette initialized")

    async def initialize(self) -> None:
        """Initialize the command palette system."""
        try:
            # Register built-in commands
            await self._register_builtin_commands()

            # Load favorites and history
            await self._load_user_data()

            # Update context
            await self._update_context()

            self.logger.info("CommandPalette initialization completed")

        except Exception as e:
            self.logger.error(f"Error initializing CommandPalette: {e}")

    async def open_palette(self, initial_query: str = "") -> Dict[str, Any]:
        """Open the command palette."""
        try:
            self.is_open = True
            self.current_query = initial_query
            self.selected_index = 0

            # Update context
            await self._update_context()

            # Perform initial search
            results = await self.search_commands(initial_query)

            return {
                "success": True,
                "is_open": True,
                "query": self.current_query,
                "results": [self._serialize_search_result(r) for r in results],
                "selected_index": self.selected_index,
                "context": self.current_context,
                "shortcuts": self._get_relevant_shortcuts()
            }

        except Exception as e:
            self.logger.error(f"Error opening command palette: {e}")
            return {"success": False, "error": str(e)}

    async def close_palette(self) -> Dict[str, Any]:
        """Close the command palette."""
        try:
            self.is_open = False
            self.current_query = ""
            self.selected_index = 0
            self.current_results = []

            return {"success": True, "is_open": False}

        except Exception as e:
            self.logger.error(f"Error closing command palette: {e}")
            return {"success": False, "error": str(e)}

    async def search_commands(self, query: str) -> List[FuzzySearchResult]:
        """Search commands with fuzzy matching."""
        try:
            self.current_query = query

            # Get all available commands
            all_commands = self.registry.get_all_commands()

            # Update usage counts from history
            for command in all_commands:
                stats = self.history.get_command_stats(command.id)
                command.usage_count = stats["usage_count"]
                if stats["last_used"]:
                    command.last_used = datetime.fromisoformat(stats["last_used"])

            # Perform fuzzy search
            results = self.search_engine.search(all_commands, query, self.current_context)

            self.current_results = results
            self.selected_index = 0

            return results

        except Exception as e:
            self.logger.error(f"Error searching commands: {e}")
            return []

    async def execute_command(self, command_id: str, parameters: Dict[str, Any] = None) -> CommandExecution:
        """Execute a command by ID."""
        start_time = datetime.now()

        try:
            command = self.registry.get_command(command_id)
            if not command:
                raise ValueError(f"Command not found: {command_id}")

            if not command.is_available(self.current_context):
                raise ValueError(f"Command not available in current context: {command_id}")

            # Validate parameters
            validated_params = await self._validate_parameters(command, parameters or {})

            # Execute command
            if command.handler:
                if asyncio.iscoroutinefunction(command.handler):
                    result = await command.handler(validated_params, self.current_context)
                else:
                    # Run in executor for non-async handlers
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    result = await loop.run_in_executor(
                        self.executor, command.handler, validated_params, self.current_context
                    )
            else:
                # Handle built-in commands
                result = await self._execute_builtin_command(command, validated_params)

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds() * 1000

            # Create execution record
            execution = CommandExecution(
                command_id=command_id,
                success=True,
                result=result,
                duration_ms=int(duration),
                parameters=validated_params
            )

            # Update history
            self.history.add_execution(execution)

            # Update command usage
            command.usage_count += 1
            command.last_used = datetime.now()

            self.logger.info(f"Executed command: {command_id} in {duration:.1f}ms")
            return execution

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000

            execution = CommandExecution(
                command_id=command_id,
                success=False,
                error=str(e),
                duration_ms=int(duration),
                parameters=parameters or {}
            )

            self.history.add_execution(execution)
            self.logger.error(f"Error executing command {command_id}: {e}")
            return execution

    async def execute_shortcut(self, shortcut: str) -> Optional[CommandExecution]:
        """Execute command by keyboard shortcut."""
        try:
            await self._update_context()

            command = self.registry.find_command_by_shortcut(shortcut, self.current_context)
            if not command:
                return None

            return await self.execute_command(command.id)

        except Exception as e:
            self.logger.error(f"Error executing shortcut {shortcut}: {e}")
            return None

    async def navigate_results(self, direction: str) -> Dict[str, Any]:
        """Navigate through search results."""
        try:
            if not self.current_results:
                return {"success": False, "error": "No results available"}

            if direction == "up":
                self.selected_index = max(0, self.selected_index - 1)
            elif direction == "down":
                self.selected_index = min(len(self.current_results) - 1, self.selected_index + 1)
            elif direction == "page_up":
                self.selected_index = max(0, self.selected_index - 10)
            elif direction == "page_down":
                self.selected_index = min(len(self.current_results) - 1, self.selected_index + 10)
            elif direction == "home":
                self.selected_index = 0
            elif direction == "end":
                self.selected_index = len(self.current_results) - 1

            return {
                "success": True,
                "selected_index": self.selected_index,
                "selected_command": self._serialize_search_result(self.current_results[self.selected_index]) if self.current_results else None
            }

        except Exception as e:
            self.logger.error(f"Error navigating results: {e}")
            return {"success": False, "error": str(e)}

    async def execute_selected(self) -> Optional[CommandExecution]:
        """Execute the currently selected command."""
        try:
            if not self.current_results or self.selected_index >= len(self.current_results):
                return None

            selected_result = self.current_results[self.selected_index]
            return await self.execute_command(selected_result.command.id)

        except Exception as e:
            self.logger.error(f"Error executing selected command: {e}")
            return None

    async def toggle_favorite(self, command_id: str) -> bool:
        """Toggle favorite status of a command."""
        try:
            command = self.registry.get_command(command_id)
            if not command:
                return False

            if command.is_favorite:
                command.is_favorite = False
                self.favorites.discard(command_id)
            else:
                command.is_favorite = True
                self.favorites.add(command_id)

            await self._save_user_data()
            return True

        except Exception as e:
            self.logger.error(f"Error toggling favorite for {command_id}: {e}")
            return False

    async def get_command_details(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a command."""
        try:
            command = self.registry.get_command(command_id)
            if not command:
                return None

            stats = self.history.get_command_stats(command_id)

            return {
                **command.to_dict(),
                "stats": stats,
                "is_available": command.is_available(self.current_context),
                "shortcuts_formatted": [self._format_shortcut(s.key) for s in command.shortcuts]
            }

        except Exception as e:
            self.logger.error(f"Error getting command details for {command_id}: {e}")
            return None

    async def get_recent_commands(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently executed commands."""
        try:
            recent_ids = self.history.get_recent_commands(limit)
            return [self.registry.get_command(cmd_id).to_dict()
                   for cmd_id in recent_ids
                   if self.registry.get_command(cmd_id)]

        except Exception as e:
            self.logger.error(f"Error getting recent commands: {e}")
            return []

    async def get_popular_commands(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular commands."""
        try:
            popular = self.history.get_popular_commands(limit)
            return [{"command": self.registry.get_command(cmd_id).to_dict(), "usage_count": count}
                   for cmd_id, count in popular
                   if self.registry.get_command(cmd_id)]

        except Exception as e:
            self.logger.error(f"Error getting popular commands: {e}")
            return []

    async def get_favorites(self) -> List[Dict[str, Any]]:
        """Get favorite commands."""
        try:
            return [self.registry.get_command(cmd_id).to_dict()
                   for cmd_id in self.favorites
                   if self.registry.get_command(cmd_id)]

        except Exception as e:
            self.logger.error(f"Error getting favorites: {e}")
            return []

    async def register_custom_command(self, command_data: Dict[str, Any]) -> bool:
        """Register a custom command."""
        try:
            # Parse command data
            command = Command(
                id=command_data["id"],
                title=command_data["title"],
                category=CommandCategory(command_data.get("category", "general")),
                type=CommandType(command_data.get("type", "action")),
                description=command_data.get("description", ""),
                icon=command_data.get("icon", ""),
                tags=command_data.get("tags", [])
            )

            # Parse when clauses
            if "when" in command_data:
                command.when = [
                    WhenClause(
                        variable=w["variable"],
                        operator=WhenClauseOperator(w["operator"]),
                        value=w.get("value")
                    ) for w in command_data["when"]
                ]

            # Parse shortcuts
            if "shortcuts" in command_data:
                command.shortcuts = [
                    CommandShortcut(
                        key=s["key"],
                        mac=s.get("mac"),
                        when=[WhenClause(
                            variable=w["variable"],
                            operator=WhenClauseOperator(w["operator"]),
                            value=w.get("value")
                        ) for w in s.get("when", [])]
                    ) for s in command_data["shortcuts"]
                ]

            # Parse parameters
            if "parameters" in command_data:
                command.parameters = [
                    CommandParameter(
                        name=p["name"],
                        type=p["type"],
                        description=p["description"],
                        required=p.get("required", True),
                        default=p.get("default"),
                        choices=p.get("choices"),
                        validation=p.get("validation")
                    ) for p in command_data["parameters"]
                ]

            return self.registry.register_command(command)

        except Exception as e:
            self.logger.error(f"Error registering custom command: {e}")
            return False

    def _serialize_search_result(self, result: FuzzySearchResult) -> Dict[str, Any]:
        """Serialize search result for JSON response."""
        return {
            "command": result.command.to_dict(),
            "score": result.score,
            "match_positions": result.match_positions,
            "match_type": result.match_type
        }

    def _get_relevant_shortcuts(self) -> List[Dict[str, str]]:
        """Get shortcuts relevant to current context."""
        relevant = []

        for shortcut, command_id in self.registry.shortcuts.items():
            command = self.registry.get_command(command_id)
            if command and command.is_available(self.current_context):
                relevant.append({
                    "shortcut": self._format_shortcut(shortcut),
                    "command": command.title,
                    "command_id": command_id
                })

        return sorted(relevant, key=lambda x: x["shortcut"])

    def _format_shortcut(self, shortcut: str) -> str:
        """Format shortcut for display."""
        # Convert to Windows-friendly format
        formatted = shortcut.replace("cmd", "ctrl").replace("option", "alt")

        # Capitalize and format
        parts = formatted.split("+")
        formatted_parts = []

        for part in parts:
            if part.lower() == "ctrl":
                formatted_parts.append("Ctrl")
            elif part.lower() == "alt":
                formatted_parts.append("Alt")
            elif part.lower() == "shift":
                formatted_parts.append("Shift")
            elif part.lower() == "meta":
                formatted_parts.append("Win")
            else:
                formatted_parts.append(part.upper())

        return "+".join(formatted_parts)

    async def _update_context(self) -> None:
        """Update current context for when-clause evaluation."""
        try:
            # Get active chat tab
            active_tab = None
            if self.chat_manager.active_tab_id:
                active_tab = self.chat_manager.active_tabs.get(self.chat_manager.active_tab_id)

            # Get context manager state
            context_summary = await self.context_manager.get_context_summary()

            # Get inline editor state
            inline_stats = self.inline_editor.get_edit_statistics()

            self.current_context = {
                # Chat context
                "has_active_chat": active_tab is not None,
                "chat_message_count": len(active_tab.messages) if active_tab else 0,
                "chat_model": active_tab.model if active_tab else None,
                "has_chat_selection": False,  # This would be set by UI

                # Context manager
                "active_contexts": context_summary.get("active_contexts", 0),
                "tree_sitter_available": context_summary.get("tree_sitter_available", False),

                # Inline editor
                "has_inline_selection": False,  # This would be set by UI
                "inline_edit_mode": None,  # This would be set by UI
                "ghost_suggestions": inline_stats.get("ghost_suggestions", 0),

                # General
                "platform": "windows",  # For Windows compatibility
                "has_workspace": True,  # Assume we have a workspace
                "has_git": True,  # This would be detected
                "has_files_open": True,  # This would be detected

                # Time-based
                "hour": datetime.now().hour,
                "is_weekend": datetime.now().weekday() >= 5
            }

            # Notify context watchers
            for watcher in self.context_watchers:
                try:
                    if asyncio.iscoroutinefunction(watcher):
                        await watcher(self.current_context)
                    else:
                        watcher(self.current_context)
                except Exception as e:
                    self.logger.debug(f"Error in context watcher: {e}")

        except Exception as e:
            self.logger.error(f"Error updating context: {e}")

    async def _validate_parameters(self, command: Command, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process command parameters."""
        validated = {}

        for param in command.parameters:
            value = parameters.get(param.name, param.default)

            # Check required parameters
            if param.required and value is None:
                raise ValueError(f"Required parameter missing: {param.name}")

            # Type validation
            if value is not None:
                if param.type == "string" and not isinstance(value, str):
                    value = str(value)
                elif param.type == "number":
                    try:
                        value = float(value) if '.' in str(value) else int(value)
                    except ValueError:
                        raise ValueError(f"Invalid number for parameter {param.name}: {value}")
                elif param.type == "boolean":
                    value = bool(value)

                # Choice validation
                if param.choices and value not in param.choices:
                    raise ValueError(f"Invalid choice for {param.name}: {value}. Must be one of {param.choices}")

                # Pattern validation
                if param.validation and isinstance(value, str):
                    if not re.match(param.validation, value):
                        raise ValueError(f"Parameter {param.name} does not match pattern: {param.validation}")

            validated[param.name] = value

        return validated

    async def _execute_builtin_command(self, command: Command, parameters: Dict[str, Any]) -> Any:
        """Execute a built-in command."""
        # This would route to the appropriate handler based on command ID
        command_id = command.id

        try:
            if command_id.startswith("chat."):
                return await self._execute_chat_command(command_id, parameters)
            elif command_id.startswith("edit."):
                return await self._execute_edit_command(command_id, parameters)
            elif command_id.startswith("context."):
                return await self._execute_context_command(command_id, parameters)
            elif command_id.startswith("view."):
                return await self._execute_view_command(command_id, parameters)
            elif command_id.startswith("file."):
                return await self._execute_file_command(command_id, parameters)
            else:
                return await self._execute_general_command(command_id, parameters)

        except Exception as e:
            self.logger.error(f"Error executing builtin command {command_id}: {e}")
            raise

    async def _register_builtin_commands(self) -> None:
        """Register all built-in commands."""
        try:
            for category, register_func in self.builtin_commands.items():
                await register_func()

            self.logger.info(f"Registered {len(self.registry.commands)} built-in commands")

        except Exception as e:
            self.logger.error(f"Error registering builtin commands: {e}")

    async def _register_general_commands(self) -> None:
        """Register general commands."""
        commands = [
            Command(
                id="general.command_palette",
                title="Show Command Palette",
                category=CommandCategory.GENERAL,
                type=CommandType.ACTION,
                description="Open the command palette",
                icon="search",
                shortcuts=[CommandShortcut(key="ctrl+shift+p")],
                tags=["palette", "commands", "search"]
            ),
            Command(
                id="general.quick_open",
                title="Quick Open File",
                category=CommandCategory.GENERAL,
                type=CommandType.ACTION,
                description="Quickly open a file",
                icon="file",
                shortcuts=[CommandShortcut(key="ctrl+p")],
                tags=["file", "open", "quick"]
            ),
            Command(
                id="general.settings",
                title="Open Settings",
                category=CommandCategory.GENERAL,
                type=CommandType.ACTION,
                description="Open TORQ Console settings",
                icon="settings",
                tags=["settings", "preferences", "config"]
            ),
            Command(
                id="general.help",
                title="Show Help",
                category=CommandCategory.GENERAL,
                type=CommandType.ACTION,
                description="Show help documentation",
                icon="help",
                shortcuts=[CommandShortcut(key="f1")],
                tags=["help", "documentation", "guide"]
            )
        ]

        for command in commands:
            self.registry.register_command(command)

    async def _register_file_commands(self) -> None:
        """Register file operation commands."""
        commands = [
            Command(
                id="file.new",
                title="New File",
                category=CommandCategory.FILE,
                type=CommandType.ACTION,
                description="Create a new file",
                icon="file-plus",
                shortcuts=[CommandShortcut(key="ctrl+n")],
                tags=["file", "new", "create"]
            ),
            Command(
                id="file.open",
                title="Open File",
                category=CommandCategory.FILE,
                type=CommandType.ACTION,
                description="Open an existing file",
                icon="folder-open",
                shortcuts=[CommandShortcut(key="ctrl+o")],
                tags=["file", "open"]
            ),
            Command(
                id="file.save",
                title="Save File",
                category=CommandCategory.FILE,
                type=CommandType.ACTION,
                description="Save the current file",
                icon="save",
                shortcuts=[CommandShortcut(key="ctrl+s")],
                when=[WhenClause("has_files_open", WhenClauseOperator.EQUALS, True)],
                tags=["file", "save"]
            ),
            Command(
                id="file.save_all",
                title="Save All Files",
                category=CommandCategory.FILE,
                type=CommandType.ACTION,
                description="Save all open files",
                icon="save-all",
                shortcuts=[CommandShortcut(key="ctrl+shift+s")],
                when=[WhenClause("has_files_open", WhenClauseOperator.EQUALS, True)],
                tags=["file", "save", "all"]
            )
        ]

        for command in commands:
            self.registry.register_command(command)

    async def _register_edit_commands(self) -> None:
        """Register editing commands."""
        commands = [
            Command(
                id="edit.inline_edit",
                title="Inline Edit",
                category=CommandCategory.EDIT,
                type=CommandType.ACTION,
                description="Open inline editor",
                icon="edit",
                shortcuts=[CommandShortcut(key="ctrl+k")],
                tags=["edit", "inline", "ai"]
            ),
            Command(
                id="edit.quick_question",
                title="Quick Question",
                category=CommandCategory.EDIT,
                type=CommandType.ACTION,
                description="Ask a quick question about code",
                icon="help-circle",
                shortcuts=[CommandShortcut(key="alt+enter")],
                tags=["question", "help", "ai"]
            ),
            Command(
                id="edit.code_actions",
                title="Show Code Actions",
                category=CommandCategory.EDIT,
                type=CommandType.ACTION,
                description="Show available code actions",
                icon="lightbulb",
                shortcuts=[CommandShortcut(key="ctrl+.")],
                when=[WhenClause("has_inline_selection", WhenClauseOperator.EQUALS, True)],
                tags=["code", "actions", "refactor"]
            ),
            Command(
                id="edit.format_document",
                title="Format Document",
                category=CommandCategory.EDIT,
                type=CommandType.ACTION,
                description="Format the current document",
                icon="code",
                shortcuts=[CommandShortcut(key="shift+alt+f")],
                when=[WhenClause("has_files_open", WhenClauseOperator.EQUALS, True)],
                tags=["format", "code", "style"]
            )
        ]

        for command in commands:
            self.registry.register_command(command)

    async def _register_view_commands(self) -> None:
        """Register view commands."""
        commands = [
            Command(
                id="view.toggle_sidebar",
                title="Toggle Sidebar",
                category=CommandCategory.VIEW,
                type=CommandType.TOGGLE,
                description="Show/hide the sidebar",
                icon="sidebar",
                shortcuts=[CommandShortcut(key="ctrl+b")],
                tags=["view", "sidebar", "toggle"]
            ),
            Command(
                id="view.toggle_chat_panel",
                title="Toggle Chat Panel",
                category=CommandCategory.VIEW,
                type=CommandType.TOGGLE,
                description="Show/hide the chat panel",
                icon="message-square",
                shortcuts=[CommandShortcut(key="ctrl+shift+c")],
                tags=["view", "chat", "toggle"]
            ),
            Command(
                id="view.toggle_diff_panel",
                title="Toggle Diff Panel",
                category=CommandCategory.VIEW,
                type=CommandType.TOGGLE,
                description="Show/hide the diff panel",
                icon="git-compare",
                shortcuts=[CommandShortcut(key="ctrl+shift+d")],
                tags=["view", "diff", "toggle"]
            ),
            Command(
                id="view.zen_mode",
                title="Toggle Zen Mode",
                category=CommandCategory.VIEW,
                type=CommandType.TOGGLE,
                description="Enter/exit zen mode",
                icon="eye-off",
                shortcuts=[CommandShortcut(key="ctrl+k z")],
                tags=["view", "zen", "focus"]
            )
        ]

        for command in commands:
            self.registry.register_command(command)

    async def _register_chat_commands(self) -> None:
        """Register chat-related commands."""
        commands = [
            Command(
                id="chat.new_tab",
                title="New Chat Tab",
                category=CommandCategory.CHAT,
                type=CommandType.ACTION,
                description="Create a new chat tab",
                icon="plus",
                shortcuts=[CommandShortcut(key="ctrl+t")],
                tags=["chat", "tab", "new"]
            ),
            Command(
                id="chat.close_tab",
                title="Close Chat Tab",
                category=CommandCategory.CHAT,
                type=CommandType.ACTION,
                description="Close the current chat tab",
                icon="x",
                shortcuts=[CommandShortcut(key="ctrl+w")],
                when=[WhenClause("has_active_chat", WhenClauseOperator.EQUALS, True)],
                tags=["chat", "tab", "close"]
            ),
            Command(
                id="chat.next_tab",
                title="Next Chat Tab",
                category=CommandCategory.CHAT,
                type=CommandType.ACTION,
                description="Switch to next chat tab",
                icon="arrow-right",
                shortcuts=[CommandShortcut(key="ctrl+tab")],
                when=[WhenClause("has_active_chat", WhenClauseOperator.EQUALS, True)],
                tags=["chat", "tab", "next"]
            ),
            Command(
                id="chat.export_markdown",
                title="Export Chat to Markdown",
                category=CommandCategory.CHAT,
                type=CommandType.ACTION,
                description="Export current chat to markdown file",
                icon="download",
                when=[WhenClause("chat_message_count", WhenClauseOperator.NOT_EQUALS, 0)],
                tags=["chat", "export", "markdown"]
            ),
            Command(
                id="chat.clear_history",
                title="Clear Chat History",
                category=CommandCategory.CHAT,
                type=CommandType.ACTION,
                description="Clear the current chat history",
                icon="trash",
                when=[WhenClause("chat_message_count", WhenClauseOperator.NOT_EQUALS, 0)],
                tags=["chat", "clear", "history"]
            )
        ]

        for command in commands:
            self.registry.register_command(command)

    async def _register_context_commands(self) -> None:
        """Register context management commands."""
        commands = [
            Command(
                id="context.add_files",
                title="Add Files to Context",
                category=CommandCategory.CONTEXT,
                type=CommandType.ACTION,
                description="Add files to the current context",
                icon="file-plus",
                tags=["context", "files", "add"]
            ),
            Command(
                id="context.search_code",
                title="Search Code Context",
                category=CommandCategory.CONTEXT,
                type=CommandType.ACTION,
                description="Search for code in context",
                icon="search",
                tags=["context", "search", "code"]
            ),
            Command(
                id="context.clear_all",
                title="Clear All Context",
                category=CommandCategory.CONTEXT,
                type=CommandType.ACTION,
                description="Clear all active context",
                icon="trash",
                when=[WhenClause("active_contexts", WhenClauseOperator.NOT_EQUALS, 0)],
                tags=["context", "clear", "all"]
            ),
            Command(
                id="context.export",
                title="Export Context",
                category=CommandCategory.CONTEXT,
                type=CommandType.ACTION,
                description="Export current context to file",
                icon="download",
                when=[WhenClause("active_contexts", WhenClauseOperator.NOT_EQUALS, 0)],
                tags=["context", "export"]
            )
        ]

        for command in commands:
            self.registry.register_command(command)

    async def _register_ai_commands(self) -> None:
        """Register AI-related commands."""
        commands = [
            Command(
                id="ai.explain_code",
                title="Explain Code",
                category=CommandCategory.AI,
                type=CommandType.ACTION,
                description="Explain the selected code",
                icon="help-circle",
                when=[WhenClause("has_inline_selection", WhenClauseOperator.EQUALS, True)],
                tags=["ai", "explain", "code"]
            ),
            Command(
                id="ai.refactor_code",
                title="Refactor Code",
                category=CommandCategory.AI,
                type=CommandType.ACTION,
                description="Refactor the selected code",
                icon="refresh-cw",
                when=[WhenClause("has_inline_selection", WhenClauseOperator.EQUALS, True)],
                tags=["ai", "refactor", "code"]
            ),
            Command(
                id="ai.generate_tests",
                title="Generate Tests",
                category=CommandCategory.AI,
                type=CommandType.ACTION,
                description="Generate tests for the selected code",
                icon="check-circle",
                when=[WhenClause("has_inline_selection", WhenClauseOperator.EQUALS, True)],
                tags=["ai", "tests", "generate"]
            ),
            Command(
                id="ai.add_documentation",
                title="Add Documentation",
                category=CommandCategory.AI,
                type=CommandType.ACTION,
                description="Add documentation to the selected code",
                icon="book",
                when=[WhenClause("has_inline_selection", WhenClauseOperator.EQUALS, True)],
                tags=["ai", "documentation", "docstring"]
            ),
            Command(
                id="ai.optimize_code",
                title="Optimize Code",
                category=CommandCategory.AI,
                type=CommandType.ACTION,
                description="Optimize the selected code for performance",
                icon="zap",
                when=[WhenClause("has_inline_selection", WhenClauseOperator.EQUALS, True)],
                tags=["ai", "optimize", "performance"]
            )
        ]

        for command in commands:
            self.registry.register_command(command)

    async def _register_workspace_commands(self) -> None:
        """Register workspace commands."""
        commands = [
            Command(
                id="workspace.open_folder",
                title="Open Folder",
                category=CommandCategory.WORKSPACE,
                type=CommandType.ACTION,
                description="Open a folder as workspace",
                icon="folder",
                shortcuts=[CommandShortcut(key="ctrl+k ctrl+o")],
                tags=["workspace", "folder", "open"]
            ),
            Command(
                id="workspace.close_folder",
                title="Close Folder",
                category=CommandCategory.WORKSPACE,
                type=CommandType.ACTION,
                description="Close the current workspace folder",
                icon="folder-x",
                when=[WhenClause("has_workspace", WhenClauseOperator.EQUALS, True)],
                tags=["workspace", "folder", "close"]
            ),
            Command(
                id="workspace.reload_window",
                title="Reload Window",
                category=CommandCategory.WORKSPACE,
                type=CommandType.ACTION,
                description="Reload the TORQ Console window",
                icon="refresh-cw",
                shortcuts=[CommandShortcut(key="ctrl+r")],
                tags=["workspace", "reload", "refresh"]
            )
        ]

        for command in commands:
            self.registry.register_command(command)

    async def _register_mcp_commands(self) -> None:
        """Register MCP-related commands."""
        commands = [
            Command(
                id="mcp.list_servers",
                title="MCP: List Servers",
                category=CommandCategory.MCP,
                type=CommandType.ACTION,
                description="List all configured MCP servers",
                icon="server",
                tags=["mcp", "servers", "list"],
                executor=self._execute_mcp_command
            ),
            Command(
                id="mcp.status",
                title="MCP: Server Status",
                category=CommandCategory.MCP,
                type=CommandType.ACTION,
                description="Show status of all MCP servers",
                icon="activity",
                tags=["mcp", "status", "servers"],
                executor=self._execute_mcp_command
            ),
            Command(
                id="mcp.connect_server",
                title="MCP: Connect Server",
                category=CommandCategory.MCP,
                type=CommandType.ACTION,
                description="Connect to an MCP server",
                icon="link",
                tags=["mcp", "connect", "server"],
                executor=self._execute_mcp_command,
                parameters={
                    "server_name": {
                        "type": "string",
                        "description": "Name of the server to connect to",
                        "required": True
                    }
                }
            ),
            Command(
                id="mcp.disconnect_server",
                title="MCP: Disconnect Server",
                category=CommandCategory.MCP,
                type=CommandType.ACTION,
                description="Disconnect from an MCP server",
                icon="unlink",
                tags=["mcp", "disconnect", "server"],
                executor=self._execute_mcp_command,
                parameters={
                    "server_name": {
                        "type": "string",
                        "description": "Name of the server to disconnect from",
                        "required": True
                    }
                }
            ),
            Command(
                id="mcp.list_tools",
                title="MCP: List Available Tools",
                category=CommandCategory.MCP,
                type=CommandType.ACTION,
                description="List available tools from MCP servers",
                icon="tool",
                tags=["mcp", "tools", "list"],
                executor=self._execute_mcp_command
            ),
            Command(
                id="mcp.add_server",
                title="MCP: Add Server",
                category=CommandCategory.MCP,
                type=CommandType.ACTION,
                description="Add a new MCP server configuration",
                icon="plus-circle",
                tags=["mcp", "add", "server", "config"],
                executor=self._execute_mcp_command,
                parameters={
                    "server_name": {
                        "type": "string",
                        "description": "Name for the new server",
                        "required": True
                    },
                    "server_type": {
                        "type": "string",
                        "description": "Type of server (github, filesystem, etc.)",
                        "required": True
                    }
                }
            ),
            Command(
                id="mcp.remove_server",
                title="MCP: Remove Server",
                category=CommandCategory.MCP,
                type=CommandType.ACTION,
                description="Remove an MCP server configuration",
                icon="trash-2",
                tags=["mcp", "remove", "server"],
                executor=self._execute_mcp_command,
                parameters={
                    "server_name": {
                        "type": "string",
                        "description": "Name of the server to remove",
                        "required": True
                    }
                }
            )
        ]

        for command in commands:
            self.registry.register_command(command)

    async def _execute_chat_command(self, command_id: str, parameters: Dict[str, Any]) -> Any:
        """Execute chat-related commands."""
        if command_id == "chat.new_tab":
            tab = await self.chat_manager.create_new_tab()
            return {"tab_id": tab.id, "title": tab.title}
        elif command_id == "chat.close_tab":
            if self.chat_manager.active_tab_id:
                success = await self.chat_manager.close_tab(self.chat_manager.active_tab_id)
                return {"success": success}
        elif command_id == "chat.export_markdown":
            if self.chat_manager.active_tab_id:
                path = await self.chat_manager.export_tab_to_markdown(self.chat_manager.active_tab_id)
                return {"export_path": str(path) if path else None}
        # Add more chat command implementations as needed
        return {"executed": command_id}

    async def _execute_edit_command(self, command_id: str, parameters: Dict[str, Any]) -> Any:
        """Execute edit-related commands."""
        if command_id == "edit.inline_edit":
            # This would trigger the inline editor
            return {"action": "show_inline_editor"}
        elif command_id == "edit.quick_question":
            # This would trigger quick question mode
            return {"action": "show_quick_question"}
        # Add more edit command implementations as needed
        return {"executed": command_id}

    async def _execute_context_command(self, command_id: str, parameters: Dict[str, Any]) -> Any:
        """Execute context-related commands."""
        if command_id == "context.clear_all":
            await self.context_manager.clear_context()
            return {"action": "context_cleared"}
        # Add more context command implementations as needed
        return {"executed": command_id}

    async def _execute_view_command(self, command_id: str, parameters: Dict[str, Any]) -> Any:
        """Execute view-related commands."""
        # These would typically send UI events to the frontend
        return {"action": "ui_toggle", "target": command_id.split(".")[1]}

    async def _execute_file_command(self, command_id: str, parameters: Dict[str, Any]) -> Any:
        """Execute file-related commands."""
        # File operations would be implemented here
        return {"executed": command_id}

    async def _execute_general_command(self, command_id: str, parameters: Dict[str, Any]) -> Any:
        """Execute general commands."""
        if command_id == "general.command_palette":
            return {"action": "toggle_command_palette"}
        elif command_id == "general.help":
            return {"action": "show_help"}
        # Add more general command implementations as needed
        return {"executed": command_id}

    async def _execute_mcp_command(self, command_id: str, parameters: Dict[str, Any]) -> Any:
        """Execute MCP-related commands."""
        try:
            # Get the enhanced MCP integration from the console (needs to be passed in)
            console = getattr(self, '_console', None)
            if not console or not hasattr(console, 'enhanced_mcp'):
                return {"error": "MCP integration not available"}

            enhanced_mcp = console.enhanced_mcp

            if command_id == "mcp.list_servers":
                servers = enhanced_mcp.get_configured_servers()
                return {"servers": servers}

            elif command_id == "mcp.status":
                status = await enhanced_mcp.get_server_status()
                return {"status": status}

            elif command_id == "mcp.connect_server":
                server_name = parameters.get("server_name")
                if not server_name:
                    return {"error": "Server name required"}
                success = await enhanced_mcp.connect_server(server_name)
                return {"success": success, "server": server_name}

            elif command_id == "mcp.disconnect_server":
                server_name = parameters.get("server_name")
                if not server_name:
                    return {"error": "Server name required"}
                await enhanced_mcp.disconnect_server(server_name)
                return {"success": True, "server": server_name}

            elif command_id == "mcp.list_tools":
                tools = await enhanced_mcp.list_available_tools()
                return {"tools": tools}

            elif command_id == "mcp.add_server":
                server_name = parameters.get("server_name")
                server_type = parameters.get("server_type")
                if not server_name or not server_type:
                    return {"error": "Server name and type required"}

                # Convert server type to config
                templates = {
                    "github": {
                        "type": "stdio",
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-github"],
                        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"}
                    },
                    "filesystem": {
                        "type": "stdio",
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
                    }
                    # Add more templates as needed
                }

                if server_type not in templates:
                    return {"error": f"Unknown server type: {server_type}"}

                enhanced_mcp.add_server(server_name, templates[server_type])
                return {"success": True, "server": server_name, "type": server_type}

            elif command_id == "mcp.remove_server":
                server_name = parameters.get("server_name")
                if not server_name:
                    return {"error": "Server name required"}
                enhanced_mcp.remove_server(server_name)
                return {"success": True, "server": server_name}

            else:
                return {"error": f"Unknown MCP command: {command_id}"}

        except Exception as e:
            return {"error": f"MCP command failed: {str(e)}"}

    async def _load_user_data(self) -> None:
        """Load user favorites and preferences."""
        try:
            user_data_path = Path.home() / ".torq_console" / "command_palette.json"
            if user_data_path.exists():
                data = json.loads(user_data_path.read_text())
                self.favorites = set(data.get("favorites", []))

                # Update command favorite status
                for command_id in self.favorites:
                    command = self.registry.get_command(command_id)
                    if command:
                        command.is_favorite = True

        except Exception as e:
            self.logger.debug(f"Could not load user data: {e}")

    async def _save_user_data(self) -> None:
        """Save user favorites and preferences."""
        try:
            user_data_path = Path.home() / ".torq_console" / "command_palette.json"
            user_data_path.parent.mkdir(parents=True, exist_ok=True)

            data = {"favorites": list(self.favorites)}
            user_data_path.write_text(json.dumps(data, indent=2))

        except Exception as e:
            self.logger.error(f"Error saving user data: {e}")

    async def get_palette_statistics(self) -> Dict[str, Any]:
        """Get command palette statistics."""
        try:
            return {
                "total_commands": len(self.registry.commands),
                "categories": {cat.value: len(self.registry.categories[cat])
                             for cat in CommandCategory},
                "shortcuts": len(self.registry.shortcuts),
                "favorites": len(self.favorites),
                "history_size": len(self.history.history),
                "popular_commands": self.history.get_popular_commands(5),
                "recent_commands": self.history.get_recent_commands(5),
                "shortcut_conflicts": len(self.registry.get_shortcut_conflicts())
            }

        except Exception as e:
            self.logger.error(f"Error getting palette statistics: {e}")
            return {}

    async def shutdown(self) -> None:
        """Shutdown the command palette system."""
        try:
            # Save user data
            await self._save_user_data()

            # Shutdown executor
            self.executor.shutdown(wait=True)

            # Cancel executing commands
            for task in self.executing_commands.values():
                if not task.done():
                    task.cancel()

            # Clear state
            self.registry.commands.clear()
            self.registry.shortcuts.clear()
            self.registry.categories.clear()
            self.favorites.clear()
            self.context_watchers.clear()
            self.executing_commands.clear()

            self.logger.info("CommandPalette shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during CommandPalette shutdown: {e}")