"""
Learning Signal Service

Orchestrates signal extraction from evaluations, workspace entries, and syntheses.
Two-pass approach:
1. Deterministic heuristic rules extract explicit patterns
2. LLM-assisted summarization for clusters worth synthesizing
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict

from .models import (
    LearningSignalCreate,
    LearningSignalRead,
    LearningSignalUpdate,
    ExtractionResult,
    ExtractionContext,
    AggregatedSignal,
    LearningSignalType,
    SignalStrength,
    SignalSource,
)
from .rules import (
    DEFAULT_EXTRACTION_RULES,
    get_default_rule_configs,
    BaseExtractionRule,
)


logger = logging.getLogger(__name__)


class LearningSignalService:
    """
    Service for extracting and managing learning signals.

    The learning signal engine operates in two passes:

    Pass 1 (Deterministic):
    - Run extraction rules on evaluations, entries, syntheses
    - Generate explicit signals for patterns that meet thresholds
    - All signals are explainable and grounded in observable data

    Pass 2 (LLM-Assisted, optional):
    - Cluster related signals
    - Generate higher-level synthesis of signal themes
    - Propose aggregated adaptations
    """

    def __init__(self, supabase_client, llm_client=None):
        """
        Initialize the learning signal service.

        Args:
            supabase_client: Database client for persistence
            llm_client: Optional LLM client for signal summarization
        """
        self.supabase = supabase_client
        self.llm = llm_client

        # Load extraction rules
        self.rule_configs = get_default_rule_configs()
        self.rules: dict[LearningSignalType, BaseExtractionRule] = {}

        # Initialize rule instances
        for rule_class in DEFAULT_EXTRACTION_RULES:
            signal_type = rule_class.__name__.replace("Rule", "")
            # Map class name to signal type
            for signal_type_enum in LearningSignalType:
                if signal_type_enum.value in signal_type.lower():
                    config = self.rule_configs.get(signal_type_enum)
                    if config:
                        self.rules[signal_type_enum] = rule_class(config)
                        break

        logger.info(f"Loaded {len(self.rules)} extraction rules")

    # ========================================================================
    # Signal Extraction (Two-Pass)
    # ========================================================================

    async def extract_signals(
        self,
        context: ExtractionContext,
        use_llm_summarization: bool = False
    ) -> ExtractionResult:
        """
        Extract learning signals using two-pass approach.

        Pass 1: Run deterministic extraction rules
        Pass 2: Optionally use LLM to cluster and summarize
        """
        start_time = time.time()

        # Fetch data within time window
        time_threshold = datetime.now() - timedelta(hours=context.time_window_hours)

        evaluations = await self._fetch_evaluations(context, time_threshold)
        workspace_entries = await self._fetch_workspace_entries(context, time_threshold)
        syntheses = await self._fetch_syntheses(context, time_threshold)
        executions = await self._fetch_executions(context, time_threshold)

        # Pass 1: Deterministic extraction
        detected_signals = await self._deterministic_pass(
            evaluations, workspace_entries, syntheses, executions
        )

        # Pass 2: LLM summarization (optional)
        if use_llm_summarization and self.llm and detected_signals:
            await self._llm_summarization_pass(detected_signals)

        duration_ms = int((time.time() - start_time) * 1000)

        # Persist signals
        for signal in detected_signals:
            await self._persist_signal(signal)

        result = ExtractionResult(
            signals_detected=detected_signals,
            execution_analyzed=len(executions),
            entries_analyzed=len(workspace_entries),
            evaluations_analyzed=len(evaluations),
            extraction_duration_ms=duration_ms
        )

        logger.info(
            f"Signal extraction complete: {len(detected_signals)} signals "
            f"from {len(executions)} executions in {duration_ms}ms"
        )

        return result

    async def _deterministic_pass(
        self,
        evaluations: List[Dict[str, Any]],
        workspace_entries: List[Dict[str, Any]],
        syntheses: List[Dict[str, Any]],
        executions: List[Dict[str, Any]]
    ) -> List[LearningSignalCreate]:
        """Run deterministic extraction rules."""
        all_signals = []

        for signal_type, rule in self.rules.items():
            try:
                signals = rule.extract(evaluations, workspace_entries, syntheses, executions)
                all_signals.extend(signals)
                logger.debug(f"Rule {signal_type.value} extracted {len(signals)} signals")
            except Exception as e:
                logger.error(f"Error in rule {signal_type.value}: {e}")
                continue

        # Deduplicate signals by type + scope
        unique_signals = self._deduplicate_signals(all_signals)
        logger.info(f"Deterministic pass extracted {len(unique_signals)} unique signals")

        return unique_signals

    async def _llm_summarization_pass(
        self,
        signals: List[LearningSignalCreate]
    ) -> None:
        """Use LLM to cluster and summarize signals."""
        if not signals:
            return

        # Group signals by scope
        signals_by_scope = defaultdict(list)
        for signal in signals:
            key = f"{signal.scope_type}:{signal.scope_id}"
            signals_by_scope[key].append(signal)

        # For each scope with multiple signals, generate a summary
        for scope_key, scope_signals in signals_by_scope.items():
            if len(scope_signals) < 2:
                continue

            try:
                summary = await self._generate_signal_summary(scope_signals)
                if summary:
                    # Could store this as a meta-signal or add to metadata
                    logger.info(f"Generated LLM summary for {scope_key}: {summary[:100]}...")
            except Exception as e:
                logger.error(f"Error generating LLM summary for {scope_key}: {e}")

    async def _generate_signal_summary(self, signals: List[LearningSignalCreate]) -> Optional[str]:
        """Generate an LLM-based summary of clustered signals."""
        if not self.llm:
            return None

        signal_descriptions = "\n".join([
            f"- {s.signal_type.value}: {s.description}"
            for s in signals
        ])

        prompt = f"""The following learning signals were extracted from agent executions:

