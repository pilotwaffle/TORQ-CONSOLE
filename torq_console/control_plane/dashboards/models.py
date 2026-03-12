"""
TORQ Control Plane - Dashboard Models

L7-M1: Data models for dashboard widgets and layouts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


# ============================================================================
# Widget Models
# ============================================================================

class WidgetType(str, Enum):
    """Types of dashboard widgets."""
    METRIC_CARD = "metric_card"
    CHART = "chart"
    TABLE = "table"
    LIST = "list"
    ALERT_BANNER = "alert_banner"
    PROGRESS = "progress"
    STATUS_GRID = "status_grid"
    TIMELINE = "timeline"
    HEATMAP = "heatmap"


class ChartType(str, Enum):
    """Types of charts."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"


class WidgetPosition(BaseModel):
    """
    Position and size of a widget in the layout.
    """
    x: int = 0
    y: int = 0
    width: int = 4  # Grid columns (12 column grid)
    height: int = 3  # Grid rows


class DataSource(BaseModel):
    """
    Data source configuration for a widget.
    """
    type: str  # api, websocket, poll
    endpoint: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    refresh_interval: Optional[int] = None  # Seconds
    transform: Optional[str] = None


class DashboardWidget(BaseModel):
    """
    A single dashboard widget.
    """
    id: str
    type: WidgetType
    title: str
    position: WidgetPosition

    # Widget-specific configuration
    config: Dict[str, Any] = Field(default_factory=dict)

    # Data source
    data_source: Optional[DataSource] = None

    # Static data (for demos or when data source unavailable)
    static_data: Optional[Dict[str, Any]] = None

    # Visual settings
    color_scheme: Optional[str] = None
    icon: Optional[str] = None

    # Permissions
    required_permission: Optional[str] = None

    class Config:
        use_enum_values = True


class MetricCardWidget(DashboardWidget):
    """
    Widget displaying a single metric with trend.
    """
    type: WidgetType = WidgetType.METRIC_CARD

    # Metric-specific
    metric_key: str
    metric_value: Optional[float] = None
    metric_label: Optional[str] = None
    trend: Optional[str] = None  # up, down, neutral
    trend_percent: Optional[float] = None
    unit: Optional[str] = None


class ChartWidget(DashboardWidget):
    """
    Widget displaying a chart.
    """
    type: WidgetType = WidgetType.CHART

    # Chart-specific
    chart_type: ChartType
    x_axis_key: Optional[str] = None
    y_axis_keys: List[str] = Field(default_factory=list)
    series: List[Dict[str, Any]] = Field(default_factory=list)


class AlertBannerWidget(DashboardWidget):
    """
    Widget displaying alerts.
    """
    type: WidgetType = WidgetType.ALERT_BANNER

    # Alert-specific
    max_alerts: int = 5
    severity_filter: Optional[List[str]] = None


# ============================================================================
# Layout Models
# ============================================================================

class DashboardLayout(BaseModel):
    """
    Layout configuration for a dashboard.
    """
    id: str
    name: str
    description: Optional[str] = None

    # Grid configuration
    columns: int = 12
    row_height: int = 60  # Pixels

    # Widgets
    widgets: List[DashboardWidget] = Field(default_factory=list)

    # Layout settings
    draggable: bool = True
    resizable: bool = True
    collapsible: bool = True

    class Config:
        use_enum_values = True


class DashboardConfig(BaseModel):
    """
    Complete dashboard configuration.
    """
    id: str
    name: str
    title: str
    description: Optional[str] = None
    version: str = "1.0"

    # Layouts (tabs/views)
    layouts: List[DashboardLayout] = Field(default_factory=list)
    default_layout: Optional[str] = None

    # Global settings
    refresh_interval: int = 30  # Seconds
    auto_refresh: bool = True

    # Permissions
    required_permission: Optional[str] = None

    # Theme
    theme: Optional[str] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Preset Dashboard Configurations
