"""
Marvin-Powered Specification Analyzer for TORQ Console Spec-Kit

Enhances specification analysis with Marvin 3.0's structured outputs
and AI-powered insights. Provides type-safe, intelligent analysis
that supersedes traditional RL heuristics.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Import Marvin integration
from torq_console.marvin_integration import (
    TorqMarvinIntegration,
    TorqSpecAnalysis,
    create_spec_analyzer,
    IntentClassification,
    ComplexityLevel,
    Priority,
    AnalysisConfidence,
)

# Import existing Spec-Kit types
from .rl_spec_analyzer import SpecAnalysis, SpecificationContext


class MarvinSpecAnalyzer:
    """
    Marvin-powered specification analyzer using structured outputs.

    Provides enhanced specification analysis using LLM-powered insights
    with full type safety via Pydantic models.
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize Marvin specification analyzer.

        Args:
            model: Optional LLM model override (defaults to Claude Sonnet 4)
        """
        self.logger = logging.getLogger("TORQ.SpecKit.MarvinAnalyzer")
        self.marvin = TorqMarvinIntegration(model=model)
        self.spec_agent = create_spec_analyzer(model=model)
        self.analysis_history = []

        self.logger.info("Initialized Marvin-powered Spec Analyzer")

    async def analyze_specification(
        self,
        spec_text: str,
        context: SpecificationContext
    ) -> SpecAnalysis:
        """
        Analyze specification using Marvin's structured outputs.

        Args:
            spec_text: The specification text to analyze
            context: Context information for the specification

        Returns:
            SpecAnalysis compatible with existing Spec-Kit
        """
        try:
            self.logger.info(f"Analyzing specification with context: {context.domain}")

            # Build analysis prompt with context
            analysis_prompt = self._build_analysis_prompt(spec_text, context)

            # Use Marvin to extract structured analysis
            torq_analysis = await self._run_marvin_analysis(analysis_prompt)

            # Convert to Spec-Kit SpecAnalysis format
            spec_analysis = self._convert_to_spec_analysis(torq_analysis)

            # Store in history for learning
            self.analysis_history.append({
                'spec_text': spec_text[:200],  # Store snippet
                'context': context,
                'analysis': spec_analysis,
                'marvin_metrics': self.marvin.get_metrics()
            })

            self.logger.info(f"Analysis complete - Confidence: {spec_analysis.confidence:.2f}")
            return spec_analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze specification: {e}", exc_info=True)
            # Return fallback analysis
            return self._fallback_analysis()

    def _build_analysis_prompt(
        self,
        spec_text: str,
        context: SpecificationContext
    ) -> str:
        """Build comprehensive analysis prompt for Marvin."""
        return f"""
Analyze this software specification thoroughly:

SPECIFICATION:
{spec_text}

CONTEXT:
- Domain: {context.domain}
- Tech Stack: {', '.join(context.tech_stack)}
- Project Size: {context.project_size}
- Team Size: {context.team_size} people
- Timeline: {context.timeline}
- Constraints: {', '.join(context.constraints)}

Provide a comprehensive analysis evaluating:
1. CLARITY: How well-defined and unambiguous are the requirements?
2. COMPLETENESS: Are all necessary components and details specified?
3. FEASIBILITY: Is this technically and practically achievable?
4. RISKS: What are the technical, scope, and timeline risks?
5. RECOMMENDATIONS: What improvements would strengthen this specification?
6. STRENGTHS: What does this specification do well?

