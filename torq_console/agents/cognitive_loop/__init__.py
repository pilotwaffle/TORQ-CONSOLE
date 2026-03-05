"""
TORQ Agent Cognitive Loop System

Implements the autonomous reasoning cycle: Reason -> Retrieve -> Plan -> Act -> Evaluate -> Learn

This system transforms TORQ from a stateless assistant into a compounding intelligence platform.
"""

from .models import (
    CognitiveLoopConfig,
    ReasoningPlan,
    ExecutionPlan,
    ExecutionStep,
    ExecutionResult,
    EvaluationResult,
    LearningEvent,
    CognitiveLoopResult,
    CognitiveLoopStatus,
    KnowledgeContext,
    ToolCallResult
)

from .reasoning_engine import ReasoningEngine
from .knowledge_retriever import KnowledgeRetriever
from .planner import Planner
from .tool_executor import ToolExecutor
from .evaluator import Evaluator
from .learning_writer import LearningWriter
from .cognitive_loop import CognitiveLoop
from .config import get_cognitive_config

__all__ = [
    # Models
    'CognitiveLoopConfig',
    'ReasoningPlan',
    'ExecutionPlan',
    'ExecutionStep',
    'ExecutionResult',
    'EvaluationResult',
    'LearningEvent',
    'CognitiveLoopResult',
    'CognitiveLoopStatus',
    'KnowledgeContext',
    'ToolCallResult',
    # Core components
    'ReasoningEngine',
    'KnowledgeRetriever',
    'Planner',
    'ToolExecutor',
    'Evaluator',
    'LearningWriter',
    'CognitiveLoop',
    # Configuration
    'get_cognitive_config',
    # Factory function
    'create_cognitive_loop',
]


def create_cognitive_loop(
    agent_id: str = "torq_agent",
    config: CognitiveLoopConfig | None = None
) -> CognitiveLoop:
    """Factory function to create a cognitive loop instance."""
    from ..config import get_agent_config
    from ..llm.providers.base import BaseLLMProvider

    cfg = config or get_cognitive_config()

    # Create components
    reasoning_engine = ReasoningEngine(config=cfg)
    knowledge_retriever = KnowledgeRetriever(config=cfg)
    planner = Planner(config=cfg)
    tool_executor = ToolExecutor(config=cfg)
    evaluator = Evaluator(config=cfg)
    learning_writer = LearningWriter(config=cfg)

    return CognitiveLoop(
        agent_id=agent_id,
        reasoning_engine=reasoning_engine,
        knowledge_retriever=knowledge_retriever,
        planner=planner,
        tool_executor=tool_executor,
        evaluator=evaluator,
        learning_writer=learning_writer,
        config=cfg
    )
