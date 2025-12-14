"""
TORQ Console Telemetry Collector.

Centralized collection and processing of telemetry events
with performance-optimized batching and async processing.
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from dataclasses import dataclass, field, asdict
from pathlib import Path
import aiofiles
import sqlite3
from contextlib import asynccontextmanager

from .event import TorqEvent, TorqEventType
from .trace import TraceManager, get_trace_manager


@dataclass
class TelemetryConfig:
    """Configuration for telemetry collection."""
    # Collection settings
    enabled: bool = True
    batch_size: int = 100
    flush_interval_seconds: float = 5.0
    max_queue_size: int = 10000

    # Storage settings
    storage_type: str = "sqlite"  # sqlite, file, memory
    storage_path: Optional[Path] = None
    compression: bool = True

    # Retention settings
    retention_days: int = 30
    max_events_per_hour: int = 10000

    # Performance settings
    async_flush: bool = True
    max_flush_workers: int = 4
    sampling_rate: float = 1.0  # 1.0 = 100% sampling

    # Filtering settings
    event_types: List[TorqEventType] = field(default_factory=list)  # Empty = all
    min_severity: Optional[str] = None

    # Security settings
    pii_filtering: bool = True
    sanitize_fields: List[str] = field(default_factory=lambda: [
        'user_query', 'user_feedback', 'error_message', 'query'
    ])

    def __post_init__(self):
        """Initialize default storage path."""
        if self.storage_type == "sqlite" and not self.storage_path:
            self.storage_path = Path.home() / ".torq_console" / "telemetry.db"


class TelemetryStorage:
    """Abstract base class for telemetry storage backends."""

    async def store_events(self, events: List[TorqEvent]) -> bool:
        """Store a batch of events."""
        raise NotImplementedError

    async def get_events(
        self,
        limit: int = 1000,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve events with optional filtering."""
        raise NotImplementedError

    async def get_events_by_run_id(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all events for a specific run ID."""
        raise NotImplementedError

    async def cleanup_old_events(self, cutoff_date: datetime) -> int:
        """Clean up events older than cutoff date. Returns number of events deleted."""
        raise NotImplementedError

    async def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""
        raise NotImplementedError


class SQLiteTelemetryStorage(TelemetryStorage):
    """SQLite-based telemetry storage."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._lock = asyncio.Lock()
        self._init_database()

    def _init_database(self):
        """Initialize the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                session_id TEXT NOT NULL,
                run_id TEXT,
                severity TEXT,
                source TEXT,
                version TEXT,
                trace_id TEXT,
                span_id TEXT,
                parent_span_id TEXT,
                data TEXT,
                tags TEXT,
                context TEXT,
                duration_ms INTEGER,
                cpu_usage_percent REAL,
                memory_usage_mb REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create agent runs table (for specialized queries)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_runs (
                run_id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                status TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_ms INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                success BOOLEAN,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_session_id ON events(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_run_id ON events(run_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_runs_run_id ON agent_runs(run_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_runs_start_time ON agent_runs(start_time)')

        conn.commit()
        conn.close()

    async def store_events(self, events: List[TorqEvent]) -> bool:
        """Store a batch of events."""
        async with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                for event in events:
                    event_dict = event.to_dict()

                    # Store main event
                    cursor.execute('''
                        INSERT OR REPLACE INTO events (
                            id, event_type, timestamp, session_id, run_id, severity,
                            source, version, trace_id, span_id, parent_span_id,
                            data, tags, context, duration_ms, cpu_usage_percent, memory_usage_mb
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event_dict['event_id'],
                        event_dict['event_type'],
                        event_dict['timestamp'],
                        event_dict['session_id'],
                        event_dict['run_id'],
                        event_dict['severity'],
                        event_dict['source'],
                        event_dict['version'],
                        event_dict['trace_id'],
                        event_dict['span_id'],
                        event_dict['parent_span_id'],
                        json.dumps(event_dict['data']),
                        json.dumps(event_dict['tags']),
                        json.dumps(event_dict['context']),
                        event_dict['duration_ms'],
                        event_dict['cpu_usage_percent'],
                        event_dict['memory_usage_mb']
                    ))

                    # Store agent run specific data
                    if event.event_type == TorqEventType.AGENT_RUN:
                        self._store_agent_run(cursor, event)

                conn.commit()
                conn.close()
                return True

            except Exception as e:
                logging.error(f"Failed to store events: {e}")
                return False

    def _store_agent_run(self, cursor: sqlite3.Cursor, event: TorqEvent):
        """Store agent run specific data."""
        data = event.data
        cursor.execute('''
            INSERT OR REPLACE INTO agent_runs (
                run_id, agent_name, agent_type, status, start_time,
                end_time, duration_ms, input_tokens, output_tokens,
                total_tokens, success, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.run_id,
            data.get('agent_name', ''),
            data.get('agent_type', ''),
            data.get('status', ''),
            event.timestamp.isoformat(),
            event.timestamp.isoformat() if event.duration_ms else None,
            event.duration_ms,
            data.get('input_tokens'),
            data.get('output_tokens'),
            data.get('total_tokens'),
            data.get('success', True),
            data.get('error_message')
        ))

    async def get_events(
        self,
        limit: int = 1000,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve events with optional filtering."""
        query = "SELECT * FROM events"
        params = []

        if filters:
            conditions = []
            if 'event_type' in filters:
                conditions.append("event_type = ?")
                params.append(filters['event_type'])
            if 'session_id' in filters:
                conditions.append("session_id = ?")
                params.append(filters['session_id'])
            if 'run_id' in filters:
                conditions.append("run_id = ?")
                params.append(filters['run_id'])
            if 'start_time' in filters:
                conditions.append("timestamp >= ?")
                params.append(filters['start_time'])
            if 'end_time' in filters:
                conditions.append("timestamp <= ?")
                params.append(filters['end_time'])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        columns = [
            'id', 'event_type', 'timestamp', 'session_id', 'run_id',
            'severity', 'source', 'version', 'trace_id', 'span_id',
            'parent_span_id', 'data', 'tags', 'context',
            'duration_ms', 'cpu_usage_percent', 'memory_usage_mb', 'created_at'
        ]

        events = []
        for row in rows:
            event_dict = dict(zip(columns, row))
            # Parse JSON fields
            for field in ['data', 'tags', 'context']:
                if event_dict[field]:
                    try:
                        event_dict[field] = json.loads(event_dict[field])
                    except:
                        pass
            events.append(event_dict)

        return events

    async def get_events_by_run_id(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all events for a specific run ID."""
        return await self.get_events(filters={'run_id': run_id})

    async def cleanup_old_events(self, cutoff_date: datetime) -> int:
        """Clean up events older than cutoff date."""
        async with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cutoff_str = cutoff_date.isoformat()

                # Delete old events
                cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff_str,))
                events_deleted = cursor.rowcount

                # Delete old agent runs
                cursor.execute("DELETE FROM agent_runs WHERE start_time < ?", (cutoff_str,))
                runs_deleted = cursor.rowcount

                conn.commit()
                conn.close()

                # VACUUM to reclaim space
                conn = sqlite3.connect(self.db_path)
                conn.execute("VACUUM")
                conn.close()

                return events_deleted + runs_deleted

            except Exception as e:
                logging.error(f"Failed to cleanup old events: {e}")
                return 0

    async def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Event statistics
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]

        cursor.execute("""
            SELECT event_type, COUNT(*)
            FROM events
            GROUP BY event_type
        """)
        events_by_type = dict(cursor.fetchall())

        # Agent run statistics
        cursor.execute("SELECT COUNT(*) FROM agent_runs")
        total_runs = cursor.fetchone()[0]

        cursor.execute("""
            SELECT status, COUNT(*)
            FROM agent_runs
            GROUP BY status
        """)
        runs_by_status = dict(cursor.fetchall())

        # Database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size_bytes = cursor.fetchone()[0]

        conn.close()

        return {
            'total_events': total_events,
            'events_by_type': events_by_type,
            'total_agent_runs': total_runs,
            'agent_runs_by_status': runs_by_status,
            'database_size_bytes': db_size_bytes,
            'database_size_mb': round(db_size_bytes / (1024 * 1024), 2)
        }


class FileTelemetryStorage(TelemetryStorage):
    """File-based telemetry storage."""

    def __init__(self, file_path: Path, compression: bool = True):
        self.file_path = file_path
        self.compression = compression
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    async def store_events(self, events: List[TorqEvent]) -> bool:
        """Store events to file."""
        try:
            async with aiofiles.open(self.file_path, 'a') as f:
                for event in events:
                    line = json.dumps(event.to_dict()) + '\n'
                    await f.write(line)
            return True
        except Exception as e:
            logging.error(f"Failed to store events to file: {e}")
            return False

    async def get_events(
        self,
        limit: int = 1000,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Read events from file."""
        events = []
        try:
            if not self.file_path.exists():
                return events

            async with aiofiles.open(self.file_path, 'r') as f:
                async for line in f:
                    if line.strip():
                        try:
                            event = json.loads(line.strip())
                            events.append(event)
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logging.error(f"Failed to read events from file: {e}")

        # Apply filters
        if filters:
            filtered_events = []
            for event in events:
                match = True
                for key, value in filters.items():
                    if event.get(key) != value:
                        match = False
                        break
                if match:
                    filtered_events.append(event)
            events = filtered_events

        # Apply pagination
        return events[offset:offset + limit]

    async def get_events_by_run_id(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all events for a specific run ID."""
        return await self.get_events(filters={'run_id': run_id})

    async def cleanup_old_events(self, cutoff_date: datetime) -> int:
        """Clean up old events (not implemented for file storage)."""
        return 0

    async def get_statistics(self) -> Dict[str, Any]:
        """Get file statistics."""
        try:
            if self.file_path.exists():
                size_bytes = self.file_path.stat().st_size
                line_count = 0
                async with aiofiles.open(self.file_path, 'r') as f:
                    async for _ in f:
                        line_count += 1
                return {
                    'file_size_bytes': size_bytes,
                    'event_count': line_count
                }
        except Exception as e:
            logging.error(f"Failed to get file statistics: {e}")

        return {'file_size_bytes': 0, 'event_count': 0}


class MemoryTelemetryStorage(TelemetryStorage):
    """In-memory telemetry storage (for testing)."""

    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self._events: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def store_events(self, events: List[TorqEvent]) -> bool:
        """Store events in memory."""
        async with self._lock:
            try:
                for event in events:
                    self._events.append(event.to_dict())

                # Maintain max size
                if len(self._events) > self.max_events:
                    self._events = self._events[-self.max_events:]

                return True
            except Exception as e:
                logging.error(f"Failed to store events in memory: {e}")
                return False

    async def get_events(
        self,
        limit: int = 1000,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve events from memory."""
        async with self._lock:
            events = self._events.copy()

            # Apply filters
            if filters:
                filtered_events = []
                for event in events:
                    match = True
                    for key, value in filters.items():
                        if event.get(key) != value:
                            match = False
                            break
                    if match:
                        filtered_events.append(event)
                events = filtered_events

            return events[offset:offset + limit]

    async def get_events_by_run_id(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all events for a specific run ID."""
        return await self.get_events(filters={'run_id': run_id})

    async def cleanup_old_events(self, cutoff_date: datetime) -> int:
        """Clean up old events."""
        async with self._lock:
            original_count = len(self._events)
            cutoff_str = cutoff_date.isoformat()

            self._events = [
                event for event in self._events
                if event.get('timestamp', '') >= cutoff_str
            ]

            return original_count - len(self._events)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics."""
        async with self._lock:
            return {
                'event_count': len(self._events),
                'max_events': self.max_events,
                'memory_usage_estimate': len(json.dumps(self._events))
            }


class TelemetryCollector:
    """Centralized telemetry collection system."""

    def __init__(self, config: TelemetryConfig, trace_manager: Optional[TraceManager] = None):
        self.config = config
        self.trace_manager = trace_manager or get_trace_manager()
        self.storage = self._create_storage()

        # Event processing
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=config.max_queue_size)
        self._flush_task: Optional[asyncio.Task] = None
        self._processing = False
        self._shutdown_event = asyncio.Event()

        # Statistics
        self._stats = {
            'events_collected': 0,
            'events_stored': 0,
            'events_dropped': 0,
            'storage_errors': 0,
            'last_flush_time': None,
            'start_time': datetime.utcnow()
        }

        # PII filtering
        self._pii_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        ]

    def _create_storage(self) -> TelemetryStorage:
        """Create storage backend based on configuration."""
        if self.config.storage_type == "sqlite":
            return SQLiteTelemetryStorage(self.config.storage_path)
        elif self.config.storage_type == "file":
            return FileTelemetryStorage(self.config.storage_path, self.config.compression)
        elif self.config.storage_type == "memory":
            return MemoryTelemetryStorage()
        else:
            raise ValueError(f"Unknown storage type: {self.config.storage_type}")

    async def start(self):
        """Start the telemetry collector."""
        if self._processing:
            return

        self._processing = True
        self._shutdown_event.clear()

        # Start flush task
        self._flush_task = asyncio.create_task(self._flush_loop())

        logging.info("Telemetry collector started")

    async def stop(self):
        """Stop the telemetry collector."""
        if not self._processing:
            return

        self._processing = False
        self._shutdown_event.set()

        # Cancel flush task
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Flush remaining events
        await self._flush_events()

        logging.info("Telemetry collector stopped")

    async def collect_event(self, event: TorqEvent) -> bool:
        """Collect a single telemetry event."""
        if not self.config.enabled:
            return True

        # Apply sampling
        if self.config.sampling_rate < 1.0:
            import random
            if random.random() > self.config.sampling_rate:
                return True

        # Apply filters
        if self.config.event_types and event.event_type not in self.config.event_types:
            return True

        if self.config.min_severity and event.severity.value < self.config.min_severity:
            return True

        # Sanitize PII
        if self.config.pii_filtering:
            event = self._sanitize_event(event)

        try:
            await self._event_queue.put(event)
            self._stats['events_collected'] += 1
            return True
        except asyncio.QueueFull:
            self._stats['events_dropped'] += 1
            logging.warning("Telemetry queue full, dropping event")
            return False

    async def collect_events(self, events: List[TorqEvent]) -> bool:
        """Collect multiple telemetry events."""
        success = True
        for event in events:
            if not await self.collect_event(event):
                success = False
        return success

    async def get_events_by_run_id(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all events for a specific run ID."""
        return await self.storage.get_events_by_run_id(run_id)

    async def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """Get a summary of a specific run."""
        events = await self.get_events_by_run_id(run_id)

        if not events:
            return {}

        # Extract key information
        agent_events = [e for e in events if e['event_type'] == TorqEventType.AGENT_RUN.value]
        tool_events = [e for e in events if e['event_type'] == TorqEventType.TOOL_EXECUTION.value]
        model_events = [e for e in events if e['event_type'] == TorqEventType.MODEL_INTERACTION.value]

        summary = {
            'run_id': run_id,
            'event_count': len(events),
            'agent_events': len(agent_events),
            'tool_events': len(tool_events),
            'model_events': len(model_events),
            'start_time': events[0]['timestamp'] if events else None,
            'end_time': events[-1]['timestamp'] if events else None,
        }

        # Add agent run details
        if agent_events:
            agent_data = agent_events[0]['data']
            summary.update({
                'agent_name': agent_data.get('agent_name'),
                'agent_type': agent_data.get('agent_type'),
                'status': agent_data.get('status'),
                'success': agent_data.get('success', True),
                'total_tokens': agent_data.get('total_tokens', 0),
                'tools_used': agent_data.get('tools_used', [])
            })

        # Add performance metrics
        durations = [e.get('duration_ms') for e in events if e.get('duration_ms')]
        if durations:
            summary.update({
                'avg_duration_ms': sum(durations) / len(durations),
                'max_duration_ms': max(durations),
                'total_duration_ms': sum(durations)
            })

        return summary

    async def _sanitize_event(self, event: TorqEvent) -> TorqEvent:
        """Sanitize PII from event data."""
        import re

        # Create a copy to avoid modifying the original
        sanitized_data = event.data.copy()
        sanitized_context = event.context.copy()

        # Sanitize specified fields
        for field in self.config.sanitize_fields:
            if field in sanitized_data and isinstance(sanitized_data[field], str):
                for pattern in self._pii_patterns:
                    sanitized_data[field] = re.sub(pattern, '[REDACTED]', sanitized_data[field], flags=re.IGNORECASE)

            if field in sanitized_context and isinstance(sanitized_context[field], str):
                for pattern in self._pii_patterns:
                    sanitized_context[field] = re.sub(pattern, '[REDACTED]', sanitized_context[field], flags=re.IGNORECASE)

        # Create new event with sanitized data
        return type(event)(
            event_id=event.event_id,
            event_type=event.event_type,
            timestamp=event.timestamp,
            session_id=event.session_id,
            run_id=event.run_id,
            severity=event.severity,
            source=event.source,
            version=event.version,
            trace_id=event.trace_id,
            span_id=event.span_id,
            parent_span_id=event.parent_span_id,
            data=sanitized_data,
            tags=event.tags,
            context=sanitized_context,
            duration_ms=event.duration_ms,
            cpu_usage_percent=event.cpu_usage_percent,
            memory_usage_mb=event.memory_usage_mb
        )

    async def _flush_loop(self):
        """Background task to flush events periodically."""
        while self._processing:
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.config.flush_interval_seconds
                )
                break  # Shutdown event was set
            except asyncio.TimeoutError:
                # Flush interval reached
                await self._flush_events()

    async def _flush_events(self):
        """Flush queued events to storage."""
        if self._event_queue.empty():
            return

        events = []
        while not self._event_queue.empty():
            try:
                event = self._event_queue.get_nowait()
                events.append(event)
            except asyncio.QueueEmpty:
                break

        if not events:
            return

        try:
            success = await self.storage.store_events(events)
            if success:
                self._stats['events_stored'] += len(events)
                self._stats['last_flush_time'] = datetime.utcnow()
            else:
                self._stats['storage_errors'] += 1
                logging.error(f"Failed to store {len(events)} events")

        except Exception as e:
            self._stats['storage_errors'] += 1
            logging.error(f"Error flushing events: {e}")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics."""
        runtime = (datetime.utcnow() - self._stats['start_time']).total_seconds()
        storage_stats = await self.storage.get_statistics()

        return {
            **self._stats,
            'runtime_seconds': runtime,
            'events_per_second': self._stats['events_collected'] / runtime if runtime > 0 else 0,
            'queue_size': self._event_queue.qsize(),
            'storage': storage_stats,
            'config': {
                'enabled': self.config.enabled,
                'batch_size': self.config.batch_size,
                'flush_interval_seconds': self.config.flush_interval_seconds,
                'storage_type': self.config.storage_type
            }
        }


# Global collector instance
_global_collector: Optional[TelemetryCollector] = None


def get_telemetry_collector(config: Optional[TelemetryConfig] = None) -> TelemetryCollector:
    """Get the global telemetry collector instance."""
    global _global_collector
    if _global_collector is None:
        _global_collector = TelemetryCollector(config or TelemetryConfig())
    return _global_collector


# Context manager for telemetry collection
@asynccontextmanager
async def telemetry_scope(config: Optional[TelemetryConfig] = None):
    """Context manager for telemetry collection with automatic cleanup."""
    collector = get_telemetry_collector(config)
    await collector.start()
    try:
        yield collector
    finally:
        await collector.stop()