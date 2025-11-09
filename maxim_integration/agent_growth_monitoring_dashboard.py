#!/usr/bin/env python3
"""
Agent Growth Monitoring Dashboard

Integrated system that combines all advanced testing frameworks
to provide comprehensive monitoring of agent growth and capabilities.

Features:
- Real-time growth metrics tracking
- Historical performance analysis
- Predictive growth modeling
- Automated testing scheduling
- Comprehensive reporting dashboard
- Alert system for growth anomalies
"""

import asyncio
import json
import logging
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# Import all testing frameworks
from advanced_agent_growth_tests import AdvancedAgentGrowthTester, GrowthTestResult
from human_in_the_loop_evaluation import HumanInTheLoopEvaluator, HybridAssessmentResult
from configure_llm_and_test import configure_and_test_complete_system

# Add TORQ Console to path
sys.path.append('E:/TORQ-CONSOLE')

from zep_enhanced_prince_flowers import create_zep_enhanced_prince_flowers
from torq_console.llm.providers.claude import ClaudeProvider

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GrowthStatus(Enum):
    """Agent growth status levels"""
    EXCEPTIONAL = "exceptional"
    STRONG = "strong"
    COMPETENT = "competent"
    DEVELOPING = "developing"
    EMERGING = "emerging"
    CONCERNING = "concerning"

