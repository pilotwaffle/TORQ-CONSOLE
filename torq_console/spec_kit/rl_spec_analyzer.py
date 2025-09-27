"""
RL-Powered Specification Analyzer for TORQ Console Spec-Kit Integration
Uses Enhanced RL System to analyze and optimize specifications
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import numpy as np

@dataclass
class SpecAnalysis:
    """Analysis result from RL-powered specification analysis"""
    clarity_score: float
    completeness_score: float
    feasibility_score: float
    complexity_score: float
    risk_assessment: Dict[str, float]
    recommendations: List[str]
    confidence: float

@dataclass
class SpecificationContext:
    """Context for specification analysis"""
    domain: str
    tech_stack: List[str]
    project_size: str  # small, medium, large, enterprise
    team_size: int
    timeline: str
    constraints: List[str]

class RLSpecAnalyzer:
    """RL-powered specification analyzer using Enhanced RL System"""

    def __init__(self, enhanced_rl_system=None):
        self.logger = logging.getLogger("TORQ.SpecKit.RLAnalyzer")
        self.enhanced_rl_system = enhanced_rl_system
        self.analysis_history = []
        self.spec_patterns = {}
        self.success_metrics = {}

        # Initialize RL components
        self._initialize_rl_components()

    def _initialize_rl_components(self):
        """Initialize RL-specific components for spec analysis"""
        try:
            # Import RL components if available
            if self.enhanced_rl_system:
                self.rl_agent = self.enhanced_rl_system.get_agent("spec_analyzer")
                self.logger.info("Initialized RL agent for spec analysis")
            else:
                self.logger.warning("No Enhanced RL System available, using heuristic analysis")
        except Exception as e:
            self.logger.error(f"Failed to initialize RL components: {e}")

    async def analyze_specification(self, spec_text: str, context: SpecificationContext) -> SpecAnalysis:
        """Analyze specification using RL-powered intelligence"""
        try:
            # Prepare specification for analysis
            spec_features = self._extract_spec_features(spec_text)
            context_features = self._extract_context_features(context)

            # Use RL analysis if available
            if self.enhanced_rl_system:
                analysis = await self._rl_analyze_spec(spec_features, context_features)
            else:
                analysis = await self._heuristic_analyze_spec(spec_features, context_features)

            # Store analysis for learning
            self.analysis_history.append({
                'spec_features': spec_features,
                'context': context,
                'analysis': analysis,
                'timestamp': asyncio.get_event_loop().time()
            })

            return analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze specification: {e}")
            # Return fallback analysis
            return SpecAnalysis(
                clarity_score=0.5,
                completeness_score=0.5,
                feasibility_score=0.5,
                complexity_score=0.5,
                risk_assessment={'unknown': 0.5},
                recommendations=['Unable to perform detailed analysis'],
                confidence=0.1
            )

    def _extract_spec_features(self, spec_text: str) -> Dict[str, float]:
        """Extract quantifiable features from specification text"""
        features = {}

        # Basic text metrics
        words = spec_text.lower().split()
        features['word_count'] = len(words)
        features['sentence_count'] = spec_text.count('.') + spec_text.count('!') + spec_text.count('?')
        features['avg_sentence_length'] = features['word_count'] / max(features['sentence_count'], 1)

        # Technical indicators
        tech_keywords = ['api', 'database', 'frontend', 'backend', 'ui', 'ux', 'auth', 'security']
        features['tech_density'] = sum(1 for word in words if word in tech_keywords) / len(words)

        # Requirement indicators
        req_keywords = ['must', 'should', 'shall', 'will', 'require', 'need']
        features['requirement_density'] = sum(1 for word in words if word in req_keywords) / len(words)

        # Uncertainty indicators
        uncertain_keywords = ['maybe', 'possibly', 'probably', 'might', 'could', 'tbd', 'todo']
        features['uncertainty_score'] = sum(1 for word in words if word in uncertain_keywords) / len(words)

        # Detail level indicators
        detail_keywords = ['implement', 'design', 'create', 'build', 'develop', 'configure']
        features['detail_level'] = sum(1 for word in words if word in detail_keywords) / len(words)

        return features

    def _extract_context_features(self, context: SpecificationContext) -> Dict[str, float]:
        """Extract quantifiable features from context"""
        features = {}

        # Project size mapping
        size_mapping = {'small': 0.2, 'medium': 0.5, 'large': 0.8, 'enterprise': 1.0}
        features['project_size'] = size_mapping.get(context.project_size, 0.5)

        # Team size normalization (log scale)
        features['team_size_norm'] = min(np.log(context.team_size + 1) / np.log(100), 1.0)

        # Tech stack complexity
        features['tech_stack_size'] = min(len(context.tech_stack) / 10.0, 1.0)

        # Constraint complexity
        features['constraint_count'] = min(len(context.constraints) / 5.0, 1.0)

        return features

    async def _rl_analyze_spec(self, spec_features: Dict[str, float], context_features: Dict[str, float]) -> SpecAnalysis:
        """Perform RL-powered specification analysis"""
        try:
            # Combine features for RL agent
            state_vector = np.array(list(spec_features.values()) + list(context_features.values()))

            # Get RL agent prediction
            action_probs = await self.enhanced_rl_system.predict(self.rl_agent, state_vector)

            # Convert RL output to analysis scores
            clarity_score = float(action_probs[0]) if len(action_probs) > 0 else 0.5
            completeness_score = float(action_probs[1]) if len(action_probs) > 1 else 0.5
            feasibility_score = float(action_probs[2]) if len(action_probs) > 2 else 0.5
            complexity_score = float(action_probs[3]) if len(action_probs) > 3 else 0.5

            # Generate recommendations based on RL analysis
            recommendations = self._generate_rl_recommendations(spec_features, context_features, action_probs)

            # Calculate risk assessment
            risk_assessment = self._calculate_risk_assessment(spec_features, context_features, action_probs)

            # Calculate confidence based on RL certainty
            confidence = float(np.std(action_probs)) if len(action_probs) > 0 else 0.1

            return SpecAnalysis(
                clarity_score=clarity_score,
                completeness_score=completeness_score,
                feasibility_score=feasibility_score,
                complexity_score=complexity_score,
                risk_assessment=risk_assessment,
                recommendations=recommendations,
                confidence=confidence
            )

        except Exception as e:
            self.logger.error(f"RL analysis failed: {e}")
            return await self._heuristic_analyze_spec(spec_features, context_features)

    async def _heuristic_analyze_spec(self, spec_features: Dict[str, float], context_features: Dict[str, float]) -> SpecAnalysis:
        """Fallback heuristic analysis when RL is not available"""

        # Calculate clarity score
        clarity_score = 1.0 - spec_features.get('uncertainty_score', 0.5)
        clarity_score = max(0.0, min(1.0, clarity_score))

        # Calculate completeness score
        completeness_score = spec_features.get('detail_level', 0.5) + spec_features.get('requirement_density', 0.5)
        completeness_score = max(0.0, min(1.0, completeness_score / 2.0))

        # Calculate feasibility score
        feasibility_score = 1.0 - (context_features.get('constraint_count', 0.5) * 0.3)
        feasibility_score = max(0.0, min(1.0, feasibility_score))

        # Calculate complexity score
        complexity_score = (context_features.get('project_size', 0.5) +
                          context_features.get('tech_stack_size', 0.5)) / 2.0

        # Generate heuristic recommendations
        recommendations = self._generate_heuristic_recommendations(spec_features, context_features)

        # Calculate risk assessment
        risk_assessment = {
            'scope_creep': complexity_score * 0.7,
            'technical_debt': spec_features.get('tech_density', 0.5),
            'timeline_risk': 1.0 - feasibility_score,
            'quality_risk': 1.0 - clarity_score
        }

        return SpecAnalysis(
            clarity_score=clarity_score,
            completeness_score=completeness_score,
            feasibility_score=feasibility_score,
            complexity_score=complexity_score,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            confidence=0.6  # Medium confidence for heuristic analysis
        )

    def _generate_rl_recommendations(self, spec_features: Dict[str, float],
                                   context_features: Dict[str, float],
                                   action_probs: np.ndarray) -> List[str]:
        """Generate recommendations based on RL analysis"""
        recommendations = []

        # Analyze RL predictions for specific recommendations
        if len(action_probs) > 0 and action_probs[0] < 0.6:  # Low clarity
            recommendations.append("Consider adding more specific requirements and acceptance criteria")

        if len(action_probs) > 1 and action_probs[1] < 0.6:  # Low completeness
            recommendations.append("Specification appears incomplete - review for missing components")

        if len(action_probs) > 2 and action_probs[2] < 0.6:  # Low feasibility
            recommendations.append("Technical feasibility concerns detected - consider scope reduction")

        if len(action_probs) > 3 and action_probs[3] > 0.8:  # High complexity
            recommendations.append("High complexity detected - consider breaking into smaller phases")

        return recommendations

    def _generate_heuristic_recommendations(self, spec_features: Dict[str, float],
                                          context_features: Dict[str, float]) -> List[str]:
        """Generate recommendations using heuristic analysis"""
        recommendations = []

        if spec_features.get('uncertainty_score', 0) > 0.2:
            recommendations.append("Reduce ambiguity by replacing uncertain language with specific requirements")

        if spec_features.get('detail_level', 0) < 0.3:
            recommendations.append("Add more implementation details and technical specifications")

        if context_features.get('constraint_count', 0) > 0.6:
            recommendations.append("High constraint complexity - consider prioritizing core requirements")

        if context_features.get('project_size', 0) > 0.7:
            recommendations.append("Large project scope - recommend phased delivery approach")

        if spec_features.get('requirement_density', 0) < 0.2:
            recommendations.append("Add more explicit requirements using 'must', 'should', 'shall' language")

        return recommendations

    def _calculate_risk_assessment(self, spec_features: Dict[str, float],
                                 context_features: Dict[str, float],
                                 action_probs: np.ndarray) -> Dict[str, float]:
        """Calculate detailed risk assessment"""
        risks = {}

        # Technical risk
        tech_complexity = context_features.get('tech_stack_size', 0.5)
        risks['technical_risk'] = tech_complexity * 0.8

        # Scope risk
        uncertainty = spec_features.get('uncertainty_score', 0.5)
        project_size = context_features.get('project_size', 0.5)
        risks['scope_risk'] = (uncertainty + project_size) / 2.0

        # Timeline risk
        complexity = spec_features.get('tech_density', 0.5)
        team_size = context_features.get('team_size_norm', 0.5)
        risks['timeline_risk'] = complexity / max(team_size, 0.1)

        # Quality risk
        detail_level = spec_features.get('detail_level', 0.5)
        risks['quality_risk'] = 1.0 - detail_level

        return risks

    async def learn_from_feedback(self, spec_analysis: SpecAnalysis, actual_outcome: Dict[str, Any]):
        """Learn from project outcomes to improve analysis"""
        try:
            if self.enhanced_rl_system:
                # Update RL agent with feedback
                reward = self._calculate_reward(spec_analysis, actual_outcome)
                await self.enhanced_rl_system.update_agent(self.rl_agent, reward)
                self.logger.info(f"Updated RL agent with reward: {reward}")

            # Store success metrics for heuristic improvement
            self.success_metrics[len(self.analysis_history)] = {
                'predicted': spec_analysis,
                'actual': actual_outcome,
                'accuracy': self._calculate_accuracy(spec_analysis, actual_outcome)
            }

        except Exception as e:
            self.logger.error(f"Failed to learn from feedback: {e}")

    def _calculate_reward(self, spec_analysis: SpecAnalysis, actual_outcome: Dict[str, Any]) -> float:
        """Calculate reward signal for RL training"""
        try:
            # Compare predictions with actual outcomes
            accuracy_score = self._calculate_accuracy(spec_analysis, actual_outcome)

            # Reward based on prediction accuracy
            reward = accuracy_score * 2.0 - 1.0  # Scale to [-1, 1]

            return float(reward)

        except Exception:
            return 0.0  # Neutral reward on error

    def _calculate_accuracy(self, spec_analysis: SpecAnalysis, actual_outcome: Dict[str, Any]) -> float:
        """Calculate prediction accuracy"""
        try:
            accuracy_scores = []

            # Compare each prediction with actual outcome
            if 'on_time' in actual_outcome:
                timeline_accuracy = 1.0 - abs(spec_analysis.feasibility_score - actual_outcome['on_time'])
                accuracy_scores.append(timeline_accuracy)

            if 'quality_score' in actual_outcome:
                quality_accuracy = 1.0 - abs(spec_analysis.clarity_score - actual_outcome['quality_score'])
                accuracy_scores.append(quality_accuracy)

            if 'complexity_actual' in actual_outcome:
                complexity_accuracy = 1.0 - abs(spec_analysis.complexity_score - actual_outcome['complexity_actual'])
                accuracy_scores.append(complexity_accuracy)

            return np.mean(accuracy_scores) if accuracy_scores else 0.5

        except Exception:
            return 0.5

    def get_analysis_insights(self) -> Dict[str, Any]:
        """Get insights from analysis history"""
        if not self.analysis_history:
            return {"message": "No analysis history available"}

        insights = {
            "total_analyses": len(self.analysis_history),
            "avg_clarity_score": np.mean([a['analysis'].clarity_score for a in self.analysis_history]),
            "avg_complexity_score": np.mean([a['analysis'].complexity_score for a in self.analysis_history]),
            "common_recommendations": self._get_common_recommendations(),
            "accuracy_trends": self._get_accuracy_trends()
        }

        return insights

    def _get_common_recommendations(self) -> List[str]:
        """Get most common recommendations from analysis history"""
        all_recommendations = []
        for analysis in self.analysis_history:
            all_recommendations.extend(analysis['analysis'].recommendations)

        # Count recommendations
        rec_counts = {}
        for rec in all_recommendations:
            rec_counts[rec] = rec_counts.get(rec, 0) + 1

        # Return top 5 most common
        sorted_recs = sorted(rec_counts.items(), key=lambda x: x[1], reverse=True)
        return [rec for rec, count in sorted_recs[:5]]

    def _get_accuracy_trends(self) -> Dict[str, float]:
        """Get accuracy trends over time"""
        if not self.success_metrics:
            return {"message": "No feedback data available"}

        accuracies = [metrics['accuracy'] for metrics in self.success_metrics.values()]

        return {
            "avg_accuracy": np.mean(accuracies),
            "accuracy_trend": "improving" if len(accuracies) > 1 and accuracies[-1] > accuracies[0] else "stable",
            "best_accuracy": max(accuracies),
            "worst_accuracy": min(accuracies)
        }