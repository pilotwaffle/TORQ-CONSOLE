"""
Maxim AI Integration - Phase 2: Experiment Management
Advanced prompt optimization and A/B testing framework for Prince Flowers agents

This module implements Maxim's Experiment component to enable:
- Prompt optimization workflows
- A/B testing for routing strategies
- Version control for agent improvements
- Experiment tracking and comparison
"""

import asyncio
import json
import time
import logging
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime, timedelta
import statistics
import numpy as np
import os

# Import Phase 1 evaluator
from prince_flowers_evaluator import PrinceFlowersEvaluator, EvaluationMetric, AgentType

class ExperimentType(Enum):
    """Types of experiments supported"""
    PROMPT_OPTIMIZATION = "prompt_optimization"
    ROUTING_STRATEGY = "routing_strategy"
    AGENT_VERSION = "agent_version"
    TOOL_CONFIGURATION = "tool_configuration"
    PARAMETER_TUNING = "parameter_tuning"

class ExperimentStatus(Enum):
    """Experiment status tracking"""
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"
    ANALYZED = "analyzed"

class PromptVariant(Enum):
    """Prompt variant types for optimization"""
    ORIGINAL = "original"
    STRUCTURED = "structured"
    CONCISE = "concise"
    DETAILED = "detailed"
    ROLE_BASED = "role_based"
    CONTEXT_AWARE = "context_aware"

@dataclass
class ExperimentHypothesis:
    """Experiment hypothesis definition"""
    statement: str
    expected_improvement: float  # Expected improvement percentage
    confidence_level: float  # Statistical confidence (0.0-1.0)
    primary_metric: str  # Primary metric to measure
    secondary_metrics: List[str] = field(default_factory=list)

@dataclass
class ExperimentConfig:
    """Configuration for an experiment"""
    experiment_id: str
    name: str
    description: str
    experiment_type: ExperimentType
    hypothesis: ExperimentHypothesis
    control_config: Dict[str, Any]
    treatment_configs: List[Dict[str, Any]]
    sample_size: int  # Number of test cases per variant
    duration_hours: int
    success_criteria: Dict[str, float]  # Minimum acceptable improvements
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class PromptTemplate:
    """Prompt template with versioning"""
    template_id: str
    name: str
    content: str
    variant_type: PromptVariant
    version: int
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    parent_template_id: Optional[str] = None

@dataclass
class ExperimentResult:
    """Results from a single experiment variant"""
    variant_id: str
    variant_name: str
    test_cases: List[Dict[str, Any]]
    metrics: Dict[str, float]
    execution_time: float
    success_rate: float
    confidence_scores: List[float]
    error_count: int
    qualitative_feedback: List[str] = field(default_factory=list)

@dataclass
class ExperimentSummary:
    """Complete experiment summary and analysis"""
    experiment_id: str
    status: ExperimentStatus
    control_result: ExperimentResult
    treatment_results: List[ExperimentResult]
    statistical_significance: Dict[str, float]
    winning_variant: Optional[str]
    improvement_percentages: Dict[str, float]
    recommendations: List[str]
    analysis_timestamp: datetime
    next_steps: List[str]

