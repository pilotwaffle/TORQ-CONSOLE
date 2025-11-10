"""
Maxim AI Integration - Phase 2: Prompt Optimization Workflows
Comprehensive prompt optimization workflow system for Prince Flowers agents

This module implements advanced prompt optimization workflows:
- Automated prompt generation and testing
- Multi-objective optimization
- Performance tracking and analysis
- Iterative improvement cycles
- Template management and versioning
"""

import asyncio
import json
import time
import logging
import random
import uuid
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime, timedelta
import statistics
import os

from experiment_manager import ExperimentManager, PromptTemplate, PromptVariant
from version_control import VersionControlSystem, ChangeRecord, ChangeCategory

class OptimizationObjective(Enum):
    """Optimization objectives for prompt engineering"""
    RESPONSE_QUALITY = "response_quality"
    EXECUTION_SPEED = "execution_speed"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    CONSISTENCY = "consistency"
    SAFETY = "safety"
    COST_EFFICIENCY = "cost_efficiency"

class OptimizationStrategy(Enum):
    """Prompt optimization strategies"""
    HILL_CLIMBING = "hill_climbing"
    GENETIC_ALGORITHM = "genetic_algorithm"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    SIMULATED_ANNEALING = "simulated_annealing"

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class OptimizationTarget:
    """Target for prompt optimization"""
    objective: OptimizationObjective
    target_value: float
    weight: float  # Importance weight (0.0-1.0)
    constraint: Optional[str] = None  # Constraint description

@dataclass
class PromptVariation:
    """Generated variation of a prompt template"""
    template_id: str
    content: str
    generation_method: str
    parent_template: str
    score: float = 0.0
    evaluation_metrics: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class OptimizationIteration:
    """Single iteration in optimization workflow"""
    iteration_number: int
    best_prompt: PromptVariation
    all_variants: List[PromptVariation]
    improvement: float
    convergence_score: float
    execution_time: float
    objectives_met: Dict[str, bool]

@dataclass
class OptimizationWorkflow:
    """Complete optimization workflow configuration"""
    workflow_id: str
    name: str
    description: str
    base_prompt: str
    agent_type: str
    objectives: List[OptimizationTarget]
    optimization_strategy: OptimizationStrategy
    max_iterations: int
    convergence_threshold: float
    test_queries: List[str]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    iterations: List[OptimizationIteration] = field(default_factory=list)
    best_overall_prompt: Optional[PromptVariation] = None

