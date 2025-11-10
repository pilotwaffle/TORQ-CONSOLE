"""
Maxim AI Integration - Phase 2: Experiment Tracking and Comparison Tools
Comprehensive experiment tracking, analysis, and comparison system

This module implements advanced tracking capabilities:
- Cross-experiment performance comparison
- Trend analysis and insights
- Automated reporting and dashboards
- Performance metrics aggregation
- Experiment recommendation engine
"""

import asyncio
import json
import time
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime, timedelta
import statistics
import os
import numpy as np

from experiment_manager import ExperimentManager, ExperimentSummary, ExperimentStatus
from ab_testing_framework import ABTestingFramework, ABTestResult
from prompt_optimization_workflow import PromptOptimizationWorkflow, OptimizationWorkflow

class TrendDirection(Enum):
    """Trend direction indicators"""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"

class ComparisonMetric(Enum):
    """Metrics for experiment comparison"""
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    SUCCESS_RATE = "success_rate"
    EXECUTION_TIME = "execution_time"
    CONFIDENCE_SCORE = "confidence_score"
    ERROR_REDUCTION = "error_reduction"
    CONSISTENCY = "consistency"

@dataclass
class ExperimentTrend:
    """Trend analysis for experiments over time"""
    metric: str
    direction: TrendDirection
    trend_strength: float  # 0.0 to 1.0
    change_rate: float  # Change per unit time
    confidence: float  # Statistical confidence
    data_points: List[Tuple[datetime, float]]
    forecast: Optional[List[Tuple[datetime, float]]] = None

@dataclass
class ExperimentComparison:
    """Comparison between multiple experiments"""
    comparison_id: str
    name: str
    experiment_ids: List[str]
    comparison_metrics: Dict[str, Dict[str, float]]  # metric -> {experiment_id: value}
    ranking: List[Tuple[str, float]]  # (experiment_id, score) sorted by performance
    insights: List[str]
    recommendations: List[str]
    statistical_significance: Dict[str, float]
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class PerformanceDashboard:
    """Performance dashboard data"""
    dashboard_id: str
    title: str
    time_period: Tuple[datetime, datetime]
    key_metrics: Dict[str, Any]
    trend_analyses: Dict[str, ExperimentTrend]
    top_performers: Dict[str, List[Tuple[str, float]]]
    alerts: List[str]
    recommendations: List[str]
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class ExperimentInsight:
    """Insight generated from experiment analysis"""
    insight_id: str
    title: str
    description: str
    insight_type: str  # performance, trend, anomaly, recommendation
    confidence: float
    impact_level: str  # high, medium, low
    action_items: List[str]
    supporting_data: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)

