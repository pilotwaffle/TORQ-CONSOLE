"""
TORQ Console Spec-Kit Command Interface
Implements /torq-spec commands: /constitution, /specify, /plan, /tasks, /implement
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from .spec_engine import SpecKitEngine, ProjectConstitution, Specification, TaskPlan

class SpecKitCommands:
    """Command interface for TORQ Console Spec-Kit integration"""

    def __init__(self, spec_engine: SpecKitEngine):
        self.logger = logging.getLogger("TORQ.SpecKit.Commands")
        self.spec_engine = spec_engine

    async def handle_torq_spec_command(self, subcommand: str, args: List[str]) -> str:
        """Handle /torq-spec subcommands"""
        try:
            if subcommand == "constitution":
                return await self._handle_constitution(args)
            elif subcommand == "specify":
                return await self._handle_specify(args)
            elif subcommand == "plan":
                return await self._handle_plan(args)
            elif subcommand == "tasks":
                return await self._handle_tasks(args)
            elif subcommand == "implement":
                return await self._handle_implement(args)
            elif subcommand == "status":
                return await self._handle_status(args)
            elif subcommand == "list":
                return await self._handle_list(args)
            elif subcommand == "search":
                return await self._handle_search(args)
            elif subcommand == "export":
                return await self._handle_export(args)
            else:
                return self._help()
        except Exception as e:
            self.logger.error(f"Command error: {e}")
            return f"ERROR Failed to execute command: {e}"

    async def _handle_constitution(self, args: List[str]) -> str:
        """Handle constitution creation and management"""
        if not args:
            return self._constitution_help()

        action = args[0]

        if action == "create":
            return await self._create_constitution(args[1:])
        elif action == "list":
            return await self._list_constitutions()
        elif action == "show":
            return await self._show_constitution(args[1:])
        elif action == "update":
            return await self._update_constitution(args[1:])
        else:
            return self._constitution_help()

    async def _create_constitution(self, args: List[str]) -> str:
        """Create a new project constitution"""
        if len(args) < 2:
            return "Usage: /torq-spec constitution create <name> <purpose> [principles...] [--constraints=...] [--criteria=...] [--stakeholders=...]"

        name = args[0]
        purpose = args[1]

        # Parse optional arguments
        principles = []
        constraints = []
        success_criteria = []
        stakeholders = []

        # Simple parsing - in real implementation, use proper argument parser
        for i, arg in enumerate(args[2:], 2):
            if arg.startswith("--constraints="):
                constraints = arg[13:].split(",")
            elif arg.startswith("--criteria="):
                success_criteria = arg[11:].split(",")
            elif arg.startswith("--stakeholders="):
                stakeholders = arg[15:].split(",")
            elif not arg.startswith("--"):
                principles.append(arg)

        # Set defaults if not provided
        if not principles:
            principles = ["Quality first", "User-centered design", "Maintainable code"]
        if not constraints:
            constraints = ["Budget limitations", "Time constraints", "Technical debt"]
        if not success_criteria:
            success_criteria = ["User satisfaction", "Performance targets", "Code quality metrics"]
        if not stakeholders:
            stakeholders = ["Development team", "Product owner", "End users"]

        try:
            constitution = await self.spec_engine.create_constitution(
                name=name,
                purpose=purpose,
                principles=principles,
                constraints=constraints,
                success_criteria=success_criteria,
                stakeholders=stakeholders
            )

            return f"""PASS Created constitution: {name}

Purpose: {purpose}

Principles:
{self._format_list(principles)}

Constraints:
{self._format_list(constraints)}

Success Criteria:
{self._format_list(success_criteria)}

Stakeholders:
{self._format_list(stakeholders)}"""

        except Exception as e:
            return f"FAIL Failed to create constitution: {e}"

    async def _list_constitutions(self) -> str:
        """List all constitutions"""
        constitutions = self.spec_engine.constitutions

        if not constitutions:
            return "No constitutions found. Use '/torq-spec constitution create' to create one."

        result = "Project Constitutions:\\n"
        for name, const in constitutions.items():
            result += f"\\n  • {name}\\n"
            result += f"    Purpose: {const.purpose}\\n"
            result += f"    Created: {const.created_at[:10]}\\n"

        return result

    async def _show_constitution(self, args: List[str]) -> str:
        """Show detailed constitution"""
        if not args:
            return "Usage: /torq-spec constitution show <name>"

        name = args[0]
        if name not in self.spec_engine.constitutions:
            return f"Constitution '{name}' not found"

        const = self.spec_engine.constitutions[name]

        return f"""Constitution: {const.name}

