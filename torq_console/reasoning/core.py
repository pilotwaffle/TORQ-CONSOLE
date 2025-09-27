#!/usr/bin/env python3
"""
TORQ Console Chain-of-Thought (CoT) Reasoning Core Framework

This module implements the foundational classes for Chain-of-Thought reasoning
that enhances all 4 phases of TORQ Console development methodology.

Classes:
    ReasoningStep: Individual step in a reasoning chain
    ReasoningChain: Container for multiple reasoning steps
    CoTReasoning: Main framework for Chain-of-Thought processing
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    """Types of reasoning supported by the CoT framework."""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    DECISION = "decision"
    PROBLEM_SOLVING = "problem_solving"
    VALIDATION = "validation"
    SYNTHESIS = "synthesis"
    PLANNING = "planning"
    EXECUTION = "execution"


class StepStatus(Enum):
    """Status of individual reasoning steps."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ReasoningStep:
    """
    Individual step in a Chain-of-Thought reasoning process.

    Attributes:
        step_id: Unique identifier for the step
        description: Human-readable description of what this step does
        reasoning: The logical reasoning for this step
        action: Function or method to execute for this step
        inputs: Input data for the step
        outputs: Results from executing the step
        confidence: Confidence score (0.0 - 1.0) for this step
        dependencies: List of step_ids that must complete before this step
        validation_criteria: Criteria for validating step success
        status: Current status of the step
        start_time: When step execution began
        end_time: When step execution completed
        execution_time: Time taken to execute (in seconds)
        metadata: Additional metadata for the step
    """
    step_id: str
    description: str
    reasoning: str
    action: Optional[Callable] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    dependencies: List[str] = field(default_factory=list)
    validation_criteria: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate step configuration after initialization."""
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

        if not self.step_id or not self.description:
            raise ValueError("step_id and description are required")

    async def execute(self) -> bool:
        """
        Execute this reasoning step.

        Returns:
            bool: True if execution was successful, False otherwise
        """
        try:
            self.status = StepStatus.IN_PROGRESS
            self.start_time = datetime.now()

            logger.debug(f"Executing reasoning step: {self.step_id}")

            if self.action:
                if asyncio.iscoroutinefunction(self.action):
                    self.outputs = await self.action(**self.inputs)
                else:
                    self.outputs = self.action(**self.inputs)

            self.end_time = datetime.now()
            self.execution_time = (self.end_time - self.start_time).total_seconds()
            self.status = StepStatus.COMPLETED

            logger.debug(f"Step {self.step_id} completed in {self.execution_time:.2f}s")
            return True

        except Exception as e:
            self.status = StepStatus.FAILED
            self.error_message = str(e)
            self.end_time = datetime.now()
            if self.start_time:
                self.execution_time = (self.end_time - self.start_time).total_seconds()

            logger.error(f"Step {self.step_id} failed: {e}")
            return False

    def validate(self) -> bool:
        """
        Validate that this step meets its success criteria.

        Returns:
            bool: True if validation passes, False otherwise
        """
        if self.status != StepStatus.COMPLETED:
            return False

        # Check if outputs meet validation criteria
        for criterion in self.validation_criteria:
            # Simple validation - can be enhanced with more sophisticated logic
            if criterion not in str(self.outputs):
                logger.warning(f"Step {self.step_id} failed validation: {criterion}")
                return False

        return True


@dataclass
class ReasoningChain:
    """
    Container for a sequence of reasoning steps that form a complete thought process.

    Attributes:
        chain_id: Unique identifier for the reasoning chain
        title: Human-readable title for the reasoning process
        reasoning_type: Type of reasoning this chain performs
        steps: List of reasoning steps in execution order
        context: Shared context available to all steps
        total_confidence: Overall confidence in the reasoning chain
        start_time: When chain execution began
        end_time: When chain execution completed
        total_execution_time: Total time taken for all steps
        success_rate: Percentage of steps that completed successfully
        metadata: Additional metadata for the chain
    """
    chain_id: str
    title: str
    reasoning_type: ReasoningType
    steps: List[ReasoningStep] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    total_confidence: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_execution_time: Optional[float] = None
    success_rate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: ReasoningStep) -> None:
        """Add a reasoning step to the chain."""
        self.steps.append(step)
        logger.debug(f"Added step {step.step_id} to chain {self.chain_id}")

    def get_step(self, step_id: str) -> Optional[ReasoningStep]:
        """Get a specific step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def calculate_confidence(self) -> float:
        """Calculate overall confidence based on individual step confidences."""
        if not self.steps:
            return 0.0

        # Weighted average of step confidences
        total_confidence = sum(step.confidence for step in self.steps)
        self.total_confidence = total_confidence / len(self.steps)
        return self.total_confidence

    def calculate_success_rate(self) -> float:
        """Calculate percentage of steps that completed successfully."""
        if not self.steps:
            return 0.0

        completed_steps = sum(1 for step in self.steps if step.status == StepStatus.COMPLETED)
        self.success_rate = (completed_steps / len(self.steps)) * 100
        return self.success_rate

    async def execute(self) -> bool:
        """
        Execute all steps in the reasoning chain.

        Returns:
            bool: True if the chain executed successfully, False otherwise
        """
        try:
            self.start_time = datetime.now()
            logger.info(f"Starting execution of reasoning chain: {self.chain_id}")

            # Execute steps in dependency order
            executed_steps = set()

            while len(executed_steps) < len(self.steps):
                progress_made = False

                for step in self.steps:
                    if step.step_id in executed_steps:
                        continue

                    # Check if all dependencies are satisfied
                    dependencies_met = all(dep_id in executed_steps for dep_id in step.dependencies)

                    if dependencies_met:
                        # Pass context and previous step outputs as inputs
                        step.inputs.update(self.context)
                        for prev_step in self.steps:
                            if prev_step.step_id in executed_steps:
                                step.inputs.update(prev_step.outputs)

                        success = await step.execute()
                        executed_steps.add(step.step_id)
                        progress_made = True

                        if success and step.validate():
                            logger.debug(f"Step {step.step_id} completed and validated")
                        else:
                            logger.warning(f"Step {step.step_id} failed validation")

                if not progress_made:
                    logger.error("Circular dependency or unsatisfiable dependencies detected")
                    break

            self.end_time = datetime.now()
            self.total_execution_time = (self.end_time - self.start_time).total_seconds()

            self.calculate_confidence()
            self.calculate_success_rate()

            logger.info(f"Chain {self.chain_id} completed with {self.success_rate:.1f}% success rate")
            return self.success_rate > 80.0  # Consider successful if >80% of steps completed

        except Exception as e:
            logger.error(f"Chain {self.chain_id} execution failed: {e}")
            return False

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of the chain execution."""
        return {
            "chain_id": self.chain_id,
            "title": self.title,
            "reasoning_type": self.reasoning_type.value,
            "total_steps": len(self.steps),
            "completed_steps": sum(1 for s in self.steps if s.status == StepStatus.COMPLETED),
            "failed_steps": sum(1 for s in self.steps if s.status == StepStatus.FAILED),
            "total_confidence": self.total_confidence,
            "success_rate": self.success_rate,
            "execution_time": self.total_execution_time,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


class CoTReasoning:
    """
    Main Chain-of-Thought reasoning framework that orchestrates reasoning chains
    across all 4 phases of TORQ Console development.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CoT reasoning framework.

        Args:
            config: Configuration dictionary for the reasoning framework
        """
        self.config = config or {}
        self.chains: Dict[str, ReasoningChain] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)

        self.logger.info("CoT Reasoning framework initialized")

    async def create_chain(
        self,
        chain_id: str,
        title: str,
        reasoning_type: ReasoningType,
        context: Optional[Dict[str, Any]] = None
    ) -> ReasoningChain:
        """
        Create a new reasoning chain.

        Args:
            chain_id: Unique identifier for the chain
            title: Human-readable title
            reasoning_type: Type of reasoning this chain performs
            context: Initial context for the chain

        Returns:
            ReasoningChain: The created reasoning chain
        """
        chain = ReasoningChain(
            chain_id=chain_id,
            title=title,
            reasoning_type=reasoning_type,
            context=context or {}
        )

        self.chains[chain_id] = chain
        self.logger.debug(f"Created reasoning chain: {chain_id}")
        return chain

    async def execute_chain(self, chain_id: str) -> bool:
        """
        Execute a reasoning chain by ID.

        Args:
            chain_id: ID of the chain to execute

        Returns:
            bool: True if execution was successful, False otherwise
        """
        if chain_id not in self.chains:
            self.logger.error(f"Chain {chain_id} not found")
            return False

        chain = self.chains[chain_id]
        success = await chain.execute()

        # Record execution in history
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "chain_id": chain_id,
            "success": success,
            "summary": chain.get_execution_summary()
        })

        return success

    def get_chain(self, chain_id: str) -> Optional[ReasoningChain]:
        """Get a reasoning chain by ID."""
        return self.chains.get(chain_id)

    def list_chains(self) -> List[str]:
        """Get list of all chain IDs."""
        return list(self.chains.keys())

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the execution history."""
        return self.execution_history.copy()

    async def validate_reasoning(self, chain_id: str) -> Dict[str, Any]:
        """
        Validate the reasoning quality of a specific chain.

        Args:
            chain_id: ID of the chain to validate

        Returns:
            Dict containing validation results
        """
        chain = self.get_chain(chain_id)
        if not chain:
            return {"error": f"Chain {chain_id} not found"}

        validation_results = {
            "chain_id": chain_id,
            "overall_valid": True,
            "step_validations": [],
            "confidence_score": chain.total_confidence,
            "success_rate": chain.success_rate,
            "recommendations": []
        }

        for step in chain.steps:
            step_valid = step.validate()
            validation_results["step_validations"].append({
                "step_id": step.step_id,
                "valid": step_valid,
                "confidence": step.confidence,
                "status": step.status.value
            })

            if not step_valid:
                validation_results["overall_valid"] = False
                validation_results["recommendations"].append(
                    f"Review step {step.step_id}: {step.description}"
                )

        return validation_results