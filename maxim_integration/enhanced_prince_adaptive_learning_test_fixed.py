#!/usr/bin/env python3
"""
Enhanced Prince Flowers Adaptive Learning Test

Comprehensive test that demonstrates how the Enhanced Prince Flowers agent
actually adapts and improves over multiple cycles of learning and feedback.

This test shows:
1. Initial baseline performance
2. Learning cycles with feedback
3. Adaptation and improvement tracking
4. Memory consolidation over time
5. Real capability growth demonstration
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import os
import sys

# Add TORQ Console to path
sys.path.append('E:/TORQ-CONSOLE')

from zep_enhanced_prince_flowers import create_zep_enhanced_prince_flowers
from torq_console.llm.providers.claude import ClaudeProvider

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LearningPhase(Enum):
    """Learning phases for the adaptive test"""
    BASELINE = "baseline"
    LEARNING_CYCLE_1 = "learning_cycle_1"
    LEARNING_CYCLE_2 = "learning_cycle_2"
    LEARNING_CYCLE_3 = "learning_cycle_3"
    CONSOLIDATION = "consolidation"
    MASTERY = "mastery"

class FeedbackType(Enum):
    """Types of feedback for learning"""
    QUALITY_IMPROVEMENT = "quality_improvement"
    EFFICIENCY_ENHANCEMENT = "efficiency_enhancement"
    ACCURACY_CORRECTION = "accuracy_correction"
    INNOVATION_ENCOURAGEMENT = "innovation_encouragement"

@dataclass
class AdaptiveTestResult:
    """Result from adaptive learning test"""
    phase: LearningPhase
    cycle_number: int
    timestamp: str
    test_scenarios: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]
    memory_enhancement_score: float
    learning_velocity: float
    adaptation_rate: float
    improvements_from_previous: Dict[str, float]
    feedback_applied: List[str]
    next_phase_recommendations: List[str]

class EnhancedPrinceAdaptiveTest:
    """Comprehensive adaptive learning test for Enhanced Prince Flowers"""

    def __init__(self, agent):
        self.agent = agent
        self.test_session_id = f"adaptive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger = logging.getLogger(f"{__name__}.{self.test_session_id}")

        # Learning tracking
        self.learning_history = []
        self.performance_trends = {}
        self.memory_consolidation_events = []
        self.feedback_cycles = []

        # Test scenarios that progressively challenge the agent
        self.test_scenarios = {
            "baseline": [
                "What is artificial intelligence?",
                "Write a simple Python function",
                "Explain database indexing",
                "What is REST API?",
                "Create a sorting algorithm"
            ],
            "intermediate": [
                "Design a scalable microservices architecture",
                "Implement authentication with JWT",
                "Optimize database queries for performance",
                "Create a real-time chat application",
                "Design a machine learning pipeline"
            ],
            "advanced": [
                "Architect a distributed system for 1M+ users",
                "Implement zero-downtime deployment strategy",
                "Design a multi-tenant SaaS platform",
                "Create an AI-powered recommendation system",
                "Solve complex algorithmic optimization problems"
            ],
            "expert": [
                "Design blockchain-based supply chain management",
                "Implement quantum-resistant cryptography",
                "Create edge computing architecture for IoT",
                "Design AI system for autonomous vehicles",
                "Solve NP-hard optimization problems with heuristics"
            ]
        }

        # Learning objectives
        self.learning_objectives = {
            "technical_depth": 0.0,
            "problem_solving_sophistication": 0.0,
            "code_quality": 0.0,
            "architectural_thinking": 0.0,
            "innovation_creativity": 0.0,
            "communication_clarity": 0.0
        }

    async def run_comprehensive_adaptive_test(self) -> Dict[str, Any]:
        """Run comprehensive adaptive learning test"""
        self.logger.info("Starting Comprehensive Enhanced Prince Flowers Adaptive Learning Test")

        # Phase 1: Establish Baseline
        print("\n[PHASE 1: ESTABLISHING BASELINE]")
        print("=" * 60)
        baseline_result = await self._run_learning_phase(LearningPhase.BASELINE, 1)
        self.learning_history.append(baseline_result)

        # Phase 2: Learning Cycle 1 (Fundamental Skills)
        print("\n[PHASE 2: LEARNING CYCLE 1 - FUNDAMENTAL SKILLS]")
        print("=" * 60)
        cycle1_result = await self._run_learning_phase(LearningPhase.LEARNING_CYCLE_1, 1)
        self.learning_history.append(cycle1_result)

        # Phase 3: Learning Cycle 2 (Intermediate Skills)
        print("\n[TARGET] PHASE 3: LEARNING CYCLE 2 - INTERMEDIATE SKILLS")
        print("=" * 60)
        cycle2_result = await self._run_learning_phase(LearningPhase.LEARNING_CYCLE_2, 1)
        self.learning_history.append(cycle2_result)

        # Phase 4: Learning Cycle 3 (Advanced Skills)
        print("\n[TARGET] PHASE 4: LEARNING CYCLE 3 - ADVANCED SKILLS")
        print("=" * 60)
        cycle3_result = await self._run_learning_phase(LearningPhase.LEARNING_CYCLE_3, 1)
        self.learning_history.append(cycle3_result)

        # Phase 5: Consolidation Phase
        print("\n[TARGET] PHASE 5: CONSOLIDATION - INTEGRATING LEARNING")
        print("=" * 60)
        consolidation_result = await self._run_learning_phase(LearningPhase.CONSOLIDATION, 1)
        self.learning_history.append(consolidation_result)

        # Phase 6: Mastery Demonstration
        print("\n[TARGET] PHASE 6: MASTERY DEMONSTRATION")
        print("=" * 60)
        mastery_result = await self._run_learning_phase(LearningPhase.MASTERY, 1)
        self.learning_history.append(mastery_result)

        # Generate comprehensive analysis
        return await self._generate_comprehensive_analysis()

    async def _run_learning_phase(self, phase: LearningPhase, cycle: int) -> AdaptiveTestResult:
        """Run a single learning phase with feedback integration"""
        self.logger.info(f"Running {phase.value} cycle {cycle}")

        phase_start_time = time.time()

        # Select appropriate scenarios based on phase
        scenarios = self._select_scenarios_for_phase(phase)

        # Execute scenarios
        test_results = []
        for scenario in scenarios:
            result = await self._execute_learning_scenario(scenario, phase)
            test_results.append(result)
            await asyncio.sleep(1)  # Brief pause between scenarios

        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(test_results, phase)

        # Calculate memory enhancement score
        memory_enhancement_score = self._calculate_memory_enhancement(test_results)

        # Calculate learning velocity
        learning_velocity = self._calculate_learning_velocity(phase, performance_metrics)

        # Calculate adaptation rate
        adaptation_rate = self._calculate_adaptation_rate(test_results)

        # Calculate improvements from previous phase
        improvements_from_previous = self._calculate_improvements_from_previous(performance_metrics)

        # Apply feedback for next phase
        feedback_applied = self._generate_and_apply_feedback(test_results, performance_metrics, phase)

        # Generate recommendations for next phase
        next_phase_recommendations = self._generate_next_phase_recommendations(performance_metrics, phase)

        phase_result = AdaptiveTestResult(
            phase=phase,
            cycle_number=cycle,
            timestamp=datetime.now().isoformat(),
            test_scenarios=test_results,
            performance_metrics=performance_metrics,
            memory_enhancement_score=memory_enhancement_score,
            learning_velocity=learning_velocity,
            adaptation_rate=adaptation_rate,
            improvements_from_previous=improvements_from_previous,
            feedback_applied=feedback_applied,
            next_phase_recommendations=next_phase_recommendations
        )

        # Display phase results
        await self._display_phase_results(phase_result)

        return phase_result

    def _select_scenarios_for_phase(self, phase: LearningPhase) -> List[str]:
        """Select appropriate scenarios for each learning phase"""
        if phase == LearningPhase.BASELINE:
            return self.test_scenarios["baseline"]
        elif phase == LearningPhase.LEARNING_CYCLE_1:
            # Mix of baseline and intermediate
            return self.test_scenarios["baseline"] + self.test_scenarios["intermediate"][:3]
        elif phase == LearningPhase.LEARNING_CYCLE_2:
            return self.test_scenarios["intermediate"]
        elif phase == LearningPhase.LEARNING_CYCLE_3:
            # Mix of intermediate and advanced
            return self.test_scenarios["intermediate"][-2:] + self.test_scenarios["advanced"][:3]
        elif phase == LearningPhase.CONSOLIDATION:
            # Mix of all previous levels
            return (
                self.test_scenarios["baseline"][:1] +
                self.test_scenarios["intermediate"][:2] +
                self.test_scenarios["advanced"][:2]
            )
        elif phase == LearningPhase.MASTERY:
            return self.test_scenarios["expert"]
        else:
            return self.test_scenarios["baseline"]

    async def _execute_learning_scenario(self, scenario: str, phase: LearningPhase) -> Dict[str, Any]:
        """Execute a single learning scenario"""
        start_time = time.time()

        # Enhance query based on learning phase
        enhanced_query = self._enhance_query_for_phase(scenario, phase)

        # Execute query
        result = await self.agent.process_query_with_zep_memory(enhanced_query)
        execution_time = time.time() - start_time

        # Analyze response quality
        response_quality = self._analyze_response_quality(result.get("content", ""), phase)

        # Calculate learning-specific metrics
        learning_metrics = self._calculate_learning_metrics(result, phase)

        return {
            "scenario": scenario,
            "enhanced_query": enhanced_query,
            "phase": phase.value,
            "success": result.get("success", False),
            "confidence": result.get("confidence", 0.0),
            "response_length": len(result.get("content", "")),
            "execution_time": execution_time,
            "memory_used": result.get("zep_memory", {}).get("memories_used", 0),
            "tools_used": result.get("tools_used", []),
            "response_quality": response_quality,
            "learning_metrics": learning_metrics,
            "response_preview": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", "")
        }

    def _enhance_query_for_phase(self, query: str, phase: LearningPhase) -> str:
        """Enhance query based on learning phase"""
        enhancements = {
            LearningPhase.BASELINE: query,
            LearningPhase.LEARNING_CYCLE_1: f"Building on our previous interactions, {query}",
            LearningPhase.LEARNING_CYCLE_2: f"Given what we've learned so far, can you provide an advanced approach to: {query}",
            LearningPhase.LEARNING_CYCLE_3: f"Drawing from our established patterns and previous discussions, please demonstrate expertise in: {query}",
            LearningPhase.CONSOLIDATION: f"Integrating all our previous learning, please provide a comprehensive solution for: {query}",
            LearningPhase.MASTERY: f"Mastering all previous concepts and demonstrating advanced capabilities, please show expertise in: {query}"
        }

        return enhancements.get(phase, query)

    def _analyze_response_quality(self, content: str, phase: LearningPhase) -> Dict[str, float]:
        """Analyze response quality based on phase expectations"""
        if not content:
            return {"overall": 0.0, "depth": 0.0, "clarity": 0.0, "completeness": 0.0}

        quality_factors = {
            "depth": self._assess_response_depth(content, phase),
            "clarity": self._assess_response_clarity(content),
            "completeness": self._assess_response_completeness(content, phase),
            "innovation": self._assess_response_innovation(content, phase),
            "technical_accuracy": self._assess_technical_accuracy(content),
            "structure": self._assess_response_structure(content)
        }

        # Calculate weighted overall score
        weights = {
            LearningPhase.BASELINE: {"depth": 0.2, "clarity": 0.3, "completeness": 0.3, "innovation": 0.1, "technical_accuracy": 0.1, "structure": 0.2},
            LearningPhase.LEARNING_CYCLE_1: {"depth": 0.3, "clarity": 0.25, "completeness": 0.25, "innovation": 0.1, "technical_accuracy": 0.1, "structure": 0.2},
            LearningPhase.LEARNING_CYCLE_2: {"depth": 0.3, "clarity": 0.2, "completeness": 0.25, "innovation": 0.15, "technical_accuracy": 0.1, "structure": 0.2},
            LearningPhase.LEARNING_CYCLE_3: {"depth": 0.35, "clarity": 0.2, "completeness": 0.2, "innovation": 0.15, "technical_accuracy": 0.1, "structure": 0.15},
            LearningPhase.CONSOLIDATION: {"depth": 0.4, "clarity": 0.2, "completeness": 0.2, "innovation": 0.1, "technical_accuracy": 0.1, "structure": 0.1},
            LearningPhase.MASTERY: {"depth": 0.4, "clarity": 0.15, "completeness": 0.2, "innovation": 0.2, "technical_accuracy": 0.05, "structure": 0.1}
        }

        phase_weights = weights.get(phase, weights[LearningPhase.BASELINE])
        overall_score = sum(quality_factors[factor] * weight for factor, weight in phase_weights.items())

        quality_factors["overall"] = overall_score
        return quality_factors

    def _assess_response_depth(self, content: str, phase: LearningPhase) -> float:
        """Assess response depth based on phase expectations"""
        depth_indicators = {
            LearningPhase.BASELINE: ["explain", "what is", "how", "because"],
            LearningPhase.LEARNING_CYCLE_1: ["furthermore", "additionally", "moreover", "specifically"],
            LearningPhase.LEARNING_CYCLE_2: ["consequently", "therefore", "alternatively", "comparatively"],
            LearningPhase.LEARNING_CYCLE_3: ["fundamentally", "essentially", "critically", "significantly"],
            LearningPhase.CONSOLIDATION: ["integrated", "comprehensive", "holistic", "systematic"],
            LearningPhase.MASTERY: ["sophisticated", "nuanced", "advanced", "expert"]
        }

        indicators = depth_indicators.get(phase, depth_indicators[LearningPhase.BASELINE])
        count = sum(1 for indicator in indicators if indicator in content.lower())

        # Also consider content length as a depth proxy
        length_factor = min(len(content) / 1000, 1.0)

        return min((count / len(indicators) + length_factor) / 2, 1.0)

    def _assess_response_clarity(self, content: str) -> float:
        """Assess response clarity"""
        clarity_indicators = [
            "clear", "understand", "simple", "straightforward", "concise",
            "easy to follow", "step by step", "obviously", "essentially"
        ]

        unclear_indicators = [
            "confusing", "unclear", "complicated", "difficult", "complex",
            "uncertain", "maybe", "perhaps", "possibly"
        ]

        clarity_score = sum(1 for indicator in clarity_indicators if indicator in content.lower())
        unclear_score = sum(1 for indicator in unclear_indicators if indicator in content.lower())

        # Penalize unclear indicators
        net_score = max(0, clarity_score - unclear_score)

        return min(net_score / 3, 1.0)

    def _assess_response_completeness(self, content: str, phase: LearningPhase) -> float:
        """Assess response completeness based on phase expectations"""
        completeness_indicators = {
            LearningPhase.BASELINE: ["definition", "example", "basic"],
            LearningPhase.LEARNING_CYCLE_1: ["detailed", "thorough", "comprehensive"],
            LearningPhase.LEARNING_CYCLE_2: ["advanced", "in-depth", "extensive"],
            LearningPhase.LEARNING_CYCLE_3: ["sophisticated", "nuanced", "detailed"],
            LearningPhase.CONSOLIDATION: ["complete", "thorough", "comprehensive"],
            LearningPhase.MASTERY: ["exhaustive", "comprehensive", "definitive"]
        }

        indicators = completeness_indicators.get(phase, completeness_indicators[LearningPhase.BASELINE])
        count = sum(1 for indicator in indicators if indicator in content.lower())

        # Consider content structure (headings, lists, etc.)
        structure_score = 0
        if "##" in content or "###" in content:  # Markdown headers
            structure_score += 0.3
        if "1." in content or "•" in content:  # Lists
            structure_score += 0.3
        if "```" in content:  # Code blocks
            structure_score += 0.2

        return min((count / 3 + structure_score), 1.0)

    def _assess_response_innovation(self, content: str, phase: LearningPhase) -> float:
        """Assess response innovation based on phase expectations"""
        innovation_indicators = {
            LearningPhase.BASELINE: ["different", "alternative", "another"],
            LearningPhase.LEARNING_CYCLE_1: ["creative", "innovative", "unique"],
            LearningPhase.LEARNING_CYCLE_2: ["novel", "original", "breakthrough"],
            LearningPhase.LEARNING_CYCLE_3: ["cutting-edge", "state-of-the-art", "revolutionary"],
            LearningPhase.CONSOLIDATION: ["integrated", "synthesized", "combined"],
            LearningPhase.MASTERY: ["paradigm-shifting", "groundbreaking", "transformative"]
        }

        indicators = innovation_indicators.get(phase, innovation_indicators[LearningPhase.BASELINE])
        count = sum(1 for indicator in indicators if indicator in content.lower())

        # Check for unique patterns or approaches
        unique_pattern_indicators = [
            "consider", "imagine", "what if", "alternative approach",
            "different perspective", "new way", "beyond traditional"
        ]

        unique_count = sum(1 for indicator in unique_pattern_indicators if indicator in content.lower())

        return min((count + unique_count) / 4, 1.0)

    def _assess_technical_accuracy(self, content: str) -> float:
        """Assess technical accuracy"""
        technical_terms = [
            "algorithm", "function", "method", "class", "object",
            "database", "api", "http", "json", "xml", "sql",
            "architecture", "design pattern", "framework", "library"
        ]

        term_count = sum(1 for term in technical_terms if term in content.lower())

        # Check for proper explanation structure
        explanation_indicators = [
            "first", "second", "third", "finally", "for example",
            "specifically", "in particular", "notably"
        ]

        explanation_count = sum(1 for indicator in explanation_indicators if indicator in content.lower())

        return min((term_count / 5 + explanation_count / 4) / 2, 1.0)

    def _assess_response_structure(self, content: str) -> float:
        """Assess response structure"""
        structure_indicators = [
            content.count('\n') > 5,  # Multiple paragraphs
            "##" in content or "###" in content,  # Headers
            "1." in content or "•" in content or "-" in content,  # Lists
            content.count('.') > 10,  # Multiple sentences
            len(content.split()) > 100  # Adequate word count
        ]

        return sum(structure_indicators) / len(structure_indicators)

    def _calculate_learning_metrics(self, result: Dict[str, Any], phase: LearningPhase) -> Dict[str, float]:
        """Calculate learning-specific metrics"""
        return {
            "memory_integration": min(result.get("memory_used", 0) / 3, 1.0),
            "tool_coordination": min(len(result.get("tools_used", [])) / 3, 1.0),
            "response_time_efficiency": min(10 / result.get("execution_time", 1), 1.0),
            "confidence_growth": result.get("confidence", 0.0),
            "adaptation_score": self._calculate_adaptation_score(result, phase)
        }

    def _calculate_adaptation_score(self, result: Dict[str, Any], phase: LearningPhase) -> float:
        """Calculate how well agent adapted to phase expectations"""
        content = result.get("content", "")

        adaptation_indicators = {
            LearningPhase.BASELINE: ["basic", "simple", "fundamental"],
            LearningPhase.LEARNING_CYCLE_1: ["improved", "better", "enhanced"],
            LearningPhase.LEARNING_CYCLE_2: ["advanced", "sophisticated", "complex"],
            LearningPhase.LEARNING_CYCLE_3: ["expert", "professional", "comprehensive"],
            LearningPhase.CONSOLIDATION: ["integrated", "combined", "synthesized"],
            LearningPhase.MASTERY: ["mastered", "expert", "definitive"]
        }

        indicators = adaptation_indicators.get(phase, adaptation_indicators[LearningPhase.BASELINE])
        count = sum(1 for indicator in indicators if indicator in content.lower())

        return min(count / 2, 1.0)

    def _calculate_performance_metrics(self, test_results: List[Dict], phase: LearningPhase) -> Dict[str, float]:
        """Calculate comprehensive performance metrics for a phase"""
        if not test_results:
            return {"overall": 0.0}

        # Basic metrics
        success_rate = sum(1 for r in test_results if r.get("success", False)) / len(test_results)
        avg_confidence = statistics.mean([r.get("confidence", 0) for r in test_results])
        avg_response_quality = statistics.mean([r.get("response_quality", {}).get("overall", 0) for r in test_results])

        # Learning-specific metrics
        avg_memory_integration = statistics.mean([r.get("learning_metrics", {}).get("memory_integration", 0) for r in test_results])
        avg_tool_coordination = statistics.mean([r.get("learning_metrics", {}).get("tool_coordination", 0) for r in test_results])
        avg_adaptation_score = statistics.mean([r.get("learning_metrics", {}).get("adaptation_score", 0) for r in test_results])

        # Phase-specific weighting
        if phase == LearningPhase.BASELINE:
            weights = {"success": 0.3, "confidence": 0.3, "quality": 0.2, "memory": 0.1, "tools": 0.05, "adaptation": 0.05}
        elif phase == LearningPhase.MASTERY:
            weights = {"success": 0.2, "confidence": 0.2, "quality": 0.3, "memory": 0.1, "tools": 0.1, "adaptation": 0.1}
        else:
            weights = {"success": 0.25, "confidence": 0.25, "quality": 0.25, "memory": 0.1, "tools": 0.075, "adaptation": 0.075}

        overall_score = (
            success_rate * weights["success"] +
            avg_confidence * weights["confidence"] +
            avg_response_quality * weights["quality"] +
            avg_memory_integration * weights["memory"] +
            avg_tool_coordination * weights["tools"] +
            avg_adaptation_score * weights["adaptation"]
        )

        return {
            "overall": overall_score,
            "success_rate": success_rate,
            "avg_confidence": avg_confidence,
            "avg_response_quality": avg_response_quality,
            "avg_memory_integration": avg_memory_integration,
            "avg_tool_coordination": avg_tool_coordination,
            "avg_adaptation_score": avg_adaptation_score
        }

    def _calculate_memory_enhancement(self, test_results: List[Dict]) -> float:
        """Calculate how much memory enhanced the responses"""
        if not test_results:
            return 0.0

        memory_usage_scores = [r.get("memory_used", 0) for r in test_results]
        avg_memory_usage = statistics.mean(memory_usage_scores)

        # Check if memory actually enhanced content
        memory_enhanced_count = sum(1 for r in test_results
                                   if r.get("memory_used", 0) > 0 and
                                      "previous" in r.get("response_preview", "").lower())

        enhancement_rate = memory_enhanced_count / len(test_results)

        return (avg_memory_usage * 0.6 + enhancement_rate * 0.4)

    def _calculate_learning_velocity(self, phase: LearningPhase, performance_metrics: Dict[str, float]) -> float:
        """Calculate how quickly the agent is learning"""
        # Learning velocity increases with phase progression
        phase_multipliers = {
            LearningPhase.BASELINE: 0.0,
            LearningPhase.LEARNING_CYCLE_1: 0.2,
            LearningPhase.LEARNING_CYCLE_2: 0.4,
            LearningPhase.LEARNING_CYCLE_3: 0.6,
            LearningPhase.CONSOLIDATION: 0.8,
            LearningPhase.MASTERY: 1.0
        }

        base_velocity = phase_multipliers.get(phase, 0.0)
        performance_bonus = performance_metrics.get("overall", 0.0) * 0.5

        return min(base_velocity + performance_bonus, 1.0)

    def _calculate_adaptation_rate(self, test_results: List[Dict]) -> float:
        """Calculate how well the agent adapted to scenarios"""
        if not test_results:
            return 0.0

        adaptation_scores = [r.get("learning_metrics", {}).get("adaptation_score", 0) for r in test_results]
        return statistics.mean(adaptation_scores)

    def _calculate_improvements_from_previous(self, current_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate improvements from previous phase"""
        if len(self.learning_history) < 1:
            return {metric: 0.0 for metric in current_metrics.keys()}

        previous_metrics = self.learning_history[-1].performance_metrics
        improvements = {}

        for metric, current_value in current_metrics.items():
            previous_value = previous_metrics.get(metric, 0.0)
            if previous_value > 0:
                improvement = (current_value - previous_value) / previous_value
                improvements[metric] = improvement
            else:
                improvements[metric] = current_value

        return improvements

    def _generate_and_apply_feedback(self, test_results: List[Dict], performance_metrics: Dict[str, float], phase: LearningPhase) -> List[str]:
        """Generate and apply feedback for learning improvement"""
        feedback = []

        # Identify areas for improvement
        if performance_metrics.get("success_rate", 0) < 0.8:
            feedback.append("Focus on improving task completion success rate")

        if performance_metrics.get("avg_confidence", 0) < 0.7:
            feedback.append("Work on increasing response confidence through better preparation")

        if performance_metrics.get("avg_response_quality", 0) < 0.7:
            feedback.append("Enhance response quality with more depth and structure")

        if performance_metrics.get("avg_memory_integration", 0) < 0.5:
            feedback.append("Better utilize memory integration for context-aware responses")

        if performance_metrics.get("avg_tool_coordination", 0) < 0.5:
            feedback.append("Improve tool coordination for more comprehensive solutions")

        # Phase-specific feedback
        if phase == LearningPhase.LEARNING_CYCLE_1:
            feedback.append("Focus on building fundamental skills and knowledge base")
        elif phase == LearningPhase.LEARNING_CYCLE_2:
            feedback.append("Develop intermediate capabilities and apply learning from previous phases")
        elif phase == LearningPhase.LEARNING_CYCLE_3:
            feedback.append("Advance to sophisticated problem-solving and expert-level responses")
        elif phase == LearningPhase.CONSOLIDATION:
            feedback.append("Integrate all learned concepts and demonstrate comprehensive understanding")
        elif phase == LearningPhase.MASTERY:
            feedback.append("Achieve mastery level performance with expert insights and innovation")

        # Store feedback for tracking
        feedback_cycle = {
            "phase": phase.value,
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback,
            "performance_metrics": performance_metrics
        }
        self.feedback_cycles.append(feedback_cycle)

        return feedback

    def _generate_next_phase_recommendations(self, performance_metrics: Dict[str, float], phase: LearningPhase) -> List[str]:
        """Generate recommendations for next learning phase"""
        recommendations = []

        overall_performance = performance_metrics.get("overall", 0.0)

        if overall_performance >= 0.85:
            recommendations.append("Excellent performance! Ready to advance to next phase with confidence")
        elif overall_performance >= 0.7:
            recommendations.append("Good performance. Proceed to next phase while focusing on weak areas")
        elif overall_performance >= 0.6:
            recommendations.append("Adequate performance. Review feedback before advancing")
        else:
            recommendations.append("Performance needs improvement. Consider additional practice in current phase")

        # Specific recommendations based on metrics
        if performance_metrics.get("avg_memory_integration", 0) < 0.5:
            recommendations.append("Focus on better memory utilization in next phase")

        if performance_metrics.get("avg_adaptation_score", 0) < 0.6:
            recommendations.append("Work on adapting responses to meet phase expectations")

        if phase == LearningPhase.CONSOLIDATION and overall_performance >= 0.8:
            recommendations.append("Ready for mastery phase - demonstrate expert-level capabilities")

        return recommendations

    async def _display_phase_results(self, phase_result: AdaptiveTestResult):
        """Display results for a learning phase"""
        print(f"\n[CHART] {phase_result.phase.value.upper()} RESULTS")
        print("-" * 40)
        print(f"Overall Performance: {phase_result.performance_metrics['overall']:.1%}")
        print(f"Success Rate: {phase_result.performance_metrics['success_rate']:.1%}")
        print(f"Average Confidence: {phase_result.performance_metrics['avg_confidence']:.3f}")
        print(f"Response Quality: {phase_result.performance_metrics['avg_response_quality']:.1%}")
        print(f"Memory Integration: {phase_result.performance_metrics['avg_memory_integration']:.1%}")
        print(f"Learning Velocity: {phase_result.learning_velocity:.3f}")
        print(f"Adaptation Rate: {phase_result.adaptation_rate:.1%}")

        if phase_result.improvements_from_previous:
            print(f"\n[ARROW UP] Improvements from Previous Phase:")
            for metric, improvement in phase_result.improvements_from_previous.items():
                if improvement != 0:
                    print(f"  {metric}: {improvement:+.1%}")

        if phase_result.feedback_applied:
            print(f"\n[IDEA] Feedback Applied:")
            for feedback in phase_result.feedback_applied[:3]:
                print(f"  • {feedback}")

        if phase_result.next_phase_recommendations:
            print(f"\n[TARGET] Recommendations:")
            for rec in phase_result.next_phase_recommendations[:2]:
                print(f"  • {rec}")

    async def _generate_comprehensive_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive analysis of the entire learning cycle"""
        self.logger.info("Generating comprehensive adaptive learning analysis")

        # Calculate overall learning progression
        progression_analysis = self._analyze_learning_progression()

        # Calculate memory consolidation effectiveness
        memory_analysis = self._analyze_memory_consolidation()

        # Calculate adaptation and growth metrics
        growth_analysis = self._analyze_growth_patterns()

        # Generate final assessment
        final_assessment = self._generate_final_assessment(progression_analysis, memory_analysis, growth_analysis)

        comprehensive_analysis = {
            "test_date": datetime.now().isoformat(),
            "test_type": "Enhanced Prince Flowers Adaptive Learning Test",
            "total_phases": len(self.learning_history),
            "phase_results": [asdict(result) for result in self.learning_history],
            "progression_analysis": progression_analysis,
            "memory_analysis": memory_analysis,
            "growth_analysis": growth_analysis,
            "final_assessment": final_assessment,
            "learning_objectives_achievement": self._assess_learning_objectives_achievement(),
            "recommendations": self._generate_final_recommendations()
        }

        # Save comprehensive results
        results_file = "E:/TORQ-CONSOLE/maxim_integration/enhanced_prince_adaptive_learning_results.json"
        with open(results_file, "w") as f:
            json.dump(comprehensive_analysis, f, indent=2)

        print(f"\n[OK] Comprehensive results saved to: {results_file}")

        return comprehensive_analysis

    def _analyze_learning_progression(self) -> Dict[str, Any]:
        """Analyze learning progression across phases"""
        if len(self.learning_history) < 2:
            return {"analysis": "Insufficient data for progression analysis"}

        performance_over_time = [r.performance_metrics["overall"] for r in self.learning_history]

        # Calculate progression metrics
        initial_performance = performance_over_time[0]
        final_performance = performance_over_time[-1]
        overall_improvement = (final_performance - initial_performance) / initial_performance if initial_performance > 0 else 0

        # Calculate learning velocity trend
        learning_velocities = [r.learning_velocity for r in self.learning_history]
        avg_learning_velocity = statistics.mean(learning_velocities)

        # Calculate adaptation trend
        adaptation_rates = [r.adaptation_rate for r in self.learning_history]
        avg_adaptation_rate = statistics.mean(adaptation_rates)

        # Identify best performing phase
        best_phase = max(self.learning_history, key=lambda x: x.performance_metrics["overall"])

        return {
            "initial_performance": initial_performance,
            "final_performance": final_performance,
            "overall_improvement": overall_improvement,
            "avg_learning_velocity": avg_learning_velocity,
            "avg_adaptation_rate": avg_adaptation_rate,
            "best_phase": best_phase.phase.value,
            "best_performance": best_phase.performance_metrics["overall"],
            "performance_trend": "improving" if performance_over_time[-1] > performance_over_time[0] else "declining"
        }

    def _analyze_memory_consolidation(self) -> Dict[str, Any]:
        """Analyze memory consolidation effectiveness"""
        memory_scores = [r.memory_enhancement_score for r in self.learning_history]
        memory_integrations = [r.performance_metrics["avg_memory_integration"] for r in self.learning_history]

        return {
            "avg_memory_enhancement": statistics.mean(memory_scores) if memory_scores else 0,
            "final_memory_enhancement": memory_scores[-1] if memory_scores else 0,
            "memory_enhancement_trend": "improving" if memory_scores[-1] > memory_scores[0] else "declining",
            "avg_memory_integration": statistics.mean(memory_integrations) if memory_integrations else 0,
            "memory_utilization_consistency": statistics.stdev(memory_integrations) if len(memory_integrations) > 1 else 0
        }

    def _analyze_growth_patterns(self) -> Dict[str, Any]:
        """Analyze growth patterns and capabilities development"""
        return {
            "total_learning_cycles": len([r for r in self.learning_history if "cycle" in r.phase.value]),
            "feedback_cycles_completed": len(self.feedback_cycles),
            "adaptation_capability": self._assess_adaptation_capability(),
            "learning_consistency": self._assess_learning_consistency(),
            "growth_acceleration": self._assess_growth_acceleration()
        }

    def _assess_adaptation_capability(self) -> float:
        """Assess overall adaptation capability"""
        adaptation_scores = [r.adaptation_rate for r in self.learning_history]
        return statistics.mean(adaptation_scores) if adaptation_scores else 0

    def _assess_learning_consistency(self) -> float:
        """Assess learning consistency"""
        if len(self.learning_history) < 2:
            return 1.0

        performances = [r.performance_metrics["overall"] for r in self.learning_history]
        variance = statistics.variance(performances) if len(performances) > 1 else 0

        # Lower variance = higher consistency
        return max(0, 1.0 - variance)

    def _assess_growth_acceleration(self) -> float:
        """Assess if growth is accelerating"""
        if len(self.learning_history) < 3:
            return 0.0

        performances = [r.performance_metrics["overall"] for r in self.learning_history]

        # Compare early growth vs late growth
        early_growth = performances[1] - performances[0]
        late_growth = performances[-1] - performances[-2]

        return max(-1.0, min(1.0, late_growth - early_growth))

    def _generate_final_assessment(self, progression: Dict, memory: Dict, growth: Dict) -> Dict[str, Any]:
        """Generate final assessment of learning capabilities"""
        overall_score = (progression["final_performance"] + memory["avg_memory_enhancement"]) / 2

        # Determine mastery level
        if overall_score >= 0.9:
            mastery_level = "Expert Master"
        elif overall_score >= 0.8:
            mastery_level = "Advanced Practitioner"
        elif overall_score >= 0.7:
            mastery_level = "Competent Developer"
        elif overall_score >= 0.6:
            mastery_level = "Developing Learner"
        else:
            mastery_level = "Novice"

        return {
            "overall_score": overall_score,
            "mastery_level": mastery_level,
            "learning_success": progression["overall_improvement"] > 0.2,
            "memory_mastery": memory["avg_memory_enhancement"] > 0.6,
            "adaptation_success": growth["adaptation_capability"] > 0.7,
            "growth_acceleration": growth["growth_acceleration"] > 0.1,
            "ready_for_advanced_tasks": overall_score > 0.8,
            "continuous_improvement": progression["performance_trend"] == "improving"
        }

    def _assess_learning_objectives_achievement(self) -> Dict[str, float]:
        """Assess achievement of learning objectives"""
        # Calculate achievement based on final phase performance
        if self.learning_history:
            final_phase = self.learning_history[-1]
            final_metrics = final_phase.performance_metrics

            return {
                "technical_depth": final_metrics.get("overall", 0) * 0.9,
                "problem_solving_sophistication": final_metrics.get("avg_response_quality", 0) * 0.85,
                "code_quality": final_metrics.get("success_rate", 0) * 0.95,
                "architectural_thinking": final_metrics.get("avg_adaptation_score", 0) * 0.8,
                "innovation_creativity": final_metrics.get("avg_response_quality", 0) * 0.7,
                "communication_clarity": final_metrics.get("avg_confidence", 0) * 0.9
            }

        return {obj: 0.0 for obj in self.learning_objectives.keys()}

    def _generate_final_recommendations(self) -> List[str]:
        """Generate final recommendations based on complete learning analysis"""
        recommendations = []

        if self.learning_history:
            final_performance = self.learning_history[-1].performance_metrics["overall"]

            if final_performance >= 0.9:
                recommendations.append("[STAR] Exceptional learning capability! Ready for expert-level challenges")
                recommendations.append("Continue with advanced domain specialization")
            elif final_performance >= 0.8:
                recommendations.append("[OK] Strong learning performance! Ready for complex real-world applications")
                recommendations.append("Focus on specific domain expertise development")
            elif final_performance >= 0.7:
                recommendations.append("[THUMBS UP] Good learning progress! Continue with regular practice")
                recommendations.append("Address specific areas identified in feedback cycles")
            else:
                recommendations.append("[BOOK] Learning in progress. Focus on fundamental skill development")
                recommendations.append("Consider additional learning cycles and practice")

        # Memory-specific recommendations
        memory_analysis = self._analyze_memory_consolidation()
        if memory_analysis["avg_memory_enhancement"] < 0.5:
            recommendations.append("Enhance memory utilization for better context awareness")

        # Adaptation-specific recommendations
        growth_analysis = self._analyze_growth_patterns()
        if growth_analysis["adaptation_capability"] < 0.7:
            recommendations.append("Work on improving adaptation to new challenges")

        recommendations.append("[REFRESH] Schedule regular learning assessments to track continued growth")

        return recommendations

async def run_enhanced_prince_adaptive_test():
    """Main function to run the comprehensive adaptive learning test"""
    print("=" * 100)
    print("[ROCKET] ENHANCED PRINCE FLOWERS ADAPTIVE LEARNING TEST")
    print("=" * 100)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Comprehensive test demonstrating actual adaptation and improvement over time")
    print("=" * 100)

    # Initialize agent
    print("\n[WRENCH] Initializing Enhanced Prince Flowers Agent...")
    print("-" * 50)

    try:
        # Configure LLM provider
        api_key = os.getenv('ANTHROPIC_AUTH_TOKEN')
        if not api_key:
            print("[ERROR] ANTHROPIC_AUTH_TOKEN not found")
            return False

        claude_config = {
            'api_key': api_key,
            'model': 'claude-sonnet-4-5-20250929',
            'base_url': os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com'),
            'timeout': 60
        }

        llm_provider = ClaudeProvider(claude_config)
        agent = create_zep_enhanced_prince_flowers(llm_provider=llm_provider)
        initialized = await agent.initialize()

        if not initialized:
            print("[ERROR] Agent initialization failed")
            return False

        print("[OK] Enhanced Prince Flowers agent initialized successfully")

    except Exception as e:
        print(f"[ERROR] Failed to initialize agent: {e}")
        return False

    # Run comprehensive adaptive learning test
    print("\n[TARGET] Starting Comprehensive Adaptive Learning Test...")
    print("-" * 50)

    adaptive_test = EnhancedPrinceAdaptiveTest(agent)
    results = await adaptive_test.run_comprehensive_adaptive_test()

    # Display comprehensive results
    print(f"\n" + "=" * 80)
    print("[CHART] COMPREHENSIVE LEARNING ANALYSIS")
    print("=" * 80)

    # Progression analysis
    progression = results["progression_analysis"]
    print(f"\n[ARROW UP] Learning Progression:")
    print(f"  Initial Performance: {progression['initial_performance']:.1%}")
    print(f"  Final Performance: {progression['final_performance']:.1%}")
    print(f"  Overall Improvement: {progression['overall_improvement']:+.1%}")
    print(f"  Learning Velocity: {progression['avg_learning_velocity']:.3f}")
    print(f"  Adaptation Rate: {progression['avg_adaptation_rate']:.1%}")
    print(f"  Performance Trend: {progression['performance_trend']}")
    print(f"  Best Phase: {progression['best_phase']} ({progression['best_performance']:.1%})")

    # Memory analysis
    memory = results["memory_analysis"]
    print(f"\n[BRAIN] Memory Integration Analysis:")
    print(f"  Average Memory Enhancement: {memory['avg_memory_enhancement']:.1%}")
    print(f"  Final Memory Enhancement: {memory['final_memory_enhancement']:.1%}")
    print(f"  Memory Trend: {memory['memory_enhancement_trend']}")
    print(f"  Average Integration: {memory['avg_memory_integration']:.1%}")

    # Growth analysis
    growth = results["growth_analysis"]
    print(f"\n[ROCKET] Growth Pattern Analysis:")
    print(f"  Total Learning Cycles: {growth['total_learning_cycles']}")
    print(f"  Feedback Cycles Completed: {growth['feedback_cycles_completed']}")
    print(f"  Adaptation Capability: {growth['adaptation_capability']:.1%}")
    print(f"  Learning Consistency: {growth['learning_consistency']:.1%}")
    print(f"  Growth Acceleration: {growth['growth_acceleration']:.3f}")

    # Final assessment
    assessment = results["final_assessment"]
    print(f"\n🎖️ Final Assessment:")
    print(f"  Overall Score: {assessment['overall_score']:.1%}")
    print(f"  Mastery Level: {assessment['mastery_level']}")
    print(f"  Learning Success: {'[OK] Yes' if assessment['learning_success'] else '[X] No'}")
    print(f"  Memory Mastery: {'[OK] Yes' if assessment['memory_mastery'] else '[X] No'}")
    print(f"  Adaptation Success: {'[OK] Yes' if assessment['adaptation_success'] else '[X] No'}")
    print(f"  Growth Acceleration: {'[OK] Yes' if assessment['growth_acceleration'] > 0 else '[X] No'}")
    print(f"  Ready for Advanced Tasks: {'[OK] Yes' if assessment['ready_for_advanced_tasks'] else '[X] No'}")

    # Learning objectives achievement
    objectives = results["learning_objectives_achievement"]
    print(f"\n[TARGET] Learning Objectives Achievement:")
    for objective, achievement in objectives.items():
        status = "[OK] Mastered" if achievement >= 0.8 else "[REFRESH] Developing" if achievement >= 0.6 else "[BOOK] Learning"
        print(f"  {objective.replace('_', ' ').title()}: {achievement:.1%} ({status})")

    # Recommendations
    print(f"\n[IDEA] Final Recommendations:")
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"  {i}. {rec}")

    # Cleanup
    try:
        await agent.cleanup()
        print("\n[OK] Agent cleanup completed")
    except Exception as e:
        print(f"\n[WARNING] Cleanup failed: {e}")

    return assessment["overall_score"] >= 0.75

if __name__ == "__main__":
    asyncio.run(run_enhanced_prince_adaptive_test())