Purpose: {const.purpose}

Principles:
{self._format_list(const.principles)}

Constraints:
{self._format_list(const.constraints)}

Success Criteria:
{self._format_list(const.success_criteria)}

Stakeholders:
{self._format_list(const.stakeholders)}

Created: {const.created_at}
Updated: {const.updated_at}"""

    async def _handle_specify(self, args: List[str]) -> str:
        """Handle specification creation"""
        if not args:
            return self._specify_help()

        action = args[0]

        if action == "create":
            return await self._create_specification(args[1:])
        elif action == "list":
            return await self._list_specifications()
        elif action == "show":
            return await self._show_specification(args[1:])
        elif action == "update":
            return await self._update_specification(args[1:])
        elif action == "analyze":
            return await self._analyze_specification(args[1:])
        else:
            return self._specify_help()

    async def _create_specification(self, args: List[str]) -> str:
        """Create a new specification"""
        if len(args) < 2:
            return """Usage: /torq-spec specify create <title> <description>

Example: /torq-spec specify create "User Authentication" "Implement secure user login and registration system"

Optional flags:
  --requirements="req1,req2,req3"
  --acceptance="criteria1,criteria2"
  --dependencies="dep1,dep2"
  --tech="tech1,tech2,tech3"
  --timeline="2-weeks"
  --complexity="medium"
  --priority="high"
"""

        title = args[0]
        description = args[1]

        # Parse optional arguments
        requirements = ["User can register with email", "User can login securely", "Password reset functionality"]
        acceptance_criteria = ["All tests pass", "Security audit completed", "Performance benchmarks met"]
        dependencies = []
        tech_stack = ["python", "database", "api"]
        timeline = "2-weeks"
        complexity = "medium"
        priority = "medium"

        # Simple parsing for optional arguments
        for arg in args[2:]:
            if arg.startswith("--requirements="):
                requirements = arg[15:].split(",")
            elif arg.startswith("--acceptance="):
                acceptance_criteria = arg[13:].split(",")
            elif arg.startswith("--dependencies="):
                dependencies = arg[15:].split(",")
            elif arg.startswith("--tech="):
                tech_stack = arg[7:].split(",")
            elif arg.startswith("--timeline="):
                timeline = arg[11:]
            elif arg.startswith("--complexity="):
                complexity = arg[13:]
            elif arg.startswith("--priority="):
                priority = arg[11:]

        try:
            spec = await self.spec_engine.create_specification(
                title=title,
                description=description,
                requirements=requirements,
                acceptance_criteria=acceptance_criteria,
                dependencies=dependencies,
                tech_stack=tech_stack,
                timeline=timeline,
                complexity=complexity,
                priority=priority
            )

            result = f"""PASS Created specification: {spec.id} - {title}

Description: {description}

Requirements:
{self._format_list(requirements)}

Acceptance Criteria:
{self._format_list(acceptance_criteria)}

Tech Stack: {', '.join(tech_stack)}
Timeline: {timeline}
Complexity: {complexity}
Priority: {priority}"""

            # Add RL analysis results
            if spec.analysis:
                result += f"""

RL-Powered Analysis:
  Clarity Score: {spec.analysis.clarity_score:.2f}
  Completeness Score: {spec.analysis.completeness_score:.2f}
  Feasibility Score: {spec.analysis.feasibility_score:.2f}
  Complexity Score: {spec.analysis.complexity_score:.2f}
  Confidence: {spec.analysis.confidence:.2f}

Recommendations:
{self._format_list(spec.analysis.recommendations)}

Risk Assessment:
{self._format_dict(spec.analysis.risk_assessment)}"""

            return result

        except Exception as e:
            return f"FAIL Failed to create specification: {e}"

    async def _list_specifications(self) -> str:
        """List all specifications"""
        specs = self.spec_engine.specifications

        if not specs:
            return "No specifications found. Use '/torq-spec specify create' to create one."

        result = "Project Specifications:\\n"
        for spec_id, spec in specs.items():
            status_emoji = self._get_status_emoji(spec.status)
            result += f"\\n  {status_emoji} {spec_id}: {spec.title}\\n"
            result += f"    Status: {spec.status} | Priority: {spec.priority} | Complexity: {spec.complexity}\\n"
            if spec.analysis:
                result += f"    Feasibility: {spec.analysis.feasibility_score:.2f} | Clarity: {spec.analysis.clarity_score:.2f}\\n"

        return result

    async def _show_specification(self, args: List[str]) -> str:
        """Show detailed specification"""
        if not args:
            return "Usage: /torq-spec specify show <spec_id>"

        spec_id = args[0]
        if spec_id not in self.spec_engine.specifications:
            return f"Specification '{spec_id}' not found"

        spec = self.spec_engine.specifications[spec_id]

        result = f"""Specification: {spec.id} - {spec.title}

