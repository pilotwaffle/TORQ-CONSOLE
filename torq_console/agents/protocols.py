"""
Agent Protocol Contracts

Defines the interface that all agents must implement to work with
TORQ Console's web API and other systems.

This prevents "silent broken UI" deployments by enforcing contracts
at type-check time and providing runtime validation.
"""

from typing import Protocol, Dict, Any, Optional, runtime_checkable
from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    """
    Standard response format for all agents.

    Schema version: torq-agent-run-v1
    """
    # Core response
    response: str = Field(..., description="The agent's text response")
    success: bool = Field(True, description="Whether the request succeeded")

    # Metadata
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Confidence score")
    execution_time: float = Field(0.0, ge=0.0, description="Execution time in seconds")
    tools_used: list[str] = Field(default_factory=list, description="Tools used")

    # Optional fields (null until computed)
    reasoning_summary: Optional[str] = Field(None, description="Summary of reasoning")
    evidence_level: Optional[str] = Field(
        None,
        description="Evidence level: low/medium/high (computed from actual signals)"
    )
    routing_success: Optional[bool] = Field(
        None,
        description="Whether routing succeeded (computed from actual result)"
    )
    policy_compliance: Optional[float] = Field(
        None,
        ge=0.0, le=1.0,
        description="Policy compliance score (computed from policy engine)"
    )
    satisfaction: Optional[float] = Field(
        None,
        ge=0.0, le=1.0,
        description="Predicted user satisfaction (computed from actual signals)"
    )

    # Error handling
    error: Optional[str] = Field(None, description="Error message if failed")
    error_type: Optional[str] = Field(None, description="Error type/class if failed")

    # Schema version for forward compatibility
    schema_version: str = Field("torq-agent-run-v1", description="Response schema version")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Hello! I can help you with...",
                "success": True,
                "confidence": 0.85,
                "execution_time": 1.2,
                "tools_used": ["web_search"],
                "reasoning_summary": "Used web search to find current information",
                "evidence_level": "high",
                "routing_success": True,
                "policy_compliance": 1.0,
                "satisfaction": 0.9,
                "schema_version": "torq-agent-run-v1",
            }
        }


@runtime_checkable
class AsyncAgent(Protocol):
    """
    Protocol that all async agents must implement.

    This is the contract that the web API depends on.
    Using Protocol (structural subtyping) means any class with these
    methods will work, regardless of inheritance.
    """

    async def arun(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run the agent and return a response.

        Args:
            message: User message/query
            context: Additional context (session_id, user_info, etc.)

        Returns:
            Dict matching AgentResponse schema (use AgentResponse.model_dump())
        """
        ...

    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and statistics."""
        ...

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        ...


def validate_agent_contract(agent: Any) -> tuple[bool, list[str]]:
    """
    Validate that an agent implements the required AsyncAgent contract.

    Returns:
        (is_valid, list_of_errors)

    Use this at startup to fail fast if agent is misconfigured.
    """
    errors = []

    # Check for required methods
    if not hasattr(agent, 'arun'):
        errors.append("Missing required method: arun()")
    elif not callable(agent.arun):
        errors.append("arun() exists but is not callable")

    if not hasattr(agent, 'get_agent_status'):
        errors.append("Missing required method: get_agent_status()")
    elif not callable(getattr(agent, 'get_agent_status')):
        errors.append("get_agent_status() exists but is not callable")

    if not hasattr(agent, 'health_check'):
        errors.append("Missing required method: health_check()")
    elif not callable(getattr(agent, 'health_check')):
        errors.append("health_check() exists but is not callable")

    # Check arun signature (basic)
    if hasattr(agent, 'arun') and callable(agent.arun):
        import inspect
        sig = inspect.signature(agent.arun)
        if 'message' not in sig.parameters:
            errors.append("arun() missing required parameter: message")

    is_valid = len(errors) == 0
    return is_valid, errors


def assert_agent_contract(agent: Any, agent_name: str = "Agent") -> None:
    """
    Assert that an agent implements the AsyncAgent contract.

    Raises:
        RuntimeError: If contract validation fails

    Use this at startup to fail fast with clear error messages.
    """
    is_valid, errors = validate_agent_contract(agent)

    if not is_valid:
        raise RuntimeError(
            f"{agent_name} does not implement AsyncAgent contract:\n" +
            "\n".join(f"  - {e}" for e in errors) +
            "\n\nThis prevents the web API from functioning correctly."
        )
