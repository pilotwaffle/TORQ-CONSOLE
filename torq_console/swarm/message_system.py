"""
Message System for TORQ Console - Agency Swarm Compatible.

Handles message queuing, delivery, persistence, and acknowledgment
for inter-agent communication in the swarm system.
"""

import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class MessageStatus(Enum):
    """Message delivery status."""
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class Message:
    """Represents an inter-agent message."""
    message_id: str
    source_agent: str
    target_agent: str
    content: str
    priority: MessagePriority = MessagePriority.NORMAL
    require_ack: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: MessageStatus = MessageStatus.PENDING
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        """Set expiration time if not provided."""
        if self.expires_at is None:
            # Set expiration based on priority
            if self.priority == MessagePriority.CRITICAL:
                self.expires_at = self.created_at + timedelta(minutes=5)
            elif self.priority == MessagePriority.HIGH:
                self.expires_at = self.created_at + timedelta(minutes=15)
            else:
                self.expires_at = self.created_at + timedelta(hours=1)

    def is_expired(self) -> bool:
        """Check if message has expired."""
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            'message_id': self.message_id,
            'source_agent': self.source_agent,
            'target_agent': self.target_agent,
            'content': self.content,
            'priority': self.priority.name,
            'require_ack': self.require_ack,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'status': self.status.value,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'metadata': self.metadata,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        msg = cls(
            message_id=data['message_id'],
            source_agent=data['source_agent'],
            target_agent=data['target_agent'],
            content=data['content'],
            priority=MessagePriority[data['priority']],
            require_ack=data['require_ack'],
            metadata=data.get('metadata', {}),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3)
        )

        # Parse datetime fields
        msg.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('expires_at'):
            msg.expires_at = datetime.fromisoformat(data['expires_at'])
        if data.get('delivered_at'):
            msg.delivered_at = datetime.fromisoformat(data['delivered_at'])
        if data.get('acknowledged_at'):
            msg.acknowledged_at = datetime.fromisoformat(data['acknowledged_at'])

        msg.status = MessageStatus(data['status'])
        return msg


class MessageQueue:
    """Priority-based message queue for agents."""

    def __init__(self, agent_id: str, max_size: int = 1000):
        self.agent_id = agent_id
        self.max_size = max_size
        self._queues = {
            MessagePriority.CRITICAL: deque(),
            MessagePriority.HIGH: deque(),
            MessagePriority.NORMAL: deque(),
            MessagePriority.LOW: deque()
        }
        self._lock = asyncio.Lock()

    async def enqueue(self, message: Message) -> bool:
        """Add message to queue based on priority."""
        async with self._lock:
            # Check if queue is full
            total_messages = sum(len(q) for q in self._queues.values())
            if total_messages >= self.max_size:
                # Remove oldest low priority message if possible
                if self._queues[MessagePriority.LOW]:
                    self._queues[MessagePriority.LOW].popleft()
                else:
                    return False  # Queue full, can't add

            # Add to appropriate priority queue
            self._queues[message.priority].append(message)
            return True

    async def dequeue(self) -> Optional[Message]:
        """Remove and return highest priority message."""
        async with self._lock:
            # Check queues in priority order
            for priority in [MessagePriority.CRITICAL, MessagePriority.HIGH,
                           MessagePriority.NORMAL, MessagePriority.LOW]:
                if self._queues[priority]:
                    return self._queues[priority].popleft()
            return None

    async def peek(self) -> Optional[Message]:
        """Return next message without removing it."""
        async with self._lock:
            for priority in [MessagePriority.CRITICAL, MessagePriority.HIGH,
                           MessagePriority.NORMAL, MessagePriority.LOW]:
                if self._queues[priority]:
                    return self._queues[priority][0]
            return None

    async def get_all_messages(self) -> List[Message]:
        """Get all messages in priority order."""
        async with self._lock:
            messages = []
            for priority in [MessagePriority.CRITICAL, MessagePriority.HIGH,
                           MessagePriority.NORMAL, MessagePriority.LOW]:
                messages.extend(list(self._queues[priority]))
            return messages

    async def clear_expired(self) -> int:
        """Remove expired messages and return count."""
        async with self._lock:
            removed_count = 0
            for priority_queue in self._queues.values():
                expired_messages = []
                for message in priority_queue:
                    if message.is_expired():
                        expired_messages.append(message)

                for expired_msg in expired_messages:
                    priority_queue.remove(expired_msg)
                    expired_msg.status = MessageStatus.EXPIRED
                    removed_count += 1

            return removed_count

    async def size(self) -> int:
        """Get total number of messages in queue."""
        async with self._lock:
            return sum(len(q) for q in self._queues.values())


