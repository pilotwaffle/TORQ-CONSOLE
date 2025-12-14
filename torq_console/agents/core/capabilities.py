"""
Agent Capabilities - Modular capability implementations.

Consolidates scattered capability code from multiple agents into
reusable, composable modules that can be mixed and matched.
"""

import asyncio
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any, Dict, List, Optional, Union, Callable, Type,
    AsyncGenerator
)

from .base_agent import BaseAgent, AgentCapability, AgentContext, AgentResult
from .interfaces import (
    CodeContext, DocumentationRequest, TestRequest,
    ResearchQuery, ConversationTurn, WorkflowType
)


class BaseCapability(ABC):
    """Base class for agent capabilities."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize capability."""
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"Capability.{name}")

    @abstractmethod
    async def execute(
        self,
        *args,
        **kwargs
    ) -> AgentResult:
        """Execute the capability."""
        pass

    async def validate_input(
        self,
        *args,
        **kwargs
    ) -> bool:
        """Validate input parameters."""
        return True

    async def setup(self) -> None:
        """Setup capability resources."""
        pass

    async def cleanup(self) -> None:
        """Cleanup capability resources."""
        pass


class ConversationCapability(BaseCapability):
    """Capability for handling conversations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("conversation", config)
        self._conversations: Dict[str, List[ConversationTurn]] = {}
        self._max_conversation_length = self.config.get("max_length", 50)
        self._conversation_timeout = self.config.get("timeout", 3600)  # 1 hour

    async def execute(
        self,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute conversation capability."""
        start_time = time.time()

        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = f"conv_{int(time.time())}_{hash(message) % 10000}"

            # Get or create conversation
            if session_id not in self._conversations:
                self._conversations[session_id] = []

            conversation = self._conversations[session_id]

            # Add user message to conversation
            user_turn = ConversationTurn(
                user_input=message,
                agent_response="",  # Will be filled below
                timestamp=time.time(),
                context=context.metadata if context else {}
            )

            # Generate response (placeholder implementation)
            response = await self._generate_response(message, conversation)

            # Complete the turn
            user_turn.agent_response = response.content
            user_turn.confidence = response.confidence

            conversation.append(user_turn)

            # Trim conversation if too long
            if len(conversation) > self._max_conversation_length:
                self._conversations[session_id] = conversation[-self._max_conversation_length:]

            response.execution_time = time.time() - start_time
            response.metadata["session_id"] = session_id
            response.metadata["turn_number"] = len(conversation)

            return response

        except Exception as e:
            self.logger.error(f"Conversation error: {e}")
            return AgentResult(
                success=False,
                content="I encountered an error while processing your message.",
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def _generate_response(
        self,
        message: str,
        conversation: List[ConversationTurn]
    ) -> AgentResult:
        """Generate response to user message."""
        # This is a simplified implementation
        # In a real agent, this would use LLM provider or other AI systems

        context_summary = self._summarize_conversation(conversation)

        # Simple rule-based responses for demonstration
        if "hello" in message.lower() or "hi" in message.lower():
            response = "Hello! How can I help you today?"
        elif "help" in message.lower():
            response = "I'm here to help! You can ask me about coding, debugging, documentation, testing, and many other topics."
        elif "thank" in message.lower():
            response = "You're welcome! Is there anything else I can help you with?"
        elif context_summary:
            response = f"Based on our conversation, I understand you're discussing {context_summary}. How can I assist you further?"
        else:
            response = "I understand your message. Could you provide more details about what you'd like help with?"

        return AgentResult(
            success=True,
            content=response,
            confidence=0.8,
            metadata={"response_type": "conversation"}
        )

    def _summarize_conversation(self, conversation: List[ConversationTurn]) -> str:
        """Summarize conversation context."""
        if not conversation:
            return ""

        recent_messages = [turn.user_input for turn in conversation[-3:]]
        return f"recent messages about: {', '.join(recent_messages)}"

    async def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[ConversationTurn]:
        """Get conversation history."""
        if session_id not in self._conversations:
            return []

        conversation = self._conversations[session_id]
        if limit:
            return conversation[-limit:]
        return conversation.copy()

    async def clear_conversation(self, session_id: str) -> bool:
        """Clear conversation history."""
        if session_id in self._conversations:
            del self._conversations[session_id]
            return True
        return False


class ResearchCapability(BaseCapability):
    """Capability for performing research and information gathering."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("research", config)
        self._search_engines = self.config.get("search_engines", ["web"])
        self._max_results = self.config.get("max_results", 10)

    async def execute(
        self,
        query: str,
        scope: str = "web",
        max_results: Optional[int] = None,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute research capability."""
        start_time = time.time()

        try:
            max_results = max_results or self._max_results

            # Perform search (placeholder implementation)
            results = await self._perform_search(query, scope, max_results)

            # Summarize results
            summary = await self._summarize_search_results(query, results)

            execution_time = time.time() - start_time

            return AgentResult(
                success=True,
                content=summary,
                confidence=0.9,
                execution_time=execution_time,
                metadata={
                    "query": query,
                    "scope": scope,
                    "results_count": len(results),
                    "sources": [r.get("source", "unknown") for r in results]
                }
            )

        except Exception as e:
            self.logger.error(f"Research error: {e}")
            return AgentResult(
                success=False,
                content="I encountered an error while performing research.",
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def _perform_search(
        self,
        query: str,
        scope: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Perform search operation."""
        # This is a placeholder implementation
        # In a real system, this would integrate with search APIs

        # Simulate search results
        mock_results = [
            {
                "title": f"Result {i+1} for '{query}'",
                "snippet": f"This is a mock search result snippet for the query: {query}",
                "url": f"https://example.com/result{i+1}",
                "source": "mock_search",
                "relevance": 0.9 - (i * 0.1)
            }
            for i in range(min(max_results, 5))
        ]

        return mock_results

    async def _summarize_search_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """Summarize search results."""
        if not results:
            return f"No results found for query: {query}"

        summary_parts = [f"Found {len(results)} results for '{query}':\n"]

        for i, result in enumerate(results, 1):
            summary_parts.append(
                f"{i}. {result['title']}\n"
                f"   {result['snippet']}\n"
                f"   Source: {result['source']}\n"
            )

        return "\n".join(summary_parts)


class CodeGenerationCapability(BaseCapability):
    """Capability for generating code from requirements."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("code_generation", config)
        self._supported_languages = self.config.get("languages", ["python", "javascript", "typescript"])
        self._default_language = self.config.get("default_language", "python")

    async def execute(
        self,
        requirements: str,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute code generation capability."""
        start_time = time.time()

        try:
            language = language or self._default_language

            if language not in self._supported_languages:
                return AgentResult(
                    success=False,
                    content=f"Language '{language}' is not supported. Supported languages: {self._supported_languages}",
                    execution_time=time.time() - start_time
                )

            # Generate code
            generated_code = await self._generate_code(requirements, language, framework)

            # Generate explanation
            explanation = await self._generate_explanation(requirements, generated_code, language)

            execution_time = time.time() - start_time

            return AgentResult(
                success=True,
                content=f"```{language}\n{generated_code}\n```\n\n**Explanation:**\n{explanation}",
                confidence=0.85,
                execution_time=execution_time,
                metadata={
                    "language": language,
                    "framework": framework,
                    "code_lines": len(generated_code.split('\n'))
                }
            )

        except Exception as e:
            self.logger.error(f"Code generation error: {e}")
            return AgentResult(
                success=False,
                content="I encountered an error while generating code.",
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def _generate_code(
        self,
        requirements: str,
        language: str,
        framework: Optional[str]
    ) -> str:
        """Generate code from requirements."""
        # This is a simplified implementation
        # In a real system, this would use LLM or code generation models

        # Simple pattern-based code generation
        requirements_lower = requirements.lower()

        if "function" in requirements_lower and "add" in requirements_lower:
            return """def add(a, b):
    \"\"\"Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    \"\"\"
    return a + b"""

        elif "class" in requirements_lower:
            return """class GeneratedClass:
    \"\"\"A generated class based on requirements.\"\"\"

    def __init__(self):
        self.initialized = True

    def process(self, data):
        \"\"\"Process the provided data.\"\"\"
        return f"Processed: {data}\""""

        else:
            return """# Generated code based on requirements
def main():
    \"\"\"Main function.\"\"\"
    print("Generated code executed successfully.")

if __name__ == "__main__":
    main()"""

    async def _generate_explanation(
        self,
        requirements: str,
        code: str,
        language: str
    ) -> str:
        """Generate explanation for the generated code."""
        return f"""
This code is written in {language} and addresses the requirements: "{requirements}".

The code includes:
- Proper structure and formatting
- Docstrings for documentation
- Error handling where appropriate
- Example usage patterns

Feel free to modify the code to better suit your specific needs.
"""


class DebuggingCapability(BaseCapability):
    """Capability for debugging code issues."""

    async def execute(
        self,
        code: str,
        error_message: str,
        language: Optional[str] = None,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute debugging capability."""
        start_time = time.time()

        try:
            # Analyze the error
            analysis = await self._analyze_error(code, error_message, language)

            # Suggest fixes
            fixes = await self._suggest_fixes(code, error_message, analysis)

            execution_time = time.time() - start_time

            return AgentResult(
                success=True,
                content=f"**Error Analysis:**\n{analysis}\n\n**Suggested Fixes:**\n{fixes}",
                confidence=0.8,
                execution_time=execution_time,
                metadata={
                    "error_type": analysis.get("error_type", "unknown"),
                    "fix_count": len(fixes.split('\n')) if fixes else 0
                }
            )

        except Exception as e:
            self.logger.error(f"Debugging error: {e}")
            return AgentResult(
                success=False,
                content="I encountered an error while debugging the code.",
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def _analyze_error(
        self,
        code: str,
        error_message: str,
        language: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze the error and code."""
        error_lower = error_message.lower()

        # Simple error pattern matching
        if "syntaxerror" in error_lower:
            return {
                "error_type": "syntax",
                "description": "There's a syntax error in the code.",
                "likely_cause": "Missing parenthesis, incorrect indentation, or invalid syntax"
            }
        elif "nameerror" in error_lower or "not defined" in error_lower:
            return {
                "error_type": "name_error",
                "description": "A variable or function name is not defined.",
                "likely_cause": "Typo in variable name or using variable before definition"
            }
        elif "typeerror" in error_lower:
            return {
                "error_type": "type_error",
                "description": "Operation performed on incompatible types.",
                "likely_cause": "Trying to perform operation on wrong data type"
            }
        elif "division by zero" in error_lower:
            return {
                "error_type": "zerodivision",
                "description": "Attempted to divide by zero.",
                "likely_cause": "Divisor is zero or could become zero"
            }
        else:
            return {
                "error_type": "general",
                "description": "An error occurred during code execution.",
                "likely_cause": "Various possible causes, need more investigation"
            }

    async def _suggest_fixes(
        self,
        code: str,
        error_message: str,
        analysis: Dict[str, Any]
    ) -> str:
        """Suggest fixes for the error."""
        error_type = analysis.get("error_type", "general")

        if error_type == "syntax":
            return """
1. Check for missing parentheses or brackets
2. Verify correct indentation
3. Ensure all string literals are properly closed
4. Check for invalid syntax characters
"""
        elif error_type == "name_error":
            return """
1. Check variable name spelling
2. Ensure variables are defined before use
3. Check for scope issues
4. Import required modules if needed
"""
        elif error_type == "type_error":
            return """
1. Check variable types before operations
2. Use type conversion functions (str(), int(), float())
3. Validate input data
4. Add type checking if needed
"""
        elif error_type == "zerodivision":
            return """
1. Check if divisor is zero before division
2. Add try-except block for ZeroDivisionError
3. Provide default value for zero case
4. Use conditional logic to avoid division by zero
"""
        else:
            return """
1. Review the error message and code carefully
2. Add debug prints to identify the issue
3. Check variable values at error point
4. Consider using a debugger for detailed analysis
"""


class DocumentationCapability(BaseCapability):
    """Capability for generating documentation."""

    async def execute(
        self,
        content: str,
        doc_type: str = "api",
        audience: str = "developers",
        format: str = "markdown",
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute documentation generation capability."""
        start_time = time.time()

        try:
            # Generate documentation
            documentation = await self._generate_documentation(
                content, doc_type, audience, format
            )

            execution_time = time.time() - start_time

            return AgentResult(
                success=True,
                content=documentation,
                confidence=0.85,
                execution_time=execution_time,
                metadata={
                    "doc_type": doc_type,
                    "audience": audience,
                    "format": format
                }
            )

        except Exception as e:
            self.logger.error(f"Documentation generation error: {e}")
            return AgentResult(
                success=False,
                content="I encountered an error while generating documentation.",
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def _generate_documentation(
        self,
        content: str,
        doc_type: str,
        audience: str,
        format: str
    ) -> str:
        """Generate documentation based on type and audience."""
        if doc_type == "api":
            return await self._generate_api_docs(content, audience)
        elif doc_type == "guide":
            return await self._generate_guide_docs(content, audience)
        elif doc_type == "reference":
            return await self._generate_reference_docs(content, audience)
        else:
            return await self._generate_general_docs(content, audience)

    async def _generate_api_docs(self, content: str, audience: str) -> str:
        """Generate API documentation."""
        return f"""# API Documentation

## Overview
This document describes the API based on the provided code/content.

## Usage

```python
{content}
```

## Parameters
- Detailed parameter descriptions would go here

## Returns
- Return value descriptions would go here

## Examples
```python
# Example usage
result = your_function()
print(result)
```

## Notes
This documentation is generated automatically. Please review and customize as needed.
"""

    async def _generate_guide_docs(self, content: str, audience: str) -> str:
        """Generate guide documentation."""
        return f"""# User Guide

## Introduction
This guide explains how to use the provided functionality.

## Getting Started

### Prerequisites
- Basic understanding of the concepts
- Required dependencies

### Basic Usage

{content}

## Advanced Usage
Advanced features and configurations would be documented here.

## Troubleshooting
Common issues and solutions would be listed here.

## FAQ
Frequently asked questions would be answered here.
"""

    async def _generate_reference_docs(self, content: str, audience: str) -> str:
        """Generate reference documentation."""
        return f"""# Reference Documentation

## Overview
This is a comprehensive reference for the provided functionality.

## Details

{content}

## Technical Specifications
Technical details and specifications would be included here.

## Related Documentation
- Related documentation links would be provided here
"""

    async def _generate_general_docs(self, content: str, audience: str) -> str:
        """Generate general documentation."""
        return f"""# Documentation

## Summary
This document provides information about the following content.

{content}

## Additional Information
Additional context and details would be provided here.
"""


# Additional capability classes can be added here
class TestingCapability(BaseCapability):
    """Capability for generating tests."""

    async def execute(self, *args, **kwargs) -> AgentResult:
        """Execute testing capability."""
        # Implementation would go here
        return AgentResult(success=True, content="Testing capability not yet implemented")


class ArchitectureCapability(BaseCapability):
    """Capability for architecture design."""

    async def execute(self, *args, **kwargs) -> AgentResult:
        """Execute architecture capability."""
        # Implementation would go here
        return AgentResult(success=True, content="Architecture capability not yet implemented")


# Capability factory for easy creation
class CapabilityFactory:
    """Factory for creating capability instances."""

    _capabilities = {
        AgentCapability.CONVERSATION: ConversationCapability,
        AgentCapability.RESEARCH: ResearchCapability,
        AgentCapability.CODE_GENERATION: CodeGenerationCapability,
        AgentCapability.DEBUGGING: DebuggingCapability,
        AgentCapability.DOCUMENTATION: DocumentationCapability,
        AgentCapability.TESTING: TestingCapability,
        AgentCapability.ARCHITECTURE: ArchitectureCapability,
    }

    @classmethod
    def create_capability(
        self,
        capability: AgentCapability,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseCapability:
        """Create a capability instance."""
        if capability not in self._capabilities:
            raise ValueError(f"Unknown capability: {capability}")

        capability_class = self._capabilities[capability]
        return capability_class(config)

    @classmethod
    def get_available_capabilities(self) -> List[AgentCapability]:
        """Get list of available capabilities."""
        return list(self._capabilities.keys())