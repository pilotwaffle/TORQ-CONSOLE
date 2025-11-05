"""
Marvin-Powered Specification Quality Engine

Provides comprehensive quality scoring, validation, and improvement
suggestions for specifications using Marvin's AI capabilities.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from torq_console.marvin_integration import (
    TorqMarvinIntegration,
    TorqSpecAnalysis,
    ComplexityLevel,
    Priority,
    AnalysisConfidence,
)


class QualityLevel(str, Enum):
    """Overall quality level for a specification."""
    EXCELLENT = "excellent"     # 0.9+
    GOOD = "good"              # 0.75-0.89
    ADEQUATE = "adequate"      # 0.6-0.74
    NEEDS_WORK = "needs_work"  # 0.4-0.59
    POOR = "poor"              # <0.4


@dataclass
class QualityScore:
    """Comprehensive quality score for a specification."""
    overall_score: float  # 0.0 - 1.0
    quality_level: QualityLevel
    dimension_scores: Dict[str, float]  # Individual dimension scores
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    validation_errors: List[str]
    confidence: float


@dataclass
class ValidationResult:
    """Result of specification validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


class MarvinQualityEngine:
    """
    AI-powered specification quality assessment engine.

    Provides multi-dimensional quality analysis using Marvin's
    structured outputs and intelligent reasoning.
    """

    # Quality dimensions and their weights
    QUALITY_DIMENSIONS = {
        'clarity': 0.25,           # Clear, unambiguous language
        'completeness': 0.25,      # All necessary details present
        'feasibility': 0.20,       # Technically achievable
        'testability': 0.15,       # Can be tested/validated
        'maintainability': 0.15,   # Can be maintained over time
    }

    def __init__(self, model: Optional[str] = None):
        """
        Initialize quality engine.

        Args:
            model: Optional LLM model override
        """
        self.logger = logging.getLogger("TORQ.SpecKit.QualityEngine")
        self.marvin = TorqMarvinIntegration(model=model)
        self.quality_history = []

        self.logger.info("Initialized Marvin Quality Engine")

    async def assess_quality(
        self,
        spec_text: str,
        analysis: TorqSpecAnalysis
    ) -> QualityScore:
        """
        Assess overall specification quality.

        Args:
            spec_text: Specification text
            analysis: Marvin analysis results

        Returns:
            Comprehensive quality score
        """
        try:
            # Calculate dimension scores
            dimension_scores = self._calculate_dimension_scores(
                spec_text,
                analysis
            )

            # Calculate weighted overall score
            overall_score = self._calculate_overall_score(dimension_scores)

            # Determine quality level
            quality_level = self._classify_quality_level(overall_score)

            # Extract strengths and weaknesses
            strengths = analysis.strengths
            weaknesses = analysis.missing_requirements

            # Get improvement suggestions
            improvement_suggestions = analysis.recommendations

            # Validate specification
            validation = await self.validate_specification(spec_text)

            quality_score = QualityScore(
                overall_score=overall_score,
                quality_level=quality_level,
                dimension_scores=dimension_scores,
                strengths=strengths,
                weaknesses=weaknesses,
                improvement_suggestions=improvement_suggestions,
                validation_errors=validation.errors,
                confidence=self._map_confidence(analysis.confidence)
            )

            # Store in history
            self.quality_history.append({
                'overall_score': overall_score,
                'quality_level': quality_level.value,
                'dimension_scores': dimension_scores
            })

            self.logger.info(
                f"Quality assessment: {quality_level.value} "
                f"(score: {overall_score:.2f})"
            )

            return quality_score

        except Exception as e:
            self.logger.error(f"Failed to assess quality: {e}", exc_info=True)
            return self._fallback_quality_score()

    def _calculate_dimension_scores(
        self,
        spec_text: str,
        analysis: TorqSpecAnalysis
    ) -> Dict[str, float]:
        """Calculate individual dimension scores."""
        # Base scores from analysis
        scores = {
            'clarity': analysis.clarity_score,
            'completeness': analysis.completeness_score,
            'feasibility': analysis.feasibility_score,
        }

        # Estimate testability from completeness and clarity
        scores['testability'] = (
            analysis.completeness_score * 0.6 +
            analysis.clarity_score * 0.4
        )

        # Estimate maintainability from clarity and feasibility
        scores['maintainability'] = (
            analysis.clarity_score * 0.5 +
            analysis.feasibility_score * 0.5
        )

        return scores

    def _calculate_overall_score(self, dimension_scores: Dict[str, float]) -> float:
        """Calculate weighted overall quality score."""
        total_score = 0.0

        for dimension, weight in self.QUALITY_DIMENSIONS.items():
            score = dimension_scores.get(dimension, 0.5)
            total_score += score * weight

        return round(total_score, 3)

    def _classify_quality_level(self, score: float) -> QualityLevel:
        """Classify quality level from score."""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.75:
            return QualityLevel.GOOD
        elif score >= 0.6:
            return QualityLevel.ADEQUATE
        elif score >= 0.4:
            return QualityLevel.NEEDS_WORK
        else:
            return QualityLevel.POOR

    def _map_confidence(self, confidence: AnalysisConfidence) -> float:
        """Map confidence enum to float."""
        confidence_map = {
            AnalysisConfidence.LOW: 0.3,
            AnalysisConfidence.MEDIUM: 0.6,
            AnalysisConfidence.HIGH: 0.8,
            AnalysisConfidence.VERY_HIGH: 0.95
        }
        return confidence_map.get(confidence, 0.5)

    async def validate_specification(self, spec_text: str) -> ValidationResult:
        """
        Validate specification structure and content.

        Uses AI to identify structural issues, missing components,
        and potential problems.

        Args:
            spec_text: Specification text

        Returns:
            Validation result with errors and warnings
        """
        try:
            # Build validation prompt
            validation_prompt = f"""
Validate this software specification and identify any issues:

{spec_text}

Identify:
1. ERRORS: Critical missing components or fundamental problems
2. WARNINGS: Potential issues or areas of concern
3. SUGGESTIONS: Recommendations for improvement

Focus on:
- Missing essential sections (purpose, requirements, acceptance criteria)
- Ambiguous or vague language
- Conflicting requirements
- Incomplete technical details
- Missing non-functional requirements
"""

            # Use Marvin to analyze validation
            validation_text = self.marvin.run(
                validation_prompt,
                result_type=str
            )

            # Parse validation results
            errors, warnings, suggestions = self._parse_validation_results(
                validation_text
            )

            is_valid = len(errors) == 0

            self.logger.info(
                f"Validation complete: "
                f"{len(errors)} errors, "
                f"{len(warnings)} warnings"
            )

            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )

        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation system error: {str(e)}"],
                warnings=[],
                suggestions=[]
            )

    def _parse_validation_results(
        self,
        validation_text: str
    ) -> tuple[List[str], List[str], List[str]]:
        """Parse validation results from AI response."""
        errors = []
        warnings = []
        suggestions = []

        current_section = None

        for line in validation_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Detect section headers
            line_lower = line.lower()
            if 'error' in line_lower and ':' in line:
                current_section = 'errors'
                continue
            elif 'warning' in line_lower and ':' in line:
                current_section = 'warnings'
                continue
            elif 'suggestion' in line_lower and ':' in line:
                current_section = 'suggestions'
                continue

            # Add items to appropriate list
            if line.startswith('-') or line.startswith('*') or line.startswith('•'):
                item = line.lstrip('-*• ').strip()
                if current_section == 'errors':
                    errors.append(item)
                elif current_section == 'warnings':
                    warnings.append(item)
                elif current_section == 'suggestions':
                    suggestions.append(item)

        return errors, warnings, suggestions

    async def suggest_improvements(
        self,
        spec_text: str,
        quality_score: QualityScore
    ) -> List[Dict[str, str]]:
        """
        Generate prioritized improvement suggestions.

        Args:
            spec_text: Original specification
            quality_score: Current quality assessment

        Returns:
            List of prioritized improvements with rationale
        """
        try:
            improvements_prompt = f"""
Based on this specification quality assessment, provide specific, actionable improvements:

CURRENT QUALITY: {quality_score.quality_level.value}
OVERALL SCORE: {quality_score.overall_score:.2f}

WEAKNESSES:
{chr(10).join(f"- {w}" for w in quality_score.weaknesses)}

VALIDATION ERRORS:
{chr(10).join(f"- {e}" for e in quality_score.validation_errors)}

SPECIFICATION:
{spec_text[:500]}...

Provide 3-5 specific, high-impact improvements that would most increase quality.
For each improvement:
1. What to change
2. Why it matters
3. Expected impact on quality
"""

            improvements_text = self.marvin.run(
                improvements_prompt,
                result_type=str
            )

            improvements = self._parse_improvements(improvements_text)

            self.logger.info(f"Generated {len(improvements)} improvement suggestions")

            return improvements

        except Exception as e:
            self.logger.error(f"Failed to generate improvements: {e}")
            return []

    def _parse_improvements(self, improvements_text: str) -> List[Dict[str, str]]:
        """Parse improvement suggestions from AI response."""
        improvements = []

        # Simple parsing - extract paragraphs as improvements
        current_improvement = {}
        lines = improvements_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                if current_improvement:
                    improvements.append(current_improvement)
                    current_improvement = {}
                continue

            # Try to detect structured format
            if 'what' in line.lower() and ':' in line:
                current_improvement['what'] = line.split(':', 1)[1].strip()
            elif 'why' in line.lower() and ':' in line:
                current_improvement['why'] = line.split(':', 1)[1].strip()
            elif 'impact' in line.lower() and ':' in line:
                current_improvement['impact'] = line.split(':', 1)[1].strip()
            elif line.startswith(('-', '*', '•', '1', '2', '3', '4', '5')):
                # Unstructured improvement
                if 'description' not in current_improvement:
                    current_improvement['description'] = line.lstrip('-*•0123456789. ').strip()

        # Add last improvement if exists
        if current_improvement:
            improvements.append(current_improvement)

        return improvements

    def _fallback_quality_score(self) -> QualityScore:
        """Return fallback quality score on error."""
        return QualityScore(
            overall_score=0.5,
            quality_level=QualityLevel.NEEDS_WORK,
            dimension_scores={dim: 0.5 for dim in self.QUALITY_DIMENSIONS.keys()},
            strengths=[],
            weaknesses=["Unable to assess - check system configuration"],
            improvement_suggestions=["Configure AI analysis system"],
            validation_errors=["Analysis system unavailable"],
            confidence=0.1
        )

    def get_quality_trends(self) -> Dict[str, Any]:
        """Get quality trends from history."""
        if not self.quality_history:
            return {
                'average_score': 0.0,
                'trend': 'insufficient_data',
                'count': 0
            }

        scores = [h['overall_score'] for h in self.quality_history]
        avg_score = sum(scores) / len(scores)

        # Calculate trend (simple: compare last 3 vs previous)
        if len(scores) >= 6:
            recent_avg = sum(scores[-3:]) / 3
            previous_avg = sum(scores[-6:-3]) / 3
            trend = 'improving' if recent_avg > previous_avg else 'declining'
        else:
            trend = 'stable'

        return {
            'average_score': round(avg_score, 3),
            'trend': trend,
            'count': len(scores),
            'latest_score': scores[-1] if scores else 0.0
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get quality engine metrics."""
        return {
            'quality_assessments': len(self.quality_history),
            'quality_trends': self.get_quality_trends(),
            'marvin_metrics': self.marvin.get_metrics()
        }


# Factory function
def create_marvin_quality_engine(model: Optional[str] = None) -> MarvinQualityEngine:
    """
    Create a Marvin-powered quality engine.

    Args:
        model: Optional LLM model override

    Returns:
        MarvinQualityEngine instance
    """
    return MarvinQualityEngine(model=model)
