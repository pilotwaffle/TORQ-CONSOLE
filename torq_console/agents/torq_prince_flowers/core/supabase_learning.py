"""
Supabase Learning Writer for TORQ Console v2

Writes learning events, telemetry traces, and audit log entries to Supabase
instead of local JSONL files. This enables the learning loop to close in
production on Railway where there's no persistent local filesystem.

Required env vars:
    SUPABASE_URL — Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY — Server-side write access key
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("TORQ.SupabaseLearning")

# ---------------------------------------------------------------------------
# Lazy Supabase client (only import when needed)
# ---------------------------------------------------------------------------

_supabase_client = None


def _get_supabase():
    """Get or create Supabase client (lazy initialization)."""
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        logger.warning("Supabase not configured — learning events will be logged but not persisted to DB")
        return None

    try:
        from supabase import create_client
        _supabase_client = create_client(url, key)
        logger.info(f"Supabase learning writer connected to {url}")
        return _supabase_client
    except ImportError:
        logger.warning("supabase-py not installed — pip install supabase")
        return None
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        return None


# ---------------------------------------------------------------------------
# Table schemas (these need to exist in Supabase)
# ---------------------------------------------------------------------------
# Run this SQL in Supabase SQL Editor to create required tables:
#
# CREATE TABLE IF NOT EXISTS learning_events (
#     id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
#     trace_id text NOT NULL,
#     timestamp timestamptz DEFAULT now(),
#     query text NOT NULL,
#     route_selected text,
#     tools_used jsonb DEFAULT '[]',
#     evidence_sources jsonb DEFAULT '[]',
#     latency_seconds float,
#     confidence float,
#     outcome_score float,
#     reward jsonb DEFAULT '{}',
#     total_reward float,
#     response_preview text,
#     error text,
#     user_feedback float,
#     created_at timestamptz DEFAULT now()
# );
#
# CREATE TABLE IF NOT EXISTS routing_performance (
#     id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
#     intent_class text NOT NULL,
#     route text NOT NULL,
#     total_attempts int DEFAULT 0,
#     successes int DEFAULT 0,
#     total_reward float DEFAULT 0,
#     avg_reward float DEFAULT 0,
#     last_updated timestamptz DEFAULT now()
# );
#
# CREATE TABLE IF NOT EXISTS advisory_audit_log (
#     id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
#     trace_id text NOT NULL,
#     timestamp timestamptz DEFAULT now(),
#     action text NOT NULL,
#     details jsonb DEFAULT '{}',
#     policy_version text,
#     compliance_status text DEFAULT 'compliant',
#     created_at timestamptz DEFAULT now()
# );
#
# CREATE INDEX idx_learning_events_trace ON learning_events(trace_id);
# CREATE INDEX idx_learning_events_timestamp ON learning_events(timestamp);
# CREATE INDEX idx_routing_perf_intent ON routing_performance(intent_class, route);
# CREATE INDEX idx_audit_trace ON advisory_audit_log(trace_id);
# ---------------------------------------------------------------------------


async def write_learning_event(event_data: Dict[str, Any]) -> bool:
    """
    Write a learning event to Supabase learning_events table.
    
    Args:
        event_data: Dict from LearningEvent.to_dict()
    
    Returns:
        True if write succeeded, False otherwise
    """
    sb = _get_supabase()
    if not sb:
        logger.debug(f"Learning event logged (no DB): trace={event_data.get('trace_id', '?')[:8]}")
        return False

    try:
        reward = event_data.get("reward", {})
        row = {
            "trace_id": event_data.get("trace_id"),
            "timestamp": event_data.get("timestamp"),
            "query": event_data.get("query", "")[:1000],  # Truncate long queries
            "route_selected": event_data.get("route_selected"),
            "tools_used": json.dumps(event_data.get("tools_used", [])),
            "evidence_sources": json.dumps(event_data.get("evidence_sources", [])),
            "latency_seconds": event_data.get("latency"),
            "confidence": event_data.get("confidence"),
            "outcome_score": event_data.get("outcome_score"),
            "reward": json.dumps(reward),
            "total_reward": reward.get("total_reward", 0.0),
            "response_preview": event_data.get("response_preview", "")[:500],
            "error": event_data.get("error"),
            "user_feedback": event_data.get("user_feedback"),
        }

        result = sb.table("learning_events").insert(row).execute()
        logger.debug(f"Learning event written to Supabase: trace={row['trace_id'][:8]}")
        return True

    except Exception as e:
        logger.error(f"Failed to write learning event to Supabase: {e}")
        return False


async def write_audit_log(
    trace_id: str,
    action: str,
    details: Dict[str, Any],
    policy_version: str = "v2.0",
    compliance_status: str = "compliant",
) -> bool:
    """Write an advisory audit log entry to Supabase."""
    sb = _get_supabase()
    if not sb:
        return False

    try:
        row = {
            "trace_id": trace_id,
            "action": action,
            "details": json.dumps(details),
            "policy_version": policy_version,
            "compliance_status": compliance_status,
        }

        sb.table("advisory_audit_log").insert(row).execute()
        return True

    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
        return False


async def upsert_routing_performance(
    intent_class: str,
    route: str,
    reward: float,
    success: bool,
) -> bool:
    """
    Upsert routing performance statistics to Supabase.
    Replaces the local routing_success.json file.
    """
    sb = _get_supabase()
    if not sb:
        return False

    try:
        # Try to get existing record
        existing = (
            sb.table("routing_performance")
            .select("*")
            .eq("intent_class", intent_class)
            .eq("route", route)
            .execute()
        )

        if existing.data:
            # Update existing
            record = existing.data[0]
            new_attempts = record["total_attempts"] + 1
            new_successes = record["successes"] + (1 if success else 0)
            new_total_reward = record["total_reward"] + reward
            new_avg_reward = new_total_reward / new_attempts

            sb.table("routing_performance").update({
                "total_attempts": new_attempts,
                "successes": new_successes,
                "total_reward": new_total_reward,
                "avg_reward": new_avg_reward,
                "last_updated": datetime.utcnow().isoformat(),
            }).eq("id", record["id"]).execute()
        else:
            # Insert new
            sb.table("routing_performance").insert({
                "intent_class": intent_class,
                "route": route,
                "total_attempts": 1,
                "successes": 1 if success else 0,
                "total_reward": reward,
                "avg_reward": reward,
            }).execute()

        return True

    except Exception as e:
        logger.error(f"Failed to upsert routing performance: {e}")
        return False


async def get_routing_q_values() -> Dict[str, Dict[str, float]]:
    """
    Load routing Q-values from Supabase for the router to use.
    Returns: {intent_class: {route: avg_reward}}
    """
    sb = _get_supabase()
    if not sb:
        return {}

    try:
        result = sb.table("routing_performance").select("intent_class, route, avg_reward").execute()

        q_values = {}
        for row in result.data:
            intent = row["intent_class"]
            route = row["route"]
            if intent not in q_values:
                q_values[intent] = {}
            q_values[intent][route] = row["avg_reward"]

        return q_values

    except Exception as e:
        logger.error(f"Failed to load routing Q-values: {e}")
        return {}


# ---------------------------------------------------------------------------
# Migration SQL (convenience function)
# ---------------------------------------------------------------------------

def get_migration_sql() -> str:
    """Return the SQL needed to create learning tables in Supabase."""
    return """
