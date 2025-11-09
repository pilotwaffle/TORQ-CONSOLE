"""
Maxim AI Integration - Prince Flowers Evaluator
Phase 1: Evaluation Framework Integration

This module provides comprehensive evaluation capabilities for the TORQ Console
Prince Flowers agents using Maxim AI's evaluation methodology.
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from datetime import datetime, timedelta
import numpy as np

# Import TORQ Console agents
try:
    from torq_console.agents.torq_prince_flowers import TorqPrinceFlowers
    from torq_console.agents.marvin_prince_flowers import MarvinPrinceFlowers
    from torq_console.agents.marvin_orchestrator import MarvinAgentOrchestrator
except ImportError as e:
    logging.warning(f"TORQ agents not available: {e}")
    # Create mock classes for testing
    class MockTorqPrinceFlowers:
        def __init__(self, llm_provider=None): pass
        async def process_query(self, query):
            return {"response": f"Mock TorqPrince response to: {query}", "success": True}

    class MockMarvinPrinceFlowers:
        def __init__(self): pass
        async def chat(self, query, context=None):
            return f"Mock MarvinPrince response to: {query}"

    TorqPrinceFlowers = MockTorqPrinceFlowers
    MarvinPrinceFlowers = MockMarvinPrinceFlowers

class EvaluationMetric(Enum):
    """Standard evaluation metrics based on Maxim AI framework"""
    REASONING_QUALITY = "reasoning_quality"
    RESPONSE_RELEVANCE = "response_relevance"
    TOOL_SELECTION_EFFICIENCY = "tool_selection_efficiency"
    MULTI_STEP_ACCURACY = "multi_step_accuracy"
    EXECUTION_TIME = "execution_time"
    ERROR_RATE = "error_rate"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    USER_SATISFACTION = "user_satisfaction"

class AgentType(Enum):
    TORQ_PRINCE = "torq_prince_flowers"
    MARVIN_PRINCE = "marvin_prince_flowers"
    ORCHESTRATOR = "orchestrator"

@dataclass
class EvaluationCriteria:
    """Custom evaluation criteria for agentic workflows"""
    name: str
    description: str
    weight: float  # 0.0 to 1.0
    measurement_method: str  # "quantitative", "qualitative", "hybrid"
    target_threshold: float  # Minimum acceptable score
    evaluation_function: str  # Name of evaluation function

@dataclass
class QueryTestCase:
    """Test case for agent evaluation"""
    query: str
    expected_agent_type: AgentType
    expected_tools: List[str]
    complexity_score: float  # 0.0 to 1.0
    domain: str  # "search", "analysis", "code", "general"
    expected_quality_score: float  # 0.0 to 1.0
    reasoning_steps_expected: int

@dataclass
class AgentPerformanceResult:
    """Result of single agent evaluation"""
    agent_type: AgentType
    query: str
    response: str
    success: bool
    execution_time: float
    confidence: float
    tools_used: List[str]
    reasoning_steps: int
    error_count: int
    timestamp: datetime
    detailed_metrics: Dict[str, float]

@dataclass
class EvaluationSummary:
    """Summary of evaluation results"""
    total_queries: int
    success_rate: float
    average_execution_time: float
    average_confidence: float
    agent_performance: Dict[AgentType, Dict[str, float]]
    metric_scores: Dict[EvaluationMetric, float]
    recommendations: List[str]
    overall_quality_score: float
    evaluation_timestamp: datetime

class PrinceFlowersEvaluator:
    """
    Comprehensive evaluator for Prince Flowers agents using Maxim AI methodology
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

        # Initialize agents
        self.agents = {}
        self._initialize_agents()

        # Evaluation criteria based on Maxim's framework
        self.evaluation_criteria = self._setup_evaluation_criteria()

        # Test cases for evaluation
        self.test_cases = self._create_test_cases()

        # Results storage
        self.evaluation_results = []
        self.performance_history = []

        self.logger.info("Prince Flowers Evaluator initialized with Maxim AI integration")

    def setup_logging(self):
        """Setup detailed logging for evaluation"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('E:/TORQ-CONSOLE/logs/prince_flowers_evaluation.log'),
                logging.StreamHandler()
            ]
        )

    def _initialize_agents(self):
        """Initialize available Prince Flowers agents"""
        try:
            # Initialize TorqPrinceFlowers (with tools)
            self.agents[AgentType.TORQ_PRINCE] = TorqPrinceFlowers()
            self.logger.info("TorqPrinceFlowers agent initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize TorqPrinceFlowers: {e}")

        try:
            # Initialize MarvinPrinceFlowers (conversational)
            self.agents[AgentType.MARVIN_PRINCE] = MarvinPrinceFlowers()
            self.logger.info("MarvinPrinceFlowers agent initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize MarvinPrinceFlowers: {e}")

        try:
            # Initialize Orchestrator
            self.agents[AgentType.ORCHESTRATOR] = MarvinAgentOrchestrator()
            self.logger.info("MarvinAgentOrchestrator initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize orchestrator: {e}")

    def _setup_evaluation_criteria(self) -> List[EvaluationCriteria]:
        """Setup evaluation criteria based on Maxim AI framework"""
        return [
            EvaluationCriteria(
                name="Reasoning Quality",
                description="Quality of logical reasoning and step-by-step analysis",
                weight=0.25,
                measurement_method="hybrid",
                target_threshold=0.75,
                evaluation_function="evaluate_reasoning_quality"
            ),
            EvaluationCriteria(
                name="Response Relevance",
                description="How well the response addresses the user's query",
                weight=0.20,
                measurement_method="quantitative",
                target_threshold=0.80,
                evaluation_function="evaluate_response_relevance"
            ),
            EvaluationCriteria(
                name="Tool Selection Efficiency",
                description="Appropriateness and efficiency of tool usage",
                weight=0.15,
                measurement_method="quantitative",
                target_threshold=0.70,
                evaluation_function="evaluate_tool_efficiency"
            ),
            EvaluationCriteria(
                name="Multi-step Accuracy",
                description="Accuracy of multi-step reasoning processes",
                weight=0.15,
                measurement_method="quantitative",
                target_threshold=0.75,
                evaluation_function="evaluate_multi_step_accuracy"
            ),
            EvaluationCriteria(
                name="Execution Performance",
                description="Speed and efficiency of response generation",
                weight=0.10,
                measurement_method="quantitative",
                target_threshold=0.80,
                evaluation_function="evaluate_execution_performance"
            ),
            EvaluationCriteria(
                name="Error Handling",
                description="Ability to handle errors gracefully",
                weight=0.10,
                measurement_method="quantitative",
                target_threshold=0.90,
                evaluation_function="evaluate_error_handling"
            ),
            EvaluationCriteria(
                name="Confidence Calibration",
                description="Accuracy of confidence scores",
                weight=0.05,
                measurement_method="quantitative",
                target_threshold=0.70,
                evaluation_function="evaluate_confidence_calibration"
            )
        ]

    def _create_test_cases(self) -> List[QueryTestCase]:
        """Create comprehensive test cases for evaluation"""
        return [
            # Search queries (should route to TorqPrinceFlowers)
            QueryTestCase(
                query="Search GitHub and list top 3 repository links with the most workflows",
                expected_agent_type=AgentType.TORQ_PRINCE,
                expected_tools=["web_search", "github_api"],
                complexity_score=0.7,
                domain="search",
                expected_quality_score=0.8,
                reasoning_steps_expected=3
            ),
            QueryTestCase(
                query="Find latest news about artificial intelligence developments",
                expected_agent_type=AgentType.TORQ_PRINCE,
                expected_tools=["web_search", "news_api"],
                complexity_score=0.6,
                domain="search",
                expected_quality_score=0.8,
                reasoning_steps_expected=2
            ),

            # Analysis queries (should route to MarvinPrinceFlowers)
            QueryTestCase(
                query="Explain the benefits of async/await patterns in Python",
                expected_agent_type=AgentType.MARVIN_PRINCE,
                expected_tools=[],
                complexity_score=0.8,
                domain="analysis",
                expected_quality_score=0.9,
                reasoning_steps_expected=4
            ),
            QueryTestCase(
                query="Compare machine learning frameworks: TensorFlow vs PyTorch",
                expected_agent_type=AgentType.MARVIN_PRINCE,
                expected_tools=[],
                complexity_score=0.9,
                domain="analysis",
                expected_quality_score=0.9,
                reasoning_steps_expected=5
            ),

            # Code generation queries
            QueryTestCase(
                query="Create a simple REST API with Python FastAPI",
                expected_agent_type=AgentType.ORCHESTRATOR,
                expected_tools=["code_generation"],
                complexity_score=0.8,
                domain="code",
                expected_quality_score=0.85,
                reasoning_steps_expected=4
            ),

            # General queries
            QueryTestCase(
                query="What are your capabilities and how can you help me?",
                expected_agent_type=AgentType.MARVIN_PRINCE,
                expected_tools=[],
                complexity_score=0.3,
                domain="general",
                expected_quality_score=0.8,
                reasoning_steps_expected=2
            ),

            # Complex multi-tool queries
            QueryTestCase(
                query="Research the latest trends in web development and create a summary",
                expected_agent_type=AgentType.TORQ_PRINCE,
                expected_tools=["web_search", "content_analysis"],
                complexity_score=0.9,
                domain="research",
                expected_quality_score=0.85,
                reasoning_steps_expected=5
            )
        ]

    async def evaluate_single_query(self, test_case: QueryTestCase, agent_type: AgentType) -> AgentPerformanceResult:
        """
        Evaluate a single query against a specific agent
        """
        start_time = time.time()

        try:
            # Get the appropriate agent
            agent = self.agents.get(agent_type)
            if not agent:
                raise Exception(f"Agent {agent_type} not available")

            # Execute the query
            if agent_type == AgentType.TORQ_PRINCE:
                result = await agent.process_query(test_case.query)
                response = result.get("response", "")
                success = result.get("success", False)
                tools_used = result.get("tools_used", [])
                confidence = result.get("confidence", 0.5)
            elif agent_type == AgentType.MARVIN_PRINCE:
                response = await agent.chat(test_case.query)
                success = True  # Assume success for chat
                tools_used = []
                confidence = 0.8  # Default confidence
            elif agent_type == AgentType.ORCHESTRATOR:
                result = await agent.process_query(test_case.query)
                response = result.get("answer", "")
                success = result.get("success", False)
                tools_used = result.get("tools_used", [])
                confidence = result.get("confidence", 0.5)
            else:
                raise Exception(f"Unknown agent type: {agent_type}")

            execution_time = time.time() - start_time

            # Calculate detailed metrics
            detailed_metrics = await self._calculate_detailed_metrics(
                test_case, response, success, execution_time, tools_used, confidence
            )

            # Count reasoning steps (simplified)
            reasoning_steps = self._count_reasoning_steps(response)

            return AgentPerformanceResult(
                agent_type=agent_type,
                query=test_case.query,
                response=response,
                success=success,
                execution_time=execution_time,
                confidence=confidence,
                tools_used=tools_used,
                reasoning_steps=reasoning_steps,
                error_count=0 if success else 1,
                timestamp=datetime.now(),
                detailed_metrics=detailed_metrics
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error evaluating query '{test_case.query}' with {agent_type}: {e}")

            return AgentPerformanceResult(
                agent_type=agent_type,
                query=test_case.query,
                response=f"Error: {str(e)}",
                success=False,
                execution_time=execution_time,
                confidence=0.0,
                tools_used=[],
                reasoning_steps=0,
                error_count=1,
                timestamp=datetime.now(),
                detailed_metrics={}
            )

    async def _calculate_detailed_metrics(self, test_case: QueryTestCase, response: str,
                                        success: bool, execution_time: float,
                                        tools_used: List[str], confidence: float) -> Dict[str, float]:
        """Calculate detailed evaluation metrics"""
        metrics = {}

        # Reasoning Quality
        metrics["reasoning_quality"] = self.evaluate_reasoning_quality(
            test_case, response, success
        )

        # Response Relevance
        metrics["response_relevance"] = self.evaluate_response_relevance(
            test_case, response
        )

        # Tool Selection Efficiency
        metrics["tool_selection_efficiency"] = self.evaluate_tool_efficiency(
            test_case, tools_used
        )

        # Multi-step Accuracy
        metrics["multi_step_accuracy"] = self.evaluate_multi_step_accuracy(
            test_case, response
        )

        # Execution Performance
        metrics["execution_performance"] = self.evaluate_execution_performance(
            execution_time, test_case.complexity_score
        )

        # Error Handling
        metrics["error_handling"] = self.evaluate_error_handling(
            success, response
        )

        # Confidence Calibration
        metrics["confidence_calibration"] = self.evaluate_confidence_calibration(
            confidence, success, response
        )

        return metrics

    def evaluate_reasoning_quality(self, test_case: QueryTestCase, response: str, success: bool) -> float:
        """Evaluate the quality of reasoning in the response"""
        score = 0.5  # Base score

        # Check for structured reasoning
        reasoning_indicators = ["first", "second", "finally", "therefore", "because", "however"]
        reasoning_count = sum(1 for indicator in reasoning_indicators if indicator.lower() in response.lower())
        score += min(0.3, reasoning_count * 0.1)

        # Check length appropriateness
        expected_length = 50 + test_case.complexity_score * 200
        actual_length = len(response)
        length_ratio = min(actual_length / expected_length, 2.0)
        if 0.5 <= length_ratio <= 1.5:
            score += 0.2

        # Success bonus
        if success:
            score += 0.2

        return min(1.0, score)

    def evaluate_response_relevance(self, test_case: QueryTestCase, response: str) -> float:
        """Evaluate how relevant the response is to the query"""
        query_words = set(test_case.query.lower().split())
        response_words = set(response.lower().split())

        # Calculate word overlap
        overlap = len(query_words.intersection(response_words))
        relevance_score = min(1.0, overlap / len(query_words)) if query_words else 0.0

        # Check for domain-specific keywords
        domain_keywords = {
            "search": ["search", "find", "look up", "results", "links"],
            "analysis": ["analyze", "explain", "compare", "benefits", "differences"],
            "code": ["create", "generate", "code", "implement", "function"],
            "general": ["help", "capabilities", "can", "features"]
        }

        if test_case.domain in domain_keywords:
            domain_words = set(domain_keywords[test_case.domain])
            domain_overlap = len(domain_words.intersection(response_words))
            relevance_score += min(0.3, domain_overlap * 0.1)

        return min(1.0, relevance_score)

    def evaluate_tool_efficiency(self, test_case: QueryTestCase, tools_used: List[str]) -> float:
        """Evaluate the efficiency of tool selection"""
        expected_tools = set(test_case.expected_tools)
        actual_tools = set(tools_used)

        # Perfect match
        if expected_tools == actual_tools:
            return 1.0

        # Calculate precision and recall
        if len(actual_tools) == 0:
            precision = 0.0
        else:
            precision = len(expected_tools.intersection(actual_tools)) / len(actual_tools)

        if len(expected_tools) == 0:
            recall = 1.0 if len(actual_tools) == 0 else 0.0
        else:
            recall = len(expected_tools.intersection(actual_tools)) / len(expected_tools)

        # F1 score
        if precision + recall == 0:
            return 0.0
        f1_score = 2 * (precision * recall) / (precision + recall)

        return f1_score

    def evaluate_multi_step_accuracy(self, test_case: QueryTestCase, response: str) -> float:
        """Evaluate accuracy of multi-step reasoning"""
        reasoning_steps = self._count_reasoning_steps(response)
        expected_steps = test_case.reasoning_steps_expected

        if expected_steps == 0:
            return 1.0

        # Calculate how close the number of steps is to expected
        step_ratio = min(reasoning_steps / expected_steps, 2.0)

        if 0.8 <= step_ratio <= 1.2:
            return 1.0
        elif 0.6 <= step_ratio <= 1.5:
            return 0.8
        elif 0.4 <= step_ratio <= 2.0:
            return 0.6
        else:
            return 0.4

    def evaluate_execution_performance(self, execution_time: float, complexity_score: float) -> float:
        """Evaluate execution performance based on complexity"""
        # Expected time based on complexity
        expected_time = 1.0 + complexity_score * 3.0  # 1-4 seconds

        if execution_time <= expected_time:
            return 1.0
        elif execution_time <= expected_time * 2:
            return 0.8
        elif execution_time <= expected_time * 3:
            return 0.6
        else:
            return 0.4

    def evaluate_error_handling(self, success: bool, response: str) -> float:
        """Evaluate error handling capabilities"""
        if success:
            return 1.0

        # Check for graceful error messages
        error_indicators = ["error", "failed", "issue", "problem", "unavailable"]
        has_error_message = any(indicator in response.lower() for indicator in error_indicators)

        if has_error_message:
            return 0.8  # Graceful error handling
        else:
            return 0.4  # Poor error handling

    def evaluate_confidence_calibration(self, confidence: float, success: bool, response: str) -> float:
        """Evaluate how well confidence scores are calibrated"""
        if not success:
            # Failed responses should have low confidence
            return max(0.0, 1.0 - confidence)

        # Successful responses should have appropriate confidence
        # Based on response length and complexity
        response_quality = min(1.0, len(response) / 200)
        expected_confidence = 0.5 + response_quality * 0.4

        calibration_score = 1.0 - abs(confidence - expected_confidence)
        return max(0.0, calibration_score)

    def _count_reasoning_steps(self, response: str) -> int:
        """Count the number of reasoning steps in a response"""
        step_indicators = [
            "first", "second", "third", "fourth", "fifth",
            "step 1", "step 2", "step 3", "step 4", "step 5",
            "1.", "2.", "3.", "4.", "5.",
            "next", "then", "after that", "finally"
        ]

        step_count = 0
        for indicator in step_indicators:
            step_count += response.lower().count(indicator)

        return min(step_count, 10)  # Cap at 10 steps

    async def run_comprehensive_evaluation(self) -> EvaluationSummary:
        """
        Run comprehensive evaluation of all agents against all test cases
        """
        self.logger.info("Starting comprehensive Prince Flowers evaluation")

        all_results = []
        agent_results = {agent_type: [] for agent_type in AgentType}

        # Test each query with each appropriate agent
        for test_case in self.test_cases:
            self.logger.info(f"Evaluating query: {test_case.query[:50]}...")

            # Test with expected agent
            result = await self.evaluate_single_query(test_case, test_case.expected_agent_type)
            all_results.append(result)
            agent_results[test_case.expected_agent_type].append(result)

            # Test with other agents for comparison
            for agent_type in AgentType:
                if agent_type != test_case.expected_agent_type and agent_type in self.agents:
                    comparison_result = await self.evaluate_single_query(test_case, agent_type)
                    all_results.append(comparison_result)
                    agent_results[agent_type].append(comparison_result)

        # Calculate overall metrics
        evaluation_summary = self._calculate_evaluation_summary(all_results, agent_results)

        # Store results
        self.evaluation_results.extend(all_results)
        self.performance_history.append(evaluation_summary)

        # Save results to file
        await self._save_evaluation_results(evaluation_summary, all_results)

        self.logger.info(f"Evaluation completed. Overall quality score: {evaluation_summary.overall_quality_score:.2f}")

        return evaluation_summary

    def _calculate_evaluation_summary(self, all_results: List[AgentPerformanceResult],
                                    agent_results: Dict[AgentType, List[AgentPerformanceResult]]) -> EvaluationSummary:
        """Calculate comprehensive evaluation summary"""

        # Basic metrics
        total_queries = len(all_results)
        successful_queries = sum(1 for r in all_results if r.success)
        success_rate = successful_queries / total_queries if total_queries > 0 else 0.0

        execution_times = [r.execution_time for r in all_results]
        average_execution_time = statistics.mean(execution_times) if execution_times else 0.0

        confidences = [r.confidence for r in all_results if r.confidence > 0]
        average_confidence = statistics.mean(confidences) if confidences else 0.0

        # Agent performance
        agent_performance = {}
        for agent_type, results in agent_results.items():
            if results:
                agent_success_rate = sum(1 for r in results if r.success) / len(results)
                agent_avg_time = statistics.mean([r.execution_time for r in results])
                agent_avg_confidence = statistics.mean([r.confidence for r in results])

                # Calculate average metric scores
                avg_metrics = {}
                if results[0].detailed_metrics:
                    for metric_name in results[0].detailed_metrics.keys():
                        metric_values = [r.detailed_metrics.get(metric_name, 0.0) for r in results]
                        avg_metrics[metric_name] = statistics.mean(metric_values)

                agent_performance[agent_type] = {
                    "success_rate": agent_success_rate,
                    "average_execution_time": agent_avg_time,
                    "average_confidence": agent_avg_confidence,
                    "total_queries": len(results),
                    **avg_metrics
                }

        # Calculate metric scores across all results
        metric_scores = {}
        if all_results and all_results[0].detailed_metrics:
            for metric_name in all_results[0].detailed_metrics.keys():
                metric_values = [r.detailed_metrics.get(metric_name, 0.0) for r in all_results]
                metric_scores[EvaluationMetric(metric_name)] = statistics.mean(metric_values)

        # Calculate overall quality score
        overall_quality_score = self._calculate_overall_quality_score(metric_scores, self.evaluation_criteria)

        # Generate recommendations
        recommendations = self._generate_recommendations(agent_performance, metric_scores)

        return EvaluationSummary(
            total_queries=total_queries,
            success_rate=success_rate,
            average_execution_time=average_execution_time,
            average_confidence=average_confidence,
            agent_performance=agent_performance,
            metric_scores=metric_scores,
            recommendations=recommendations,
            overall_quality_score=overall_quality_score,
            evaluation_timestamp=datetime.now()
        )

    def _calculate_overall_quality_score(self, metric_scores: Dict[EvaluationMetric, float],
                                       criteria: List[EvaluationCriteria]) -> float:
        """Calculate overall quality score using weighted criteria"""
        total_score = 0.0
        total_weight = 0.0

        for criterion in criteria:
            metric_enum = EvaluationMetric(criterion.name.lower().replace(" ", "_"))
            if metric_enum in metric_scores:
                score = metric_scores[metric_enum]
                weight = criterion.weight
                total_score += score * weight
                total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _generate_recommendations(self, agent_performance: Dict[AgentType, Dict[str, float]],
                                metric_scores: Dict[EvaluationMetric, float]) -> List[str]:
        """Generate improvement recommendations based on evaluation results"""
        recommendations = []

        # Analyze overall performance
        if metric_scores.get(EvaluationMetric.REASONING_QUALITY, 0) < 0.75:
            recommendations.append("Improve reasoning quality by implementing more structured step-by-step analysis")

        if metric_scores.get(EvaluationMetric.RESPONSE_RELEVANCE, 0) < 0.80:
            recommendations.append("Enhance response relevance through better query understanding and context matching")

        if metric_scores.get(EvaluationMetric.TOOL_SELECTION_EFFICIENCY, 0) < 0.70:
            recommendations.append("Optimize tool selection algorithms to better match query requirements")

        # Agent-specific recommendations
        for agent_type, performance in agent_performance.items():
            if performance.get("success_rate", 0) < 0.80:
                recommendations.append(f"Improve {agent_type.value} reliability and error handling")

            if performance.get("average_execution_time", 0) > 5.0:
                recommendations.append(f"Optimize {agent_type.value} performance for faster response times")

        # If no major issues, provide positive feedback
        if not recommendations:
            recommendations.append("Overall performance is excellent - consider adding more complex test cases")

        return recommendations

    async def _save_evaluation_results(self, summary: EvaluationSummary, results: List[AgentPerformanceResult]):
        """Save evaluation results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save summary
        summary_file = f"E:/TORQ-CONSOLE/evaluation_results/summary_{timestamp}.json"
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)

        summary_data = asdict(summary)
        summary_data["evaluation_timestamp"] = summary.evaluation_timestamp.isoformat()
        summary_data["metric_scores"] = {k.value: v for k, v in summary.metric_scores.items()}
        summary_data["agent_performance"] = {k.value: v for k, v in summary.agent_performance.items()}

        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)

        # Save detailed results
        results_file = f"E:/TORQ-CONSOLE/evaluation_results/detailed_{timestamp}.json"
        results_data = []

        for result in results:
            result_data = asdict(result)
            result_data["timestamp"] = result.timestamp.isoformat()
            result_data["agent_type"] = result.agent_type.value
            results_data.append(result_data)

        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)

        self.logger.info(f"Evaluation results saved to {summary_file} and {results_file}")

    def print_evaluation_summary(self, summary: EvaluationSummary):
        """Print a formatted evaluation summary"""
        print("\n" + "="*80)
        print("🤖 PRINCE FLOWERS AGENT EVALUATION SUMMARY")
        print("="*80)

        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"   • Total Queries: {summary.total_queries}")
        print(f"   • Success Rate: {summary.success_rate:.1%}")
        print(f"   • Average Execution Time: {summary.average_execution_time:.2f}s")
        print(f"   • Average Confidence: {summary.average_confidence:.1%}")
        print(f"   • Overall Quality Score: {summary.overall_quality_score:.1%}")

        print(f"\n🔍 DETAILED METRICS:")
        for metric, score in summary.metric_scores.items():
            status = "✅" if score >= 0.8 else "⚠️" if score >= 0.6 else "❌"
            print(f"   {status} {metric.value.replace('_', ' ').title()}: {score:.1%}")

        print(f"\n🤖 AGENT PERFORMANCE:")
        for agent_type, performance in summary.agent_performance.items():
            print(f"   • {agent_type.value}:")
            print(f"     - Success Rate: {performance.get('success_rate', 0):.1%}")
            print(f"     - Avg Execution Time: {performance.get('average_execution_time', 0):.2f}s")
            print(f"     - Avg Confidence: {performance.get('average_confidence', 0):.1%}")
            print(f"     - Total Queries: {performance.get('total_queries', 0)}")

        print(f"\n💡 RECOMMENDATIONS:")
        for i, recommendation in enumerate(summary.recommendations, 1):
            print(f"   {i}. {recommendation}")

        print(f"\n📅 Evaluation completed: {summary.evaluation_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

# Main execution function
async def main():
    """Main execution function for Prince Flowers evaluation"""
    print("🚀 Starting Prince Flowers Evaluation with Maxim AI Integration")

    evaluator = PrinceFlowersEvaluator()

    try:
        # Run comprehensive evaluation
        summary = await evaluator.run_comprehensive_evaluation()

        # Print results
        evaluator.print_evaluation_summary(summary)

        return summary

    except Exception as e:
        logging.error(f"Evaluation failed: {e}")
        print(f"❌ Evaluation failed: {e}")
        return None

if __name__ == "__main__":
    import os
    asyncio.run(main())