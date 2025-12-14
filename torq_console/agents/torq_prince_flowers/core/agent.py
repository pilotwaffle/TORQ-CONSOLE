"""
Core TORQ Prince Flowers agent implementation.

This module contains the main agent class with initialization,
core functionality, and high-level reasoning strategies.
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from ..llm.providers.base import BaseLLMProvider
from .state import ReasoningMode, AgenticAction, ReasoningTrajectory, TORQAgentResult
from ..capabilities.reasoning import ReasoningEngine
from ..capabilities.planning import PlanningEngine
from ..capabilities.learning import LearningEngine
from ..integrations.mcp import MCPIntegrator
from ..tools.websearch import WebSearchTool
from ..tools.file_ops import FileOperationsTool
from ..utils.context import ContextManager
from ..utils.performance import PerformanceTracker


class TORQPrinceFlowers:
    """
    Enhanced Prince Flowers Agent with ARTIST-style Agentic RL for TORQ Console.

    Implements the complete agentic RL framework with:
    - Meta-learning for strategy selection
    - Tool composition and chaining
    - Self-correction and error recovery
    - Memory systems with intelligent retrieval
    - Performance optimization through experience replay
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None, config: Dict[str, Any] = None):
        """Initialize the enhanced Prince Flowers agent."""
        self.agent_name = "Prince Flowers Enhanced"
        self.agent_id = "torq_prince_flowers"
        self.version = "2.1.0"

        self.llm_provider = llm_provider
        self.config = config or {}
        self.logger = logging.getLogger(f"TORQPrinceFlowers.{self.agent_id}")

        # Core system prompt
        self.system_prompt = self._build_system_prompt()

        # Initialize core components
        self.reasoning_engine = ReasoningEngine(self.llm_provider)
        self.planning_engine = PlanningEngine()
        self.learning_engine = LearningEngine()
        self.mcp_integrator = MCPIntegrator()

        # Initialize tools
        self.web_search_tool = WebSearchTool()
        self.file_operations_tool = FileOperationsTool()

        # Initialize utilities
        self.context_manager = ContextManager()
        self.performance_tracker = PerformanceTracker()

        # Performance tracking
        self.active_since = time.time()
        self.total_queries = 0
        self.successful_responses = 0
        self.trajectory_history: List[ReasoningTrajectory] = []

        # Learning persistence
        self.learning_data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            ".torq-data", "prince_learning.json"
        )
        self._ensure_data_directory()
        self.load_learning_state()

        self.logger.info(f"TORQ Prince Flowers Enhanced v{self.version} initialized")

    def _build_system_prompt(self) -> str:
        """Build the core system prompt for the agent."""
        return """You are Prince Flowers Code, an advanced AI assistant integrated with TORQ Console.

# CORE IDENTITY & CAPABILITIES

You are a highly capable AI assistant with expertise in:
- Software development, architecture, and best practices
- Web search, research, and information synthesis
- Analysis, problem-solving, and strategic thinking
- Task management and project planning
- Code generation with security and quality focus

# OPERATIONAL GUIDELINES

## 1. Communication Style
- Be direct, concise, and task-focused
- Provide clear, actionable responses
- Use technical precision when appropriate
- Adapt communication to user's expertise level

## 2. Security & Safety
- NEVER execute potentially harmful operations without explicit confirmation
- Validate all inputs and outputs for security implications
- Follow secure coding practices in all generated code
- Refuse malicious requests politely but firmly

## 3. Task Execution
- Break complex tasks into manageable steps
- Provide progress updates for long-running operations
- Handle errors gracefully with clear explanations
- Suggest alternatives when primary approach fails

## 4. Quality Standards
- Generate production-ready code with proper error handling
- Include relevant documentation and comments
- Follow language-specific best practices and conventions
- Optimize for readability, maintainability, and performance

## 5. Research & Analysis
- Synthesize information from multiple sources
- Provide citations and source reliability assessment
- Distinguish between facts, opinions, and speculation
- Update knowledge with latest information when requested

# ROLE-BASED CONFIGURATIONS

You operate in multiple modes depending on the task:

**Research Mode**: Web search → Content analysis → Synthesis
- Multi-source information gathering
- Quality assessment and validation
- Comprehensive response generation

**Analysis Mode**: Problem analysis → Pattern recognition → Recommendations
- Deep technical analysis
- Comparative evaluation
- Strategic recommendations

**Composition Mode**: Planning → Multi-step execution → Integration
- Complex task orchestration
- Tool chaining and coordination
- Adaptive error recovery

**Direct Mode**: Immediate response generation
- Quick queries and simple tasks
- Conversational interactions
- Status and help requests

# INTERACTION PATTERNS

## Command Formats
- Direct queries: Process immediately
- "prince search [query]": Research mode with web search
- "prince analyze [topic]": Deep analysis mode
- "prince help": System capabilities and guidance

## Response Structure
1. **Acknowledge**: Confirm understanding of request
2. **Execute**: Perform required operations
3. **Report**: Provide results with context
4. **Suggest**: Offer next steps or improvements

## Error Handling
- Identify error cause clearly
- Suggest specific corrective actions
- Provide workarounds when available
- Escalate to user when intervention needed

# LEARNING & ADAPTATION

- Track performance metrics for continuous improvement
- Learn from user feedback and corrections
- Adapt strategies based on success patterns
- Maintain context across conversation

# INTEGRATION WITH TORQ CONSOLE

- Seamless integration with MCP (Model Context Protocol)
- Access to TORQ Console's enhanced features
- Coordination with other AI providers when beneficial
- Full context awareness of development environment

# RESPONSE QUALITY CHECKLIST

Before providing any response, ensure:
✓ Accuracy: Information is correct and up-to-date
✓ Completeness: All aspects of query addressed
✓ Clarity: Response is easy to understand
✓ Actionability: User knows what to do next
✓ Safety: No security risks or harmful guidance

Remember: Your goal is to be maximally helpful while maintaining the highest standards of quality, security, and user satisfaction."""

    async def process_query(self, query: str, context: Dict[str, Any] = None) -> TORQAgentResult:
        """
        Main entry point for processing user queries.

        Args:
            query: The user's query or command
            context: Additional context for the query

        Returns:
            TORQAgentResult with the response and metadata
        """
        start_time = time.time()

        # Initialize trajectory for tracking
        trajectory = ReasoningTrajectory(
            query=query,
            start_time=datetime.now(),
            context=context or {}
        )

        try:
            self.total_queries += 1

            # Enhanced query analysis with intent detection
            analysis = await self.reasoning_engine.analyze_query(query, context)
            trajectory.context.update(analysis)

            # Select reasoning mode
            reasoning_mode = await self.reasoning_engine.select_reasoning_mode(
                analysis, trajectory
            )
            trajectory.mode = reasoning_mode

            # Execute reasoning strategy
            result = await self.reasoning_engine.execute_reasoning_strategy(
                reasoning_mode, query, analysis, trajectory, context
            )

            # Calculate execution time
            execution_time = time.time() - start_time

            # Mark trajectory as successful
            trajectory.mark_complete(True, result.get('response', ''))

            # Update learning systems
            await self.learning_engine.update_learning_systems(
                trajectory, analysis, True
            )

            # Create result
            agent_result = TORQAgentResult(
                success=True,
                response=result.get('response', ''),
                trajectory=trajectory,
                metadata=result.get('metadata', {}),
                tools_used=result.get('tools_used', []),
                confidence=result.get('confidence', 0.0),
                execution_time=execution_time,
                reasoning_summary=result.get('reasoning_summary', '')
            )

            self.successful_responses += 1
            self.trajectory_history.append(trajectory)

            return agent_result

        except Exception as e:
            execution_time = time.time() - start_time

            # Mark trajectory as failed
            trajectory.mark_complete(False, str(e))

            # Log error
            self.logger.error(f"Error processing query '{query}': {e}")

            # Analyze failure for learning
            await self._analyze_failure(trajectory, e)

            # Return error result
            return TORQAgentResult(
                success=False,
                response=f"An error occurred while processing your request: {str(e)}",
                trajectory=trajectory,
                error=str(e),
                execution_time=execution_time
            )

    async def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check of the agent."""
        try:
            # Check core components
            components_status = {
                "reasoning_engine": await self.reasoning_engine.health_check(),
                "planning_engine": await self.planning_engine.health_check(),
                "learning_engine": await self.learning_engine.health_check(),
                "mcp_integrator": await self.mcp_integrator.health_check(),
                "web_search_tool": await self.web_search_tool.health_check(),
                "file_operations_tool": await self.file_operations_tool.health_check(),
            }

            # Calculate overall health
            healthy_components = sum(
                1 for status in components_status.values()
                if status.get('healthy', False)
            )
            overall_health = healthy_components / len(components_status)

            # Performance metrics
            performance_metrics = self.performance_tracker.get_metrics()

            return {
                "agent_id": self.agent_id,
                "version": self.version,
                "healthy": overall_health >= 0.8,
                "overall_health_score": overall_health,
                "components": components_status,
                "performance": performance_metrics,
                "statistics": {
                    "active_since": self.active_since,
                    "total_queries": self.total_queries,
                    "successful_responses": self.successful_responses,
                    "success_rate": self.successful_responses / max(self.total_queries, 1),
                    "trajectory_count": len(self.trajectory_history)
                },
                "timestamp": time.time()
            }

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "agent_id": self.agent_id,
                "healthy": False,
                "error": str(e),
                "timestamp": time.time()
            }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and statistics."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "version": self.version,
            "active_since": self.active_since,
            "uptime_seconds": time.time() - self.active_since,
            "total_queries": self.total_queries,
            "successful_responses": self.successful_responses,
            "success_rate": self.successful_responses / max(self.total_queries, 1),
            "trajectory_count": len(self.trajectory_history),
            "available_tools": list(self.web_search_tool.get_available_tools()),
            "learning_engine_status": self.learning_engine.get_status(),
            "memory_usage": self.performance_tracker.get_memory_usage(),
            "last_update": time.time()
        }

    def get_capabilities_description(self) -> str:
        """Get a description of agent capabilities."""
        capabilities = [
            "🔍 **Advanced Web Search**: Multi-source search with content extraction and analysis",
            "🤖 **Intelligent Reasoning**: Multiple reasoning modes (Research, Analysis, Composition, Meta-Planning)",
            "🛠️ **Dynamic Tool Composition**: Automated tool selection and chaining",
            "📊 **Performance Learning**: Continuous learning from experience and user feedback",
            "🔒 **Security-First**: Comprehensive security controls and validation",
            "💾 **Memory Systems**: Intelligent context management and information retrieval",
            "🎯 **Meta-Planning**: Strategic planning and adaptive execution",
            "🔄 **Self-Correction**: Automatic error detection and correction",
            "📈 **Performance Optimization**: Experience replay and strategy refinement"
        ]

        return "## TORQ Prince Flowers Enhanced Capabilities\n\n" + "\n".join(capabilities)

    def _ensure_data_directory(self):
        """Ensure the data directory exists for learning persistence."""
        data_dir = os.path.dirname(self.learning_data_path)
        os.makedirs(data_dir, exist_ok=True)

    def save_learning_state(self, filepath: str = None):
        """Save the current learning state to disk."""
        target_path = filepath or self.learning_data_path

        try:
            learning_state = {
                "version": self.version,
                "timestamp": time.time(),
                "statistics": {
                    "total_queries": self.total_queries,
                    "successful_responses": self.successful_responses,
                    "trajectory_count": len(self.trajectory_history)
                },
                "learning_data": self.learning_engine.export_learning_data(),
                "trajectory_summaries": [
                    t.get_execution_summary() for t in self.trajectory_history[-100:]  # Last 100 trajectories
                ]
            }

            with open(target_path, 'w') as f:
                json.dump(learning_state, f, indent=2, default=str)

            self.logger.info(f"Learning state saved to {target_path}")

        except Exception as e:
            self.logger.error(f"Failed to save learning state: {e}")

    def load_learning_state(self, filepath: str = None):
        """Load learning state from disk."""
        target_path = filepath or self.learning_data_path

        try:
            if os.path.exists(target_path):
                with open(target_path, 'r') as f:
                    learning_state = json.load(f)

                # Restore statistics
                stats = learning_state.get("statistics", {})
                self.total_queries = stats.get("total_queries", 0)
                self.successful_responses = stats.get("successful_responses", 0)

                # Restore learning data
                if "learning_data" in learning_state:
                    self.learning_engine.import_learning_data(learning_state["learning_data"])

                self.logger.info(f"Learning state loaded from {target_path}")
            else:
                self.logger.info("No existing learning state found, starting fresh")

        except Exception as e:
            self.logger.error(f"Failed to load learning state: {e}")

    async def _analyze_failure(self, trajectory: ReasoningTrajectory, error: Exception):
        """Analyze a failure for learning and improvement."""
        try:
            failure_analysis = {
                "query": trajectory.query,
                "mode": trajectory.mode.value,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "actions_taken": len(trajectory.actions),
                "execution_time": trajectory.total_time,
                "timestamp": time.time()
            }

            # Add to learning data
            await self.learning_engine.record_failure(failure_analysis)

        except Exception as e:
            self.logger.error(f"Failed to analyze failure: {e}")