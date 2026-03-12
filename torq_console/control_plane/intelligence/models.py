"""
TORQ Control Plane - Intelligence Models

L7-M1: Data models for operational intelligence views.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


# ============================================================================
# Intelligence Layer Models
# ============================================================================

class LayerType(str, Enum):
    """Types of intelligence layers."""
    EXECUTION = "execution"
    ARTIFACTS = "artifacts"
    MEMORY = "memory"
    INSIGHTS = "insights"
    PATTERNS = "patterns"
    READINESS = "readiness"
    GOVERNANCE = "governance"


class LayerStatus(str, Enum):
    """Status of an intelligence layer."""
    ACTIVE = "active"
    IDLE = "idle"
    DEGRADED = "degraded"
    DOWN = "down"
    MAINTENANCE = "maintenance"


class IntelligenceLayer(BaseModel):
    """
    Status and metrics for a single intelligence layer.
    """
    layer_type: LayerType
    name: str
    description: Optional[str] = None

    # Status
    status: LayerStatus = LayerStatus.ACTIVE
    last_activity: Optional[datetime] = None
    health_score: float = 100.0

    # Metrics
    metrics: Dict[str, Any] = Field(default_factory=dict)
    item_count: int = 0
    throughput_per_hour: float = 0.0
    error_rate: float = 0.0

    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class IntelligenceView(BaseModel):
    """
    Aggregated view of all intelligence layers.
    """
    view_id: str = "system"
    timestamp: datetime = Field(default_factory=datetime.now)

    # Layer status
    layers: List[IntelligenceLayer] = Field(default_factory=list)

    # System-wide metrics
    total_items: int = 0
    active_processes: int = 0
    system_health: float = 100.0

    # Recent activity
    recent_insights: List[Dict[str, Any]] = Field(default_factory=list)
    recent_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    recent_governance_actions: List[Dict[str, Any]] = Field(default_factory=list)

    # Alerts
    active_alerts: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        use_enum_values = True


# ============================================================================
# Insight Models
# ============================================================================

class InsightStatus(str, Enum):
    """Status of an insight."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    EXPIRED = "expired"


class InsightView(BaseModel):
    """
    A single insight from the insight system.
    """
    id: UUID
    title: str
    description: Optional[str] = None

    # Status
    status: InsightStatus
    confidence: float
    created_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None

    # Content
    content_type: str  # pattern, recommendation, anomaly, etc.
    source_layer: LayerType
    data_sources: List[str] = Field(default_factory=list)

    # Impact
    impact_score: float
    applications: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


# ============================================================================
# Memory Models
# ============================================================================

class MemoryItem(BaseModel):
    """
    A governed memory item.
    """
    id: UUID
    key: str
    value_type: str  # pattern, insight, configuration, etc.
    confidence: float

    # Governance
    governed: bool = True
    validated: bool = False
    validated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Usage
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class MemoryStatistics(BaseModel):
    """
    Statistics for governed memory.
    """
    total_items: int = 0
    governed_items: int = 0
    validated_items: int = 0

    # By type
    items_by_type: Dict[str, int] = Field(default_factory=dict)

    # Health
    avg_confidence: float = 0.0
    expired_items: int = 0
    low_confidence_items: int = 0

    # Activity
    total_accesses: int = 0
    unique_items_accessed: int = 0
    most_accessed_items: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


# ============================================================================
# Helper Functions
# ============================================================================

def create_layer_status(
    layer_type: LayerType,
    status: LayerStatus = LayerStatus.ACTIVE,
    metrics: Optional[Dict[str, Any]] = None,
) -> IntelligenceLayer:
    """
    Create an IntelligenceLayer with defaults.

    Args:
        layer_type: Type of the layer
        status: Current status
        metrics: Optional metrics dictionary

    Returns:
        IntelligenceLayer instance
    """
    names = {
        LayerType.EXECUTION: "Execution Layer",
        LayerType.ARTIFACTS: "Artifacts Layer",
        LayerType.MEMORY: "Governed Memory",
        LayerType.INSIGHTS: "Insight Intelligence",
        LayerType.PATTERNS: "Pattern Intelligence",
        LayerType.READINESS: "Readiness Governance",
        LayerType.GOVERNANCE: "Governance Actions",
    }

    return IntelligenceLayer(
        layer_type=layer_type,
        name=names.get(layer_type, layer_type.value),
        status=status,
        metrics=metrics or {},
    )


def get_default_layers() -> List[IntelligenceLayer]:
    """Get default intelligence layer configuration."""
    return [
        create_layer_status(LayerType.EXECUTION),
        create_layer_status(LayerType.ARTIFACTS),
        create_layer_status(LayerType.MEMORY),
        create_layer_status(LayerType.INSIGHTS),
        create_layer_status(LayerType.PATTERNS),
        create_layer_status(LayerType.READINESS),
        create_layer_status(LayerType.GOVERNANCE),
    ]
