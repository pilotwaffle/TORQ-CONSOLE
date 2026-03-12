"""
TORQ Layer 10 - Strategic Decision Audit System

L10-M1: Creates audit artifacts for every simulated strategic decision.

The DecisionAuditSystem provides:
- Scenario configuration storage
- Simulation output archival
- Forecast confidence tracking
- Risk analysis documentation
- Operator decision recording with traceability

These artifacts become training data for future simulation improvement.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Audit Models
# ============================================================================

class AuditArtifactType(str, Enum):
    """Types of audit artifacts."""
    SCENARIO_CONFIG = "scenario_config"
    SIMULATION_OUTPUT = "simulation_output"
    FORECAST_DATA = "forecast_data"
    RISK_ANALYSIS = "risk_analysis"
    OPERATOR_DECISION = "operator_decision"
    CALIBRATION_DATA = "calibration_data"


class DecisionStatus(str, Enum):
    """Status of operator decisions."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    DEFERRED = "deferred"


class AuditArtifact(BaseModel):
    """An audit artifact for a strategic decision."""
    artifact_id: UUID = Field(default_factory=uuid4)
    artifact_type: AuditArtifactType
    scenario_id: UUID

    # Content
    title: str
    description: str
    content: Dict[str, Any]

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    version: int = 1

    # Classification
    sensitivity: str = "internal"  # internal, confidential, public
    retention_days: int = 365

    # Links to related artifacts
    related_artifacts: List[UUID] = Field(default_factory=list)


class StrategicDecisionRecord(BaseModel):
    """Complete record of a strategic decision process."""
    decision_id: UUID = Field(default_factory=uuid4)
    scenario_id: UUID
    title: str

    # Scenario Phase
    scenario_artifact_id: UUID

    # Simulation Phase
    simulation_artifact_id: UUID
    forecast_artifact_id: Optional[UUID] = None

    # Risk Analysis Phase
    risk_artifact_id: Optional[UUID] = None

    # Operator Decision
    operator_decision: DecisionStatus = DecisionStatus.PENDING
    decision_artifact_id: Optional[UUID] = None
    decision_maker: Optional[str] = None
    decision_at: Optional[datetime] = None

    # Rationale
    rationale: str = ""
    alternative_considered: str = ""

    # Follow-up
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    actual_outcome: Optional[Dict[str, Any]] = None
    outcome_recorded_at: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)


# ============================================================================
# Audit Storage Backend
# ============================================================================

