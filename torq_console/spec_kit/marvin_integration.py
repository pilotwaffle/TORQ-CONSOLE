"""
Marvin Integration Layer for TORQ Spec-Kit

Provides seamless integration between Marvin-powered AI analysis
and the existing Spec-Kit engine, allowing CLI commands to use
enhanced AI capabilities.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from .marvin_spec_analyzer import MarvinSpecAnalyzer, create_marvin_spec_analyzer
from .marvin_quality_engine import (
    MarvinQualityEngine,
    create_marvin_quality_engine,
    QualityScore,
    QualityLevel
)
from .rl_spec_analyzer import SpecAnalysis, SpecificationContext


class MarvinSpecKitBridge:
    """
    Bridge between Marvin AI capabilities and Spec-Kit engine.

    Provides high-level interface for CLI commands to use Marvin-powered
    analysis without directly managing Marvin components.
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize Marvin Spec-Kit bridge.

        Args:
            model: Optional LLM model override
        """
        self.logger = logging.getLogger("TORQ.SpecKit.MarvinBridge")
        self.analyzer = create_marvin_spec_analyzer(model=model)
        self.quality_engine = create_marvin_quality_engine(model=model)

        # Track if Marvin is available
        self.marvin_available = True

        self.logger.info("Initialized Marvin Spec-Kit Bridge")

    async def analyze_and_score_specification(
        self,
        spec_text: str,
        context: SpecificationContext
    ) -> Dict[str, Any]:
        """
        Comprehensive specification analysis and quality scoring.

        Provides everything needed to assess a specification's quality
        and provide actionable feedback.

        Args:
            spec_text: Specification text
            context: Specification context

        Returns:
            Dictionary with analysis, quality score, and recommendations
        """
        try:
            # Run Marvin analysis
            spec_analysis = await self.analyzer.analyze_specification(
                spec_text,
                context
            )

            # Get enhanced analysis (includes requirements, intent, etc.)
            enhanced = await self.analyzer.enhance_specification(
                spec_text,
                context
            )

            # Get TorqSpecAnalysis for quality assessment
            marvin_analysis = enhanced.get('marvin_analysis')
            if not marvin_analysis:
                # Re-run to get TorqSpecAnalysis
                prompt = self.analyzer._build_analysis_prompt(spec_text, context)
                marvin_analysis = await self.analyzer._run_marvin_analysis(prompt)

            # Assess quality
            quality_score = await self.quality_engine.assess_quality(
                spec_text,
                marvin_analysis
            )

            # Get improvement suggestions
            improvements = await self.quality_engine.suggest_improvements(
                spec_text,
                quality_score
            )

            return {
                'spec_analysis': asdict(spec_analysis),
                'quality_score': asdict(quality_score),
                'extracted_requirements': enhanced.get('extracted_requirements', []),
                'intent': enhanced.get('intent', 'unknown'),
                'complexity': enhanced.get('complexity', 'unknown'),
                'acceptance_criteria': enhanced.get('generated_acceptance_criteria', []),
                'improvements': improvements,
                'marvin_available': True
            }

        except Exception as e:
            self.logger.error(f"Marvin analysis failed: {e}", exc_info=True)
            return self._fallback_analysis(spec_text, context)

    async def quick_analyze(
        self,
        spec_text: str,
        context: SpecificationContext
    ) -> SpecAnalysis:
        """
        Quick analysis using Marvin (returns legacy SpecAnalysis).

        For backward compatibility with existing Spec-Kit code.

        Args:
            spec_text: Specification text
            context: Specification context

        Returns:
            SpecAnalysis compatible with existing code
        """
        try:
            return await self.analyzer.analyze_specification(spec_text, context)
        except Exception as e:
            self.logger.error(f"Quick analysis failed: {e}")
            return self.analyzer._fallback_analysis()

    async def extract_and_enhance_requirements(
        self,
        spec_text: str
    ) -> Dict[str, List[str]]:
        """
        Extract requirements and generate acceptance criteria.

        Args:
            spec_text: Specification text

        Returns:
            Dictionary with requirements and acceptance criteria
        """
        try:
            requirements = await self.analyzer.extract_requirements(spec_text)
            acceptance_criteria = await self.analyzer.generate_acceptance_criteria(
                spec_text
            )

            return {
                'requirements': requirements,
                'acceptance_criteria': acceptance_criteria
            }

        except Exception as e:
            self.logger.error(f"Requirement extraction failed: {e}")
            return {
                'requirements': [],
                'acceptance_criteria': []
            }

    async def validate_and_improve(
        self,
        spec_text: str
    ) -> Dict[str, Any]:
        """
        Validate specification and provide improvement suggestions.

        Args:
            spec_text: Specification text

        Returns:
            Dictionary with validation results and improvements
        """
        try:
            # Validate
            validation = await self.quality_engine.validate_specification(spec_text)

            # For improvements, we need a quality score
            # Create minimal analysis
            context = SpecificationContext(
                domain="general",
                tech_stack=[],
                project_size="medium",
                team_size=5,
                timeline="unknown",
                constraints=[]
            )

            analysis = await self.analyzer.analyze_specification(spec_text, context)
            prompt = self.analyzer._build_analysis_prompt(spec_text, context)
            marvin_analysis = await self.analyzer._run_marvin_analysis(prompt)
            quality_score = await self.quality_engine.assess_quality(
                spec_text,
                marvin_analysis
            )

            improvements = await self.quality_engine.suggest_improvements(
                spec_text,
                quality_score
            )

            return {
                'validation': asdict(validation),
                'quality_score': asdict(quality_score),
                'improvements': improvements
            }

        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return {
                'validation': {
                    'is_valid': False,
                    'errors': [str(e)],
                    'warnings': [],
                    'suggestions': []
                },
                'improvements': []
            }

    def _fallback_analysis(
        self,
        spec_text: str,
        context: SpecificationContext
    ) -> Dict[str, Any]:
        """Return fallback analysis when Marvin unavailable."""
        self.marvin_available = False

        return {
            'spec_analysis': asdict(self.analyzer._fallback_analysis()),
            'quality_score': asdict(self.quality_engine._fallback_quality_score()),
            'extracted_requirements': [],
            'intent': 'unknown',
            'complexity': 'unknown',
            'acceptance_criteria': [],
            'improvements': [],
            'marvin_available': False,
            'error': 'Marvin analysis unavailable - check API configuration'
        }

    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get metrics from all Marvin components."""
        return {
            'analyzer_metrics': self.analyzer.get_metrics(),
            'quality_metrics': self.quality_engine.get_metrics(),
            'analysis_history': len(self.analyzer.get_analysis_history()),
            'quality_trends': self.quality_engine.get_quality_trends(),
            'marvin_available': self.marvin_available
        }

    def is_available(self) -> bool:
        """Check if Marvin is available and working."""
        return self.marvin_available