class AlertPriority(Enum):
    """Alert priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class GrowthMetricsSnapshot:
    """Snapshot of growth metrics at a point in time"""
    timestamp: str
    overall_score: float
    test_results: Dict[str, float]
    growth_trend: float
    capabilities_assessment: Dict[str, float]
    performance_indicators: Dict[str, float]
    learning_velocity: float
    memory_effectiveness: float
    tool_coordination: float

@dataclass
class GrowthAlert:
    """Growth monitoring alert"""
    alert_id: str
    timestamp: str
    priority: AlertPriority
    metric_name: str
    current_value: float
    threshold_value: float
    trend_direction: str
    description: str
    recommended_actions: List[str]

@dataclass
class GrowthProjection:
    """Projected growth based on current trends"""
    projection_date: str
    projected_score: float
    confidence_interval: Tuple[float, float]
    key_growth_areas: List[str]
    potential_blockers: List[str]

class AgentGrowthMonitoringDashboard:
    """Comprehensive agent growth monitoring system"""

    def __init__(self, agent):
        self.agent = agent
        self.dashboard_id = f"growth_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger = logging.getLogger(f"{__name__}.{self.dashboard_id}")

        # Data storage
        self.metrics_history: List[GrowthMetricsSnapshot] = []
        self.alerts: List[GrowthAlert] = []
        self.projections: List[GrowthProjection] = []

        # Monitoring configuration
        self.monitoring_config = {
            "baseline_score": 0.5,
            "target_score": 0.95,
            "critical_threshold": 0.4,
            "warning_threshold": 0.6,
            "alert_thresholds": {
                "overall_score": {"critical": 0.4, "warning": 0.6},
                "learning_velocity": {"critical": 0.1, "warning": 0.3},
                "memory_effectiveness": {"critical": 0.5, "warning": 0.7},
                "tool_coordination": {"critical": 0.5, "warning": 0.7}
            }
        }

        # Initialize testing frameworks
        self.advanced_tester = AdvancedAgentGrowthTester(agent)
        self.human_evaluator = HumanInTheLoopEvaluator(agent)

    async def run_comprehensive_growth_monitoring(self) -> Dict[str, Any]:
        """Run complete growth monitoring cycle"""
        self.logger.info("Starting Comprehensive Growth Monitoring Cycle")

        # Step 1: Run all test suites
        print("\n1. Running Comprehensive Test Suites...")
        print("-" * 50)

        test_results = await self._run_all_test_suites()

        # Step 2: Calculate current metrics
        print("\n2. Calculating Growth Metrics...")
        print("-" * 50)

        current_metrics = await self._calculate_comprehensive_metrics(test_results)

        # Step 3: Analyze trends and generate alerts
        print("\n3. Analyzing Trends and Generating Alerts...")
        print("-" * 50)

        alerts = await self._analyze_growth_trends(current_metrics)

        # Step 4: Generate growth projections
        print("\n4. Generating Growth Projections...")
        print("-" * 50)

        projections = await self._generate_growth_projections(current_metrics)

        # Step 5: Create dashboard report
        print("\n5. Creating Dashboard Report...")
        print("-" * 50)

        dashboard_report = await self._create_dashboard_report(current_metrics, alerts, projections)

        # Step 6: Save results and generate visualizations
        print("\n6. Saving Results and Generating Visualizations...")
        print("-" * 50)

        await self._save_monitoring_results(dashboard_report)
        await self._generate_visualizations(current_metrics)

        return dashboard_report

    async def _run_all_test_suites(self) -> Dict[str, Any]:
        """Run all available test suites"""
        test_results = {}

        # 1. Advanced Growth Tests
        print("   Running Advanced Growth Tests...")
        try:
            advanced_results = await self.advanced_tester.run_comprehensive_growth_evaluation()
            test_results["advanced_tests"] = advanced_results
            print(f"   [OK] Advanced tests completed: {len(advanced_results)} scenarios")
        except Exception as e:
            self.logger.error(f"Advanced tests failed: {e}")
            test_results["advanced_tests"] = {"error": str(e)}
            print(f"   [ERROR] Advanced tests failed: {e}")

        # 2. Human-in-the-Loop Evaluation
        print("   Running Human-in-the-Loop Evaluation...")
        try:
            human_results = await self.human_evaluator.run_comprehensive_human_evaluation()
            test_results["human_evaluation"] = human_results
            print(f"   [OK] Human evaluation completed: {len(human_results)} scenarios")
        except Exception as e:
            self.logger.error(f"Human evaluation failed: {e}")
            test_results["human_evaluation"] = {"error": str(e)}
            print(f"   [ERROR] Human evaluation failed: {e}")

        # 3. Complete System Performance Test
        print("   Running Complete System Performance Test...")
        try:
            system_success = await configure_and_test_complete_system()
            test_results["system_performance"] = {"success": system_success}
            print(f"   [OK] System performance test: {'PASS' if system_success else 'FAIL'}")
        except Exception as e:
            self.logger.error(f"System performance test failed: {e}")
            test_results["system_performance"] = {"error": str(e)}
            print(f"   [ERROR] System performance test failed: {e}")

        return test_results

    async def _calculate_comprehensive_metrics(self, test_results: Dict[str, Any]) -> GrowthMetricsSnapshot:
        """Calculate comprehensive growth metrics from test results"""

        # Extract scores from different test suites
        scores = []

        # Advanced test scores
        if "advanced_tests" in test_results and isinstance(test_results["advanced_tests"], dict):
            for test_name, result in test_results["advanced_tests"].items():
                if hasattr(result, 'score'):
                    scores.append(result.score)
                    self.logger.info(f"Advanced test {test_name}: {result.score:.3f}")

        # Human evaluation scores
        if "human_evaluation" in test_results and isinstance(test_results["human_evaluation"], dict):
            for scenario, result in test_results["human_evaluation"].items():
                if hasattr(result, 'hybrid_score'):
                    scores.append(result.hybrid_score)
                    self.logger.info(f"Human evaluation {scenario}: {result.hybrid_score:.3f}")

        # System performance
        if "system_performance" in test_results:
            sys_perf = test_results["system_performance"]
            if isinstance(sys_perf, dict) and sys_perf.get("success"):
                scores.append(0.95)  # High score for successful system test
                self.logger.info("System performance: 0.950")
            elif isinstance(sys_perf, dict) and "error" in sys_perf:
                scores.append(0.3)  # Low score for failed system test
                self.logger.info("System performance: 0.300 (failed)")

        # Calculate overall score
        overall_score = statistics.mean(scores) if scores else 0.0

        # Calculate growth trend (compare with historical data)
        growth_trend = self._calculate_growth_trend(overall_score)

        # Assess specific capabilities
        capabilities_assessment = await self._assess_capabilities(test_results)

        # Calculate performance indicators
        performance_indicators = self._calculate_performance_indicators(test_results)

        # Calculate learning velocity
        learning_velocity = self._calculate_learning_velocity(test_results)

        # Calculate memory effectiveness
        memory_effectiveness = self._calculate_memory_effectiveness(test_results)

        # Calculate tool coordination
        tool_coordination = self._calculate_tool_coordination(test_results)

        # Create metrics snapshot
        snapshot = GrowthMetricsSnapshot(
            timestamp=datetime.now().isoformat(),
            overall_score=overall_score,
            test_results={name: (result.score if hasattr(result, 'score') else
                             result.hybrid_score if hasattr(result, 'hybrid_score') else 0.5)
                         for name, result in test_results.items()
                         if isinstance(result, (GrowthTestResult, HybridAssessmentResult)) or
                            (isinstance(result, dict) and not result.get("error"))},
            growth_trend=growth_trend,
            capabilities_assessment=capabilities_assessment,
            performance_indicators=performance_indicators,
            learning_velocity=learning_velocity,
            memory_effectiveness=memory_effectiveness,
            tool_coordination=tool_coordination
        )

        # Store in history
        self.metrics_history.append(snapshot)

        # Keep only last 30 snapshots (30 days of data)
        if len(self.metrics_history) > 30:
            self.metrics_history = self.metrics_history[-30:]

        return snapshot

    def _calculate_growth_trend(self, current_score: float) -> float:
        """Calculate growth trend based on historical data"""
        if len(self.metrics_history) < 2:
            return 0.0  # No trend data available

        # Calculate trend over last 5 measurements
        recent_snapshots = self.metrics_history[-5:]
        scores = [s.overall_score for s in recent_snapshots]

        if len(scores) < 2:
            return 0.0

        # Simple linear trend calculation
        x = list(range(len(scores)))
        n = len(scores)

        sum_x = sum(x)
        sum_y = sum(scores)
        sum_xy = sum(x[i] * scores[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        # Calculate slope (trend)
        if n * sum_x2 - sum_x ** 2 != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        else:
            slope = 0.0

        # Normalize trend to -1 to 1 range
        normalized_trend = max(min(slope * 10, 1.0), -1.0)

        return normalized_trend

    async def _assess_capabilities(self, test_results: Dict[str, Any]) -> Dict[str, float]:
        """Assess specific capabilities from test results"""
        capabilities = {
            "memory_integration": 0.0,
            "learning_adaptation": 0.0,
            "problem_solving": 0.0,
            "communication": 0.0,
            "collaboration": 0.0,
            "creativity": 0.0,
            "ethical_reasoning": 0.0,
            "technical_skills": 0.0
        }

        # Extract capability scores from test results
        if "advanced_tests" in test_results and isinstance(test_results["advanced_tests"], dict):
            advanced_tests = test_results["advanced_tests"]

            # Map test results to capabilities
            if "locomo_test" in advanced_tests and hasattr(advanced_tests["locomo_test"], 'metrics'):
                metrics = advanced_tests["locomo_test"].metrics
                capabilities["memory_integration"] = metrics.get("cross_session_recall", 0.5)
                capabilities["learning_adaptation"] = metrics.get("preference_retention", 0.5)

            if "professional_tasks" in advanced_tests and hasattr(advanced_tests["professional_tasks"], 'metrics'):
                metrics = advanced_tests["professional_tasks"].metrics
                capabilities["problem_solving"] = metrics.get("avg_problem_solving", 0.5)
                capabilities["technical_skills"] = metrics.get("avg_completion_rate", 0.5)

            if "coherence_benchmarks" in advanced_tests and hasattr(advanced_tests["coherence_benchmarks"], 'metrics'):
                metrics = advanced_tests["coherence_benchmarks"].metrics
                capabilities["communication"] = metrics.get("overall_consistency", 0.5)

            if "multi_tool_interactions" in advanced_tests and hasattr(advanced_tests["multi_tool_interactions"], 'metrics'):
                metrics = advanced_tests["multi_tool_interactions"].metrics
                capabilities["collaboration"] = metrics.get("avg_tool_coordination", 0.5)

        if "human_evaluation" in test_results and isinstance(test_results["human_evaluation"], dict):
            human_eval = test_results["human_evaluation"]

            # Extract capabilities from human evaluation
            for scenario, result in human_eval.items():
                if hasattr(result, 'growth_indicators'):
                    indicators = result.growth_indicators

                    if "communication_effectiveness" in indicators:
                        capabilities["communication"] = max(capabilities["communication"], indicators["communication_effectiveness"])

                    if "collaboration_readiness" in indicators:
                        capabilities["collaboration"] = max(capabilities["collaboration"], indicators["collaboration_readiness"])

                    if "ethical_grounding" in indicators:
                        capabilities["ethical_reasoning"] = max(capabilities["ethical_reasoning"], indicators["ethical_grounding"])

        return capabilities

    def _calculate_performance_indicators(self, test_results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate overall performance indicators"""
        indicators = {
            "consistency": 0.0,
            "reliability": 0.0,
            "adaptability": 0.0,
            "efficiency": 0.0,
            "robustness": 0.0
        }

        # Calculate consistency from test score variance
        scores = []
        if "advanced_tests" in test_results and isinstance(test_results["advanced_tests"], dict):
            for result in test_results["advanced_tests"].values():
                if hasattr(result, 'score'):
                    scores.append(result.score)

        if "human_evaluation" in test_results and isinstance(test_results["human_evaluation"], dict):
            for result in test_results["human_evaluation"].values():
                if hasattr(result, 'hybrid_score'):
                    scores.append(result.hybrid_score)

        if len(scores) > 1:
            variance = statistics.stdev(scores)
            indicators["consistency"] = max(0, 1.0 - variance)  # Lower variance = higher consistency
        elif len(scores) == 1:
            indicators["consistency"] = scores[0]

        # Calculate reliability (system performance success)
        if "system_performance" in test_results:
            sys_perf = test_results["system_performance"]
            if isinstance(sys_perf, dict) and sys_perf.get("success"):
                indicators["reliability"] = 0.95
            else:
                indicators["reliability"] = 0.4

        # Calculate adaptability from learning velocity
        indicators["adaptability"] = self._calculate_learning_velocity(test_results)

        # Calculate efficiency from execution times
        execution_times = []
        if "advanced_tests" in test_results and isinstance(test_results["advanced_tests"], dict):
            for result in test_results["advanced_tests"].values():
                if hasattr(result, 'execution_time'):
                    execution_times.append(result.execution_time)

        if execution_times:
            # Normalize efficiency (lower times = higher efficiency)
            avg_time = statistics.mean(execution_times)
            indicators["efficiency"] = max(0, 1.0 - (avg_time / 300))  # Normalize to 5 minutes max

        # Calculate robustness (error handling and recovery)
        error_count = 0
        total_tests = 0

        for test_suite in test_results.values():
            if isinstance(test_suite, dict):
                total_tests += 1
                if "error" in test_suite:
                    error_count += 1

        if total_tests > 0:
            indicators["robustness"] = 1.0 - (error_count / total_tests)

        return indicators

    def _calculate_learning_velocity(self, test_results: Dict[str, Any]) -> float:
        """Calculate learning velocity from test results"""
        learning_indicators = []

        # Extract learning-related metrics
        if "advanced_tests" in test_results and isinstance(test_results["advanced_tests"], dict):
            advanced_tests = test_results["advanced_tests"]

            if "evolutionary_learning" in advanced_tests and hasattr(advanced_tests["evolutionary_learning"], 'metrics'):
                metrics = advanced_tests["evolutionary_learning"].metrics
                learning_indicators.append(metrics.get("avg_learning_velocity", 0.5))

            if "adaptive_learning" in advanced_tests and hasattr(advanced_tests["adaptive_learning"], 'metrics'):
                metrics = advanced_tests["adaptive_learning"].metrics
                learning_indicators.append(metrics.get("avg_learning_velocity", 0.5))

        if "human_evaluation" in test_results and isinstance(test_results["human_evaluation"], dict):
            human_eval = test_results["human_evaluation"]
            for result in human_eval.values():
                if hasattr(result, 'growth_indicators'):
                    indicators = result.growth_indicators
                    if "learning_potential" in indicators:
                        learning_indicators.append(indicators["learning_potential"])

        return statistics.mean(learning_indicators) if learning_indicators else 0.5

    def _calculate_memory_effectiveness(self, test_results: Dict[str, Any]) -> float:
        """Calculate memory effectiveness from test results"""
        memory_indicators = []

        # Extract memory-related metrics
        if "advanced_tests" in test_results and isinstance(test_results["advanced_tests"], dict):
            advanced_tests = test_results["advanced_tests"]

            if "locomo_test" in advanced_tests and hasattr(advanced_tests["locomo_test"], 'metrics'):
                metrics = advanced_tests["locomo_test"].metrics
                memory_indicators.append(metrics.get("cross_session_recall", 0.5))
                memory_indicators.append(metrics.get("preference_retention", 0.5))
                memory_indicators.append(metrics.get("knowledge_accumulation", 0.5))

        # If no specific memory tests, use overall score as proxy
        if not memory_indicators:
            if "advanced_tests" in test_results and isinstance(test_results["advanced_tests"], dict):
                for result in test_results["advanced_tests"].values():
                    if hasattr(result, 'score'):
                        memory_indicators.append(result.score * 0.8)  # Assume 80% memory contribution

        return statistics.mean(memory_indicators) if memory_indicators else 0.5

    def _calculate_tool_coordination(self, test_results: Dict[str, Any]) -> float:
        """Calculate tool coordination effectiveness"""
        tool_indicators = []

        # Extract tool coordination metrics
        if "advanced_tests" in test_results and isinstance(test_results["advanced_tests"], dict):
            advanced_tests = test_results["advanced_tests"]

            if "multi_tool_interactions" in advanced_tests and hasattr(advanced_tests["multi_tool_interactions"], 'metrics'):
                metrics = advanced_tests["multi_tool_interactions"].metrics
                tool_indicators.append(metrics.get("avg_tool_coordination", 0.5))
                tool_indicators.append(metrics.get("avg_workflow_continuity", 0.5))

        return statistics.mean(tool_indicators) if tool_indicators else 0.5

    async def _analyze_growth_trends(self, current_metrics: GrowthMetricsSnapshot) -> List[GrowthAlert]:
        """Analyze trends and generate alerts"""
        alerts = []

        # Check overall score thresholds
        overall_thresholds = self.monitoring_config["alert_thresholds"]["overall_score"]
        if current_metrics.overall_score < overall_thresholds["critical"]:
            alerts.append(GrowthAlert(
                alert_id=f"overall_critical_{int(time.time())}",
                timestamp=current_metrics.timestamp,
                priority=AlertPriority.CRITICAL,
                metric_name="overall_score",
                current_value=current_metrics.overall_score,
                threshold_value=overall_thresholds["critical"],
                trend_direction="declining" if current_metrics.growth_trend < 0 else "stable",
                description=f"Overall score ({current_metrics.overall_score:.1%}) is below critical threshold ({overall_thresholds['critical']:.1%})",
                recommended_actions=[
                    "Immediate intervention required",
                    "Comprehensive capability assessment needed",
                    "Intensive skill development program recommended"
                ]
            ))
        elif current_metrics.overall_score < overall_thresholds["warning"]:
            alerts.append(GrowthAlert(
                alert_id=f"overall_warning_{int(time.time())}",
                timestamp=current_metrics.timestamp,
                priority=AlertPriority.HIGH,
                metric_name="overall_score",
                current_value=current_metrics.overall_score,
                threshold_value=overall_thresholds["warning"],
                trend_direction="declining" if current_metrics.growth_trend < -0.1 else "stable",
                description=f"Overall score ({current_metrics.overall_score:.1%}) is below warning threshold ({overall_thresholds['warning']:.1%})",
                recommended_actions=[
                    "Monitor closely for improvement",
                    "Identify specific areas needing attention",
                    "Consider targeted skill development"
                ]
            ))

        # Check learning velocity
        learning_thresholds = self.monitoring_config["alert_thresholds"]["learning_velocity"]
        if current_metrics.learning_velocity < learning_thresholds["critical"]:
            alerts.append(GrowthAlert(
                alert_id=f"learning_critical_{int(time.time())}",
                timestamp=current_metrics.timestamp,
                priority=AlertPriority.HIGH,
                metric_name="learning_velocity",
                current_value=current_metrics.learning_velocity,
                threshold_value=learning_thresholds["critical"],
                trend_direction="declining",
                description=f"Learning velocity ({current_metrics.learning_velocity:.3f}) is critically low",
                recommended_actions=[
                    "Review learning mechanisms and feedback integration",
                    "Enhance adaptive learning capabilities",
                    "Implement more aggressive learning strategies"
                ]
            ))

        # Check memory effectiveness
        memory_thresholds = self.monitoring_config["alert_thresholds"]["memory_effectiveness"]
        if current_metrics.memory_effectiveness < memory_thresholds["warning"]:
            alerts.append(GrowthAlert(
                alert_id=f"memory_warning_{int(time.time())}",
                timestamp=current_metrics.timestamp,
                priority=AlertPriority.MEDIUM,
                metric_name="memory_effectiveness",
                current_value=current_metrics.memory_effectiveness,
                threshold_value=memory_thresholds["warning"],
                trend_direction="declining" if current_metrics.growth_trend < 0 else "stable",
                description=f"Memory effectiveness ({current_metrics.memory_effectiveness:.1%}) needs improvement",
                recommended_actions=[
                    "Review memory integration mechanisms",
                    "Enhance cross-session memory retrieval",
                    "Improve knowledge consolidation processes"
                ]
            ))

        # Check for negative growth trend
        if current_metrics.growth_trend < -0.2:
            alerts.append(GrowthAlert(
                alert_id=f"trend_declining_{int(time.time())}",
                timestamp=current_metrics.timestamp,
                priority=AlertPriority.HIGH,
                metric_name="growth_trend",
                current_value=current_metrics.growth_trend,
                threshold_value=-0.2,
                trend_direction="declining",
                description=f"Negative growth trend detected ({current_metrics.growth_trend:.3f})",
                recommended_actions=[
                    "Investigate causes of performance decline",
                    "Review recent changes and interventions",
                    "Implement recovery strategies"
                ]
            ))

        # Store alerts
        self.alerts.extend(alerts)

        # Keep only last 50 alerts
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]

        return alerts

    async def _generate_growth_projections(self, current_metrics: GrowthMetricsSnapshot) -> List[GrowthProjection]:
        """Generate growth projections based on current trends"""
        projections = []

        # Current trend projection
        if len(self.metrics_history) >= 3:
            # Simple linear projection
            recent_scores = [s.overall_score for s in self.metrics_history[-5:]]
            if len(recent_scores) >= 2:
                # Calculate trend
                x = list(range(len(recent_scores)))
                slope = (recent_scores[-1] - recent_scores[0]) / len(recent_scores) if len(recent_scores) > 1 else 0

                # Project 30 days forward
                future_score = min(max(current_metrics.overall_score + (slope * 30), 0.0), 1.0)

                # Calculate confidence interval (simplified)
                variance = statistics.variance(recent_scores) if len(recent_scores) > 1 else 0.01
                std_dev = variance ** 0.5
                confidence_interval = (
                    max(0.0, future_score - (1.96 * std_dev)),
                    min(1.0, future_score + (1.96 * std_dev))
                )

                # Identify key growth areas
                capabilities = current_metrics.capabilities_assessment
                low_capabilities = [(cap, score) for cap, score in capabilities.items() if score < 0.7]
                key_growth_areas = [cap for cap, _ in sorted(low_capabilities, key=lambda x: x[1])[:3]]

                # Identify potential blockers
                potential_blockers = []
                if current_metrics.learning_velocity < 0.3:
                    potential_blockers.append("Low learning velocity")
                if current_metrics.memory_effectiveness < 0.7:
                    potential_blockers.append("Inadequate memory integration")
                if current_metrics.growth_trend < -0.1:
                    potential_blockers.append("Negative growth trend")

                projections.append(GrowthProjection(
                    projection_date=(datetime.now() + timedelta(days=30)).isoformat(),
                    projected_score=future_score,
                    confidence_interval=confidence_interval,
                    key_growth_areas=key_growth_areas,
                    potential_blockers=potential_blockers
                ))

        # Target achievement projection
        if current_metrics.overall_score < self.monitoring_config["target_score"]:
            # Estimate time to reach target
            target_diff = self.monitoring_config["target_score"] - current_metrics.overall_score
            if current_metrics.growth_trend > 0:
                days_to_target = int(target_diff / max(current_metrics.growth_trend, 0.01))
                target_date = datetime.now() + timedelta(days=days_to_target)

                projections.append(GrowthProjection(
                    projection_date=target_date.isoformat(),
                    projected_score=self.monitoring_config["target_score"],
                    confidence_interval=(self.monitoring_config["target_score"] * 0.9, 1.0),
                    key_growth_areas=["Overall capability development"],
                    potential_blockers=["Insufficient growth velocity"] if current_metrics.growth_trend < 0.1 else []
                ))

        # Store projections
        self.projections.extend(projections)

        # Keep only last 10 projections
        if len(self.projections) > 10:
            self.projections = self.projections[-10:]

        return projections

    async def _create_dashboard_report(self, current_metrics: GrowthMetricsSnapshot, alerts: List[GrowthAlert], projections: List[GrowthProjection]) -> Dict[str, Any]:
        """Create comprehensive dashboard report"""

        # Determine overall status
        overall_status = self._determine_overall_status(current_metrics)

        # Calculate key metrics
        key_metrics = {
            "overall_score": current_metrics.overall_score,
            "growth_trend": current_metrics.growth_trend,
            "learning_velocity": current_metrics.learning_velocity,
            "memory_effectiveness": current_metrics.memory_effectiveness,
            "tool_coordination": current_metrics.tool_coordination
        }

        # Get top capabilities and areas for improvement
        capabilities = current_metrics.capabilities_assessment
        top_capabilities = sorted(capabilities.items(), key=lambda x: x[1], reverse=True)[:3]
        improvement_areas = sorted(capabilities.items(), key=lambda x: x[1])[:3]

        # Get recent alerts summary
        recent_alerts = [alert for alert in alerts if datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')) > datetime.now() - timedelta(hours=24)]
        critical_alerts = [alert for alert in recent_alerts if alert.priority == AlertPriority.CRITICAL]

        # Performance indicators summary
        performance_summary = {
            "consistency": current_metrics.performance_indicators.get("consistency", 0.5),
            "reliability": current_metrics.performance_indicators.get("reliability", 0.5),
            "adaptability": current_metrics.performance_indicators.get("adaptability", 0.5),
            "efficiency": current_metrics.performance_indicators.get("efficiency", 0.5),
            "robustness": current_metrics.performance_indicators.get("robustness", 0.5)
        }

        return {
            "dashboard_id": self.dashboard_id,
            "report_date": datetime.now().isoformat(),
            "overall_status": overall_status.value,
            "key_metrics": key_metrics,
            "current_capabilities": dict(capabilities),
            "top_capabilities": dict(top_capabilities),
            "improvement_areas": dict(improvement_areas),
            "performance_indicators": performance_summary,
            "alerts_summary": {
                "total_alerts": len(recent_alerts),
                "critical_alerts": len(critical_alerts),
                "high_priority_alerts": len([a for a in recent_alerts if a.priority == AlertPriority.HIGH]),
                "recent_alerts": [asdict(alert) for alert in recent_alerts[:5]]
            },
            "growth_projections": [asdict(projection) for projection in projections[:3]],
            "historical_trend": {
                "data_points": len(self.metrics_history),
                "trend_direction": "improving" if current_metrics.growth_trend > 0.1 else "declining" if current_metrics.growth_trend < -0.1 else "stable",
                "average_score": statistics.mean([s.overall_score for s in self.metrics_history]) if self.metrics_history else current_metrics.overall_score
            },
            "recommendations": self._generate_dashboard_recommendations(current_metrics, alerts, projections)
        }

    def _determine_overall_status(self, current_metrics: GrowthMetricsSnapshot) -> GrowthStatus:
        """Determine overall growth status"""
        score = current_metrics.overall_score
        trend = current_metrics.growth_trend

        if score >= 0.9 and trend > 0:
            return GrowthStatus.EXCEPTIONAL
        elif score >= 0.8 and trend >= 0:
            return GrowthStatus.STRONG
        elif score >= 0.7 and trend >= -0.1:
            return GrowthStatus.COMPETENT
        elif score >= 0.6 and trend >= -0.2:
            return GrowthStatus.DEVELOPING
        elif score >= 0.4:
            return GrowthStatus.EMERGING
        else:
            return GrowthStatus.CONCERNING

    def _generate_dashboard_recommendations(self, current_metrics: GrowthMetricsSnapshot, alerts: List[GrowthAlert], projections: List[GrowthProjection]) -> List[str]:
        """Generate actionable recommendations based on dashboard analysis"""
        recommendations = []

        # Overall performance recommendations
        if current_metrics.overall_score < 0.7:
            recommendations.append("Focus on foundational capabilities to improve overall performance")
        elif current_metrics.overall_score >= 0.9:
            recommendations.append("Maintain excellence while pushing for advanced capabilities")

        # Learning and adaptation recommendations
        if current_metrics.learning_velocity < 0.3:
            recommendations.append("Enhance learning mechanisms through better feedback integration")

        # Memory effectiveness recommendations
        if current_metrics.memory_effectiveness < 0.7:
            recommendations.append("Improve memory integration and cross-session information retention")

        # Capability-specific recommendations
        capabilities = current_metrics.capabilities_assessment
        low_capabilities = [(cap, score) for cap, score in capabilities.items() if score < 0.6]
        if low_capabilities:
            top_priority = sorted(low_capabilities, key=lambda x: x[1])[0]
            recommendations.append(f"Priority development area: {top_priority[0].replace('_', ' ').title()}")

        # Trend-based recommendations
        if current_metrics.growth_trend < -0.1:
            recommendations.append("Investigate and address causes of performance decline")
        elif current_metrics.growth_trend > 0.2:
            recommendations.append("Leverage positive growth momentum for accelerated development")

        # Alert-based recommendations
        critical_alerts = [alert for alert in alerts if alert.priority == AlertPriority.CRITICAL]
        if critical_alerts:
            recommendations.append("Address critical alerts immediately to prevent performance degradation")

        # Projection-based recommendations
        if projections:
            blockers = set()
            for projection in projections:
                blockers.update(projection.potential_blockers)

            if blockers:
                recommendations.append(f"Address potential growth blockers: {', '.join(blockers)}")

        return recommendations[:5]  # Return top 5 recommendations

    async def _save_monitoring_results(self, dashboard_report: Dict[str, Any]) -> None:
        """Save monitoring results to files"""

        # Save main dashboard report
        dashboard_file = f"E:/TORQ-CONSOLE/maxim_integration/growth_dashboard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(dashboard_file, "w") as f:
            json.dump(dashboard_report, f, indent=2)

        # Save metrics history
        history_file = "E:/TORQ-CONSOLE/maxim_integration/growth_metrics_history.json"
        history_data = {
            "last_updated": datetime.now().isoformat(),
            "total_snapshots": len(self.metrics_history),
            "metrics_history": [asdict(snapshot) for snapshot in self.metrics_history]
        }
        with open(history_file, "w") as f:
            json.dump(history_data, f, indent=2)

        # Save alerts
        alerts_file = "E:/TORQ-CONSOLE/maxim_integration/growth_alerts.json"
        alerts_data = {
            "last_updated": datetime.now().isoformat(),
            "total_alerts": len(self.alerts),
            "alerts": [asdict(alert) for alert in self.alerts]
        }
        with open(alerts_file, "w") as f:
            json.dump(alerts_data, f, indent=2)

        print(f"[OK] Dashboard report saved to: {dashboard_file}")
        print(f"[OK] Metrics history saved to: {history_file}")
        print(f"[OK] Alerts saved to: {alerts_file}")

    async def _generate_visualizations(self, current_metrics: GrowthMetricsSnapshot) -> None:
        """Generate visualizations for the dashboard"""
        try:
            # Create output directory
            output_dir = Path("E:/TORQ-CONSOLE/maxim_integration/visualizations")
            output_dir.mkdir(exist_ok=True)

            # Generate growth trend chart
            if len(self.metrics_history) >= 2:
                self._create_growth_trend_chart(output_dir)

            # Generate capabilities radar chart
            self._create_capabilities_radar_chart(current_metrics, output_dir)

            # Generate performance indicators chart
            self._create_performance_indicators_chart(current_metrics, output_dir)

            print(f"[OK] Visualizations saved to: {output_dir}")

        except Exception as e:
            self.logger.error(f"Failed to generate visualizations: {e}")
            print(f"[WARNING] Visualization generation failed: {e}")

    def _create_growth_trend_chart(self, output_dir: Path) -> None:
        """Create growth trend visualization"""
        plt.figure(figsize=(12, 6))

        # Extract data
        timestamps = [datetime.fromisoformat(s.timestamp.replace('Z', '+00:00')) for s in self.metrics_history]
        scores = [s.overall_score for s in self.metrics_history]

        # Create plot
        plt.plot(timestamps, scores, 'b-', linewidth=2, marker='o', markersize=4)
        plt.axhline(y=self.monitoring_config["target_score"], color='g', linestyle='--', alpha=0.7, label=f'Target ({self.monitoring_config["target_score"]:.1%})')
        plt.axhline(y=self.monitoring_config["warning_threshold"], color='orange', linestyle='--', alpha=0.7, label=f'Warning ({self.monitoring_config["warning_threshold"]:.1%})')
        plt.axhline(y=self.monitoring_config["critical_threshold"], color='r', linestyle='--', alpha=0.7, label=f'Critical ({self.monitoring_config["critical_threshold"]:.1%})')

        plt.title('Agent Growth Trend Over Time', fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Overall Score', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(timestamps)//10)))
        plt.gcf().autofmt_xdate()

        # Save chart
        chart_file = output_dir / f"growth_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.tight_layout()
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()

    def _create_capabilities_radar_chart(self, current_metrics: GrowthMetricsSnapshot, output_dir: Path) -> None:
        """Create capabilities radar chart"""
        capabilities = current_metrics.capabilities_assessment

        # Prepare data
        categories = list(capabilities.keys())
        values = list(capabilities.values())

        # Number of variables
        N = len(categories)

        # Compute angle for each axis
        angles = [n / float(N) * 2 * 3.14159 for n in range(N)]
        angles += angles[:1]  # Complete the circle

        values += values[:1]  # Complete the circle

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

        # Plot data
        ax.plot(angles, values, 'o-', linewidth=2, color='blue', alpha=0.7)
        ax.fill(angles, values, alpha=0.25, color='blue')

        # Add labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([cat.replace('_', ' ').title() for cat in categories])
        ax.set_ylim(0, 1)

        # Add grid
        ax.grid(True)

        plt.title('Agent Capabilities Assessment', fontsize=16, fontweight='bold', pad=20)

        # Save chart
        chart_file = output_dir / f"capabilities_radar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.tight_layout()
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()

    def _create_performance_indicators_chart(self, current_metrics: GrowthMetricsSnapshot, output_dir: Path) -> None:
        """Create performance indicators bar chart"""
        indicators = current_metrics.performance_indicators

        # Prepare data
        categories = list(indicators.keys())
        values = list(indicators.values())

        # Create color map based on performance
        colors = ['red' if v < 0.5 else 'orange' if v < 0.7 else 'green' for v in values]

        # Create plot
        plt.figure(figsize=(10, 6))
        bars = plt.bar(categories, values, color=colors, alpha=0.7, edgecolor='black', linewidth=1)

        # Add value labels on bars
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.1%}', ha='center', va='bottom', fontweight='bold')

        plt.title('Performance Indicators', fontsize=16, fontweight='bold')
        plt.xlabel('Performance Metrics', fontsize=12)
        plt.ylabel('Score', fontsize=12)
        plt.ylim(0, 1.1)
        plt.xticks(rotation=45, ha='right')

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='red', alpha=0.7, label='Poor (<50%)'),
            Patch(facecolor='orange', alpha=0.7, label='Fair (50-70%)'),
            Patch(facecolor='green', alpha=0.7, label='Good (>70%)')
        ]
        plt.legend(handles=legend_elements, loc='upper right')

        plt.grid(True, alpha=0.3, axis='y')

        # Save chart
        chart_file = output_dir / f"performance_indicators_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.tight_layout()
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()