Description: {spec.description}

Status: {spec.status}
Priority: {spec.priority}
Complexity: {spec.complexity}
Timeline: {spec.timeline}

Requirements:
{self._format_list(spec.requirements)}

Acceptance Criteria:
{self._format_list(spec.acceptance_criteria)}

Tech Stack: {', '.join(spec.tech_stack)}
Dependencies: {', '.join(spec.dependencies) if spec.dependencies else 'None'}

Created: {spec.created_at}
Updated: {spec.updated_at}"""

        if spec.analysis:
            result += f"""

RL Analysis:
  Clarity: {spec.analysis.clarity_score:.2f}
  Completeness: {spec.analysis.completeness_score:.2f}
  Feasibility: {spec.analysis.feasibility_score:.2f}
  Complexity: {spec.analysis.complexity_score:.2f}
  Confidence: {spec.analysis.confidence:.2f}

Recommendations:
{self._format_list(spec.analysis.recommendations)}

Risk Assessment:
{self._format_dict(spec.analysis.risk_assessment)}"""

        return result

    async def _handle_plan(self, args: List[str]) -> str:
        """Handle task plan generation"""
        if not args:
            return self._plan_help()

        action = args[0]

        if action == "generate":
            return await self._generate_plan(args[1:])
        elif action == "show":
            return await self._show_plan(args[1:])
        elif action == "list":
            return await self._list_plans()
        else:
            return self._plan_help()

    async def _generate_plan(self, args: List[str]) -> str:
        """Generate implementation plan for specification"""
        if not args:
            return "Usage: /torq-spec plan generate <spec_id>"

        spec_id = args[0]
        if spec_id not in self.spec_engine.specifications:
            return f"Specification '{spec_id}' not found"

        try:
            plan = await self.spec_engine.generate_task_plan(spec_id)
            spec = self.spec_engine.specifications[spec_id]

            result = f"""PASS Generated implementation plan for: {spec.title}

Estimated Resources:
  Total Hours: {plan.resource_requirements.get('estimated_total_hours', 'TBD')}
  Team Size: {plan.resource_requirements.get('recommended_team_size', 'TBD')}
  Duration: {plan.resource_requirements.get('estimated_duration_weeks', 'TBD')} weeks
  Budget: ${plan.resource_requirements.get('budget_estimate', 'TBD'):,}

Tasks ({len(plan.tasks)} total):"""

            for task in plan.tasks:
                result += f"""
  • {task['title']} ({task['type']})
    Priority: {task['priority']} | Est. Hours: {task['estimated_hours']}
    Dependencies: {', '.join(task['dependencies']) if task['dependencies'] else 'None'}"""

            result += f"""

Milestones ({len(plan.milestones)} total):"""

            for milestone in plan.milestones:
                result += f"""
  • {milestone['title']}
    Target: {milestone['target_date'][:10]}
    Tasks: {len(milestone['tasks'])} tasks"""

            result += f"""