# ============================================================================

def create_operational_dashboard() -> DashboardConfig:
    """Create the main operational dashboard."""
    return DashboardConfig(
        id="operational",
        name="operational",
        title="Operational Overview",
        description="Real-time view of TORQ system status",
        layouts=[
            DashboardLayout(
                id="overview",
                name="Overview",
                widgets=[
                    MetricCardWidget(
                        id="active_missions",
                        type=WidgetType.METRIC_CARD,
                        title="Active Missions",
                        position=WidgetPosition(x=0, y=0, width=3, height=2),
                        metric_key="active_missions_count",
                        metric_label="Active",
                        icon="target",
                    ),
                    MetricCardWidget(
                        id="ready_candidates",
                        type=WidgetType.METRIC_CARD,
                        title="Ready Candidates",
                        position=WidgetPosition(x=3, y=0, width=3, height=2),
                        metric_key="ready_candidates_count",
                        metric_label="Ready",
                        icon="check-circle",
                    ),
                    MetricCardWidget(
                        id="system_health",
                        type=WidgetType.METRIC_CARD,
                        title="System Health",
                        position=WidgetPosition(x=6, y=0, width=3, height=2),
                        metric_key="health_score",
                        metric_label="Health",
                        icon="heart",
                    ),
                    MetricCardWidget(
                        id="alerts",
                        type=WidgetType.METRIC_CARD,
                        title="Active Alerts",
                        position=WidgetPosition(x=9, y=0, width=3, height=2),
                        metric_key="active_alerts_count",
                        metric_label="Alerts",
                        icon="alert",
                        color_scheme="warning",
                    ),
                    AlertBannerWidget(
                        id="alert_banner",
                        type=WidgetType.ALERT_BANNER,
                        title="Recent Alerts",
                        position=WidgetPosition(x=0, y=2, width=12, height=2),
                    ),
                ],
            ),
        ],
    )


def create_readiness_dashboard() -> DashboardConfig:
    """Create the readiness governance dashboard."""
    return DashboardConfig(
        id="readiness",
        name="readiness",
        title="Readiness Governance",
        description="Candidate readiness and promotion management",
        layouts=[
            DashboardLayout(
                id="readiness_overview",
                name="Overview",
                widgets=[
                    MetricCardWidget(
                        id="total_candidates",
                        type=WidgetType.METRIC_CARD,
                        title="Total Candidates",
                        position=WidgetPosition(x=0, y=0, width=3, height=2),
                        metric_key="total_candidates",
                        icon="users",
                    ),
                    MetricCardWidget(
                        id="ready_count",
                        type=WidgetType.METRIC_CARD,
                        title="Ready for Promotion",
                        position=WidgetPosition(x=3, y=0, width=3, height=2),
                        metric_key="ready_count",
                        icon="check-circle",
                        color_scheme="success",
                    ),
                    MetricCardWidget(
                        id="blocked_count",
                        type=WidgetType.METRIC_CARD,
                        title="Blocked",
                        position=WidgetPosition(x=6, y=0, width=3, height=2),
                        metric_key="blocked_count",
                        icon="ban",
                        color_scheme="danger",
                    ),
                    MetricCardWidget(
                        id="promotion_rate",
                        type=WidgetType.METRIC_CARD,
                        title="Promotion Rate",
                        position=WidgetPosition(x=9, y=0, width=3, height=2),
                        metric_key="promotion_rate",
                        metric_label="Rate",
                        unit="%",
                        icon="trending-up",
                    ),
                    ChartWidget(
                        id="readiness_trends",
                        type=WidgetType.CHART,
                        title="Readiness Trends",
                        position=WidgetPosition(x=0, y=2, width=8, height=4),
                        chart_type=ChartType.LINE,
                        x_axis_key="date",
                        y_axis_keys=["ready", "blocked", "regressed"],
                    ),
                    ChartWidget(
                        id="state_distribution",
                        type=WidgetType.CHART,
                        title="State Distribution",
                        position=WidgetPosition(x=8, y=2, width=4, height=4),
                        chart_type=ChartType.PIE,
                    ),
                ],
            ),
        ],
    )