-- TORQ Console v2 Learning Tables
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS learning_events (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    trace_id text NOT NULL,
    timestamp timestamptz DEFAULT now(),
    query text NOT NULL,
    route_selected text,
    tools_used jsonb DEFAULT '[]',
    evidence_sources jsonb DEFAULT '[]',
    latency_seconds float,
    confidence float,
    outcome_score float,
    reward jsonb DEFAULT '{}',
    total_reward float,
    response_preview text,
    error text,
    user_feedback float,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS routing_performance (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    intent_class text NOT NULL,
    route text NOT NULL,
    total_attempts int DEFAULT 0,
    successes int DEFAULT 0,
    total_reward float DEFAULT 0,
    avg_reward float DEFAULT 0,
    last_updated timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS advisory_audit_log (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    trace_id text NOT NULL,
    timestamp timestamptz DEFAULT now(),
    action text NOT NULL,
    details jsonb DEFAULT '{}',
    policy_version text,
    compliance_status text DEFAULT 'compliant',
    created_at timestamptz DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_learning_events_trace ON learning_events(trace_id);
CREATE INDEX IF NOT EXISTS idx_learning_events_timestamp ON learning_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_learning_events_reward ON learning_events(total_reward);
CREATE INDEX IF NOT EXISTS idx_routing_perf_intent ON routing_performance(intent_class, route);
CREATE INDEX IF NOT EXISTS idx_audit_trace ON advisory_audit_log(trace_id);

-- Enable RLS (but allow service role full access)
ALTER TABLE learning_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE routing_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE advisory_audit_log ENABLE ROW LEVEL SECURITY;

-- Service role bypass policies
CREATE POLICY "Service role full access" ON learning_events FOR ALL
    USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON routing_performance FOR ALL
    USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON advisory_audit_log FOR ALL
    USING (auth.role() = 'service_role');
"""
