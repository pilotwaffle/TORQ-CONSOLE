#!/usr/bin/env python3
"""
Phase 2: Adaptive Intelligence Layer
Real-time specification analysis and intelligent assistance system
"""

import asyncio
import json
import time
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class RealTimeAnalysis:
    """Real-time analysis results for specification editing"""
    timestamp: datetime
    clarity_score: float
    completeness_score: float
    feasibility_score: float
    complexity_score: float
    confidence: float
    suggestions: List[str]
    warnings: List[str]
    dependencies_detected: List[str]
    risk_factors: List[str]
    improvement_areas: List[str]


@dataclass
class CompletionSuggestion:
    """Intelligent completion suggestion"""
    text: str
    confidence: float
    category: str  # 'requirement', 'acceptance_criteria', 'tech_stack', 'risk'
    position: int  # Suggested insertion position
    context: str  # Context that triggered this suggestion


@dataclass
class RiskPrediction:
    """Context-aware risk prediction"""
    risk_type: str  # 'technical', 'scope', 'timeline', 'quality'
    severity: float  # 0.0 to 1.0
    description: str
    mitigation_suggestions: List[str]
    triggers: List[str]  # What patterns triggered this prediction
    confidence: float


@dataclass
class DependencyDetection:
    """Detected dependency with context"""
    dependency_name: str
    dependency_type: str  # 'technical', 'business', 'resource', 'external'
    description: str
    required_by: List[str]  # What requires this dependency
    impact_level: float  # 0.0 to 1.0
    auto_detected: bool