def create_mission_dashboard() -> DashboardConfig:
    """Create the mission command dashboard."""
    return DashboardConfig(
        id="missions",
        name="missions",
        title="Mission Command",
        description="Active mission and agent monitoring",
        layouts=[
            DashboardLayout(
                id="mission_overview",
                name="Overview",
                widgets=[
                    MetricCardWidget(
                        id="active_missions",
                        type=WidgetType.METRIC_CARD,
                        title="Active Missions",
                        position=WidgetPosition(x=0, y=0, width=4, height=2),
                        metric_key="active_missions",
                        icon="target",
                    ),
                    MetricCardWidget(
                        id="running_agents",
                        type=WidgetType.METRIC_CARD,
                        title="Running Agents",
                        position=WidgetPosition(x=4, y=0, width=4, height=2),
                        metric_key="running_agents",
                        icon="bot",
                    ),
                    MetricCardWidget(
                        id="completed_tasks",
                        type=WidgetType.METRIC_CARD,
                        title="Tasks Completed",
                        position=WidgetPosition(x=8, y=0, width=4, height=2),
                        metric_key="completed_tasks",
                        icon="check-square",
                    ),
                    ChartWidget(
                        id="mission_throughput",
                        type=WidgetType.CHART,
                        title="Mission Throughput",
                        position=WidgetPosition(x=0, y=2, width=12, height=4),
                        chart_type=ChartType.BAR,
                        x_axis_key="mission_type",
                        y_axis_keys=["completed", "failed", "active"],
                    ),
                ],
            ),
        ],
    )


def create_pattern_dashboard() -> DashboardConfig:
    """Create the pattern intelligence dashboard."""
    return DashboardConfig(
        id="patterns",
        name="patterns",
        title="Pattern Intelligence",
        description="Discovered and validated pattern tracking",
        layouts=[
            DashboardLayout(
                id="pattern_overview",
                name="Overview",
                widgets=[
                    MetricCardWidget(
                        id="discovered_patterns",
                        type=WidgetType.METRIC_CARD,
                        title="Discovered Patterns",
                        position=WidgetPosition(x=0, y=0, width=4, height=2),
                        metric_key="discovered_count",
                        icon="search",
                    ),
                    MetricCardWidget(
                        id="validated_patterns",
                        type=WidgetType.METRIC_CARD,
                        title="Validated Patterns",
                        position=WidgetPosition(x=4, y=0, width=4, height=2),
                        metric_key="validated_count",
                        icon="check",
                        color_scheme="success",
                    ),
                    MetricCardWidget(
                        id="patterns_in_use",
                        type=WidgetType.METRIC_CARD,
                        title="Active in Production",
                        position=WidgetPosition(x=8, y=0, width=4, height=2),
                        metric_key="in_use_count",
                        icon="zap",
                    ),
                    ChartWidget(
                        id="pattern_discovery_rate",
                        type=WidgetType.CHART,
                        title="Discovery Rate",
                        position=WidgetPosition(x=0, y=2, width=6, height=4),
                        chart_type=ChartType.AREA,
                    ),
                    ChartWidget(
                        id="pattern_categories",
                        type=WidgetType.CHART,
                        title="Patterns by Category",
                        position=WidgetPosition(x=6, y=2, width=6, height=4),
                        chart_type=ChartType.PIE,
                    ),
                ],
            ),
        ],
    )


# Get all preset dashboards
def get_preset_dashboards() -> Dict[str, DashboardConfig]:
    """Get all preset dashboard configurations."""
    return {
        "operational": create_operational_dashboard(),
        "readiness": create_readiness_dashboard(),
        "missions": create_mission_dashboard(),
        "patterns": create_pattern_dashboard(),
    }
