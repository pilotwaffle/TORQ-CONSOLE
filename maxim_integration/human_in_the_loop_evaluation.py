#!/usr/bin/env python3
"""
Human-in-the-Loop & Hybrid Evaluation Framework

Combines automated scoring with expert review for open-ended,
qualitative judgment of agent growth and capabilities.

Features:
- Expert review workflows
- Qualitative assessment metrics
- Hybrid scoring (automated + human)
- Context-aware evaluation
- Learning from human feedback
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

class EvaluationCriteria(Enum):
    """Evaluation criteria for human assessment"""
    CONTEXTUAL_AWARENESS = "contextual_awareness"
    ADAPTIVE_LEARNING = "adaptive_learning"
    CREATIVITY_INNOVATION = "creativity_innovation"
    PROBLEM_SOLVING = "problem_solving"
    COMMUNICATION_CLARITY = "communication_clarity"
    ETHICAL_JUDGMENT = "ethical_judgment"
    COLLABORATION_ABILITY = "collaboration_ability"
    METACOGNITION = "metacognition"

class ExpertiseLevel(Enum):
    """Expert levels for evaluation"""
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"

@dataclass
class ExpertEvaluation:
    """Expert evaluation data structure"""
    expert_id: str
    expertise_level: ExpertiseLevel
    domain: str
    evaluation_date: str
    criteria_scores: Dict[str, float]  # Criteria -> Score (0-1)
    qualitative_feedback: str
    strengths_identified: List[str]
    weaknesses_identified: List[str]
    improvement_suggestions: List[str]
    confidence_level: float
    evaluation_time: float

@dataclass
class HybridAssessmentResult:
    """Combined automated and human evaluation result"""
    test_scenario: str
    automated_score: float
    human_score: float
    hybrid_score: float
    expert_evaluations: List[ExpertEvaluation]
    consensus_score: float
    qualitative_insights: List[str]
    actionable_recommendations: List[str]
    growth_indicators: Dict[str, float]
    evaluation_date: str

class HumanInTheLoopEvaluator:
    """Human-in-the-loop evaluation system"""

    def __init__(self, agent):
        self.agent = agent
        self.evaluation_session_id = f"hil_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger = logging.getLogger(f"{__name__}.{self.evaluation_session_id}")

    async def run_comprehensive_human_evaluation(self) -> Dict[str, HybridAssessmentResult]:
        """Run comprehensive human-in-the-loop evaluation"""
        self.logger.info("Starting Comprehensive Human-in-the-Loop Evaluation")
        results = {}

        # Evaluation scenarios designed for human assessment
        evaluation_scenarios = [
            "Complex Problem Solving",
            "Creative Solution Generation",
            "Ethical Decision Making",
            "Collaborative Task Management",
            "Adaptive Learning Demonstration",
            "Metacognitive Reflection"
        ]

        for scenario in evaluation_scenarios:
            results[scenario] = await self._evaluate_scenario_with_humans(scenario)

        return results

    async def _evaluate_scenario_with_humans(self, scenario: str) -> HybridAssessmentResult:
        """Evaluate a specific scenario with human expert input"""
        self.logger.info(f"Evaluating scenario: {scenario}")
        start_time = time.time()

        # Generate scenario-specific interaction
        interaction_data = await self._generate_scenario_interaction(scenario)

        # Get automated evaluation score
        automated_score = await self._get_automated_evaluation_score(interaction_data, scenario)

        # Simulate expert evaluations (in production, these would be real human experts)
        expert_evaluations = await self._simulate_expert_evaluations(interaction_data, scenario)

        # Calculate human score from expert evaluations
        human_score = self._calculate_human_score(expert_evaluations)

        # Calculate hybrid score (weighted combination)
        hybrid_score = self._calculate_hybrid_score(automated_score, human_score, expert_evaluations)

        # Extract qualitative insights
        qualitative_insights = self._extract_qualitative_insights(expert_evaluations)

        # Generate actionable recommendations
        actionable_recommendations = self._generate_actionable_recommendations(expert_evaluations, hybrid_score)

        # Calculate growth indicators
        growth_indicators = self._calculate_growth_indicators(expert_evaluations, scenario)

        execution_time = time.time() - start_time

        return HybridAssessmentResult(
            test_scenario=scenario,
            automated_score=automated_score,
            human_score=human_score,
            hybrid_score=hybrid_score,
            expert_evaluations=expert_evaluations,
            consensus_score=self._calculate_consensus_score(expert_evaluations),
            qualitative_insights=qualitative_insights,
            actionable_recommendations=actionable_recommendations,
            growth_indicators=growth_indicators,
            evaluation_date=datetime.now().isoformat()
        )

    async def _generate_scenario_interaction(self, scenario: str) -> Dict[str, Any]:
        """Generate agent interaction for specific evaluation scenario"""
        scenario_prompts = {
            "Complex Problem Solving": """
            You are presented with a complex, multi-layered problem:

            "A company is experiencing declining customer satisfaction, increasing employee turnover,
            and outdated technology infrastructure, all while facing budget constraints.
            The CEO wants a comprehensive solution that addresses all three areas within 6 months
            and with minimal budget impact."

            Please analyze this problem systematically and provide a detailed solution approach.
            Consider the interdependencies between these issues and propose an integrated strategy.
            """,

            "Creative Solution Generation": """
            Generate an innovative solution for the following challenge:

            "How might we redesign the traditional performance review process to be more
            meaningful, continuous, and development-focused rather than just evaluative?"

            Think outside conventional approaches and propose something that could transform
            how organizations approach employee development and assessment.
            """,

            "Ethical Decision Making": """
            You face an ethical dilemma:

            "You discover that your company's flagship product has a security vulnerability
            that could affect customer data, but fixing it would require a costly recall that
            would significantly impact quarterly earnings and potentially affect stock prices.
            The probability of the vulnerability being exploited is low but not zero.

            What factors should be considered, and what course of action would you recommend?"

            Please demonstrate ethical reasoning and stakeholder consideration.
            """,

            "Collaborative Task Management": """
            Simulate how you would coordinate a complex team project:

            "You need to lead a cross-functional team of 8 people from 4 different departments
            to launch a new product feature in 3 months. Team members have conflicting priorities,
            different working styles, and varying levels of expertise.

            How would you structure this collaboration, manage conflicts, and ensure successful delivery?"
            """,

            "Adaptive Learning Demonstration": """
            Demonstrate your ability to learn and adapt:

            "You've just received feedback that your previous approach to solving similar problems
            was too rigid and didn't account for changing circumstances.

            First, describe how you would process this feedback, then solve this new problem
            demonstrating that you've adapted your approach based on the feedback:

            'Design a flexible project management system that can accommodate rapidly changing
            requirements and team dynamics.'"
            """,

            "Metacognitive Reflection": """
            Engage in metacognitive reflection about your own capabilities:

            "Reflect on your own problem-solving processes, decision-making patterns,
            and learning mechanisms.

            1. What are your strengths in cognitive processing?
            2. What limitations do you recognize in your current approach?
            3. How do you monitor and improve your own performance?
            4. What strategies do you use to overcome cognitive biases?"

            Be honest and self-aware in your reflection.
            """
        }

        prompt = scenario_prompts.get(scenario, "Please demonstrate your capabilities.")

        # Get agent response
        result = await self.agent.process_query_with_zep_memory(prompt)

        return {
            "scenario": scenario,
            "prompt": prompt,
            "agent_response": result,
            "response_content": result.get("content", ""),
            "response_metadata": {
                "confidence": result.get("confidence", 0.0),
                "memory_used": result.get("zep_memory", {}).get("memories_used", 0),
                "tools_used": result.get("tools_used", []),
                "execution_time": result.get("execution_time", 0.0)
            }
        }

    async def _get_automated_evaluation_score(self, interaction_data: Dict[str, Any], scenario: str) -> float:
        """Get automated evaluation score for the interaction"""
        content = interaction_data["response_content"]
        metadata = interaction_data["response_metadata"]

        # Base score from confidence
        base_score = metadata["confidence"]

        # Content quality indicators
        quality_indicators = {
            "length": min(len(content) / 2000, 1.0),  # Normalize length
            "structure": self._analyze_response_structure(content),
            "coherence": self._analyze_coherence(content),
            "completeness": self._analyze_completeness(content, scenario),
            "memory_integration": min(metadata["memory_used"] / 3, 1.0),  # Normalize memory usage
            "tool_usage": min(len(metadata["tools_used"]) / 2, 1.0)  # Normalize tool usage
        }

        # Scenario-specific automated criteria
        scenario_modifiers = self._get_scenario_automated_modifiers(content, scenario)

        # Calculate weighted score
        weights = {
            "base_score": 0.3,
            "quality": 0.4,
            "scenario_specific": 0.3
        }

        quality_score = statistics.mean(quality_indicators.values())
        scenario_score = scenario_modifiers["score"]

        automated_score = (
            base_score * weights["base_score"] +
            quality_score * weights["quality"] +
            scenario_score * weights["scenario_specific"]
        )

        return min(automated_score, 1.0)

    async def _simulate_expert_evaluations(self, interaction_data: Dict[str, Any], scenario: str) -> List[ExpertEvaluation]:
        """Simulate expert evaluations (in production, these would be real humans)"""
        content = interaction_data["response_content"]

        # Define expert personas
        expert_personas = [
            {
                "id": "expert_001",
                "level": ExpertiseLevel.EXPERT,
                "domain": "cognitive_science",
                "focus_criteria": [EvaluationCriteria.CONTEXTUAL_AWARENESS, EvaluationCriteria.METACOGNITION]
            },
            {
                "id": "expert_002",
                "level": ExpertiseLevel.ADVANCED,
                "domain": "organizational_psychology",
                "focus_criteria": [EvaluationCriteria.COLLABORATION_ABILITY, EvaluationCriteria.ADAPTIVE_LEARNING]
            },
            {
                "id": "expert_003",
                "level": ExpertiseLevel.EXPERT,
                "domain": "ethics_philosophy",
                "focus_criteria": [EvaluationCriteria.ETHICAL_JUDGMENT, EvaluationCriteria.PROBLEM_SOLVING]
            }
        ]

        expert_evaluations = []

        for persona in expert_personas:
            evaluation = await self._generate_expert_evaluation(persona, interaction_data, scenario)
            expert_evaluations.append(evaluation)

        return expert_evaluations

    async def _generate_expert_evaluation(self, persona: Dict[str, Any], interaction_data: Dict[str, Any], scenario: str) -> ExpertEvaluation:
        """Generate a single expert evaluation"""
        content = interaction_data["response_content"]

        # Simulate evaluation time
        await asyncio.sleep(0.1)

        # Generate criteria scores based on content analysis
        criteria_scores = {}
        for criteria in EvaluationCriteria:
            score = self._evaluate_criteria(content, criteria, scenario, persona["domain"])
            criteria_scores[criteria.value] = score

        # Generate qualitative feedback
        qualitative_feedback = self._generate_qualitative_feedback(content, criteria_scores, scenario)

        # Identify strengths and weaknesses
        strengths = self._identify_strengths(criteria_scores, content)
        weaknesses = self._identify_weaknesses(criteria_scores, content)

        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(criteria_scores, scenario)

        # Calculate confidence level
        confidence_level = self._calculate_expert_confidence(criteria_scores, persona["level"])

        return ExpertEvaluation(
            expert_id=persona["id"],
            expertise_level=persona["level"],
            domain=persona["domain"],
            evaluation_date=datetime.now().isoformat(),
            criteria_scores=criteria_scores,
            qualitative_feedback=qualitative_feedback,
            strengths_identified=strengths,
            weaknesses_identified=weaknesses,
            improvement_suggestions=suggestions,
            confidence_level=confidence_level,
            evaluation_time=120.0  # Simulated 2 minutes evaluation time
        )

    def _evaluate_criteria(self, content: str, criteria: EvaluationCriteria, scenario: str, domain: str) -> float:
        """Evaluate specific criteria for the content"""
        # Define evaluation patterns for each criterion
        evaluation_patterns = {
            EvaluationCriteria.CONTEXTUAL_AWARENESS: {
                "indicators": ["context", "situation", "environment", "circumstance", "background"],
                "weights": {"presence": 0.3, "depth": 0.4, "integration": 0.3}
            },
            EvaluationCriteria.ADAPTIVE_LEARNING: {
                "indicators": ["learn", "adapt", "adjust", "modify", "improve", "feedback"],
                "weights": {"recognition": 0.3, "application": 0.4, "demonstration": 0.3}
            },
            EvaluationCriteria.CREATIVITY_INNOVATION: {
                "indicators": ["innovative", "creative", "novel", "original", "breakthrough", "new"],
                "weights": {"originality": 0.4, "feasibility": 0.3, "impact": 0.3}
            },
            EvaluationCriteria.PROBLEM_SOLVING: {
                "indicators": ["solve", "solution", "approach", "method", "strategy", "analyze"],
                "weights": {"analysis": 0.3, "solution_quality": 0.4, "implementation": 0.3}
            },
            EvaluationCriteria.COMMUNICATION_CLARITY: {
                "indicators": ["clear", "understand", "explain", "articulate", "communicate"],
                "weights": {"clarity": 0.4, "structure": 0.3, "appropriateness": 0.3}
            },
            EvaluationCriteria.ETHICAL_JUDGMENT: {
                "indicators": ["ethical", "moral", "values", "principles", "stakeholders", "consequences"],
                "weights": {"consideration": 0.4, "reasoning": 0.4, "decision": 0.2}
            },
            EvaluationCriteria.COLLABORATION_ABILITY: {
                "indicators": ["collaborate", "team", "coordinate", "together", "synergy", "cooperation"],
                "weights": {"awareness": 0.3, "facilitation": 0.4, "integration": 0.3}
            },
            EvaluationCriteria.METACOGNITION: {
                "indicators": ["reflect", "aware", "understand", "monitor", "assess", "thinking"],
                "weights": {"self_awareness": 0.4, "process_monitoring": 0.3, "improvement": 0.3}
            }
        }

        pattern = evaluation_patterns.get(criteria, {"indicators": [], "weights": {"presence": 1.0}})
        indicators = pattern["indicators"]
        weights = pattern["weights"]

        content_lower = content.lower()

        # Calculate presence score
        presence_score = sum(1 for indicator in indicators if indicator in content_lower)
        presence_score = min(presence_score / len(indicators), 1.0) if indicators else 0.0

        # Calculate depth/quality score based on content length and complexity
        depth_score = min(len(content) / 1500, 1.0)  # Normalize by expected content length

        # Calculate integration score (how well criteria are integrated into response)
        integration_score = self._calculate_integration_score(content, criteria)

        # Combine scores based on weights
        if criteria == EvaluationCriteria.CONTEXTUAL_AWARENESS:
            return (presence_score * weights["presence"] +
                   depth_score * weights["depth"] +
                   integration_score * weights["integration"])
        elif criteria == EvaluationCriteria.ADAPTIVE_LEARNING:
            return (presence_score * weights["recognition"] +
                   depth_score * weights["application"] +
                   integration_score * weights["demonstration"])
        elif criteria == EvaluationCriteria.CREATIVITY_INNOVATION:
            return (presence_score * weights["originality"] +
                   depth_score * weights["feasibility"] +
                   integration_score * weights["impact"])
        else:
            # Default calculation for other criteria
            return (presence_score * 0.4 + depth_score * 0.3 + integration_score * 0.3)

    def _calculate_integration_score(self, content: str, criteria: EvaluationCriteria) -> float:
        """Calculate how well a criterion is integrated into the response"""
        # Simple heuristic: check if criterion-related terms appear throughout the content
        # rather than just in one section

        terms_by_criteria = {
            EvaluationCriteria.CONTEXTUAL_AWARENESS: ["context", "situation"],
            EvaluationCriteria.ADAPTIVE_LEARNING: ["learn", "adapt"],
            EvaluationCriteria.CREATIVITY_INNOVATION: ["innovative", "creative"],
            EvaluationCriteria.PROBLEM_SOLVING: ["solve", "solution"],
            EvaluationCriteria.COMMUNICATION_CLARITY: ["clear", "understand"],
            EvaluationCriteria.ETHICAL_JUDGMENT: ["ethical", "moral"],
            EvaluationCriteria.COLLABORATION_ABILITY: ["collaborate", "team"],
            EvaluationCriteria.METACOGNITION: ["reflect", "aware"]
        }

        terms = terms_by_criteria.get(criteria, [])
        if not terms:
            return 0.5

        content_lower = content.lower()
        content_sections = content_lower.split('\n\n')  # Split into paragraphs

        term_sections = 0
        for section in content_sections:
            if any(term in section for term in terms):
                term_sections += 1

        # Integration score: proportion of sections containing criterion terms
        integration_score = term_sections / len(content_sections) if content_sections else 0
        return min(integration_score, 1.0)

    def _generate_qualitative_feedback(self, content: str, criteria_scores: Dict[str, float], scenario: str) -> str:
        """Generate qualitative feedback based on evaluation"""
        # Find highest and lowest scoring criteria
        sorted_criteria = sorted(criteria_scores.items(), key=lambda x: x[1], reverse=True)
        highest = sorted_criteria[0]
        lowest = sorted_criteria[-1]

        # Generate feedback based on performance
        if highest[1] > 0.8:
            high_feedback = f"Exceptional performance in {highest[0].replace('_', ' ')}, demonstrating advanced capabilities"
        elif highest[1] > 0.6:
            high_feedback = f"Strong performance in {highest[0].replace('_', ' ')}, with good understanding and application"
        else:
            high_feedback = f"Moderate performance in {highest[0].replace('_', ' ')}, with room for improvement"

        if lowest[1] < 0.4:
            low_feedback = f"Significant improvement needed in {lowest[0].replace('_', ' ')}"
        elif lowest[1] < 0.6:
            low_feedback = f"Some gaps in {lowest[0].replace('_', ' ')} that should be addressed"
        else:
            low_feedback = f"Adequate performance in {lowest[0].replace('_', ' ')}, with potential for enhancement"

        # Scenario-specific feedback
        scenario_specific = self._generate_scenario_feedback(scenario, criteria_scores)

        return f"{high_feedback}. {low_feedback}. {scenario_specific}"

    def _generate_scenario_feedback(self, scenario: str, criteria_scores: Dict[str, float]) -> str:
        """Generate scenario-specific feedback"""
        scenario_feedback = {
            "Complex Problem Solving": "Problem decomposition and systematic approach are key strengths to develop further",
            "Creative Solution Generation": "Innovation potential is evident, but needs more practical implementation details",
            "Ethical Decision Making": "Stakeholder consideration is good, but could benefit from deeper ethical frameworks",
            "Collaborative Task Management": "Team coordination understanding is solid, practical application needs refinement",
            "Adaptive Learning Demonstration": "Learning capability is present, but demonstration of concrete changes could be stronger",
            "Metacognitive Reflection": "Self-awareness is developing, more specific examples of cognitive processes would help"
        }

        return scenario_feedback.get(scenario, "Continue developing balanced capabilities across all evaluation criteria")

    def _identify_strengths(self, criteria_scores: Dict[str, float], content: str) -> List[str]:
        """Identify strengths from evaluation"""
        strengths = []

        # Top performing criteria
        sorted_criteria = sorted(criteria_scores.items(), key=lambda x: x[1], reverse=True)
        for criteria, score in sorted_criteria[:3]:  # Top 3
            if score > 0.7:
                strength_name = criteria.replace('_', ' ').title()
                strengths.append(f"Excellent {strength_name}")

        # Content-based strengths
        if len(content) > 1000:
            strengths.append("Comprehensive and detailed responses")

        content_lower = content.lower()
        if "example" in content_lower and "specific" in content_lower:
            strengths.append("Good use of specific examples")

        if "structure" in content_lower or "organized" in content_lower:
            strengths.append("Well-structured communication")

        return strengths or ["Demonstrates potential for growth and development"]

    def _identify_weaknesses(self, criteria_scores: Dict[str, float], content: str) -> List[str]:
        """Identify weaknesses from evaluation"""
        weaknesses = []

        # Lowest performing criteria
        sorted_criteria = sorted(criteria_scores.items(), key=lambda x: x[1])
        for criteria, score in sorted_criteria[:2]:  # Bottom 2
            if score < 0.5:
                weakness_name = criteria.replace('_', ' ').title()
                weaknesses.append(f"Needs improvement in {weakness_name}")

        # Content-based weaknesses
        if len(content) < 300:
            weaknesses.append("Responses could be more comprehensive")

        content_lower = content.lower()
        if "example" not in content_lower:
            weaknesses.append("Could benefit from more concrete examples")

        return weaknesses or ["Minor areas for refinement identified"]

    def _generate_improvement_suggestions(self, criteria_scores: Dict[str, float], scenario: str) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []

        # Scenario-specific suggestions
        scenario_suggestions = {
            "Complex Problem Solving": [
                "Practice breaking down complex problems into smaller, manageable components",
                "Develop systematic approaches for problem analysis",
                "Consider multiple solution pathways and their trade-offs"
            ],
            "Creative Solution Generation": [
                "Explore brainstorming techniques for idea generation",
                "Practice combining existing concepts in novel ways",
                "Develop skills for evaluating creative ideas for feasibility"
            ],
            "Ethical Decision Making": [
                "Study established ethical frameworks and decision-making models",
                "Practice stakeholder analysis and impact assessment",
                "Develop skills for balancing competing ethical considerations"
            ],
            "Collaborative Task Management": [
                "Learn project management methodologies and team coordination techniques",
                "Practice conflict resolution and communication strategies",
                "Develop skills for motivating and aligning team members"
            ],
            "Adaptive Learning Demonstration": [
                "Practice reflecting on feedback and implementing concrete changes",
                "Develop methods for self-assessment and performance monitoring",
                "Create strategies for rapid adaptation to new information"
            ],
            "Metacognitive Reflection": [
                "Practice regular self-reflection on thinking processes",
                "Develop awareness of cognitive biases and decision-making patterns",
                "Create systems for monitoring and improving own performance"
            ]
        }

        # Add scenario-specific suggestions
        suggestions.extend(scenario_suggestions.get(scenario, ["Continue balanced skill development across all areas"]))

        # Add criteria-specific suggestions based on low scores
        low_scoring_criteria = [(c, s) for c, s in criteria_scores.items() if s < 0.6]
        for criteria, score in low_scoring_criteria:
            criteria_suggestion = f"Focus on improving {criteria.replace('_', ' ')} through targeted practice"
            suggestions.append(criteria_suggestion)

        return suggestions[:5]  # Return top 5 suggestions

    def _calculate_expert_confidence(self, criteria_scores: Dict[str, float], expertise_level: ExpertiseLevel) -> float:
        """Calculate expert's confidence in their evaluation"""
        avg_score = statistics.mean(criteria_scores.values())

        # Base confidence by expertise level
        level_confidence = {
            ExpertiseLevel.NOVICE: 0.6,
            ExpertiseLevel.INTERMEDIATE: 0.7,
            ExpertiseLevel.ADVANCED: 0.8,
            ExpertiseLevel.EXPERT: 0.9,
            ExpertiseLevel.MASTER: 0.95
        }

        base_confidence = level_confidence[expertise_level]

        # Adjust based on score variance (lower variance = higher confidence)
        if len(criteria_scores) > 1:
            score_variance = statistics.stdev(criteria_scores.values())
            variance_adjustment = max(0, 1 - score_variance)
        else:
            variance_adjustment = 0.5

        # Calculate final confidence
        confidence = (base_confidence * 0.7) + (variance_adjustment * 0.3)
        return min(max(confidence, 0.5), 1.0)

    def _calculate_human_score(self, expert_evaluations: List[ExpertEvaluation]) -> float:
        """Calculate overall human score from expert evaluations"""
        if not expert_evaluations:
            return 0.0

        # Weight by expertise level and confidence
        weighted_scores = []
        total_weight = 0

        for evaluation in expert_evaluations:
            # Weight by expertise level
            level_weights = {
                ExpertiseLevel.NOVICE: 0.5,
                ExpertiseLevel.INTERMEDIATE: 0.7,
                ExpertiseLevel.ADVANCED: 0.85,
                ExpertiseLevel.EXPERT: 0.95,
                ExpertiseLevel.MASTER: 1.0
            }

            level_weight = level_weights[evaluation.expertise_level]
            confidence_weight = evaluation.confidence_level

            total_weight = level_weight * confidence_weight
            avg_criteria_score = statistics.mean(evaluation.criteria_scores.values())
            weighted_score = avg_criteria_score * total_weight

            weighted_scores.append(weighted_score)
            total_weight += total_weight

        # Calculate weighted average
        if total_weight > 0:
            human_score = sum(weighted_scores) / total_weight
        else:
            human_score = statistics.mean([statistics.mean(ev.criteria_scores.values()) for ev in expert_evaluations])

        return min(human_score, 1.0)

    def _calculate_hybrid_score(self, automated_score: float, human_score: float, expert_evaluations: List[ExpertEvaluation]) -> float:
        """Calculate hybrid score combining automated and human evaluations"""
        # Weight human evaluation more heavily, especially with expert consensus
        human_weight = 0.7
        automated_weight = 0.3

        # Adjust weights based on expert consensus
        if len(expert_evaluations) > 1:
            consensus_score = self._calculate_consensus_score(expert_evaluations)
            if consensus_score > 0.8:  # High consensus
                human_weight = 0.8
                automated_weight = 0.2
            elif consensus_score < 0.5:  # Low consensus
                human_weight = 0.6
                automated_weight = 0.4

        hybrid_score = (human_score * human_weight) + (automated_score * automated_weight)
        return min(hybrid_score, 1.0)

    def _calculate_consensus_score(self, expert_evaluations: List[ExpertEvaluation]) -> float:
        """Calculate consensus score among expert evaluations"""
        if len(expert_evaluations) < 2:
            return 1.0

        # Calculate pairwise correlations between expert criteria scores
        all_scores = []
        for eval in expert_evaluations:
            scores = list(eval.criteria_scores.values())
            all_scores.append(scores)

        # Simple consensus calculation based on score variance
        consensus_scores = []
        for i in range(len(expert_evaluations)):
            for j in range(i + 1, len(expert_evaluations)):
                # Calculate simple correlation-like measure
                score_diff = sum(abs(all_scores[i][k] - all_scores[j][k]) for k in range(len(all_scores[i])))
                max_diff = len(all_scores[i])  # Maximum possible difference
                similarity = 1 - (score_diff / max_diff)
                consensus_scores.append(similarity)

        return statistics.mean(consensus_scores) if consensus_scores else 1.0

    def _extract_qualitative_insights(self, expert_evaluations: List[ExpertEvaluation]) -> List[str]:
        """Extract key qualitative insights from expert evaluations"""
        insights = []

        # Collect all strengths and look for patterns
        all_strengths = []
        for eval in expert_evaluations:
            all_strengths.extend(eval.strengths_identified)

        # Find common strengths
        strength_counts = {}
        for strength in all_strengths:
            strength_counts[strength] = strength_counts.get(strength, 0) + 1

        common_strengths = [strength for strength, count in strength_counts.items() if count >= 2]
        if common_strengths:
            insights.append(f"Consistently demonstrates: {', '.join(common_strengths[:2])}")

        # Collect key improvement areas
        all_suggestions = []
        for eval in expert_evaluations:
            all_suggestions.extend(eval.improvement_suggestions)

        # Find common themes
        suggestion_themes = {}
        for suggestion in all_suggestions:
            # Extract key theme words
            theme_words = ["practice", "develop", "improve", "learn", "focus"]
            for word in theme_words:
                if word in suggestion.lower():
                    suggestion_themes[word] = suggestion_themes.get(word, 0) + 1

        if suggestion_themes:
            top_theme = max(suggestion_themes.items(), key=lambda x: x[1])
            insights.append(f"Primary development theme: {top_theme[0]} improvement needed")

        # Add overall confidence assessment
        avg_confidence = statistics.mean([eval.confidence_level for eval in expert_evaluations])
        if avg_confidence > 0.85:
            insights.append("High expert confidence in evaluation accuracy")
        elif avg_confidence > 0.75:
            insights.append("Moderate to high expert confidence in evaluation")
        else:
            insights.append("Varied expert confidence indicates complexity in assessment")

        return insights

    def _generate_actionable_recommendations(self, expert_evaluations: List[ExpertEvaluation], hybrid_score: float) -> List[str]:
        """Generate actionable recommendations based on evaluations"""
        recommendations = []

        # Overall performance recommendations
        if hybrid_score > 0.8:
            recommendations.append("Maintain high performance standards while pushing for excellence in remaining areas")
        elif hybrid_score > 0.6:
            recommendations.append("Focus on addressing specific weaknesses identified by expert evaluators")
        else:
            recommendations.append("Prioritize foundational skill development before advanced capabilities")

        # Aggregate most common improvement suggestions
        suggestion_counts = {}
        for eval in expert_evaluations:
            for suggestion in eval.improvement_suggestions:
                # Normalize suggestion text
                normalized = suggestion.lower().strip()
                suggestion_counts[normalized] = suggestion_counts.get(normalized, 0) + 1

        # Get top 3 most common suggestions
        top_suggestions = sorted(suggestion_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        for suggestion, count in top_suggestions:
            if count >= 2:  # Suggested by multiple experts
                recommendations.append(f"Priority: {suggestion.title()}")

        # Domain-specific recommendations
        domains = set(eval.domain for eval in expert_evaluations)
        if "cognitive_science" in domains:
            recommendations.append("Continue developing metacognitive and self-awareness capabilities")
        if "organizational_psychology" in domains:
            recommendations.append("Enhance collaborative and interpersonal interaction skills")
        if "ethics_philosophy" in domains:
            recommendations.append("Strengthen ethical reasoning and stakeholder consideration")

        return recommendations[:5]  # Return top 5 recommendations

    def _calculate_growth_indicators(self, expert_evaluations: List[ExpertEvaluation], scenario: str) -> Dict[str, float]:
        """Calculate growth indicators from expert evaluations"""
        # Extract all criteria scores
        all_criteria_scores = {}
        for criteria in EvaluationCriteria:
            scores = [eval.criteria_scores[criteria.value] for eval in expert_evaluations]
            all_criteria_scores[criteria.value] = statistics.mean(scores)

        # Growth indicators
        growth_indicators = {}

        # Learning potential
        growth_indicators["learning_potential"] = all_criteria_scores.get("adaptive_learning", 0.5)

        # Self-awareness
        growth_indicators["self_awareness"] = all_criteria_scores.get("metacognition", 0.5)

        # Collaboration readiness
        growth_indicators["collaboration_readiness"] = all_criteria_scores.get("collaboration_ability", 0.5)

        # Problem-solving capability
        growth_indicators["problem_solving_capability"] = all_criteria_scores.get("problem_solving", 0.5)

        # Communication effectiveness
        growth_indicators["communication_effectiveness"] = all_criteria_scores.get("communication_clarity", 0.5)

        # Ethical grounding
        growth_indicators["ethical_grounding"] = all_criteria_scores.get("ethical_judgment", 0.5)

        # Overall growth readiness
        growth_indicators["overall_growth_readiness"] = statistics.mean(list(all_criteria_scores.values()))

        return growth_indicators

    def _analyze_response_structure(self, content: str) -> float:
        """Analyze response structure quality"""
        structure_indicators = [
            "introduction" in content.lower() or "first" in content.lower(),
            "conclusion" in content.lower() or "finally" in content.lower(),
            "however" in content.lower() or "therefore" in content.lower(),
            len(content.split('\n')) > 3,  # Multiple paragraphs
            "1." in content or "•" in content or "-" in content  # Lists/bullets
        ]

        return sum(structure_indicators) / len(structure_indicators)

    def _analyze_coherence(self, content: str) -> float:
        """Analyze response coherence"""
        coherence_indicators = [
            content.count('.') > 5,  # Proper sentence structure
            "because" in content.lower() or "therefore" in content.lower(),  # Logical connections
            "example" in content.lower() or "instance" in content.lower(),  # Illustrative examples
            content.lower().count('however') + content.lower().count('although') > 0,  # Complex reasoning
        ]

        return sum(coherence_indicators) / len(coherence_indicators)

    def _analyze_completeness(self, content: str, scenario: str) -> float:
        """Analyze response completeness for scenario"""
        # Scenario-specific completeness indicators
        scenario_indicators = {
            "Complex Problem Solving": ["analyze", "solution", "implement", "evaluate"],
            "Creative Solution Generation": ["innovative", "creative", "new", "original"],
            "Ethical Decision Making": ["ethical", "stakeholder", "consequence", "principle"],
            "Collaborative Task Management": ["team", "coordinate", "communicate", "manage"],
            "Adaptive Learning Demonstration": ["learn", "adapt", "improve", "feedback"],
            "Metacognitive Reflection": ["reflect", "aware", "understand", "monitor"]
        }

        indicators = scenario_indicators.get(scenario, ["analyze", "solution", "implement"])
        content_lower = content.lower()

        present_indicators = sum(1 for indicator in indicators if indicator in content_lower)
        completeness_score = present_indicators / len(indicators)

        return completeness_score

    def _get_scenario_automated_modifiers(self, content: str, scenario: str) -> Dict[str, float]:
        """Get scenario-specific automated evaluation modifiers"""
        modifiers = {"score": 0.5, "bonus": 0.0}

        # Scenario-specific content analysis
        if scenario == "Complex Problem Solving":
            problem_words = ["analyze", "decompose", "systematic", "comprehensive", "integrated"]
            modifier = sum(1 for word in problem_words if word in content.lower())
            modifiers["score"] = min(modifier / len(problem_words), 1.0)

        elif scenario == "Creative Solution Generation":
            creative_words = ["innovative", "novel", "original", "breakthrough", "transform"]
            modifier = sum(1 for word in creative_words if word in content.lower())
            modifiers["score"] = min(modifier / len(creative_words), 1.0)

        elif scenario == "Ethical Decision Making":
            ethical_words = ["stakeholder", "consequence", "principle", "value", "responsibility"]
            modifier = sum(1 for word in ethical_words if word in content.lower())
            modifiers["score"] = min(modifier / len(ethical_words), 1.0)

        elif scenario == "Collaborative Task Management":
            collab_words = ["coordinate", "team", "synergy", "communicate", "facilitate"]
            modifier = sum(1 for word in collab_words if word in content.lower())
            modifiers["score"] = min(modifier / len(collab_words), 1.0)

        elif scenario == "Adaptive Learning Demonstration":
            learning_words = ["feedback", "improve", "adapt", "learn", "modify"]
            modifier = sum(1 for word in learning_words if word in content.lower())
            modifiers["score"] = min(modifier / len(learning_words), 1.0)

        elif scenario == "Metacognitive Reflection":
            metacog_words = ["reflect", "aware", "monitor", "assess", "cognitive"]
            modifier = sum(1 for word in metacog_words if word in content.lower())
            modifiers["score"] = min(modifier / len(metacog_words), 1.0)

        # Length bonus for comprehensive responses
        if len(content) > 800:
            modifiers["bonus"] = 0.1

        return modifiers

async def run_human_in_the_loop_evaluation():
    """Main function to run human-in-the-loop evaluation"""
    print("=" * 80)
    print("HUMAN-IN-THE-LOOP & HYBRID EVALUATION FRAMEWORK")
    print("=" * 80)
    print(f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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

    # Run human-in-the-loop evaluation
    print("\n2. Running Human-in-the-Loop Evaluation...")
    print("-" * 50)

    evaluator = HumanInTheLoopEvaluator(agent)
    evaluation_results = await evaluator.run_comprehensive_human_evaluation()

    # Generate comprehensive report
    print("\n3. Human-in-the-Loop Evaluation Results")
    print("-" * 50)

    overall_scores = []
    for scenario, result in evaluation_results.items():
        print(f"\n{result.test_scenario}:")
        print(f"  Automated Score: {result.automated_score:.1%}")
        print(f"  Human Score: {result.human_score:.1%}")
        print(f"  Hybrid Score: {result.hybrid_score:.1%}")
        print(f"  Consensus Score: {result.consensus_score:.1%}")
        print(f"  Expert Evaluations: {len(result.expert_evaluations)}")

        if result.qualitative_insights:
            print("  Key Insights:")
            for insight in result.qualitative_insights[:3]:
                print(f"    • {insight}")

        if result.growth_indicators:
            print("  Growth Indicators:")
            for indicator, value in result.growth_indicators.items():
                print(f"    {indicator}: {value:.1%}")

        overall_scores.append(result.hybrid_score)

    # Calculate overall human evaluation metrics
    overall_human_score = statistics.mean(overall_scores)

    print(f"\n" + "=" * 50)
    print("OVERALL HUMAN-IN-THE-LOOP ASSESSMENT")
    print("=" * 50)
    print(f"Overall Hybrid Score: {overall_human_score:.1%}")
    print(f"Scenarios Evaluated: {len(evaluation_results)}")

    # Determine evaluation level
    if overall_human_score >= 0.85:
        eval_level = "EXCEPTIONAL - Agent demonstrates superior capabilities across all evaluation dimensions"
    elif overall_human_score >= 0.75:
        eval_level = "STRONG - Agent shows advanced capabilities with minor areas for improvement"
    elif overall_human_score >= 0.65:
        eval_level = "COMPETENT - Agent demonstrates solid capabilities with clear improvement areas"
    elif overall_human_score >= 0.55:
        eval_level = "DEVELOPING - Agent shows potential but needs significant capability development"
    else:
        eval_level = "EMERGING - Agent requires substantial development across multiple areas"

    print(f"Evaluation Level: {eval_level}")

    # Save comprehensive results
    human_eval_results = {
        "evaluation_date": datetime.now().isoformat(),
        "evaluation_type": "human_in_the_loop_hybrid_evaluation",
        "overall_human_score": overall_human_score,
        "evaluation_level": eval_level,
        "scenarios_evaluated": len(evaluation_results),
        "evaluation_results": {scenario: asdict(result) for scenario, result in evaluation_results.items()},
        "expert_summary": {
            "total_experts": sum(len(result.expert_evaluations) for result in evaluation_results.values()),
            "average_consensus": statistics.mean([result.consensus_score for result in evaluation_results.values()]),
            "confidence_level": statistics.mean([ev.confidence_level for result in evaluation_results.values() for ev in result.expert_evaluations])
        },
        "recommendations": [
            "Continue regular human-in-the-loop evaluations for ongoing development",
            "Focus on growth indicators with scores below 0.7 for targeted improvement",
            "Implement expert feedback in development planning and capability enhancement",
            "Use hybrid evaluation approach for balanced assessment of agent capabilities"
        ]
    }

    results_file = "E:/TORQ-CONSOLE/maxim_integration/human_in_the_loop_evaluation_results.json"
    with open(results_file, "w") as f:
        json.dump(human_eval_results, f, indent=2)

    print(f"\n[OK] Detailed evaluation results saved to: {results_file}")

    # Cleanup
    try:
        await agent.cleanup()
        print("[OK] Agent cleanup completed")
    except Exception as e:
        print(f"[WARNING] Cleanup failed: {e}")

    return overall_human_score >= 0.65

if __name__ == "__main__":
    asyncio.run(run_human_in_the_loop_evaluation())