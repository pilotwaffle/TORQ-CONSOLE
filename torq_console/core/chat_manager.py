"""
TORQ CONSOLE Advanced Chat Management System v0.70.0 - Phase 3

Advanced chat management with multiple tab support, persistent storage,
checkpoint system, and real-time collaboration features.

Features:
- Multiple tab management with independent contexts (Cmd+T/Ctrl+T pattern)
- Chat history persistence using JSON storage with 30-day rotation
- Checkpoint system for state tracking and restoration
- Markdown export functionality for conversations
- Chat session isolation and parallel execution
- WebSocket integration for real-time updates
- Context-aware conversation management
"""

import asyncio
import json
import logging
import os
import uuid
import weakref
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable, Set, Tuple
from enum import Enum
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
import shutil

from .config import TorqConfig
from .context_manager import ContextManager, ContextMatch
from .logger import setup_logger


class ChatTabStatus(Enum):
    """Status of a chat tab."""
    ACTIVE = "active"
    BACKGROUND = "background"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class MessageType(Enum):
    """Types of chat messages."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    CONTEXT = "context"
    ERROR = "error"
    CHECKPOINT = "checkpoint"


class CheckpointType(Enum):
    """Types of checkpoints."""
    AUTO = "auto"
    MANUAL = "manual"
    CONTEXT_CHANGE = "context_change"
    FILE_CHANGE = "file_change"
    ERROR_STATE = "error_state"


@dataclass
class ChatMessage:
    """Represents a chat message."""
    id: str
    type: MessageType
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    context_matches: List[Dict[str, Any]] = field(default_factory=list)
    tokens: Optional[int] = None
    model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "context_matches": self.context_matches,
            "tokens": self.tokens,
            "model": self.model
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=MessageType(data["type"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            context_matches=data.get("context_matches", []),
            tokens=data.get("tokens"),
            model=data.get("model")
        )


@dataclass
class ChatCheckpoint:
    """Represents a chat state checkpoint."""
    id: str
    tab_id: str
    type: CheckpointType
    timestamp: datetime
    state_snapshot: Dict[str, Any]
    description: str = ""
    auto_created: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "tab_id": self.tab_id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "state_snapshot": self.state_snapshot,
            "description": self.description,
            "auto_created": self.auto_created
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatCheckpoint':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            tab_id=data["tab_id"],
            type=CheckpointType(data["type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            state_snapshot=data["state_snapshot"],
            description=data.get("description", ""),
            auto_created=data.get("auto_created", True)
        )


@dataclass
class ChatTab:
    """Represents a chat tab with independent context."""
    id: str
    title: str
    created_at: datetime
    last_accessed: datetime
    status: ChatTabStatus
    messages: List[ChatMessage] = field(default_factory=list)
    context_state: Dict[str, Any] = field(default_factory=dict)
    workspace_path: Optional[Path] = None
    model: str = "claude-sonnet-4"
    system_prompt: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "status": self.status.value,
            "messages": [msg.to_dict() for msg in self.messages],
            "context_state": self.context_state,
            "workspace_path": str(self.workspace_path) if self.workspace_path else None,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatTab':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            status=ChatTabStatus(data["status"]),
            messages=[ChatMessage.from_dict(msg) for msg in data.get("messages", [])],
            context_state=data.get("context_state", {}),
            workspace_path=Path(data["workspace_path"]) if data.get("workspace_path") else None,
            model=data.get("model", "claude-sonnet-4"),
            system_prompt=data.get("system_prompt", ""),
            metadata=data.get("metadata", {})
        )

    def get_message_count(self) -> int:
        """Get total message count."""
        return len(self.messages)

    def get_last_message(self) -> Optional[ChatMessage]:
        """Get the last message in the tab."""
        return self.messages[-1] if self.messages else None

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the tab."""
        self.messages.append(message)
        self.last_accessed = datetime.now()

    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context."""
        return {
            "message_count": len(self.messages),
            "last_activity": self.last_accessed.isoformat(),
            "context_items": len(self.context_state),
            "model": self.model,
            "workspace": str(self.workspace_path) if self.workspace_path else None
        }


class ChatPersistence:
    """Handles chat history persistence with rotation."""

    def __init__(self, storage_path: Path, retention_days: int = 30):
        self.storage_path = storage_path
        self.retention_days = retention_days
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Initialize storage structure
        self._init_storage_structure()

    def _init_storage_structure(self) -> None:
        """Initialize storage directory structure."""
        try:
            # Create subdirectories
            (self.storage_path / "tabs").mkdir(exist_ok=True)
            (self.storage_path / "checkpoints").mkdir(exist_ok=True)
            (self.storage_path / "exports").mkdir(exist_ok=True)
            (self.storage_path / "archive").mkdir(exist_ok=True)

            # Create index file if it doesn't exist
            index_file = self.storage_path / "index.json"
            if not index_file.exists():
                index_file.write_text(json.dumps({
                    "tabs": {},
                    "active_tab": None,
                    "last_cleanup": datetime.now().isoformat(),
                    "version": "0.70.0"
                }, indent=2))

        except Exception as e:
            self.logger.error(f"Error initializing storage structure: {e}")

    async def save_tab(self, tab: ChatTab) -> bool:
        """Save a chat tab to persistent storage."""
        try:
            tab_file = self.storage_path / "tabs" / f"{tab.id}.json"
            tab_data = tab.to_dict()

            # Write to temporary file first for atomic operation
            temp_file = tab_file.with_suffix('.tmp')
            temp_file.write_text(json.dumps(tab_data, indent=2), encoding='utf-8')

            # Atomic move
            if os.name == 'nt':  # Windows
                if tab_file.exists():
                    tab_file.unlink()
                temp_file.rename(tab_file)
            else:
                temp_file.rename(tab_file)

            # Update index
            await self._update_index(tab.id, {
                "title": tab.title,
                "last_accessed": tab.last_accessed.isoformat(),
                "status": tab.status.value,
                "message_count": len(tab.messages)
            })

            return True

        except Exception as e:
            self.logger.error(f"Error saving tab {tab.id}: {e}")
            return False

    async def load_tab(self, tab_id: str) -> Optional[ChatTab]:
        """Load a chat tab from persistent storage."""
        try:
            tab_file = self.storage_path / "tabs" / f"{tab_id}.json"
            if not tab_file.exists():
                return None

            tab_data = json.loads(tab_file.read_text(encoding='utf-8'))
            return ChatTab.from_dict(tab_data)

        except Exception as e:
            self.logger.error(f"Error loading tab {tab_id}: {e}")
            return None

    async def save_checkpoint(self, checkpoint: ChatCheckpoint) -> bool:
        """Save a checkpoint to persistent storage."""
        try:
            checkpoint_file = self.storage_path / "checkpoints" / f"{checkpoint.id}.json"
            checkpoint_data = checkpoint.to_dict()

            checkpoint_file.write_text(json.dumps(checkpoint_data, indent=2), encoding='utf-8')
            return True

        except Exception as e:
            self.logger.error(f"Error saving checkpoint {checkpoint.id}: {e}")
            return False

    async def load_checkpoints(self, tab_id: str) -> List[ChatCheckpoint]:
        """Load all checkpoints for a tab."""
        try:
            checkpoints = []
            checkpoint_dir = self.storage_path / "checkpoints"

            for checkpoint_file in checkpoint_dir.glob("*.json"):
                try:
                    checkpoint_data = json.loads(checkpoint_file.read_text(encoding='utf-8'))
                    if checkpoint_data.get("tab_id") == tab_id:
                        checkpoints.append(ChatCheckpoint.from_dict(checkpoint_data))
                except Exception as e:
                    self.logger.debug(f"Error loading checkpoint {checkpoint_file}: {e}")

            # Sort by timestamp
            checkpoints.sort(key=lambda c: c.timestamp, reverse=True)
            return checkpoints

        except Exception as e:
            self.logger.error(f"Error loading checkpoints for tab {tab_id}: {e}")
            return []

    async def list_tabs(self) -> List[Dict[str, Any]]:
        """List all available tabs."""
        try:
            index_file = self.storage_path / "index.json"
            if not index_file.exists():
                return []

            index_data = json.loads(index_file.read_text(encoding='utf-8'))
            return list(index_data.get("tabs", {}).values())

        except Exception as e:
            self.logger.error(f"Error listing tabs: {e}")
            return []

    async def delete_tab(self, tab_id: str) -> bool:
        """Delete a tab and its associated data."""
        try:
            # Delete tab file
            tab_file = self.storage_path / "tabs" / f"{tab_id}.json"
            if tab_file.exists():
                tab_file.unlink()

            # Delete associated checkpoints
            checkpoint_dir = self.storage_path / "checkpoints"
            for checkpoint_file in checkpoint_dir.glob("*.json"):
                try:
                    checkpoint_data = json.loads(checkpoint_file.read_text(encoding='utf-8'))
                    if checkpoint_data.get("tab_id") == tab_id:
                        checkpoint_file.unlink()
                except Exception:
                    pass

            # Update index
            await self._remove_from_index(tab_id)
            return True

        except Exception as e:
            self.logger.error(f"Error deleting tab {tab_id}: {e}")
            return False

    async def cleanup_old_data(self) -> Dict[str, int]:
        """Clean up old data based on retention policy."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            stats = {"tabs_archived": 0, "checkpoints_deleted": 0}

            # Archive old tabs
            tabs_dir = self.storage_path / "tabs"
            archive_dir = self.storage_path / "archive"

            for tab_file in tabs_dir.glob("*.json"):
                try:
                    tab_data = json.loads(tab_file.read_text(encoding='utf-8'))
                    last_accessed = datetime.fromisoformat(tab_data["last_accessed"])

                    if last_accessed < cutoff_date:
                        # Move to archive
                        archive_file = archive_dir / tab_file.name
                        shutil.move(str(tab_file), str(archive_file))
                        stats["tabs_archived"] += 1

                        # Remove from index
                        tab_id = tab_file.stem
                        await self._remove_from_index(tab_id)

                except Exception as e:
                    self.logger.debug(f"Error processing tab file {tab_file}: {e}")

            # Delete old checkpoints
            checkpoint_dir = self.storage_path / "checkpoints"
            for checkpoint_file in checkpoint_dir.glob("*.json"):
                try:
                    checkpoint_data = json.loads(checkpoint_file.read_text(encoding='utf-8'))
                    timestamp = datetime.fromisoformat(checkpoint_data["timestamp"])

                    if timestamp < cutoff_date:
                        checkpoint_file.unlink()
                        stats["checkpoints_deleted"] += 1

                except Exception as e:
                    self.logger.debug(f"Error processing checkpoint file {checkpoint_file}: {e}")

            # Update cleanup timestamp
            await self._update_cleanup_timestamp()

            self.logger.info(f"Cleanup completed: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return {"tabs_archived": 0, "checkpoints_deleted": 0}

    async def _update_index(self, tab_id: str, tab_info: Dict[str, Any]) -> None:
        """Update the index file."""
        try:
            index_file = self.storage_path / "index.json"
            index_data = json.loads(index_file.read_text(encoding='utf-8'))

            index_data["tabs"][tab_id] = tab_info
            index_file.write_text(json.dumps(index_data, indent=2), encoding='utf-8')

        except Exception as e:
            self.logger.error(f"Error updating index: {e}")

    async def _remove_from_index(self, tab_id: str) -> None:
        """Remove a tab from the index."""
        try:
            index_file = self.storage_path / "index.json"
            index_data = json.loads(index_file.read_text(encoding='utf-8'))

            index_data["tabs"].pop(tab_id, None)
            if index_data.get("active_tab") == tab_id:
                index_data["active_tab"] = None

            index_file.write_text(json.dumps(index_data, indent=2), encoding='utf-8')

        except Exception as e:
            self.logger.error(f"Error removing from index: {e}")

    async def _update_cleanup_timestamp(self) -> None:
        """Update the last cleanup timestamp."""
        try:
            index_file = self.storage_path / "index.json"
            index_data = json.loads(index_file.read_text(encoding='utf-8'))

            index_data["last_cleanup"] = datetime.now().isoformat()
            index_file.write_text(json.dumps(index_data, indent=2), encoding='utf-8')

        except Exception as e:
            self.logger.error(f"Error updating cleanup timestamp: {e}")


class MarkdownExporter:
    """Handles markdown export of chat conversations."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.exports_dir = storage_path / "exports"
        self.exports_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

    async def export_tab(self, tab: ChatTab, include_context: bool = False) -> Optional[Path]:
        """Export a chat tab to markdown format."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{tab.title.replace(' ', '_')}_{timestamp}.md"
            export_path = self.exports_dir / filename

            markdown_content = self._generate_markdown(tab, include_context)
            export_path.write_text(markdown_content, encoding='utf-8')

            self.logger.info(f"Exported tab '{tab.title}' to {export_path}")
            return export_path

        except Exception as e:
            self.logger.error(f"Error exporting tab: {e}")
            return None

    def _generate_markdown(self, tab: ChatTab, include_context: bool) -> str:
        """Generate markdown content for a chat tab."""
        lines = []

        # Header
        lines.append(f"# {tab.title}")
        lines.append("")
        lines.append(f"**Created:** {tab.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Last Accessed:** {tab.last_accessed.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Model:** {tab.model}")
        if tab.workspace_path:
            lines.append(f"**Workspace:** {tab.workspace_path}")
        lines.append("")

        # System prompt if present
        if tab.system_prompt:
            lines.append("## System Prompt")
            lines.append("")
            lines.append(f"```\n{tab.system_prompt}\n```")
            lines.append("")

        # Messages
        lines.append("## Conversation")
        lines.append("")

        for message in tab.messages:
            if message.type == MessageType.SYSTEM:
                continue  # Skip system messages in export

            # Message header
            timestamp = message.timestamp.strftime('%H:%M:%S')
            if message.type == MessageType.USER:
                lines.append(f"### 👤 User ({timestamp})")
            elif message.type == MessageType.ASSISTANT:
                lines.append(f"### 🤖 Assistant ({timestamp})")
                if message.model:
                    lines.append(f"*Model: {message.model}*")
            elif message.type == MessageType.ERROR:
                lines.append(f"### ❌ Error ({timestamp})")
            else:
                lines.append(f"### 📝 {message.type.value.title()} ({timestamp})")

            lines.append("")

            # Message content
            content = message.content.strip()
            if content.startswith("```") and content.endswith("```"):
                # Already formatted as code block
                lines.append(content)
            else:
                # Add as regular text
                lines.append(content)

            lines.append("")

            # Context information if requested
            if include_context and message.context_matches:
                lines.append("**Context Used:**")
                for ctx in message.context_matches:
                    lines.append(f"- {ctx.get('pattern', 'Unknown')} (score: {ctx.get('score', 0):.2f})")
                lines.append("")

            # Metadata if present
            if message.metadata and any(k not in ['context_used', 'tokens'] for k in message.metadata):
                lines.append("**Metadata:**")
                for key, value in message.metadata.items():
                    if key not in ['context_used', 'tokens']:
                        lines.append(f"- {key}: {value}")
                lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} from TORQ CONSOLE v0.70.0*")

        return "\n".join(lines)


