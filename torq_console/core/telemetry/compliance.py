"""
TORQ Console Telemetry Schema Compliance Checker.

Ensures ≥95% schema compliance requirement for all telemetry events.
Provides validation, reporting, and compliance monitoring.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .event import (
    TorqEvent, TorqEventType, AgentRunEvent, ToolExecutionEvent,
    ModelInteractionEvent, MemoryOperationEvent, RoutingDecisionEvent,
    SystemEvent, AgentRunEventModel
)


class ComplianceLevel(Enum):
    """Schema compliance levels."""
    EXCELLENT = "excellent"      # 100% compliance
    GOOD = "good"              # 95-99% compliance
    ADEQUATE = "adequate"      # 90-94% compliance
    NEEDS_WORK = "needs_work" # 80-89% compliance
    POOR = "poor"              # <80% compliance


class ValidationSeverity(Enum):
    """Validation issue severity."""
    ERROR = "error"      # Critical schema violation
    WARNING = "warning"  # Minor compliance issue
    INFO = "info"       # Informational note


@dataclass
class ValidationIssue:
    """A schema validation issue."""
    severity: ValidationSeverity
    field: str
    message: str
    expected_type: Optional[str] = None
    actual_value: Optional[Any] = None
    suggestion: Optional[str] = None


@dataclass
class EventValidationResult:
    """Validation result for a single event."""
    event_id: str
    event_type: TorqEventType
    is_compliant: bool
    compliance_score: float  # 0.0 - 1.0
    issues: List[ValidationIssue] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    invalid_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ComplianceReport:
    """Comprehensive compliance report."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    total_events: int = 0
    compliant_events: int = 0
    non_compliant_events: int = 0
    overall_compliance_score: float = 0.0
    compliance_level: ComplianceLevel = ComplianceLevel.POOR

    # Detailed breakdowns
    compliance_by_type: Dict[str, float] = field(default_factory=dict)
    common_issues: Dict[str, int] = field(default_factory=dict)
    field_compliance: Dict[str, float] = field(default_factory=dict)

    # Event details
    validation_results: List[EventValidationResult] = field(default_factory=list)

    # Recommendations
    recommendations: List[str] = field(default_factory=list)

    def calculate_compliance_level(self) -> ComplianceLevel:
        """Determine compliance level based on score."""
        if self.overall_compliance_score >= 1.0:
            return ComplianceLevel.EXCELLENT
        elif self.overall_compliance_score >= 0.95:
            return ComplianceLevel.GOOD
        elif self.overall_compliance_score >= 0.90:
            return ComplianceLevel.ADEQUATE
        elif self.overall_compliance_score >= 0.80:
            return ComplianceLevel.NEEDS_WORK
        else:
            return ComplianceLevel.POOR