Risk Mitigation:
{self._format_list(plan.risk_mitigation)}"""

            return result

        except Exception as e:
            return f"FAIL Failed to generate plan: {e}"

    async def _handle_tasks(self, args: List[str]) -> str:
        """Handle task management"""
        if not args:
            return self._tasks_help()

        action = args[0]

        if action == "list":
            return await self._list_tasks(args[1:])
        elif action == "show":
            return await self._show_task(args[1:])
        elif action == "update":
            return await self._update_task(args[1:])
        else:
            return self._tasks_help()

    async def _list_tasks(self, args: List[str]) -> str:
        """List tasks for a specification"""
        if not args:
            return "Usage: /torq-spec tasks list <spec_id>"

        spec_id = args[0]
        if spec_id not in self.spec_engine.task_plans:
            return f"No task plan found for specification '{spec_id}'"

        plan = self.spec_engine.task_plans[spec_id]
        spec = self.spec_engine.specifications[spec_id]

        result = f"Tasks for: {spec.title}\\n"

        for task in plan.tasks:
            status_emoji = self._get_task_status_emoji(task['status'])
            result += f"\\n  {status_emoji} {task['id']}: {task['title']}\\n"
            result += f"    Type: {task['type']} | Priority: {task['priority']} | Hours: {task['estimated_hours']}\\n"
            result += f"    Status: {task['status']}\\n"

        return result

    async def _handle_implement(self, args: List[str]) -> str:
        """Handle implementation assistance"""
        if not args:
            return self._implement_help()

        action = args[0]

        if action == "start":
            return await self._start_implementation(args[1:])
        elif action == "status":
            return await self._implementation_status(args[1:])
        elif action == "complete":
            return await self._complete_implementation(args[1:])
        else:
            return self._implement_help()

    async def _start_implementation(self, args: List[str]) -> str:
        """Start implementation of a specification"""
        if not args:
            return "Usage: /torq-spec implement start <spec_id>"

        spec_id = args[0]
        if spec_id not in self.spec_engine.specifications:
            return f"Specification '{spec_id}' not found"

        try:
            await self.spec_engine.update_specification_status(spec_id, "in_progress")
            spec = self.spec_engine.specifications[spec_id]

            return f"""PASS Started implementation: {spec.title}

Status: {spec.status}

Next Steps:
1. Set up development environment
2. Review specification and acceptance criteria
3. Begin with highest priority tasks
4. Implement iteratively with regular testing

Use '/torq-spec tasks list {spec_id}' to see implementation tasks."""

        except Exception as e:
            return f"FAIL Failed to start implementation: {e}"

    async def _handle_status(self, args: List[str]) -> str:
        """Show overall status"""
        status = self.spec_engine.get_status_summary()

        result = f"""TORQ Console Spec-Kit Status

Workspace: {status['workspace_path']}
Spec Directory: {status['spec_directory']}

Summary:
  Constitutions: {status['constitutions']}
  Specifications: {status['specifications']}
  Task Plans: {status['task_plans']}
  RL Analyzer: {'Active' if status['rl_analyzer_active'] else 'Heuristic Mode'}