# Convenience functions for CLI integration
_global_bridge: Optional[MarvinSpecKitBridge] = None


def get_marvin_bridge(model: Optional[str] = None) -> MarvinSpecKitBridge:
    """
    Get global Marvin bridge instance (singleton pattern).

    Args:
        model: Optional LLM model override

    Returns:
        MarvinSpecKitBridge instance
    """
    global _global_bridge

    if _global_bridge is None:
        _global_bridge = MarvinSpecKitBridge(model=model)

    return _global_bridge


async def marvin_analyze_spec(
    spec_text: str,
    context: SpecificationContext,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function for specification analysis.

    Args:
        spec_text: Specification text
        context: Specification context
        model: Optional LLM model override

    Returns:
        Complete analysis results
    """
    bridge = get_marvin_bridge(model=model)
    return await bridge.analyze_and_score_specification(spec_text, context)


async def marvin_validate_spec(
    spec_text: str,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function for specification validation.

    Args:
        spec_text: Specification text
        model: Optional LLM model override

    Returns:
        Validation results
    """
    bridge = get_marvin_bridge(model=model)
    return await bridge.validate_and_improve(spec_text)


def marvin_is_available() -> bool:
    """
    Check if Marvin is available.

    Returns:
        True if Marvin is configured and working
    """
    # Note: _global_bridge is initialized in get_marvin_bridge()
    # This function assumes Marvin is available until proven otherwise
    if _global_bridge is None:
        return True  # Assume available until proven otherwise

    return _global_bridge.is_available()