async def run_growth_monitoring_dashboard():
    """Main function to run the growth monitoring dashboard"""
    print("=" * 80)
    print("AGENT GROWTH MONITORING DASHBOARD")
    print("=" * 80)
    print(f"Monitoring Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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

    # Run comprehensive monitoring
    print("\n2. Running Comprehensive Growth Monitoring...")
    print("-" * 50)

    dashboard = AgentGrowthMonitoringDashboard(agent)
    dashboard_report = await dashboard.run_comprehensive_growth_monitoring()

    # Display dashboard summary
    print("\n3. Dashboard Summary")
    print("-" * 50)

    print(f"Overall Status: {dashboard_report['overall_status'].upper()}")
    print(f"Overall Score: {dashboard_report['key_metrics']['overall_score']:.1%}")
    print(f"Growth Trend: {dashboard_report['historical_trend']['trend_direction']}")
    print(f"Learning Velocity: {dashboard_report['key_metrics']['learning_velocity']:.3f}")
    print(f"Memory Effectiveness: {dashboard_report['key_metrics']['memory_effectiveness']:.1%}")

    print(f"\nTop Capabilities:")
    for capability, score in dashboard_report['top_capabilities'].items():
        print(f"  {capability.replace('_', ' ').title()}: {score:.1%}")

    print(f"\nAreas for Improvement:")
    for area, score in dashboard_report['improvement_areas'].items():
        print(f"  {area.replace('_', ' ').title()}: {score:.1%}")

    if dashboard_report['alerts_summary']['critical_alerts'] > 0:
        print(f"\n⚠️  CRITICAL ALERTS: {dashboard_report['alerts_summary']['critical_alerts']}")
        for alert in dashboard_report['alerts_summary']['recent_alerts']:
            if alert['priority'] == 'critical':
                print(f"  • {alert['description']}")

    if dashboard_report['growth_projections']:
        print(f"\n📈 Growth Projections:")
        for projection in dashboard_report['growth_projections']:
            target_date = datetime.fromisoformat(projection['projection_date'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
            print(f"  • {target_date}: {projection['projected_score']:.1%} projected")

    print(f"\n📋 Key Recommendations:")
    for i, rec in enumerate(dashboard_report['recommendations'], 1):
        print(f"  {i}. {rec}")

    # Cleanup
    try:
        await agent.cleanup()
        print("\n[OK] Agent cleanup completed")
    except Exception as e:
        print(f"\n[WARNING] Cleanup failed: {e}")

    return dashboard_report['key_metrics']['overall_score'] >= 0.7

if __name__ == "__main__":
    asyncio.run(run_growth_monitoring_dashboard())