"""
Learning engine for TORQ Prince Flowers agent.

This module provides continuous learning capabilities including:
- Experience replay
- Performance tracking
- Strategy adaptation
- User feedback integration
"""

import json
import logging
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict


class LearningEngine:
    """Continuous learning engine for agent improvement."""

    def __init__(self):
        """Initialize the learning engine."""
        self.logger = logging.getLogger("LearningEngine")

        # Learning data
        self.experience_buffer = []
        self.strategy_performance = defaultdict(list)
        self.user_feedback = []
        self.performance_metrics = []

        # Learning parameters
        self.learning_rate = 0.01
        self.exploration_rate = 0.15
        self.max_buffer_size = 1000

        # Performance tracking
        self.total_interactions = 0
        self.successful_interactions = 0
        self.avg_response_time = 0.0

        self.logger.info("Learning engine initialized")

    async def record_experience(self, trajectory, analysis: Dict[str, Any], success: bool):
        """Record an experience for learning."""
        try:
            experience = {
                "timestamp": time.time(),
                "query": trajectory.query,
                "mode": trajectory.mode.value,
                "success": success,
                "execution_time": trajectory.total_time,
                "tools_used": trajectory.context.get("tools_used", []),
                "confidence": getattr(trajectory, 'confidence_score', 0.0),
                "self_corrections": trajectory.self_corrections,
                "analysis": analysis
            }

            # Add to experience buffer
            self.experience_buffer.append(experience)

            # Maintain buffer size
            if len(self.experience_buffer) > self.max_buffer_size:
                self.experience_buffer.pop(0)

            # Update strategy performance
            strategy = trajectory.mode.value
            self.strategy_performance[strategy].append({
                "success": success,
                "execution_time": trajectory.total_time,
                "timestamp": time.time()
            })

            # Update metrics
            self.total_interactions += 1
            if success:
                self.successful_interactions += 1

            # Update average response time
            self.avg_response_time = (
                (self.avg_response_time * (self.total_interactions - 1) + trajectory.total_time) /
                self.total_interactions
            )

            self.logger.debug(f"Recorded experience: {trajectory.mode.value} - {'SUCCESS' if success else 'FAILURE'}")

        except Exception as e:
            self.logger.error(f"Error recording experience: {e}")

    async def update_learning_systems(self, trajectory, analysis: Dict[str, Any], success: bool):
        """Update all learning systems with new experience."""
        try:
            await self.record_experience(trajectory, analysis, success)
            await self._update_strategies()
            await self._update_performance_metrics()

        except Exception as e:
            self.logger.error(f"Error updating learning systems: {e}")

    async def _update_strategies(self):
        """Update strategy performance and adaptation."""
        try:
            # Analyze recent performance for each strategy
            for strategy, experiences in self.strategy_performance.items():
                if len(experiences) >= 10:  # Need minimum data for analysis
                    recent_experiences = experiences[-20:]  # Last 20 experiences
                    success_rate = sum(e["success"] for e in recent_experiences) / len(recent_experiences)
                    avg_time = sum(e["execution_time"] for e in recent_experiences) / len(recent_experiences)

                    # Update exploration/exploitation balance
                    if success_rate > 0.8:
                        # Reduce exploration for successful strategies
                        self.exploration_rate *= 0.95
                    elif success_rate < 0.5:
                        # Increase exploration for struggling strategies
                        self.exploration_rate = min(0.3, self.exploration_rate * 1.1)

                    self.logger.debug(f"Strategy {strategy}: {success_rate:.2f} success, {avg_time:.2f}s avg")

        except Exception as e:
            self.logger.error(f"Error updating strategies: {e}")

    async def _update_performance_metrics(self):
        """Update performance metrics tracking."""
        try:
            current_metrics = {
                "timestamp": time.time(),
                "total_interactions": self.total_interactions,
                "success_rate": self.successful_interactions / max(self.total_interactions, 1),
                "avg_response_time": self.avg_response_time,
                "exploration_rate": self.exploration_rate,
                "experience_buffer_size": len(self.experience_buffer)
            }

            self.performance_metrics.append(current_metrics)

            # Keep only last 100 metrics points
            if len(self.performance_metrics) > 100:
                self.performance_metrics.pop(0)

        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")

    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning data."""
        try:
            if not self.experience_buffer:
                return {"message": "No learning data available yet"}

            # Analyze recent performance
            recent_experiences = self.experience_buffer[-50:]  # Last 50 experiences
            recent_success_rate = sum(e["success"] for e in recent_experiences) / len(recent_experiences)

            # Best performing strategies
            strategy_stats = {}
            for strategy, experiences in self.strategy_performance.items():
                if experiences:
                    success_rate = sum(e["success"] for e in experiences[-20:]) / min(len(experiences), 20)
                    avg_time = sum(e["execution_time"] for e in experiences[-20:]) / min(len(experiences), 20)
                    strategy_stats[strategy] = {
                        "success_rate": success_rate,
                        "avg_time": avg_time,
                        "total_uses": len(experiences)
                    }

            return {
                "total_experiences": len(self.experience_buffer),
                "recent_success_rate": recent_success_rate,
                "overall_success_rate": self.successful_interactions / max(self.total_interactions, 1),
                "avg_response_time": self.avg_response_time,
                "exploration_rate": self.exploration_rate,
                "strategy_performance": strategy_stats,
                "learning_rate": self.learning_rate
            }

        except Exception as e:
            self.logger.error(f"Error getting learning insights: {e}")
            return {"error": str(e)}

    async def record_failure(self, failure_analysis: Dict[str, Any]):
        """Record a failure for analysis and learning."""
        try:
            failure_record = {
                "timestamp": time.time(),
                **failure_analysis
            }

            # Add to experience buffer with success=False
            self.experience_buffer.append({
                "timestamp": failure_record["timestamp"],
                "query": failure_record["query"],
                "mode": failure_record.get("mode", "unknown"),
                "success": False,
                "execution_time": failure_record.get("execution_time", 0.0),
                "error_type": failure_record.get("error_type"),
                "error_message": failure_record.get("error_message"),
                "analysis": failure_record
            })

            self.logger.info(f"Recorded failure analysis: {failure_record.get('error_type', 'Unknown')}")

        except Exception as e:
            self.logger.error(f"Error recording failure: {e}")

    def add_user_feedback(self, query: str, rating: float, comment: str = ""):
        """Add user feedback for learning."""
        try:
            feedback_record = {
                "timestamp": time.time(),
                "query": query,
                "rating": rating,
                "comment": comment
            }

            self.user_feedback.append(feedback_record)
            self.logger.info(f"Added user feedback: {rating}/5.0 for query: {query[:50]}...")

        except Exception as e:
            self.logger.error(f"Error adding user feedback: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current learning engine status."""
        return {
            "total_experiences": len(self.experience_buffer),
            "total_interactions": self.total_interactions,
            "success_rate": self.successful_interactions / max(self.total_interactions, 1),
            "avg_response_time": self.avg_response_time,
            "learning_rate": self.learning_rate,
            "exploration_rate": self.exploration_rate,
            "strategies_tracked": len(self.strategy_performance),
            "user_feedback_count": len(self.user_feedback)
        }

    def export_learning_data(self) -> Dict[str, Any]:
        """Export learning data for persistence."""
        try:
            return {
                "experience_buffer": self.experience_buffer[-100:],  # Last 100 experiences
                "strategy_performance": dict(self.strategy_performance),
                "user_feedback": self.user_feedback[-50:],  # Last 50 feedback entries
                "performance_metrics": self.performance_metrics[-20:],  # Last 20 metrics
                "learning_parameters": {
                    "learning_rate": self.learning_rate,
                    "exploration_rate": self.exploration_rate
                },
                "statistics": {
                    "total_interactions": self.total_interactions,
                    "successful_interactions": self.successful_interactions,
                    "avg_response_time": self.avg_response_time
                }
            }

        except Exception as e:
            self.logger.error(f"Error exporting learning data: {e}")
            return {}

    def import_learning_data(self, learning_data: Dict[str, Any]):
        """Import learning data from persistence."""
        try:
            if "experience_buffer" in learning_data:
                self.experience_buffer.extend(learning_data["experience_buffer"])

            if "strategy_performance" in learning_data:
                for strategy, experiences in learning_data["strategy_performance"].items():
                    self.strategy_performance[strategy].extend(experiences)

            if "user_feedback" in learning_data:
                self.user_feedback.extend(learning_data["user_feedback"])

            if "learning_parameters" in learning_data:
                params = learning_data["learning_parameters"]
                self.learning_rate = params.get("learning_rate", self.learning_rate)
                self.exploration_rate = params.get("exploration_rate", self.exploration_rate)

            if "statistics" in learning_data:
                stats = learning_data["statistics"]
                self.total_interactions = stats.get("total_interactions", self.total_interactions)
                self.successful_interactions = stats.get("successful_interactions", self.successful_interactions)
                self.avg_response_time = stats.get("avg_response_time", self.avg_response_time)

            self.logger.info("Learning data imported successfully")

        except Exception as e:
            self.logger.error(f"Error importing learning data: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the learning engine."""
        try:
            return {
                "healthy": True,
                "experience_buffer_size": len(self.experience_buffer),
                "learning_rate": self.learning_rate,
                "exploration_rate": self.exploration_rate,
                "components": {
                    "experience_recorder": True,
                    "strategy_updater": True,
                    "performance_tracker": True,
                    "feedback_processor": True
                }
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }