"""
n8n Workflow Architect-Builder Agent

Specialized Marvin-powered agent for designing and generating production-ready
n8n workflow JSON configurations.
"""

import logging
import json
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import marvin

from torq_console.marvin_integration import TorqMarvinIntegration


class WorkflowTriggerType(str, Enum):
    """Types of workflow triggers."""
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    SUB_WORKFLOW = "sub_workflow"


class ErrorHandlingStrategy(str, Enum):
    """Error handling strategies."""
    HARD_FAIL = "hard_fail"  # Stop + Alert
    SOFT_FAIL = "soft_fail"  # Log + Continue
    RETRY_BACKOFF = "retry_backoff"  # Retry with exponential backoff


@dataclass
class WorkflowRequirements:
    """Requirements for workflow generation."""
    name: str
    purpose: str
    trigger_type: WorkflowTriggerType
    error_handling: ErrorHandlingStrategy
    data_sources: List[str] = field(default_factory=list)
    security_requirements: List[str] = field(default_factory=list)
    expected_volume: str = "low"  # low, medium, high
    outputs: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowBlueprint:
    """Workflow design blueprint."""
    metadata: Dict[str, Any]
    architecture_diagram: str
    node_execution_plan: List[Dict[str, Any]]
    data_contracts: Dict[str, Any]
    error_handling_strategy: Dict[str, Any]
    security_measures: List[str]
    observability: Dict[str, Any]
    production_ready_checklist: List[str]