class SchemaComplianceChecker:
    """Comprehensive schema compliance checker for TORQ telemetry events."""

    def __init__(self):
        self._required_fields = self._define_required_fields()
        self._field_types = self._define_field_types()
        self._field_validators = self._define_field_validators()
        self._event_specific_schemas = self._define_event_schemas()

    def _define_required_fields(self) -> Dict[TorqEventType, Set[str]]:
        """Define required fields for each event type."""
        return {
            TorqEventType.AGENT_RUN: {
                'event_id', 'event_type', 'timestamp', 'session_id',
                'agent_name', 'agent_type', 'status'
            },
            TorqEventType.TOOL_EXECUTION: {
                'event_id', 'event_type', 'timestamp', 'session_id',
                'tool_name', 'tool_type', 'status'
            },
            TorqEventType.MODEL_INTERACTION: {
                'event_id', 'event_type', 'timestamp', 'session_id',
                'model_provider', 'model_name', 'prompt_tokens', 'response_time_ms'
            },
            TorqEventType.MEMORY_OPERATION: {
                'event_id', 'event_type', 'timestamp', 'session_id',
                'memory_type', 'memory_backend', 'operation_type', 'operation_time_ms'
            },
            TorqEventType.ROUTING_DECISION: {
                'event_id', 'event_type', 'timestamp', 'session_id',
                'query', 'selected_agent', 'routing_strategy', 'confidence_score', 'routing_time_ms'
            },
            TorqEventType.SYSTEM_EVENT: {
                'event_id', 'event_type', 'timestamp', 'session_id',
                'component', 'operation'
            }
        }

    def _define_field_types(self) -> Dict[str, type]:
        """Define expected types for common fields."""
        return {
            'event_id': str,
            'event_type': str,
            'timestamp': str,  # ISO format
            'session_id': str,
            'run_id': str,
            'severity': str,
            'source': str,
            'version': str,
            'trace_id': str,
            'span_id': str,
            'parent_span_id': str,
            'duration_ms': int,
            'cpu_usage_percent': (int, float),
            'memory_usage_mb': (int, float),

            # Agent run specific
            'agent_name': str,
            'agent_type': str,
            'agent_version': str,
            'status': str,
            'input_tokens': int,
            'output_tokens': int,
            'total_tokens': int,
            'model_provider': str,
            'model_name': str,
            'temperature': (int, float),
            'max_tokens': int,
            'user_query': str,
            'user_intent': str,
            'confidence_score': (int, float),
            'tools_used': list,
            'tool_calls_count': int,
            'memory_reads': int,
            'memory_writes': int,
            'queue_time_ms': int,
            'processing_time_ms': int,
            'success': bool,
            'error_message': str,
            'error_type': str,
            'user_rating': int,
            'user_feedback': str,

            # Tool execution specific
            'tool_name': str,
            'tool_type': str,
            'tool_version': str,
            'execution_time_ms': int,
            'input_parameters': dict,
            'output_result': object,
            'cpu_time_ms': int,
            'memory_peak_mb': (int, float),
            'error_code': str,
            'access_level': str,
            'permissions_required': list,

            # Model interaction specific
            'model_provider': str,
            'model_name': str,
            'model_version': str,
            'prompt_tokens': int,
            'completion_tokens': int,
            'total_tokens': int,
            'response_time_ms': int,
            'ttft_ms': int,
            'tps': (int, float),
            'cost_usd': (int, float),
            'top_p': (int, float),
            'frequency_penalty': (int, float),
            'presence_penalty': (int, float),
            'content_filter_flagged': bool,

            # Memory operation specific
            'memory_type': str,
            'memory_backend': str,
            'operation_type': str,
            'key': str,
            'keys': list,
            'data_size_bytes': int,
            'cache_hit': bool,
            'cache_ttl_seconds': int,

            # Routing decision specific
            'query': str,
            'query_type': str,
            'user_intent': str,
            'selected_agent': str,
            'routing_strategy': str,
            'candidate_agents': list,
            'agent_scores': dict,
            'factors_considered': dict,
            'expected_performance': dict,
            'cost_estimate_usd': (int, float),

            # System event specific
            'component': str,
            'operation': str,
            'cpu_usage_percent': (int, float),
            'disk_usage_percent': (int, float),
            'network_io_bytes': int,
            'config_changes': dict,
            'health_status': str,
            'uptime_seconds': int
        }

    def _define_field_validators(self) -> Dict[str, callable]:
        """Define custom validators for fields."""
        return {
            'timestamp': lambda x: self._is_valid_iso_timestamp(x),
            'session_id': lambda x: isinstance(x, str) and len(x) > 0,
            'confidence_score': lambda x: isinstance(x, (int, float)) and 0.0 <= x <= 1.0,
            'temperature': lambda x: isinstance(x, (int, float)) and 0.0 <= x <= 2.0,
            'max_tokens': lambda x: isinstance(x, int) and x > 0,
            'user_rating': lambda x: isinstance(x, int) and 1 <= x <= 5,
            'response_time_ms': lambda x: isinstance(x, int) and x >= 0,
            'prompt_tokens': lambda x: isinstance(x, int) and x >= 0,
            'total_tokens': lambda x: isinstance(x, int) and x >= 0,
            'cost_usd': lambda x: isinstance(x, (int, float)) and x >= 0
        }

    def _define_event_schemas(self) -> Dict[TorqEventType, dict]:
        """Define detailed schema requirements for each event type."""
        return {
            TorqEventType.AGENT_RUN: {
                'required_data_fields': ['agent_name', 'agent_type', 'status'],
                'recommended_fields': ['confidence_score', 'tools_used', 'total_tokens'],
                'status_values': ['started', 'running', 'completed', 'failed', 'cancelled', 'timeout']
            },
            TorqEventType.TOOL_EXECUTION: {
                'required_data_fields': ['tool_name', 'tool_type', 'status'],
                'recommended_fields': ['execution_time_ms', 'success'],
                'status_values': ['started', 'completed', 'failed']
            },
            TorqEventType.MODEL_INTERACTION: {
                'required_data_fields': ['model_provider', 'model_name', 'prompt_tokens', 'response_time_ms'],
                'recommended_fields': ['total_tokens', 'completion_tokens', 'success'],
                'provider_values': ['anthropic', 'openai', 'google', 'azure', 'local', 'custom']
            },
            TorqEventType.MEMORY_OPERATION: {
                'required_data_fields': ['memory_type', 'memory_backend', 'operation_type', 'operation_time_ms'],
                'recommended_fields': ['success', 'cache_hit'],
                'operation_values': ['read', 'write', 'update', 'delete', 'search', 'clear']
            },
            TorqEventType.ROUTING_DECISION: {
                'required_data_fields': ['query', 'selected_agent', 'routing_strategy', 'confidence_score'],
                'recommended_fields': ['candidate_agents', 'routing_time_ms'],
                'strategy_values': ['intent_based', 'capability_based', 'performance_based', 'cost_based', 'manual']
            },
            TorqEventType.SYSTEM_EVENT: {
                'required_data_fields': ['component', 'operation'],
                'recommended_fields': ['success', 'cpu_usage_percent', 'memory_usage_mb']
            }
        }

    def validate_event(self, event: TorqEvent) -> EventValidationResult:
        """Validate a single telemetry event."""
        issues = []
        missing_fields = []
        invalid_fields = []
        warnings = []

        # Check required fields
        required_fields = self._required_fields.get(event.event_type, set())

        # Base required fields
        base_required = {'event_id', 'event_type', 'timestamp', 'session_id'}
        for field in base_required:
            if not hasattr(event, field) or getattr(event, field) is None:
                missing_fields.append(field)
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field=field,
                    message=f"Missing required field",
                    suggestion=f"Add '{field}' field to event"
                ))

        # Event-specific required fields in data
        schema = self._event_specific_schemas.get(event.event_type, {})
        required_data_fields = schema.get('required_data_fields', [])

        for field in required_data_fields:
            if field not in event.data or event.data[field] is None:
                missing_fields.append(f"data.{field}")
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field=f"data.{field}",
                    message=f"Missing required data field",
                    suggestion=f"Add '{field}' to event data"
                ))

        # Check field types
        for field_name, field_value in self._get_all_fields(event).items():
            if field_value is not None:
                expected_type = self._field_types.get(field_name)
                if expected_type and not isinstance(field_value, expected_type):
                    invalid_fields.append(field_name)
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field=field_name,
                        message=f"Invalid field type",
                        expected_type=str(expected_type),
                        actual_value=type(field_value).__name__,
                        suggestion=f"Convert {field_name} to {expected_type}"
                    ))

        # Custom field validation
        for field_name, field_value in self._get_all_fields(event).items():
            if field_value is not None and field_name in self._field_validators:
                validator = self._field_validators[field_name]
                try:
                    if not validator(field_value):
                        invalid_fields.append(field_name)
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            field=field_name,
                            message=f"Field validation failed",
                            actual_value=field_value,
                            suggestion=f"Check {field_name} value"
                        ))
                except Exception as e:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field=field_name,
                        message=f"Validation error: {str(e)}",
                        actual_value=field_value
                    ))

        # Check recommended fields (warnings only)
        recommended_fields = schema.get('recommended_fields', [])
        for field in recommended_fields:
            if field not in event.data or event.data[field] is None:
                warnings.append(f"Missing recommended field: {field}")

        # Validate enum values
        self._validate_enum_values(event, schema, issues)

        # Calculate compliance score
        total_checks = len(required_fields) + len(required_data_fields) + len(recommended_fields)
        passed_checks = total_checks - len(issues) - len(warnings) * 0.5  # Warnings count as half
        compliance_score = max(0.0, min(1.0, passed_checks / total_checks))

        is_compliant = compliance_score >= 0.95 and len(missing_fields) == 0

        return EventValidationResult(
            event_id=event.event_id,
            event_type=event.event_type,
            is_compliant=is_compliant,
            compliance_score=compliance_score,
            issues=issues,
            missing_fields=missing_fields,
            invalid_fields=invalid_fields,
            warnings=warnings
        )

    def _get_all_fields(self, event: TorqEvent) -> Dict[str, Any]:
        """Get all fields from an event as a flat dictionary."""
        fields = {}

        # Base event fields
        for attr in dir(event):
            if not attr.startswith('_') and not callable(getattr(event, attr)):
                value = getattr(event, attr)
                if not isinstance(value, (list, dict, datetime)) and value is not None:
                    fields[attr] = value

        # Data fields
        if hasattr(event, 'data') and isinstance(event.data, dict):
            for key, value in event.data.items():
                if not isinstance(value, (dict, list)):
                    fields[key] = value

        return fields

    def _validate_enum_values(self, event: TorqEvent, schema: Dict[str, Any], issues: List[ValidationIssue]):
        """Validate enum values in event data."""
        # Validate status values
        if event.event_type == TorqEventType.AGENT_RUN and 'status' in event.data:
            valid_statuses = schema.get('status_values', [])
            if valid_statuses and event.data['status'] not in valid_statuses:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="data.status",
                    message=f"Invalid status value",
                    actual_value=event.data['status'],
                    suggestion=f"Use one of: {valid_statuses}"
                ))

        # Validate provider values
        if event.event_type == TorqEventType.MODEL_INTERACTION and 'model_provider' in event.data:
            valid_providers = schema.get('provider_values', [])
            if valid_providers and event.data['model_provider'] not in valid_providers:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="data.model_provider",
                    message=f"Invalid model provider",
                    actual_value=event.data['model_provider'],
                    suggestion=f"Use one of: {valid_providers}"
                ))

    async def validate_events_batch(self, events: List[TorqEvent]) -> List[EventValidationResult]:
        """Validate a batch of events."""
        results = []
        for event in events:
            result = self.validate_event(event)
            results.append(result)
        return results

    async def generate_compliance_report(self, events: List[TorqEvent]) -> ComplianceReport:
        """Generate a comprehensive compliance report."""
        validation_results = await self.validate_events_batch(events)

        total_events = len(events)
        compliant_events = sum(1 for r in validation_results if r.is_compliant)
        non_compliant_events = total_events - compliant_events

        # Calculate overall compliance score
        overall_score = sum(r.compliance_score for r in validation_results) / total_events if total_events > 0 else 0.0

        # Calculate compliance by type
        compliance_by_type = {}
        for result in validation_results:
            event_type = result.event_type.value
            if event_type not in compliance_by_type:
                compliance_by_type[event_type] = []
            compliance_by_type[event_type].append(result.compliance_score)

        for event_type, scores in compliance_by_type.items():
            compliance_by_type[event_type] = sum(scores) / len(scores)

        # Track common issues
        common_issues = {}
        field_compliance = {}
        for result in validation_results:
            for issue in result.issues:
                issue_key = f"{issue.field}:{issue.message[:50]}"
                common_issues[issue_key] = common_issues.get(issue_key, 0) + 1

            # Track field-level compliance
            for missing_field in result.missing_fields:
                field_compliance[missing_field] = field_compliance.get(missing_field, 0) + 1

        # Generate recommendations
        recommendations = self._generate_recommendations(common_issues, field_compliance, overall_score)

        report = ComplianceReport(
            total_events=total_events,
            compliant_events=compliant_events,
            non_compliant_events=non_compliant_events,
            overall_compliance_score=overall_score,
            compliance_by_type=compliance_by_type,
            common_issues=dict(sorted(common_issues.items(), key=lambda x: x[1], reverse=True)[:10]),
            field_compliance=field_compliance,
            validation_results=validation_results,
            recommendations=recommendations
        )

        report.compliance_level = report.calculate_compliance_level()
        return report

    def _generate_recommendations(
        self,
        common_issues: Dict[str, int],
        field_compliance: Dict[str, int],
        overall_score: float
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []

        if overall_score < 0.95:
            recommendations.append("Overall compliance is below 95%. Focus on fixing missing required fields.")

        # Most common missing fields
        if field_compliance:
            most_missing = max(field_compliance, key=field_compliance.get)
            recommendations.append(f"Most commonly missing field: {most_missing} ({field_compliance[most_missing]} events)")

        # Most common issues
        if common_issues:
            most_common_issue = max(common_issues, key=common_issues.get)
            recommendations.append(f"Most common issue: {most_common_issue} ({common_issues[most_common_issue]} occurrences)")

        # Specific recommendations based on score
        if overall_score < 0.80:
            recommendations.extend([
                "Critical: Implement automated validation in event creation",
                "Review event generation pipeline for missing fields",
                "Add unit tests for event schema compliance"
            ])
        elif overall_score < 0.90:
            recommendations.extend([
                "Add validation warnings to development environment",
                "Document required fields for event types",
                "Consider adding field validation to event creation helpers"
            ])
        elif overall_score < 0.95:
            recommendations.extend([
                "Focus on adding recommended fields to improve data quality",
                "Review and enhance existing validation logic",
                "Consider implementing schema versioning"
            ])

        return recommendations

    def _is_valid_iso_timestamp(self, timestamp_str: str) -> bool:
        """Check if timestamp is valid ISO format."""
        try:
            if isinstance(timestamp_str, datetime):
                return True
            datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return True
        except (ValueError, AttributeError):
            return False


# Global compliance checker instance
_global_compliance_checker: Optional[SchemaComplianceChecker] = None


def get_schema_compliance_checker() -> SchemaComplianceChecker:
    """Get the global schema compliance checker instance."""
    global _global_compliance_checker
    if _global_compliance_checker is None:
        _global_compliance_checker = SchemaComplianceChecker()
    return _global_compliance_checker


# Convenience functions
async def check_schema_compliance(events: List[TorqEvent]) -> ComplianceReport:
    """Check schema compliance for a list of events."""
    checker = get_schema_compliance_checker()
    return await checker.generate_compliance_report(events)


async def validate_event_schema(event: TorqEvent) -> EventValidationResult:
    """Validate a single event's schema compliance."""
    checker = get_schema_compliance_checker()
    return checker.validate_event(event)


# Decorator for automatic compliance checking
def ensure_compliance(checker: Optional[SchemaComplianceChecker] = None):
    """Decorator to ensure events are compliant before emission."""
    compliance_checker = checker or get_schema_compliance_checker()

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # If result is an event or list of events, validate it
            if isinstance(result, TorqEvent):
                validation = compliance_checker.validate_event(result)
                if not validation.is_compliant:
                    logging.warning(f"Event {result.event_id} is not compliant: {validation.issues}")
            elif isinstance(result, list) and result and isinstance(result[0], TorqEvent):
                for event in result:
                    validation = compliance_checker.validate_event(event)
                    if not validation.is_compliant:
                        logging.warning(f"Event {event.event_id} is not compliant: {validation.issues}")

            return result

        return async_wrapper

    return decorator