class ChatManager:
    """
    Advanced chat management system for TORQ CONSOLE v0.70.0.

    Provides multiple tab management, persistent storage, checkpoint system,
    real-time collaboration features, and session isolation for parallel execution.
    """

    def __init__(self, config: TorqConfig, context_manager: ContextManager,
                 storage_path: Optional[Path] = None):
        self.config = config
        self.context_manager = context_manager
        self.logger = setup_logger("chat_manager")

        # Storage configuration
        if storage_path is None:
            storage_path = Path.home() / ".torq_console" / "chat_history"
        self.storage_path = storage_path

        # Initialize components
        self.persistence = ChatPersistence(self.storage_path)
        self.exporter = MarkdownExporter(self.storage_path)

        # Chat state
        self.active_tabs: Dict[str, ChatTab] = {}
        self.active_tab_id: Optional[str] = None
        self.checkpoints: Dict[str, List[ChatCheckpoint]] = defaultdict(list)

        # Session isolation for parallel execution
        self.isolated_sessions: Dict[str, Dict[str, Any]] = {}  # tab_id -> session_state
        self.session_locks: Dict[str, asyncio.Lock] = {}  # tab_id -> lock
        self.parallel_executors: Dict[str, ThreadPoolExecutor] = {}  # tab_id -> executor

        # WebSocket connections for real-time updates
        self.websocket_connections: Dict[str, weakref.ReferenceType] = {}
        self.websocket_callbacks: List[Callable] = []

        # Threading for background operations
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="chat_mgr")
        self._cleanup_task: Optional[asyncio.Task] = None

        # Message processing queue for parallel execution
        self.message_processing_queue: asyncio.Queue = asyncio.Queue()
        self.processing_tasks: Dict[str, asyncio.Task] = {}  # tab_id -> processing_task

        # Tab management
        self.tab_order: List[str] = []  # For managing tab order
        self.max_concurrent_tabs = 10
        self.max_parallel_sessions = 5

        self.logger.info(f"ChatManager initialized with storage at {self.storage_path}")

    async def initialize(self) -> None:
        """Initialize the chat manager."""
        try:
            # Load existing tabs
            await self._load_existing_tabs()

            # Start background cleanup task
            self._cleanup_task = asyncio.create_task(self._background_cleanup())

            self.logger.info("ChatManager initialization completed")

        except Exception as e:
            self.logger.error(f"Error initializing ChatManager: {e}")

    async def create_new_tab(self, title: Optional[str] = None,
                           workspace_path: Optional[Path] = None,
                           model: str = "claude-sonnet-4") -> ChatTab:
        """Create a new chat tab (Cmd+T/Ctrl+T pattern)."""
        try:
            # Generate unique ID
            tab_id = str(uuid.uuid4())

            # Generate title if not provided
            if not title:
                tab_count = len(self.active_tabs) + 1
                title = f"Chat {tab_count}"

            # Create new tab
            tab = ChatTab(
                id=tab_id,
                title=title,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                status=ChatTabStatus.ACTIVE,
                workspace_path=workspace_path,
                model=model
            )

            # Add to active tabs
            self.active_tabs[tab_id] = tab
            self.tab_order.append(tab_id)

            # Set as active tab
            await self.switch_to_tab(tab_id)

            # Create initial checkpoint
            await self._create_checkpoint(
                tab_id, CheckpointType.AUTO, "Tab created"
            )

            # Save to persistence
            await self.persistence.save_tab(tab)

            # Notify WebSocket clients
            await self._notify_websocket_clients({
                "type": "tab_created",
                "tab": tab.to_dict(),
                "timestamp": datetime.now().isoformat()
            })

            self.logger.info(f"Created new chat tab: {title} ({tab_id})")
            return tab

        except Exception as e:
            self.logger.error(f"Error creating new tab: {e}")
            raise

    async def switch_to_tab(self, tab_id: str) -> bool:
        """Switch to a specific chat tab."""
        try:
            if tab_id not in self.active_tabs:
                # Try to load from persistence
                tab = await self.persistence.load_tab(tab_id)
                if tab:
                    self.active_tabs[tab_id] = tab
                    if tab_id not in self.tab_order:
                        self.tab_order.append(tab_id)
                else:
                    return False

            # Update tab status
            if self.active_tab_id:
                old_tab = self.active_tabs.get(self.active_tab_id)
                if old_tab:
                    old_tab.status = ChatTabStatus.BACKGROUND

            self.active_tab_id = tab_id
            current_tab = self.active_tabs[tab_id]
            current_tab.status = ChatTabStatus.ACTIVE
            current_tab.last_accessed = datetime.now()

            # Save updated tab
            await self.persistence.save_tab(current_tab)

            # Notify WebSocket clients
            await self._notify_websocket_clients({
                "type": "tab_switched",
                "active_tab_id": tab_id,
                "timestamp": datetime.now().isoformat()
            })

            self.logger.debug(f"Switched to tab: {tab_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error switching to tab {tab_id}: {e}")
            return False

    async def close_tab(self, tab_id: str, force: bool = False) -> bool:
        """Close a chat tab."""
        try:
            if tab_id not in self.active_tabs:
                return False

            tab = self.active_tabs[tab_id]

            # Check if tab has unsaved changes
            if not force and len(tab.messages) > 0:
                # Create final checkpoint before closing
                await self._create_checkpoint(
                    tab_id, CheckpointType.AUTO, "Tab closed"
                )

            # Remove from active tabs
            del self.active_tabs[tab_id]
            if tab_id in self.tab_order:
                self.tab_order.remove(tab_id)

            # Switch to another tab if this was active
            if self.active_tab_id == tab_id:
                if self.tab_order:
                    await self.switch_to_tab(self.tab_order[-1])
                else:
                    self.active_tab_id = None

            # Save final state
            await self.persistence.save_tab(tab)

            # Notify WebSocket clients
            await self._notify_websocket_clients({
                "type": "tab_closed",
                "tab_id": tab_id,
                "timestamp": datetime.now().isoformat()
            })

            self.logger.info(f"Closed chat tab: {tab.title} ({tab_id})")
            return True

        except Exception as e:
            self.logger.error(f"Error closing tab {tab_id}: {e}")
            return False

    async def add_message(self, content: str, message_type: MessageType = MessageType.USER,
                         tab_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
                         context_matches: Optional[List[ContextMatch]] = None) -> Optional[ChatMessage]:
        """Add a message to a chat tab."""
        try:
            # Use active tab if not specified
            if tab_id is None:
                tab_id = self.active_tab_id

            if not tab_id or tab_id not in self.active_tabs:
                return None

            tab = self.active_tabs[tab_id]

            # Create message
            message = ChatMessage(
                id=str(uuid.uuid4()),
                type=message_type,
                content=content,
                timestamp=datetime.now(),
                metadata=metadata or {},
                context_matches=[match.metadata for match in (context_matches or [])],
                model=tab.model if message_type == MessageType.ASSISTANT else None
            )

            # Add to tab
            tab.add_message(message)

            # Auto-create checkpoint for significant messages
            if len(tab.messages) % 10 == 0:  # Every 10 messages
                await self._create_checkpoint(
                    tab_id, CheckpointType.AUTO, f"Message #{len(tab.messages)}"
                )

            # Save tab
            await self.persistence.save_tab(tab)

            # Notify WebSocket clients
            await self._notify_websocket_clients({
                "type": "message_added",
                "tab_id": tab_id,
                "message": message.to_dict(),
                "timestamp": datetime.now().isoformat()
            })

            return message

        except Exception as e:
            self.logger.error(f"Error adding message: {e}")
            return None

    async def get_tab_messages(self, tab_id: str, limit: Optional[int] = None,
                              offset: int = 0) -> List[ChatMessage]:
        """Get messages from a chat tab."""
        try:
            if tab_id not in self.active_tabs:
                # Try to load from persistence
                tab = await self.persistence.load_tab(tab_id)
                if not tab:
                    return []
                self.active_tabs[tab_id] = tab

            tab = self.active_tabs[tab_id]
            messages = tab.messages[offset:]

            if limit:
                messages = messages[:limit]

            return messages

        except Exception as e:
            self.logger.error(f"Error getting messages for tab {tab_id}: {e}")
            return []

    async def create_checkpoint(self, tab_id: Optional[str] = None,
                              checkpoint_type: CheckpointType = CheckpointType.MANUAL,
                              description: str = "") -> Optional[ChatCheckpoint]:
        """Create a manual checkpoint."""
        if tab_id is None:
            tab_id = self.active_tab_id

        if not tab_id:
            return None

        return await self._create_checkpoint(tab_id, checkpoint_type, description, auto_created=False)

    async def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """Restore a chat tab to a previous checkpoint."""
        try:
            # Find the checkpoint
            checkpoint = None
            for tab_checkpoints in self.checkpoints.values():
                for cp in tab_checkpoints:
                    if cp.id == checkpoint_id:
                        checkpoint = cp
                        break
                if checkpoint:
                    break

            if not checkpoint:
                return False

            tab_id = checkpoint.tab_id
            if tab_id not in self.active_tabs:
                # Load tab from persistence
                tab = await self.persistence.load_tab(tab_id)
                if not tab:
                    return False
                self.active_tabs[tab_id] = tab

            tab = self.active_tabs[tab_id]

            # Restore state from checkpoint
            state = checkpoint.state_snapshot
            if "messages" in state:
                tab.messages = [ChatMessage.from_dict(msg) for msg in state["messages"]]
            if "context_state" in state:
                tab.context_state = state["context_state"]
            if "model" in state:
                tab.model = state["model"]
            if "system_prompt" in state:
                tab.system_prompt = state["system_prompt"]

            # Save restored tab
            await self.persistence.save_tab(tab)

            # Create checkpoint for this restoration
            await self._create_checkpoint(
                tab_id, CheckpointType.AUTO, f"Restored to: {checkpoint.description}"
            )

            # Notify WebSocket clients
            await self._notify_websocket_clients({
                "type": "checkpoint_restored",
                "tab_id": tab_id,
                "checkpoint_id": checkpoint_id,
                "timestamp": datetime.now().isoformat()
            })

            self.logger.info(f"Restored tab {tab_id} to checkpoint {checkpoint_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error restoring checkpoint {checkpoint_id}: {e}")
            return False

    async def export_tab_to_markdown(self, tab_id: str, include_context: bool = False) -> Optional[Path]:
        """Export a chat tab to markdown format."""
        try:
            if tab_id not in self.active_tabs:
                tab = await self.persistence.load_tab(tab_id)
                if not tab:
                    return None
            else:
                tab = self.active_tabs[tab_id]

            export_path = await self.exporter.export_tab(tab, include_context)

            if export_path:
                # Notify WebSocket clients
                await self._notify_websocket_clients({
                    "type": "tab_exported",
                    "tab_id": tab_id,
                    "export_path": str(export_path),
                    "timestamp": datetime.now().isoformat()
                })

            return export_path

        except Exception as e:
            self.logger.error(f"Error exporting tab {tab_id}: {e}")
            return None

    async def get_tab_list(self) -> List[Dict[str, Any]]:
        """Get list of all chat tabs."""
        try:
            tab_list = []

            # Add active tabs
            for tab_id in self.tab_order:
                if tab_id in self.active_tabs:
                    tab = self.active_tabs[tab_id]
                    tab_list.append({
                        "id": tab.id,
                        "title": tab.title,
                        "status": tab.status.value,
                        "message_count": len(tab.messages),
                        "last_accessed": tab.last_accessed.isoformat(),
                        "created_at": tab.created_at.isoformat(),
                        "model": tab.model,
                        "is_active": tab_id == self.active_tab_id
                    })

            # Add available tabs from persistence
            persisted_tabs = await self.persistence.list_tabs()
            for tab_info in persisted_tabs:
                if not any(t["id"] == tab_info.get("id") for t in tab_list):
                    tab_list.append({
                        **tab_info,
                        "is_active": False,
                        "status": "background"
                    })

            return tab_list

        except Exception as e:
            self.logger.error(f"Error getting tab list: {e}")
            return []

    async def get_checkpoint_list(self, tab_id: str) -> List[Dict[str, Any]]:
        """Get list of checkpoints for a tab."""
        try:
            checkpoints = await self.persistence.load_checkpoints(tab_id)
            return [cp.to_dict() for cp in checkpoints]

        except Exception as e:
            self.logger.error(f"Error getting checkpoint list for tab {tab_id}: {e}")
            return []

    async def update_tab_context(self, tab_id: str, context_update: Dict[str, Any]) -> bool:
        """Update the context state of a tab."""
        try:
            if tab_id not in self.active_tabs:
                return False

            tab = self.active_tabs[tab_id]
            old_context = tab.context_state.copy()

            # Update context
            tab.context_state.update(context_update)

            # Create checkpoint if significant context change
            if len(context_update) > 3:
                await self._create_checkpoint(
                    tab_id, CheckpointType.CONTEXT_CHANGE, "Context updated"
                )

            # Save tab
            await self.persistence.save_tab(tab)

            # Notify WebSocket clients
            await self._notify_websocket_clients({
                "type": "context_updated",
                "tab_id": tab_id,
                "context_update": context_update,
                "timestamp": datetime.now().isoformat()
            })

            return True

        except Exception as e:
            self.logger.error(f"Error updating tab context: {e}")
            return False

    async def register_websocket_callback(self, callback: Callable) -> None:
        """Register a callback for WebSocket notifications."""
        self.websocket_callbacks.append(callback)

    async def unregister_websocket_callback(self, callback: Callable) -> None:
        """Unregister a WebSocket callback."""
        if callback in self.websocket_callbacks:
            self.websocket_callbacks.remove(callback)

    async def get_chat_statistics(self) -> Dict[str, Any]:
        """Get chat management statistics."""
        try:
            active_tabs = len(self.active_tabs)
            total_messages = sum(len(tab.messages) for tab in self.active_tabs.values())
            total_checkpoints = sum(len(checkpoints) for checkpoints in self.checkpoints.values())

            # Get storage statistics
            storage_size = 0
            if self.storage_path.exists():
                for file_path in self.storage_path.rglob("*.json"):
                    try:
                        storage_size += file_path.stat().st_size
                    except Exception:
                        pass

            return {
                "active_tabs": active_tabs,
                "total_messages": total_messages,
                "total_checkpoints": total_checkpoints,
                "storage_size_mb": storage_size / (1024 * 1024),
                "storage_path": str(self.storage_path),
                "websocket_connections": len(self.websocket_callbacks),
                "current_tab": self.active_tab_id
            }

        except Exception as e:
            self.logger.error(f"Error getting chat statistics: {e}")
            return {}

    async def _create_checkpoint(self, tab_id: str, checkpoint_type: CheckpointType,
                               description: str, auto_created: bool = True) -> Optional[ChatCheckpoint]:
        """Create a checkpoint for a chat tab."""
        try:
            if tab_id not in self.active_tabs:
                return None

            tab = self.active_tabs[tab_id]

            # Create state snapshot
            state_snapshot = {
                "messages": [msg.to_dict() for msg in tab.messages],
                "context_state": tab.context_state.copy(),
                "model": tab.model,
                "system_prompt": tab.system_prompt,
                "metadata": tab.metadata.copy()
            }

            # Create checkpoint
            checkpoint = ChatCheckpoint(
                id=str(uuid.uuid4()),
                tab_id=tab_id,
                type=checkpoint_type,
                timestamp=datetime.now(),
                state_snapshot=state_snapshot,
                description=description,
                auto_created=auto_created
            )

            # Store checkpoint
            self.checkpoints[tab_id].append(checkpoint)

            # Limit number of checkpoints per tab
            if len(self.checkpoints[tab_id]) > 50:
                # Remove oldest auto-created checkpoint
                for i, cp in enumerate(self.checkpoints[tab_id]):
                    if cp.auto_created:
                        self.checkpoints[tab_id].pop(i)
                        break

            # Save to persistence
            await self.persistence.save_checkpoint(checkpoint)

            self.logger.debug(f"Created checkpoint for tab {tab_id}: {description}")
            return checkpoint

        except Exception as e:
            self.logger.error(f"Error creating checkpoint: {e}")
            return None

    async def _load_existing_tabs(self) -> None:
        """Load existing tabs from persistence."""
        try:
            tab_list = await self.persistence.list_tabs()

            # Load recently accessed tabs
            recent_tabs = sorted(
                tab_list,
                key=lambda t: t.get("last_accessed", ""),
                reverse=True
            )[:5]  # Load top 5 recent tabs

            for tab_info in recent_tabs:
                tab_id = tab_info.get("id")
                if tab_id:
                    tab = await self.persistence.load_tab(tab_id)
                    if tab:
                        tab.status = ChatTabStatus.BACKGROUND
                        self.active_tabs[tab_id] = tab
                        self.tab_order.append(tab_id)

            # Set most recent as active
            if self.tab_order:
                await self.switch_to_tab(self.tab_order[0])

            self.logger.info(f"Loaded {len(self.active_tabs)} existing tabs")

        except Exception as e:
            self.logger.error(f"Error loading existing tabs: {e}")

    async def _notify_websocket_clients(self, message: Dict[str, Any]) -> None:
        """Notify all WebSocket clients of an event."""
        try:
            for callback in self.websocket_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    self.logger.debug(f"Error in WebSocket callback: {e}")

        except Exception as e:
            self.logger.error(f"Error notifying WebSocket clients: {e}")

    async def _background_cleanup(self) -> None:
        """Background task for periodic cleanup."""
        try:
            while True:
                await asyncio.sleep(3600)  # Run every hour

                try:
                    # Cleanup old data
                    stats = await self.persistence.cleanup_old_data()
                    if stats["tabs_archived"] > 0 or stats["checkpoints_deleted"] > 0:
                        self.logger.info(f"Background cleanup: {stats}")

                    # Suspend inactive tabs
                    cutoff_time = datetime.now() - timedelta(hours=2)
                    for tab_id, tab in list(self.active_tabs.items()):
                        if (tab.status == ChatTabStatus.BACKGROUND and
                            tab.last_accessed < cutoff_time):
                            tab.status = ChatTabStatus.SUSPENDED
                            await self.persistence.save_tab(tab)

                            # Remove from memory if too many tabs
                            if len(self.active_tabs) > self.max_concurrent_tabs:
                                del self.active_tabs[tab_id]
                                if tab_id in self.tab_order:
                                    self.tab_order.remove(tab_id)

                except Exception as e:
                    self.logger.error(f"Error in background cleanup: {e}")

        except asyncio.CancelledError:
            self.logger.info("Background cleanup task cancelled")
        except Exception as e:
            self.logger.error(f"Unexpected error in background cleanup: {e}")

    async def create_isolated_session(self, tab_id: str) -> Dict[str, Any]:
        """Create an isolated session for a chat tab."""
        try:
            if tab_id not in self.active_tabs:
                raise ValueError(f"Tab {tab_id} not found")

            # Create session lock if not exists
            if tab_id not in self.session_locks:
                self.session_locks[tab_id] = asyncio.Lock()

            async with self.session_locks[tab_id]:
                # Create isolated session state
                session_state = {
                    "tab_id": tab_id,
                    "created_at": datetime.now(),
                    "context_state": self.active_tabs[tab_id].context_state.copy(),
                    "workspace_path": self.active_tabs[tab_id].workspace_path,
                    "model": self.active_tabs[tab_id].model,
                    "system_prompt": self.active_tabs[tab_id].system_prompt,
                    "active_tools": [],
                    "execution_queue": asyncio.Queue(),
                    "result_cache": {}
                }

                self.isolated_sessions[tab_id] = session_state

                # Create dedicated executor for this session
                if tab_id not in self.parallel_executors:
                    self.parallel_executors[tab_id] = ThreadPoolExecutor(
                        max_workers=2,
                        thread_name_prefix=f"tab_{tab_id[:8]}"
                    )

                # Start processing task for this tab
                if tab_id not in self.processing_tasks:
                    self.processing_tasks[tab_id] = asyncio.create_task(
                        self._process_tab_messages(tab_id)
                    )

                self.logger.info(f"Created isolated session for tab {tab_id}")
                return session_state

        except Exception as e:
            self.logger.error(f"Error creating isolated session for {tab_id}: {e}")
            raise

    async def execute_in_isolated_session(self, tab_id: str, operation: Callable,
                                        *args, **kwargs) -> Any:
        """Execute an operation in an isolated session."""
        try:
            if tab_id not in self.isolated_sessions:
                await self.create_isolated_session(tab_id)

            if tab_id not in self.session_locks:
                self.session_locks[tab_id] = asyncio.Lock()

            async with self.session_locks[tab_id]:
                session_state = self.isolated_sessions[tab_id]
                executor = self.parallel_executors.get(tab_id)

                if not executor:
                    raise RuntimeError(f"No executor found for tab {tab_id}")

                # Execute operation in isolated context
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(session_state, *args, **kwargs)
                else:
                    # Run in executor for CPU-bound operations
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        executor, operation, session_state, *args, **kwargs
                    )

                # Update session state if needed
                if isinstance(result, dict) and "session_update" in result:
                    session_state.update(result["session_update"])

                return result

        except Exception as e:
            self.logger.error(f"Error executing in isolated session {tab_id}: {e}")
            raise

    async def _process_tab_messages(self, tab_id: str) -> None:
        """Process messages for a specific tab in parallel."""
        try:
            session_state = self.isolated_sessions.get(tab_id)
            if not session_state:
                return

            execution_queue = session_state["execution_queue"]

            while True:
                try:
                    # Wait for messages with timeout
                    message_task = await asyncio.wait_for(
                        execution_queue.get(), timeout=5.0
                    )

                    # Process the message
                    await self._handle_tab_message_task(tab_id, message_task)

                    # Mark task as done
                    execution_queue.task_done()

                except asyncio.TimeoutError:
                    # No messages to process, continue
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing message for tab {tab_id}: {e}")

        except asyncio.CancelledError:
            self.logger.info(f"Message processing cancelled for tab {tab_id}")
        except Exception as e:
            self.logger.error(f"Unexpected error in message processing for {tab_id}: {e}")

    async def _handle_tab_message_task(self, tab_id: str, message_task: Dict[str, Any]) -> None:
        """Handle a specific message task for a tab."""
        try:
            task_type = message_task.get("type")
            task_data = message_task.get("data", {})

            if task_type == "ai_response":
                await self._generate_ai_response(tab_id, task_data)
            elif task_type == "context_update":
                await self._update_tab_context_async(tab_id, task_data)
            elif task_type == "file_operation":
                await self._handle_file_operation(tab_id, task_data)
            else:
                self.logger.warning(f"Unknown task type for tab {tab_id}: {task_type}")

        except Exception as e:
            self.logger.error(f"Error handling task for tab {tab_id}: {e}")

    async def _generate_ai_response(self, tab_id: str, task_data: Dict[str, Any]) -> None:
        """Generate AI response for a message."""
        try:
            # This would integrate with the actual AI model
            # For now, simulate response generation
            prompt = task_data.get("prompt", "")
            context = task_data.get("context", [])

            # Simulate AI processing time
            await asyncio.sleep(0.5)

            response_content = f"AI response to: {prompt[:50]}..."

            # Add response message
            await self.add_message(
                content=response_content,
                message_type=MessageType.ASSISTANT,
                tab_id=tab_id,
                metadata={"generated": True, "model": self.active_tabs[tab_id].model}
            )

        except Exception as e:
            self.logger.error(f"Error generating AI response for tab {tab_id}: {e}")

    async def _update_tab_context_async(self, tab_id: str, context_data: Dict[str, Any]) -> None:
        """Update tab context asynchronously."""
        try:
            await self.update_tab_context(tab_id, context_data)
        except Exception as e:
            self.logger.error(f"Error updating context for tab {tab_id}: {e}")

    async def _handle_file_operation(self, tab_id: str, operation_data: Dict[str, Any]) -> None:
        """Handle file operations for a tab."""
        try:
            operation = operation_data.get("operation")
            file_path = operation_data.get("file_path")

            if operation == "read":
                # Handle file read operation
                pass
            elif operation == "write":
                # Handle file write operation
                pass
            elif operation == "analyze":
                # Handle file analysis operation
                pass

            self.logger.debug(f"Handled file operation {operation} for tab {tab_id}")

        except Exception as e:
            self.logger.error(f"Error handling file operation for tab {tab_id}: {e}")

    async def queue_message_for_processing(self, tab_id: str, message_type: str,
                                         data: Dict[str, Any]) -> None:
        """Queue a message for processing in the tab's isolated session."""
        try:
            if tab_id not in self.isolated_sessions:
                await self.create_isolated_session(tab_id)

            session_state = self.isolated_sessions[tab_id]
            execution_queue = session_state["execution_queue"]

            message_task = {
                "type": message_type,
                "data": data,
                "timestamp": datetime.now(),
                "tab_id": tab_id
            }

            await execution_queue.put(message_task)
            self.logger.debug(f"Queued {message_type} for tab {tab_id}")

        except Exception as e:
            self.logger.error(f"Error queuing message for tab {tab_id}: {e}")

    async def get_session_status(self, tab_id: str) -> Dict[str, Any]:
        """Get the status of an isolated session."""
        try:
            if tab_id not in self.isolated_sessions:
                return {"status": "not_created"}

            session_state = self.isolated_sessions[tab_id]
            processing_task = self.processing_tasks.get(tab_id)
            executor = self.parallel_executors.get(tab_id)

            return {
                "status": "active",
                "created_at": session_state["created_at"].isoformat(),
                "queue_size": session_state["execution_queue"].qsize(),
                "processing_task_running": processing_task and not processing_task.done(),
                "executor_active": executor and not executor._shutdown,
                "cache_size": len(session_state.get("result_cache", {}))
            }

        except Exception as e:
            self.logger.error(f"Error getting session status for {tab_id}: {e}")
            return {"status": "error", "error": str(e)}

    async def cleanup_isolated_session(self, tab_id: str) -> None:
        """Clean up an isolated session."""
        try:
            # Cancel processing task
            if tab_id in self.processing_tasks:
                task = self.processing_tasks.pop(tab_id)
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            # Shutdown executor
            if tab_id in self.parallel_executors:
                executor = self.parallel_executors.pop(tab_id)
                executor.shutdown(wait=False)

            # Remove session state
            self.isolated_sessions.pop(tab_id, None)
            self.session_locks.pop(tab_id, None)

            self.logger.info(f"Cleaned up isolated session for tab {tab_id}")

        except Exception as e:
            self.logger.error(f"Error cleaning up session for {tab_id}: {e}")

    async def shutdown(self) -> None:
        """Shutdown the chat manager."""
        try:
            # Cancel background task
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass

            # Cleanup all isolated sessions
            for tab_id in list(self.isolated_sessions.keys()):
                await self.cleanup_isolated_session(tab_id)

            # Save all active tabs
            for tab in self.active_tabs.values():
                await self.persistence.save_tab(tab)

            # Shutdown main executor
            self.executor.shutdown(wait=True)

            # Shutdown remaining parallel executors
            for executor in self.parallel_executors.values():
                executor.shutdown(wait=False)

            # Clear state
            self.active_tabs.clear()
            self.checkpoints.clear()
            self.websocket_callbacks.clear()
            self.isolated_sessions.clear()
            self.session_locks.clear()
            self.parallel_executors.clear()
            self.processing_tasks.clear()

            self.logger.info("ChatManager shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during ChatManager shutdown: {e}")