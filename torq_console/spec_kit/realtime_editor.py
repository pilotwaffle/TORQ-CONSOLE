#!/usr/bin/env python3
"""
Phase 2: Real-time Editing Assistance
Provides intelligent editing assistance during specification creation
"""

import asyncio
import json
import time
import re
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from .adaptive_intelligence import AdaptiveIntelligenceEngine, CompletionSuggestion, RealTimeAnalysis

logger = logging.getLogger(__name__)


@dataclass
class EditingContext:
    """Context for real-time editing session"""
    specification_id: Optional[str]
    cursor_position: int
    selected_text: str
    current_section: str  # 'title', 'description', 'requirements', etc.
    document_length: int
    edit_history: List[str]
    user_preferences: Dict[str, Any]


@dataclass
class EditingSuggestion:
    """Real-time editing suggestion"""
    type: str  # 'completion', 'correction', 'enhancement', 'warning'
    text: str
    position: int
    replacement_length: int
    confidence: float
    category: str
    explanation: str
    action: str  # 'insert', 'replace', 'append'


@dataclass
class EditingMetrics:
    """Metrics for editing session"""
    session_start: datetime
    total_edits: int
    suggestions_offered: int
    suggestions_accepted: int
    analysis_requests: int
    avg_response_time: float
    user_satisfaction: Optional[float]