{signal_descriptions}

Provide a concise 2-3 sentence summary of the main themes and suggested actions.
Focus on the most impactful changes that would improve agent performance."""

        try:
            response = await self.llm.generate(prompt, max_tokens=200)
            return response.strip() if response else None
        except Exception as e:
            logger.warning(f"LLM summarization failed: {e}")
            return None

    # ========================================================================
    # Data Fetching
    # ========================================================================

    async def _fetch_evaluations(
        self,
        context: ExtractionContext,
        since: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch evaluation data for signal extraction."""
        try:
            query = self.supabase.table("execution_evaluations").select("*")
            query = query.gte("created_at", since.isoformat())

            if context.agent_id:
                query = query.eq("agent_id", context.agent_id)
            if context.workflow_id:
                query = query.eq("workflow_id", context.workflow_id)

            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching evaluations: {e}")
            return []

    async def _fetch_workspace_entries(
        self,
        context: ExtractionContext,
        since: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch workspace entries, prioritizing high-value entries."""
        try:
            # Use the high_value view if available, otherwise fall back to table
            try:
                query = self.supabase.table("high_value_working_memory_entries").select("*")
            except Exception:
                # View doesn't exist, use table with filters
                query = self.supabase.table("working_memory_entries").select("*")
                query = query.in_("importance", ["high", "critical"])

            query = query.gte("created_at", since.isoformat())
            query = query.order("created_at", desc=True)
            query = query.limit(1000)  # Reasonable limit

            if context.agent_id:
                query = query.eq("agent_id", context.agent_id)
            if context.workflow_id:
                query = query.eq("workflow_id", context.workflow_id)

            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching workspace entries: {e}")
            return []

    async def _fetch_syntheses(
        self,
        context: ExtractionContext,
        since: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch synthesis outputs for signal extraction."""
        try:
            query = self.supabase.table("workspace_syntheses").select("*")
            query = query.gte("created_at", since.isoformat())

            # Focus on synthesis types that reveal patterns
            query = query.in_("synthesis_type", ["contradictions", "risks", "insights"])

            if context.agent_id:
                query = query.eq("agent_id", context.agent_id)
            if context.workflow_id:
                query = query.eq("workflow_id", context.workflow_id)

            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching syntheses: {e}")
            return []

    async def _fetch_executions(
        self,
        context: ExtractionContext,
        since: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch execution data for correlation."""
        try:
            query = self.supabase.table("task_executions").select("*")
            query = query.gte("created_at", since.isoformat())

            if context.agent_id:
                query = query.eq("agent_id", context.agent_id)
            if context.workflow_id:
                query = query.eq("workflow_id", context.workflow_id)

            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching executions: {e}")
            return []

    # ========================================================================
    # Signal Management
    # ========================================================================

    def _deduplicate_signals(
        self,
        signals: List[LearningSignalCreate]
    ) -> List[LearningSignalCreate]:
        """Deduplicate signals by type + scope."""
        seen = {}
        unique = []

        for signal in signals:
            key = (signal.signal_type, signal.scope_type, signal.scope_id)

            if key in seen:
                # Merge evidence
                existing = seen[key]
                existing.evidence_count += signal.evidence_count
                existing.supporting_execution_ids.extend(signal.supporting_execution_ids)
                # Keep strongest strength
                if self._strength_value(signal.strength) > self._strength_value(existing.strength):
                    existing.strength = signal.strength
            else:
                seen[key] = signal
                unique.append(signal)

        return unique

    def _strength_value(self, strength: SignalStrength) -> int:
        """Get numeric value for strength comparison."""
        values = {
            SignalStrength.WEAK: 0,
            SignalStrength.MODERATE: 1,
            SignalStrength.STRONG: 2,
            SignalStrength.CONCLUSIVE: 3
        }
        return values.get(strength, 0)

    async def _persist_signal(self, signal: LearningSignalCreate) -> str:
        """Persist a learning signal to the database."""
        try:
            # Check for existing similar signal
            existing = await self._find_existing_signal(signal)

            payload = signal.model_dump()

            if existing:
                # Update existing signal
                signal_id = existing.get("signal_id")

                # Merge evidence
                new_evidence_count = existing.get("evidence_count", 0) + signal.evidence_count
                new_supporting = existing.get("supporting_execution_ids", []) + signal.supporting_execution_ids

                update_data = {
                    "evidence_count": new_evidence_count,
                    "supporting_execution_ids": list(set(new_supporting)),
                    "updated_at": datetime.now().isoformat()
                }

                self.supabase.table("learning_signals").update(update_data).eq("signal_id", signal_id).execute()

                logger.debug(f"Updated signal {signal_id} with new evidence")
                return signal_id
            else:
                # Create new signal
                payload["status"] = "pending"
                payload["created_at"] = datetime.now().isoformat()
                payload["updated_at"] = datetime.now().isoformat()

                result = self.supabase.table("learning_signals").insert(payload).execute()

                if result.data:
                    signal_id = result.data[0].get("signal_id")
                    logger.debug(f"Created new signal {signal_id}")
                    return signal_id

        except Exception as e:
            logger.error(f"Error persisting signal: {e}")

        return ""

    async def _find_existing_signal(
        self,
        signal: LearningSignalCreate
    ) -> Optional[Dict[str, Any]]:
        """Find an existing similar signal."""
        try:
            query = self.supabase.table("learning_signals").select("*")
            query = query.eq("signal_type", signal.signal_type.value)
            query = query.eq("scope_type", signal.scope_type)
            query = query.eq("scope_id", signal.scope_id)
            query = query.in_("status", ["pending", "acknowledged"])
            query = query.order("created_at", desc=True)
            query = query.limit(1)

            result = query.execute()
            return result.data[0] if result.data else None
        except Exception:
            return None

    # ========================================================================
    # Signal Query API
    # ========================================================================

    async def get_signals(
        self,
        scope_type: Optional[str] = None,
        scope_id: Optional[str] = None,
        signal_type: Optional[LearningSignalType] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[LearningSignalRead]:
        """Query learning signals with filters."""
        try:
            query = self.supabase.table("learning_signals").select("*")

            if scope_type:
                query = query.eq("scope_type", scope_type)
            if scope_id:
                query = query.eq("scope_id", scope_id)
            if signal_type:
                query = query.eq("signal_type", signal_type.value)
            if status:
                query = query.eq("status", status)

            query = query.order("created_at", desc=True)
            query = query.limit(limit)

            result = query.execute()

            signals = []
            for item in result.data or []:
                try:
                    signals.append(LearningSignalRead.model_validate(item))
                except Exception:
                    continue

            return signals

        except Exception as e:
            logger.error(f"Error querying signals: {e}")
            return []

    async def get_signal(self, signal_id: str) -> Optional[LearningSignalRead]:
        """Get a specific learning signal."""
        try:
            query = self.supabase.table("learning_signals").select("*")
            query = query.eq("signal_id", signal_id)
            query = query.limit(1)

            result = query.execute()

            if result.data:
                return LearningSignalRead.model_validate(result.data[0])

        except Exception as e:
            logger.error(f"Error getting signal {signal_id}: {e}")

        return None

    async def update_signal(
        self,
        signal_id: str,
        update: LearningSignalUpdate
    ) -> Optional[LearningSignalRead]:
        """Update a learning signal."""
        try:
            payload = {k: v for k, v in update.model_dump().items() if v is not None}
            payload["updated_at"] = datetime.now().isoformat()

            result = self.supabase.table("learning_signals").update(payload).eq("signal_id", signal_id).execute()

            if result.data:
                return LearningSignalRead.model_validate(result.data[0])

        except Exception as e:
            logger.error(f"Error updating signal {signal_id}: {e}")

        return None

    async def acknowledge_signal(self, signal_id: str) -> bool:
        """Mark a signal as acknowledged."""
        return await self._set_signal_status(signal_id, "acknowledged")

    async def incorporate_signal(self, signal_id: str) -> bool:
        """Mark a signal as incorporated into behavior."""
        return await self._set_signal_status(signal_id, "incorporated")

    async def reject_signal(self, signal_id: str) -> bool:
        """Mark a signal as rejected."""
        return await self._set_signal_status(signal_id, "rejected")

    async def _set_signal_status(self, signal_id: str, status: str) -> bool:
        """Set signal status."""
        try:
            self.supabase.table("learning_signals").update({
                "status": status,
                "updated_at": datetime.now().isoformat()
            }).eq("signal_id", signal_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error setting signal status: {e}")
            return False

    # ========================================================================
    # Signal Aggregation
    # ========================================================================

    async def aggregate_signals(
        self,
        scope_type: Optional[str] = None,
        scope_id: Optional[str] = None
    ) -> List[AggregatedSignal]:
        """Aggregate related signals into higher-level patterns."""
        signals = await self.get_signals(scope_type=scope_type, scope_id=scope_id, status="pending")

        # Group by signal type + scope
        groups = defaultdict(list)
        for signal in signals:
            key = (signal.signal_type, signal.scope_type, signal.scope_id)
            groups[key].append(signal)

        aggregated = []
        for (signal_type, st, sid), group_signals in groups.items():
            if len(group_signals) < 2:
                continue

            total_evidence = sum(s.evidence_count for s in group_signals)
            unique_executions = set()
            for s in group_signals:
                unique_executions.update(s.supporting_execution_ids)

            # Determine strength from aggregated evidence
            if total_evidence >= 10:
                strength = SignalStrength.CONCLUSIVE
            elif total_evidence >= 6:
                strength = SignalStrength.STRONG
            elif total_evidence >= 3:
                strength = SignalStrength.MODERATE
            else:
                strength = SignalStrength.WEAK

            aggregated.append(AggregatedSignal(
                signal_type=signal_type,
                scope_type=st,
                scope_id=sid,
                total_evidence=total_evidence,
                unique_executions=len(unique_executions),
                strength=strength,
                first_observed=min(s.created_at for s in group_signals),
                last_observed=max(s.created_at for s in group_signals),
                representative_signals=[s.signal_id for s in group_signals[:3]]
            ))

        return sorted(aggregated, key=lambda x: x.total_evidence, reverse=True)
