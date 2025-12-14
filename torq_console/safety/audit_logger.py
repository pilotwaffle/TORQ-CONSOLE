"""
Audit Logger for Tool Safety System

Comprehensive logging and auditing of all tool operations and security events
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from logging.handlers import RotatingFileHandler
import gzip
import threading

from .models import (
    AuditLog, SecurityViolation, ToolRequest, PolicyDecision,
    Decision, RiskLevel, OperationType
)

logger = logging.getLogger(__name__)


class AuditLogger:
    """Comprehensive audit logging for tool safety system"""

    def __init__(
        self,
        log_dir: Optional[str] = None,
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 10,
        compress_backups: bool = True
    ):
        """
        Initialize audit logger

        Args:
            log_dir: Directory for log files
            max_file_size: Maximum size of log files before rotation
            backup_count: Number of backup files to keep
            compress_backups: Whether to compress backup files
        """
        self.log_dir = Path(log_dir) if log_dir else Path.home() / ".torq" / "audit_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.compress_backups = compress_backups

        # Create separate loggers for different types of events
        self.audit_logger = self._setup_logger(
            "audit", "audit.log", "AUDIT"
        )
        self.security_logger = self._setup_logger(
            "security", "security.log", "SECURITY"
        )
        self.performance_logger = self._setup_logger(
            "performance", "performance.log", "PERFORMANCE"
        )
        self.error_logger = self._setup_logger(
            "error", "error.log", "ERROR"
        )

        # Thread lock for thread safety
        self._lock = threading.Lock()

        # Statistics tracking
        self.stats = {
            "total_events": 0,
            "security_violations": 0,
            "policy_denials": 0,
            "confirmations_requested": 0,
            "sandboxes_created": 0
        }

    def _setup_logger(self, name: str, filename: str, prefix: str) -> logging.Logger:
        """Setup a specific logger with rotation"""
        log_path = self.log_dir / filename

        logger_instance = logging.getLogger(f"torq_audit_{name}")
        logger_instance.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        logger_instance.handlers.clear()

        # Create rotating file handler
        handler = RotatingFileHandler(
            log_path,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )

        # Create formatter
        formatter = logging.Formatter(
            f'%(asctime)s UTC | {prefix} | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        logger_instance.addHandler(handler)

        # Ensure logger propagates to root logger for console output
        logger_instance.propagate = False

        return logger_instance

    def log_tool_request(
        self,
        request: ToolRequest,
        decision: PolicyDecision,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a tool request and its decision

        Args:
            request: Tool request that was made
            decision: Policy decision for the request
            user_id: User identifier
            session_id: Session identifier
            execution_time_ms: Execution time in milliseconds
            error_message: Error message if operation failed
            additional_data: Additional data to log

        Returns:
            Event ID for the log entry
        """
        with self._lock:
            audit_log = AuditLog(
                tool_name=request.tool_name,
                operation=request.operation,
                decision=decision.decision,
                user_id=user_id,
                session_id=session_id,
                target_path=getattr(request, 'target_path', None),
                risk_level=decision.risk_level,
                reason=decision.reason,
                execution_time_ms=execution_time_ms,
                error_message=error_message,
                additional_data=additional_data or {}
            )

            # Log to appropriate logger based on decision
            log_data = audit_log.dict()
            # Handle datetime serialization
            for key, value in log_data.items():
                if isinstance(value, datetime):
                    log_data[key] = value.isoformat()
                elif isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        if isinstance(subvalue, datetime):
                            value[subkey] = subvalue.isoformat()

            if decision.decision == Decision.DENY:
                self.audit_logger.warning(f"DENIED | {json.dumps(log_data)}")
                self.stats["policy_denials"] += 1
            elif decision.decision == Decision.REQUIRE_CONFIRMATION:
                self.audit_logger.info(f"CONFIRMATION_REQUIRED | {json.dumps(log_data)}")
                self.stats["confirmations_requested"] += 1
            else:
                self.audit_logger.info(f"ALLOWED | {json.dumps(log_data)}")

            # Log performance data
            if execution_time_ms:
                perf_data = {
                    "event_id": audit_log.event_id,
                    "tool_name": request.tool_name,
                    "operation": request.operation.value,
                    "execution_time_ms": execution_time_ms,
                    "risk_level": decision.risk_level.value
                }
                self.performance_logger.info(json.dumps(perf_data))

            # Log errors
            if error_message:
                error_data = {
                    "event_id": audit_log.event_id,
                    "tool_name": request.tool_name,
                    "operation": request.operation.value,
                    "error": error_message,
                    "risk_level": decision.risk_level.value
                }
                self.error_logger.error(json.dumps(error_data))

            self.stats["total_events"] += 1
            return audit_log.event_id

    def log_security_violation(
        self,
        violation_type: str,
        severity: RiskLevel,
        tool_name: str,
        description: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        blocked: bool = True,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a security violation

        Args:
            violation_type: Type of security violation
            severity: Severity level
            tool_name: Tool that caused the violation
            description: Description of the violation
            user_id: User identifier
            session_id: Session identifier
            ip_address: IP address
            user_agent: User agent string
            blocked: Whether the violation was blocked
            details: Additional violation details

        Returns:
            Violation ID for the log entry
        """
        with self._lock:
            violation = SecurityViolation(
                violation_type=violation_type,
                severity=severity,
                tool_name=tool_name,
                description=description,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                blocked=blocked,
                details=details or {}
            )

            # Log security violation
            violation_data = violation.dict()
            # Handle datetime serialization
            for key, value in violation_data.items():
                if isinstance(value, datetime):
                    violation_data[key] = value.isoformat()
            log_level = "CRITICAL" if severity == RiskLevel.CRITICAL else "WARNING"
            self.security_logger.log(
                getattr(logging, log_level),
                f"{log_level} | {json.dumps(violation_data)}"
            )

            self.stats["security_violations"] += 1
            return violation.violation_id

    def log_sandbox_event(
        self,
        event_type: str,
        sandbox_id: str,
        tool_name: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None
    ):
        """
        Log sandbox-related events

        Args:
            event_type: Type of sandbox event (created, destroyed, violation, etc.)
            sandbox_id: Sandbox identifier
            tool_name: Tool name
            details: Event details
            user_id: User identifier
        """
        with self._lock:
            event_data = {
                "event_type": f"sandbox_{event_type}",
                "timestamp": datetime.utcnow().isoformat(),
                "sandbox_id": sandbox_id,
                "tool_name": tool_name,
                "user_id": user_id,
                "details": details
            }

            if event_type == "created":
                self.stats["sandboxes_created"] += 1
                self.audit_logger.info(f"SANDBOX_CREATED | {json.dumps(event_data)}")
            elif event_type == "destroyed":
                self.audit_logger.info(f"SANDBOX_DESTROYED | {json.dumps(event_data)}")
            elif event_type == "violation":
                self.security_logger.warning(f"SANDBOX_VIOLATION | {json.dumps(event_data)}")
            else:
                self.audit_logger.info(f"SANDBOX_EVENT | {json.dumps(event_data)}")

    def log_configuration_change(
        self,
        component: str,
        change_type: str,
        old_value: Any,
        new_value: Any,
        user_id: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """
        Log configuration changes

        Args:
            component: Component being changed
            change_type: Type of change
            old_value: Previous value
            new_value: New value
            user_id: User making the change
            reason: Reason for the change
        """
        with self._lock:
            event_data = {
                "event_type": "configuration_change",
                "timestamp": datetime.utcnow().isoformat(),
                "component": component,
                "change_type": change_type,
                "old_value": str(old_value),
                "new_value": str(new_value),
                "user_id": user_id,
                "reason": reason
            }

            self.audit_logger.info(f"CONFIG_CHANGE | {json.dumps(event_data)}")

    def search_logs(
        self,
        event_type: Optional[str] = None,
        tool_name: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search audit logs

        Args:
            event_type: Filter by event type
            tool_name: Filter by tool name
            user_id: Filter by user ID
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results

        Returns:
            List of matching log entries
        """
        results = []

        # This is a simplified implementation
        # In production, you'd want to use a proper log search system
        try:
            audit_log_path = self.log_dir / "audit.log"
            if audit_log_path.exists():
                with open(audit_log_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            # Parse log line
                            if '|' in line:
                                log_entry = self._parse_log_line(line)
                                if self._matches_filters(log_entry, event_type, tool_name, user_id, start_time, end_time):
                                    results.append(log_entry)
                                    if len(results) >= limit:
                                        break
                        except Exception as e:
                            logger.debug(f"Error parsing log line: {e}")
                            continue

        except Exception as e:
            logger.error(f"Error searching logs: {e}")

        return results

    def _parse_log_line(self, line: str) -> Dict[str, Any]:
        """Parse a log line into structured data"""
        try:
            parts = line.strip().split(' | ', 3)
            if len(parts) >= 4:
                timestamp_str, log_type, level, data_str = parts

                # Try to parse JSON data
                try:
                    data = json.loads(data_str)
                except:
                    data = {"raw_message": data_str}

                return {
                    "timestamp": timestamp_str,
                    "log_type": log_type,
                    "level": level,
                    "data": data
                }
        except Exception:
            pass

        return {"raw_line": line.strip()}

    def _matches_filters(
        self,
        log_entry: Dict[str, Any],
        event_type: Optional[str],
        tool_name: Optional[str],
        user_id: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> bool:
        """Check if log entry matches search filters"""
        # Check event type
        if event_type and log_entry.get("log_type") != event_type:
            return False

        # Check tool name
        data = log_entry.get("data", {})
        if tool_name and data.get("tool_name") != tool_name:
            return False

        # Check user ID
        if user_id and data.get("user_id") != user_id:
            return False

        # Check time range (simplified)
        # In production, you'd want proper datetime parsing
        if start_time or end_time:
            try:
                timestamp_str = log_entry.get("timestamp", "")
                # This is simplified - proper parsing would be better
                if start_time and start_time > datetime.utcnow():
                    return False
                if end_time and end_time < datetime.utcnow():
                    return False
            except:
                pass

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit logging statistics"""
        with self._lock:
            # Calculate additional statistics
            log_files = list(self.log_dir.glob("*.log*"))
            total_log_size = sum(f.stat().st_size for f in log_files if f.exists())

            stats = self.stats.copy()
            stats.update({
                "log_directory": str(self.log_dir),
                "total_log_size_bytes": total_log_size,
                "total_log_size_mb": round(total_log_size / 1024 / 1024, 2),
                "log_files_count": len(log_files),
                "max_file_size_mb": round(self.max_file_size / 1024 / 1024, 2),
                "backup_count": self.backup_count
            })

            return stats

    def export_logs(
        self,
        output_file: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = "json"
    ) -> bool:
        """
        Export logs to a file

        Args:
            output_file: Output file path
            start_time: Start time filter
            end_time: End time filter
            format: Export format (json, csv)

        Returns:
            True if export was successful
        """
        try:
            # Get logs within time range
            logs = self.search_logs(start_time=start_time, end_time=end_time, limit=10000)

            output_path = Path(output_file)

            if format.lower() == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2, default=str)

            elif format.lower() == "csv":
                import csv

                if logs:
                    # Get all possible field names
                    fieldnames = set()
                    for log in logs:
                        fieldnames.update(log.keys())
                        fieldnames.update(log.get("data", {}).keys())

                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
                        writer.writeheader()

                        for log in logs:
                            # Flatten the data structure
                            flat_log = log.copy()
                            data = log.get("data", {})
                            for key, value in data.items():
                                flat_log[f"data_{key}"] = value
                            writer.writerow(flat_log)

            logger.info(f"Exported {len(logs)} log entries to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
            return False

    def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """
        Clean up old log files

        Args:
            days_to_keep: Number of days to keep logs

        Returns:
            Number of files cleaned up
        """
        try:
            cutoff_date = datetime.utcnow().timestamp() - (days_to_keep * 24 * 60 * 60)
            cleaned_count = 0

            for log_file in self.log_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
                    cleaned_count += 1
                    logger.info(f"Removed old log file: {log_file}")

            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            return 0