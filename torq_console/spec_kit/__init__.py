"""
TORQ Console Spec-Kit Integration
- Phase 1: Intelligent Spec-Driven Foundation with RL
- Phase 2: Marvin-Powered AI Analysis (Enhanced)
"""

# Phase 1: Core Spec-Kit (always available)
from .spec_engine import SpecKitEngine
from .spec_commands import SpecKitCommands
from .rl_spec_analyzer import RLSpecAnalyzer

__all__ = [
    # Phase 1: Core Spec-Kit
    'SpecKitEngine',
    'SpecKitCommands',
    'RLSpecAnalyzer',
]

# Phase 2: Marvin Integration (optional)
try:
    from .marvin_spec_analyzer import MarvinSpecAnalyzer, create_marvin_spec_analyzer
    from .marvin_quality_engine import (
        MarvinQualityEngine,
        create_marvin_quality_engine,
        QualityScore,
        QualityLevel
    )
    from .marvin_integration import (
        MarvinSpecKitBridge,
        get_marvin_bridge,
        marvin_analyze_spec,
        marvin_validate_spec,
        marvin_is_available
    )

    __all__.extend([
        # Phase 2: Marvin Integration
        'MarvinSpecAnalyzer',
        'create_marvin_spec_analyzer',
        'MarvinQualityEngine',
        'create_marvin_quality_engine',
        'QualityScore',
        'QualityLevel',
        'MarvinSpecKitBridge',
        'get_marvin_bridge',
        'marvin_analyze_spec',
        'marvin_validate_spec',
        'marvin_is_available',
    ])

except ImportError:
    # Marvin integration not available - Spec-Kit will work with RL-only analysis
    pass