class AdaptiveIntelligenceEngine:
    """
    Phase 2: Adaptive Intelligence Layer
    Provides real-time analysis, intelligent suggestions, and adaptive learning
    """

    def __init__(self, rl_analyzer=None):
        self.rl_analyzer = rl_analyzer
        self.analysis_history = deque(maxlen=1000)
        self.user_feedback_history = deque(maxlen=500)
        self.pattern_cache = {}
        self.suggestion_patterns = self._load_suggestion_patterns()
        self.dependency_patterns = self._load_dependency_patterns()
        self.risk_patterns = self._load_risk_patterns()
        self.learning_weights = self._initialize_learning_weights()

        # Real-time analysis state
        self.active_analyses = {}
        self.analysis_queue = asyncio.Queue()
        self.suggestion_cache = {}

        # Performance metrics
        self.metrics = {
            'total_analyses': 0,
            'avg_analysis_time': 0.0,
            'suggestion_accuracy': 0.0,
            'user_adoption_rate': 0.0
        }

    def _load_suggestion_patterns(self) -> Dict[str, List[Dict]]:
        """Load patterns for intelligent completion suggestions"""
        return {
            'requirements': [
                {'pattern': r'\b(?:user|users)\b.*(?:can|should|must|shall)\b', 'suggestion': 'Define specific user actions and outcomes'},
                {'pattern': r'\b(?:system|application)\b.*(?:must|should|shall)\b', 'suggestion': 'Specify performance criteria and constraints'},
                {'pattern': r'\b(?:authentication|auth|login)\b', 'suggestion': 'Consider security requirements: OAuth, JWT, MFA, password policies'},
                {'pattern': r'\b(?:database|data|storage)\b', 'suggestion': 'Define data models, backup, migration, and performance requirements'},
                {'pattern': r'\b(?:api|endpoint|service)\b', 'suggestion': 'Specify REST/GraphQL standards, rate limiting, versioning'},
                {'pattern': r'\b(?:ui|interface|frontend)\b', 'suggestion': 'Define responsive design, accessibility, browser support'},
                {'pattern': r'\b(?:payment|billing|subscription)\b', 'suggestion': 'Consider PCI compliance, payment gateways, refund policies'},
                {'pattern': r'\b(?:notification|email|sms)\b', 'suggestion': 'Define delivery guarantees, templates, opt-out mechanisms'},
            ],
            'acceptance_criteria': [
                {'pattern': r'\b(?:test|testing)\b', 'suggestion': 'Define unit tests, integration tests, and performance benchmarks'},
                {'pattern': r'\b(?:security|secure)\b', 'suggestion': 'Include penetration testing and security audit requirements'},
                {'pattern': r'\b(?:performance|speed|fast)\b', 'suggestion': 'Specify load times, throughput, and concurrent user limits'},
                {'pattern': r'\b(?:mobile|responsive)\b', 'suggestion': 'Define device compatibility and touch interface requirements'},
                {'pattern': r'\b(?:accessibility|a11y)\b', 'suggestion': 'Include WCAG compliance and screen reader compatibility'},
            ],
            'tech_stack': [
                {'pattern': r'\b(?:python|django|flask|fastapi)\b', 'suggestion': 'Consider: PostgreSQL, Redis, Celery, Docker'},
                {'pattern': r'\b(?:react|vue|angular)\b', 'suggestion': 'Consider: TypeScript, state management, testing frameworks'},
                {'pattern': r'\b(?:node|nodejs|express)\b', 'suggestion': 'Consider: MongoDB, JWT, WebSockets, PM2'},
                {'pattern': r'\b(?:mobile|ios|android)\b', 'suggestion': 'Consider: React Native, Flutter, native development'},
                {'pattern': r'\b(?:cloud|aws|azure|gcp)\b', 'suggestion': 'Consider: containerization, CI/CD, monitoring, scaling'},
            ]
        }

    def _load_dependency_patterns(self) -> Dict[str, List[Dict]]:
        """Load patterns for automated dependency detection"""
        return {
            'technical': [
                {'pattern': r'\b(?:database|db|sql|postgresql|mysql|mongodb)\b', 'dependencies': ['Database server', 'Database migrations', 'Backup strategy']},
                {'pattern': r'\b(?:authentication|auth|login|oauth|jwt)\b', 'dependencies': ['User management system', 'Session management', 'Security policies']},
                {'pattern': r'\b(?:email|notification|sms)\b', 'dependencies': ['Email service provider', 'Message templates', 'Delivery tracking']},
                {'pattern': r'\b(?:payment|billing|stripe|paypal)\b', 'dependencies': ['Payment gateway', 'PCI compliance', 'Financial reporting']},
                {'pattern': r'\b(?:api|rest|graphql|endpoint)\b', 'dependencies': ['API documentation', 'Rate limiting', 'API versioning']},
                {'pattern': r'\b(?:file|upload|storage|s3|blob)\b', 'dependencies': ['File storage service', 'CDN', 'File validation']},
                {'pattern': r'\b(?:search|elasticsearch|solr)\b', 'dependencies': ['Search engine', 'Index management', 'Search analytics']},
                {'pattern': r'\b(?:cache|redis|memcache)\b', 'dependencies': ['Cache server', 'Cache invalidation', 'Memory management']},
            ],
            'business': [
                {'pattern': r'\b(?:user|customer|account)\b', 'dependencies': ['User onboarding', 'Customer support', 'User analytics']},
                {'pattern': r'\b(?:admin|administrator|management)\b', 'dependencies': ['Admin interface', 'Role management', 'Audit logging']},
                {'pattern': r'\b(?:report|analytics|dashboard)\b', 'dependencies': ['Data warehouse', 'Business intelligence', 'Report generation']},
                {'pattern': r'\b(?:integration|third.?party|external)\b', 'dependencies': ['API agreements', 'Data mapping', 'Error handling']},
            ],
            'infrastructure': [
                {'pattern': r'\b(?:deploy|deployment|production)\b', 'dependencies': ['CI/CD pipeline', 'Environment configuration', 'Monitoring']},
                {'pattern': r'\b(?:scale|scaling|load)\b', 'dependencies': ['Load balancer', 'Auto-scaling', 'Performance monitoring']},
                {'pattern': r'\b(?:backup|disaster|recovery)\b', 'dependencies': ['Backup strategy', 'Recovery procedures', 'Data archival']},
                {'pattern': r'\b(?:security|encryption|ssl)\b', 'dependencies': ['SSL certificates', 'Security policies', 'Vulnerability scanning']},
            ]
        }

    def _load_risk_patterns(self) -> Dict[str, List[Dict]]:
        """Load patterns for context-aware risk prediction"""
        return {
            'technical_risk': [
                {'pattern': r'\b(?:new|experimental|cutting.?edge|latest)\b.*(?:technology|framework|library)\b', 'severity': 0.7, 'description': 'Using unproven technology increases technical risk'},
                {'pattern': r'\b(?:complex|complicated|intricate)\b.*(?:integration|system|architecture)\b', 'severity': 0.6, 'description': 'Complex integrations often lead to unexpected issues'},
                {'pattern': r'\b(?:legacy|old|outdated|deprecated)\b', 'severity': 0.8, 'description': 'Legacy system dependencies create maintenance and security risks'},
                {'pattern': r'\b(?:real.?time|live|instant|immediate)\b', 'severity': 0.6, 'description': 'Real-time requirements add complexity and potential failure points'},
                {'pattern': r'\b(?:migration|upgrade|refactor)\b', 'severity': 0.7, 'description': 'System migrations carry risk of data loss and downtime'},
            ],
            'scope_risk': [
                {'pattern': r'\b(?:all|every|complete|comprehensive|full)\b', 'severity': 0.6, 'description': 'Overly broad scope increases risk of scope creep'},
                {'pattern': r'\b(?:scalable|scale|enterprise|global)\b', 'severity': 0.5, 'description': 'Scalability requirements can significantly expand scope'},
                {'pattern': r'\b(?:custom|bespoke|unique|specialized)\b', 'severity': 0.6, 'description': 'Custom solutions require more development time and testing'},
                {'pattern': r'\b(?:integration|integrate|connect)\b.*(?:multiple|many|various)\b', 'severity': 0.7, 'description': 'Multiple integrations increase scope complexity'},
            ],
            'timeline_risk': [
                {'pattern': r'\b(?:urgent|asap|immediately|rush|quickly)\b', 'severity': 0.8, 'description': 'Tight timelines increase risk of quality issues'},
                {'pattern': r'\b(?:parallel|concurrent|simultaneous)\b', 'severity': 0.6, 'description': 'Parallel development can lead to integration challenges'},
                {'pattern': r'\b(?:dependency|depends|dependent)\b.*(?:external|third.?party)\b', 'severity': 0.7, 'description': 'External dependencies can cause timeline delays'},
                {'pattern': r'\b(?:research|investigation|exploration)\b', 'severity': 0.5, 'description': 'Research phases add uncertainty to timeline estimates'},
            ],
            'quality_risk': [
                {'pattern': r'\b(?:prototype|mvp|proof.?of.?concept)\b', 'severity': 0.4, 'description': 'MVP approach may compromise long-term quality'},
                {'pattern': r'\b(?:no|minimal|limited)\b.*(?:test|testing)\b', 'severity': 0.9, 'description': 'Insufficient testing significantly increases quality risk'},
                {'pattern': r'\b(?:manual|ad.?hoc|informal)\b.*(?:process|procedure)\b', 'severity': 0.6, 'description': 'Manual processes are error-prone and inconsistent'},
                {'pattern': r'\b(?:skip|bypass|omit)\b.*(?:review|validation|approval)\b', 'severity': 0.8, 'description': 'Skipping quality gates increases defect risk'},
            ]
        }

    def _initialize_learning_weights(self) -> Dict[str, float]:
        """Initialize adaptive learning weights"""
        return {
            'suggestion_relevance': 1.0,
            'risk_accuracy': 1.0,
            'dependency_detection': 1.0,
            'user_preference': 1.0,
            'context_awareness': 1.0
        }

    async def analyze_specification_realtime(self, spec_text: str, context: Dict[str, Any]) -> RealTimeAnalysis:
        """
        Perform real-time analysis of specification text as user types
        """
        start_time = time.time()

        try:
            # Base RL analysis if available
            base_scores = {'clarity_score': 0.5, 'completeness_score': 0.5, 'feasibility_score': 0.5, 'complexity_score': 0.5}
            if self.rl_analyzer:
                try:
                    from .rl_spec_analyzer import SpecificationContext
                    spec_context = SpecificationContext(
                        domain=context.get('domain', 'general'),
                        tech_stack=context.get('tech_stack', []),
                        project_size=context.get('project_size', 'medium'),
                        team_size=context.get('team_size', 4),
                        timeline=context.get('timeline', '4-weeks'),
                        constraints=context.get('constraints', [])
                    )
                    rl_analysis = await self.rl_analyzer.analyze_specification(spec_text, spec_context)
                    base_scores = {
                        'clarity_score': rl_analysis.clarity_score,
                        'completeness_score': rl_analysis.completeness_score,
                        'feasibility_score': rl_analysis.feasibility_score,
                        'complexity_score': rl_analysis.complexity_score
                    }
                except Exception as e:
                    logger.warning(f"RL analysis failed, using heuristic: {e}")

            # Generate intelligent suggestions
            suggestions = await self._generate_intelligent_suggestions(spec_text, context)

            # Detect dependencies
            dependencies = await self._detect_dependencies(spec_text)

            # Predict risks
            risks = await self._predict_risks(spec_text, context)

            # Generate improvement areas
            improvements = await self._identify_improvement_areas(spec_text, base_scores)

            # Generate warnings
            warnings = await self._generate_warnings(spec_text, context)

            analysis = RealTimeAnalysis(
                timestamp=datetime.now(),
                clarity_score=base_scores['clarity_score'],
                completeness_score=base_scores['completeness_score'],
                feasibility_score=base_scores['feasibility_score'],
                complexity_score=base_scores['complexity_score'],
                confidence=min(base_scores.values()) * 0.9,  # Conservative confidence
                suggestions=[s.text for s in suggestions[:5]],  # Top 5 suggestions
                warnings=warnings,
                dependencies_detected=dependencies,
                risk_factors=[r.description for r in risks],
                improvement_areas=improvements
            )

            # Update metrics
            analysis_time = time.time() - start_time
            self.metrics['total_analyses'] += 1
            self.metrics['avg_analysis_time'] = (
                (self.metrics['avg_analysis_time'] * (self.metrics['total_analyses'] - 1) + analysis_time) /
                self.metrics['total_analyses']
            )

            # Store for learning
            self.analysis_history.append(analysis)

            return analysis

        except Exception as e:
            logger.error(f"Real-time analysis failed: {e}")
            # Return safe fallback analysis
            return RealTimeAnalysis(
                timestamp=datetime.now(),
                clarity_score=0.5,
                completeness_score=0.5,
                feasibility_score=0.5,
                complexity_score=0.5,
                confidence=0.3,
                suggestions=["Consider adding more specific requirements"],
                warnings=["Analysis engine encountered an error"],
                dependencies_detected=[],
                risk_factors=[],
                improvement_areas=["Review specification structure"]
            )

    async def _generate_intelligent_suggestions(self, spec_text: str, context: Dict[str, Any]) -> List[CompletionSuggestion]:
        """Generate intelligent completion suggestions based on current text and context"""
        suggestions = []
        spec_lower = spec_text.lower()

        # Analyze current content and suggest completions
        for category, patterns in self.suggestion_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                suggestion_text = pattern_info['suggestion']

                if re.search(pattern, spec_lower):
                    # Calculate confidence based on context match and learning
                    confidence = self._calculate_suggestion_confidence(pattern, context, spec_text)

                    suggestions.append(CompletionSuggestion(
                        text=suggestion_text,
                        confidence=confidence,
                        category=category,
                        position=len(spec_text),  # Suggest at end for now
                        context=f"Detected {category} pattern: {pattern}"
                    ))

        # Sort by confidence and return top suggestions
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return suggestions[:10]

    async def _detect_dependencies(self, spec_text: str) -> List[str]:
        """Detect dependencies automatically from specification text"""
        dependencies = set()
        spec_lower = spec_text.lower()

        for dep_type, patterns in self.dependency_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                deps = pattern_info['dependencies']

                if re.search(pattern, spec_lower):
                    dependencies.update(deps)

        return list(dependencies)

    async def _predict_risks(self, spec_text: str, context: Dict[str, Any]) -> List[RiskPrediction]:
        """Predict risks based on specification content and context"""
        risks = []
        spec_lower = spec_text.lower()

        for risk_type, patterns in self.risk_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                base_severity = pattern_info['severity']
                description = pattern_info['description']

                matches = re.findall(pattern, spec_lower)
                if matches:
                    # Adjust severity based on context
                    adjusted_severity = self._adjust_risk_severity(base_severity, context, risk_type)

                    risks.append(RiskPrediction(
                        risk_type=risk_type,
                        severity=adjusted_severity,
                        description=description,
                        mitigation_suggestions=self._generate_risk_mitigation(risk_type, pattern),
                        triggers=[pattern],
                        confidence=min(0.9, adjusted_severity + 0.1)
                    ))

        return risks

    async def _identify_improvement_areas(self, spec_text: str, scores: Dict[str, float]) -> List[str]:
        """Identify specific areas for improvement based on analysis scores"""
        improvements = []

        if scores['clarity_score'] < 0.6:
            improvements.append("Clarify ambiguous requirements and use more specific language")

        if scores['completeness_score'] < 0.6:
            improvements.append("Add missing acceptance criteria and technical details")

        if scores['feasibility_score'] < 0.6:
            improvements.append("Review technical feasibility and resource requirements")

        if scores['complexity_score'] > 0.8:
            improvements.append("Consider breaking down complex requirements into smaller components")

        # Text-based improvements
        if len(spec_text.split()) < 50:
            improvements.append("Expand specification with more detailed requirements")

        if not re.search(r'\b(?:test|testing|qa|quality)\b', spec_text.lower()):
            improvements.append("Include testing and quality assurance requirements")

        if not re.search(r'\b(?:security|secure|auth)\b', spec_text.lower()):
            improvements.append("Consider security and authentication requirements")

        return improvements

    async def _generate_warnings(self, spec_text: str, context: Dict[str, Any]) -> List[str]:
        """Generate warnings for potential issues"""
        warnings = []
        spec_lower = spec_text.lower()

        # Check for common warning patterns
        if re.search(r'\b(?:simple|easy|quick|trivial)\b', spec_lower):
            warnings.append("Avoid underestimating complexity - 'simple' features often have hidden complexity")

        if re.search(r'\b(?:everything|all|complete|total)\b', spec_lower):
            warnings.append("Overly broad scope detected - consider breaking into phases")

        if not re.search(r'\b(?:user|customer|stakeholder)\b', spec_lower):
            warnings.append("No user perspective mentioned - consider user stories and personas")

        if context.get('timeline') and 'week' in context['timeline']:
            weeks = re.findall(r'(\d+).?week', context['timeline'])
            if weeks and int(weeks[0]) < 4 and len(spec_text.split()) > 200:
                warnings.append("Complex specification with tight timeline - high risk of quality issues")

        return warnings

    def _calculate_suggestion_confidence(self, pattern: str, context: Dict[str, Any], spec_text: str) -> float:
        """Calculate confidence score for a suggestion based on context and learning"""
        base_confidence = 0.7

        # Adjust based on context relevance
        if context.get('domain') == 'web' and 'api' in pattern:
            base_confidence += 0.1

        # Adjust based on specification length and complexity
        word_count = len(spec_text.split())
        if word_count > 100:
            base_confidence += 0.1

        # Apply learning weights
        confidence = base_confidence * self.learning_weights.get('suggestion_relevance', 1.0)

        return min(1.0, max(0.1, confidence))

    def _adjust_risk_severity(self, base_severity: float, context: Dict[str, Any], risk_type: str) -> float:
        """Adjust risk severity based on context"""
        adjusted = base_severity

        # Timeline pressure increases all risks
        if context.get('timeline') and 'week' in context.get('timeline', ''):
            weeks = re.findall(r'(\d+)', context['timeline'])
            if weeks and int(weeks[0]) < 6:
                adjusted = min(1.0, adjusted + 0.2)

        # Team size affects certain risks
        team_size = context.get('team_size', 4)
        if team_size < 3 and risk_type == 'scope_risk':
            adjusted = min(1.0, adjusted + 0.1)
        elif team_size > 8 and risk_type == 'technical_risk':
            adjusted = min(1.0, adjusted + 0.1)

        return adjusted

    def _generate_risk_mitigation(self, risk_type: str, pattern: str) -> List[str]:
        """Generate mitigation suggestions for detected risks"""
        mitigations = {
            'technical_risk': [
                "Conduct proof-of-concept development early",
                "Plan for additional testing and validation",
                "Consider fallback technologies or approaches",
                "Allocate extra time for technical research"
            ],
            'scope_risk': [
                "Define clear scope boundaries and exclusions",
                "Implement change control processes",
                "Break down into smaller, manageable phases",
                "Regular stakeholder alignment meetings"
            ],
            'timeline_risk': [
                "Add buffer time to critical path items",
                "Identify parallel development opportunities",
                "Plan for resource scaling if needed",
                "Define minimum viable product scope"
            ],
            'quality_risk': [
                "Implement comprehensive testing strategy",
                "Define quality gates and review processes",
                "Plan for code review and pair programming",
                "Establish automated quality checks"
            ]
        }

        return mitigations.get(risk_type, ["Review and validate requirements"])

    async def learn_from_feedback(self, feedback: Dict[str, Any]):
        """Learn from user feedback to improve suggestions and analysis"""
        self.user_feedback_history.append({
            'timestamp': datetime.now(),
            'feedback': feedback
        })

        # Update learning weights based on feedback
        if feedback.get('suggestion_helpful') is not None:
            if feedback['suggestion_helpful']:
                self.learning_weights['suggestion_relevance'] = min(2.0, self.learning_weights['suggestion_relevance'] + 0.1)
            else:
                self.learning_weights['suggestion_relevance'] = max(0.5, self.learning_weights['suggestion_relevance'] - 0.05)

        if feedback.get('risk_accurate') is not None:
            if feedback['risk_accurate']:
                self.learning_weights['risk_accuracy'] = min(2.0, self.learning_weights['risk_accuracy'] + 0.1)
            else:
                self.learning_weights['risk_accuracy'] = max(0.5, self.learning_weights['risk_accuracy'] - 0.05)

        # Update metrics
        total_feedback = len(self.user_feedback_history)
        helpful_feedback = sum(1 for f in self.user_feedback_history if f['feedback'].get('suggestion_helpful', False))
        self.metrics['user_adoption_rate'] = helpful_feedback / total_feedback if total_feedback > 0 else 0.0

    def get_intelligence_metrics(self) -> Dict[str, Any]:
        """Get metrics about the adaptive intelligence system"""
        return {
            'performance': self.metrics,
            'learning_weights': self.learning_weights,
            'analysis_history_size': len(self.analysis_history),
            'feedback_history_size': len(self.user_feedback_history),
            'pattern_cache_size': len(self.pattern_cache),
            'active_analyses': len(self.active_analyses)
        }