Recent Specifications:"""

        for spec in status['recent_specs']:
            status_emoji = self._get_status_emoji(spec['status'])
            result += f"\\n  {status_emoji} {spec['id']}: {spec['title']} ({spec['status']})"

        return result

    async def _handle_search(self, args: List[str]) -> str:
        """Search specifications"""
        if not args:
            return "Usage: /torq-spec search <query> [--status=<status>] [--complexity=<complexity>]"

        query = args[0]
        filters = {}

        # Parse filters
        for arg in args[1:]:
            if arg.startswith("--status="):
                filters['status'] = arg[9:]
            elif arg.startswith("--complexity="):
                filters['complexity'] = arg[13:]
            elif arg.startswith("--priority="):
                filters['priority'] = arg[11:]

        results = self.spec_engine.search_specifications(query, filters)

        if not results:
            return f"No specifications found matching '{query}'"

        result = f"Search Results for '{query}' ({len(results)} found):\\n"

        for spec in results:
            status_emoji = self._get_status_emoji(spec.status)
            result += f"\\n  {status_emoji} {spec.id}: {spec.title}\\n"
            result += f"    {spec.description[:100]}{'...' if len(spec.description) > 100 else ''}\\n"
            result += f"    Status: {spec.status} | Priority: {spec.priority} | Complexity: {spec.complexity}\\n"

        return result

    def _format_list(self, items: List[str]) -> str:
        """Format list with bullet points"""
        return "\\n".join(f"  • {item}" for item in items)

    def _format_dict(self, data: Dict[str, Any]) -> str:
        """Format dictionary as key-value pairs"""
        return "\\n".join(f"  • {key}: {value:.2f}" if isinstance(value, float) else f"  • {key}: {value}"
                         for key, value in data.items())

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status"""
        status_emojis = {
            "draft": "DRAFT",
            "active": "ACTIVE",
            "in_progress": "PROGRESS",
            "completed": "DONE",
            "on_hold": "HOLD",
            "cancelled": "CANCEL"
        }
        return status_emojis.get(status, "UNKNOWN")

    def _get_task_status_emoji(self, status: str) -> str:
        """Get emoji for task status"""
        task_emojis = {
            "pending": "PENDING",
            "in_progress": "WORKING",
            "completed": "DONE",
            "blocked": "BLOCKED"
        }
        return task_emojis.get(status, "UNKNOWN")

    def _constitution_help(self) -> str:
        """Constitution command help"""
        return """TORQ Console Spec-Kit Constitution Commands:

/torq-spec constitution create <name> <purpose> [principles...] [options]
  Create a new project constitution
  Options:
    --constraints="constraint1,constraint2,..."
    --criteria="criteria1,criteria2,..."
    --stakeholders="stakeholder1,stakeholder2,..."

/torq-spec constitution list
  List all constitutions

/torq-spec constitution show <name>
  Show detailed constitution

/torq-spec constitution update <name> [options]
  Update existing constitution

Example:
  /torq-spec constitution create "MyApp" "Build the best task management app" \\
    "User-first design" "Quality code" \\
    --constraints="Budget 50k,Timeline 3 months" \\
    --criteria="1000 users,4.5 rating" \\
    --stakeholders="Developers,Users,PM"
"""

    def _specify_help(self) -> str:
        """Specification command help"""
        return """TORQ Console Spec-Kit Specification Commands:

/torq-spec specify create <title> <description> [options]
  Create a new specification with RL-powered analysis
  Options:
    --requirements="req1,req2,..."
    --acceptance="criteria1,criteria2,..."
    --dependencies="dep1,dep2,..."
    --tech="tech1,tech2,..."
    --timeline="duration"
    --complexity="small|medium|large|enterprise"
    --priority="low|medium|high"

/torq-spec specify list
  List all specifications

/torq-spec specify show <spec_id>
  Show detailed specification with RL analysis

/torq-spec specify analyze <spec_id>
  Re-run RL analysis on specification

Example:
  /torq-spec specify create "User Auth" "Secure authentication system" \\
    --requirements="Login,Logout,Password reset" \\
    --tech="python,jwt,database" \\
    --complexity="medium" \\
    --priority="high"
"""

    def _plan_help(self) -> str:
        """Plan command help"""
        return """TORQ Console Spec-Kit Planning Commands:

/torq-spec plan generate <spec_id>
  Generate implementation plan with tasks and milestones

/torq-spec plan show <spec_id>
  Show existing implementation plan

/torq-spec plan list
  List all task plans

Example:
  /torq-spec plan generate spec_0001
"""

    def _tasks_help(self) -> str:
        """Tasks command help"""
        return """TORQ Console Spec-Kit Task Commands:

/torq-spec tasks list <spec_id>
  List all tasks for a specification

/torq-spec tasks show <spec_id> <task_id>
  Show detailed task information

/torq-spec tasks update <spec_id> <task_id> <status>
  Update task status (pending|in_progress|completed|blocked)

Example:
  /torq-spec tasks list spec_0001
  /torq-spec tasks update spec_0001 task_001 completed
"""

    def _implement_help(self) -> str:
        """Implementation command help"""
        return """TORQ Console Spec-Kit Implementation Commands:

/torq-spec implement start <spec_id>
  Start implementation of a specification

/torq-spec implement status <spec_id>
  Check implementation status and progress

/torq-spec implement complete <spec_id>
  Mark implementation as complete and gather feedback

Example:
  /torq-spec implement start spec_0001
"""

    def _help(self) -> str:
        """Main help text"""
        return """TORQ Console Spec-Kit - GitHub Spec-Kit Integration with Enhanced RL

Spec-Kit Commands follow the GitHub workflow:
  /constitution → /specify → /plan → /tasks → /implement

Commands:
  /torq-spec constitution  - Manage project constitutions (principles, constraints)
  /torq-spec specify      - Create and manage specifications with RL analysis
  /torq-spec plan         - Generate implementation plans and milestones
  /torq-spec tasks        - Manage implementation tasks
  /torq-spec implement    - Start and track implementation progress

  /torq-spec status       - Show overall status and summary
  /torq-spec list         - List all items (constitutions, specs, plans)
  /torq-spec search       - Search specifications by content
  /torq-spec export       - Export specifications and plans

Features:
  • RL-powered specification analysis and recommendations
  • Risk assessment and mitigation strategies
  • Automated task generation and resource estimation
  • Integration with TORQ Console Enhanced RL System
  • MCP compatibility for tool integration

Use '/torq-spec <command> help' for detailed help on specific commands.

Example Workflow:
  1. /torq-spec constitution create "MyApp" "Build awesome app"
  2. /torq-spec specify create "User Auth" "Secure login system"
  3. /torq-spec plan generate spec_0001
  4. /torq-spec implement start spec_0001
"""