class PromptOptimizationWorkflow:
    """
    Advanced prompt optimization workflow system
    """

    def __init__(self, experiment_manager: ExperimentManager, version_control: VersionControlSystem):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

        self.experiment_manager = experiment_manager
        self.version_control = version_control

        # Workflow storage
        self.workflows: Dict[str, OptimizationWorkflow] = {}
        self.prompt_templates: Dict[str, PromptTemplate] = {}
        self.optimization_history: List[Dict] = []

        # Configuration
        self.workflows_dir = "E:/TORQ-CONSOLE/optimization_workflows"
        self.templates_dir = f"{self.workflows_dir}/templates"

        # Initialize directories
        self._initialize_directories()

        # Optimization algorithms
        self.optimizers = {
            OptimizationStrategy.HILL_CLIMBING: self._hill_climbing_optimization,
            OptimizationStrategy.GENETIC_ALGORITHM: self._genetic_algorithm_optimization,
            OptimizationStrategy.BAYESIAN_OPTIMIZATION: self._bayesian_optimization,
            OptimizationStrategy.GRID_SEARCH: self._grid_search_optimization,
            OptimizationStrategy.RANDOM_SEARCH: self._random_search_optimization,
            OptimizationStrategy.SIMULATED_ANNEALING: self._simulated_annealing_optimization
        }

        self.logger.info("Prompt Optimization Workflow system initialized")

    def setup_logging(self):
        """Setup logging for optimization workflows"""
        os.makedirs("E:/TORQ-CONSOLE/logs", exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('E:/TORQ-CONSOLE/logs/prompt_optimization.log'),
                logging.StreamHandler()
            ]
        )

    def _initialize_directories(self):
        """Initialize required directories"""
        directories = [
            self.workflows_dir,
            self.templates_dir,
            f"{self.workflows_dir}/results",
            f"{self.workflows_dir}/cache"
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def create_optimization_workflow(self, name: str, description: str,
                                   base_prompt: str, agent_type: str,
                                   objectives: List[Dict[str, Any]],
                                   strategy: str, test_queries: List[str],
                                   config: Dict[str, Any]) -> str:
        """
        Create a new prompt optimization workflow

        Args:
            name: Workflow name
            description: Workflow description
            base_prompt: Base prompt to optimize
            agent_type: Target agent type
            objectives: List of optimization objectives
            strategy: Optimization strategy
            test_queries: Test queries for evaluation
            config: Additional configuration

        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())

        # Convert objectives
        optimization_objectives = []
        for obj in objectives:
            optimization_objectives.append(OptimizationTarget(
                objective=OptimizationObjective(obj["objective"]),
                target_value=obj["target_value"],
                weight=obj["weight"],
                constraint=obj.get("constraint")
            ))

        # Create workflow
        workflow = OptimizationWorkflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            base_prompt=base_prompt,
            agent_type=agent_type,
            objectives=optimization_objectives,
            optimization_strategy=OptimizationStrategy(strategy),
            max_iterations=config.get("max_iterations", 20),
            convergence_threshold=config.get("convergence_threshold", 0.01),
            test_queries=test_queries
        )

        self.workflows[workflow_id] = workflow

        # Save workflow
        self._save_workflow(workflow)

        self.logger.info(f"Created optimization workflow: {workflow_id}")
        return workflow_id

    async def run_optimization_workflow(self, workflow_id: str) -> OptimizationWorkflow:
        """
        Run an optimization workflow

        Args:
            workflow_id: ID of workflow to run

        Returns:
            Completed workflow with results
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        self.logger.info(f"Starting optimization workflow: {workflow.name}")
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()

        # Initialize with base prompt
        base_variation = PromptVariation(
            template_id=f"{workflow_id}_base",
            content=workflow.base_prompt,
            generation_method="base_prompt",
            parent_template="",
            score=0.0
        )

        # Evaluate base prompt
        await self._evaluate_prompt_variation(base_variation, workflow.test_queries, workflow)

        current_best = base_variation
        all_iterations = []

        # Run optimization iterations
        for iteration in range(workflow.max_iterations):
            self.logger.info(f"Running iteration {iteration + 1}/{workflow.max_iterations}")

            # Generate variations
            variations = await self._generate_prompt_variations(
                current_best, workflow, iteration
            )

            # Evaluate all variations
            for variation in variations:
                await self._evaluate_prompt_variation(
                    variation, workflow.test_queries, workflow
                )

            # Select best variation
            best_variation = max(variations, key=lambda v: v.score)
            improvement = best_variation.score - current_best.score

            # Calculate convergence
            convergence_score = self._calculate_convergence_score(
                workflow, all_iterations, best_variation
            )

            # Create iteration record
            iteration_record = OptimizationIteration(
                iteration_number=iteration + 1,
                best_prompt=best_variation,
                all_variants=variations,
                improvement=improvement,
                convergence_score=convergence_score,
                execution_time=0.0,  # Would track actual time
                objectives_met=self._check_objectives_met(best_variation, workflow)
            )

            all_iterations.append(iteration_record)

            # Check convergence
            if convergence_score >= workflow.convergence_threshold and iteration > 2:
                self.logger.info(f"Converged after {iteration + 1} iterations")
                break

            # Update best prompt
            current_best = best_variation

        # Complete workflow
        workflow.status = WorkflowStatus.COMPLETED
        workflow.completed_at = datetime.now()
        workflow.iterations = all_iterations
        workflow.best_overall_prompt = current_best

        # Save results
        self._save_workflow(workflow)
        await self._save_workflow_results(workflow)

        # Create version control entry
        await self._create_version_from_workflow(workflow)

        self.logger.info(f"Completed optimization workflow: {workflow.name}")
        return workflow

    async def _generate_prompt_variations(self, base_variation: PromptVariation,
                                         workflow: OptimizationWorkflow,
                                         iteration: int) -> List[PromptVariation]:
        """Generate prompt variations using the specified strategy"""
        optimizer = self.optimizers.get(workflow.optimization_strategy)
        if not optimizer:
            raise ValueError(f"Unknown optimization strategy: {workflow.optimization_strategy}")

        return await optimizer(base_variation, workflow, iteration)

    async def _hill_climbing_optimization(self, base_variation: PromptVariation,
                                        workflow: OptimizationWorkflow,
                                        iteration: int) -> List[PromptVariation]:
        """Hill climbing optimization strategy"""
        variations = []
        base_prompt = base_variation.content

        # Generate variations by modifying different aspects
        modifications = [
            self._add_structure_prompt(base_prompt),
            self._add_examples_prompt(base_prompt),
            self._add_constraints_prompt(base_prompt),
            self._simplify_prompt(base_prompt),
            self._add_role_prompt(base_prompt),
            self._add_context_prompt(base_prompt)
        ]

        for i, modified_prompt in enumerate(modifications):
            variation = PromptVariation(
                template_id=f"{workflow.workflow_id}_iter{iteration}_var{i}",
                content=modified_prompt,
                generation_method="hill_climbing",
                parent_template=base_variation.template_id
            )
            variations.append(variation)

        return variations

    async def _genetic_algorithm_optimization(self, base_variation: PromptVariation,
                                           workflow: OptimizationWorkflow,
                                           iteration: int) -> List[PromptVariation]:
        """Genetic algorithm optimization strategy"""
        variations = []

        # Create population through crossover and mutation
        if iteration == 0:
            # First iteration - create diverse initial population
            parents = [base_variation.content]
        else:
            # Use previous best as parent
            parents = [base_variation.content]

        # Generate offspring
        for i in range(6):  # Population size
            if len(parents) >= 2 and random.random() < 0.7:
                # Crossover
                parent1, parent2 = random.sample(parents, 2)
                child_prompt = self._crossover_prompts(parent1, parent2)
            else:
                # Mutation
                parent = random.choice(parents)
                child_prompt = self._mutate_prompt(parent)

            # Apply mutation
            if random.random() < 0.3:
                child_prompt = self._mutate_prompt(child_prompt)

            variation = PromptVariation(
                template_id=f"{workflow.workflow_id}_gen{iteration}_pop{i}",
                content=child_prompt,
                generation_method="genetic_algorithm",
                parent_template=base_variation.template_id
            )
            variations.append(variation)

        return variations

    async def _bayesian_optimization(self, base_variation: PromptVariation,
                                   workflow: OptimizationWorkflow,
                                   iteration: int) -> List[PromptVariation]:
        """Bayesian optimization strategy (simplified)"""
        variations = []

        # Use previous iterations to guide search
        if workflow.iterations:
            # Analyze what worked in previous iterations
            successful_patterns = self._analyze_successful_patterns(workflow)
            base_prompt = base_variation.content

            # Generate variations based on successful patterns
            for pattern in successful_patterns[:3]:
                modified_prompt = self._apply_pattern(base_prompt, pattern)
                variation = PromptVariation(
                    template_id=f"{workflow.workflow_id}_bayes{iteration}_pat{len(variations)}",
                    content=modified_prompt,
                    generation_method="bayesian_optimization",
                    parent_template=base_variation.template_id
                )
                variations.append(variation)
        else:
            # First iteration - diverse exploration
            variations = await self._hill_climbing_optimization(base_variation, workflow, iteration)

        return variations

    async def _grid_search_optimization(self, base_variation: PromptVariation,
                                     workflow: OptimizationWorkflow,
                                     iteration: int) -> List[PromptVariation]:
        """Grid search optimization strategy"""
        variations = []

        # Define grid of parameters to test
        parameter_grid = {
            "add_structure": [True, False],
            "add_examples": [True, False],
            "add_constraints": [True, False],
            "add_role": [True, False],
            "detail_level": ["concise", "standard", "detailed"]
        }

        # Generate combinations (sample for efficiency)
        combinations = self._sample_grid_combinations(parameter_grid, 6)

        base_prompt = base_variation.content
        for i, params in enumerate(combinations):
            modified_prompt = base_prompt

            # Apply parameters
            if params.get("add_structure"):
                modified_prompt = self._add_structure_prompt(modified_prompt)
            if params.get("add_examples"):
                modified_prompt = self._add_examples_prompt(modified_prompt)
            if params.get("add_constraints"):
                modified_prompt = self._add_constraints_prompt(modified_prompt)
            if params.get("add_role"):
                modified_prompt = self._add_role_prompt(modified_prompt)

            # Adjust detail level
            if params.get("detail_level") == "concise":
                modified_prompt = self._simplify_prompt(modified_prompt)
            elif params.get("detail_level") == "detailed":
                modified_prompt = self._add_detail_prompt(modified_prompt)

            variation = PromptVariation(
                template_id=f"{workflow.workflow_id}_grid{iteration}_comb{i}",
                content=modified_prompt,
                generation_method="grid_search",
                parent_template=base_variation.template_id
            )
            variations.append(variation)

        return variations

    async def _random_search_optimization(self, base_variation: PromptVariation,
                                       workflow: OptimizationWorkflow,
                                       iteration: int) -> List[PromptVariation]:
        """Random search optimization strategy"""
        variations = []

        # Generate random modifications
        modifications = [
            self._add_structure_prompt,
            self._add_examples_prompt,
            self._add_constraints_prompt,
            self._add_role_prompt,
            self._add_context_prompt,
            self._simplify_prompt,
            self._add_detail_prompt
        ]

        base_prompt = base_variation.content
        for i in range(6):
            # Apply random modifications
            modified_prompt = base_prompt
            num_modifications = random.randint(1, 3)

            for _ in range(num_modifications):
                modifier = random.choice(modifications)
                modified_prompt = modifier(modified_prompt)

            variation = PromptVariation(
                template_id=f"{workflow.workflow_id}_rand{iteration}_var{i}",
                content=modified_prompt,
                generation_method="random_search",
                parent_template=base_variation.template_id
            )
            variations.append(variation)

        return variations

    async def _simulated_annealing_optimization(self, base_variation: PromptVariation,
                                             workflow: OptimizationWorkflow,
                                             iteration: int) -> List[PromptVariation]:
        """Simulated annealing optimization strategy"""
        variations = []

        # Temperature decreases over iterations
        temperature = max(0.1, 1.0 - (iteration / workflow.max_iterations))

        base_prompt = base_variation.content

        # Generate variations with temperature-controlled randomness
        for i in range(6):
            if random.random() < temperature:
                # High temperature - more exploration
                modified_prompt = self._random_modification(base_prompt)
            else:
                # Low temperature - more exploitation
                modified_prompt = self._guided_modification(base_prompt)

            variation = PromptVariation(
                template_id=f"{workflow.workflow_id}_anneal{iteration}_var{i}",
                content=modified_prompt,
                generation_method="simulated_annealing",
                parent_template=base_variation.template_id
            )
            variations.append(variation)

        return variations

    def _add_structure_prompt(self, prompt: str) -> str:
        """Add structured format to prompt"""
        return f"""{prompt}

STRUCTURE YOUR RESPONSE:
1. Understand the user's request clearly
2. Provide step-by-step reasoning
3. Deliver a comprehensive solution
4. Include relevant examples if applicable"""

    def _add_examples_prompt(self, prompt: str) -> str:
        """Add examples to prompt"""
        return f"""{prompt}

EXAMPLES:
For analysis requests, break down complex topics into understandable components.
For creative tasks, provide multiple options and explain your reasoning.
For technical questions, include code examples and explanations."""

    def _add_constraints_prompt(self, prompt: str) -> str:
        """Add constraints to prompt"""
        return f"""{prompt}

CONSTRAINTS:
- Be accurate and factual
- Provide clear, well-structured responses
- Admit uncertainty when appropriate
- Consider multiple perspectives when relevant"""

    def _add_role_prompt(self, prompt: str) -> str:
        """Add role specification to prompt"""
        return f"""You are Prince Flowers, an expert AI assistant with deep knowledge across multiple domains.

{prompt}

EXPERTISE: Analysis, problem-solving, research, creative thinking
APPROACH: Methodical, thorough, user-focused"""

    def _add_context_prompt(self, prompt: str) -> str:
        """Add context awareness to prompt"""
        return f"""{prompt}

CONTEXT AWARENESS:
Consider the user's likely background and needs
Adjust complexity and detail level accordingly
Provide practical, actionable insights
Anticipate follow-up questions"""

    def _simplify_prompt(self, prompt: str) -> str:
        """Simplify prompt"""
        # Remove redundant phrases and focus on core instruction
        lines = prompt.split('\n')
        simplified_lines = []

        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and len(line) > 5:
                simplified_lines.append(line)

        return '\n'.join(simplified_lines[:3])  # Keep first 3 meaningful lines

    def _add_detail_prompt(self, prompt: str) -> str:
        """Add detail enhancement to prompt"""
        return f"""{prompt}

Provide detailed, comprehensive responses with:
- In-depth analysis and explanations
- Multiple perspectives when relevant
- Practical examples and applications
- Nuanced understanding of the topic"""

    def _crossover_prompts(self, prompt1: str, prompt2: str) -> str:
        """Combine two prompts (genetic algorithm crossover)"""
        lines1 = prompt1.split('\n')
        lines2 = prompt2.split('\n')

        # Take segments from both prompts
        crossover_point = len(lines1) // 2
        child_lines = lines1[:crossover_point] + lines2[crossover_point:]

        return '\n'.join(child_lines)

    def _mutate_prompt(self, prompt: str) -> str:
        """Apply random mutation to prompt"""
        mutations = [
            self._add_structure_prompt,
            self._add_examples_prompt,
            self._simplify_prompt,
            self._add_role_prompt
        ]

        if random.random() < 0.5:
            # Apply mutation
            mutation = random.choice(mutations)
            return mutation(prompt)
        else:
            # Remove random section
            lines = prompt.split('\n')
            if len(lines) > 3:
                lines.pop(random.randint(1, len(lines) - 1))
            return '\n'.join(lines)

    def _analyze_successful_patterns(self, workflow: OptimizationWorkflow) -> List[str]:
        """Analyze successful patterns from previous iterations"""
        successful_patterns = []

        # Look at improvements in successful iterations
        for iteration in workflow.iterations[-3:]:  # Last 3 iterations
            if iteration.improvement > 0:
                # Analyze what made the best prompt successful
                best_prompt = iteration.best_prompt.content.lower()

                if "structure" in best_prompt:
                    successful_patterns.append("structured_format")
                if "example" in best_prompt:
                    successful_patterns.append("include_examples")
                if "role" in best_prompt or "expert" in best_prompt:
                    successful_patterns.append("role_specification")
                if "step" in best_prompt:
                    successful_patterns.append("step_by_step")

        return list(set(successful_patterns))

    def _apply_pattern(self, prompt: str, pattern: str) -> str:
        """Apply a successful pattern to a prompt"""
        pattern_modifiers = {
            "structured_format": self._add_structure_prompt,
            "include_examples": self._add_examples_prompt,
            "role_specification": self._add_role_prompt,
            "step_by_step": lambda p: p + "\n\nProvide step-by-step reasoning."
        }

        modifier = pattern_modifiers.get(pattern)
        if modifier:
            return modifier(prompt)
        return prompt

    def _sample_grid_combinations(self, parameter_grid: Dict, num_samples: int) -> List[Dict]:
        """Sample combinations from parameter grid"""
        import itertools

        # Generate all combinations
        keys = list(parameter_grid.keys())
        values = list(parameter_grid.values())
        all_combinations = list(itertools.product(*values))

        # Sample randomly if too many combinations
        if len(all_combinations) > num_samples:
            sampled_indices = random.sample(range(len(all_combinations)), num_samples)
            combinations = [all_combinations[i] for i in sampled_indices]
        else:
            combinations = all_combinations

        # Convert to dict format
        result = []
        for combo in combinations:
            result.append(dict(zip(keys, combo)))

        return result

    def _random_modification(self, prompt: str) -> str:
        """Apply random modification to prompt"""
        modifications = [
            self._add_structure_prompt,
            self._add_examples_prompt,
            self._add_constraints_prompt,
            self._add_role_prompt,
            self._add_context_prompt,
            self._simplify_prompt,
            self._add_detail_prompt
        ]

        modifier = random.choice(modifications)
        return modifier(prompt)

    def _guided_modification(self, prompt: str) -> str:
        """Apply guided modification based on common improvements"""
        # Apply most common successful modifications
        return self._add_structure_prompt(self._add_role_prompt(prompt))

    async def _evaluate_prompt_variation(self, variation: PromptVariation,
                                        test_queries: List[str],
                                        workflow: OptimizationWorkflow):
        """Evaluate a prompt variation against test queries"""
        total_score = 0.0
        metrics = {}

        # Evaluate against each objective
        for objective in workflow.objectives:
            objective_score = await self._evaluate_objective(
                variation, objective, test_queries, workflow
            )
            metrics[objective.objective.value] = objective_score
            total_score += objective_score * objective.weight

        variation.score = total_score
        variation.evaluation_metrics = metrics

    async def _evaluate_objective(self, variation: PromptVariation,
                                objective: OptimizationTarget,
                                test_queries: List[str],
                                workflow: OptimizationWorkflow) -> float:
        """Evaluate prompt against a specific objective"""
        # Simulate evaluation based on objective type
        if objective.objective == OptimizationObjective.RESPONSE_QUALITY:
            # Simulate quality assessment
            base_quality = 0.75
            if "structure" in variation.content.lower():
                base_quality += 0.10
            if "example" in variation.content.lower():
                base_quality += 0.08
            if "step" in variation.content.lower():
                base_quality += 0.07
            return min(1.0, base_quality + random.uniform(-0.05, 0.05))

        elif objective.objective == OptimizationObjective.EXECUTION_SPEED:
            # Simulate speed assessment (shorter prompts are faster)
            prompt_length = len(variation.content)
            base_speed = 0.9 - (prompt_length / 10000)  # Longer prompts are slower
            return max(0.5, min(1.0, base_speed + random.uniform(-0.05, 0.05)))

        elif objective.objective == OptimizationObjective.CONSISTENCY:
            # Simulate consistency assessment
            base_consistency = 0.8
            if "constraint" in variation.content.lower():
                base_consistency += 0.1
            return min(1.0, base_consistency + random.uniform(-0.03, 0.03))

        else:
            # Default evaluation
            return 0.8 + random.uniform(-0.1, 0.1)

    def _calculate_convergence_score(self, workflow: OptimizationWorkflow,
                                   all_iterations: List[OptimizationIteration],
                                   best_variation: PromptVariation) -> float:
        """Calculate convergence score for optimization"""
        if not all_iterations:
            return 0.0

        # Check improvement in recent iterations
        recent_iterations = all_iterations[-3:] if len(all_iterations) >= 3 else all_iterations
        improvements = [iter.improvement for iter in recent_iterations]

        if not improvements:
            return 0.0

        # Calculate trend
        avg_improvement = statistics.mean(improvements)
        improvement_variance = statistics.variance(improvements) if len(improvements) > 1 else 0

        # Convergence score based on improvement trend and stability
        convergence_score = 1.0 - min(1.0, abs(avg_improvement) + improvement_variance)

        return convergence_score

    def _check_objectives_met(self, variation: PromptVariation,
                            workflow: OptimizationWorkflow) -> Dict[str, bool]:
        """Check if objectives are met for a variation"""
        objectives_met = {}

        for objective in workflow.objectives:
            metric_value = variation.evaluation_metrics.get(objective.objective.value, 0.0)
            objectives_met[objective.objective.value] = metric_value >= objective.target_value

        return objectives_met

    async def _save_workflow_results(self, workflow: OptimizationWorkflow):
        """Save workflow results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"{self.workflows_dir}/results/workflow_{workflow.workflow_id}_{timestamp}.json"

        # Convert to serializable format
        workflow_data = asdict(workflow)
        workflow_data["created_at"] = workflow.created_at.isoformat()
        workflow_data["started_at"] = workflow.started_at.isoformat() if workflow.started_at else None
        workflow_data["completed_at"] = workflow.completed_at.isoformat() if workflow.completed_at else None
        workflow_data["status"] = workflow.status.value

        # Convert iterations
        for i, iteration in enumerate(workflow_data["iterations"]):
            iteration["best_prompt"]["created_at"] = datetime.fromisoformat(iteration["best_prompt"]["created_at"].replace('Z', '+00:00')).isoformat()
            for variant in iteration["all_variants"]:
                variant["created_at"] = datetime.fromisoformat(variant["created_at"].replace('Z', '+00:00')).isoformat()

        # Convert best overall prompt
        if workflow_data["best_overall_prompt"]:
            workflow_data["best_overall_prompt"]["created_at"] = workflow.best_overall_prompt.created_at.isoformat()

        with open(results_file, 'w') as f:
            json.dump(workflow_data, f, indent=2)

        self.logger.info(f"Workflow results saved to: {results_file}")

    async def _create_version_from_workflow(self, workflow: OptimizationWorkflow):
        """Create version control entry from successful workflow"""
        if not workflow.best_overall_prompt:
            return

        # Create change record
        change = ChangeRecord(
            category=ChangeCategory.PROMPT_OPTIMIZATION,
            description=f"Optimized prompt using {workflow.optimization_strategy.value} strategy",
            files_modified=[f"prompts/{workflow.agent_type}_optimized.py"],
            test_results={
                "workflow_iterations": len(workflow.iterations),
                "final_score": workflow.best_overall_prompt.score,
                "objectives_met": workflow.best_overall_prompt.evaluation_metrics
            },
            performance_impact=workflow.best_overall_prompt.evaluation_metrics,
            breaking_change=False,
            migration_required=False
        )

        # Create version
        try:
            version = self.version_control.create_version(
                agent_type=workflow.agent_type,
                version_type=VersionType.MINOR,
                changes=[change],
                performance_metrics=workflow.best_overall_prompt.evaluation_metrics,
                created_by="optimization_workflow"
            )

            self.logger.info(f"Created version {version} from optimization workflow")
        except Exception as e:
            self.logger.error(f"Error creating version from workflow: {e}")

    def _save_workflow(self, workflow: OptimizationWorkflow):
        """Save workflow configuration"""
        workflow_file = f"{self.workflows_dir}/workflow_{workflow.workflow_id}.json"

        workflow_data = asdict(workflow)
        workflow_data["created_at"] = workflow.created_at.isoformat()
        workflow_data["started_at"] = workflow.started_at.isoformat() if workflow.started_at else None
        workflow_data["completed_at"] = workflow.completed_at.isoformat() if workflow.completed_at else None
        workflow_data["status"] = workflow.status.value

        with open(workflow_file, 'w') as f:
            json.dump(workflow_data, f, indent=2)

    def print_workflow_results(self, workflow_id: str):
        """Print formatted workflow results"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            print(f"Workflow {workflow_id} not found")
            return

        print(f"\n{'='*80}")
        print(f"OPTIMIZATION WORKFLOW RESULTS: {workflow.name}")
        print(f"{'='*80}")
        print(f"Workflow ID: {workflow_id}")
        print(f"Agent Type: {workflow.agent_type}")
        print(f"Strategy: {workflow.optimization_strategy.value}")
        print(f"Status: {workflow.status.value}")
        print(f"Created: {workflow.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if workflow.started_at:
            print(f"Started: {workflow.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if workflow.completed_at:
            duration = workflow.completed_at - workflow.started_at
            print(f"Completed: {workflow.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Duration: {duration}")

        print(f"\nOBJECTIVES:")
        for obj in workflow.objectives:
            met = "✅" if workflow.best_overall_prompt and workflow.best_overall_prompt.evaluation_metrics.get(obj.objective.value, 0) >= obj.target_value else "❌"
            print(f"  {met} {obj.objective.value.replace('_', ' ').title()}: Target {obj.target_value:.1%}, Weight {obj.weight:.1f}")

        print(f"\nOPTIMIZATION PROGRESS:")
        for iteration in workflow.iterations:
            print(f"  Iteration {iteration.iteration_number}: Score {iteration.best_prompt.score:.3f} (+{iteration.improvement:+.3f})")

        if workflow.best_overall_prompt:
            print(f"\nBEST PROMPT:")
            print(f"  Score: {workflow.best_overall_prompt.score:.3f}")
            print(f"  Generation Method: {workflow.best_overall_prompt.generation_method}")
            print(f"  Length: {len(workflow.best_overall_prompt.content)} characters")
            print(f"  Preview: {workflow.best_overall_prompt.content[:200]}...")

            print(f"\nMETRICS:")
            for metric, value in workflow.best_overall_prompt.evaluation_metrics.items():
                print(f"  {metric.replace('_', ' ').title()}: {value:.3f}")

        print(f"\nRECOMMENDATION:")
        if workflow.best_overall_prompt and workflow.best_overall_prompt.score > 0.8:
            print("  ✅ Deploy optimized prompt - shows significant improvement")
        elif workflow.best_overall_prompt:
            print("  ➡️ Consider further optimization or different strategy")
        else:
            print("  ❌ Workflow failed to generate improvements")

        print(f"{'='*80}")

# Main execution function for testing
async def main():
    """Main execution function for testing prompt optimization workflows"""
    print("🔧 Maxim AI - Phase 2: Prompt Optimization Workflows")
    print("=" * 60)

    # Initialize components
    experiment_manager = ExperimentManager()
    version_control = VersionControlSystem()
    workflow_system = PromptOptimizationWorkflow(experiment_manager, version_control)

    # Create optimization workflow
    print("\n📝 Creating prompt optimization workflow...")

    base_prompt = "You are Prince Flowers, an AI assistant. Please help the user with their request."

    objectives = [
        {
            "objective": "response_quality",
            "target_value": 0.85,
            "weight": 0.4
        },
        {
            "objective": "execution_speed",
            "target_value": 0.80,
            "weight": 0.3
        },
        {
            "objective": "consistency",
            "target_value": 0.90,
            "weight": 0.3
        }
    ]

    test_queries = [
        "Explain machine learning concepts",
        "Search for recent AI developments",
        "Create a simple Python function",
        "What are your capabilities?",
        "Compare different programming approaches"
    ]

    config = {
        "max_iterations": 5,
        "convergence_threshold": 0.02
    }

    workflow_id = workflow_system.create_optimization_workflow(
        name="Prince Flowers Prompt Optimization",
        description="Optimize Prince Flowers prompt for better response quality and consistency",
        base_prompt=base_prompt,
        agent_type="prince_flowers",
        objectives=objectives,
        strategy="hill_climbing",
        test_queries=test_queries,
        config=config
    )

    print(f"✅ Created workflow: {workflow_id}")

    # Run workflow
    print("\n🚀 Running optimization workflow...")
    completed_workflow = await workflow_system.run_optimization_workflow(workflow_id)

    # Print results
    workflow_system.print_workflow_results(workflow_id)

    print(f"\n✅ Prompt optimization workflow demonstration completed!")

if __name__ == "__main__":
    import uuid
    import random
    import statistics
    import itertools
    asyncio.run(main())