class N8NWorkflowArchitectAgent:
    """
    Specialized Marvin-powered agent for n8n workflow design and generation.

    This agent follows a three-phase process:
    1. Requirements Discovery - Extract complete specifications
    2. Workflow Design Blueprint - Present architectural specification
    3. JSON Generation - Generate production-ready n8n workflow JSON

    Features:
    - Production-grade error handling and retry logic
    - Security-first design (secrets via env vars, input validation)
    - Git-friendly output (deterministic IDs, stable ordering)
    - Environment-agnostic configuration
    - Comprehensive observability and logging
    """

    # Agent system prompt
    AGENT_PROMPT = """# n8n Workflow Architect-Builder Agent v2.0

## ROLE & IDENTITY
You are an elite n8n workflow architect with 5+ years of production automation engineering experience. You specialize in translating business requirements into secure, scalable, Git-versioned n8n workflows that are immediately importable and production-ready.

## CORE EXPERTISE
- n8n workflow architecture (JSON v1.0+ format)
- Production-grade error handling, retry logic, and observability
- API integration patterns, webhook security, and rate limiting
- LLM orchestration with structured output enforcement
- Multi-agent workflows and sub-workflow decomposition
- Environment-agnostic, idempotent workflow design

## YOUR APPROACH
1. **Requirements Discovery**: Ask targeted questions to extract complete specifications
2. **Blueprint Design**: Create detailed architectural specification for approval
3. **JSON Generation**: Generate production-ready n8n workflow JSON

## QUALITY STANDARDS
- All secrets via environment variables ({{$env.SECRET_NAME}})
- Input validation with JSON schemas
- Comprehensive error handling with retry logic
- Structured logging and observability
- Idempotent and environment-agnostic design
- Git-friendly (deterministic node IDs, stable ordering)

## RESPONSE STYLE
- Clear, concise, and actionable
- Ask targeted questions (not vague "tell me more")
- Provide complete solutions, not placeholders
- Include production-ready best practices
- Focus on security, scalability, and maintainability
"""

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the n8n Workflow Architect Agent.

        Args:
            model: Optional LLM model to use (defaults to TorqMarvinIntegration default)
        """
        self.logger = logging.getLogger("TORQ.Agents.N8NArchitect")
        self.marvin = TorqMarvinIntegration(model=model)
        self.agent = self._create_agent()

        # Agent metadata
        self.name = "n8n Workflow Architect-Builder"
        self.version = "2.0"
        self.capabilities = [
            "workflow_design",
            "json_generation",
            "error_handling",
            "security_best_practices",
            "api_integration",
            "webhook_design"
        ]

    def _create_agent(self) -> marvin.Agent:
        """Create Marvin agent for n8n workflow architecture."""
        return marvin.Agent(
            name="n8n Workflow Architect",
            instructions=self.AGENT_PROMPT,
            model=self.marvin.model
        )

    async def discover_requirements(
        self,
        initial_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Phase 1: Requirements Discovery

        Asks targeted questions to extract complete specifications.

        Args:
            initial_request: User's initial workflow request
            context: Optional additional context

        Returns:
            Dict containing discovered requirements and next questions to ask
        """
        try:
            prompt = f"""
PHASE 1: REQUIREMENTS DISCOVERY

User's initial request:
{initial_request}

Your task: Extract complete specifications using the requirements framework.

Ask 2-3 targeted questions covering:
- **Trigger**: Webhook/Schedule/Manual/Sub-workflow?
- **Error Handling**: Hard-fail (stop+alert) or soft-fail (log+continue)?
- **Data Sources**: Which APIs, databases, LLMs, file storage?
- **Security**: API keys, OAuth, HMAC? Compliance requirements?
- **Scale**: Volume expectations (<100/day, 100-10K/day, >10K/day)?
- **Outputs**: Data transformation, API writes, notifications?

DO NOT ask vague questions like "tell me more" or "can you provide more details".
Ask SPECIFIC, ACTIONABLE questions.

Format your response as:
1. What I understand so far
2. Specific questions I need answered (2-3 maximum)
3. Why these questions matter
"""

            response = self.marvin.run(
                prompt,
                result_type=str,
                context=context,
                agents=[self.agent]
            )

            return {
                'success': True,
                'phase': 'requirements_discovery',
                'response': response,
                'next_action': 'await_user_answers'
            }

        except Exception as e:
            self.logger.error(f"Requirements discovery failed: {e}")
            return {
                'success': False,
                'phase': 'requirements_discovery',
                'error': str(e)
            }

    async def design_blueprint(
        self,
        requirements: WorkflowRequirements,
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowBlueprint:
        """
        Phase 2: Workflow Design Blueprint

        Creates a complete architectural specification for user approval.

        Args:
            requirements: Extracted workflow requirements
            context: Optional additional context

        Returns:
            WorkflowBlueprint with complete design specification
        """
        try:
            prompt = f"""
PHASE 2: WORKFLOW DESIGN BLUEPRINT

Requirements:
- Name: {requirements.name}
- Purpose: {requirements.purpose}
- Trigger: {requirements.trigger_type.value}
- Error Handling: {requirements.error_handling.value}
- Data Sources: {', '.join(requirements.data_sources)}
- Security: {', '.join(requirements.security_requirements)}
- Scale: {requirements.expected_volume}
- Outputs: {', '.join(requirements.outputs)}

Create a complete architectural specification including:

1. **Workflow Metadata**
   - Name (snake_case)
   - Purpose (2-3 sentences)
   - Tags
   - Required environment variables

2. **Architecture Diagram** (ASCII)
   - Visual flow of all nodes
   - Error paths
   - Retry logic

3. **Node Execution Plan**
   - Each node: Name, Type, Purpose, Configuration
   - Data flow between nodes
   - Error handling per node

4. **Data Contracts**
   - Input JSON schema
   - Output JSON schema
   - Error schema

5. **Error Handling Strategy**
   - Retry logic details
   - Failure paths (hard vs soft fail)
   - Alerting configuration

6. **Security & Observability**
   - How secrets are managed
   - Input validation approach
   - Logging points
   - Metrics to track

7. **Production Readiness Checklist**
   - Idempotency
   - Environment-agnostic
   - Git-friendly
   - Sub-workflow compatible

Provide COMPLETE, DETAILED specifications. No placeholders.
"""

            response = self.marvin.run(
                prompt,
                result_type=str,
                context=context or {},
                agents=[self.agent]
            )

            # Parse the blueprint response into structured format
            blueprint = WorkflowBlueprint(
                metadata={
                    'name': requirements.name,
                    'purpose': requirements.purpose,
                    'trigger_type': requirements.trigger_type.value,
                    'created_at': datetime.now().isoformat(),
                    'version': '1.0.0'
                },
                architecture_diagram=response,  # Full response contains diagram
                node_execution_plan=[],  # Would be parsed from response
                data_contracts={
                    'input': {},
                    'output': {},
                    'error': {}
                },
                error_handling_strategy={
                    'type': requirements.error_handling.value,
                    'retry_enabled': requirements.error_handling == ErrorHandlingStrategy.RETRY_BACKOFF
                },
                security_measures=requirements.security_requirements,
                observability={
                    'logging_enabled': True,
                    'metrics_enabled': True
                },
                production_ready_checklist=[
                    'Idempotent design',
                    'Environment-agnostic',
                    'Git-friendly IDs',
                    'Sub-workflow compatible',
                    'Comprehensive error handling'
                ]
            )

            return blueprint

        except Exception as e:
            self.logger.error(f"Blueprint design failed: {e}")
            raise

    async def generate_workflow_json(
        self,
        blueprint: WorkflowBlueprint,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Phase 3: JSON Generation

        Generates production-ready n8n workflow JSON.

        Args:
            blueprint: Approved workflow blueprint
            context: Optional additional context

        Returns:
            Dict containing n8n workflow JSON configuration
        """
        try:
            # Generate unique IDs for the workflow
            workflow_id = str(uuid.uuid4())
            instance_id = str(uuid.uuid4())

            prompt = f"""
PHASE 3: JSON GENERATION

Blueprint approved. Generate complete n8n workflow JSON.

Blueprint summary:
{json.dumps(blueprint.metadata, indent=2)}

Requirements:
1. **Valid n8n format** (v1.0+ compatible)
2. **Production-ready** with:
   - All secrets via {{{{$env.VAR_NAME}}}}
   - Input validation nodes
   - Error handling nodes
   - Retry logic (exponential backoff)
   - Structured logging
3. **Git-friendly**:
   - Deterministic node IDs
   - Stable node ordering
   - Clear node names
4. **Complete metadata**:
   - templateCreatedBy: "n8n Workflow Architect-Builder Agent v2.0"
   - description, version, tags
   - requiredEnvVars list
   - Input/output/error schemas

Generate the COMPLETE JSON workflow. No placeholders. No "..." or "add more nodes".
All nodes must be fully configured and ready to import into n8n.

Return ONLY valid JSON. No markdown code blocks, no explanation text.
"""

            # Generate workflow JSON
            workflow_json_str = self.marvin.run(
                prompt,
                result_type=str,
                context=context or {},
                agents=[self.agent]
            )

            # Parse and validate JSON
            workflow_json = json.loads(workflow_json_str)

            # Ensure required fields
            if 'meta' not in workflow_json:
                workflow_json['meta'] = {}

            workflow_json['meta'].update({
                'templateCreatedBy': f'{self.name} v{self.version}',
                'instanceId': instance_id,
                'created': datetime.now().isoformat(),
                'version': blueprint.metadata.get('version', '1.0.0')
            })

            # Ensure workflow has required top-level fields
            workflow_json.setdefault('name', blueprint.metadata['name'])
            workflow_json.setdefault('nodes', [])
            workflow_json.setdefault('connections', {})
            workflow_json.setdefault('settings', {'executionOrder': 'v1'})
            workflow_json.setdefault('staticData', None)
            workflow_json.setdefault('pinData', {})
            workflow_json.setdefault('versionId', workflow_id)

            return {
                'success': True,
                'phase': 'json_generation',
                'workflow_json': workflow_json,
                'metadata': {
                    'workflow_id': workflow_id,
                    'node_count': len(workflow_json.get('nodes', [])),
                    'created_at': datetime.now().isoformat()
                }
            }

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON generated: {e}")
            return {
                'success': False,
                'phase': 'json_generation',
                'error': f'Invalid JSON: {str(e)}'
            }
        except Exception as e:
            self.logger.error(f"JSON generation failed: {e}")
            return {
                'success': False,
                'phase': 'json_generation',
                'error': str(e)
            }

    async def full_workflow_creation(
        self,
        request: str,
        requirements: Optional[WorkflowRequirements] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete end-to-end workflow creation.

        Executes all three phases automatically if requirements are provided.

        Args:
            request: Initial workflow request
            requirements: Optional pre-filled requirements
            context: Optional additional context

        Returns:
            Dict with complete workflow generation result
        """
        try:
            # Phase 1: If no requirements, start discovery
            if not requirements:
                discovery = await self.discover_requirements(request, context)
                if not discovery['success']:
                    return discovery

                # In a real implementation, would wait for user responses
                # For now, return discovery questions
                return discovery

            # Phase 2: Design blueprint
            self.logger.info("Designing workflow blueprint...")
            blueprint = await self.design_blueprint(requirements, context)

            # Phase 3: Generate JSON
            self.logger.info("Generating workflow JSON...")
            result = await self.generate_workflow_json(blueprint, context)

            if result['success']:
                self.logger.info(f"Successfully generated workflow: {blueprint.metadata['name']}")

            return result

        except Exception as e:
            self.logger.error(f"Full workflow creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information for registration."""
        return {
            'name': self.name,
            'version': self.version,
            'type': 'n8n_workflow_architect',
            'capabilities': self.capabilities,
            'phases': [
                'requirements_discovery',
                'blueprint_design',
                'json_generation'
            ],
            'description': 'Elite n8n workflow architect for designing and generating production-ready workflow JSON',
            'model': self.marvin.model
        }


# Factory function
def create_n8n_architect_agent(model: Optional[str] = None) -> N8NWorkflowArchitectAgent:
    """
    Create an n8n Workflow Architect Agent instance.

    Args:
        model: Optional LLM model to use

    Returns:
        N8NWorkflowArchitectAgent instance

    Example:
        >>> agent = create_n8n_architect_agent()
        >>> result = await agent.discover_requirements("Create a webhook that processes payments")
        >>> print(result['response'])
    """
    return N8NWorkflowArchitectAgent(model=model)
