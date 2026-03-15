"""TORQ Layer 14 - Governance Audit Ledger

This module implements an immutable audit ledger for all
governance decisions and evaluations.
"""

from collections import deque
from datetime import datetime
from typing import TYPE_CHECKING

from .models import (
    GovernanceDecisionPacket,
    GovernanceResult,
    GovernanceViolation,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# AUDIT RECORD MODELS
# =============================================================================


class GovernanceDecision:
    """A governance decision record for the audit ledger.

    Represents a complete record of a governance decision,
    including the proposal, evaluation, and outcome.
    """

    def __init__(
        self,
        decision_id: str,
        packet: GovernanceDecisionPacket,
        result: GovernanceResult,
    ):
        """Initialize a governance decision record.

        Args:
            decision_id: Decision identifier
            packet: Original decision packet
            result: Governance evaluation result
        """
        self.decision_id = decision_id
        self.packet = packet
        self.result = result
        self.timestamp = datetime.utcnow()

    @property
    def was_executed(self) -> bool:
        """Check if decision was authorized for execution."""
        return self.result.execution_authorized

    @property
    def had_violations(self) -> bool:
        """Check if decision had any violations."""
        return (
            len(self.result.blocking_violations) > 0
            or len(self.result.warning_violations) > 0
        )


class GovernanceRecord:
    """An entry in the governance audit ledger.

    Represents a single auditable governance event.
    """

    def __init__(
        self,
        record_id: str,
        decision_id: str,
        timestamp: datetime,
        agent_id: str,
        legitimacy_score: float,
        violations: list[GovernanceViolation],
        execution_authorized: bool,
        event_type: str = "decision",
    ):
        """Initialize a governance record.

        Args:
            record_id: Unique record identifier
            decision_id: Associated decision ID
            timestamp: When the record was created
            agent_id: Agent responsible for the decision
            legitimacy_score: Legitimacy score of the decision
            violations: Any violations found
            execution_authorized: Whether execution was authorized
            event_type: Type of event (decision, rule_change, etc.)
        """
        self.record_id = record_id
        self.decision_id = decision_id
        self.timestamp = timestamp
        self.agent_id = agent_id
        self.legitimacy_score = legitimacy_score
        self.violations = violations
        self.execution_authorized = execution_authorized
        self.event_type = event_type

    def to_dict(self) -> dict:
        """Convert record to dictionary.

        Returns:
            Dictionary representation of the record
        """
        return {
            "record_id": self.record_id,
            "decision_id": self.decision_id,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "legitimacy_score": self.legitimacy_score,
            "violations": [
                {
                    "violation_id": v.violation_id,
                    "rule_type": v.rule_type.value,
                    "severity": v.severity,
                    "description": v.description,
                }
                for v in self.violations
            ],
            "execution_authorized": self.execution_authorized,
            "event_type": self.event_type,
        }


# =============================================================================
# GOVERNANCE AUDIT LEDGER
# =============================================================================


class GovernanceAuditLedger:
    """Immutable audit ledger for governance events.

    This ledger maintains a complete, append-only record of all
    governance decisions and evaluations for system auditability.

    The ledger provides:
    - Complete decision history
    - Violation tracking
    - Agent accountability
    - System transparency
    """

    def __init__(self, max_size: int = 10000):
        """Initialize the governance audit ledger.

        Args:
            max_size: Maximum number of records to keep (0 = unlimited)
        """
        self.max_size = max_size
        self.records: deque[GovernanceRecord] = deque(maxlen=max_size if max_size > 0 else None)
        self.decisions: dict[str, GovernanceDecision] = {}
        self.record_counter = 0

    async def record_decision(
        self,
        packet: GovernanceDecisionPacket,
        result: GovernanceResult,
    ) -> str:
        """Record a governance decision in the ledger.

        Args:
            packet: Decision packet
            result: Governance evaluation result

        Returns:
            Record ID
        """
        # Create decision record
        decision = GovernanceDecision(
            decision_id=packet.decision_id,
            packet=packet,
            result=result,
        )
        self.decisions[packet.decision_id] = decision

        # Create audit record
        self.record_counter += 1
        record_id = f"gov_record_{self.record_counter:06d}"

        record = GovernanceRecord(
            record_id=record_id,
            decision_id=packet.decision_id,
            timestamp=datetime.utcnow(),
            agent_id=packet.proposing_agent_id,
            legitimacy_score=result.legitimacy_score,
            violations=(
                result.blocking_violations + result.warning_violations
            ),
            execution_authorized=result.execution_authorized,
            event_type="decision",
        )

        self.records.append(record)
        return record_id

    async def record_rule_change(
        self,
        rule_id: str,
        change_type: str,
        agent_id: str,
        description: str,
    ) -> str:
        """Record a governance rule change.

        Args:
            rule_id: Rule that was changed
            change_type: Type of change (add, modify, remove)
            agent_id: Agent making the change
            description: Description of the change

        Returns:
            Record ID
        """
        self.record_counter += 1
        record_id = f"gov_rule_change_{self.record_counter:06d}"

        # For rule changes, create a special record
        record = GovernanceRecord(
            record_id=record_id,
            decision_id=f"rule_change_{rule_id}",
            timestamp=datetime.utcnow(),
            agent_id=agent_id,
            legitimacy_score=1.0,  # Rule changes are assumed legitimate if authorized
            violations=[],
            execution_authorized=True,
            event_type=f"rule_{change_type}",
        )

        self.records.append(record)
        return record_id

    async def record_authority_change(
        self,
        target_agent_id: str,
        change_type: str,
        authorizing_agent_id: str,
        old_authority: str | None = None,
        new_authority: str | None = None,
    ) -> str:
        """Record an authority level change.

        Args:
            target_agent_id: Agent whose authority is changing
            change_type: Type of change (grant, revoke, modify)
            authorizing_agent_id: Agent authorizing the change
            old_authority: Previous authority level
            new_authority: New authority level

        Returns:
            Record ID
        """
        self.record_counter += 1
        record_id = f"gov_auth_change_{self.record_counter:06d}"

        record = GovernanceRecord(
            record_id=record_id,
            decision_id=f"auth_change_{target_agent_id}",
            timestamp=datetime.utcnow(),
            agent_id=authorizing_agent_id,
            legitimacy_score=1.0,
            violations=[],
            execution_authorized=True,
            event_type=f"authority_{change_type}",
        )

        self.records.append(record)
        return record_id

    def get_decision(self, decision_id: str) -> GovernanceDecision | None:
        """Get a decision record by ID.

        Args:
            decision_id: Decision identifier

        Returns:
            GovernanceDecision if found, None otherwise
        """
        return self.decisions.get(decision_id)

    def get_records(
        self,
        limit: int = 100,
        agent_id: str | None = None,
        event_type: str | None = None,
    ) -> list[GovernanceRecord]:
        """Get records from the ledger.

        Args:
            limit: Maximum number of records to return
            agent_id: Filter by agent ID
            event_type: Filter by event type

        Returns:
            List of GovernanceRecord
        """
        records = list(self.records)

        # Apply filters
        if agent_id:
            records = [r for r in records if r.agent_id == agent_id]

        if event_type:
            records = [r for r in records if r.event_type == event_type]

        # Sort by timestamp (most recent first) and limit
        records = sorted(records, key=lambda r: r.timestamp, reverse=True)
        return records[:limit]

    def get_violations(
        self,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get violations from the ledger.

        Args:
            severity: Filter by severity level
            limit: Maximum number of violations to return

        Returns:
            List of violation dictionaries
        """
        violations = []

        for record in self.records:
            for violation in record.violations:
                if severity is None or violation.severity == severity:
                    violations.append({
                        "record_id": record.record_id,
                        "decision_id": record.decision_id,
                        "timestamp": record.timestamp.isoformat(),
                        "agent_id": record.agent_id,
                        "violation": violation.to_dict() if hasattr(violation, "to_dict") else {
                            "violation_id": violation.violation_id,
                            "rule_type": violation.rule_type.value,
                            "severity": violation.severity,
                            "description": violation.description,
                        },
                    })

        # Sort by timestamp (most recent first) and limit
        violations = sorted(violations, key=lambda v: v["timestamp"], reverse=True)
        return violations[:limit]

    def get_agent_history(
        self,
        agent_id: str,
        limit: int = 50,
    ) -> dict:
        """Get governance history for an agent.

        Args:
            agent_id: Agent identifier
            limit: Maximum records to return

        Returns:
            Dictionary with agent statistics and history
        """
        records = self.get_records(limit=limit * 2, agent_id=agent_id)

        # Calculate statistics
        total_decisions = len([r for r in records if r.event_type == "decision"])
        authorized_decisions = len([
            r for r in records
            if r.event_type == "decision" and r.execution_authorized
        ])
        total_violations = sum(len(r.violations) for r in records)

        # Calculate average legitimacy score
        decision_scores = [
            r.legitimacy_score
            for r in records
            if r.event_type == "decision"
        ]
        avg_legitimacy = (
            sum(decision_scores) / len(decision_scores)
            if decision_scores
            else 0.0
        )

        return {
            "agent_id": agent_id,
            "total_decisions": total_decisions,
            "authorized_decisions": authorized_decisions,
            "authorization_rate": (
                authorized_decisions / total_decisions
                if total_decisions > 0
                else 0.0
            ),
            "total_violations": total_violations,
            "average_legitimacy_score": avg_legitimacy,
            "recent_records": [
                r.to_dict() for r in records[:limit]
            ],
        }

    def get_statistics(self) -> dict:
        """Get overall ledger statistics.

        Returns:
            Dictionary with ledger statistics
        """
        total_records = len(self.records)

        # Count by event type
        event_types = {}
        for record in self.records:
            event_types[record.event_type] = event_types.get(record.event_type, 0) + 1

        # Count violations
        total_violations = sum(len(r.violations) for r in self.records)
        critical_violations = sum(
            len([v for v in r.violations if v.severity == "critical"])
            for r in self.records
        )

        # Calculate authorization rate
        decisions = [r for r in self.records if r.event_type == "decision"]
        authorized = len([r for r in decisions if r.execution_authorized])
        authorization_rate = (
            authorized / len(decisions) if decisions else 0.0
        )

        # Calculate average legitimacy
        legitimacy_scores = [r.legitimacy_score for r in decisions]
        avg_legitimacy = (
            sum(legitimacy_scores) / len(legitimacy_scores)
            if legitimacy_scores
            else 0.0
        )

        return {
            "total_records": total_records,
            "total_decisions": len(decisions),
            "event_type_counts": event_types,
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "authorization_rate": authorization_rate,
            "average_legitimacy_score": avg_legitimacy,
            "records_in_memory": total_records,
            "max_capacity": self.max_size if self.max_size > 0 else "unlimited",
        }

    def export_records(
        self,
        output_format: str = "dict",
    ) -> list | str:
        """Export all records from the ledger.

        Args:
            output_format: Format for export ("dict", "json", "csv")

        Returns:
            Exported records in specified format
        """
        records_data = [r.to_dict() for r in self.records]

        if output_format == "dict":
            return records_data
        elif output_format == "json":
            import json
            return json.dumps(records_data, indent=2)
        elif output_format == "csv":
            # Simple CSV export
            if not records_data:
                return ""

            headers = list(records_data[0].keys())
            rows = []
            for record in records_data:
                row = [
                    str(record.get(h, ""))
                    for h in headers
                ]
                rows.append(",".join(row))

            return ",".join(headers) + "\n" + "\n".join(rows)
        else:
            raise ValueError(f"Unknown output format: {output_format}")

    def clear(self):
        """Clear all records from the ledger.

        Warning: This operation cannot be undone.
        """
        self.records.clear()
        self.decisions.clear()
        self.record_counter = 0


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_governance_audit_ledger(
    max_size: int = 10000,
) -> GovernanceAuditLedger:
    """Factory function to create a governance audit ledger.

    Args:
        max_size: Maximum number of records to keep

    Returns:
        Configured GovernanceAuditLedger instance
    """
    return GovernanceAuditLedger(max_size=max_size)


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "GovernanceAuditLedger",
    "GovernanceRecord",
    "GovernanceDecision",
    "create_governance_audit_ledger",
]
