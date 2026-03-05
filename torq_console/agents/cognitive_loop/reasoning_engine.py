"""
Reasoning Engine for the TORQ Agent Cognitive Loop.

Interprets user intent and generates structured reasoning plans.
"""

import asyncio
import logging
import re
import time
from typing import Any, Dict, List, Optional

from .models import (
    CognitiveLoopConfig,
    IntentType,
    KnowledgeContext,
    ReasoningPlan,
    SessionContext,
)


logger = logging.getLogger(__name__)


class ReasoningEngine:
    """
    Interprets user queries and generates reasoning plans.

    The reasoning engine analyzes the user's intent, extracts key entities
    and concepts, and determines what tools might be needed.
    """

    # Intent detection patterns
    INTENT_PATTERNS = {
        IntentType.QUERY: [
            r"\b(what|how|why|when|where|who|which|explain|describe|tell me|show me)\b",
            r"\?",
            r"\b(define|meaning of|is|are)\b",
        ],
        IntentType.TASK: [
            r"\b(create|make|build|generate|write|produce|develop|implement)\b",
            r"\b(do|perform|execute|run|carry out)\b",
        ],
        IntentType.ANALYSIS: [
            r"\b(analyze|analysis|evaluate|assess|compare|contrast|review)\b",
            r"\b(what are the pros and cons|breakdown|break down)\b",
        ],
        IntentType.GENERATION: [
            r"\b(generate|create|make|write|produce|compose|draft)\b",
            r"\b(code|document|report|summary|content)\b",
        ],
        IntentType.RESEARCH: [
            r"\b(search|find|look for|research|investigate|explore|discover)\b",
            r"\b(latest|recent|current|trending|popular)\b",
        ],
    }

    # Complexity indicators
    COMPLEXITY_KEYWORDS = {
        "high": [
            "comprehensive", "detailed", "extensive", "complex", "advanced",
            "multi-step", "integrated", "comparative", "comparision"
        ],
        "medium": [
            "basic", "simple", "quick", "brief", "overview", "summary"
        ],
    }

    # Tool suggestions based on keywords
    TOOL_KEYWORDS = {
        "web_search": ["search", "find", "look up", "research", "latest", "news", "information"],
        "database": ["data", "records", "query", "table", "database", "fetch"],
        "file_operations": ["file", "read", "write", "save", "load", "document"],
        "code_execution": ["run", "execute", "test", "compile", "interpret"],
        "api_call": ["api", "endpoint", "request", "fetch", "web service"],
        "document_generation": ["generate", "create", "write", "document", "report"],
        "data_analysis": ["analyze", "calculate", "statistics", "metrics", "aggregate"],
    }

    def __init__(self, config: CognitiveLoopConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ReasoningEngine")

    async def reason(
        self,
        query: str,
        session_context: Optional[SessionContext] = None,
        knowledge_contexts: Optional[List[KnowledgeContext]] = None,
        **kwargs
    ) -> ReasoningPlan:
        """
        Generate a reasoning plan for the given query.

        Args:
            query: The user's query
            session_context: Current session context
            knowledge_contexts: Retrieved knowledge contexts
            **kwargs: Additional context

        Returns:
            ReasoningPlan with intent analysis and tool suggestions
        """
        start_time = time.time()

        # Detect intent
        intent, confidence = self._detect_intent(query)

        # Extract entities and concepts
        entities = self._extract_entities(query)
        concepts = self._extract_concepts(query)

        # Estimate complexity
        complexity = self._estimate_complexity(query, entities, concepts)

        # Determine if tools are needed
        requires_tools, suggested_tools = self._suggest_tools(query, intent, entities)

        # Generate reasoning explanation
        reasoning = self._generate_reasoning(
            query, intent, entities, concepts, requires_tools
        )

        # Enhance with knowledge contexts if available
        metadata = {}
        if knowledge_contexts:
            metadata["knowledge_count"] = len(knowledge_contexts)
            metadata["knowledge_sources"] = [k.source for k in knowledge_contexts]

        execution_time = time.time() - start_time

        plan = ReasoningPlan(
            intent=intent,
            intent_confidence=confidence,
            reasoning=reasoning,
            key_entities=entities,
            key_concepts=concepts,
            requires_tools=requires_tools,
            suggested_tools=suggested_tools,
            complexity_estimate=complexity,
            metadata={
                **metadata,
                "reasoning_time_seconds": execution_time,
                "query_length": len(query),
                "word_count": len(query.split()),
            }
        )

        self.logger.debug(
            f"Reasoning complete: intent={intent.value}, "
            f"confidence={confidence:.2f}, complexity={complexity:.2f}"
        )

        return plan

    def _detect_intent(self, query: str) -> tuple[IntentType, float]:
        """Detect the primary intent of the query."""
        query_lower = query.lower()

        scores = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    score += 1
            scores[intent] = score

        # Get the intent with the highest score
        max_score = max(scores.values())
        if max_score == 0:
            return IntentType.UNKNOWN, 0.0

        best_intent = max(scores, key=scores.get)
        confidence = min(max_score / len(self.INTENT_PATTERNS[best_intent]), 1.0)

        return best_intent, confidence

    def _extract_entities(self, query: str) -> List[str]:
        """Extract key entities from the query."""
        entities = []

        # Extract quoted strings
        quoted = re.findall(r'"([^"]+)"', query)
        entities.extend(quoted)

        # Extract capitalized phrases (potential proper nouns)
        capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', query)
        entities.extend(capitalized)

        # Extract numbers with units
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\s*(?:%|percent|seconds?|minutes?|hours?|days?)\b', query)
        entities.extend(numbers)

        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            entity_lower = entity.lower()
            if entity_lower not in seen and len(entity_lower) > 2:
                seen.add(entity_lower)
                unique_entities.append(entity)

        return unique_entities[:10]  # Limit to top 10 entities

    def _extract_concepts(self, query: str) -> List[str]:
        """Extract key concepts from the query."""
        # Common technical and domain concepts
        query_lower = query.lower()

        # Remove common words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "for",
            "to", "of", "in", "on", "at", "by", "with", "from", "as", "into",
            "through", "during", "before", "after", "above", "below", "between",
            "under", "again", "further", "then", "once", "here", "there", "when",
            "where", "why", "how", "all", "each", "few", "more", "most", "other",
            "some", "such", "no", "nor", "not", "only", "own", "same", "so",
            "than", "too", "very", "just", "but", "and", "or", "if"
        }

        # Tokenize and filter
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query_lower)
        concepts = [w for w in words if w not in stop_words]

        # Return unique concepts
        seen = set()
        unique_concepts = []
        for concept in concepts:
            if concept not in seen:
                seen.add(concept)
                unique_concepts.append(concept)

        return unique_concepts[:15]  # Limit to top 15 concepts

    def _estimate_complexity(
        self,
        query: str,
        entities: List[str],
        concepts: List[str]
    ) -> float:
        """Estimate the complexity of the query (0.0 to 1.0)."""
        complexity = 0.5  # Base complexity

        query_lower = query.lower()

        # Check for high complexity keywords
        for keyword in self.COMPLEXITY_KEYWORDS["high"]:
            if keyword in query_lower:
                complexity += 0.15
                break

        # Check for low complexity keywords
        for keyword in self.COMPLEXITY_KEYWORDS["medium"]:
            if keyword in query_lower:
                complexity -= 0.1
                break

        # Factor in query length
        word_count = len(query.split())
        if word_count > 30:
            complexity += 0.1
        elif word_count < 10:
            complexity -= 0.1

        # Factor in entity/concept count
        if len(entities) > 5:
            complexity += 0.1
        if len(concepts) > 10:
            complexity += 0.1

        # Factor in compound sentences
        if query.count(",") >= 2 or query.count(" and ") >= 2:
            complexity += 0.1

        return max(0.0, min(1.0, complexity))

    def _suggest_tools(
        self,
        query: str,
        intent: IntentType,
        entities: List[str]
    ) -> tuple[bool, List[str]]:
        """Suggest tools that might be needed."""
        query_lower = query.lower()
        suggested_tools = []

        for tool, keywords in self.TOOL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    if tool not in suggested_tools:
                        suggested_tools.append(tool)

        # Intent-based tool suggestions
        if intent == IntentType.RESEARCH and "web_search" not in suggested_tools:
            suggested_tools.append("web_search")
        elif intent == IntentType.ANALYSIS and "data_analysis" not in suggested_tools:
            suggested_tools.append("data_analysis")
        elif intent == IntentType.GENERATION and "document_generation" not in suggested_tools:
            suggested_tools.append("document_generation")

        # Check if tools are required
        requires_tools = (
            intent in (IntentType.RESEARCH, IntentType.GENERATION, IntentType.TASK) or
            len(suggested_tools) > 0
        )

        return requires_tools, suggested_tools[:5]  # Limit to 5 tools

    def _generate_reasoning(
        self,
        query: str,
        intent: IntentType,
        entities: List[str],
        concepts: List[str],
        requires_tools: bool
    ) -> str:
        """Generate a human-readable reasoning explanation."""
        parts = []

        # Intent explanation
        intent_explanations = {
            IntentType.QUERY: "This is a query seeking information",
            IntentType.TASK: "This is a request to perform a specific task",
            IntentType.ANALYSIS: "This requires analysis and evaluation",
            IntentType.GENERATION: "This requires generating new content",
            IntentType.RESEARCH: "This requires research and information gathering",
            IntentType.UNKNOWN: "The intent is not clearly specified",
        }
        parts.append(intent_explanations.get(intent, "Unknown intent"))

        # Entities mention
        if entities:
            parts.append(f"Key entities identified: {', '.join(entities[:5])}")

        # Tools mention
        if requires_tools:
            parts.append("External tools and resources are required")

        return ". ".join(parts) + "."

    async def emit_telemetry(
        self,
        phase: str,
        data: Dict[str, Any],
        run_id: Optional[str] = None
    ):
        """Emit telemetry for the reasoning phase."""
        if not self.config.telemetry_enabled:
            return

        try:
            from torq_console.core.telemetry.event import create_system_event
            from torq_console.core.telemetry.integration import get_telemetry_integration

            integration = get_telemetry_integration()
            await integration.record_agent_run(
                agent_name="reasoning_engine",
                agent_type="cognitive_loop",
                status="started",
                run_id=run_id,
                **{f"reasoning.{k}": v for k, v in data.items()}
            )
        except Exception as e:
            self.logger.warning(f"Failed to emit telemetry: {e}")