class MessageSystem:
    """
    Central message system for inter-agent communication.

    Features:
    - Priority-based message queuing
    - Message delivery and acknowledgment
    - Message persistence and history
    - Automatic retry and expiration
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)

        # Message queues per agent
        self.agent_queues: Dict[str, MessageQueue] = {}

        # Message storage and tracking
        self.message_history: Dict[str, Message] = {}
        self.pending_acknowledgments: Dict[str, Message] = {}

        # System configuration
        self.max_history_size = 10000
        self.cleanup_interval = timedelta(minutes=10)
        self.last_cleanup = datetime.now()

        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_delivered': 0,
            'messages_acknowledged': 0,
            'messages_failed': 0,
            'messages_expired': 0
        }

    async def create_message(self, source_agent: str, target_agent: str,
                           content: str, priority: str = 'normal',
                           require_ack: bool = False, **kwargs) -> Message:
        """Create a new message."""
        message_id = str(uuid.uuid4())

        # Convert priority string to enum
        priority_map = {
            'low': MessagePriority.LOW,
            'normal': MessagePriority.NORMAL,
            'high': MessagePriority.HIGH,
            'critical': MessagePriority.CRITICAL
        }

        msg_priority = priority_map.get(priority.lower(), MessagePriority.NORMAL)

        message = Message(
            message_id=message_id,
            source_agent=source_agent,
            target_agent=target_agent,
            content=content,
            priority=msg_priority,
            require_ack=require_ack,
            metadata=kwargs
        )

        # Store in history
        self.message_history[message_id] = message

        return message

    async def send_message(self, message: Message) -> Dict[str, Any]:
        """Send message to target agent."""
        try:
            # Ensure target agent queue exists
            if message.target_agent not in self.agent_queues:
                self.agent_queues[message.target_agent] = MessageQueue(message.target_agent)

            # Add to target agent's queue
            success = await self.agent_queues[message.target_agent].enqueue(message)

            if success:
                message.status = MessageStatus.DELIVERED
                message.delivered_at = datetime.now()

                # Track pending acknowledgment if required
                if message.require_ack:
                    self.pending_acknowledgments[message.message_id] = message

                self.stats['messages_sent'] += 1
                self.stats['messages_delivered'] += 1

                self.logger.info(f"Message {message.message_id} delivered: "
                               f"{message.source_agent} -> {message.target_agent}")

                return {
                    'success': True,
                    'message_id': message.message_id,
                    'status': 'delivered',
                    'delivered_at': message.delivered_at.isoformat()
                }
            else:
                message.status = MessageStatus.FAILED
                self.stats['messages_failed'] += 1

                self.logger.error(f"Failed to deliver message {message.message_id}: Queue full")

                return {
                    'success': False,
                    'message_id': message.message_id,
                    'status': 'failed',
                    'error': 'Target agent queue is full'
                }

        except Exception as e:
            message.status = MessageStatus.FAILED
            self.stats['messages_failed'] += 1

            self.logger.error(f"Error sending message {message.message_id}: {e}")

            return {
                'success': False,
                'message_id': message.message_id,
                'status': 'failed',
                'error': str(e)
            }

    async def receive_messages(self, agent_id: str) -> List[Message]:
        """Retrieve all messages for an agent."""
        if agent_id not in self.agent_queues:
            return []

        messages = []
        queue = self.agent_queues[agent_id]

        # Get all messages from queue
        while True:
            message = await queue.dequeue()
            if message is None:
                break

            # Check if message has expired
            if message.is_expired():
                message.status = MessageStatus.EXPIRED
                self.stats['messages_expired'] += 1
                continue

            messages.append(message)

        return messages

    async def acknowledge_message(self, message_id: str, agent_id: str) -> bool:
        """Acknowledge receipt of a message."""
        if message_id in self.pending_acknowledgments:
            message = self.pending_acknowledgments[message_id]

            if message.target_agent == agent_id:
                message.status = MessageStatus.ACKNOWLEDGED
                message.acknowledged_at = datetime.now()

                del self.pending_acknowledgments[message_id]
                self.stats['messages_acknowledged'] += 1

                self.logger.info(f"Message {message_id} acknowledged by {agent_id}")
                return True

        return False

    async def get_message_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific message."""
        if message_id in self.message_history:
            message = self.message_history[message_id]
            return {
                'message_id': message_id,
                'status': message.status.value,
                'created_at': message.created_at.isoformat(),
                'delivered_at': message.delivered_at.isoformat() if message.delivered_at else None,
                'acknowledged_at': message.acknowledged_at.isoformat() if message.acknowledged_at else None,
                'is_expired': message.is_expired(),
                'retry_count': message.retry_count
            }
        return None

    async def get_agent_message_count(self, agent_id: str) -> int:
        """Get number of pending messages for an agent."""
        if agent_id not in self.agent_queues:
            return 0
        return await self.agent_queues[agent_id].size()

    async def cleanup_expired_messages(self) -> Dict[str, int]:
        """Clean up expired messages and update statistics."""
        cleanup_stats = {
            'expired_messages': 0,
            'cleaned_queues': 0
        }

        # Clean message queues
        for agent_id, queue in self.agent_queues.items():
            expired_count = await queue.clear_expired()
            if expired_count > 0:
                cleanup_stats['expired_messages'] += expired_count
                cleanup_stats['cleaned_queues'] += 1

        # Clean pending acknowledgments
        expired_acks = []
        for msg_id, message in self.pending_acknowledgments.items():
            if message.is_expired():
                expired_acks.append(msg_id)
                message.status = MessageStatus.EXPIRED

        for msg_id in expired_acks:
            del self.pending_acknowledgments[msg_id]

        cleanup_stats['expired_acknowledgments'] = len(expired_acks)
        self.stats['messages_expired'] += cleanup_stats['expired_messages']

        self.last_cleanup = datetime.now()

        if cleanup_stats['expired_messages'] > 0:
            self.logger.info(f"Cleanup completed: {cleanup_stats}")

        return cleanup_stats

    async def get_communication_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        # Clean up if needed
        if datetime.now() - self.last_cleanup > self.cleanup_interval:
            await self.cleanup_expired_messages()

        queue_stats = {}
        for agent_id, queue in self.agent_queues.items():
            queue_stats[agent_id] = await queue.size()

        return {
            'message_stats': self.stats.copy(),
            'queue_stats': queue_stats,
            'pending_acknowledgments': len(self.pending_acknowledgments),
            'total_history_size': len(self.message_history),
            'last_cleanup': self.last_cleanup.isoformat(),
            'active_agents': len(self.agent_queues)
        }


# Export message system instance
message_system = MessageSystem()

async def send_agent_message(source_agent: str, target_agent: str, content: str,
                           priority: str = 'normal', require_ack: bool = False,
                           **kwargs) -> Dict[str, Any]:
    """
    Convenience function for sending messages between agents.
    Compatible with Agency Swarm messaging patterns.
    """
    message = await message_system.create_message(
        source_agent, target_agent, content, priority, require_ack, **kwargs
    )
    return await message_system.send_message(message)