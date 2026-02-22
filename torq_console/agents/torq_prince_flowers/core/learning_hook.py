"""
MANDATORY Post-Response Learning Hook for TORQ Console v2

This is NOT optional. Every response Prince Flowers produces MUST pass through
this hook. No response is complete without a learning event.

The Core Principle:
    Prince Flowers cannot complete a response without producing a learning event.
    Learning is mandatory, not optional.

Integration Points:
    1. Mandatory post-response learning event recording
    2. Consulting-grade reward calculation
    3. Experience replay trigger (every N interactions)
    4. Swarm memory update for routing feedback
"""

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger("TORQ.LearningHook")

# ============================================================================
# REWARD FUNCTION: Consulting-Grade
# ============================================================================
# Reward =
#   0.3 * evidence_score +
#   0.2 * routing_confidence +
#   0.2 * policy_compliance +
#   0.2 * numeric_validity +
#   0.1 * user_feedback
#   - tool_error_penalty
# ============================================================================


def calculate_consulting_reward(
    evidence_sources: List[str],
    evidence_completeness: float,
    routing_confidence: float,
    policy_compliance: bool,
    numeric_values_valid: bool,
    user_feedback: Optional[float],
    tool_errors: int,
    hallucination_flags: int,
    latency_seconds: float,
    response_length: int,
) -> Dict[str, Any]:
    """
    Calculate reward aligned with paid-grade consulting quality.

    This replaces the vague reward system. Every dimension maps to
    something a consulting client actually cares about.

    Returns:
        Dict with total_reward, component scores, and breakdown
    """
    # Evidence completeness (30% weight)
    # Did the response cite sources? Were they relevant?
    evidence_score = 0.0
    if evidence_sources:
        source_count_score = min(len(evidence_sources) / 3.0, 1.0)  # 3+ sources = full score
        evidence_score = (source_count_score * 0.4 + evidence_completeness * 0.6)
    elif evidence_completeness > 0:
        evidence_score = evidence_completeness * 0.5  # Partial credit without explicit sources

    # Routing confidence (20% weight)
    # Did the router know where to send this? High confidence = good routing.
    routing_score = min(max(routing_confidence, 0.0), 1.0)

    # Policy compliance (20% weight)
    # Did the response follow consulting policies? Binary but important.
    compliance_score = 1.0 if policy_compliance else 0.0

    # Numeric validity (20% weight)
    # Are numbers in the response sane? Critical for financial consulting.
    numeric_score = 1.0 if numeric_values_valid else 0.3  # Partial credit if no numbers present

    # User feedback (10% weight)
    # Explicit thumbs up/down from the user
    feedback_score = 0.5  # Default neutral if no feedback
    if user_feedback is not None:
        feedback_score = min(max(user_feedback, 0.0), 1.0)

    # Penalties
    tool_error_penalty = min(tool_errors * 0.15, 0.5)  # Cap at -0.5
    hallucination_penalty = min(hallucination_flags * 0.25, 0.5)  # Cap at -0.5
    latency_penalty = max(0, (latency_seconds - 10.0) * 0.02)  # Penalize > 10s responses

    # Weighted sum
    raw_reward = (
        0.30 * evidence_score +
        0.20 * routing_score +
        0.20 * compliance_score +
        0.20 * numeric_score +
        0.10 * feedback_score
    )

    total_penalty = tool_error_penalty + hallucination_penalty + latency_penalty
    total_reward = max(min(raw_reward - total_penalty, 1.0), -1.0)

    return {
        "total_reward": round(total_reward, 4),
        "components": {
            "evidence_score": round(evidence_score, 4),
            "routing_confidence": round(routing_score, 4),
            "policy_compliance": round(compliance_score, 4),
            "numeric_validity": round(numeric_score, 4),
            "user_feedback": round(feedback_score, 4),
        },
        "penalties": {
            "tool_errors": round(tool_error_penalty, 4),
            "hallucination": round(hallucination_penalty, 4),
            "latency": round(latency_penalty, 4),
            "total_penalty": round(total_penalty, 4),
        },
        "raw_reward": round(raw_reward, 4),
        "metadata": {
            "evidence_source_count": len(evidence_sources),
            "latency_seconds": round(latency_seconds, 2),
            "response_length": response_length,
        }
    }


