"""
Marvin-Powered Specialized Workflow Agents

Provides specialized agents for specific workflows: code generation,
debugging, documentation, testing, and architecture design.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import marvin

from torq_console.marvin_integration import (
    TorqMarvinIntegration,
    TorqCodeReview,
    ComplexityLevel,
)


class WorkflowType(str, Enum):
    """Types of specialized workflows."""
    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    REFACTORING = "refactoring"


@dataclass
class WorkflowResult:
    """Result from a workflow execution."""
    workflow_type: WorkflowType
    success: bool
    output: Any
    metadata: Dict[str, Any]
    recommendations: List[str]


class CodeGenerationAgent:
    """Specialized agent for code generation tasks."""

    def __init__(self, model: Optional[str] = None):
        self.logger = logging.getLogger("TORQ.Agents.CodeGeneration")
        self.marvin = TorqMarvinIntegration(model=model)
        self.agent = self._create_agent()

    def _create_agent(self) -> marvin.Agent:
        """Create Marvin agent for code generation."""
        return marvin.Agent(
            name="Code Generation Specialist",
            instructions="""
You are a code generation specialist focused on producing clean,
efficient, and well-documented code.

Your approach:
1. Understand requirements thoroughly
2. Consider edge cases and error handling
3. Follow best practices and design patterns
4. Include clear comments and docstrings
5. Provide usage examples
6. Suggest tests

Code quality standards:
- Readable and maintainable
- Follows language conventions
- Handles errors gracefully
- Includes type hints (when applicable)
- Documented with docstrings
""",
            model=self.marvin.model
        )

    async def generate_code(
        self,
        requirements: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Generate code based on requirements.

        Args:
            requirements: What the code should do
            language: Programming language
            context: Optional context (existing code, patterns, etc.)

        Returns:
            WorkflowResult with generated code
        """
        try:
            prompt = f"""
Generate {language} code for the following requirements:

{requirements}

Provide:
1. Complete, working code
2. Explanation of the implementation
3. Usage example
4. Suggested tests
5. Any assumptions made
"""

            code_output = self.marvin.run(
                prompt,
                result_type=str,
                context=context,
                agents=[self.agent]
            )

            return WorkflowResult(
                workflow_type=WorkflowType.CODE_GENERATION,
                success=True,
                output=code_output,
                metadata={
                    'language': language,
                    'requirements': requirements[:200]
                },
                recommendations=[
                    "Review the generated code",
                    "Add comprehensive tests",
                    "Consider edge cases"
                ]
            )

        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            return WorkflowResult(
                workflow_type=WorkflowType.CODE_GENERATION,
                success=False,
                output=None,
                metadata={'error': str(e)},
                recommendations=["Check requirements clarity", "Simplify the request"]
            )


