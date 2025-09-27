"""
TORQ Console Spec-Kit Engine - Core specification-driven development engine
Integrates GitHub Spec-Kit patterns with Enhanced RL System
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from .rl_spec_analyzer import RLSpecAnalyzer, SpecAnalysis, SpecificationContext
from .adaptive_intelligence import AdaptiveIntelligenceEngine
from .realtime_editor import RealTimeEditor

@dataclass
class ProjectConstitution:
    """Project constitution defining core principles and constraints"""
    name: str
    purpose: str
    principles: List[str]
    constraints: List[str]
    success_criteria: List[str]
    stakeholders: List[str]
    created_at: str
    updated_at: str

@dataclass
class Specification:
    """Detailed specification for a project component"""
    id: str
    title: str
    description: str
    requirements: List[str]
    acceptance_criteria: List[str]
    dependencies: List[str]
    tech_stack: List[str]
    timeline: str
    complexity: str
    priority: str
    status: str
    analysis: Optional[SpecAnalysis] = None
    created_at: str = ""
    updated_at: str = ""

@dataclass
class TaskPlan:
    """Implementation plan with specific tasks"""
    spec_id: str
    tasks: List[Dict[str, Any]]
    milestones: List[Dict[str, Any]]
    resource_requirements: Dict[str, Any]
    risk_mitigation: List[str]
    created_at: str
    updated_at: str

class SpecKitEngine:
    """Core engine for spec-driven development following GitHub Spec-Kit patterns"""

    def __init__(self, workspace_path: str = None, enhanced_rl_system=None):
        self.logger = logging.getLogger("TORQ.SpecKit.Engine")
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self.spec_dir = self.workspace_path / ".torq-specs"
        self.enhanced_rl_system = enhanced_rl_system

        # Initialize components
        self.rl_analyzer = RLSpecAnalyzer(enhanced_rl_system)

        # Phase 2: Adaptive Intelligence Layer
        self.adaptive_intelligence = AdaptiveIntelligenceEngine(self.rl_analyzer)
        self.realtime_editor = RealTimeEditor(self.adaptive_intelligence)

        self.constitutions = {}
        self.specifications = {}
        self.task_plans = {}

        # Ensure spec directory exists
        self.spec_dir.mkdir(exist_ok=True)

        self.logger.info(f"Initialized SpecKit Engine at {self.workspace_path}")

    async def initialize(self):
        """Initialize the Spec-Kit Engine"""
        try:
            await self._load_existing_specs()
            self.logger.info("SpecKit Engine initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize SpecKit Engine: {e}")

    async def _load_existing_specs(self):
        """Load existing specifications from workspace"""
        try:
            # Load constitutions
            const_file = self.spec_dir / "constitutions.json"
            if const_file.exists():
                with open(const_file, 'r', encoding='utf-8') as f:
                    const_data = json.load(f)
                    self.constitutions = {
                        name: ProjectConstitution(**data)
                        for name, data in const_data.items()
                    }

            # Load specifications
            spec_file = self.spec_dir / "specifications.json"
            if spec_file.exists():
                with open(spec_file, 'r', encoding='utf-8') as f:
                    spec_data = json.load(f)
                    self.specifications = {
                        spec_id: Specification(**data)
                        for spec_id, data in spec_data.items()
                    }

            # Load task plans
            plan_file = self.spec_dir / "task_plans.json"
            if plan_file.exists():
                with open(plan_file, 'r', encoding='utf-8') as f:
                    plan_data = json.load(f)
                    self.task_plans = {
                        spec_id: TaskPlan(**data)
                        for spec_id, data in plan_data.items()
                    }

            self.logger.info(f"Loaded {len(self.constitutions)} constitutions, "
                           f"{len(self.specifications)} specifications, "
                           f"{len(self.task_plans)} task plans")

        except Exception as e:
            self.logger.error(f"Failed to load existing specs: {e}")

    async def create_constitution(self, name: str, purpose: str, principles: List[str],
                                constraints: List[str], success_criteria: List[str],
                                stakeholders: List[str]) -> ProjectConstitution:
        """Create a new project constitution"""
        try:
            constitution = ProjectConstitution(
                name=name,
                purpose=purpose,
                principles=principles,
                constraints=constraints,
                success_criteria=success_criteria,
                stakeholders=stakeholders,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )

            self.constitutions[name] = constitution
            await self._save_constitutions()

            self.logger.info(f"Created constitution: {name}")
            return constitution

        except Exception as e:
            self.logger.error(f"Failed to create constitution: {e}")
            raise

    async def create_specification(self, title: str, description: str,
                                 requirements: List[str], acceptance_criteria: List[str],
                                 dependencies: List[str], tech_stack: List[str],
                                 timeline: str, complexity: str, priority: str,
                                 constitution_name: str = None) -> Specification:
        """Create a new specification with RL-powered analysis"""
        try:
            spec_id = f"spec_{len(self.specifications) + 1:04d}"

            # Create specification context for analysis
            context = SpecificationContext(
                domain=self._infer_domain(tech_stack),
                tech_stack=tech_stack,
                project_size=complexity,
                team_size=self._estimate_team_size(complexity),
                timeline=timeline,
                constraints=dependencies
            )

            # Perform RL-powered analysis
            spec_text = f"{title}\\n{description}\\n" + "\\n".join(requirements)
            analysis = await self.rl_analyzer.analyze_specification(spec_text, context)

            specification = Specification(
                id=spec_id,
                title=title,
                description=description,
                requirements=requirements,
                acceptance_criteria=acceptance_criteria,
                dependencies=dependencies,
                tech_stack=tech_stack,
                timeline=timeline,
                complexity=complexity,
                priority=priority,
                status="draft",
                analysis=analysis,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )

            self.specifications[spec_id] = specification
            await self._save_specifications()

            self.logger.info(f"Created specification: {spec_id} - {title}")
            return specification

        except Exception as e:
            self.logger.error(f"Failed to create specification: {e}")
            raise

    async def generate_task_plan(self, spec_id: str) -> TaskPlan:
        """Generate implementation plan for a specification"""
        try:
            if spec_id not in self.specifications:
                raise ValueError(f"Specification {spec_id} not found")

            spec = self.specifications[spec_id]

            # Generate tasks based on specification
            tasks = await self._generate_tasks_from_spec(spec)
            milestones = await self._generate_milestones(spec, tasks)
            resource_requirements = await self._estimate_resources(spec)
            risk_mitigation = await self._generate_risk_mitigation(spec)

            task_plan = TaskPlan(
                spec_id=spec_id,
                tasks=tasks,
                milestones=milestones,
                resource_requirements=resource_requirements,
                risk_mitigation=risk_mitigation,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )

            self.task_plans[spec_id] = task_plan
            await self._save_task_plans()

            self.logger.info(f"Generated task plan for specification: {spec_id}")
            return task_plan

        except Exception as e:
            self.logger.error(f"Failed to generate task plan: {e}")
            raise

    async def _generate_tasks_from_spec(self, spec: Specification) -> List[Dict[str, Any]]:
        """Generate implementation tasks from specification"""
        tasks = []

        # Setup and planning tasks
        tasks.append({
            "id": f"task_{len(tasks) + 1:03d}",
            "title": "Project Setup and Environment Configuration",
            "description": "Set up development environment and project structure",
            "type": "setup",
            "priority": "high",
            "estimated_hours": 4,
            "dependencies": [],
            "status": "pending"
        })

        # Technical implementation tasks based on tech stack
        for tech in spec.tech_stack:
            tasks.append({
                "id": f"task_{len(tasks) + 1:03d}",
                "title": f"Implement {tech} Components",
                "description": f"Develop core functionality using {tech}",
                "type": "implementation",
                "priority": "high",
                "estimated_hours": self._estimate_tech_hours(tech, spec.complexity),
                "dependencies": [tasks[0]["id"]] if tasks else [],
                "status": "pending"
            })

        # Testing tasks
        tasks.append({
            "id": f"task_{len(tasks) + 1:03d}",
            "title": "Implement Test Suite",
            "description": "Create comprehensive test coverage",
            "type": "testing",
            "priority": "medium",
            "estimated_hours": 8,
            "dependencies": [t["id"] for t in tasks if t["type"] == "implementation"],
            "status": "pending"
        })

        # Documentation tasks
        tasks.append({
            "id": f"task_{len(tasks) + 1:03d}",
            "title": "Create Documentation",
            "description": "Write user and developer documentation",
            "type": "documentation",
            "priority": "medium",
            "estimated_hours": 6,
            "dependencies": [t["id"] for t in tasks if t["type"] == "implementation"],
            "status": "pending"
        })

        return tasks

    async def _generate_milestones(self, spec: Specification, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate project milestones"""
        milestones = []

        # Setup milestone
        setup_tasks = [t for t in tasks if t["type"] == "setup"]
        if setup_tasks:
            milestones.append({
                "id": "milestone_001",
                "title": "Development Environment Ready",
                "description": "All setup and configuration completed",
                "tasks": [t["id"] for t in setup_tasks],
                "target_date": self._calculate_milestone_date(setup_tasks),
                "status": "pending"
            })

        # Implementation milestone
        impl_tasks = [t for t in tasks if t["type"] == "implementation"]
        if impl_tasks:
            milestones.append({
                "id": "milestone_002",
                "title": "Core Features Implemented",
                "description": "All core functionality completed",
                "tasks": [t["id"] for t in impl_tasks],
                "target_date": self._calculate_milestone_date(impl_tasks),
                "status": "pending"
            })

        # Testing milestone
        test_tasks = [t for t in tasks if t["type"] == "testing"]
        if test_tasks:
            milestones.append({
                "id": "milestone_003",
                "title": "Testing Completed",
                "description": "All tests passing and coverage targets met",
                "tasks": [t["id"] for t in test_tasks],
                "target_date": self._calculate_milestone_date(test_tasks),
                "status": "pending"
            })

        return milestones

    async def _estimate_resources(self, spec: Specification) -> Dict[str, Any]:
        """Estimate resource requirements"""
        complexity_multipliers = {
            "small": 1.0,
            "medium": 2.0,
            "large": 4.0,
            "enterprise": 8.0
        }

        base_hours = 40
        multiplier = complexity_multipliers.get(spec.complexity, 2.0)
        tech_multiplier = len(spec.tech_stack) * 0.5 + 1.0

        total_hours = int(base_hours * multiplier * tech_multiplier)

        return {
            "estimated_total_hours": total_hours,
            "recommended_team_size": self._estimate_team_size(spec.complexity),
            "estimated_duration_weeks": max(1, total_hours // (40 * self._estimate_team_size(spec.complexity))),
            "budget_estimate": total_hours * 100,  # $100/hour estimate
            "required_skills": spec.tech_stack + ["testing", "documentation"]
        }

    async def _generate_risk_mitigation(self, spec: Specification) -> List[str]:
        """Generate risk mitigation strategies"""
        risks = []

        if spec.analysis and spec.analysis.risk_assessment:
            for risk_type, risk_level in spec.analysis.risk_assessment.items():
                if risk_level > 0.7:
                    if risk_type == "technical_risk":
                        risks.append("Conduct technical proof-of-concept early")
                    elif risk_type == "scope_risk":
                        risks.append("Define clear scope boundaries and change control process")
                    elif risk_type == "timeline_risk":
                        risks.append("Build buffer time into schedule and consider MVP approach")
                    elif risk_type == "quality_risk":
                        risks.append("Implement continuous integration and automated testing")

        # Add general mitigation strategies
        risks.extend([
            "Regular stakeholder communication and progress reviews",
            "Iterative development with frequent demos",
            "Maintain comprehensive documentation",
            "Plan for technical debt management"
        ])

        return risks

    def _infer_domain(self, tech_stack: List[str]) -> str:
        """Infer project domain from tech stack"""
        web_indicators = {"react", "vue", "angular", "javascript", "html", "css"}
        backend_indicators = {"python", "java", "node", "go", "rust", "ruby"}
        mobile_indicators = {"react-native", "flutter", "ios", "android", "swift", "kotlin"}
        data_indicators = {"tensorflow", "pytorch", "pandas", "numpy", "sql", "mongodb"}

        tech_lower = [tech.lower() for tech in tech_stack]

        if any(tech in mobile_indicators for tech in tech_lower):
            return "mobile"
        elif any(tech in data_indicators for tech in tech_lower):
            return "data_science"
        elif any(tech in web_indicators for tech in tech_lower):
            return "web"
        elif any(tech in backend_indicators for tech in tech_lower):
            return "backend"
        else:
            return "general"

    def _estimate_team_size(self, complexity: str) -> int:
        """Estimate required team size based on complexity"""
        team_sizes = {
            "small": 2,
            "medium": 4,
            "large": 8,
            "enterprise": 12
        }
        return team_sizes.get(complexity, 4)

    def _estimate_tech_hours(self, tech: str, complexity: str) -> int:
        """Estimate implementation hours for a technology"""
        base_hours = {
            "small": 8,
            "medium": 16,
            "large": 32,
            "enterprise": 64
        }

        tech_multipliers = {
            "react": 1.2,
            "vue": 1.1,
            "angular": 1.5,
            "python": 1.0,
            "java": 1.3,
            "javascript": 1.0,
            "typescript": 1.1,
            "database": 1.4,
            "api": 1.2
        }

        base = base_hours.get(complexity, 16)
        multiplier = tech_multipliers.get(tech.lower(), 1.0)

        return int(base * multiplier)

    def _calculate_milestone_date(self, tasks: List[Dict[str, Any]]) -> str:
        """Calculate target date for milestone based on tasks"""
        total_hours = sum(task.get("estimated_hours", 8) for task in tasks)
        weeks = max(1, total_hours // 40)  # Assuming 40 hours per week

        from datetime import datetime, timedelta
        target_date = datetime.now() + timedelta(weeks=weeks)
        return target_date.isoformat()

    async def _save_constitutions(self):
        """Save constitutions to file"""
        try:
            const_file = self.spec_dir / "constitutions.json"
            with open(const_file, 'w', encoding='utf-8') as f:
                json.dump({
                    name: asdict(const) for name, const in self.constitutions.items()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save constitutions: {e}")

    async def _save_specifications(self):
        """Save specifications to file"""
        try:
            spec_file = self.spec_dir / "specifications.json"
            spec_data = {}
            for spec_id, spec in self.specifications.items():
                spec_dict = asdict(spec)
                # Handle SpecAnalysis serialization
                if spec_dict.get('analysis') and hasattr(spec_dict['analysis'], '__dict__'):
                    try:
                        spec_dict['analysis'] = asdict(spec_dict['analysis'])
                    except:
                        # Fallback to manual conversion if asdict fails
                        analysis = spec_dict['analysis']
                        spec_dict['analysis'] = {
                            'clarity_score': getattr(analysis, 'clarity_score', 0.0),
                            'completeness_score': getattr(analysis, 'completeness_score', 0.0),
                            'feasibility_score': getattr(analysis, 'feasibility_score', 0.0),
                            'complexity_score': getattr(analysis, 'complexity_score', 0.0),
                            'risk_assessment': getattr(analysis, 'risk_assessment', {}),
                            'recommendations': getattr(analysis, 'recommendations', []),
                            'confidence': getattr(analysis, 'confidence', 0.0)
                        }
                spec_data[spec_id] = spec_dict

            with open(spec_file, 'w', encoding='utf-8') as f:
                json.dump(spec_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save specifications: {e}")

    async def _save_task_plans(self):
        """Save task plans to file"""
        try:
            plan_file = self.spec_dir / "task_plans.json"
            with open(plan_file, 'w', encoding='utf-8') as f:
                json.dump({
                    spec_id: asdict(plan) for spec_id, plan in self.task_plans.items()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save task plans: {e}")

    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status summary"""
        return {
            "constitutions": len(self.constitutions),
            "specifications": len(self.specifications),
            "task_plans": len(self.task_plans),
            "workspace_path": str(self.workspace_path),
            "spec_directory": str(self.spec_dir),
            "rl_analyzer_active": self.enhanced_rl_system is not None,
            "recent_specs": [
                {"id": spec.id, "title": spec.title, "status": spec.status}
                for spec in list(self.specifications.values())[-5:]
            ]
        }

    async def update_specification_status(self, spec_id: str, new_status: str, feedback: Dict[str, Any] = None):
        """Update specification status and learn from feedback"""
        try:
            if spec_id not in self.specifications:
                raise ValueError(f"Specification {spec_id} not found")

            spec = self.specifications[spec_id]
            spec.status = new_status
            spec.updated_at = datetime.now().isoformat()

            # Learn from feedback if provided
            if feedback and spec.analysis:
                await self.rl_analyzer.learn_from_feedback(spec.analysis, feedback)

            await self._save_specifications()
            self.logger.info(f"Updated specification {spec_id} status to {new_status}")

        except Exception as e:
            self.logger.error(f"Failed to update specification status: {e}")
            raise

    def search_specifications(self, query: str, filters: Dict[str, Any] = None) -> List[Specification]:
        """Search specifications by title, description, or requirements"""
        results = []
        query_lower = query.lower()

        for spec in self.specifications.values():
            # Text search
            if (query_lower in spec.title.lower() or
                query_lower in spec.description.lower() or
                any(query_lower in req.lower() for req in spec.requirements)):

                # Apply filters if provided
                if filters:
                    if filters.get('status') and spec.status != filters['status']:
                        continue
                    if filters.get('complexity') and spec.complexity != filters['complexity']:
                        continue
                    if filters.get('priority') and spec.priority != filters['priority']:
                        continue

                results.append(spec)

        return results

    # ============================================================================
    # PHASE 2: ADAPTIVE INTELLIGENCE LAYER METHODS
    # ============================================================================

    async def start_realtime_editing(self, spec_id: str, initial_content: str, user_prefs: Dict[str, Any]) -> str:
        """Start real-time editing session for a specification"""
        try:
            session_id = await self.realtime_editor.start_editing_session(
                spec_id, initial_content, user_prefs
            )
            self.logger.info(f"Started real-time editing session {session_id} for spec {spec_id}")
            return session_id
        except Exception as e:
            self.logger.error(f"Failed to start real-time editing: {e}")
            raise

    async def handle_realtime_edit(self, session_id: str, new_content: str, cursor_pos: int,
                                 selected_text: str = "", section: str = "description") -> Dict[str, Any]:
        """Handle real-time text changes and get intelligent suggestions"""
        try:
            return await self.realtime_editor.handle_text_change(
                session_id, new_content, cursor_pos, selected_text, section
            )
        except Exception as e:
            self.logger.error(f"Failed to handle real-time edit: {e}")
            return {'error': str(e)}

    async def get_realtime_analysis(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached real-time analysis results"""
        try:
            return await self.realtime_editor.get_cached_analysis(session_id)
        except Exception as e:
            self.logger.error(f"Failed to get real-time analysis: {e}")
            return None

    async def accept_editing_suggestion(self, session_id: str, suggestion_id: str) -> Dict[str, Any]:
        """Accept a real-time editing suggestion"""
        try:
            return await self.realtime_editor.accept_suggestion(session_id, suggestion_id)
        except Exception as e:
            self.logger.error(f"Failed to accept suggestion: {e}")
            return {'error': str(e)}

    async def reject_editing_suggestion(self, session_id: str, suggestion_id: str, reason: str = None) -> Dict[str, Any]:
        """Reject a real-time editing suggestion"""
        try:
            return await self.realtime_editor.reject_suggestion(session_id, suggestion_id, reason)
        except Exception as e:
            self.logger.error(f"Failed to reject suggestion: {e}")
            return {'error': str(e)}

    async def end_realtime_editing(self, session_id: str, user_satisfaction: float = None) -> Dict[str, Any]:
        """End real-time editing session and get summary"""
        try:
            summary = await self.realtime_editor.end_editing_session(session_id, user_satisfaction)
            self.logger.info(f"Ended real-time editing session {session_id}")
            return summary
        except Exception as e:
            self.logger.error(f"Failed to end real-time editing: {e}")
            return {'error': str(e)}

    async def analyze_specification_realtime(self, spec_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform real-time analysis of specification text"""
        try:
            analysis = await self.adaptive_intelligence.analyze_specification_realtime(spec_text, context)
            return asdict(analysis)
        except Exception as e:
            self.logger.error(f"Failed real-time analysis: {e}")
            raise

    async def learn_from_user_feedback(self, feedback: Dict[str, Any]):
        """Learn from user feedback to improve adaptive intelligence"""
        try:
            await self.adaptive_intelligence.learn_from_feedback(feedback)
            self.logger.info("Processed user feedback for adaptive learning")
        except Exception as e:
            self.logger.error(f"Failed to process user feedback: {e}")

    def get_adaptive_intelligence_metrics(self) -> Dict[str, Any]:
        """Get metrics from adaptive intelligence system"""
        try:
            ai_metrics = self.adaptive_intelligence.get_intelligence_metrics()
            editor_metrics = self.realtime_editor.get_editor_metrics()

            return {
                'adaptive_intelligence': ai_metrics,
                'realtime_editor': editor_metrics,
                'phase2_status': 'active'
            }
        except Exception as e:
            self.logger.error(f"Failed to get adaptive intelligence metrics: {e}")
            return {'phase2_status': 'error', 'error': str(e)}

    def get_enhanced_status_summary(self) -> Dict[str, Any]:
        """Get enhanced status summary including Phase 2 features"""
        base_status = self.get_status_summary()

        # Add Phase 2 metrics
        try:
            phase2_metrics = self.get_adaptive_intelligence_metrics()
            base_status['phase2_adaptive_intelligence'] = phase2_metrics
            base_status['realtime_editing_active'] = len(self.realtime_editor.active_sessions) > 0
            base_status['adaptive_learning_enabled'] = True
        except Exception as e:
            self.logger.error(f"Failed to get Phase 2 status: {e}")
            base_status['phase2_adaptive_intelligence'] = {'status': 'error', 'error': str(e)}
            base_status['realtime_editing_active'] = False
            base_status['adaptive_learning_enabled'] = False

        return base_status