class RealTimeEditor:
    """
    Real-time editing assistance with intelligent suggestions
    """

    def __init__(self, adaptive_engine: AdaptiveIntelligenceEngine):
        self.adaptive_engine = adaptive_engine
        self.active_sessions = {}
        self.suggestion_cache = {}
        self.editing_patterns = self._load_editing_patterns()
        self.auto_correction = self._load_auto_corrections()

        # Performance settings
        self.debounce_delay = 0.3  # Seconds to wait before analyzing
        self.max_suggestions = 5
        self.suggestion_threshold = 0.6

    def _load_editing_patterns(self) -> Dict[str, List[Dict]]:
        """Load patterns for real-time editing assistance"""
        return {
            'requirements_patterns': [
                {
                    'trigger': r'\b(?:user|customer|stakeholder)\b.*(?:should|must|can|will)\b',
                    'suggestion': 'Consider using more specific user story format: "As a [user type], I want [goal] so that [benefit]"',
                    'category': 'structure'
                },
                {
                    'trigger': r'\b(?:system|application|software)\b.*(?:should|must|will)\b',
                    'suggestion': 'Define specific system behavior and measurable criteria',
                    'category': 'clarity'
                },
                {
                    'trigger': r'\b(?:fast|quick|responsive|efficient)\b',
                    'suggestion': 'Specify exact performance requirements (e.g., "< 2 seconds response time")',
                    'category': 'specificity'
                },
                {
                    'trigger': r'\b(?:secure|safe|protected)\b',
                    'suggestion': 'Define specific security requirements (encryption, authentication, authorization)',
                    'category': 'security'
                }
            ],
            'acceptance_criteria_patterns': [
                {
                    'trigger': r'^(?:given|when|then)\b',
                    'suggestion': 'Great! Using Given-When-Then format. Ensure all scenarios are covered.',
                    'category': 'validation'
                },
                {
                    'trigger': r'\b(?:test|testing|verify|validate)\b',
                    'suggestion': 'Include both positive and negative test scenarios',
                    'category': 'testing'
                },
                {
                    'trigger': r'\b(?:performance|load|stress)\b',
                    'suggestion': 'Specify exact metrics: concurrent users, response times, throughput',
                    'category': 'performance'
                }
            ],
            'technical_patterns': [
                {
                    'trigger': r'\b(?:api|rest|graphql|endpoint)\b',
                    'suggestion': 'Consider: rate limiting, versioning, documentation, error handling',
                    'category': 'api_design'
                },
                {
                    'trigger': r'\b(?:database|db|sql|nosql)\b',
                    'suggestion': 'Consider: data modeling, migrations, backup strategy, performance optimization',
                    'category': 'data'
                },
                {
                    'trigger': r'\b(?:frontend|ui|ux|interface)\b',
                    'suggestion': 'Consider: responsive design, accessibility, browser compatibility, user testing',
                    'category': 'frontend'
                }
            ]
        }

    def _load_auto_corrections(self) -> Dict[str, str]:
        """Load common auto-corrections"""
        return {
            # Common typos in technical writing
            'utilise': 'utilize',
            'realise': 'realize',
            'colour': 'color',
            'behaviour': 'behavior',
            'centre': 'center',
            'optimise': 'optimize',

            # Technical term corrections
            'rest api': 'REST API',
            'json': 'JSON',
            'xml': 'XML',
            'html': 'HTML',
            'css': 'CSS',
            'javascript': 'JavaScript',
            'typescript': 'TypeScript',
            'nodejs': 'Node.js',
            'mongodb': 'MongoDB',
            'postgresql': 'PostgreSQL',
            'mysql': 'MySQL',

            # Common specification terms
            'user story': 'user story',
            'acceptance criteria': 'acceptance criteria',
            'non-functional': 'non-functional',
            'proof of concept': 'proof of concept'
        }

    async def start_editing_session(self, spec_id: str, initial_content: str, user_prefs: Dict[str, Any]) -> str:
        """Start a new real-time editing session"""
        session_id = f"edit_{spec_id}_{int(time.time())}"

        self.active_sessions[session_id] = {
            'specification_id': spec_id,
            'content': initial_content,
            'user_preferences': user_prefs,
            'metrics': EditingMetrics(
                session_start=datetime.now(),
                total_edits=0,
                suggestions_offered=0,
                suggestions_accepted=0,
                analysis_requests=0,
                avg_response_time=0.0,
                user_satisfaction=None
            ),
            'context': EditingContext(
                specification_id=spec_id,
                cursor_position=len(initial_content),
                selected_text="",
                current_section="description",
                document_length=len(initial_content),
                edit_history=[initial_content],
                user_preferences=user_prefs
            ),
            'pending_analysis': None
        }

        logger.info(f"Started editing session {session_id} for spec {spec_id}")
        return session_id

    async def handle_text_change(self, session_id: str, new_content: str, cursor_pos: int,
                                selected_text: str = "", section: str = "description") -> Dict[str, Any]:
        """Handle real-time text changes and provide suggestions"""
        if session_id not in self.active_sessions:
            return {'error': 'Invalid session ID'}

        session = self.active_sessions[session_id]
        start_time = time.time()

        try:
            # Update session context
            session['content'] = new_content
            session['context'].cursor_position = cursor_pos
            session['context'].selected_text = selected_text
            session['context'].current_section = section
            session['context'].document_length = len(new_content)
            session['context'].edit_history.append(new_content)
            session['metrics'].total_edits += 1

            # Debounce analysis requests
            if session['pending_analysis']:
                session['pending_analysis'].cancel()

            session['pending_analysis'] = asyncio.create_task(
                self._delayed_analysis(session_id, new_content, cursor_pos, section)
            )

            # Immediate suggestions for current edit
            immediate_suggestions = await self._get_immediate_suggestions(
                new_content, cursor_pos, selected_text, section, session['context']
            )

            # Auto-corrections
            corrections = self._get_auto_corrections(new_content, cursor_pos)

            response_time = time.time() - start_time
            self._update_response_time(session['metrics'], response_time)

            return {
                'suggestions': immediate_suggestions,
                'corrections': corrections,
                'response_time': response_time,
                'session_metrics': asdict(session['metrics'])
            }

        except Exception as e:
            logger.error(f"Error handling text change in session {session_id}: {e}")
            return {'error': str(e)}

    async def _delayed_analysis(self, session_id: str, content: str, cursor_pos: int, section: str):
        """Perform delayed comprehensive analysis"""
        await asyncio.sleep(self.debounce_delay)

        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]

        try:
            # Get context for analysis
            context = {
                'domain': session['user_preferences'].get('domain', 'general'),
                'tech_stack': session['user_preferences'].get('tech_stack', []),
                'project_size': session['user_preferences'].get('project_size', 'medium'),
                'team_size': session['user_preferences'].get('team_size', 4),
                'timeline': session['user_preferences'].get('timeline', '4-weeks'),
                'constraints': session['user_preferences'].get('constraints', [])
            }

            # Perform comprehensive analysis
            analysis = await self.adaptive_engine.analyze_specification_realtime(content, context)
            session['metrics'].analysis_requests += 1

            # Generate advanced suggestions based on analysis
            advanced_suggestions = await self._generate_advanced_suggestions(
                content, cursor_pos, analysis, session['context']
            )

            # Cache results for immediate retrieval
            self.suggestion_cache[session_id] = {
                'analysis': analysis,
                'suggestions': advanced_suggestions,
                'timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Error in delayed analysis for session {session_id}: {e}")

    async def _get_immediate_suggestions(self, content: str, cursor_pos: int, selected_text: str,
                                       section: str, context: EditingContext) -> List[EditingSuggestion]:
        """Get immediate suggestions based on current edit"""
        suggestions = []

        # Pattern-based suggestions
        for pattern_type, patterns in self.editing_patterns.items():
            if section in pattern_type or pattern_type == 'general':
                for pattern_info in patterns:
                    if re.search(pattern_info['trigger'], content.lower()):
                        suggestions.append(EditingSuggestion(
                            type='enhancement',
                            text=pattern_info['suggestion'],
                            position=cursor_pos,
                            replacement_length=0,
                            confidence=0.8,
                            category=pattern_info['category'],
                            explanation=f"Pattern detected: {pattern_info['trigger']}",
                            action='insert'
                        ))

        # Context-aware suggestions
        if cursor_pos > 0:
            context_suggestions = await self._get_contextual_suggestions(
                content, cursor_pos, section, context
            )
            suggestions.extend(context_suggestions)

        # Filter and sort suggestions
        filtered_suggestions = [s for s in suggestions if s.confidence >= self.suggestion_threshold]
        filtered_suggestions.sort(key=lambda x: x.confidence, reverse=True)

        return filtered_suggestions[:self.max_suggestions]

    async def _get_contextual_suggestions(self, content: str, cursor_pos: int,
                                        section: str, context: EditingContext) -> List[EditingSuggestion]:
        """Get suggestions based on current context"""
        suggestions = []

        # Get text around cursor
        start = max(0, cursor_pos - 50)
        end = min(len(content), cursor_pos + 50)
        surrounding_text = content[start:end].lower()

        # Section-specific suggestions
        if section == 'requirements':
            if not re.search(r'\b(?:must|should|shall|will)\b', surrounding_text):
                suggestions.append(EditingSuggestion(
                    type='enhancement',
                    text='Consider using modal verbs (must, should, shall) to indicate requirement priority',
                    position=cursor_pos,
                    replacement_length=0,
                    confidence=0.7,
                    category='requirement_clarity',
                    explanation='Modal verbs improve requirement clarity',
                    action='insert'
                ))

        elif section == 'acceptance_criteria':
            if not re.search(r'\b(?:given|when|then)\b', surrounding_text):
                suggestions.append(EditingSuggestion(
                    type='enhancement',
                    text='Consider using Given-When-Then format for clearer acceptance criteria',
                    position=cursor_pos,
                    replacement_length=0,
                    confidence=0.8,
                    category='testing_format',
                    explanation='Given-When-Then format improves testability',
                    action='insert'
                ))

        elif section == 'tech_stack':
            # Suggest complementary technologies
            if 'react' in surrounding_text and 'typescript' not in content.lower():
                suggestions.append(EditingSuggestion(
                    type='completion',
                    text='TypeScript',
                    position=cursor_pos,
                    replacement_length=0,
                    confidence=0.9,
                    category='tech_completion',
                    explanation='TypeScript complements React development',
                    action='insert'
                ))

        return suggestions

    def _get_auto_corrections(self, content: str, cursor_pos: int) -> List[EditingSuggestion]:
        """Get auto-correction suggestions"""
        corrections = []

        # Find words around cursor that might need correction
        words = re.findall(r'\b\w+\b', content.lower())

        for word in words:
            if word in self.auto_correction:
                corrected = self.auto_correction[word]
                # Find position of word in content
                word_pattern = r'\b' + re.escape(word) + r'\b'
                matches = list(re.finditer(word_pattern, content, re.IGNORECASE))

                for match in matches:
                    if abs(match.start() - cursor_pos) <= 20:  # Near cursor
                        corrections.append(EditingSuggestion(
                            type='correction',
                            text=corrected,
                            position=match.start(),
                            replacement_length=len(word),
                            confidence=0.95,
                            category='spelling',
                            explanation=f'Auto-correct "{word}" to "{corrected}"',
                            action='replace'
                        ))

        return corrections

    async def _generate_advanced_suggestions(self, content: str, cursor_pos: int,
                                           analysis: RealTimeAnalysis,
                                           context: EditingContext) -> List[EditingSuggestion]:
        """Generate advanced suggestions based on comprehensive analysis"""
        suggestions = []

        # Suggestions based on analysis scores
        if analysis.clarity_score < 0.6:
            suggestions.append(EditingSuggestion(
                type='warning',
                text='Consider clarifying ambiguous terms and adding more specific details',
                position=cursor_pos,
                replacement_length=0,
                confidence=0.8,
                category='clarity',
                explanation=f'Clarity score: {analysis.clarity_score:.2f}',
                action='insert'
            ))

        if analysis.completeness_score < 0.6:
            suggestions.append(EditingSuggestion(
                type='enhancement',
                text='Add missing requirements or acceptance criteria',
                position=cursor_pos,
                replacement_length=0,
                confidence=0.7,
                category='completeness',
                explanation=f'Completeness score: {analysis.completeness_score:.2f}',
                action='insert'
            ))

        # Risk-based suggestions
        for risk in analysis.risk_factors:
            suggestions.append(EditingSuggestion(
                type='warning',
                text=f'Risk identified: {risk}',
                position=cursor_pos,
                replacement_length=0,
                confidence=0.8,
                category='risk',
                explanation='Based on risk analysis',
                action='insert'
            ))

        # Dependency suggestions
        for dep in analysis.dependencies_detected:
            suggestions.append(EditingSuggestion(
                type='enhancement',
                text=f'Consider dependency: {dep}',
                position=cursor_pos,
                replacement_length=0,
                confidence=0.6,
                category='dependency',
                explanation='Auto-detected dependency',
                action='insert'
            ))

        return suggestions

    async def accept_suggestion(self, session_id: str, suggestion_id: str) -> Dict[str, Any]:
        """Handle user accepting a suggestion"""
        if session_id not in self.active_sessions:
            return {'error': 'Invalid session ID'}

        session = self.active_sessions[session_id]
        session['metrics'].suggestions_accepted += 1

        # Learn from user acceptance
        await self.adaptive_engine.learn_from_feedback({
            'suggestion_helpful': True,
            'suggestion_id': suggestion_id,
            'session_id': session_id
        })

        return {'status': 'suggestion_accepted'}

    async def reject_suggestion(self, session_id: str, suggestion_id: str, reason: str = None) -> Dict[str, Any]:
        """Handle user rejecting a suggestion"""
        if session_id not in self.active_sessions:
            return {'error': 'Invalid session ID'}

        # Learn from user rejection
        await self.adaptive_engine.learn_from_feedback({
            'suggestion_helpful': False,
            'suggestion_id': suggestion_id,
            'rejection_reason': reason,
            'session_id': session_id
        })

        return {'status': 'suggestion_rejected'}

    async def get_cached_analysis(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis results"""
        if session_id in self.suggestion_cache:
            cache_entry = self.suggestion_cache[session_id]
            # Check if cache is still valid (within 5 seconds)
            if time.time() - cache_entry['timestamp'] < 5.0:
                return cache_entry
        return None

    def _update_response_time(self, metrics: EditingMetrics, response_time: float):
        """Update average response time metric"""
        total_requests = metrics.analysis_requests + 1
        metrics.avg_response_time = (
            (metrics.avg_response_time * metrics.analysis_requests + response_time) / total_requests
        )

    async def end_editing_session(self, session_id: str, user_satisfaction: float = None) -> Dict[str, Any]:
        """End editing session and return summary"""
        if session_id not in self.active_sessions:
            return {'error': 'Invalid session ID'}

        session = self.active_sessions[session_id]
        session['metrics'].user_satisfaction = user_satisfaction

        # Calculate final metrics
        session_duration = (datetime.now() - session['metrics'].session_start).total_seconds()
        acceptance_rate = (
            session['metrics'].suggestions_accepted / session['metrics'].suggestions_offered
            if session['metrics'].suggestions_offered > 0 else 0.0
        )

        summary = {
            'session_duration': session_duration,
            'total_edits': session['metrics'].total_edits,
            'suggestions_offered': session['metrics'].suggestions_offered,
            'suggestions_accepted': session['metrics'].suggestions_accepted,
            'acceptance_rate': acceptance_rate,
            'avg_response_time': session['metrics'].avg_response_time,
            'user_satisfaction': user_satisfaction,
            'final_content_length': session['context'].document_length
        }

        # Clean up session
        del self.active_sessions[session_id]
        if session_id in self.suggestion_cache:
            del self.suggestion_cache[session_id]

        logger.info(f"Ended editing session {session_id} with summary: {summary}")
        return summary

    def get_editor_metrics(self) -> Dict[str, Any]:
        """Get overall editor metrics"""
        active_sessions_count = len(self.active_sessions)
        cache_size = len(self.suggestion_cache)

        return {
            'active_sessions': active_sessions_count,
            'cache_size': cache_size,
            'total_patterns': sum(len(patterns) for patterns in self.editing_patterns.values()),
            'auto_corrections': len(self.auto_correction),
            'debounce_delay': self.debounce_delay,
            'max_suggestions': self.max_suggestions,
            'suggestion_threshold': self.suggestion_threshold
        }