Consider the tech stack, project size, and constraints in your analysis.
Be specific and actionable in your recommendations.
"""

    async def _run_marvin_analysis(self, prompt: str) -> TorqSpecAnalysis:
        """Run Marvin analysis to extract structured output."""
        # Use Marvin's cast to get a single TorqSpecAnalysis instance
        analysis = self.marvin.cast(
            prompt,
            TorqSpecAnalysis,
            instructions="Analyze the specification and provide structured feedback"
        )
        return analysis

    def _convert_to_spec_analysis(self, torq_analysis: TorqSpecAnalysis) -> SpecAnalysis:
        """
        Convert TorqSpecAnalysis to legacy SpecAnalysis format.

        Maintains compatibility with existing Spec-Kit code.
        """
        # Map confidence to numeric
        confidence_map = {
            AnalysisConfidence.LOW: 0.3,
            AnalysisConfidence.MEDIUM: 0.6,
            AnalysisConfidence.HIGH: 0.8,
            AnalysisConfidence.VERY_HIGH: 0.95
        }

        # Build risk assessment from technical risks
        risk_assessment = {}

        # Derive risk scores from recommendations and identified risks
        num_risks = len(torq_analysis.technical_risks)
        num_missing = len(torq_analysis.missing_requirements)

        # Calculate risk categories
        technical_risk = min(0.9, 0.2 + (num_risks * 0.15))
        scope_risk = min(0.9, 0.2 + (num_missing * 0.15))
        timeline_risk = 1.0 - torq_analysis.feasibility_score
        quality_risk = 1.0 - torq_analysis.completeness_score

        risk_assessment = {
            'technical': technical_risk,
            'scope': scope_risk,
            'timeline': timeline_risk,
            'quality': quality_risk
        }

        # Calculate complexity from scores
        complexity_score = 1.0 - (
            (torq_analysis.clarity_score +
             torq_analysis.completeness_score +
             torq_analysis.feasibility_score) / 3.0
        )

        return SpecAnalysis(
            clarity_score=torq_analysis.clarity_score,
            completeness_score=torq_analysis.completeness_score,
            feasibility_score=torq_analysis.feasibility_score,
            complexity_score=complexity_score,
            risk_assessment=risk_assessment,
            recommendations=torq_analysis.recommendations,
            confidence=confidence_map[torq_analysis.confidence]
        )

    def _fallback_analysis(self) -> SpecAnalysis:
        """Return fallback analysis when Marvin fails."""
        return SpecAnalysis(
            clarity_score=0.5,
            completeness_score=0.5,
            feasibility_score=0.5,
            complexity_score=0.5,
            risk_assessment={'unknown': 0.5},
            recommendations=['Unable to perform AI analysis - check API configuration'],
            confidence=0.1
        )

    async def extract_requirements(self, spec_text: str) -> List[str]:
        """
        Extract structured requirements from specification text.

        Uses Marvin's extract to identify all requirements in the spec.

        Args:
            spec_text: Specification text

        Returns:
            List of extracted requirements
        """
        try:
            requirements = self.marvin.extract(
                spec_text,
                str,
                instructions="Extract all specific requirements from this specification. "
                           "Each requirement should be a single, clear statement."
            )
            self.logger.info(f"Extracted {len(requirements)} requirements")
            return requirements
        except Exception as e:
            self.logger.error(f"Failed to extract requirements: {e}")
            return []

    async def classify_specification_intent(self, spec_text: str) -> IntentClassification:
        """
        Classify the intent of a specification.

        Args:
            spec_text: Specification text

        Returns:
            Classification of the specification's intent
        """
        try:
            intent = self.marvin.classify(
                spec_text,
                IntentClassification,
                instructions="Classify the primary intent of this specification"
            )
            self.logger.info(f"Classified specification as: {intent.value}")
            return intent
        except Exception as e:
            self.logger.error(f"Failed to classify intent: {e}")
            return IntentClassification.SPEC_CREATE

    async def assess_complexity(self, spec_text: str) -> ComplexityLevel:
        """
        Assess the complexity level of a specification.

        Args:
            spec_text: Specification text

        Returns:
            Complexity level classification
        """
        try:
            complexity = self.marvin.classify(
                spec_text,
                ComplexityLevel,
                instructions="Assess the implementation complexity of this specification"
            )
            self.logger.info(f"Assessed complexity as: {complexity.value}")
            return complexity
        except Exception as e:
            self.logger.error(f"Failed to assess complexity: {e}")
            return ComplexityLevel.MODERATE

    async def generate_acceptance_criteria(
        self,
        spec_text: str,
        num_criteria: int = 5
    ) -> List[str]:
        """
        Generate acceptance criteria for a specification.

        Uses Marvin's generate to create criteria based on the spec.

        Args:
            spec_text: Specification text
            num_criteria: Number of criteria to generate

        Returns:
            List of acceptance criteria
        """
        try:
            criteria = self.marvin.generate(
                str,
                n=num_criteria,
                instructions=f"Generate {num_criteria} specific, testable acceptance "
                           f"criteria for this specification:\n\n{spec_text}"
            )
            self.logger.info(f"Generated {len(criteria)} acceptance criteria")
            return criteria
        except Exception as e:
            self.logger.error(f"Failed to generate acceptance criteria: {e}")
            return []

    async def enhance_specification(
        self,
        spec_text: str,
        context: SpecificationContext
    ) -> Dict[str, Any]:
        """
        Provide comprehensive specification enhancement.

        Combines analysis, requirement extraction, and suggestions.

        Args:
            spec_text: Original specification text
            context: Specification context

        Returns:
            Dictionary with enhanced specification data
        """
        try:
            # Run analysis
            analysis = await self.analyze_specification(spec_text, context)

            # Extract requirements
            requirements = await self.extract_requirements(spec_text)

            # Classify intent and complexity
            intent = await self.classify_specification_intent(spec_text)
            complexity = await self.assess_complexity(spec_text)

            # Generate acceptance criteria if needed
            acceptance_criteria = await self.generate_acceptance_criteria(spec_text)

            return {
                'analysis': asdict(analysis),
                'extracted_requirements': requirements,
                'intent': intent.value,
                'complexity': complexity.value,
                'generated_acceptance_criteria': acceptance_criteria,
                'metrics': self.marvin.get_metrics()
            }

        except Exception as e:
            self.logger.error(f"Failed to enhance specification: {e}")
            return {
                'error': str(e),
                'analysis': asdict(self._fallback_analysis())
            }

    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """Get history of all analyses performed."""
        return self.analysis_history

    def get_metrics(self) -> Dict[str, Any]:
        """Get Marvin integration metrics."""
        return self.marvin.get_metrics()

    def reset_metrics(self):
        """Reset Marvin metrics."""
        self.marvin.reset_metrics()


# Factory function for easy integration
def create_marvin_spec_analyzer(model: Optional[str] = None) -> MarvinSpecAnalyzer:
    """
    Create a Marvin-powered specification analyzer.

    Args:
        model: Optional LLM model override

    Returns:
        MarvinSpecAnalyzer instance
    """
    return MarvinSpecAnalyzer(model=model)
