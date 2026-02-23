"""
Learning policy management for TORQ Console.

Provides endpoints for:
- Learning system status
- Policy approval (admin)
- Policy rollback (admin)
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")


async def get_learning_status() -> Dict[str, Any]:
    """
    Get the current status of the learning system.

    Returns configuration, policy version, and metrics.
    """
    import httpx

    configured = bool(SUPABASE_URL and SUPABASE_KEY)

    status = {
        "configured": configured,
        "backend": "supabase",
        "policy_version": os.getenv("TORQ_LEARNING_POLICY_VERSION", "1.0.0"),
        "policy_updated_at": os.getenv("TORQ_LEARNING_POLICY_UPDATED", "unknown"),
        "features": {
            "consolidated_reward": True,
            "experience_replay": True,
            "swarm_memory": True,
            "policy_approval": True,
        },
    }

    if configured:
        # Try to get actual metrics from Supabase
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check learning_events table
                response = await client.get(
                    f"{SUPABASE_URL}/rest/v1/learning_events",
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "application/json",
                    },
                    params={"select": "count", "limit": 1},
                )
                if response.status_code == 200:
                    status["reachable"] = True
                else:
                    status["reachable"] = False
                    status["error"] = f"HTTP {response.status_code}"
        except Exception as e:
            status["reachable"] = False
            status["error"] = str(e)
    else:
        status["reachable"] = False
        status["error"] = "Supabase not configured"

    return status


async def approve_policy_version(
    policy_id: str,
    routing_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Approve a new learning policy for rollout.

    This is an admin-only operation that:
    1. Validates the policy data
    2. Stores the new policy version
    3. Returns rollout instructions
    """
    import httpx

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase not configured - cannot approve policy")

    # Create policy record
    policy_record = {
        "policy_id": policy_id,
        "routing_data": routing_data,
        "status": "approved",
        "approved_at": datetime.utcnow().isoformat() + "Z",
        "created_by": "admin",  # In real impl, would be from auth context
    }

    # Store in learning_policies table
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/learning_policies",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json=policy_record,
        )
        response.raise_for_status()

    logger.info(f"Policy {policy_id} approved and stored")

    return {
        "policy_id": policy_id,
        "status": "approved",
        "approved_at": policy_record["approved_at"],
        "next_step": "deploy_to_railway",
    }


async def rollback_policy_version() -> Dict[str, Any]:
    """
    Rollback to the previous learning policy.

    This is an admin-only emergency operation.
    """
    import httpx

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase not configured - cannot rollback policy")

    # Get current policy and previous version
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get most recent approved policy (excluding current)
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/learning_policies",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
            },
            params={
                "order": "approved_at.desc",
                "limit": 2,
            },
        )
        response.raise_for_status()
        policies = response.json()

    if len(policies) < 2:
        raise ValueError("No previous policy to rollback to")

    previous_policy = policies[1]

    logger.info(f"Rolling back from {policies[0]['policy_id']} to {previous_policy['policy_id']}")

    return {
        "rollback_from": policies[0].get("policy_id"),
        "rollback_to": previous_policy.get("policy_id"),
        "policy_id": previous_policy.get("policy_id"),
        "routing_data": previous_policy.get("routing_data"),
        "status": "rolled_back",
        "rolled_back_at": datetime.utcnow().isoformat() + "Z",
    }


# ============================================================================
# Simplified learning hook API for Railway app
# ============================================================================

def calculate_consulting_reward(
    evidence_level: str = "medium",
    routing_success: bool = True,
    policy_compliance: float = 1.0,
    user_satisfaction_prediction: float = 0.8,
    response_time: float = 0.0,
) -> float:
    """
    Simplified reward calculation for Railway learning hook.

    This is a streamlined version that matches the railway_app.py signature.
    For full consulting-grade reward, use the version in learning_hook.py.
    """
    # Evidence score (30%)
    evidence_scores = {"high": 1.0, "medium": 0.7, "low": 0.4, "none": 0.0}
    evidence_score = evidence_scores.get(evidence_level, 0.7)

    # Routing success (20%)
    routing_score = 1.0 if routing_success else 0.0

    # Policy compliance (20%)
    compliance_score = max(0.0, min(1.0, policy_compliance))

    # User satisfaction (10%)
    satisfaction_score = max(0.0, min(1.0, user_satisfaction_prediction))

    # Response time bonus/penalty (20%)
    # Under 2 seconds = bonus, over 10 seconds = penalty
    if response_time < 2.0:
        time_score = 1.0
    elif response_time > 10.0:
        time_score = max(0.0, 1.0 - (response_time - 10.0) * 0.05)
    else:
        time_score = 0.8

    # Weighted sum
    reward = (
        0.30 * evidence_score +
        0.20 * routing_score +
        0.20 * compliance_score +
        0.10 * satisfaction_score +
        0.20 * time_score
    )

    return round(max(0.0, min(1.0, reward)), 4)


async def record_learning_event(
    trace_id: str,
    session_id: str,
    agent_name: str,
    user_query: str,
    agent_response: str,
    reward: float,
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Simplified learning event recording for Railway app.

    This creates a learning event compatible with the storage layer.
    """
    import httpx

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning(f"Supabase not configured - learning event {trace_id[:8]} not persisted")
        return {"ok": False, "error": "Supabase not configured"}

    event = {
        "trace_id": trace_id,
        "session_id": session_id,
        "agent_name": agent_name,
        "user_query": user_query[:500],  # Truncate
        "agent_response": agent_response[:1000],  # Truncate
        "reward": reward,
        "metadata": metadata,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SUPABASE_URL}/rest/v1/learning_events",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                json=event,
            )
            response.raise_for_status()

        logger.debug(f"Learning event stored: {trace_id[:8]}")
        return {"ok": True, "trace_id": trace_id}

    except Exception as e:
        logger.error(f"Failed to store learning event: {e}")
        return {"ok": False, "error": str(e)}