# ============================================================================
# LEARNING EVENT: The mandatory record
# ============================================================================

class LearningEvent:
    """A single, mandatory learning event produced by every response."""

    def __init__(
        self,
        trace_id: str,
        query: str,
        route_selected: str,
        tools_used: List[str],
        evidence_sources: List[str],
        latency: float,
        confidence: float,
        outcome_score: float,
        reward_breakdown: Dict[str, Any],
        response_text: str,
        error: Optional[str] = None,
        user_feedback: Optional[float] = None,
    ):
        self.trace_id = trace_id
        self.timestamp = datetime.utcnow().isoformat()
        self.query = query
        self.route_selected = route_selected
        self.tools_used = tools_used
        self.evidence_sources = evidence_sources
        self.latency = latency
        self.confidence = confidence
        self.outcome_score = outcome_score
        self.reward_breakdown = reward_breakdown
        self.response_text = response_text[:500]  # Truncate for storage
        self.error = error
        self.user_feedback = user_feedback

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "query": self.query,
            "route_selected": self.route_selected,
            "tools_used": self.tools_used,
            "evidence_sources": self.evidence_sources,
            "latency": self.latency,
            "confidence": self.confidence,
            "outcome_score": self.outcome_score,
            "reward": self.reward_breakdown,
            "response_preview": self.response_text,
            "error": self.error,
            "user_feedback": self.user_feedback,
        }


# ============================================================================
# EXPERIENCE REPLAY: Triggered every N interactions
# ============================================================================

