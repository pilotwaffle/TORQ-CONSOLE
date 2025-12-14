"""
Data models for tool safety system
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from pydantic import BaseModel, Field, validator


class RiskLevel(str, Enum):
    """Risk levels for tool operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OperationType(str, Enum):
    """Types of operations tools can perform"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    NETWORK = "network"
    SYSTEM = "system"
    FILE_SYSTEM = "file_system"
    API_CALL = "api_call"


class Decision(str, Enum):
    """Policy decision outcomes"""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_CONFIRMATION = "require_confirmation"
    RATE_LIMITED = "rate_limited"


class PolicyConfig(BaseModel):
    """Configuration for a tool policy"""
    tool_name: str
    allowed_paths: List[str] = Field(default_factory=list)
    forbidden_paths: List[str] = Field(default_factory=list)
    allowed_operations: List[OperationType] = Field(default_factory=list)
    forbidden_operations: List[OperationType] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False
    confirmation_timeout: int = 300  # seconds
    rate_limit: Optional[Dict[str, int]] = None  # {"requests": 10, "window": 3600}
    max_file_size: Optional[int] = None  # bytes
    allowed_extensions: Optional[Set[str]] = None
    network_hosts_whitelist: Optional[Set[str]] = None
    require_user_context: bool = False
    log_level: str = "info"

    @validator('allowed_paths', pre=True)
    def normalize_paths(cls, v):
        """Normalize path separators"""
        return [str(p).replace('\\', '/') for p in v]

    @validator('forbidden_paths', pre=True)
    def normalize_forbidden_paths(cls, v):
        """Normalize path separators"""
        return [str(p).replace('\\', '/') for p in v]


class ToolRequest(BaseModel):
    """A request to use a tool"""
    tool_name: str
    operation: OperationType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    target_path: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = Field(default_factory=lambda: f"req_{datetime.utcnow().timestamp()}")


class PolicyDecision(BaseModel):
    """Decision from policy engine"""
    decision: Decision
    risk_level: RiskLevel
    reason: str
    policy_name: str
    confirmation_required: bool = False
    confirmation_message: Optional[str] = None
    rate_limit_info: Optional[Dict[str, Any]] = None
    sandbox_info: Optional[Dict[str, Any]] = None
    allowed_operations: List[OperationType] = Field(default_factory=list)
    denied_operations: List[OperationType] = Field(default_factory=list)


class ConfirmationRequest(BaseModel):
    """Request for user confirmation"""
    request_id: str
    tool_name: str
    operation: OperationType
    risk_level: RiskLevel
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    expires_at: datetime
    confirmed: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(BaseModel):
    """Audit log entry"""
    event_id: str = Field(default_factory=lambda: f"audit_{datetime.utcnow().timestamp()}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_name: str
    operation: OperationType
    decision: Decision
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    target_path: Optional[str] = None
    risk_level: RiskLevel
    reason: str
    execution_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    additional_data: Dict[str, Any] = Field(default_factory=dict)


class SecurityViolation(BaseModel):
    """Security violation record"""
    violation_id: str = Field(default_factory=lambda: f"violation_{datetime.utcnow().timestamp()}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    violation_type: str
    severity: RiskLevel
    tool_name: str
    description: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    blocked: bool = True
    details: Dict[str, Any] = Field(default_factory=dict)


class SandboxConfig(BaseModel):
    """Sandbox configuration"""
    working_directory: Optional[str] = None
    temp_directory: Optional[str] = None
    network_isolated: bool = False
    filesystem_isolated: bool = True
    max_memory_mb: Optional[int] = None
    max_cpu_time_seconds: Optional[int] = None
    allowed_environment_vars: List[str] = Field(default_factory=list)
    forbidden_environment_vars: List[str] = Field(default_factory=list)
    allowed_executables: Optional[Set[str]] = None
    resource_limits: Dict[str, Any] = Field(default_factory=dict)


class RateLimitInfo(BaseModel):
    """Rate limiting information"""
    requests_made: int
    requests_allowed: int
    window_seconds: int
    reset_time: datetime
    retry_after_seconds: Optional[int] = None


class SecurityContext(BaseModel):
    """Security context for request evaluation"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    authentication_level: str = "none"  # none, basic, oauth, mfa
    permissions: Set[str] = Field(default_factory=set)
    session_start_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    risk_score: float = 0.0
    additional_context: Dict[str, Any] = Field(default_factory=dict)