class AuditStorageBackend:
    """Storage backend for audit artifacts."""

    def __init__(self, storage_path: Path):
        """Initialize the audit storage backend."""
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.storage_path / "artifacts").mkdir(exist_ok=True)
        (self.storage_path / "decisions").mkdir(exist_ok=True)
        (self.storage_path / "archive").mkdir(exist_ok=True)

    async def save_artifact(self, artifact: AuditArtifact) -> UUID:
        """Save an audit artifact to storage."""
        artifact_path = (
            self.storage_path / "artifacts" /
            f"{artifact.artifact_type.value}_{artifact.artifact_id}.json"
        )

        artifact_data = {
            "artifact_id": str(artifact.artifact_id),
            "artifact_type": artifact.artifact_type.value,
            "scenario_id": str(artifact.scenario_id),
            "title": artifact.title,
            "description": artifact.description,
            "content": artifact.content,
            "created_at": artifact.created_at.isoformat(),
            "created_by": artifact.created_by,
            "version": artifact.version,
            "sensitivity": artifact.sensitivity,
            "retention_days": artifact.retention_days,
            "related_artifacts": [str(a) for a in artifact.related_artifacts],
        }

        artifact_path.write_text(json.dumps(artifact_data, indent=2))

        logger.debug(f"[AuditStorage] Saved artifact: {artifact.artifact_id}")

        return artifact.artifact_id

    async def load_artifact(self, artifact_id: UUID) -> Optional[AuditArtifact]:
        """Load an audit artifact from storage."""
        # Search for artifact file
        for artifact_file in (self.storage_path / "artifacts").glob("*.json"):
            try:
                data = json.loads(artifact_file.read_text())
                if data.get("artifact_id") == str(artifact_id):
                    return AuditArtifact(
                        artifact_id=UUID(data["artifact_id"]),
                        artifact_type=AuditArtifactType(data["artifact_type"]),
                        scenario_id=UUID(data["scenario_id"]),
                        title=data["title"],
                        description=data["description"],
                        content=data["content"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        created_by=data.get("created_by"),
                        version=data.get("version", 1),
                        sensitivity=data.get("sensitivity", "internal"),
                        retention_days=data.get("retention_days", 365),
                        related_artifacts=[UUID(a) for a in data.get("related_artifacts", [])],
                    )
            except Exception as e:
                logger.debug(f"Error reading artifact file: {e}")

        return None

    async def save_decision_record(self, record: StrategicDecisionRecord) -> UUID:
        """Save a strategic decision record."""
        record_path = (
            self.storage_path / "decisions" /
            f"decision_{record.decision_id}.json"
        )

        record_data = {
            "decision_id": str(record.decision_id),
            "scenario_id": str(record.scenario_id),
            "title": record.title,
            "scenario_artifact_id": str(record.scenario_artifact_id),
            "simulation_artifact_id": str(record.simulation_artifact_id),
            "forecast_artifact_id": str(record.forecast_artifact_id) if record.forecast_artifact_id else None,
            "risk_artifact_id": str(record.risk_artifact_id) if record.risk_artifact_id else None,
            "operator_decision": record.operator_decision.value,
            "decision_artifact_id": str(record.decision_artifact_id) if record.decision_artifact_id else None,
            "decision_maker": record.decision_maker,
            "decision_at": record.decision_at.isoformat() if record.decision_at else None,
            "rationale": record.rationale,
            "alternative_considered": record.alternative_considered,
            "follow_up_required": record.follow_up_required,
            "follow_up_date": record.follow_up_date.isoformat() if record.follow_up_date else None,
            "actual_outcome": record.actual_outcome,
            "outcome_recorded_at": record.outcome_recorded_at.isoformat() if record.outcome_recorded_at else None,
            "created_at": record.created_at.isoformat(),
            "tags": record.tags,
        }

        record_path.write_text(json.dumps(record_data, indent=2))

        logger.info(f"[AuditStorage] Saved decision record: {record.decision_id}")

        return record.decision_id

    async def load_decision_record(self, decision_id: UUID) -> Optional[StrategicDecisionRecord]:
        """Load a strategic decision record."""
        record_path = self.storage_path / "decisions" / f"decision_{decision_id}.json"

        if record_path.exists():
            data = json.loads(record_path.read_text())
            return StrategicDecisionRecord(
                decision_id=UUID(data["decision_id"]),
                scenario_id=UUID(data["scenario_id"]),
                title=data["title"],
                scenario_artifact_id=UUID(data["scenario_artifact_id"]),
                simulation_artifact_id=UUID(data["simulation_artifact_id"]),
                forecast_artifact_id=UUID(data["forecast_artifact_id"]) if data.get("forecast_artifact_id") else None,
                risk_artifact_id=UUID(data["risk_artifact_id"]) if data.get("risk_artifact_id") else None,
                operator_decision=DecisionStatus(data["operator_decision"]),
                decision_artifact_id=UUID(data["decision_artifact_id"]) if data.get("decision_artifact_id") else None,
                decision_maker=data.get("decision_maker"),
                decision_at=datetime.fromisoformat(data["decision_at"]) if data.get("decision_at") else None,
                rationale=data.get("rationale", ""),
                alternative_considered=data.get("alternative_considered", ""),
                follow_up_required=data.get("follow_up_required", False),
                follow_up_date=datetime.fromisoformat(data["follow_up_date"]) if data.get("follow_up_date") else None,
                actual_outcome=data.get("actual_outcome"),
                outcome_recorded_at=datetime.fromisoformat(data["outcome_recorded_at"]) if data.get("outcome_recorded_at") else None,
                created_at=datetime.fromisoformat(data["created_at"]),
                tags=data.get("tags", []),
            )
        return None

    def list_decision_records(
        self,
        limit: int = 100,
        status: Optional[DecisionStatus] = None,
    ) -> List[Dict[str, Any]]:
        """List decision records with optional filtering."""
        records = []

        for record_file in (self.storage_path / "decisions").glob("decision_*.json"):
            try:
                data = json.loads(record_file.read_text())

                # Filter by status if specified
                if status and data.get("operator_decision") != status.value:
                    continue

                records.append({
                    "decision_id": data["decision_id"],
                    "title": data["title"],
                    "status": data.get("operator_decision"),
                    "created_at": data["created_at"],
                    "decision_maker": data.get("decision_maker"),
                })

                if len(records) >= limit:
                    break
            except Exception:
                continue

        return sorted(records, key=lambda r: r["created_at"], reverse=True)


# ============================================================================
# Decision Audit Service
# ============================================================================

class DecisionAuditService:
    """
    Manages audit artifacts for strategic decisions.

    Creates and maintains traceability for all strategic decisions
    made using TORQ simulations.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the decision audit service."""
        if storage_path is None:
            storage_path = Path.cwd() / "data" / "simulation_audit"
        self._storage = AuditStorageBackend(storage_path)

    async def begin_decision_process(
        self,
        scenario_id: UUID,
        scenario_config: Dict[str, Any],
        title: str,
        created_by: Optional[str] = None,
    ) -> StrategicDecisionRecord:
        """
        Begin a strategic decision process by recording the scenario.

        Args:
            scenario_id: ID of the simulation scenario
            scenario_config: Scenario configuration
            title: Decision title
            created_by: User who initiated the process

        Returns:
            StrategicDecisionRecord with scenario artifact
        """
        # Create scenario artifact
        scenario_artifact = AuditArtifact(
            artifact_type=AuditArtifactType.SCENARIO_CONFIG,
            scenario_id=scenario_id,
            title=f"Scenario: {title}",
            description="Initial scenario configuration",
            content=scenario_config,
            created_by=created_by,
        )
        scenario_artifact_id = await self._storage.save_artifact(scenario_artifact)

        # Create decision record
        record = StrategicDecisionRecord(
            scenario_id=scenario_id,
            title=title,
            scenario_artifact_id=scenario_artifact_id,
            simulation_artifact_id=uuid4(),  # Placeholder, will update after simulation
        )

        await self._storage.save_decision_record(record)

        logger.info(
            f"[DecisionAudit] Began decision process: {title} "
            f"(scenario: {scenario_id})"
        )

        return record

    async def record_simulation_results(
        self,
        decision_id: UUID,
        simulation_result: Dict[str, Any],
        forecast_data: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Record simulation results for a decision process.

        Args:
            decision_id: Decision record ID
            simulation_result: Simulation output
            forecast_data: Optional forecast data

        Returns:
            Simulation artifact ID
        """
        record = await self._storage.load_decision_record(decision_id)
        if not record:
            raise ValueError(f"Decision record not found: {decision_id}")

        # Create simulation artifact
        simulation_artifact = AuditArtifact(
            artifact_type=AuditArtifactType.SIMULATION_OUTPUT,
            scenario_id=record.scenario_id,
            title=f"Simulation Results: {record.title}",
            description="Simulation execution results",
            content=simulation_result,
            related_artifacts=[record.scenario_artifact_id],
        )
        simulation_artifact_id = await self._storage.save_artifact(simulation_artifact)

        # Create forecast artifact if provided
        forecast_artifact_id = None
        if forecast_data:
            forecast_artifact = AuditArtifact(
                artifact_type=AuditArtifactType.FORECAST_DATA,
                scenario_id=record.scenario_id,
                title=f"Forecast: {record.title}",
                description="Strategic forecast data",
                content=forecast_data,
                related_artifacts=[simulation_artifact_id],
            )
            forecast_artifact_id = await self._storage.save_artifact(forecast_artifact)

        # Update decision record
        record.simulation_artifact_id = simulation_artifact_id
        record.forecast_artifact_id = forecast_artifact_id
        await self._storage.save_decision_record(record)

        logger.debug(f"[DecisionAudit] Recorded simulation results for {decision_id}")

        return simulation_artifact_id

    async def record_operator_decision(
        self,
        decision_id: UUID,
        status: DecisionStatus,
        decision_maker: str,
        rationale: str = "",
        alternative_considered: str = "",
    ) -> StrategicDecisionRecord:
        """
        Record the operator's final decision.

        Args:
            decision_id: Decision record ID
            status: Decision status
            decision_maker: Who made the decision
            rationale: Decision rationale
            alternative_considered: Alternative options considered

        Returns:
            Updated decision record
        """
        record = await self._storage.load_decision_record(decision_id)
        if not record:
            raise ValueError(f"Decision record not found: {decision_id}")

        # Create decision artifact
        decision_artifact = AuditArtifact(
            artifact_type=AuditArtifactType.OPERATOR_DECISION,
            scenario_id=record.scenario_id,
            title=f"Operator Decision: {record.title}",
            description=f"Decision: {status.value}",
            content={
                "status": status.value,
                "rationale": rationale,
                "alternative_considered": alternative_considered,
            },
            created_by=decision_maker,
            related_artifacts=[
                record.scenario_artifact_id,
                record.simulation_artifact_id,
            ],
        )
        decision_artifact_id = await self._storage.save_artifact(decision_artifact)

        # Update record
        record.operator_decision = status
        record.decision_artifact_id = decision_artifact_id
        record.decision_maker = decision_maker
        record.decision_at = datetime.now()
        record.rationale = rationale
        record.alternative_considered = alternative_considered

        await self._storage.save_decision_record(record)

        logger.info(
            f"[DecisionAudit] Recorded operator decision: {status.value} "
            f"for {record.title} by {decision_maker}"
        )

        return record

    async def record_actual_outcome(
        self,
        decision_id: UUID,
        outcome: Dict[str, Any],
    ) -> StrategicDecisionRecord:
        """
        Record the actual outcome after a decision was implemented.

        This creates training data for future simulation calibration.

        Args:
            decision_id: Decision record ID
            outcome: Actual outcome data

        Returns:
            Updated decision record
        """
        record = await self._storage.load_decision_record(decision_id)
        if not record:
            raise ValueError(f"Decision record not found: {decision_id}")

        record.actual_outcome = outcome
        record.outcome_recorded_at = datetime.now()

        # Also store as calibration data
        calibration_artifact = AuditArtifact(
            artifact_type=AuditArtifactType.CALIBRATION_DATA,
            scenario_id=record.scenario_id,
            title=f"Calibration Data: {record.title}",
            description="Actual outcome for simulation calibration",
            content=outcome,
            created_by="system",
            related_artifacts=[record.decision_artifact_id] if record.decision_artifact_id else [],
        )
        await self._storage.save_artifact(calibration_artifact)

        await self._storage.save_decision_record(record)

        logger.info(f"[DecisionAudit] Recorded actual outcome for {decision_id}")

        return record

    def get_decision_record(self, decision_id: UUID) -> Optional[StrategicDecisionRecord]:
        """Get a decision record by ID (sync wrapper)."""
        # Find the decision file directly
        record_path = self._storage.storage_path / "decisions" / f"decision_{decision_id}.json"
        if record_path.exists():
            import json
            data = json.loads(record_path.read_text())
            return StrategicDecisionRecord(
                decision_id=UUID(data["decision_id"]),
                scenario_id=UUID(data["scenario_id"]),
                title=data["title"],
                scenario_artifact_id=UUID(data["scenario_artifact_id"]),
                simulation_artifact_id=UUID(data["simulation_artifact_id"]),
                forecast_artifact_id=UUID(data["forecast_artifact_id"]) if data.get("forecast_artifact_id") else None,
                risk_artifact_id=UUID(data["risk_artifact_id"]) if data.get("risk_artifact_id") else None,
                operator_decision=DecisionStatus(data["operator_decision"]),
                decision_artifact_id=UUID(data["decision_artifact_id"]) if data.get("decision_artifact_id") else None,
                decision_maker=data.get("decision_maker"),
                decision_at=datetime.fromisoformat(data["decision_at"]) if data.get("decision_at") else None,
                rationale=data.get("rationale", ""),
                alternative_considered=data.get("alternative_considered", ""),
                follow_up_required=data.get("follow_up_required", False),
                follow_up_date=datetime.fromisoformat(data["follow_up_date"]) if data.get("follow_up_date") else None,
                actual_outcome=data.get("actual_outcome"),
                outcome_recorded_at=datetime.fromisoformat(data["outcome_recorded_at"]) if data.get("outcome_recorded_at") else None,
                created_at=datetime.fromisoformat(data["created_at"]),
                tags=data.get("tags", []),
            )
        return None

    def list_decisions(
        self,
        limit: int = 50,
        status: Optional[DecisionStatus] = None,
    ) -> List[Dict[str, Any]]:
        """List decision records (sync wrapper)."""
        return self._storage.list_decision_records(limit, status)


# Global decision audit service instance
_service: Optional[DecisionAuditService] = None


def get_decision_audit_service(storage_path: Optional[Path] = None) -> DecisionAuditService:
    """Get the global decision audit service instance."""
    global _service
    if _service is None:
        _service = DecisionAuditService(storage_path)
    return _service