class ExperimentManager:
    """
    Advanced experiment management system for Prince Flowers agents
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

        # Experiment storage
        self.experiments: Dict[str, ExperimentConfig] = {}
        self.results: Dict[str, ExperimentSummary] = {}
        self.prompt_templates: Dict[str, PromptTemplate] = {}
        self.experiment_history: List[Dict] = []

        # Initialize evaluator
        self.evaluator = PrinceFlowersEvaluator()

        # Experiment statistics
        self.stats = {
            "total_experiments": 0,
            "successful_experiments": 0,
            "average_improvement": 0.0,
            "best_performing_variant": None
        }

        self.logger.info("Experiment Manager initialized with Maxim AI methodology")

    def setup_logging(self):
        """Setup detailed logging for experiment management"""
        os.makedirs("E:/TORQ-CONSOLE/logs", exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('E:/TORQ-CONSOLE/logs/experiment_manager.log'),
                logging.StreamHandler()
            ]
        )

    def create_prompt_optimization_experiment(self, name: str, description: str,
                                            original_prompt: str, optimized_prompts: List[Tuple[str, str]],
                                            test_queries: List[str]) -> str:
        """
        Create a prompt optimization experiment

        Args:
            name: Experiment name
            description: Experiment description
            original_prompt: Original prompt template
            optimized_prompts: List of (prompt_name, prompt_content) tuples
            test_queries: List of test queries for evaluation

        Returns:
            Experiment ID
        """
        experiment_id = str(uuid.uuid4())

        # Create original prompt template
        original_template = PromptTemplate(
            template_id=f"{experiment_id}_original",
            name="Original Prompt",
            content=original_prompt,
            variant_type=PromptVariant.ORIGINAL,
            version=1
        )
        self.prompt_templates[original_template.template_id] = original_template

        # Create optimized prompt templates
        treatment_configs = []
        for i, (prompt_name, prompt_content) in enumerate(optimized_prompts):
            template_id = f"{experiment_id}_treatment_{i+1}"
            template = PromptTemplate(
                template_id=template_id,
                name=prompt_name,
                content=prompt_content,
                variant_type=self._detect_variant_type(prompt_name),
                version=1,
                parent_template_id=original_template.template_id
            )
            self.prompt_templates[template_id] = template

            treatment_configs.append({
                "template_id": template_id,
                "prompt_content": prompt_content,
                "variant_name": prompt_name
            })

        # Create experiment configuration
        experiment = ExperimentConfig(
            experiment_id=experiment_id,
            name=name,
            description=description,
            experiment_type=ExperimentType.PROMPT_OPTIMIZATION,
            hypothesis=ExperimentHypothesis(
                statement=f"Optimized prompts will improve response quality by at least 10%",
                expected_improvement=0.10,
                confidence_level=0.95,
                primary_metric="overall_quality_score",
                secondary_metrics=["reasoning_quality", "response_relevance"]
            ),
            control_config={
                "template_id": original_template.template_id,
                "prompt_content": original_prompt,
                "variant_name": "Original"
            },
            treatment_configs=treatment_configs,
            sample_size=len(test_queries),
            duration_hours=24,
            success_criteria={
                "overall_quality_score": 0.05,  # 5% minimum improvement
                "reasoning_quality": 0.03,
                "response_relevance": 0.05
            },
            tags=["prompt_optimization", "quality_improvement"]
        )

        self.experiments[experiment_id] = experiment
        self.stats["total_experiments"] += 1

        self.logger.info(f"Created prompt optimization experiment: {experiment_id}")
        return experiment_id

    def create_routing_strategy_experiment(self, name: str, description: str,
                                       routing_strategies: List[Tuple[str, Dict]],
                                       test_queries: List[str]) -> str:
        """
        Create an A/B testing experiment for routing strategies

        Args:
            name: Experiment name
            description: Experiment description
            routing_strategies: List of (strategy_name, routing_config) tuples
            test_queries: List of test queries for evaluation

        Returns:
            Experiment ID
        """
        experiment_id = str(uuid.uuid4())

        # Setup control routing (default strategy)
        control_config = {
            "strategy_name": "default_routing",
            "routing_logic": "existing_orchestrator_logic",
            "parameters": {}
        }

        # Setup treatment routing strategies
        treatment_configs = []
        for strategy_name, routing_config in routing_strategies:
            treatment_configs.append({
                "strategy_name": strategy_name,
                "routing_logic": routing_config.get("logic", "enhanced_routing"),
                "parameters": routing_config.get("parameters", {}),
                "variant_name": strategy_name
            })

        # Create experiment configuration
        experiment = ExperimentConfig(
            experiment_id=experiment_id,
            name=name,
            description=description,
            experiment_type=ExperimentType.ROUTING_STRATEGY,
            hypothesis=ExperimentHypothesis(
                statement=f"Enhanced routing strategies will improve query routing efficiency by at least 15%",
                expected_improvement=0.15,
                confidence_level=0.90,
                primary_metric="tool_selection_efficiency",
                secondary_metrics=["execution_performance", "success_rate"]
            ),
            control_config=control_config,
            treatment_configs=treatment_configs,
            sample_size=len(test_queries),
            duration_hours=48,
            success_criteria={
                "tool_selection_efficiency": 0.10,  # 10% minimum improvement
                "execution_performance": 0.05,
                "success_rate": 0.02
            },
            tags=["routing_optimization", "ab_testing"]
        )

        self.experiments[experiment_id] = experiment
        self.stats["total_experiments"] += 1

        self.logger.info(f"Created routing strategy experiment: {experiment_id}")
        return experiment_id

    async def run_prompt_optimization_experiment(self, experiment_id: str,
                                              test_queries: List[str]) -> ExperimentSummary:
        """
        Run a prompt optimization experiment

        Args:
            experiment_id: ID of experiment to run
            test_queries: List of test queries

        Returns:
            Experiment summary with results
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.experiment_type != ExperimentType.PROMPT_OPTIMIZATION:
            raise ValueError("Experiment is not a prompt optimization type")

        self.logger.info(f"Running prompt optimization experiment: {experiment.name}")

        # Test control variant (original prompt)
        control_result = await self._test_prompt_variant(
            experiment.control_config,
            test_queries,
            "Control"
        )

        # Test treatment variants (optimized prompts)
        treatment_results = []
        for treatment_config in experiment.treatment_configs:
            result = await self._test_prompt_variant(
                treatment_config,
                test_queries,
                treatment_config["variant_name"]
            )
            treatment_results.append(result)

        # Analyze results
        summary = await self._analyze_experiment_results(
            experiment,
            control_result,
            treatment_results
        )

        # Store results
        self.results[experiment_id] = summary
        self.experiment_history.append({
            "experiment_id": experiment_id,
            "timestamp": datetime.now().isoformat(),
            "status": summary.status.value,
            "improvement": summary.improvement_percentages.get("overall_quality_score", 0)
        })

        # Save results
        await self._save_experiment_results(experiment_id, summary)

        self.logger.info(f"Completed experiment: {experiment.name}")
        return summary

    async def _test_prompt_variant(self, variant_config: Dict, test_queries: List[str],
                                 variant_name: str) -> ExperimentResult:
        """Test a single prompt variant against test queries"""
        start_time = time.time()

        test_results = []
        confidence_scores = []
        error_count = 0

        prompt_content = variant_config["prompt_content"]

        for query in test_queries:
            try:
                # Simulate applying the prompt variant to the agent
                # In real implementation, this would modify the agent's prompt
                modified_query = f"{prompt_content}\n\nUser Query: {query}"

                # Evaluate using mock agent (replace with actual agent call)
                result = await self._evaluate_with_prompt(modified_query, prompt_content)

                test_results.append({
                    "query": query,
                    "response": result["response"],
                    "success": result["success"],
                    "confidence": result["confidence"],
                    "execution_time": result["execution_time"],
                    "metrics": result.get("metrics", {})
                })

                confidence_scores.append(result["confidence"])

                if not result["success"]:
                    error_count += 1

            except Exception as e:
                self.logger.error(f"Error testing query '{query}': {e}")
                error_count += 1
                test_results.append({
                    "query": query,
                    "response": f"Error: {str(e)}",
                    "success": False,
                    "confidence": 0.0,
                    "execution_time": 0.0,
                    "metrics": {}
                })

        execution_time = time.time() - start_time

        # Calculate aggregate metrics
        metrics = self._calculate_aggregate_metrics(test_results)

        return ExperimentResult(
            variant_id=variant_config.get("template_id", variant_name),
            variant_name=variant_name,
            test_cases=test_results,
            metrics=metrics,
            execution_time=execution_time,
            success_rate=len([r for r in test_results if r["success"]]) / len(test_results),
            confidence_scores=confidence_scores,
            error_count=error_count
        )

    async def _evaluate_with_prompt(self, query: str, prompt_content: str) -> Dict[str, Any]:
        """Evaluate a query with a specific prompt"""
        # Simulate prompt-based evaluation
        # In real implementation, this would use the actual agent with modified prompt

        # Simulate processing time
        await asyncio.sleep(0.1 + len(query) * 0.001)

        # Generate mock response based on prompt and query
        if "structured" in prompt_content.lower():
            response = f"Structured response to: {query[:50]}...\n\n1. Analysis\n2. Implementation\n3. Conclusion"
            confidence = 0.88
        elif "concise" in prompt_content.lower():
            response = f"Concise answer: {query[:50]}... - Key points summarized efficiently."
            confidence = 0.82
        elif "detailed" in prompt_content.lower():
            response = f"Detailed comprehensive response to: {query[:50]}...\n\nExtensive analysis with multiple perspectives and in-depth exploration of the topic."
            confidence = 0.91
        else:
            response = f"Standard response to: {query[:50]}... - Well-formulated answer addressing the query."
            confidence = 0.85

        # Calculate mock metrics
        metrics = {
            "reasoning_quality": confidence + 0.05,
            "response_relevance": confidence,
            "tool_selection_efficiency": 0.85,
            "multi_step_accuracy": confidence - 0.02,
            "execution_performance": 0.88,
            "error_handling": 0.95,
            "confidence_calibration": confidence - 0.03
        }

        return {
            "response": response,
            "success": True,
            "confidence": confidence,
            "execution_time": 0.5 + len(query) * 0.001,
            "metrics": metrics
        }

    def _calculate_aggregate_metrics(self, test_results: List[Dict]) -> Dict[str, float]:
        """Calculate aggregate metrics from test results"""
        if not test_results:
            return {}

        # Aggregate all metric values
        all_metrics = {}
        for result in test_results:
            metrics = result.get("metrics", {})
            for metric_name, value in metrics.items():
                if metric_name not in all_metrics:
                    all_metrics[metric_name] = []
                all_metrics[metric_name].append(value)

        # Calculate averages
        aggregate_metrics = {}
        for metric_name, values in all_metrics.items():
            if values:
                aggregate_metrics[metric_name] = statistics.mean(values)

        # Add additional aggregate metrics
        aggregate_metrics["overall_quality_score"] = self._calculate_overall_quality(aggregate_metrics)
        aggregate_metrics["success_rate"] = len([r for r in test_results if r["success"]]) / len(test_results)
        aggregate_metrics["average_confidence"] = statistics.mean([r["confidence"] for r in test_results])

        return aggregate_metrics

    def _calculate_overall_quality(self, metrics: Dict[str, float]) -> float:
        """Calculate overall quality score from individual metrics"""
        weights = {
            "reasoning_quality": 0.25,
            "response_relevance": 0.20,
            "tool_selection_efficiency": 0.15,
            "multi_step_accuracy": 0.15,
            "execution_performance": 0.10,
            "error_handling": 0.10,
            "confidence_calibration": 0.05
        }

        total_score = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in metrics:
                total_score += metrics[metric] * weight
                total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    async def _analyze_experiment_results(self, experiment: ExperimentConfig,
                                        control_result: ExperimentResult,
                                        treatment_results: List[ExperimentResult]) -> ExperimentSummary:
        """Analyze experiment results and determine statistical significance"""

        # Calculate improvements for each treatment
        improvements = {}
        winning_variant = "Control"
        best_improvement = 0.0

        for treatment in treatment_results:
            treatment_improvements = {}
            for metric in experiment.hypothesis.secondary_metrics + [experiment.hypothesis.primary_metric]:
                if metric in control_result.metrics and metric in treatment.metrics:
                    control_value = control_result.metrics[metric]
                    treatment_value = treatment.metrics[metric]
                    improvement = (treatment_value - control_value) / control_value
                    treatment_improvements[metric] = improvement

            improvements[treatment.variant_name] = treatment_improvements

            # Check if this is the winning variant
            primary_improvement = treatment_improvements.get(experiment.hypothesis.primary_metric, 0)
            if primary_improvement > best_improvement:
                best_improvement = primary_improvement
                winning_variant = treatment.variant_name

        # Calculate statistical significance (simplified)
        statistical_significance = {}
        for treatment_name, treatment_improvements in improvements.items():
            for metric, improvement in treatment_improvements.items():
                # Simplified significance calculation
                # In real implementation, use proper statistical tests
                sample_size = experiment.sample_size
                if sample_size > 10:
                    # Mock significance calculation
                    significance = min(0.99, abs(improvement) * math.sqrt(sample_size) / 2)
                    statistical_significance[f"{treatment_name}_{metric}"] = significance

        # Generate recommendations
        recommendations = self._generate_experiment_recommendations(
            experiment, control_result, treatment_results, improvements, winning_variant
        )

        # Determine next steps
        next_steps = self._determine_next_steps(
            experiment, improvements, winning_variant, statistical_significance
        )

        return ExperimentSummary(
            experiment_id=experiment.experiment_id,
            status=ExperimentStatus.COMPLETED,
            control_result=control_result,
            treatment_results=treatment_results,
            statistical_significance=statistical_significance,
            winning_variant=winning_variant if best_improvement > 0 else None,
            improvement_percentages=improvements,
            recommendations=recommendations,
            analysis_timestamp=datetime.now(),
            next_steps=next_steps
        )

    def _generate_experiment_recommendations(self, experiment: ExperimentConfig,
                                           control_result: ExperimentResult,
                                           treatment_results: List[ExperimentResult],
                                           improvements: Dict, winning_variant: str) -> List[str]:
        """Generate recommendations based on experiment results"""
        recommendations = []

        # Check if any variant meets success criteria
        successful_variants = []
        for treatment_name, treatment_improvements in improvements.items():
            meets_criteria = True
            for metric, threshold in experiment.success_criteria.items():
                if treatment_improvements.get(metric, 0) < threshold:
                    meets_criteria = False
                    break
            if meets_criteria:
                successful_variants.append(treatment_name)

        if successful_variants:
            recommendations.append(f"Successful variants identified: {', '.join(successful_variants)}")
            recommendations.append(f"Recommend deploying winning variant: {winning_variant}")
        else:
            recommendations.append("No variants met success criteria")
            recommendations.append("Consider refining prompt templates or testing different approaches")

        # Specific recommendations based on metrics
        for treatment_name, treatment_improvements in improvements.items():
            primary_improvement = treatment_improvements.get(experiment.hypothesis.primary_metric, 0)
            if primary_improvement > 0.15:
                recommendations.append(f"{treatment_name} shows exceptional improvement ({primary_improvement:.1%}) - prioritize for deployment")
            elif primary_improvement > 0.05:
                recommendations.append(f"{treatment_name} shows moderate improvement ({primary_improvement:.1%}) - consider for further testing")
            else:
                recommendations.append(f"{treatment_name} shows minimal improvement ({primary_improvement:.1%}) - consider reworking or discontinuing")

        return recommendations

    def _determine_next_steps(self, experiment: ExperimentConfig,
                            improvements: Dict, winning_variant: str,
                            statistical_significance: Dict) -> List[str]:
        """Determine next steps based on experiment results"""
        next_steps = []

        # Check if results are statistically significant
        significant_results = any(sig > 0.95 for sig in statistical_significance.values())

        if winning_variant != "Control" and significant_results:
            next_steps.append("Deploy winning variant to production")
            next_steps.append("Monitor performance in production environment")
            next_steps.append("Plan follow-up experiment to validate improvements")
        elif winning_variant != "Control":
            next_steps.append("Run additional tests to validate results")
            next_steps.append("Increase sample size for better statistical significance")
        else:
            next_steps.append("Analyze why variants underperformed")
            next_steps.append("Design new experiment with different approaches")
            next_steps.append("Consider testing alternative optimization strategies")

        # Always save learnings
        next_steps.append("Document learnings and insights for future experiments")
        next_steps.append("Update prompt template library with findings")

        return next_steps

    def _detect_variant_type(self, prompt_name: str) -> PromptVariant:
        """Detect prompt variant type from name"""
        name_lower = prompt_name.lower()
        if "structured" in name_lower:
            return PromptVariant.STRUCTURED
        elif "concise" in name_lower:
            return PromptVariant.CONCISE
        elif "detailed" in name_lower:
            return PromptVariant.DETAILED
        elif "role" in name_lower:
            return PromptVariant.ROLE_BASED
        elif "context" in name_lower:
            return PromptVariant.CONTEXT_AWARE
        else:
            return PromptVariant.ORIGINAL

    async def _save_experiment_results(self, experiment_id: str, summary: ExperimentSummary):
        """Save experiment results to file"""
        os.makedirs("E:/TORQ-CONSOLE/experiment_results", exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"E:/TORQ-CONSOLE/experiment_results/experiment_{experiment_id}_{timestamp}.json"

        # Convert to serializable format
        summary_data = asdict(summary)
        summary_data["analysis_timestamp"] = summary.analysis_timestamp.isoformat()
        summary_data["status"] = summary.status.value

        with open(results_file, 'w') as f:
            json.dump(summary_data, f, indent=2)

        self.logger.info(f"Experiment results saved to: {results_file}")

    def get_experiment_summary(self, experiment_id: str) -> Optional[ExperimentSummary]:
        """Get summary of a specific experiment"""
        return self.results.get(experiment_id)

    def list_experiments(self, status_filter: Optional[ExperimentStatus] = None) -> List[ExperimentConfig]:
        """List all experiments, optionally filtered by status"""
        experiments = list(self.experiments.values())
        if status_filter:
            experiment_ids = [exp_id for exp_id, summary in self.results.items()
                           if summary.status == status_filter]
            experiments = [exp for exp in experiments if exp.experiment_id in experiment_ids]
        return experiments

    def get_experiment_statistics(self) -> Dict[str, Any]:
        """Get overall experiment statistics"""
        completed_experiments = [summary for summary in self.results.values()
                              if summary.status == ExperimentStatus.COMPLETED]

        if completed_experiments:
            improvements = []
            for summary in completed_experiments:
                if summary.winning_variant and summary.winning_variant != "Control":
                    primary_metric = "overall_quality_score"
                    for variant, metrics in summary.improvement_percentages.items():
                        if variant == summary.winning_variant and primary_metric in metrics:
                            improvements.append(metrics[primary_metric])

            avg_improvement = statistics.mean(improvements) if improvements else 0.0
            success_rate = len([s for s in completed_experiments if s.winning_variant != "Control"]) / len(completed_experiments)
        else:
            avg_improvement = 0.0
            success_rate = 0.0

        return {
            "total_experiments": len(self.experiments),
            "completed_experiments": len(completed_experiments),
            "successful_experiments": len([s for s in completed_experiments if s.winning_variant != "Control"]),
            "average_improvement": avg_improvement,
            "success_rate": success_rate,
            "total_prompt_templates": len(self.prompt_templates)
        }

    def print_experiment_summary(self, experiment_id: str):
        """Print formatted experiment summary"""
        summary = self.get_experiment_summary(experiment_id)
        if not summary:
            print(f"Experiment {experiment_id} not found")
            return

        experiment = self.experiments[experiment_id]

        print(f"\n{'='*80}")
        print(f"EXPERIMENT SUMMARY: {experiment.name}")
        print(f"{'='*80}")
        print(f"Experiment ID: {experiment_id}")
        print(f"Type: {experiment.experiment_type.value}")
        print(f"Status: {summary.status.value}")
        print(f"Analysis Date: {summary.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"\nHYPOTHESIS:")
        print(f"  {experiment.hypothesis.statement}")
        print(f"  Expected Improvement: {experiment.hypothesis.expected_improvement:.1%}")
        print(f"  Primary Metric: {experiment.hypothesis.primary_metric}")

        print(f"\nRESULTS:")
        print(f"  Control Performance:")
        print(f"    Overall Quality: {summary.control_result.metrics.get('overall_quality_score', 0):.1%}")
        print(f"    Success Rate: {summary.control_result.success_rate:.1%}")
        print(f"    Execution Time: {summary.control_result.execution_time:.2f}s")

        print(f"  Treatment Variants:")
        for treatment in summary.treatment_results:
            improvements = summary.improvement_percentages.get(treatment.variant_name, {})
            primary_improvement = improvements.get(experiment.hypothesis.primary_metric, 0)
            status = "[WINNER]" if treatment.variant_name == summary.winning_variant else "       "
            print(f"    {status} {treatment.variant_name}:")
            print(f"      Overall Quality: {treatment.metrics.get('overall_quality_score', 0):.1%} ({primary_improvement:+.1%})")
            print(f"      Success Rate: {treatment.success_rate:.1%}")
            print(f"      Execution Time: {treatment.execution_time:.2f}s")

        print(f"\nWINNING VARIANT: {summary.winning_variant or 'No significant improvement'}")

        print(f"\nRECOMMENDATIONS:")
        for i, rec in enumerate(summary.recommendations, 1):
            print(f"  {i}. {rec}")

        print(f"\nNEXT STEPS:")
        for i, step in enumerate(summary.next_steps, 1):
            print(f"  {i}. {step}")

        print(f"{'='*80}")

# Main execution function for testing
async def main():
    """Main execution function for testing experiment manager"""
    print("Maxim AI - Phase 2: Experiment Management")
    print("=" * 60)

    # Initialize experiment manager
    manager = ExperimentManager()

    # Example prompt optimization experiment
    print("\nCreating Prompt Optimization Experiment...")

    original_prompt = "You are Prince Flowers, an AI assistant. Please help the user with their request."

    optimized_prompts = [
        ("Structured Prompt", """You are Prince Flowers, an advanced AI assistant.

STRUCTURE YOUR RESPONSE:
1. Understand the user's request
2. Provide step-by-step analysis
3. Deliver comprehensive solution

User Request: {query}"""),

        ("Concise Prompt", """Prince Flowers AI - Be direct and efficient.

Task: {query}
Response: Provide clear, concise answer."""),

        ("Role-Based Prompt", """You are Prince Flowers, expert AI assistant with deep knowledge in multiple domains.

EXPERTISE: Analysis, problem-solving, tool integration
APPROACH: Methodical, thorough, user-focused

User Query: {query}
Your Response:""")
    ]

    test_queries = [
        "Explain the benefits of async programming in Python",
        "Search for recent developments in quantum computing",
        "Create a simple REST API example",
        "What are your capabilities?",
        "Compare and contrast different machine learning approaches"
    ]

    # Create experiment
    experiment_id = manager.create_prompt_optimization_experiment(
        name="Prompt Structure Optimization Test",
        description="Testing different prompt structures to improve response quality",
        original_prompt=original_prompt,
        optimized_prompts=optimized_prompts,
        test_queries=test_queries
    )

    print(f"[OK] Created experiment: {experiment_id}")

    # Run experiment
    print("\nRunning experiment...")
    summary = await manager.run_prompt_optimization_experiment(experiment_id, test_queries)

    # Print results
    manager.print_experiment_summary(experiment_id)

    # Print overall statistics
    stats = manager.get_experiment_statistics()
    print(f"\nOverall Statistics:")
    print(f"  Total Experiments: {stats['total_experiments']}")
    print(f"  Completed Experiments: {stats['completed_experiments']}")
    print(f"  Successful Experiments: {stats['successful_experiments']}")
    print(f"  Average Improvement: {stats['average_improvement']:.1%}")
    print(f"  Success Rate: {stats['success_rate']:.1%}")

if __name__ == "__main__":
    import math
    asyncio.run(main())