class ExperienceReplayEngine:
    """
    Replays experiences to update Q-values and policy performance.
    
    Currently: You log experiences. You don't replay them.
    Now: On every N interactions, trigger async replay.
    """

    REPLAY_INTERVAL = 25  # Replay every 25 interactions
    MINI_BATCH_SIZE = 10
    LEARNING_RATE = 0.1
    DISCOUNT_FACTOR = 0.9

    def __init__(self, knowledge_path: str):
        self.knowledge_path = knowledge_path
        self.interaction_count = 0
        self.q_values: Dict[str, Dict[str, float]] = {}  # state -> {action -> value}
        self.experience_buffer: List[Dict[str, Any]] = []
        self._load_knowledge()

    def _load_knowledge(self):
        """Load persisted Q-values from disk."""
        try:
            if os.path.exists(self.knowledge_path):
                with open(self.knowledge_path, 'r') as f:
                    data = json.load(f)
                self.q_values = data.get("q_values", {})
                self.interaction_count = data.get("interaction_count", 0)
                logger.info(f"Loaded RL knowledge: {len(self.q_values)} states, {self.interaction_count} interactions")
        except Exception as e:
            logger.error(f"Failed to load RL knowledge: {e}")

    def _save_knowledge(self):
        """Persist Q-values to disk."""
        try:
            os.makedirs(os.path.dirname(self.knowledge_path), exist_ok=True)
            data = {
                "q_values": self.q_values,
                "interaction_count": self.interaction_count,
                "last_updated": datetime.utcnow().isoformat(),
                "buffer_size": len(self.experience_buffer),
            }
            with open(self.knowledge_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved RL knowledge: {len(self.q_values)} states")
        except Exception as e:
            logger.error(f"Failed to save RL knowledge: {e}")

    def add_experience(self, event: LearningEvent):
        """Add experience and check if replay should trigger."""
        experience = {
            "state": self._extract_state(event),
            "action": event.route_selected,
            "reward": event.reward_breakdown.get("total_reward", 0.0),
            "confidence": event.confidence,
            "tools_used": event.tools_used,
            "timestamp": event.timestamp,
        }
        self.experience_buffer.append(experience)
        self.interaction_count += 1

        # Keep buffer bounded
        if len(self.experience_buffer) > 500:
            self.experience_buffer = self.experience_buffer[-500:]

    def should_replay(self) -> bool:
        """Check if it's time to trigger experience replay."""
        return (
            self.interaction_count > 0 and
            self.interaction_count % self.REPLAY_INTERVAL == 0 and
            len(self.experience_buffer) >= self.MINI_BATCH_SIZE
        )

    async def replay(self):
        """
        Run experience replay: sample mini-batch, update Q-values, persist.
        This is what was missing — the actual learning step.
        """
        if len(self.experience_buffer) < self.MINI_BATCH_SIZE:
            return

        logger.info(f"Running experience replay (buffer: {len(self.experience_buffer)}, interaction: {self.interaction_count})")

        # Sample mini-batch (most recent + random selection)
        import random
        recent = self.experience_buffer[-5:]  # Always include recent
        older = random.sample(
            self.experience_buffer[:-5],
            min(self.MINI_BATCH_SIZE - 5, len(self.experience_buffer) - 5)
        ) if len(self.experience_buffer) > 5 else []
        batch = recent + older

        # Update Q-values using TD(0) learning
        updates = 0
        for exp in batch:
            state = exp["state"]
            action = exp["action"]
            reward = exp["reward"]

            if state not in self.q_values:
                self.q_values[state] = {}
            if action not in self.q_values[state]:
                self.q_values[state][action] = 0.0

            # TD update: Q(s,a) += α * (r - Q(s,a))
            old_value = self.q_values[state][action]
            self.q_values[state][action] += self.LEARNING_RATE * (reward - old_value)
            updates += 1

        # Persist updated knowledge
        self._save_knowledge()
        logger.info(f"Experience replay complete: {updates} Q-value updates, {len(self.q_values)} states")

    def get_q_value(self, state: str, action: str) -> float:
        """Get Q-value for a state-action pair (used by router)."""
        return self.q_values.get(state, {}).get(action, 0.0)

    def get_best_action(self, state: str, available_actions: List[str]) -> Optional[str]:
        """Get the best action for a state based on Q-values."""
        if state not in self.q_values:
            return None

        state_values = self.q_values[state]
        valid_actions = {a: v for a, v in state_values.items() if a in available_actions}
        if not valid_actions:
            return None

        return max(valid_actions, key=valid_actions.get)

    def _extract_state(self, event: LearningEvent) -> str:
        """Extract a state representation from a learning event."""
        # State = intent class (simplified for now, can expand to features)
        query_lower = event.query.lower()
        if any(kw in query_lower for kw in ["price", "btc", "crypto", "stock", "market", "etf"]):
            return "market_research"
        elif any(kw in query_lower for kw in ["tax", "deduction", "irs", "entity", "llc", "s-corp"]):
            return "tax_strategy"
        elif any(kw in query_lower for kw in ["portfolio", "allocation", "risk", "invest", "holding"]):
            return "portfolio_analysis"
        elif any(kw in query_lower for kw in ["valuation", "dcf", "revenue", "cash flow", "ebitda"]):
            return "business_valuation"
        elif any(kw in query_lower for kw in ["report", "pdf", "brief", "memo", "deliverable"]):
            return "client_deliverable"
        else:
            return "general"


# ============================================================================
# SWARM MEMORY: Write routing outcomes so it stops being empty
# ============================================================================

class SwarmMemoryWriter:
    """
    Writes routing outcomes to swarm memory files.
    
    Why swarm memory is empty: because nothing writes to it.
    Now: After every successful route, update routing_success.json
    """

    def __init__(self, swarm_memory_dir: str):
        self.swarm_memory_dir = swarm_memory_dir
        self.routing_success_path = os.path.join(swarm_memory_dir, "routing_success.json")
        self.performance_path = os.path.join(swarm_memory_dir, "performance_history.json")
        self.shared_knowledge_path = os.path.join(swarm_memory_dir, "shared_knowledge.json")
        os.makedirs(swarm_memory_dir, exist_ok=True)

    def update_routing_success(self, intent_class: str, route: str, reward: float, success: bool):
        """Update routing success statistics."""
        try:
            data = {}
            if os.path.exists(self.routing_success_path):
                with open(self.routing_success_path, 'r') as f:
                    data = json.load(f)

            key = f"{intent_class}:{route}"
            if key not in data:
                data[key] = {
                    "intent_class": intent_class,
                    "route": route,
                    "total_attempts": 0,
                    "successes": 0,
                    "total_reward": 0.0,
                    "avg_reward": 0.0,
                    "last_updated": None,
                }

            entry = data[key]
            entry["total_attempts"] += 1
            if success:
                entry["successes"] += 1
            entry["total_reward"] += reward
            entry["avg_reward"] = entry["total_reward"] / entry["total_attempts"]
            entry["last_updated"] = datetime.utcnow().isoformat()

            with open(self.routing_success_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to update routing success: {e}")

    def update_performance_history(self, agent_id: str, event: LearningEvent):
        """Update performance history for an agent."""
        try:
            data = {}
            if os.path.exists(self.performance_path):
                with open(self.performance_path, 'r') as f:
                    data = json.load(f)

            if agent_id not in data:
                data[agent_id] = []

            data[agent_id].append({
                "metric_name": "consulting_reward",
                "metric_value": event.reward_breakdown.get("total_reward", 0.0),
                "context": {
                    "query_type": event.route_selected,
                    "latency": event.latency,
                    "tools_used": event.tools_used,
                },
                "timestamp": event.timestamp,
            })

            # Keep last 100 per agent
            data[agent_id] = data[agent_id][-100:]

            with open(self.performance_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to update performance history: {e}")


# ============================================================================
# MANDATORY LEARNING HOOK: The main integration point
# ============================================================================

class MandatoryLearningHook:
    """
    The mandatory post-response learning hook.
    
    This MUST be called after every response. No exceptions.
    It sits inside core/agent.py, not in a side module.
    
    Responsibilities:
        1. Record learning event (always)
        2. Calculate consulting-grade reward (always)
        3. Update swarm memory (always)
        4. Add to experience buffer (always)
        5. Trigger experience replay (every N interactions)
        6. Persist learning data (always)
    """

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Default: C:\Users\<user>\.torq_console
            data_dir = os.path.join(os.path.expanduser("~"), ".torq_console")

        self.data_dir = data_dir
        self.interactions_path = os.path.join(data_dir, "learning_system", "interactions.jsonl")
        self.knowledge_path = os.path.join(data_dir, "prince_flowers", "rl_knowledge_v2.json")
        self.swarm_memory_dir = os.path.join(data_dir, "swarm_memory")

        # Initialize subsystems
        self.replay_engine = ExperienceReplayEngine(self.knowledge_path)
        self.swarm_writer = SwarmMemoryWriter(self.swarm_memory_dir)

        # Ensure directories
        os.makedirs(os.path.dirname(self.interactions_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.knowledge_path), exist_ok=True)

        # Supabase writer (prod) — falls back to local if not configured
        self._supabase_writer = None
        try:
            from .supabase_learning import write_learning_event, upsert_routing_performance
            self._supabase_write = write_learning_event
            self._supabase_routing = upsert_routing_performance
            self._supabase_writer = True
            logger.info("Supabase learning writer available")
        except ImportError:
            self._supabase_write = None
            self._supabase_routing = None
            logger.info("Supabase writer not available — using local files only")

        logger.info("MandatoryLearningHook initialized — every response will produce a learning event")

    async def record_learning_event(
        self,
        trace_id: str,
        query: str,
        route_selected: str,
        tools_used: List[str],
        evidence_sources: List[str],
        latency: float,
        confidence: float,
        response_text: str,
        success: bool,
        error: Optional[str] = None,
        user_feedback: Optional[float] = None,
        policy_compliant: bool = True,
        numeric_values_valid: bool = True,
        hallucination_flags: int = 0,
    ) -> LearningEvent:
        """
        MANDATORY: Record a learning event after every response.
        
        This is called from process_query() in agent.py — ALWAYS.
        Not optional. Not conditional. Always.
        """
        # Step 1: Calculate consulting-grade reward
        evidence_completeness = min(len(evidence_sources) / 3.0, 1.0) if evidence_sources else 0.0
        if success and not evidence_sources:
            evidence_completeness = 0.6  # Baseline for successful responses without explicit sources

        reward = calculate_consulting_reward(
            evidence_sources=evidence_sources,
            evidence_completeness=evidence_completeness,
            routing_confidence=confidence,
            policy_compliance=policy_compliant,
            numeric_values_valid=numeric_values_valid,
            user_feedback=user_feedback,
            tool_errors=1 if error else 0,
            hallucination_flags=hallucination_flags,
            latency_seconds=latency,
            response_length=len(response_text),
        )

        outcome_score = 1.0 if success else 0.0

        # Step 2: Create learning event
        event = LearningEvent(
            trace_id=trace_id,
            query=query,
            route_selected=route_selected,
            tools_used=tools_used,
            evidence_sources=evidence_sources,
            latency=latency,
            confidence=confidence,
            outcome_score=outcome_score,
            reward_breakdown=reward,
            response_text=response_text,
            error=error,
            user_feedback=user_feedback,
        )

        # Step 3: Write to Supabase FIRST (prod), then local fallback
        supabase_ok = False
        if self._supabase_write:
            try:
                supabase_ok = await self._supabase_write(event.to_dict())
            except Exception as e:
                logger.error(f"Supabase write failed (falling back to local): {e}")

        # Step 3b: Append to local interactions log (always — backup in prod, primary in dev)
        self._append_interaction(event)

        if not supabase_ok and self._supabase_writer:
            logger.warning(f"Learning event {trace_id[:8]} only written locally — Supabase failed")

        # Step 4: Update swarm memory (always)
        state = self.replay_engine._extract_state(event)

        # Supabase routing performance (prod)
        if self._supabase_routing:
            try:
                await self._supabase_routing(
                    intent_class=state,
                    route=route_selected,
                    reward=reward["total_reward"],
                    success=success,
                )
            except Exception as e:
                logger.error(f"Supabase routing update failed: {e}")

        # Local swarm memory (always)
        self.swarm_writer.update_routing_success(
            intent_class=state,
            route=route_selected,
            reward=reward["total_reward"],
            success=success,
        )
        self.swarm_writer.update_performance_history("prince_flowers", event)

        # Step 5: Add to experience buffer (always)
        self.replay_engine.add_experience(event)

        # Step 6: Trigger experience replay if due (every N interactions)
        if self.replay_engine.should_replay():
            try:
                await self.replay_engine.replay()
            except Exception as e:
                logger.error(f"Experience replay failed (non-fatal): {e}")

        logger.info(
            f"Learning event recorded: trace={trace_id[:8]}, "
            f"route={route_selected}, reward={reward['total_reward']:.3f}, "
            f"success={success}"
        )

        return event

    def get_routing_q_value(self, query: str, route: str) -> float:
        """
        Get Q-value for a route given a query context.
        Used by the router to make Q-value-aware decisions.
        """
        # Create a temporary event just for state extraction
        temp_event = LearningEvent(
            trace_id="", query=query, route_selected=route,
            tools_used=[], evidence_sources=[], latency=0,
            confidence=0, outcome_score=0, reward_breakdown={},
            response_text="",
        )
        state = self.replay_engine._extract_state(temp_event)
        return self.replay_engine.get_q_value(state, route)

    def get_best_route(self, query: str, available_routes: List[str]) -> Optional[str]:
        """
        Get the best route for a query based on learned Q-values.
        Returns None if no learning data exists (fall back to policy).
        """
        temp_event = LearningEvent(
            trace_id="", query=query, route_selected="",
            tools_used=[], evidence_sources=[], latency=0,
            confidence=0, outcome_score=0, reward_breakdown={},
            response_text="",
        )
        state = self.replay_engine._extract_state(temp_event)
        return self.replay_engine.get_best_action(state, available_routes)

    def update_user_feedback(self, trace_id: str, feedback: float):
        """
        Update a learning event with user feedback (thumbs up/down).
        Called when user provides explicit feedback.
        """
        # TODO: Retroactively update the reward and re-record
        logger.info(f"User feedback received: trace={trace_id[:8]}, feedback={feedback}")

    def _append_interaction(self, event: LearningEvent):
        """Append learning event to JSONL log."""
        try:
            os.makedirs(os.path.dirname(self.interactions_path), exist_ok=True)
            with open(self.interactions_path, 'a') as f:
                f.write(json.dumps(event.to_dict(), default=str) + "\n")
        except Exception as e:
            logger.error(f"Failed to append interaction: {e}")

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get current learning statistics."""
        return {
            "total_interactions": self.replay_engine.interaction_count,
            "experience_buffer_size": len(self.replay_engine.experience_buffer),
            "q_value_states": len(self.replay_engine.q_values),
            "replay_interval": ExperienceReplayEngine.REPLAY_INTERVAL,
            "next_replay_in": (
                ExperienceReplayEngine.REPLAY_INTERVAL -
                (self.replay_engine.interaction_count % ExperienceReplayEngine.REPLAY_INTERVAL)
            ),
        }