class ExperimentTracker:
    """
    Advanced experiment tracking and comparison system
    """

    def __init__(self, experiment_manager: ExperimentManager,
                 ab_framework: ABTestingFramework,
                 workflow_system: PromptOptimizationWorkflow):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

        self.experiment_manager = experiment_manager
        self.ab_framework = ab_framework
        self.workflow_system = workflow_system

        # Data storage
        self.experiment_comparisons: Dict[str, ExperimentComparison] = {}
        self.performance_dashboards: Dict[str, PerformanceDashboard] = {}
        self.experiment_insights: List[ExperimentInsight] = []
        self.trend_analyses: Dict[str, Dict[str, ExperimentTrend]] = {}

        # Configuration
        self.tracking_dir = "E:/TORQ-CONSOLE/experiment_tracking"
        self.dashboards_dir = f"{self.tracking_dir}/dashboards"
        self.reports_dir = f"{self.tracking_dir}/reports"

        # Initialize directories
        self._initialize_directories()

        self.logger.info("Experiment Tracker initialized")

    def setup_logging(self):
        """Setup logging for experiment tracker"""
        os.makedirs("E:/TORQ-CONSOLE/logs", exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('E:/TORQ-CONSOLE/logs/experiment_tracking.log'),
                logging.StreamHandler()
            ]
        )

    def _initialize_directories(self):
        """Initialize required directories"""
        directories = [
            self.tracking_dir,
            self.dashboards_dir,
            self.reports_dir,
            f"{self.tracking_dir}/analytics",
            f"{self.tracking_dir}/insights"
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    async def create_cross_experiment_comparison(self, name: str, experiment_ids: List[str],
                                              comparison_metrics: List[str]) -> str:
        """
        Create comparison between multiple experiments

        Args:
            name: Comparison name
            experiment_ids: List of experiment IDs to compare
            comparison_metrics: List of metrics to compare

        Returns:
            Comparison ID
        """
        comparison_id = str(uuid.uuid4())

        # Collect experiment data
        experiment_data = {}
        for exp_id in experiment_ids:
            # Try to get data from different sources
            exp_summary = self.experiment_manager.get_experiment_summary(exp_id)
            if exp_summary:
                experiment_data[exp_id] = {
                    "type": "prompt_optimization",
                    "summary": exp_summary
                }
            else:
                ab_result = self.ab_framework.test_results.get(exp_id)
                if ab_result:
                    experiment_data[exp_id] = {
                        "type": "ab_test",
                        "result": ab_result
                    }

        # Calculate comparison metrics
        comparison_data = {}
        for metric in comparison_metrics:
            comparison_data[metric] = {}
            for exp_id, data in experiment_data.items():
                value = self._extract_metric_value(data, metric)
                if value is not None:
                    comparison_data[metric][exp_id] = value

        # Rank experiments
        rankings = {}
        for metric, values in comparison_data.items():
            ranking = sorted(values.items(), key=lambda x: x[1], reverse=True)
            rankings[metric] = ranking

        # Generate insights
        insights = await self._generate_comparison_insights(comparison_data, experiment_data)

        # Generate recommendations
        recommendations = await self._generate_comparison_recommendations(comparison_data, insights)

        # Calculate statistical significance (simplified)
        statistical_significance = {}
        for metric, values in comparison_data.items():
            if len(values) >= 2:
                values_list = list(values.values())
                if len(values_list) >= 2:
                    # Mock significance calculation
                    variance = statistics.variance(values_list) if len(values_list) > 1 else 0
                    statistical_significance[metric] = min(0.99, 1.0 - variance)

        # Create comparison
        comparison = ExperimentComparison(
            comparison_id=comparison_id,
            name=name,
            experiment_ids=experiment_ids,
            comparison_metrics=comparison_data,
            ranking=rankings.get(comparison_metrics[0] if comparison_metrics else "overall_quality_score", []),
            insights=insights,
            recommendations=recommendations,
            statistical_significance=statistical_significance
        )

        self.experiment_comparisons[comparison_id] = comparison
        await self._save_comparison(comparison)

        self.logger.info(f"Created cross-experiment comparison: {comparison_id}")
        return comparison_id

    def _extract_metric_value(self, experiment_data: Dict, metric: str) -> Optional[float]:
        """Extract metric value from experiment data"""
        data_type = experiment_data.get("type")

        if data_type == "prompt_optimization":
            summary = experiment_data.get("summary")
            if summary:
                # Extract from experiment summary
                if metric == "performance_improvement":
                    return summary.overall_quality_score
                elif metric == "success_rate":
                    return summary.success_rate
                elif metric == "execution_time":
                    return summary.average_execution_time
                elif metric == "confidence_score":
                    return summary.average_confidence

        elif data_type == "ab_test":
            result = experiment_data.get("result")
            if result:
                # Extract from A/B test result
                if metric == "performance_improvement":
                    # Get best variant's performance
                    if result.winning_variant and result.variant_performances:
                        best_perf = result.variant_performances.get(result.winning_variant)
                        if best_perf:
                            return best_perf.metrics.get("success_rate", 0.0)
                elif metric == "success_rate":
                    if result.variant_performances:
                        # Average success rate across variants
                        rates = [vp.metrics.get("success_rate", 0) for vp in result.variant_performances.values()]
                        return statistics.mean(rates) if rates else 0.0

        return None

    async def _generate_comparison_insights(self, comparison_data: Dict[str, Dict[str, float]],
                                        experiment_data: Dict) -> List[str]:
        """Generate insights from comparison data"""
        insights = []

        # Performance insights
        for metric, values in comparison_data.items():
            if len(values) >= 2:
                max_val = max(values.values())
                min_val = min(values.values())
                range_val = max_val - min_val

                if range_val > 0.1:  # 10% range threshold
                    best_exp = max(values.items(), key=lambda x: x[1])
                    worst_exp = min(values.items(), key=lambda x: x[1])
                    insights.append(
                        f"Significant performance variation in {metric}: "
                        f"{best_exp[0]} ({best_exp[1]:.1%}) vs {worst_exp[0]} ({worst_exp[1]:.1%})"
                    )

        # Type-based insights
        prompt_opt_exps = [eid for eid, data in experiment_data.items() if data.get("type") == "prompt_optimization"]
        ab_test_exps = [eid for eid, data in experiment_data.items() if data.get("type") == "ab_test"]

        if prompt_opt_exps and ab_test_exps:
            insights.append(f"Comparison includes {len(prompt_opt_exps)} prompt optimization and {len(ab_test_exps)} A/B tests")

        return insights

    async def _generate_comparison_recommendations(self, comparison_data: Dict[str, Dict[str, float]],
                                                insights: List[str]) -> List[str]:
        """Generate recommendations from comparison"""
        recommendations = []

        # Performance-based recommendations
        for metric, values in comparison_data.items():
            if values:
                best_exp = max(values.items(), key=lambda x: x[1])
                recommendations.append(f"Deploy {best_exp[0]} for optimal {metric} performance")

        # Consistency recommendations
        all_values = []
        for values in comparison_data.values():
            all_values.extend(values.values())

        if all_values:
            variance = statistics.variance(all_values)
            if variance > 0.01:  # High variance
                recommendations.append("Consider standardizing approaches to reduce performance variance")

        if not recommendations:
            recommendations.append("Continue testing with different optimization strategies")

        return recommendations

    async def analyze_performance_trends(self, agent_type: Optional[str] = None,
                                       time_period_days: int = 30) -> Dict[str, ExperimentTrend]:
        """Analyze performance trends over time"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_period_days)

        # Collect historical data
        historical_data = self._collect_historical_data(start_date, end_date, agent_type)

        trends = {}
        for metric, data_points in historical_data.items():
            if len(data_points) >= 3:  # Need at least 3 points for trend analysis
                trend = self._calculate_trend(data_points, metric)
                trends[metric] = trend

        # Store trends
        self.trend_analyses[f"{agent_type or 'all'}_{time_period_days}d"] = trends

        return trends

    def _collect_historical_data(self, start_date: datetime, end_date: datetime,
                               agent_type: Optional[str]) -> Dict[str, List[Tuple[datetime, float]]]:
        """Collect historical experiment data"""
        historical_data = {
            "performance_improvement": [],
            "success_rate": [],
            "execution_time": [],
            "confidence_score": []
        }

        # Collect from experiment manager results
        for summary in self.experiment_manager.results.values():
            if (summary.evaluation_timestamp >= start_date and
                summary.evaluation_timestamp <= end_date):

                # Filter by agent type if specified
                if agent_type:
                    # This is simplified - in real implementation would filter properly
                    pass

                historical_data["performance_improvement"].append(
                    (summary.evaluation_timestamp, summary.overall_quality_score)
                )
                historical_data["success_rate"].append(
                    (summary.evaluation_timestamp, summary.success_rate)
                )
                historical_data["execution_time"].append(
                    (summary.evaluation_timestamp, summary.average_execution_time)
                )
                historical_data["confidence_score"].append(
                    (summary.evaluation_timestamp, summary.average_confidence)
                )

        # Sort data points by timestamp
        for metric in historical_data:
            historical_data[metric].sort(key=lambda x: x[0])

        return historical_data

    def _calculate_trend(self, data_points: List[Tuple[datetime, float]], metric: str) -> ExperimentTrend:
        """Calculate trend from data points"""
        if len(data_points) < 3:
            return ExperimentTrend(
                metric=metric,
                direction=TrendDirection.STABLE,
                trend_strength=0.0,
                change_rate=0.0,
                confidence=0.0,
                data_points=data_points
            )

        # Extract values and timestamps
        timestamps = [int((tp[0] - data_points[0][0]).total_seconds()) for tp, _ in data_points]
        values = [tp[1] for tp in data_points]

        # Calculate linear regression
        if len(timestamps) >= 2:
            # Simple linear regression
            n = len(timestamps)
            sum_x = sum(timestamps)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(timestamps, values))
            sum_x2 = sum(x * x for x in timestamps)

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n

            # Calculate trend direction and strength
            if abs(slope) < 0.0001:
                direction = TrendDirection.STABLE
                trend_strength = 1.0 - statistics.stdev(values) if len(values) > 1 else 1.0
            elif slope > 0:
                direction = TrendDirection.IMPROVING
                trend_strength = min(1.0, slope * 1000)  # Scale slope to strength
            else:
                direction = TrendDirection.DECLINING
                trend_strength = min(1.0, abs(slope) * 1000)

            # Calculate confidence based on R-squared
            y_mean = statistics.mean(values)
            ss_tot = sum((y - y_mean) ** 2 for y in values)
            ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(timestamps, values))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            confidence = max(0.0, r_squared)

            # Check for volatility
            if len(values) >= 3:
                recent_values = values[-3:]
                volatility = statistics.stdev(recent_values) / statistics.mean(recent_values) if statistics.mean(recent_values) > 0 else 0
                if volatility > 0.2:
                    direction = TrendDirection.VOLATILE

            # Generate simple forecast
            forecast = []
            if len(data_points) >= 2:
                last_timestamp = timestamps[-1]
                for i in range(1, 4):  # Forecast 3 future points
                    future_timestamp = last_timestamp + (i * 86400)  # 1 day intervals
                    future_value = slope * future_timestamp + intercept
                    forecast.append((data_points[0][0] + timedelta(seconds=future_timestamp), future_value))

            return ExperimentTrend(
                metric=metric,
                direction=direction,
                trend_strength=min(1.0, max(0.0, trend_strength)),
                change_rate=slope,
                confidence=confidence,
                data_points=data_points,
                forecast=forecast
            )

        return ExperimentTrend(
            metric=metric,
            direction=TrendDirection.STABLE,
            trend_strength=0.0,
            change_rate=0.0,
            confidence=0.0,
            data_points=data_points
        )

    async def generate_performance_dashboard(self, title: str, time_period_days: int = 30) -> str:
        """Generate performance dashboard"""
        dashboard_id = str(uuid.uuid4())

        # Get trend analyses
        trends = await self.analyze_performance_trends(time_period_days=time_period_days)

        # Calculate key metrics
        key_metrics = self._calculate_key_metrics()

        # Identify top performers
        top_performers = self._identify_top_performers()

        # Generate alerts
        alerts = self._generate_alerts(trends)

        # Generate recommendations
        recommendations = self._generate_dashboard_recommendations(key_metrics, trends, alerts)

        dashboard = PerformanceDashboard(
            dashboard_id=dashboard_id,
            title=title,
            time_period=(datetime.now() - timedelta(days=time_period_days), datetime.now()),
            key_metrics=key_metrics,
            trend_analyses=trends,
            top_performers=top_performers,
            alerts=alerts,
            recommendations=recommendations
        )

        self.performance_dashboards[dashboard_id] = dashboard
        await self._save_dashboard(dashboard)

        return dashboard_id

    def _calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate key performance metrics"""
        metrics = {
            "total_experiments": len(self.experiment_manager.experiments),
            "completed_experiments": len(self.experiment_manager.results),
            "average_improvement": 0.0,
            "success_rate": 0.0,
            "most_tested_agent": "unknown",
            "best_performing_strategy": "unknown"
        }

        # Calculate average improvement
        if self.experiment_manager.results:
            improvements = []
            for summary in self.experiment_manager.results.values():
                if summary.winning_variant and summary.winning_variant != "Control":
                    primary_metric = "overall_quality_score"
                    for variant, improvement in summary.improvement_percentages.items():
                        if variant == summary.winning_variant and primary_metric in improvement:
                            improvements.append(improvement[primary_metric])
                            break

            if improvements:
                metrics["average_improvement"] = statistics.mean(improvements)

        # Calculate success rate
        if metrics["total_experiments"] > 0:
            metrics["success_rate"] = metrics["completed_experiments"] / metrics["total_experiments"]

        return metrics

    def _identify_top_performers(self) -> Dict[str, List[Tuple[str, float]]]:
        """Identify top performing experiments and variants"""
        top_performers = {
            "experiments": [],
            "variants": [],
            "strategies": []
        }

        # Top experiments by improvement
        experiment_scores = []
        for exp_id, summary in self.experiment_manager.results.items():
            if summary.winning_variant and summary.winning_variant != "Control":
                primary_metric = "overall_quality_score"
                for variant, improvement in summary.improvement_percentages.items():
                    if variant == summary.winning_variant and primary_metric in improvement:
                        experiment_scores.append((exp_id, improvement[primary_metric]))

        top_performers["experiments"] = sorted(experiment_scores, key=lambda x: x[1], reverse=True)[:5]

        return top_performers

    def _generate_alerts(self, trends: Dict[str, ExperimentTrend]) -> List[str]:
        """Generate alerts based on trend analysis"""
        alerts = []

        for metric, trend in trends.items():
            if trend.direction == TrendDirection.DECLINING and trend.confidence > 0.7:
                alerts.append(f"⚠️ Declining trend detected in {metric} ({trend.confidence:.1%} confidence)")
            elif trend.direction == TrendDirection.VOLATILE:
                alerts.append(f"📊 High volatility in {metric} - consider stabilization strategies")
            elif trend.trend_strength < 0.3:
                alerts.append(f"➡️ Low trend strength in {metric} - data may be too noisy")

        return alerts

    def _generate_dashboard_recommendations(self, key_metrics: Dict[str, Any],
                                           trends: Dict[str, ExperimentTrend],
                                           alerts: List[str]) -> List[str]:
        """Generate dashboard recommendations"""
        recommendations = []

        # Success rate recommendations
        if key_metrics["success_rate"] < 0.8:
            recommendations.append("Focus on improving experiment completion rates")
        elif key_metrics["success_rate"] > 0.9:
            recommendations.append("Excellent success rate - consider increasing experiment complexity")

        # Improvement recommendations
        if key_metrics["average_improvement"] < 0.05:
            recommendations.append("Experiment improvements are marginal - consider new optimization strategies")
        elif key_metrics["average_improvement"] > 0.15:
            recommendations.append("Strong improvements achieved - document and standardize successful approaches")

        # Trend-based recommendations
        declining_metrics = [metric for metric, trend in trends.items()
                           if trend.direction == TrendDirection.DECLINING]
        if declining_metrics:
            recommendations.append(f"Address declining trends in: {', '.join(declining_metrics)}")

        # Alert-based recommendations
        if alerts:
            recommendations.append("Review and address generated alerts")

        return recommendations

    async def generate_insights(self, analysis_type: str = "performance") -> List[ExperimentInsight]:
        """Generate insights from experiment data"""
        insights = []

        if analysis_type == "performance":
            # Performance insights
            insights.append(await self._generate_performance_insight())
        elif analysis_type == "trend":
            # Trend insights
            insights.extend(await self._generate_trend_insights())
        elif analysis_type == "anomaly":
            # Anomaly detection insights
            insights.extend(await self._generate_anomaly_insights())

        self.experiment_insights.extend(insights)
        await self._save_insights(insights)

        return insights

    async def _generate_performance_insight(self) -> ExperimentInsight:
        """Generate performance-related insight"""
        # Analyze best performing strategies
        strategy_performance = {}

        for summary in self.experiment_manager.results.values():
            strategy = "prompt_optimization"  # Simplified
            if summary.winning_variant and summary.winning_variant != "Control":
                if strategy not in strategy_performance:
                    strategy_performance[strategy] = []
                primary_metric = "overall_quality_score"
                for variant, improvement in summary.improvement_percentages.items():
                    if variant == summary.winning_variant and primary_metric in improvement:
                        strategy_performance[strategy].append(improvement[primary_metric])

        best_strategy = max(strategy_performance.items(), key=lambda x: statistics.mean(x[1])) if strategy_performance else ("unknown", [])

        return ExperimentInsight(
            insight_id=str(uuid.uuid4()),
            title="Optimization Strategy Performance Analysis",
            description=f"Best performing strategy: {best_strategy[0]} with average improvement of {statistics.mean(best_strategy[1]):.1%}" if best_strategy[1] else "No clear winning strategy identified",
            insight_type="performance",
            confidence=0.85,
            impact_level="high",
            action_items=[
                "Deploy best performing strategy more widely",
                "Analyze characteristics of successful experiments",
                "Document best practices for future experiments"
            ],
            supporting_data={
                "strategy_performance": strategy_performance,
                "total_experiments": len(self.experiment_manager.results)
            }
        )

    async def _generate_trend_insights(self) -> List[ExperimentInsight]:
        """Generate trend-related insights"""
        insights = []
        trends = await self.analyze_performance_trends()

        for metric, trend in trends.items():
            if trend.direction == TrendDirection.IMPROVING and trend.confidence > 0.8:
                insights.append(ExperimentInsight(
                    insight_id=str(uuid.uuid4()),
                    title=f"Positive Trend in {metric}",
                    description=f"Steady improvement detected in {metric} with {trend.confidence:.1%} confidence",
                    insight_type="trend",
                    confidence=trend.confidence,
                    impact_level="medium",
                    action_items=[
                        f"Continue current optimization approach for {metric}",
                        "Monitor trend sustainability",
                        "Consider expanding successful strategies"
                    ],
                    supporting_data={
                        "trend_direction": trend.direction.value,
                        "trend_strength": trend.trend_strength,
                        "change_rate": trend.change_rate
                    }
                ))

        return insights

    async def _generate_anomaly_insights(self) -> List[ExperimentInsight]:
        """Generate anomaly detection insights"""
        insights = []

        # Look for outlier experiments
        if self.experiment_manager.results:
            improvements = []
            for summary in self.experiment_manager.results.values():
                if summary.winning_variant and summary.winning_variant != "Control":
                    for variant, improvement in summary.improvement_percentages.items():
                        if variant == summary.winning_variant and "overall_quality_score" in improvement:
                            improvements.append(improvement["overall_quality_score"])

            if improvements:
                mean_improvement = statistics.mean(improvements)
                std_improvement = statistics.stdev(improvements) if len(improvements) > 1 else 0

                # Find outliers
                outliers = [imp for imp in improvements if abs(imp - mean_improvement) > 2 * std_improvement]

                if outliers:
                    insights.append(ExperimentInsight(
                        insight_id=str(uuid.uuid4()),
                        title="Outlier Performance Detected",
                        description=f"Found {len(outliers)} experiments with unusual performance (mean: {mean_improvement:.1%}, outliers: {outliers})",
                        insight_type="anomaly",
                        confidence=0.9,
                        impact_level="high",
                        action_items=[
                            "Investigate causes of outlier performance",
                            "Document successful outlier strategies",
                            "Consider replicating successful outlier approaches"
                        ],
                        supporting_data={
                            "mean_improvement": mean_improvement,
                            "std_improvement": std_improvement,
                            "outliers": outliers
                        }
                    ))

        return insights

    async def _save_comparison(self, comparison: ExperimentComparison):
        """Save comparison to file"""
        comparison_file = f"{self.tracking_dir}/comparisons/comparison_{comparison.comparison_id}.json"

        comparison_data = asdict(comparison)
        comparison_data["created_at"] = comparison.created_at.isoformat()

        with open(comparison_file, 'w') as f:
            json.dump(comparison_data, f, indent=2)

        self.logger.info(f"Comparison saved to: {comparison_file}")

    async def _save_dashboard(self, dashboard: PerformanceDashboard):
        """Save dashboard to file"""
        dashboard_file = f"{self.dashboards_dir}/dashboard_{dashboard.dashboard_id}.json"

        dashboard_data = asdict(dashboard)
        dashboard_data["time_period"] = (dashboard.time_period[0].isoformat(), dashboard.time_period[1].isoformat())
        dashboard_data["last_updated"] = dashboard.last_updated.isoformat()

        # Convert trend analyses
        for metric, trend in dashboard_data["trend_analyses"].items():
            trend["data_points"] = [(tp[0].isoformat(), tp[1]) for tp in trend["data_points"]]
            if trend["forecast"]:
                trend["forecast"] = [(tp[0].isoformat(), tp[1]) for tp in trend["forecast"]]

        with open(dashboard_file, 'w') as f:
            json.dump(dashboard_data, f, indent=2)

        self.logger.info(f"Dashboard saved to: {dashboard_file}")

    async def _save_insights(self, insights: List[ExperimentInsight]):
        """Save insights to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        insights_file = f"{self.tracking_dir}/insights/insights_{timestamp}.json"

        insights_data = []
        for insight in insights:
            insight_data = asdict(insight)
            insight_data["generated_at"] = insight.generated_at.isoformat()
            insights_data.append(insight_data)

        with open(insights_file, 'w') as f:
            json.dump(insights_data, f, indent=2)

        self.logger.info(f"Insights saved to: {insights_file}")

    def print_dashboard(self, dashboard_id: str):
        """Print formatted dashboard"""
        dashboard = self.performance_dashboards.get(dashboard_id)
        if not dashboard:
            print(f"Dashboard {dashboard_id} not found")
            return

        print(f"\n{'='*80}")
        print(f"PERFORMANCE DASHBOARD: {dashboard.title}")
        print(f"{'='*80}")
        print(f"Time Period: {dashboard.time_period[0].strftime('%Y-%m-%d')} to {dashboard.time_period[1].strftime('%Y-%m-%d')}")
        print(f"Last Updated: {dashboard.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"\nKEY METRICS:")
        for metric, value in dashboard.key_metrics.items():
            print(f"  {metric.replace('_', ' ').title()}: {value}")

        print(f"\nTREND ANALYSIS:")
        for metric, trend in dashboard.trend_analyses.items():
            direction_icon = {
                TrendDirection.IMPROVING: "📈",
                TrendDirection.DECLINING: "📉",
                TrendDirection.STABLE: "➡️",
                TrendDirection.VOLATILE: "📊"
            }.get(trend.direction, "❓")

            print(f"  {direction_icon} {metric}: {trend.direction.value} (confidence: {trend.confidence:.1%})")

        print(f"\nTOP PERFORMERS:")
        for category, performers in dashboard.top_performers.items():
            if performers:
                print(f"  {category.title()}:")
                for performer, score in performers[:3]:
                    print(f"    • {performer}: {score:.1%}")

        if dashboard.alerts:
            print(f"\nALERTS:")
            for alert in dashboard.alerts:
                print(f"  {alert}")

        if dashboard.recommendations:
            print(f"\nRECOMMENDATIONS:")
            for i, rec in enumerate(dashboard.recommendations, 1):
                print(f"  {i}. {rec}")

        print(f"{'='*80}")

    def print_insights(self, limit: int = 5):
        """Print recent insights"""
        if not self.experiment_insights:
            print("No insights available")
            return

        print(f"\n{'='*80}")
        print(f"RECENT EXPERIMENT INSIGHTS (Top {limit})")
        print(f"{'='*80}")

        # Sort by generated date (most recent)
        recent_insights = sorted(self.experiment_insights, key=lambda x: x.generated_at, reverse=True)[:limit]

        for insight in recent_insights:
            impact_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(insight.impact_level, "⚪")

            print(f"\n{impact_icon} {insight.title}")
            print(f"   Type: {insight.insight_type.title()} | Confidence: {insight.confidence:.1%}")
            print(f"   Description: {insight.description}")
            if insight.action_items:
                print(f"   Actions: {', '.join(insight.action_items[:2])}")

        print(f"{'='*80}")

# Main execution function for testing
async def main():
    """Main execution function for testing experiment tracker"""
    print("📊 Maxim AI - Phase 2: Experiment Tracking and Comparison Tools")
    print("=" * 70)

    # Initialize components
    experiment_manager = ExperimentManager()
    ab_framework = ABTestingFramework(experiment_manager)
    workflow_system = PromptOptimizationWorkflow(experiment_manager, VersionControlSystem())
    tracker = ExperimentTracker(experiment_manager, ab_framework, workflow_system)

    # Create cross-experiment comparison
    print("\n🔍 Creating cross-experiment comparison...")

    # Create some mock experiment data for comparison
    mock_experiment_ids = ["exp_001", "exp_002", "exp_003"]

    comparison_id = await tracker.create_cross_experiment_comparison(
        name="Q4 2024 Performance Comparison",
        experiment_ids=mock_experiment_ids,
        comparison_metrics=["performance_improvement", "success_rate", "execution_time"]
    )

    print(f"✅ Created comparison: {comparison_id}")

    # Generate performance dashboard
    print("\n📈 Generating performance dashboard...")
    dashboard_id = await tracker.generate_performance_dashboard(
        title="Prince Flowers Performance Overview",
        time_period_days=30
    )

    print(f"✅ Generated dashboard: {dashboard_id}")

    # Print dashboard
    tracker.print_dashboard(dashboard_id)

    # Generate insights
    print("\n💡 Generating experiment insights...")
    insights = await tracker.generate_insights("performance")

    print(f"✅ Generated {len(insights)} insights")

    # Print insights
    tracker.print_insights(3)

    print(f"\n✅ Experiment tracking and comparison tools demonstration completed!")

if __name__ == "__main__":
    import uuid
    import statistics
    asyncio.run(main())