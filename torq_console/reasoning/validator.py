#!/usr/bin/env python3
"""
TORQ Console Chain-of-Thought (CoT) Reasoning Validator

This module provides validation capabilities for Chain-of-Thought reasoning chains
to ensure quality, logical consistency, and completeness across all 4 phases.

Classes:
    ValidationResult: Container for validation results
    ValidationRule: Base class for validation rules
    CoTValidator: Main validator for reasoning chains

Validation Rules:
    - Logical consistency
    - Dependency resolution
    - Step completeness
    - Confidence thresholds
    - Execution quality
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
from datetime import datetime

from .core import ReasoningChain, ReasoningStep, StepStatus, ReasoningType

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """
    Represents a validation issue found in a reasoning chain.

    Attributes:
        severity: Severity level of the issue
        category: Category of the validation issue
        description: Human-readable description
        step_id: Related step ID (if applicable)
        recommendation: Suggested fix or improvement
        metadata: Additional context about the issue
    """
    severity: ValidationSeverity
    category: str
    description: str
    step_id: Optional[str] = None
    recommendation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """
    Container for validation results of a reasoning chain.

    Attributes:
        chain_id: ID of the validated chain
        is_valid: Overall validation status
        confidence_score: Confidence in the validation (0.0 - 1.0)
        quality_score: Overall quality score (0.0 - 1.0)
        issues: List of validation issues found
        metrics: Detailed validation metrics
        recommendations: High-level recommendations
        validation_time: Time taken for validation
    """
    chain_id: str
    is_valid: bool
    confidence_score: float
    quality_score: float
    issues: List[ValidationIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    validation_time: Optional[float] = None


class ValidationRule(ABC):
    """
    Base class for validation rules that can be applied to reasoning chains.
    """

    def __init__(self, rule_name: str, description: str, severity: ValidationSeverity = ValidationSeverity.WARNING):
        """
        Initialize the validation rule.

        Args:
            rule_name: Name of the validation rule
            description: Description of what this rule validates
            severity: Default severity for issues found by this rule
        """
        self.rule_name = rule_name
        self.description = description
        self.severity = severity

    @abstractmethod
    async def validate(self, chain: ReasoningChain) -> List[ValidationIssue]:
        """
        Validate a reasoning chain according to this rule.

        Args:
            chain: The reasoning chain to validate

        Returns:
            List of validation issues found
        """
        pass


class DependencyValidationRule(ValidationRule):
    """Validates that step dependencies are properly resolved."""

    def __init__(self):
        super().__init__(
            "Dependency Validation",
            "Ensures all step dependencies are properly defined and resolvable",
            ValidationSeverity.ERROR
        )

    async def validate(self, chain: ReasoningChain) -> List[ValidationIssue]:
        """Validate dependency resolution."""
        issues = []
        step_ids = {step.step_id for step in chain.steps}

        for step in chain.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    issues.append(ValidationIssue(
                        severity=self.severity,
                        category="dependency",
                        description=f"Step {step.step_id} depends on non-existent step {dep_id}",
                        step_id=step.step_id,
                        recommendation=f"Remove dependency on {dep_id} or add the missing step"
                    ))

        # Check for circular dependencies
        circular_deps = self._detect_circular_dependencies(chain.steps)
        for cycle in circular_deps:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="dependency",
                description=f"Circular dependency detected: {' -> '.join(cycle)}",
                recommendation="Restructure dependencies to eliminate cycles"
            ))

        return issues

    def _detect_circular_dependencies(self, steps: List[ReasoningStep]) -> List[List[str]]:
        """Detect circular dependencies using DFS."""
        graph = {step.step_id: step.dependencies for step in steps}
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]):
            if node in rec_stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor, path[:])

            rec_stack.remove(node)

        for step_id in graph:
            if step_id not in visited:
                dfs(step_id, [])

        return cycles


class CompletenessValidationRule(ValidationRule):
    """Validates that reasoning chains are complete and well-structured."""

    def __init__(self):
        super().__init__(
            "Completeness Validation",
            "Ensures reasoning chains have all necessary components",
            ValidationSeverity.WARNING
        )

    async def validate(self, chain: ReasoningChain) -> List[ValidationIssue]:
        """Validate chain completeness."""
        issues = []

        # Check for empty chain
        if not chain.steps:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="completeness",
                description="Reasoning chain has no steps",
                recommendation="Add reasoning steps to create a meaningful chain"
            ))
            return issues

        # Check for steps without descriptions
        for step in chain.steps:
            if not step.description.strip():
                issues.append(ValidationIssue(
                    severity=self.severity,
                    category="completeness",
                    description=f"Step {step.step_id} has no description",
                    step_id=step.step_id,
                    recommendation="Add a clear description explaining what this step does"
                ))

            if not step.reasoning.strip():
                issues.append(ValidationIssue(
                    severity=self.severity,
                    category="completeness",
                    description=f"Step {step.step_id} has no reasoning explanation",
                    step_id=step.step_id,
                    recommendation="Add reasoning to explain why this step is necessary"
                ))

        # Check for orphaned steps (no dependents and not terminal)
        dependents = self._find_dependents(chain.steps)
        terminal_steps = [step for step in chain.steps if step.step_id not in dependents]

        if len(terminal_steps) > 3:  # Too many terminal steps suggests poor structure
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="completeness",
                description=f"Chain has {len(terminal_steps)} terminal steps, which may indicate poor structure",
                recommendation="Consider consolidating steps or adding synthesis steps"
            ))

        return issues

    def _find_dependents(self, steps: List[ReasoningStep]) -> Set[str]:
        """Find all steps that have dependents."""
        dependents = set()
        for step in steps:
            dependents.update(step.dependencies)
        return dependents


class QualityValidationRule(ValidationRule):
    """Validates the quality of reasoning steps and overall chain."""

    def __init__(self):
        super().__init__(
            "Quality Validation",
            "Ensures high quality reasoning and execution",
            ValidationSeverity.WARNING
        )

    async def validate(self, chain: ReasoningChain) -> List[ValidationIssue]:
        """Validate reasoning quality."""
        issues = []

        # Check confidence scores
        low_confidence_steps = [step for step in chain.steps if step.confidence < 0.5]
        if low_confidence_steps:
            issues.append(ValidationIssue(
                severity=self.severity,
                category="quality",
                description=f"{len(low_confidence_steps)} steps have low confidence (<0.5)",
                recommendation="Review and improve low-confidence steps or provide more context"
            ))

        # Check for failed steps
        failed_steps = [step for step in chain.steps if step.status == StepStatus.FAILED]
        for step in failed_steps:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="quality",
                description=f"Step {step.step_id} failed execution",
                step_id=step.step_id,
                recommendation="Review and fix the failed step",
                metadata={"error_message": step.error_message}
            ))

        # Check overall chain confidence
        if chain.total_confidence < 0.6:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="quality",
                description=f"Overall chain confidence is low ({chain.total_confidence:.2f})",
                recommendation="Improve step quality and confidence scores"
            ))

        # Check success rate
        if chain.success_rate < 80.0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="quality",
                description=f"Chain success rate is low ({chain.success_rate:.1f}%)",
                recommendation="Fix failed steps to improve success rate"
            ))

        return issues


class LogicalConsistencyRule(ValidationRule):
    """Validates logical consistency of the reasoning chain."""

    def __init__(self):
        super().__init__(
            "Logical Consistency",
            "Ensures reasoning steps follow logical order and consistency",
            ValidationSeverity.WARNING
        )

    async def validate(self, chain: ReasoningChain) -> List[ValidationIssue]:
        """Validate logical consistency."""
        issues = []

        # Check for appropriate reasoning type alignment
        reasoning_type_steps = {
            ReasoningType.RESEARCH: ["analyze", "gather", "search", "collect"],
            ReasoningType.ANALYSIS: ["evaluate", "assess", "examine", "analyze"],
            ReasoningType.DECISION: ["decide", "choose", "select", "recommend"],
            ReasoningType.PLANNING: ["plan", "design", "structure", "organize"],
            ReasoningType.VALIDATION: ["validate", "verify", "check", "confirm"],
            ReasoningType.SYNTHESIS: ["synthesize", "combine", "integrate", "merge"]
        }

        expected_keywords = reasoning_type_steps.get(chain.reasoning_type, [])
        if expected_keywords:
            matching_steps = 0
            for step in chain.steps:
                step_text = (step.description + " " + step.reasoning).lower()
                if any(keyword in step_text for keyword in expected_keywords):
                    matching_steps += 1

            if matching_steps == 0:
                issues.append(ValidationIssue(
                    severity=self.severity,
                    category="consistency",
                    description=f"No steps match reasoning type {chain.reasoning_type.value}",
                    recommendation=f"Add steps that include keywords: {', '.join(expected_keywords)}"
                ))

        # Check for validation criteria on steps
        steps_without_validation = [step for step in chain.steps if not step.validation_criteria]
        if len(steps_without_validation) > len(chain.steps) * 0.5:  # More than 50% without validation
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="consistency",
                description="Many steps lack validation criteria",
                recommendation="Add validation criteria to help ensure step quality"
            ))

        return issues


class CoTValidator:
    """
    Main validator for Chain-of-Thought reasoning chains.

    Provides comprehensive validation including logical consistency,
    dependency resolution, completeness, and quality assessment.
    """

    def __init__(self, rules: Optional[List[ValidationRule]] = None):
        """
        Initialize the CoT validator.

        Args:
            rules: Custom validation rules to use (uses defaults if None)
        """
        self.rules = rules or self._get_default_rules()
        self.logger = logging.getLogger(__name__)

    def _get_default_rules(self) -> List[ValidationRule]:
        """Get the default set of validation rules."""
        return [
            DependencyValidationRule(),
            CompletenessValidationRule(),
            QualityValidationRule(),
            LogicalConsistencyRule()
        ]

    async def validate_chain(self, chain: ReasoningChain) -> ValidationResult:
        """
        Validate a complete reasoning chain.

        Args:
            chain: The reasoning chain to validate

        Returns:
            ValidationResult containing validation status and details
        """
        start_time = datetime.now()

        try:
            self.logger.info(f"Starting validation of chain {chain.chain_id}")

            all_issues = []

            # Run all validation rules
            for rule in self.rules:
                try:
                    rule_issues = await rule.validate(chain)
                    all_issues.extend(rule_issues)
                    self.logger.debug(f"Rule {rule.rule_name} found {len(rule_issues)} issues")
                except Exception as e:
                    self.logger.error(f"Error in validation rule {rule.rule_name}: {e}")
                    all_issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="validation_error",
                        description=f"Validation rule {rule.rule_name} failed: {str(e)}",
                        recommendation="Check validation rule implementation"
                    ))

            # Calculate overall validation result
            is_valid = not any(issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
                             for issue in all_issues)

            confidence_score = self._calculate_confidence_score(chain, all_issues)
            quality_score = self._calculate_quality_score(chain, all_issues)

            metrics = self._calculate_metrics(chain, all_issues)
            recommendations = self._generate_recommendations(all_issues)

            end_time = datetime.now()
            validation_time = (end_time - start_time).total_seconds()

            result = ValidationResult(
                chain_id=chain.chain_id,
                is_valid=is_valid,
                confidence_score=confidence_score,
                quality_score=quality_score,
                issues=all_issues,
                metrics=metrics,
                recommendations=recommendations,
                validation_time=validation_time
            )

            self.logger.info(f"Validation completed for {chain.chain_id}: "
                           f"valid={is_valid}, quality={quality_score:.2f}")

            return result

        except Exception as e:
            self.logger.error(f"Validation failed for chain {chain.chain_id}: {e}")
            return ValidationResult(
                chain_id=chain.chain_id,
                is_valid=False,
                confidence_score=0.0,
                quality_score=0.0,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    category="validation_failure",
                    description=f"Validation process failed: {str(e)}",
                    recommendation="Check chain structure and validation system"
                )]
            )

    def _calculate_confidence_score(self, chain: ReasoningChain, issues: List[ValidationIssue]) -> float:
        """Calculate confidence score based on chain quality and issues."""
        base_confidence = chain.total_confidence if chain.total_confidence > 0 else 0.5

        # Reduce confidence based on issues
        critical_issues = sum(1 for issue in issues if issue.severity == ValidationSeverity.CRITICAL)
        error_issues = sum(1 for issue in issues if issue.severity == ValidationSeverity.ERROR)
        warning_issues = sum(1 for issue in issues if issue.severity == ValidationSeverity.WARNING)

        penalty = (critical_issues * 0.3) + (error_issues * 0.2) + (warning_issues * 0.1)
        confidence = max(0.0, base_confidence - penalty)

        return min(1.0, confidence)

    def _calculate_quality_score(self, chain: ReasoningChain, issues: List[ValidationIssue]) -> float:
        """Calculate overall quality score."""
        if not chain.steps:
            return 0.0

        # Base score from success rate and confidence
        success_factor = chain.success_rate / 100.0 if chain.success_rate > 0 else 0.5
        confidence_factor = chain.total_confidence if chain.total_confidence > 0 else 0.5

        base_score = (success_factor + confidence_factor) / 2.0

        # Adjust based on issues
        critical_penalty = sum(0.4 for issue in issues if issue.severity == ValidationSeverity.CRITICAL)
        error_penalty = sum(0.2 for issue in issues if issue.severity == ValidationSeverity.ERROR)
        warning_penalty = sum(0.1 for issue in issues if issue.severity == ValidationSeverity.WARNING)

        total_penalty = critical_penalty + error_penalty + warning_penalty
        quality_score = max(0.0, base_score - total_penalty)

        return min(1.0, quality_score)

    def _calculate_metrics(self, chain: ReasoningChain, issues: List[ValidationIssue]) -> Dict[str, Any]:
        """Calculate detailed validation metrics."""
        return {
            "total_steps": len(chain.steps),
            "completed_steps": sum(1 for step in chain.steps if step.status == StepStatus.COMPLETED),
            "failed_steps": sum(1 for step in chain.steps if step.status == StepStatus.FAILED),
            "total_issues": len(issues),
            "critical_issues": sum(1 for issue in issues if issue.severity == ValidationSeverity.CRITICAL),
            "error_issues": sum(1 for issue in issues if issue.severity == ValidationSeverity.ERROR),
            "warning_issues": sum(1 for issue in issues if issue.severity == ValidationSeverity.WARNING),
            "info_issues": sum(1 for issue in issues if issue.severity == ValidationSeverity.INFO),
            "average_confidence": sum(step.confidence for step in chain.steps) / len(chain.steps) if chain.steps else 0.0,
            "execution_time": chain.total_execution_time,
            "reasoning_type": chain.reasoning_type.value
        }

    def _generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate high-level recommendations based on issues."""
        recommendations = []

        # Count issues by category
        categories = {}
        for issue in issues:
            categories[issue.category] = categories.get(issue.category, 0) + 1

        # Generate category-based recommendations
        if categories.get("dependency", 0) > 0:
            recommendations.append("Review and fix dependency relationships between steps")

        if categories.get("completeness", 0) > 0:
            recommendations.append("Add missing descriptions, reasoning, or validation criteria")

        if categories.get("quality", 0) > 0:
            recommendations.append("Improve step implementation and increase confidence scores")

        if categories.get("consistency", 0) > 0:
            recommendations.append("Ensure reasoning steps align with the chain's purpose and type")

        # Critical issues get priority
        critical_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.CRITICAL)
        if critical_count > 0:
            recommendations.insert(0, f"Address {critical_count} critical issues immediately")

        return recommendations[:5]  # Limit to top 5 recommendations


async def validate_chain_quick(chain: ReasoningChain) -> bool:
    """
    Quick validation check for basic chain validity.

    Args:
        chain: The reasoning chain to validate

    Returns:
        bool: True if chain passes basic validation
    """
    validator = CoTValidator([DependencyValidationRule(), CompletenessValidationRule()])
    result = await validator.validate_chain(chain)
    return result.is_valid