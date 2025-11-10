#!/usr/bin/env python3
"""
Advanced Agent Growth Testing Framework

Comprehensive testing suite to evaluate if the enhanced Prince Flowers agent
is truly learning, remembering, and building knowledge over time.

Based on difficult tests for agentic agents:
1. Multi-Session Long-Term Memory Evaluation (LoCoMo, LongMemEval, PrefEval)
2. Real-World Professional Task Benchmarks
3. Evolutionary and Test-Time Learning (J-TTL, EvoTest)
4. Long-Term Coherence Benchmarks
5. Multi-Turn Multi-Tool Interactions
6. Human-in-the-Loop & Hybrid Evaluation
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
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

@dataclass
class GrowthTestResult:
    """Results from growth testing framework"""
    test_name: str
    test_date: str
    success: bool
    score: float
    metrics: Dict[str, Any]
    detailed_results: List[Dict[str, Any]]
    growth_indicators: Dict[str, float]
    recommendations: List[str]
    execution_time: float

class AdvancedAgentGrowthTester:
    """Advanced testing framework for agent growth evaluation"""

    def __init__(self, agent):
        self.agent = agent
        self.test_session_id = f"growth_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger = logging.getLogger(f"{__name__}.{self.test_session_id}")

    async def run_comprehensive_growth_evaluation(self) -> Dict[str, GrowthTestResult]:
        """Run all advanced growth tests"""
        self.logger.info("Starting Comprehensive Agent Growth Evaluation")
        results = {}

        # Test 1: Multi-Session Long-Term Memory Evaluation
        results['locomo_test'] = await self._run_locomo_test()

        # Test 2: Real-World Professional Task Benchmarks
        results['professional_tasks'] = await self._run_professional_task_benchmarks()

        # Test 3: Evolutionary and Test-Time Learning
        results['evolutionary_learning'] = await self._run_evolutionary_learning_test()

        # Test 4: Long-Term Coherence Benchmarks
        results['coherence_benchmarks'] = await self._run_coherence_benchmarks()

        # Test 5: Multi-Turn Multi-Tool Interactions
        results['multi_tool_interactions'] = await self._run_multi_tool_interactions()

        # Test 6: Adaptive Learning Assessment
        results['adaptive_learning'] = await self._run_adaptive_learning_test()

        return results

    async def _run_locomo_test(self) -> GrowthTestResult:
        """
        LoCoMo Test: Multi-session persona-driven conversations
        Evaluates if agent recalls user traits and events across sessions
        """
        self.logger.info("Running LoCoMo Multi-Session Memory Test")
        start_time = time.time()

        # Simulate multiple user personas and their preferences
        user_personas = {
            "alice_developer": {
                "preferences": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "work_style": "agile",
                "expertise": "backend development",
                "goals": ["build scalable APIs", "improve performance"]
            },
            "bob_analyst": {
                "preferences": ["SQL", "Tableau", "Python pandas", "Jupyter"],
                "work_style": "data-driven",
                "expertise": "data analysis",
                "goals": ["optimize queries", "create dashboards"]
            },
            "carol_pm": {
                "preferences": ["Jira", "Confluence", "Slack", "Agile"],
                "work_style": "collaborative",
                "expertise": "project management",
                "goals": ["team coordination", "stakeholder communication"]
            }
        }

        detailed_results = []
        growth_metrics = {
            "cross_session_recall": 0.0,
            "preference_retention": 0.0,
            "context_adaptation": 0.0,
            "knowledge_accumulation": 0.0
        }

        for persona_name, persona_data in user_personas.items():
            session_results = []

            # Session 1: Establish persona and preferences
            session1_query = f"""
            I'm {persona_name.replace('_', ' ').title()}, a {persona_data['expertise']}.
            I work in a {persona_data['work_style']} environment and prefer using {', '.join(persona_data['preferences'])}.
            My main goals are {', '.join(persona_data['goals'])}.

            Can you help me with some relevant advice for my work?
            """

            result1 = await self.agent.process_query_with_zep_memory(session1_query)
            session_results.append(result1)

            # Wait a bit to simulate time gap
            await asyncio.sleep(1)

            # Session 2: Test recall of previous context
            session2_query = f"Based on our previous conversation, can you suggest specific tools for my expertise in {persona_data['expertise']}?"

            result2 = await self.agent.process_query_with_zep_memory(session2_query)
            session_results.append(result2)

            # Session 3: Test preference application
            session3_query = f"Create a workflow that aligns with my {persona_data['work_style']} work style and uses my preferred tools."

            result3 = await self.agent.process_query_with_zep_memory(session3_query)
            session_results.append(result3)

            # Evaluate persona consistency across sessions
            persona_score = self._evaluate_persona_consistency(session_results, persona_data)
            detailed_results.append({
                "persona": persona_name,
                "sessions": 3,
                "consistency_score": persona_score,
                "results": session_results
            })

            # Update growth metrics
            growth_metrics["cross_session_recall"] += persona_score.get("recall_score", 0)
            growth_metrics["preference_retention"] += persona_score.get("preference_score", 0)
            growth_metrics["context_adaptation"] += persona_score.get("adaptation_score", 0)
            growth_metrics["knowledge_accumulation"] += persona_score.get("accumulation_score", 0)

        # Calculate overall scores
        total_personas = len(user_personas)
        for metric in growth_metrics:
            growth_metrics[metric] = growth_metrics[metric] / total_personas

        overall_score = statistics.mean(growth_metrics.values())
        execution_time = time.time() - start_time

        return GrowthTestResult(
            test_name="LoCoMo Multi-Session Memory Test",
            test_date=datetime.now().isoformat(),
            success=overall_score > 0.7,
            score=overall_score,
            metrics=growth_metrics,
            detailed_results=detailed_results,
            growth_indicators={
                "memory_persistence": growth_metrics["cross_session_recall"],
                "preference_learning": growth_metrics["preference_retention"],
                "adaptability": growth_metrics["context_adaptation"]
            },
            recommendations=self._generate_locomo_recommendations(growth_metrics),
            execution_time=execution_time
        )

    async def _run_professional_task_benchmarks(self) -> GrowthTestResult:
        """
        Real-World Professional Task Benchmarks
        Complex multi-step office/workplace tasks with measurable subtasks
        """
        self.logger.info("Running Professional Task Benchmarks")
        start_time = time.time()

        professional_tasks = [
            {
                "name": "API Development Project",
                "complexity": "high",
                "subtasks": [
                    "Design REST API endpoints",
                    "Implement authentication middleware",
                    "Set up database models",
                    "Write comprehensive tests",
                    "Create API documentation",
                    "Deploy to production environment"
                ],
                "required_skills": ["backend development", "database design", "security", "testing", "deployment"]
            },
            {
                "name": "Data Analysis Pipeline",
                "complexity": "medium",
                "subtasks": [
                    "Extract data from multiple sources",
                    "Clean and preprocess data",
                    "Perform exploratory analysis",
                    "Create visualizations",
                    "Generate insights report",
                    "Set up automated scheduling"
                ],
                "required_skills": ["data analysis", "visualization", "automation", "reporting"]
            },
            {
                "name": "System Architecture Review",
                "complexity": "high",
                "subtasks": [
                    "Analyze current architecture",
                    "Identify bottlenecks and issues",
                    "Propose improvements",
                    "Create migration plan",
                    "Estimate resource requirements",
                    "Present recommendations"
                ],
                "required_skills": ["system design", "performance analysis", "planning", "communication"]
            }
        ]

        detailed_results = []
        task_performance = {
            "completion_rate": [],
            "quality_score": [],
            "efficiency_score": [],
            "problem_solving_score": []
        }

        for task in professional_tasks:
            self.logger.info(f"Executing professional task: {task['name']}")

            # Break down task into phases
            task_results = []
            total_subtasks = len(task['subtasks'])
            completed_subtasks = 0

            for i, subtask in enumerate(task['subtasks']):
                subtask_query = f"""
                Working on the task: {task['name']}
                Current subtask ({i+1}/{total_subtasks}): {subtask}

                Please provide detailed guidance for this subtask, considering:
                1. Best practices and standards
                2. Potential challenges and solutions
                3. Required resources and tools
                4. Success criteria
                """

                subtask_result = await self.agent.process_query_with_zep_memory(subtask_query)

                # Evaluate subtask completion
                subtask_score = self._evaluate_subtask_quality(subtask_result, subtask)
                task_results.append({
                    "subtask": subtask,
                    "score": subtask_score,
                    "result": subtask_result
                })

                if subtask_score > 0.6:
                    completed_subtasks += 1

            # Calculate task-level metrics
            completion_rate = completed_subtasks / total_subtasks
            quality_score = statistics.mean([r["score"] for r in task_results])
            efficiency_score = self._calculate_efficiency_score(task_results)
            problem_solving_score = self._evaluate_problem_solving(task_results)

            task_performance["completion_rate"].append(completion_rate)
            task_performance["quality_score"].append(quality_score)
            task_performance["efficiency_score"].append(efficiency_score)
            task_performance["problem_solving_score"].append(problem_solving_score)

            detailed_results.append({
                "task": task["name"],
                "complexity": task["complexity"],
                "completion_rate": completion_rate,
                "quality_score": quality_score,
                "efficiency_score": efficiency_score,
                "problem_solving_score": problem_solving_score,
                "subtask_results": task_results
            })

        # Calculate overall professional task performance
        overall_metrics = {
            "avg_completion_rate": statistics.mean(task_performance["completion_rate"]),
            "avg_quality_score": statistics.mean(task_performance["quality_score"]),
            "avg_efficiency_score": statistics.mean(task_performance["efficiency_score"]),
            "avg_problem_solving": statistics.mean(task_performance["problem_solving_score"])
        }

        overall_score = statistics.mean(overall_metrics.values())
        execution_time = time.time() - start_time

        return GrowthTestResult(
            test_name="Professional Task Benchmarks",
            test_date=datetime.now().isoformat(),
            success=overall_score > 0.75,
            score=overall_score,
            metrics=overall_metrics,
            detailed_results=detailed_results,
            growth_indicators={
                "task_execution": overall_metrics["avg_completion_rate"],
                "quality_consistency": overall_metrics["avg_quality_score"],
                "problem_solving": overall_metrics["avg_problem_solving"]
            },
            recommendations=self._generate_professional_task_recommendations(overall_metrics),
            execution_time=execution_time
        )

    async def _run_evolutionary_learning_test(self) -> GrowthTestResult:
        """
        Evolutionary and Test-Time Learning (J-TTL, EvoTest)
        Places agent in open-ended environments and measures adaptation
        """
        self.logger.info("Running Evolutionary Learning Test")
        start_time = time.time()

        # Evolutionary scenarios with increasing complexity
        evolutionary_scenarios = [
            {
                "name": "Progressive Problem Solving",
                "iterations": 5,
                "complexity_growth": "linear",
                "base_task": "Help me optimize a Python function"
            },
            {
                "name": "Adaptive Code Refactoring",
                "iterations": 4,
                "complexity_growth": "exponential",
                "base_task": "Review and improve this code structure"
            },
            {
                "name": "Knowledge Integration Challenge",
                "iterations": 6,
                "complexity_growth": "adaptive",
                "base_task": "Synthesize information from multiple domains"
            }
        ]

        detailed_results = []
        adaptation_metrics = {
            "learning_rate": [],
            "adaptation_speed": [],
            "knowledge_retention": [],
            "error_reduction": []
        }

        for scenario in evolutionary_scenarios:
            self.logger.info(f"Running evolutionary scenario: {scenario['name']}")

            scenario_results = []
            previous_performance = 0.0
            accumulated_knowledge = []

            for iteration in range(scenario["iterations"]):
                # Build progressive complexity
                complexity_modifier = self._calculate_complexity_modifier(
                    iteration, scenario["complexity_growth"]
                )

                # Add context from previous iterations
                context_modifier = ""
                if iteration > 0:
                    context_modifier = f"""
                    Building on our previous discussion, here's what we've learned:
                    {chr(10).join(accumulated_knowledge[-3:])}  # Last 3 insights

                    Now let's tackle the next level of complexity.
                    """

                iteration_query = f"""
                {scenario['base_task']} - Iteration {iteration + 1}
                Difficulty Level: {complexity_modifier}
                {context_modifier}

                Please provide a solution that demonstrates improvement from previous iterations.
                """

                iteration_result = await self.agent.process_query_with_zep_memory(iteration_query)

                # Evaluate evolutionary progress
                iteration_score = self._evaluate_evolutionary_progress(
                    iteration_result, iteration, previous_performance
                )

                # Extract new knowledge/insights
                new_insights = self._extract_knowledge_insights(iteration_result)
                accumulated_knowledge.extend(new_insights)

                scenario_results.append({
                    "iteration": iteration + 1,
                    "score": iteration_score,
                    "improvement": iteration_score - previous_performance,
                    "new_insights": len(new_insights),
                    "result": iteration_result
                })

                # Calculate adaptation metrics
                if iteration > 0:
                    learning_rate = (iteration_score - previous_performance) / previous_performance if previous_performance > 0 else 0
                    adaptation_metrics["learning_rate"].append(learning_rate)
                    adaptation_metrics["adaptation_speed"].append(learning_rate / (iteration + 1))

                adaptation_metrics["knowledge_retention"].append(len(accumulated_knowledge))

                previous_performance = iteration_score

            # Calculate error reduction (inverse of failures)
            failures = [1 - r["score"] for r in scenario_results if r["score"] < 0.7]
            error_reduction = (failures[0] - failures[-1]) / failures[0] if failures else 0.0
            adaptation_metrics["error_reduction"].append(error_reduction)

            detailed_results.append({
                "scenario": scenario["name"],
                "iterations": scenario["iterations"],
                "final_score": scenario_results[-1]["score"],
                "improvement_rate": (scenario_results[-1]["score"] - scenario_results[0]["score"]) / scenario_results[0]["score"] if scenario_results[0]["score"] > 0 else 0,
                "total_insights": sum(r["new_insights"] for r in scenario_results),
                "iteration_results": scenario_results
            })

        # Calculate overall evolutionary metrics
        overall_metrics = {
            "avg_learning_rate": statistics.mean(adaptation_metrics["learning_rate"]) if adaptation_metrics["learning_rate"] else 0,
            "avg_adaptation_speed": statistics.mean(adaptation_metrics["adaptation_speed"]) if adaptation_metrics["adaptation_speed"] else 0,
            "knowledge_accumulation": adaptation_metrics["knowledge_retention"][-1] if adaptation_metrics["knowledge_retention"] else 0,
            "error_reduction_rate": statistics.mean(adaptation_metrics["error_reduction"]) if adaptation_metrics["error_reduction"] else 0
        }

        overall_score = statistics.mean([
            overall_metrics["avg_learning_rate"] * 10,  # Scale up for significance
            min(overall_metrics["avg_adaptation_speed"] * 100, 1.0),
            min(overall_metrics["knowledge_accumulation"] / 50, 1.0),  # Normalize by expected insights
            overall_metrics["error_reduction_rate"]
        ])

        execution_time = time.time() - start_time

        return GrowthTestResult(
            test_name="Evolutionary Learning Test",
            test_date=datetime.now().isoformat(),
            success=overall_score > 0.6,
            score=overall_score,
            metrics=overall_metrics,
            detailed_results=detailed_results,
            growth_indicators={
                "adaptive_capability": overall_metrics["avg_learning_rate"],
                "learning_velocity": overall_metrics["avg_adaptation_speed"],
                "knowledge_integration": min(overall_metrics["knowledge_accumulation"] / 50, 1.0)
            },
            recommendations=self._generate_evolutionary_recommendations(overall_metrics),
            execution_time=execution_time
        )

    async def _run_coherence_benchmarks(self) -> GrowthTestResult:
        """
        Long-Term Coherence Benchmarks
        Measures logical and narrative coherence over extended interactions
        """
        self.logger.info("Running Long-Term Coherence Benchmarks")
        start_time = time.time()

        coherence_scenarios = [
            {
                "name": "Multi-Stage Project Planning",
                "duration": "extended",
                "context_type": "project_management",
                "consistency_requirements": ["timeline", "resources", "scope", "dependencies"]
            },
            {
                "name": "Technical Documentation Creation",
                "duration": "extended",
                "context_type": "technical_writing",
                "consistency_requirements": ["terminology", "format", "accuracy", "completeness"]
            },
            {
                "name": "Complex Problem Analysis",
                "duration": "extended",
                "context_type": "analytical_reasoning",
                "consistency_requirements": ["logic", "evidence", "conclusions", "methodology"]
            }
        ]

        detailed_results = []
        coherence_metrics = {
            "consistency_score": [],
            "logical_flow_score": [],
            "context_maintenance": [],
            "coherence_breakdowns": []
        }

        for scenario in coherence_scenarios:
            self.logger.info(f"Running coherence scenario: {scenario['name']}")

            # Create extended conversation sequence
            conversation_turns = []
            context_state = {
                "established_facts": [],
                "terminology_used": set(),
                "decisions_made": [],
                "contradictions_detected": []
            }

            # Generate conversation sequence
            num_turns = 8
            for turn in range(num_turns):
                if turn == 0:
                    # Initial context establishment
                    query = f"""
                    Let's work on {scenario['name']}. This requires {scenario['context_type']} expertise.
                    Please establish the foundation and key principles we should follow.
                    """
                elif turn < num_turns // 2:
                    # Development phase
                    query = f"""
                    Building on our previous discussion, let's develop the next phase.
                    Ensure consistency with what we've established and maintain focus on {', '.join(scenario['consistency_requirements'])}.
                    """
                else:
                    # Consolidation and review phase
                    query = f"""
                    Let's review our progress and ensure everything is coherent and consistent.
                    Check for any contradictions or gaps in our approach to {scenario['name']}.
                    """

                result = await self.agent.process_query_with_zep_memory(query)

                # Analyze coherence
                coherence_analysis = self._analyze_response_coherence(
                    result, context_state, scenario
                )

                # Update context state
                context_state["established_facts"].extend(coherence_analysis["new_facts"])
                context_state["terminology_used"].update(coherence_analysis["terminology"])
                context_state["decisions_made"].extend(coherence_analysis["decisions"])
                context_state["contradictions_detected"].extend(coherence_analysis["contradictions"])

                conversation_turns.append({
                    "turn": turn + 1,
                    "query": query,
                    "result": result,
                    "coherence_analysis": coherence_analysis
                })

                coherence_metrics["consistency_score"].append(coherence_analysis["consistency_score"])
                coherence_metrics["logical_flow_score"].append(coherence_analysis["logical_flow_score"])
                coherence_metrics["context_maintenance"].append(coherence_analysis["context_maintenance"])
                coherence_metrics["coherence_breakdowns"].append(len(coherence_analysis["contradictions"]))

            # Calculate scenario-level coherence
            scenario_coherence = {
                "avg_consistency": statistics.mean(coherence_metrics["consistency_score"][-num_turns:]),
                "avg_logical_flow": statistics.mean(coherence_metrics["logical_flow_score"][-num_turns:]),
                "context_stability": statistics.mean(coherence_metrics["context_maintenance"][-num_turns:]),
                "total_breakdowns": sum(coherence_metrics["coherence_breakdowns"][-num_turns:]),
                "coherence_ratio": 1 - (sum(coherence_metrics["coherence_breakdowns"][-num_turns:]) / num_turns)
            }

            detailed_results.append({
                "scenario": scenario["name"],
                "turns": num_turns,
                "coherence_metrics": scenario_coherence,
                "conversation_turns": conversation_turns,
                "context_final_state": {
                    "total_facts": len(context_state["established_facts"]),
                    "unique_terminology": len(context_state["terminology_used"]),
                    "decisions_made": len(context_state["decisions_made"]),
                    "contradictions": len(context_state["contradictions_detected"])
                }
            })

        # Calculate overall coherence metrics
        overall_metrics = {
            "overall_consistency": statistics.mean([r["coherence_metrics"]["avg_consistency"] for r in detailed_results]),
            "overall_logical_flow": statistics.mean([r["coherence_metrics"]["avg_logical_flow"] for r in detailed_results]),
            "overall_context_stability": statistics.mean([r["coherence_metrics"]["context_stability"] for r in detailed_results]),
            "overall_coherence_ratio": statistics.mean([r["coherence_metrics"]["coherence_ratio"] for r in detailed_results])
        }

        overall_score = statistics.mean(overall_metrics.values())
        execution_time = time.time() - start_time

        return GrowthTestResult(
            test_name="Long-Term Coherence Benchmarks",
            test_date=datetime.now().isoformat(),
            success=overall_score > 0.8,
            score=overall_score,
            metrics=overall_metrics,
            detailed_results=detailed_results,
            growth_indicators={
                "coherence_stability": overall_metrics["overall_coherence_ratio"],
                "logical_consistency": overall_metrics["overall_consistency"],
                "context_management": overall_metrics["overall_context_stability"]
            },
            recommendations=self._generate_coherence_recommendations(overall_metrics),
            execution_time=execution_time
        )

    async def _run_multi_tool_interactions(self) -> GrowthTestResult:
        """
        Multi-Turn Multi-Tool Interactions
        Tests agent across extended workflows with tool usage and interruptions
        """
        self.logger.info("Running Multi-Tool Interaction Tests")
        start_time = time.time()

        multi_tool_scenarios = [
            {
                "name": "Full-Stack Development Workflow",
                "tools_required": ["code_generation", "debugging", "documentation", "testing"],
                "interruptions": ["requirement_change", "bug_discovery", "priority_shift"],
                "workflow_steps": [
                    "analyze_requirements",
                    "design_architecture",
                    "implement_frontend",
                    "implement_backend",
                    "integrate_systems",
                    "test_and_debug",
                    "deploy_solution",
                    "document_results"
                ]
            },
            {
                "name": "Data Science Pipeline",
                "tools_required": ["data_analysis", "visualization", "automation", "reporting"],
                "interruptions": ["data_quality_issues", "model_performance_problems", "deadline_pressure"],
                "workflow_steps": [
                    "collect_data",
                    "clean_preprocess",
                    "explore_analyze",
                    "feature_engineering",
                    "model_development",
                    "validate_results",
                    "create_visualizations",
                    "generate_report"
                ]
            }
        ]

        detailed_results = []
        tool_interaction_metrics = {
            "tool_coordination": [],
            "workflow_continuity": [],
            "interruption_recovery": [],
            "multitask_efficiency": []
        }

        for scenario in multi_tool_scenarios:
            self.logger.info(f"Running multi-tool scenario: {scenario['name']}")

            workflow_results = []
            workflow_state = {
                "current_step": 0,
                "tools_used": [],
                "interruptions_handled": 0,
                "workflow_interruptions": 0,
                "recovery_success": 0
            }

            for step_idx, step in enumerate(scenario["workflow_steps"]):
                # Check for random interruptions
                should_interrupt = step_idx > 0 and step_idx % 2 == 0 and scenario["interruptions"]

                if should_interrupt:
                    # Inject interruption
                    interruption = scenario["interruptions"][workflow_state["workflow_interruptions"] % len(scenario["interruptions"])]
                    interruption_query = f"""
                    URGENT: {interruption.replace('_', ' ').title()} has occurred!
                    This requires immediate attention. Please pause your current task and address this issue.
                    """

                    interruption_result = await self.agent.process_query_with_zep_memory(interruption_query)
                    workflow_state["workflow_interruptions"] += 1

                    # Evaluate interruption handling
                    recovery_score = self._evaluate_interruption_handling(interruption_result, interruption)
                    workflow_results.append({
                        "type": "interruption",
                        "interruption": interruption,
                        "recovery_score": recovery_score,
                        "result": interruption_result
                    })

                    if recovery_score > 0.7:
                        workflow_state["recovery_success"] += 1

                    workflow_state["interruptions_handled"] += 1

                # Continue with regular workflow step
                step_query = f"""
                Continuing with {scenario['name']} - Step {step_idx + 1}: {step.replace('_', ' ').title()}

                Previous tools used: {', '.join(workflow_state['tools_used']) if workflow_state['tools_used'] else 'None'}
                Current context: We're working on {scenario['name']} and just completed step {step_idx}.

                Please execute this step using appropriate tools and maintain continuity with previous work.
                """

                step_result = await self.agent.process_query_with_zep_memory(step_query)

                # Analyze tool usage and coordination
                tool_analysis = self._analyze_tool_usage(step_result, scenario["tools_required"])

                workflow_results.append({
                    "type": "workflow_step",
                    "step": step,
                    "step_index": step_idx + 1,
                    "tool_analysis": tool_analysis,
                    "result": step_result
                })

                # Update workflow state
                workflow_state["tools_used"].extend(tool_analysis["tools_used"])
                workflow_state["current_step"] = step_idx + 1

                # Calculate metrics for this step
                tool_coordination = tool_analysis["coordination_score"]
                workflow_continuity = self._calculate_workflow_continuity(step_result, workflow_state)

                tool_interaction_metrics["tool_coordination"].append(tool_coordination)
                tool_interaction_metrics["workflow_continuity"].append(workflow_continuity)

            # Calculate scenario-level metrics
            if workflow_state["interruptions_handled"] > 0:
                interruption_recovery_rate = workflow_state["recovery_success"] / workflow_state["interruptions_handled"]
                tool_interaction_metrics["interruption_recovery"].append(interruption_recovery_rate)

            multitask_efficiency = self._calculate_multitask_efficiency(workflow_results, scenario)
            tool_interaction_metrics["multitask_efficiency"].append(multitask_efficiency)

            detailed_results.append({
                "scenario": scenario["name"],
                "workflow_steps": len(scenario["workflow_steps"]),
                "tools_required": scenario["tools_required"],
                "interruptions_handled": workflow_state["interruptions_handled"],
                "recovery_rate": interruption_recovery_rate if workflow_state["interruptions_handled"] > 0 else 1.0,
                "multitask_efficiency": multitask_efficiency,
                "unique_tools_used": len(set(workflow_state["tools_used"])),
                "workflow_results": workflow_results
            })

        # Calculate overall multi-tool metrics
        overall_metrics = {
            "avg_tool_coordination": statistics.mean(tool_interaction_metrics["tool_coordination"]),
            "avg_workflow_continuity": statistics.mean(tool_interaction_metrics["workflow_continuity"]),
            "avg_interruption_recovery": statistics.mean(tool_interaction_metrics["interruption_recovery"]) if tool_interaction_metrics["interruption_recovery"] else 1.0,
            "avg_multitask_efficiency": statistics.mean(tool_interaction_metrics["multitask_efficiency"])
        }

        overall_score = statistics.mean(overall_metrics.values())
        execution_time = time.time() - start_time

        return GrowthTestResult(
            test_name="Multi-Tool Interaction Tests",
            test_date=datetime.now().isoformat(),
            success=overall_score > 0.75,
            score=overall_score,
            metrics=overall_metrics,
            detailed_results=detailed_results,
            growth_indicators={
                "tool_mastery": overall_metrics["avg_tool_coordination"],
                "workflow_resilience": overall_metrics["avg_interruption_recovery"],
                "adaptive_coordination": overall_metrics["avg_multitask_efficiency"]
            },
            recommendations=self._generate_multi_tool_recommendations(overall_metrics),
            execution_time=execution_time
        )

    async def _run_adaptive_learning_test(self) -> GrowthTestResult:
        """
        Adaptive Learning Assessment
        Tests agent's ability to learn from feedback and improve performance
        """
        self.logger.info("Running Adaptive Learning Assessment")
        start_time = time.time()

        learning_scenarios = [
            {
                "name": "Iterative Code Improvement",
                "iterations": 4,
                "feedback_type": "code_quality",
                "base_task": "Write a function to process user data"
            },
            {
                "name": "Progressive Problem Solving",
                "iterations": 5,
                "feedback_type": "accuracy",
                "base_task": "Solve a complex analytical problem"
            },
            {
                "name": "Communication Style Adaptation",
                "iterations": 3,
                "feedback_type": "clarity",
                "base_task": "Explain a technical concept"
            }
        ]

        detailed_results = []
        learning_metrics = {
            "improvement_rate": [],
            "feedback_integration": [],
            "learning_velocity": [],
            "performance_convergence": []
        }

        for scenario in learning_scenarios:
            self.logger.info(f"Running learning scenario: {scenario['name']}")

            scenario_results = []
            baseline_performance = 0.0
            performance_history = []

            for iteration in range(scenario["iterations"]):
                # Build iterative query with learning context
                if iteration == 0:
                    iteration_query = f"""
                    Task: {scenario['base_task']}
                    This is iteration {iteration + 1} of {scenario['iterations']}.
                    Please provide your best attempt.
                    """
                else:
                    # Incorporate feedback from previous iteration
                    previous_feedback = scenario_results[-1].get("feedback", "")
                    iteration_query = f"""
                    Task: {scenario['base_task']}
                    This is iteration {iteration + 1} of {scenario['iterations']}.

                    Previous iteration feedback: {previous_feedback}
                    Performance history: {[f'{p:.2f}' for p in performance_history]}

                    Please improve based on the feedback and demonstrate learning.
                    """

                iteration_result = await self.agent.process_query_with_zep_memory(iteration_query)

                # Evaluate performance for this iteration
                performance_score = self._evaluate_performance(
                    iteration_result, scenario["feedback_type"]
                )

                # Generate feedback for next iteration
                feedback = self._generate_feedback(
                    iteration_result, performance_score, scenario["feedback_type"]
                )

                scenario_results.append({
                    "iteration": iteration + 1,
                    "performance_score": performance_score,
                    "feedback": feedback,
                    "improvement": performance_score - baseline_performance if iteration > 0 else 0,
                    "result": iteration_result
                })

                performance_history.append(performance_score)

                if iteration > 0:
                    # Calculate learning metrics
                    improvement_rate = (performance_score - baseline_performance) / baseline_performance if baseline_performance > 0 else 0
                    learning_metrics["improvement_rate"].append(improvement_rate)

                    # Measure feedback integration
                    feedback_integration = self._measure_feedback_integration(
                        iteration_result, scenario_results[-2]["feedback"]
                    )
                    learning_metrics["feedback_integration"].append(feedback_integration)

                    # Calculate learning velocity
                    learning_velocity = improvement_rate / (iteration + 1)
                    learning_metrics["learning_velocity"].append(learning_velocity)

                baseline_performance = performance_score

            # Calculate convergence metrics
            convergence_score = self._calculate_learning_convergence(performance_history)
            learning_metrics["performance_convergence"].append(convergence_score)

            detailed_results.append({
                "scenario": scenario["name"],
                "iterations": scenario["iterations"],
                "initial_performance": scenario_results[0]["performance_score"],
                "final_performance": scenario_results[-1]["performance_score"],
                "total_improvement": scenario_results[-1]["performance_score"] - scenario_results[0]["performance_score"],
                "convergence_score": convergence_score,
                "avg_improvement_rate": statistics.mean(learning_metrics["improvement_rate"][-scenario["iterations"]+1:]) if len(learning_metrics["improvement_rate"]) > 0 else 0,
                "iteration_results": scenario_results
            })

        # Calculate overall learning metrics
        overall_metrics = {
            "avg_improvement_rate": statistics.mean(learning_metrics["improvement_rate"]) if learning_metrics["improvement_rate"] else 0,
            "avg_feedback_integration": statistics.mean(learning_metrics["feedback_integration"]) if learning_metrics["feedback_integration"] else 0,
            "avg_learning_velocity": statistics.mean(learning_metrics["learning_velocity"]) if learning_metrics["learning_velocity"] else 0,
            "avg_convergence_score": statistics.mean(learning_metrics["performance_convergence"])
        }

        # Normalize and calculate overall score
        normalized_metrics = [
            min(overall_metrics["avg_improvement_rate"] * 5, 1.0),  # Scale improvement rate
            overall_metrics["avg_feedback_integration"],
            min(overall_metrics["avg_learning_velocity"] * 10, 1.0),  # Scale learning velocity
            overall_metrics["avg_convergence_score"]
        ]
        overall_score = statistics.mean(normalized_metrics)

        execution_time = time.time() - start_time

        return GrowthTestResult(
            test_name="Adaptive Learning Assessment",
            test_date=datetime.now().isoformat(),
            success=overall_score > 0.65,
            score=overall_score,
            metrics=overall_metrics,
            detailed_results=detailed_results,
            growth_indicators={
                "learning_capacity": overall_metrics["avg_improvement_rate"],
                "feedback_responsiveness": overall_metrics["avg_feedback_integration"],
                "adaptation_speed": overall_metrics["avg_learning_velocity"]
            },
            recommendations=self._generate_learning_recommendations(overall_metrics),
            execution_time=execution_time
        )

    # Helper methods for evaluation and analysis
    def _evaluate_persona_consistency(self, session_results: List[Dict], persona_data: Dict) -> Dict[str, float]:
        """Evaluate how well agent maintains persona consistency across sessions"""
        scores = {
            "recall_score": 0.0,
            "preference_score": 0.0,
            "adaptation_score": 0.0,
            "accumulation_score": 0.0
        }

        # Extract key terms from persona
        persona_keywords = set()
        for pref in persona_data["preferences"]:
            persona_keywords.update(pref.lower().split())
        persona_keywords.add(persona_data["expertise"].lower())
        persona_keywords.add(persona_data["work_style"].lower())

        # Analyze each session result
        for i, result in enumerate(session_results):
            content = result.get("content", "").lower()

            # Check recall of persona elements
            recall_matches = sum(1 for keyword in persona_keywords if keyword in content)
            scores["recall_score"] += recall_matches / len(persona_keywords)

            # Check preference application
            pref_matches = sum(1 for pref in persona_data["preferences"] if pref.lower() in content)
            scores["preference_score"] += pref_matches / len(persona_data["preferences"])

            # Check adaptation to work style
            adaptation_score = 1.0 if persona_data["work_style"].lower() in content else 0.5
            scores["adaptation_score"] += adaptation_score

            # Accumulation score increases with later sessions if context is maintained
            accumulation_score = 0.3 + (i * 0.2) if any(keyword in content for keyword in persona_keywords) else 0.1
            scores["accumulation_score"] += accumulation_score

        # Average across sessions
        num_sessions = len(session_results)
        for key in scores:
            scores[key] = scores[key] / num_sessions

        return scores

    def _evaluate_subtask_quality(self, subtask_result: Dict, subtask: str) -> float:
        """Evaluate the quality of a subtask completion"""
        content = subtask_result.get("content", "")

        quality_factors = {
            "completeness": 0.0,
            "relevance": 0.0,
            "practicality": 0.0,
            "clarity": 0.0
        }

        # Check for completeness indicators
        completeness_keywords = ["step", "process", "implementation", "example", "solution"]
        quality_factors["completeness"] = sum(1 for kw in completeness_keywords if kw in content.lower()) / len(completeness_keywords)

        # Check relevance to subtask
        subtask_keywords = subtask.lower().split()
        relevance_matches = sum(1 for kw in subtask_keywords if kw in content.lower())
        quality_factors["relevance"] = min(relevance_matches / len(subtask_keywords), 1.0)

        # Check practical indicators
        practical_keywords = ["code", "tool", "method", "technique", "best practice"]
        quality_factors["practicality"] = sum(1 for kw in practical_keywords if kw in content.lower()) / len(practical_keywords)

        # Check clarity indicators
        clarity_indicators = ["clear", "simple", "easy", "understand", "follow"]
        quality_factors["clarity"] = sum(1 for ind in clarity_indicators if ind in content.lower()) / len(clarity_indicators)

        return statistics.mean(quality_factors.values())

    def _calculate_efficiency_score(self, task_results: List[Dict]) -> float:
        """Calculate efficiency score based on consistency and progression"""
        if len(task_results) < 2:
            return 0.8  # Default for single subtask

        scores = [r["score"] for r in task_results]

        # Calculate consistency (low variance = high efficiency)
        consistency = 1.0 - (statistics.stdev(scores) if len(scores) > 1 else 0)

        # Calculate progression (improvement over time)
        progression = (scores[-1] - scores[0]) / scores[0] if scores[0] > 0 else 0

        # Combine factors
        efficiency = (consistency * 0.7) + (min(progression, 1.0) * 0.3)

        return max(0.0, min(1.0, efficiency))

    def _evaluate_problem_solving(self, task_results: List[Dict]) -> float:
        """Evaluate problem-solving capabilities"""
        problem_solving_indicators = []

        for result in task_results:
            content = result["result"].get("content", "").lower()

            # Look for problem-solving indicators
            indicators = [
                "solution", "solve", "approach", "method", "strategy",
                "problem", "challenge", "issue", "fix", "resolve"
            ]

            indicator_count = sum(1 for ind in indicators if ind in content)
            problem_solving_indicators.append(min(indicator_count / 3, 1.0))  # Normalize

        return statistics.mean(problem_solving_indicators) if problem_solving_indicators else 0.5

    def _calculate_complexity_modifier(self, iteration: int, growth_type: str) -> str:
        """Calculate complexity modifier for evolutionary learning"""
        base_complexities = ["basic", "intermediate", "advanced", "expert", "master"]

        if growth_type == "linear":
            return base_complexities[min(iteration, len(base_complexities) - 1)]
        elif growth_type == "exponential":
            complexity_level = min(2 ** iteration, len(base_complexities) - 1)
            return base_complexities[complexity_level]
        elif growth_type == "adaptive":
            # Adaptive based on iteration
            if iteration < 2:
                return base_complexities[iteration]
            elif iteration < 4:
                return base_complexities[2]
            else:
                return base_complexities[min(iteration - 1, len(base_complexities) - 1)]

        return "intermediate"

    def _evaluate_evolutionary_progress(self, iteration_result: Dict, iteration: int, previous_performance: float) -> float:
        """Evaluate evolutionary progress across iterations"""
        content = iteration_result.get("content", "")

        # Base quality score
        base_score = iteration_result.get("confidence", 0.5)

        # Look for evolutionary indicators
        evolutionary_indicators = [
            "improvement", "better", "enhanced", "optimized", "refined",
            "advanced", "sophisticated", "evolved", "progressive", "building on"
        ]

        indicator_count = sum(1 for ind in evolutionary_indicators if ind in content.lower())
        evolutionary_bonus = min(indicator_count / 5, 0.3)  # Max 30% bonus

        # Learning from previous iterations
        learning_indicators = ["previous", "learned", "applied", "integrated", "synthesized"]
        learning_count = sum(1 for ind in learning_indicators if ind in content.lower())
        learning_bonus = min(learning_count / 3, 0.2)  # Max 20% bonus

        # Iteration bonus (later iterations should be better)
        iteration_bonus = min(iteration * 0.05, 0.2)  # Max 20% bonus

        total_score = base_score + evolutionary_bonus + learning_bonus + iteration_bonus
        return min(total_score, 1.0)

    def _extract_knowledge_insights(self, iteration_result: Dict) -> List[str]:
        """Extract new knowledge insights from agent response"""
        content = iteration_result.get("content", "")

        # Look for insight patterns
        insight_patterns = [
            "key insight", "important to note", "crucial point",
            "best practice", "recommendation", "consider",
            "valuable lesson", "takeaway", "principle"
        ]

        insights = []
        for pattern in insight_patterns:
            if pattern in content.lower():
                # Extract surrounding context as insight
                start_idx = content.lower().find(pattern)
                if start_idx != -1:
                    # Extract sentence containing the pattern
                    start = max(0, start_idx - 50)
                    end = min(len(content), start_idx + len(pattern) + 100)
                    insight = content[start:end].strip()
                    if insight and insight not in insights:
                        insights.append(insight)

        return insights[:3]  # Return top 3 insights

    def _analyze_response_coherence(self, result: Dict, context_state: Dict, scenario: Dict) -> Dict[str, Any]:
        """Analyze response for coherence and consistency"""
        content = result.get("content", "").lower()

        analysis = {
            "new_facts": [],
            "terminology": [],
            "decisions": [],
            "contradictions": [],
            "consistency_score": 0.0,
            "logical_flow_score": 0.0,
            "context_maintenance": 0.0
        }

        # Extract new facts (simplified)
        fact_patterns = ["fact:", "important:", "note:", "key point:"]
        for pattern in fact_patterns:
            if pattern in content:
                # Simple extraction - would be more sophisticated in production
                analysis["new_facts"].append(f"New fact about {scenario['context_type']}")

        # Extract terminology
        technical_terms = ["api", "database", "system", "process", "method", "framework"]
        for term in technical_terms:
            if term in content:
                analysis["terminology"].append(term)

        # Extract decisions
        decision_patterns = ["decide:", "conclusion:", "recommendation:", "choose:"]
        for pattern in decision_patterns:
            if pattern in content:
                analysis["decisions"].append(f"Decision about {scenario['context_type']}")

        # Check for contradictions (simplified)
        contradiction_indicators = ["however", "but", "although", "contrary to"]
        for indicator in contradiction_indicators:
            if indicator in content:
                analysis["contradictions"].append(f"Potential contradiction with {indicator}")

        # Calculate scores (simplified heuristics)
        analysis["consistency_score"] = 1.0 - (len(analysis["contradictions"]) * 0.2)
        analysis["logical_flow_score"] = min(len(analysis["new_facts"]) / 3, 1.0)
        analysis["context_maintenance"] = len(analysis["terminology"]) / len(technical_terms)

        return analysis

    def _analyze_tool_usage(self, result: Dict, required_tools: List[str]) -> Dict[str, Any]:
        """Analyze how well agent coordinates multiple tools"""
        content = result.get("content", "").lower()

        analysis = {
            "tools_used": [],
            "coordination_score": 0.0,
            "integration_quality": 0.0
        }

        # Check for tool usage indicators
        tool_indicators = {
            "code_generation": ["code", "function", "class", "implement", "programming"],
            "debugging": ["debug", "error", "fix", "issue", "problem", "solution"],
            "documentation": ["document", "explain", "guide", "manual", "readme"],
            "testing": ["test", "verify", "validate", "check", "assert"],
            "data_analysis": ["analyze", "data", "process", "calculate", "statistics"],
            "visualization": ["chart", "graph", "visualize", "plot", "display"]
        }

        for tool, indicators in tool_indicators.items():
            if any(ind in content for ind in indicators):
                analysis["tools_used"].append(tool)

        # Calculate coordination score
        coordination_indicators = ["integrate", "combine", "coordinate", "workflow", "pipeline"]
        coordination_count = sum(1 for ind in coordination_indicators if ind in content)
        analysis["coordination_score"] = min(coordination_count / 3, 1.0)

        # Calculate integration quality
        tools_mentioned = len(analysis["tools_used"])
        required_mentioned = sum(1 for tool in required_tools if tool in analysis["tools_used"])
        analysis["integration_quality"] = required_mentioned / len(required_tools) if required_tools else 0

        return analysis

    def _evaluate_interruption_handling(self, interruption_result: Dict, interruption_type: str) -> float:
        """Evaluate how well agent handles interruptions"""
        content = interruption_result.get("content", "").lower()

        # Look for interruption handling indicators
        handling_indicators = [
            "understood", "address", "handle", "resolve", "urgent",
            "immediate", "priority", "pause", "switch", "context"
        ]

        indicator_count = sum(1 for ind in handling_indicators if ind in content)
        base_score = min(indicator_count / 5, 0.7)

        # Check for appropriate response to interruption type
        response_keywords = {
            "requirement_change": ["adapt", "modify", "adjust", "update"],
            "bug_discovery": ["fix", "debug", "resolve", "correct"],
            "priority_shift": ["reorder", "reprioritize", "focus", "critical"]
        }

        if interruption_type in response_keywords:
            response_matches = sum(1 for kw in response_keywords[interruption_type] if kw in content)
            response_bonus = min(response_matches / len(response_keywords[interruption_type]), 0.3)
        else:
            response_bonus = 0.1

        return min(base_score + response_bonus, 1.0)

    def _calculate_workflow_continuity(self, step_result: Dict, workflow_state: Dict) -> float:
        """Calculate how well agent maintains workflow continuity"""
        content = step_result.get("content", "").lower()

        # Check for continuity indicators
        continuity_indicators = [
            "continuing", "next step", "following", "building on",
            "previous", "earlier", "context", "workflow"
        ]

        indicator_count = sum(1 for ind in continuity_indicators if ind in content)
        continuity_score = min(indicator_count / 4, 0.8)

        # Check for step awareness
        step_awareness = 0.2 if f"step {workflow_state['current_step']}" in content else 0.0

        return min(continuity_score + step_awareness, 1.0)

    def _calculate_multitask_efficiency(self, workflow_results: List[Dict], scenario: Dict) -> float:
        """Calculate multitasking efficiency"""
        # Separate workflow steps and interruptions
        workflow_steps = [r for r in workflow_results if r["type"] == "workflow_step"]
        interruptions = [r for r in workflow_results if r["type"] == "interruption"]

        # Calculate efficiency based on task completion and interruption handling
        step_scores = [r.get("tool_analysis", {}).get("coordination_score", 0.5) for r in workflow_steps]
        interruption_scores = [r.get("recovery_score", 0.5) for r in interruptions]

        avg_step_efficiency = statistics.mean(step_scores) if step_scores else 0.5
        avg_interruption_efficiency = statistics.mean(interruption_scores) if interruptions else 1.0

        # Weight steps more heavily than interruptions
        multitask_efficiency = (avg_step_efficiency * 0.8) + (avg_interruption_efficiency * 0.2)

        return multitask_efficiency

    def _evaluate_performance(self, result: Dict, feedback_type: str) -> float:
        """Evaluate performance based on feedback type"""
        content = result.get("content", "")
        base_confidence = result.get("confidence", 0.5)

        # Quality indicators based on feedback type
        if feedback_type == "code_quality":
            quality_indicators = ["function", "class", "error", "test", "optimize", "clean"]
        elif feedback_type == "accuracy":
            quality_indicators = ["correct", "accurate", "precise", "exact", "verify"]
        elif feedback_type == "clarity":
            quality_indicators = ["clear", "simple", "understand", "explain", "example"]
        else:
            quality_indicators = ["good", "better", "improve", "quality", "effective"]

        indicator_count = sum(1 for ind in quality_indicators if ind in content.lower())
        quality_bonus = min(indicator_count / len(quality_indicators), 0.3)

        return min(base_confidence + quality_bonus, 1.0)

    def _generate_feedback(self, result: Dict, performance_score: float, feedback_type: str) -> str:
        """Generate feedback for next iteration"""
        if performance_score > 0.8:
            return "Excellent work. Consider adding more advanced features and edge case handling."
        elif performance_score > 0.6:
            return "Good progress. Focus on improving code quality and adding comprehensive error handling."
        elif performance_score > 0.4:
            return "Decent start. Need to improve clarity, structure, and add proper documentation."
        else:
            return "Needs significant improvement. Focus on basic functionality, clear structure, and proper implementation."

    def _measure_feedback_integration(self, current_result: Dict, previous_feedback: str) -> float:
        """Measure how well agent integrated previous feedback"""
        content = current_result.get("content", "").lower()
        feedback_lower = previous_feedback.lower()

        # Extract key feedback terms
        feedback_keywords = ["improve", "focus", "add", "enhance", "better", "quality"]
        feedback_terms = [term for term in feedback_keywords if term in feedback_lower]

        # Check if feedback terms are addressed in current result
        addressed_terms = sum(1 for term in feedback_terms if term in content)

        integration_score = addressed_terms / len(feedback_terms) if feedback_terms else 0.5
        return min(integration_score, 1.0)

    def _calculate_learning_convergence(self, performance_history: List[float]) -> float:
        """Calculate how quickly performance converges to optimal level"""
        if len(performance_history) < 2:
            return 0.5

        # Calculate improvement trend
        improvements = [performance_history[i] - performance_history[i-1] for i in range(1, len(performance_history))]

        # Convergence is good if early improvements are large and later ones stabilize
        if len(improvements) <= 2:
            return statistics.mean(improvements) if improvements else 0.5

        early_improvements = improvements[:len(improvements)//2]
        late_improvements = improvements[len(improvements)//2:]

        early_avg = statistics.mean(early_improvements) if early_improvements else 0
        late_avg = abs(statistics.mean(late_improvements)) if late_improvements else 0

        # Good convergence: high early improvement, low late variation
        convergence_score = (early_avg * 0.7) + ((1 - min(late_avg, 1.0)) * 0.3)
        return min(max(convergence_score, 0), 1.0)

    # Recommendation generation methods
    def _generate_locomo_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """Generate recommendations for LoCoMo test improvements"""
        recommendations = []

        if metrics["cross_session_recall"] < 0.7:
            recommendations.append("Improve cross-session memory retrieval by implementing stronger contextual associations")

        if metrics["preference_retention"] < 0.8:
            recommendations.append("Enhance preference tracking with more robust categorization and tagging")

        if metrics["context_adaptation"] < 0.7:
            recommendations.append("Develop better context switching mechanisms for different user personas")

        if metrics["knowledge_accumulation"] < 0.6:
            recommendations.append("Implement knowledge graph structures to better accumulate and relate information")

        return recommendations or ["Continue maintaining excellent multi-session memory performance"]

    def _generate_professional_task_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """Generate recommendations for professional task improvements"""
        recommendations = []

        if metrics["avg_completion_rate"] < 0.8:
            recommendations.append("Focus on breaking down complex tasks into more manageable subtasks")

        if metrics["avg_quality_score"] < 0.8:
            recommendations.append("Implement quality assurance checkpoints throughout task execution")

        if metrics["avg_efficiency_score"] < 0.7:
            recommendations.append("Optimize task sequencing and resource allocation for better efficiency")

        if metrics["avg_problem_solving"] < 0.8:
            recommendations.append("Enhance problem-solving methodologies with more systematic approaches")

        return recommendations or ["Maintain excellent professional task execution standards"]

    def _generate_evolutionary_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """Generate recommendations for evolutionary learning improvements"""
        recommendations = []

        if metrics["avg_learning_rate"] < 0.3:
            recommendations.append("Implement more aggressive learning strategies with faster adaptation cycles")

        if metrics["avg_adaptation_speed"] < 0.5:
            recommendations.append("Develop rapid response mechanisms for quick adaptation to new information")

        if metrics["knowledge_accumulation"] < 20:
            recommendations.append("Enhance knowledge extraction and synthesis capabilities for better accumulation")

        if metrics["error_reduction_rate"] < 0.4:
            recommendations.append("Implement stronger error detection and correction mechanisms")

        return recommendations or ["Continue excellent evolutionary learning performance"]

    def _generate_coherence_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """Generate recommendations for coherence improvements"""
        recommendations = []

        if metrics["overall_consistency"] < 0.9:
            recommendations.append("Implement stronger consistency checking mechanisms across extended interactions")

        if metrics["overall_logical_flow"] < 0.9:
            recommendations.append("Enhance logical flow management with better transition handling")

        if metrics["overall_context_stability"] < 0.9:
            recommendations.append("Develop more robust context maintenance and retrieval systems")

        if metrics["overall_coherence_ratio"] < 0.95:
            recommendations.append("Reduce coherence breakdowns with improved contradiction detection")

        return recommendations or ["Maintain excellent long-term coherence standards"]

    def _generate_multi_tool_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """Generate recommendations for multi-tool interaction improvements"""
        recommendations = []

        if metrics["avg_tool_coordination"] < 0.8:
            recommendations.append("Improve tool coordination mechanisms with better inter-tool communication")

        if metrics["avg_workflow_continuity"] < 0.8:
            recommendations.append("Enhance workflow continuity management with smoother transitions")

        if metrics["avg_interruption_recovery"] < 0.8:
            recommendations.append("Develop more robust interruption handling and recovery mechanisms")

        if metrics["avg_multitask_efficiency"] < 0.8:
            recommendations.append("Optimize multitasking capabilities with better resource management")

        return recommendations or ["Maintain excellent multi-tool coordination performance"]

    def _generate_learning_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """Generate recommendations for adaptive learning improvements"""
        recommendations = []

        if metrics["avg_improvement_rate"] < 0.4:
            recommendations.append("Implement more effective learning algorithms for faster improvement")

        if metrics["avg_feedback_integration"] < 0.8:
            recommendations.append("Enhance feedback processing and integration mechanisms")

        if metrics["avg_learning_velocity"] < 0.6:
            recommendations.append("Increase learning velocity with more rapid adaptation cycles")

        if metrics["avg_convergence_score"] < 0.7:
            recommendations.append("Improve convergence patterns for more stable learning trajectories")

        return recommendations or ["Continue excellent adaptive learning performance"]

async def run_advanced_growth_tests():
    """Main function to run all advanced growth tests"""
    print("=" * 80)
    print("ADVANCED AGENT GROWTH TESTING FRAMEWORK")
    print("=" * 80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Initialize agent
    print("\n1. Initializing Enhanced Prince Flowers Agent...")
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

        print("[OK] Agent initialized successfully")

    except Exception as e:
        print(f"[ERROR] Failed to initialize agent: {e}")
        return False

    # Run comprehensive growth evaluation
    print("\n2. Running Comprehensive Growth Evaluation...")
    print("-" * 50)

    tester = AdvancedAgentGrowthTester(agent)
    test_results = await tester.run_comprehensive_growth_evaluation()

    # Generate comprehensive report
    print("\n3. Advanced Growth Test Results")
    print("-" * 50)

    overall_scores = []
    for test_name, result in test_results.items():
        print(f"\n{result.test_name}:")
        print(f"  Status: {'[PASS]' if result.success else '[FAIL]'}")
        print(f"  Score: {result.score:.1%}")
        print(f"  Time: {result.execution_time:.1f}s")

        if result.metrics:
            print("  Key Metrics:")
            for metric, value in result.metrics.items():
                print(f"    {metric}: {value:.1%}")

        if result.growth_indicators:
            print("  Growth Indicators:")
            for indicator, value in result.growth_indicators.items():
                print(f"    {indicator}: {value:.1%}")

        if result.recommendations:
            print("  Recommendations:")
            for rec in result.recommendations[:3]:  # Top 3 recommendations
                print(f"    • {rec}")

        overall_scores.append(result.score)

    # Calculate overall growth score
    overall_growth_score = statistics.mean(overall_scores)

    print(f"\n" + "=" * 50)
    print("OVERALL GROWTH ASSESSMENT")
    print("=" * 50)
    print(f"Overall Growth Score: {overall_growth_score:.1%}")
    print(f"Tests Passed: {sum(1 for r in test_results.values() if r.success)}/{len(test_results)}")

    # Determine growth level
    if overall_growth_score >= 0.9:
        growth_level = "EXCEPTIONAL - Agent shows excellent growth and learning capabilities"
    elif overall_growth_score >= 0.8:
        growth_level = "STRONG - Agent demonstrates good adaptive learning and memory"
    elif overall_growth_score >= 0.7:
        growth_level = "MODERATE - Agent shows satisfactory growth with room for improvement"
    elif overall_growth_score >= 0.6:
        growth_level = "DEVELOPING - Agent exhibits basic learning but needs enhancement"
    else:
        growth_level = "NEEDS WORK - Agent requires significant improvements in growth capabilities"

    print(f"Growth Level: {growth_level}")

    # Save comprehensive results
    comprehensive_results = {
        "test_date": datetime.now().isoformat(),
        "test_type": "advanced_agent_growth_evaluation",
        "overall_growth_score": overall_growth_score,
        "growth_level": growth_level,
        "tests_passed": sum(1 for r in test_results.values() if r.success),
        "total_tests": len(test_results),
        "test_results": {name: asdict(result) for name, result in test_results.items()},
        "recommendations": [
            "Continue monitoring growth metrics on a weekly basis",
            "Focus on areas with scores below 0.7 for targeted improvement",
            "Implement learning feedback loops for continuous enhancement",
            "Document successful learning patterns for future agent development"
        ]
    }

    results_file = "E:/TORQ-CONSOLE/maxim_integration/advanced_growth_test_results.json"
    with open(results_file, "w") as f:
        json.dump(comprehensive_results, f, indent=2)

    print(f"\n[OK] Detailed results saved to: {results_file}")

    # Cleanup
    try:
        await agent.cleanup()
        print("[OK] Agent cleanup completed")
    except Exception as e:
        print(f"[WARNING] Cleanup failed: {e}")

    return overall_growth_score >= 0.7

if __name__ == "__main__":
    asyncio.run(run_advanced_growth_tests())