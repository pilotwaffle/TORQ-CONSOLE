"""
ControlFlow Orchestration Layer for TORQ Console

This module provides structured, observable multi-agent workflows using
ControlFlow and Prefect integration.

Phase 1: Core Integration
- Basic flow wrappers
- Specialized agents
- Research and analysis workflows

Phase 2: Spec-Kit Enhancement
- ControlFlow-based Spec-Kit workflows
- Parallel execution
- Prefect monitoring

Phase 3: Advanced Features
- Dynamic agent selection
- RL-based optimization
- Workflow templates

Phase 4: Production Optimization
- Performance tuning
- Comprehensive testing
- Documentation
"""

from .integration import TorqControlFlowIntegration

__all__ = ['TorqControlFlowIntegration']

__version__ = '0.1.0'  # Phase 1: Core Integration