class DebuggingAgent:
    """Specialized agent for debugging assistance."""

    def __init__(self, model: Optional[str] = None):
        self.logger = logging.getLogger("TORQ.Agents.Debugging")
        self.marvin = TorqMarvinIntegration(model=model)
        self.agent = self._create_agent()

    def _create_agent(self) -> marvin.Agent:
        """Create Marvin agent for debugging."""
        return marvin.Agent(
            name="Debugging Specialist",
            instructions="""
You are a debugging specialist expert at identifying and fixing issues in code.

Your debugging process:
1. Analyze the error message and stack trace
2. Identify the root cause
3. Explain what's going wrong
4. Provide a fix with explanation
5. Suggest preventive measures

Your approach:
- Systematic and methodical
- Consider multiple possibilities
- Explain clearly for learning
- Provide working solutions
- Suggest improvements to prevent similar issues
""",
            model=self.marvin.model
        )

    async def debug_issue(
        self,
        code: str,
        error_message: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Debug a code issue.

        Args:
            code: The problematic code
            error_message: Error or unexpected behavior description
            language: Programming language
            context: Optional context

        Returns:
            WorkflowResult with debugging analysis and fix
        """
        try:
            prompt = f"""
Debug this {language} code issue:

CODE:
{code}

ERROR/ISSUE:
{error_message}

Provide:
1. Root cause analysis
2. Explanation of what's wrong
3. Fixed code
4. Why the fix works
5. How to prevent similar issues
"""

            debug_output = self.marvin.run(
                prompt,
                result_type=str,
                context=context,
                agents=[self.agent]
            )

            return WorkflowResult(
                workflow_type=WorkflowType.DEBUGGING,
                success=True,
                output=debug_output,
                metadata={
                    'language': language,
                    'error_type': error_message[:100]
                },
                recommendations=[
                    "Test the fix thoroughly",
                    "Add error handling",
                    "Consider edge cases"
                ]
            )

        except Exception as e:
            self.logger.error(f"Debugging failed: {e}")
            return WorkflowResult(
                workflow_type=WorkflowType.DEBUGGING,
                success=False,
                output=None,
                metadata={'error': str(e)},
                recommendations=["Provide more context", "Include full error trace"]
            )


class DocumentationAgent:
    """Specialized agent for documentation generation."""

    def __init__(self, model: Optional[str] = None):
        self.logger = logging.getLogger("TORQ.Agents.Documentation")
        self.marvin = TorqMarvinIntegration(model=model)
        self.agent = self._create_agent()

    def _create_agent(self) -> marvin.Agent:
        """Create Marvin agent for documentation."""
        return marvin.Agent(
            name="Documentation Specialist",
            instructions="""
You are a documentation specialist creating clear, comprehensive
technical documentation.

Documentation principles:
1. Clear and concise
2. Audience-appropriate
3. Well-structured
4. Include examples
5. Cover common use cases

Your documentation includes:
- Purpose and overview
- Installation/setup
- Usage examples
- API reference
- Best practices
- Troubleshooting
""",
            model=self.marvin.model
        )

    async def generate_documentation(
        self,
        code: str,
        doc_type: str = "api",
        language: str = "python",
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Generate documentation for code.

        Args:
            code: Code to document
            doc_type: Type of documentation (api, guide, reference)
            language: Programming language
            context: Optional context

        Returns:
            WorkflowResult with generated documentation
        """
        try:
            prompt = f"""
Generate {doc_type} documentation for this {language} code:

{code}

Include:
1. Overview and purpose
2. Parameters/arguments
3. Return values
4. Usage examples
5. Notes and warnings (if applicable)
"""

            doc_output = self.marvin.run(
                prompt,
                result_type=str,
                context=context,
                agents=[self.agent]
            )

            return WorkflowResult(
                workflow_type=WorkflowType.DOCUMENTATION,
                success=True,
                output=doc_output,
                metadata={
                    'doc_type': doc_type,
                    'language': language
                },
                recommendations=[
                    "Review for accuracy",
                    "Add diagrams if needed",
                    "Include troubleshooting section"
                ]
            )

        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            return WorkflowResult(
                workflow_type=WorkflowType.DOCUMENTATION,
                success=False,
                output=None,
                metadata={'error': str(e)},
                recommendations=["Simplify code", "Provide more context"]
            )


class TestingAgent:
    """Specialized agent for test generation."""

    def __init__(self, model: Optional[str] = None):
        self.logger = logging.getLogger("TORQ.Agents.Testing")
        self.marvin = TorqMarvinIntegration(model=model)
        self.agent = self._create_agent()

    def _create_agent(self) -> marvin.Agent:
        """Create Marvin agent for testing."""
        return marvin.Agent(
            name="Testing Specialist",
            instructions="""
You are a testing specialist expert at creating comprehensive test suites.

Testing principles:
1. Test happy path and edge cases
2. Include both positive and negative tests
3. Clear test names and descriptions
4. Proper setup and teardown
5. Assertion messages

Test coverage:
- Unit tests for individual functions
- Integration tests for components
- Edge cases and error conditions
- Performance considerations
""",
            model=self.marvin.model
        )

    async def generate_tests(
        self,
        code: str,
        test_framework: str = "pytest",
        language: str = "python",
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Generate tests for code.

        Args:
            code: Code to test
            test_framework: Testing framework to use
            language: Programming language
            context: Optional context

        Returns:
            WorkflowResult with generated tests
        """
        try:
            prompt = f"""
Generate {test_framework} tests for this {language} code:

{code}

Include tests for:
1. Normal/happy path cases
2. Edge cases
3. Error conditions
4. Boundary values
5. Invalid inputs

Use clear test names and include assertions with messages.
"""

            test_output = self.marvin.run(
                prompt,
                result_type=str,
                context=context,
                agents=[self.agent]
            )

            return WorkflowResult(
                workflow_type=WorkflowType.TESTING,
                success=True,
                output=test_output,
                metadata={
                    'test_framework': test_framework,
                    'language': language
                },
                recommendations=[
                    "Run tests to verify they pass",
                    "Add more edge cases if needed",
                    "Check test coverage"
                ]
            )

        except Exception as e:
            self.logger.error(f"Test generation failed: {e}")
            return WorkflowResult(
                workflow_type=WorkflowType.TESTING,
                success=False,
                output=None,
                metadata={'error': str(e)},
                recommendations=["Provide cleaner code", "Specify test requirements"]
            )


class ArchitectureAgent:
    """Specialized agent for software architecture design."""

    def __init__(self, model: Optional[str] = None):
        self.logger = logging.getLogger("TORQ.Agents.Architecture")
        self.marvin = TorqMarvinIntegration(model=model)
        self.agent = self._create_agent()

    def _create_agent(self) -> marvin.Agent:
        """Create Marvin agent for architecture."""
        return marvin.Agent(
            name="Architecture Specialist",
            instructions="""
You are a software architecture specialist expert at designing
scalable, maintainable systems.

Architecture principles:
1. Separation of concerns
2. Modularity and cohesion
3. Scalability considerations
4. Security by design
5. Maintainability

Your designs include:
- Component breakdown
- Interface definitions
- Data flow
- Technology recommendations
- Trade-off analysis
""",
            model=self.marvin.model
        )

    async def design_architecture(
        self,
        requirements: str,
        system_type: str = "web_application",
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Design software architecture.

        Args:
            requirements: System requirements
            system_type: Type of system (web_application, microservice, etc.)
            context: Optional context

        Returns:
            WorkflowResult with architecture design
        """
        try:
            prompt = f"""
Design architecture for a {system_type} with these requirements:

{requirements}

Provide:
1. High-level architecture overview
2. Component breakdown
3. Interface definitions
4. Data flow
5. Technology stack recommendations
6. Scalability considerations
7. Security considerations
8. Trade-offs and alternatives
"""

            arch_output = self.marvin.run(
                prompt,
                result_type=str,
                context=context,
                agents=[self.agent]
            )

            return WorkflowResult(
                workflow_type=WorkflowType.ARCHITECTURE,
                success=True,
                output=arch_output,
                metadata={
                    'system_type': system_type,
                    'requirements': requirements[:200]
                },
                recommendations=[
                    "Review with team",
                    "Create detailed diagrams",
                    "Validate against requirements",
                    "Consider operational aspects"
                ]
            )

        except Exception as e:
            self.logger.error(f"Architecture design failed: {e}")
            return WorkflowResult(
                workflow_type=WorkflowType.ARCHITECTURE,
                success=False,
                output=None,
                metadata={'error': str(e)},
                recommendations=["Clarify requirements", "Define scope better"]
            )


# Workflow agent registry
_workflow_agents: Dict[WorkflowType, Any] = {}


def get_workflow_agent(
    workflow_type: WorkflowType,
    model: Optional[str] = None
) -> Optional[Union['CodeGenerationAgent', 'DebuggingAgent', 'DocumentationAgent', 'TestingAgent', 'ArchitectureAgent']]:
    """
    Get a workflow agent (singleton per type).

    Args:
        workflow_type: Type of workflow agent
        model: Optional LLM model override

    Returns:
        Specialized workflow agent, or None if workflow_type is invalid
    """
    if workflow_type not in _workflow_agents:
        agent_map = {
            WorkflowType.CODE_GENERATION: CodeGenerationAgent,
            WorkflowType.DEBUGGING: DebuggingAgent,
            WorkflowType.DOCUMENTATION: DocumentationAgent,
            WorkflowType.TESTING: TestingAgent,
            WorkflowType.ARCHITECTURE: ArchitectureAgent,
        }

        agent_class = agent_map.get(workflow_type)
        if agent_class:
            _workflow_agents[workflow_type] = agent_class(model=model)

    return _workflow_agents.get(workflow_type)


def list_workflow_agents() -> List[WorkflowType]:
    """List available workflow agent types."""
    return list(WorkflowType)
