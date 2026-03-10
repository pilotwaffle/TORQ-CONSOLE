"""
Tool Output Adapter - Phase 5.3 Milestone 1

Normalizes tool outputs into consistent artifact structure.

This module provides the ToolOutputAdapter which converts raw tool
execution results into the NormalizedArtifact format, ensuring
consistent artifact contracts across all tool types.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from .artifact_models import (
    ArtifactType,
    NormalizedArtifact,
    ToolExecutionMetadata,
)


class ToolOutputAdapter:
    """
    Normalizes tool execution outputs into workspace artifacts.

    This adapter takes raw tool outputs and converts them into a
    consistent NormalizedArtifact structure that can be persisted
    to the workspace.

    The adapter is designed to be additive - it does not modify
    the existing tool execution flow, only captures and normalizes
    outputs.
    """

    def __init__(self):
        """Initialize the tool output adapter."""
        self._tool_type_mapping: Dict[str, ArtifactType] = {
            # Web/Research
            "web_search": ArtifactType.WEB_SEARCH,
            "news_search": ArtifactType.NEWS_SEARCH,
            "tavily_search": ArtifactType.WEB_SEARCH,
            "brave_search": ArtifactType.WEB_SEARCH,

            # Files
            "file_read": ArtifactType.FILE_READ,
            "file_write": ArtifactType.FILE_WRITE,
            "read_file": ArtifactType.FILE_READ,
            "write_file": ArtifactType.FILE_WRITE,

            # Database
            "database": ArtifactType.DATABASE_QUERY,
            "database_query": ArtifactType.DATABASE_QUERY,

            # Code
            "code_execution": ArtifactType.CODE_EXECUTION,
            "execute_code": ArtifactType.CODE_EXECUTION,

            # API
            "api_call": ArtifactType.API_CALL,
            "http_request": ArtifactType.API_CALL,

            # Documents
            "document_generation": ArtifactType.DOCUMENT_GENERATION,

            # Data
            "data_analysis": ArtifactType.DATA_ANALYSIS,
            "data_visualization": ArtifactType.DATA_VISUALIZATION,

            # Knowledge
            "knowledge_query": ArtifactType.KNOWLEDGE_QUERY,
            "validation": ArtifactType.VALIDATION,
            "synthesis": ArtifactType.SYNTHESIS,
        }

    def adapt_tool_output(
        self,
        tool_name: str,
        tool_output: Any,
        execution_metadata: Optional[ToolExecutionMetadata] = None,
    ) -> NormalizedArtifact:
        """
        Adapt a tool output into a normalized artifact.

        Args:
            tool_name: Name of the tool that was executed
            tool_output: Raw output from the tool
            execution_metadata: Optional execution context

        Returns:
            NormalizedArtifact with consistent structure
        """
        # Infer artifact type from tool name
        artifact_type = self._infer_artifact_type(tool_name)

        # Build execution metadata if not provided
        if execution_metadata is None:
            execution_metadata = ToolExecutionMetadata(
                tool_name=tool_name,
                started_at=datetime.utcnow(),
            )
        else:
            # Ensure tool_name is set
            execution_metadata.tool_name = tool_name

        # Normalize the output based on artifact type
        normalized = self._normalize_by_type(
            artifact_type=artifact_type,
            tool_output=tool_output,
            execution_metadata=execution_metadata,
        )

        return normalized

    def adapt_claude_tool_use(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_result: str,
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> NormalizedArtifact:
        """
        Adapt a Claude tool_use API result into a normalized artifact.

        This handles the specific format used by Anthropic's Tool Use API
        where tools are invoked via the messages API.

        Args:
            tool_name: Name of the tool (e.g., 'web_search', 'news_search')
            tool_input: Input parameters passed to the tool
            tool_result: Text result from the tool
            execution_context: Optional execution context (mission_id, node_id, etc.)

        Returns:
            NormalizedArtifact
        """
        # Build execution metadata from context
        metadata = ToolExecutionMetadata(
            tool_name=tool_name,
            mission_id=execution_context.get("mission_id") if execution_context else None,
            node_id=execution_context.get("node_id") if execution_context else None,
            execution_id=execution_context.get("execution_id") if execution_context else None,
            team_execution_id=execution_context.get("team_execution_id") if execution_context else None,
            round_number=execution_context.get("round_number") if execution_context else None,
            role_name=execution_context.get("role_name") if execution_context else None,
            started_at=datetime.utcnow(),
        )

        # Parse structured result if available
        content_json: Dict[str, Any] = {"tool_input": tool_input}

        # Try to parse tool_result as JSON for structured data
        try:
            if tool_result.strip().startswith(("{", "[")):
                parsed = json.loads(tool_result)
                if isinstance(parsed, dict):
                    content_json.update(parsed)
                else:
                    content_json["results"] = parsed
        except (json.JSONDecodeError, ValueError):
            # Not JSON, store as text
            content_json["result_text"] = tool_result

        # Generate title and summary based on tool type
        artifact_type = self._infer_artifact_type(tool_name)
        title, summary = self._generate_title_summary(
            artifact_type=artifact_type,
            tool_name=tool_name,
            tool_input=tool_input,
            content_json=content_json,
        )

        return NormalizedArtifact(
            artifact_type=artifact_type,
            title=title,
            summary=summary,
            content_json=content_json,
            content_text=tool_result,
            execution_metadata=metadata,
        )

    def adapt_role_task_output(
        self,
        role_name: str,
        task_output: Dict[str, Any],
        execution_context: Dict[str, Any],
    ) -> NormalizedArtifact:
        """
        Adapt a role task output into a normalized artifact.

        This handles outputs from team role execution (Phase 5.2 Agent Teams).

        Args:
            role_name: Name of the role (e.g., 'lead', 'researcher', 'critic')
            task_output: Output dictionary from the role task
            execution_context: Team execution context

        Returns:
            NormalizedArtifact
        """
        # Build execution metadata
        metadata = ToolExecutionMetadata(
            tool_name=f"role_{role_name}",
            mission_id=execution_context.get("mission_id"),
            node_id=execution_context.get("node_id"),
            execution_id=execution_context.get("execution_id"),
            team_execution_id=execution_context.get("team_execution_id"),
            round_number=execution_context.get("round_number"),
            role_name=role_name,
            started_at=datetime.utcnow(),
        )

        # Extract output
        output_text = task_output.get("text", "")
        output_data = task_output.get("data", {})

        # Generate title and summary
        title = f"{role_name.title()} Output (Round {execution_context.get('round_number', 1)})"
        summary = output_text[:200] + "..." if len(output_text) > 200 else output_text
        if not summary:
            summary = f"Output from {role_name} role"

        return NormalizedArtifact(
            artifact_type=ArtifactType.ROLE_OUTPUT,
            title=title,
            summary=summary,
            content_json=task_output,
            content_text=output_text,
            execution_metadata=metadata,
        )

    def _infer_artifact_type(self, tool_name: str) -> ArtifactType:
        """Infer artifact type from tool name."""
        # Direct lookup
        if tool_name in self._tool_type_mapping:
            return self._tool_type_mapping[tool_name]

        # Fuzzy matching for tool variants
        tool_lower = tool_name.lower()
        for key, artifact_type in self._tool_type_mapping.items():
            if key in tool_lower or tool_lower in key:
                return artifact_type

        # Default to generic
        return ArtifactType.GENERIC_ARTIFACT

    def _normalize_by_type(
        self,
        artifact_type: ArtifactType,
        tool_output: Any,
        execution_metadata: ToolExecutionMetadata,
    ) -> NormalizedArtifact:
        """Normalize output based on artifact type."""

        # Extract JSON and text components
        content_json: Dict[str, Any] = {}
        content_text: str = ""
        source_ref: Optional[str] = None

        if isinstance(tool_output, dict):
            content_json = tool_output
            content_text = self._extract_text_from_dict(tool_output)
            source_ref = tool_output.get("url") or tool_output.get("path") or tool_output.get("source")
        elif isinstance(tool_output, str):
            content_text = tool_output
            content_json = {"output": tool_output}
        else:
            # Convert to string
            content_text = str(tool_output)
            content_json = {"output": tool_output}

        # Generate title and summary
        title, summary = self._generate_title_summary(
            artifact_type=artifact_type,
            tool_name=execution_metadata.tool_name,
            tool_input={},
            content_json=content_json,
        )

        # Update completion time if not set
        if execution_metadata.completed_at is None:
            execution_metadata.completed_at = datetime.utcnow()
            if execution_metadata.started_at:
                duration = (execution_metadata.completed_at - execution_metadata.started_at).total_seconds()
                execution_metadata.duration_seconds = duration

        return NormalizedArtifact(
            artifact_type=artifact_type,
            title=title,
            summary=summary,
            content_json=content_json,
            content_text=content_text,
            source_ref=source_ref,
            execution_metadata=execution_metadata,
        )

    def _generate_title_summary(
        self,
        artifact_type: ArtifactType,
        tool_name: str,
        tool_input: Dict[str, Any],
        content_json: Dict[str, Any],
    ) -> Tuple[str, str]:
        """Generate title and summary for an artifact."""

        # Type-specific title generation
        if artifact_type == ArtifactType.WEB_SEARCH:
            query = tool_input.get("query") or content_json.get("query") or "search"
            title = f"Web Search: {query}"
            summary = f"Search results for '{query}'"

        elif artifact_type == ArtifactType.NEWS_SEARCH:
            query = tool_input.get("query") or content_json.get("query") or "news"
            title = f"News Search: {query}"
            summary = f"News articles about '{query}'"

        elif artifact_type == ArtifactType.FILE_READ:
            path = tool_input.get("path") or content_json.get("path") or "file"
            title = f"File Read: {path}"
            size = content_json.get("size", 0)
            summary = f"Read {size} bytes from {path}"

        elif artifact_type == ArtifactType.FILE_WRITE:
            path = tool_input.get("path") or content_json.get("path") or "file"
            title = f"File Write: {path}"
            bytes_written = content_json.get("bytes_written", 0)
            summary = f"Wrote {bytes_written} bytes to {path}"

        elif artifact_type == ArtifactType.DATABASE_QUERY:
            query = tool_input.get("query") or content_json.get("query") or "query"
            row_count = content_json.get("row_count", 0)
            title = f"Database Query"
            summary = f"Query returned {row_count} rows"

        elif artifact_type == ArtifactType.CODE_EXECUTION:
            language = tool_input.get("language") or content_json.get("language") or "code"
            title = f"Code Execution ({language})"
            summary = f"Executed {language} code"

        elif artifact_type == ArtifactType.API_CALL:
            url = tool_input.get("url") or content_json.get("url") or "API"
            status = content_json.get("status", "")
            title = f"API Call: {url}"
            summary = f"API request to {url} - Status {status}" if status else f"API request to {url}"

        elif artifact_type == ArtifactType.DOCUMENT_GENERATION:
            format_type = tool_input.get("format") or content_json.get("format") or "document"
            length = content_json.get("length", 0)
            title = f"Document Generation ({format_type})"
            summary = f"Generated {length} character document"

        elif artifact_type == ArtifactType.DATA_ANALYSIS:
            analysis_type = tool_input.get("analysis_type") or content_json.get("analysis_type") or "analysis"
            title = f"Data Analysis: {analysis_type}"
            summary = f"Performed {analysis_type} analysis"

        else:
            # Generic fallback
            title = f"{tool_name.replace('_', ' ').title()} Result"
            summary = f"Output from {tool_name}"

        # Truncate summary if too long
        if len(summary) > 500:
            summary = summary[:497] + "..."

        return title, summary

    def _extract_text_from_dict(self, data: Dict[str, Any]) -> str:
        """Extract readable text from a dictionary."""
        # Priority fields for text representation
        priority_keys = ["text", "content", "output", "result", "message", "summary"]

        for key in priority_keys:
            if key in data and isinstance(data[key], str):
                return data[key]

        # Fallback to JSON serialization
        try:
            return json.dumps(data, indent=2, default=str)
        except Exception:
            return str(data)


# Singleton instance for convenience
_default_adapter: Optional[ToolOutputAdapter] = None


def get_tool_output_adapter() -> ToolOutputAdapter:
    """Get the default tool output adapter instance."""
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = ToolOutputAdapter()
    return _default_adapter


def adapt_tool_output(
    tool_name: str,
    tool_output: Any,
    execution_metadata: Optional[ToolExecutionMetadata] = None,
) -> NormalizedArtifact:
    """
    Convenience function to adapt a tool output.

    Args:
        tool_name: Name of the tool
        tool_output: Raw output from tool
        execution_metadata: Optional execution context

    Returns:
        NormalizedArtifact
    """
    adapter = get_tool_output_adapter()
    return adapter.adapt_tool_output(tool_name, tool_output, execution_metadata)
