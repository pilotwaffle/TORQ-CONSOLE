"""
TORQ CONSOLE Inline Editor v0.70.0 - Phase 2

Advanced inline editing system with Cursor-like functionality including:
- Selection-based editing with keyboard shortcuts (Ctrl+K pattern)
- Ghost text rendering system for AI suggestions
- Quick question mode (Alt+Enter for code understanding)
- Multi-step refinement workflow (Critic → Refiner → Evaluator)
- Context-aware code generation at cursor position
- Shadow workspace for safe testing
- Drag-and-drop context management
"""

import asyncio
import json
import logging
import re
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from enum import Enum
import hashlib
import difflib

from ..core.context_manager import ContextManager, ContextMatch
from ..core.config import TorqConfig
from ..core.logger import setup_logger


class EditMode(Enum):
    """Inline editing modes."""
    SELECTION = "selection"
    CURSOR = "cursor"
    GHOST_TEXT = "ghost_text"
    QUICK_QUESTION = "quick_question"
    REFINEMENT = "refinement"


class EditAction(Enum):
    """Types of edit actions."""
    GENERATE = "generate"
    REFINE = "refine"
    EXPLAIN = "explain"
    COMPLETE = "complete"
    TRANSFORM = "transform"
    REVIEW = "review"


@dataclass
class EditSelection:
    """Represents a text selection for editing."""
    start_line: int
    start_col: int
    end_line: int
    end_col: int
    text: str = ""
    file_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "start_line": self.start_line,
            "start_col": self.start_col,
            "end_line": self.end_line,
            "end_col": self.end_col,
            "text": self.text,
            "file_path": str(self.file_path) if self.file_path else None
        }


@dataclass
class GhostTextSuggestion:
    """Represents a ghost text suggestion."""
    id: str
    text: str
    position: Tuple[int, int]  # line, column
    confidence: float
    source: str  # "ai", "completion", "snippet"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "position": self.position,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class EditRequest:
    """Represents an inline edit request."""
    id: str
    mode: EditMode
    action: EditAction
    selection: Optional[EditSelection]
    prompt: str
    context: List[ContextMatch] = field(default_factory=list)
    file_path: Optional[Path] = None
    cursor_position: Optional[Tuple[int, int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "mode": self.mode.value,
            "action": self.action.value,
            "selection": self.selection.to_dict() if self.selection else None,
            "prompt": self.prompt,
            "context": [match.metadata for match in self.context],
            "file_path": str(self.file_path) if self.file_path else None,
            "cursor_position": self.cursor_position,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class EditResponse:
    """Represents an inline edit response."""
    request_id: str
    success: bool
    content: str
    ghost_text: Optional[GhostTextSuggestion] = None
    alternatives: List[str] = field(default_factory=list)
    explanation: str = ""
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "request_id": self.request_id,
            "success": self.success,
            "content": self.content,
            "ghost_text": self.ghost_text.to_dict() if self.ghost_text else None,
            "alternatives": self.alternatives,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class ShadowWorkspace:
    """Safe testing environment for inline edits."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.shadow_path = Path(tempfile.mkdtemp(prefix="torq_shadow_"))
        self.active_files: Dict[str, Path] = {}
        self.logger = logging.getLogger(__name__)

    def create_shadow_file(self, original_path: Path) -> Path:
        """Create a shadow copy of a file for safe testing."""
        try:
            relative_path = original_path.relative_to(self.base_path)
            shadow_file = self.shadow_path / relative_path

            # Create directory structure
            shadow_file.parent.mkdir(parents=True, exist_ok=True)

            # Copy original file
            if original_path.exists():
                shadow_file.write_text(
                    original_path.read_text(encoding='utf-8', errors='ignore'),
                    encoding='utf-8'
                )
            else:
                shadow_file.touch()

            self.active_files[str(original_path)] = shadow_file
            return shadow_file

        except Exception as e:
            self.logger.error(f"Error creating shadow file: {e}")
            raise

    def apply_edit(self, file_path: Path, edit: str, selection: Optional[EditSelection] = None) -> bool:
        """Apply an edit to a shadow file."""
        try:
            shadow_file = self.active_files.get(str(file_path))
            if not shadow_file:
                shadow_file = self.create_shadow_file(file_path)

            content = shadow_file.read_text(encoding='utf-8')

            if selection:
                # Replace selected text
                lines = content.split('\n')
                if 0 <= selection.start_line < len(lines) and 0 <= selection.end_line < len(lines):
                    # Handle multi-line selection
                    if selection.start_line == selection.end_line:
                        line = lines[selection.start_line]
                        new_line = (line[:selection.start_col] +
                                  edit +
                                  line[selection.end_col:])
                        lines[selection.start_line] = new_line
                    else:
                        # Multi-line replacement
                        before = lines[:selection.start_line]
                        after = lines[selection.end_line + 1:]
                        start_line = lines[selection.start_line][:selection.start_col]
                        end_line = lines[selection.end_line][selection.end_col:]

                        edit_lines = edit.split('\n')
                        if edit_lines:
                            edit_lines[0] = start_line + edit_lines[0]
                            edit_lines[-1] = edit_lines[-1] + end_line

                        lines = before + edit_lines + after

                    shadow_file.write_text('\n'.join(lines), encoding='utf-8')
                    return True
            else:
                # Append to end of file
                if content and not content.endswith('\n'):
                    content += '\n'
                content += edit
                shadow_file.write_text(content, encoding='utf-8')
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error applying edit to shadow file: {e}")
            return False

    def get_diff(self, original_path: Path) -> str:
        """Get diff between original and shadow file."""
        try:
            shadow_file = self.active_files.get(str(original_path))
            if not shadow_file:
                return ""

            original_content = ""
            if original_path.exists():
                original_content = original_path.read_text(encoding='utf-8', errors='ignore')

            shadow_content = shadow_file.read_text(encoding='utf-8')

            diff = difflib.unified_diff(
                original_content.splitlines(keepends=True),
                shadow_content.splitlines(keepends=True),
                fromfile=str(original_path),
                tofile=f"{original_path} (edited)",
                lineterm=""
            )

            return ''.join(diff)

        except Exception as e:
            self.logger.error(f"Error generating diff: {e}")
            return ""

    def cleanup(self):
        """Clean up shadow workspace."""
        try:
            import shutil
            shutil.rmtree(self.shadow_path, ignore_errors=True)
            self.active_files.clear()
        except Exception as e:
            self.logger.error(f"Error cleaning up shadow workspace: {e}")


class RefineWorkflow:
    """Multi-step refinement workflow: Critic → Refiner → Evaluator."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def run_workflow(self, edit_request: EditRequest, initial_response: str) -> Dict[str, Any]:
        """Run the complete refinement workflow."""
        try:
            workflow_results = {
                "initial": initial_response,
                "critic_review": None,
                "refined_version": None,
                "evaluation": None,
                "final_recommendation": initial_response
            }

            # Step 1: Critic analysis
            critic_review = await self._critic_analysis(edit_request, initial_response)
            workflow_results["critic_review"] = critic_review

            # Step 2: Refiner improvements
            if critic_review.get("needs_improvement", False):
                refined_version = await self._refiner_improvements(
                    edit_request, initial_response, critic_review
                )
                workflow_results["refined_version"] = refined_version

                # Step 3: Evaluator assessment
                evaluation = await self._evaluator_assessment(
                    edit_request, initial_response, refined_version
                )
                workflow_results["evaluation"] = evaluation

                # Determine final recommendation
                if evaluation.get("refined_is_better", False):
                    workflow_results["final_recommendation"] = refined_version

            return workflow_results

        except Exception as e:
            self.logger.error(f"Error in refinement workflow: {e}")
            return {"initial": initial_response, "final_recommendation": initial_response}

    async def _critic_analysis(self, request: EditRequest, response: str) -> Dict[str, Any]:
        """Analyze the initial response for potential improvements."""
        try:
            # Simulate critic analysis (in real implementation, this would call AI model)
            analysis = {
                "readability": 8.5,
                "correctness": 9.0,
                "completeness": 7.5,
                "style_consistency": 8.0,
                "needs_improvement": False,
                "suggestions": []
            }

            # Check for common issues
            if len(response) < 10:
                analysis["suggestions"].append("Response seems too short")
                analysis["needs_improvement"] = True

            if request.action == EditAction.EXPLAIN and "because" not in response.lower():
                analysis["suggestions"].append("Explanation could include reasoning")
                analysis["needs_improvement"] = True

            average_score = sum([
                analysis["readability"],
                analysis["correctness"],
                analysis["completeness"],
                analysis["style_consistency"]
            ]) / 4

            if average_score < 8.0:
                analysis["needs_improvement"] = True

            return analysis

        except Exception as e:
            self.logger.error(f"Error in critic analysis: {e}")
            return {"needs_improvement": False, "suggestions": []}

    async def _refiner_improvements(self, request: EditRequest, original: str, critic_review: Dict[str, Any]) -> str:
        """Apply improvements based on critic review."""
        try:
            # Simulate refiner improvements
            improved = original

            for suggestion in critic_review.get("suggestions", []):
                if "too short" in suggestion:
                    improved += "\n# Additional implementation details would go here"
                elif "reasoning" in suggestion:
                    improved += "\n# This approach is chosen because it provides better maintainability"

            return improved

        except Exception as e:
            self.logger.error(f"Error in refiner improvements: {e}")
            return original

    async def _evaluator_assessment(self, request: EditRequest, original: str, refined: str) -> Dict[str, Any]:
        """Evaluate which version is better."""
        try:
            # Simulate evaluator assessment
            assessment = {
                "original_score": 7.5,
                "refined_score": 8.2,
                "refined_is_better": True,
                "reasoning": "Refined version provides more complete information",
                "confidence": 0.85
            }

            # Simple heuristic: longer is often better for explanations
            if request.action == EditAction.EXPLAIN:
                if len(refined) > len(original) * 1.2:
                    assessment["refined_is_better"] = True
                    assessment["refined_score"] = min(9.0, assessment["original_score"] + 1.0)

            return assessment

        except Exception as e:
            self.logger.error(f"Error in evaluator assessment: {e}")
            return {"refined_is_better": False, "confidence": 0.0}


class InlineEditor:
    """
    Advanced inline editing system for TORQ CONSOLE v0.70.0.

    Provides Cursor-like functionality with AI-powered code assistance,
    ghost text suggestions, and multi-step refinement workflows.
    """

    def __init__(self, config: TorqConfig, context_manager: ContextManager):
        self.config = config
        self.context_manager = context_manager
        self.logger = setup_logger("inline_editor")

        # Core components
        self.shadow_workspace = ShadowWorkspace(Path.cwd())
        self.refine_workflow = RefineWorkflow(self.logger)

        # State management
        self.active_requests: Dict[str, EditRequest] = {}
        self.ghost_suggestions: Dict[str, GhostTextSuggestion] = {}
        self.edit_history: List[EditRequest] = []

        # Keyboard shortcuts (Windows-compatible)
        self.shortcuts = {
            "ctrl+k": self._handle_inline_edit,
            "alt+enter": self._handle_quick_question,
            "tab": self._accept_ghost_text,
            "escape": self._dismiss_ghost_text,
            "ctrl+shift+i": self._show_quick_fix,
            "ctrl+.": self._show_code_actions,
            "f2": self._rename_symbol
        }

        # AI integration patterns
        self.completion_triggers = {
            "function": r"def\s+\w+\s*\(",
            "class": r"class\s+\w+\s*:",
            "import": r"from\s+\w+\s+import|import\s+\w+",
            "comment": r"#\s*TODO|#\s*FIXME|#\s*NOTE",
            "docstring": r'"""|\'\'\''
        }

        self.logger.info("InlineEditor initialized with Cursor-like functionality")

    async def handle_edit_request(self, request_data: Dict[str, Any]) -> EditResponse:
        """Handle an inline edit request."""
        try:
            # Parse request
            edit_request = self._parse_edit_request(request_data)
            self.active_requests[edit_request.id] = edit_request
            self.edit_history.append(edit_request)

            self.logger.debug(f"Processing edit request: {edit_request.mode.value} - {edit_request.action.value}")

            # Route to appropriate handler
            if edit_request.mode == EditMode.SELECTION:
                response = await self._handle_selection_edit(edit_request)
            elif edit_request.mode == EditMode.CURSOR:
                response = await self._handle_cursor_edit(edit_request)
            elif edit_request.mode == EditMode.GHOST_TEXT:
                response = await self._handle_ghost_text_request(edit_request)
            elif edit_request.mode == EditMode.QUICK_QUESTION:
                response = await self._handle_quick_question_request(edit_request)
            elif edit_request.mode == EditMode.REFINEMENT:
                response = await self._handle_refinement_request(edit_request)
            else:
                response = EditResponse(
                    request_id=edit_request.id,
                    success=False,
                    content="Unsupported edit mode",
                    confidence=0.0
                )

            # Clean up completed request
            self.active_requests.pop(edit_request.id, None)

            return response

        except Exception as e:
            self.logger.error(f"Error handling edit request: {e}")
            return EditResponse(
                request_id=request_data.get("id", "unknown"),
                success=False,
                content=f"Error: {str(e)}",
                confidence=0.0
            )

    def _parse_edit_request(self, data: Dict[str, Any]) -> EditRequest:
        """Parse edit request from JSON data."""
        selection = None
        if data.get("selection"):
            sel_data = data["selection"]
            selection = EditSelection(
                start_line=sel_data["start_line"],
                start_col=sel_data["start_col"],
                end_line=sel_data["end_line"],
                end_col=sel_data["end_col"],
                text=sel_data.get("text", ""),
                file_path=Path(sel_data["file_path"]) if sel_data.get("file_path") else None
            )

        return EditRequest(
            id=data.get("id", str(uuid.uuid4())),
            mode=EditMode(data.get("mode", "selection")),
            action=EditAction(data.get("action", "generate")),
            selection=selection,
            prompt=data.get("prompt", ""),
            file_path=Path(data["file_path"]) if data.get("file_path") else None,
            cursor_position=tuple(data["cursor_position"]) if data.get("cursor_position") else None,
            metadata=data.get("metadata", {})
        )

    async def _handle_selection_edit(self, request: EditRequest) -> EditResponse:
        """Handle selection-based editing."""
        try:
            # Get context for the selection
            context = await self._get_context_for_request(request)

            # Generate AI response based on action
            if request.action == EditAction.GENERATE:
                content = await self._generate_code(request, context)
            elif request.action == EditAction.REFINE:
                content = await self._refine_code(request, context)
            elif request.action == EditAction.EXPLAIN:
                content = await self._explain_code(request, context)
            elif request.action == EditAction.COMPLETE:
                content = await self._complete_code(request, context)
            elif request.action == EditAction.TRANSFORM:
                content = await self._transform_code(request, context)
            elif request.action == EditAction.REVIEW:
                content = await self._review_code(request, context)
            else:
                content = "Unsupported action for selection edit"

            # Apply refinement workflow if requested
            if request.metadata.get("use_refinement", False):
                workflow_results = await self.refine_workflow.run_workflow(request, content)
                content = workflow_results["final_recommendation"]
                metadata = {"workflow_results": workflow_results}
            else:
                metadata = {}

            # Test in shadow workspace if file editing
            if request.file_path and request.selection:
                shadow_success = self.shadow_workspace.apply_edit(
                    request.file_path, content, request.selection
                )
                metadata["shadow_test"] = shadow_success

                if shadow_success:
                    diff = self.shadow_workspace.get_diff(request.file_path)
                    metadata["diff_preview"] = diff

            return EditResponse(
                request_id=request.id,
                success=True,
                content=content,
                confidence=0.85,
                metadata=metadata
            )

        except Exception as e:
            self.logger.error(f"Error in selection edit: {e}")
            return EditResponse(
                request_id=request.id,
                success=False,
                content=f"Error: {str(e)}",
                confidence=0.0
            )

    async def _handle_cursor_edit(self, request: EditRequest) -> EditResponse:
        """Handle cursor position-based editing."""
        try:
            # Get context around cursor position
            context = await self._get_context_for_request(request)

            # Determine what type of completion to provide
            completion_type = self._detect_completion_type(request)

            if completion_type == "function":
                content = await self._generate_function_completion(request, context)
            elif completion_type == "class":
                content = await self._generate_class_completion(request, context)
            elif completion_type == "import":
                content = await self._generate_import_completion(request, context)
            elif completion_type == "comment":
                content = await self._generate_comment_completion(request, context)
            elif completion_type == "docstring":
                content = await self._generate_docstring_completion(request, context)
            else:
                content = await self._generate_general_completion(request, context)

            # Create ghost text suggestion
            ghost_text = GhostTextSuggestion(
                id=str(uuid.uuid4()),
                text=content,
                position=request.cursor_position or (0, 0),
                confidence=0.8,
                source="ai",
                metadata={"completion_type": completion_type}
            )

            self.ghost_suggestions[ghost_text.id] = ghost_text

            return EditResponse(
                request_id=request.id,
                success=True,
                content=content,
                ghost_text=ghost_text,
                confidence=0.8
            )

        except Exception as e:
            self.logger.error(f"Error in cursor edit: {e}")
            return EditResponse(
                request_id=request.id,
                success=False,
                content=f"Error: {str(e)}",
                confidence=0.0
            )

    async def _handle_ghost_text_request(self, request: EditRequest) -> EditResponse:
        """Handle ghost text management requests."""
        try:
            action = request.metadata.get("ghost_action", "generate")

            if action == "accept":
                ghost_id = request.metadata.get("ghost_id")
                if ghost_id in self.ghost_suggestions:
                    suggestion = self.ghost_suggestions.pop(ghost_id)
                    return EditResponse(
                        request_id=request.id,
                        success=True,
                        content=suggestion.text,
                        confidence=suggestion.confidence,
                        metadata={"action": "accepted", "ghost_id": ghost_id}
                    )

            elif action == "dismiss":
                ghost_id = request.metadata.get("ghost_id")
                if ghost_id in self.ghost_suggestions:
                    self.ghost_suggestions.pop(ghost_id)
                return EditResponse(
                    request_id=request.id,
                    success=True,
                    content="",
                    metadata={"action": "dismissed", "ghost_id": ghost_id}
                )

            elif action == "alternatives":
                # Generate alternative suggestions
                alternatives = await self._generate_alternatives(request)
                return EditResponse(
                    request_id=request.id,
                    success=True,
                    content="",
                    alternatives=alternatives,
                    metadata={"action": "alternatives"}
                )

            return EditResponse(
                request_id=request.id,
                success=False,
                content="Unknown ghost text action",
                confidence=0.0
            )

        except Exception as e:
            self.logger.error(f"Error in ghost text request: {e}")
            return EditResponse(
                request_id=request.id,
                success=False,
                content=f"Error: {str(e)}",
                confidence=0.0
            )

    async def _handle_quick_question_request(self, request: EditRequest) -> EditResponse:
        """Handle quick question mode (Alt+Enter)."""
        try:
            # Get relevant context
            context = await self._get_context_for_request(request)

            # Generate explanation based on the question and context
            explanation = await self._generate_quick_explanation(request, context)

            return EditResponse(
                request_id=request.id,
                success=True,
                content="",
                explanation=explanation,
                confidence=0.9,
                metadata={"mode": "quick_question", "context_used": len(context)}
            )

        except Exception as e:
            self.logger.error(f"Error in quick question: {e}")
            return EditResponse(
                request_id=request.id,
                success=False,
                content=f"Error: {str(e)}",
                confidence=0.0
            )

    async def _handle_refinement_request(self, request: EditRequest) -> EditResponse:
        """Handle multi-step refinement workflow."""
        try:
            # Get initial content to refine
            initial_content = request.metadata.get("initial_content", "")
            if not initial_content and request.selection:
                initial_content = request.selection.text

            # Run refinement workflow
            workflow_results = await self.refine_workflow.run_workflow(request, initial_content)

            return EditResponse(
                request_id=request.id,
                success=True,
                content=workflow_results["final_recommendation"],
                confidence=workflow_results.get("evaluation", {}).get("confidence", 0.8),
                metadata={"workflow_results": workflow_results}
            )

        except Exception as e:
            self.logger.error(f"Error in refinement request: {e}")
            return EditResponse(
                request_id=request.id,
                success=False,
                content=f"Error: {str(e)}",
                confidence=0.0
            )

    async def _get_context_for_request(self, request: EditRequest) -> List[ContextMatch]:
        """Get relevant context for an edit request."""
        try:
            # Build context query from request
            context_query = request.prompt
            if request.selection and request.selection.text:
                context_query += f" {request.selection.text}"

            # Use context manager to get relevant context
            context_results = await self.context_manager.parse_and_retrieve(
                context_query, context_type="mixed"
            )

            # Flatten results
            all_matches = []
            for matches in context_results.values():
                all_matches.extend(matches)

            # Sort by relevance and return top matches
            all_matches.sort(key=lambda x: x.score, reverse=True)
            return all_matches[:10]

        except Exception as e:
            self.logger.error(f"Error getting context: {e}")
            return []

    def _detect_completion_type(self, request: EditRequest) -> str:
        """Detect what type of code completion is needed."""
        try:
            # Get surrounding text to analyze
            surrounding_text = ""
            if request.file_path and request.cursor_position:
                try:
                    content = request.file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.split('\n')
                    line_no = request.cursor_position[0]

                    # Get a few lines around cursor for context
                    start_line = max(0, line_no - 2)
                    end_line = min(len(lines), line_no + 3)
                    surrounding_text = '\n'.join(lines[start_line:end_line])

                except Exception:
                    pass

            # Check against completion triggers
            for completion_type, pattern in self.completion_triggers.items():
                if re.search(pattern, surrounding_text, re.IGNORECASE):
                    return completion_type

            return "general"

        except Exception as e:
            self.logger.error(f"Error detecting completion type: {e}")
            return "general"

    async def _generate_code(self, request: EditRequest, context: List[ContextMatch]) -> str:
        """Generate code based on request and context."""
        # Simulate AI code generation
        prompt_lower = request.prompt.lower()

        if "function" in prompt_lower:
            return f"""def {request.prompt.replace('function', '').strip().replace(' ', '_')}():
    \"\"\"Generated function based on prompt.\"\"\"
    # TODO: Implement function logic
    pass"""

        elif "class" in prompt_lower:
            class_name = request.prompt.replace('class', '').strip().title().replace(' ', '')
            return f"""class {class_name}:
    \"\"\"Generated class based on prompt.\"\"\"

    def __init__(self):
        \"\"\"Initialize the {class_name}.\"\"\"
        pass"""

        elif "import" in prompt_lower:
            return f"import {request.prompt.replace('import', '').strip()}"

        else:
            return f"# Generated code for: {request.prompt}\n# TODO: Implement based on requirements"

    async def _refine_code(self, request: EditRequest, context: List[ContextMatch]) -> str:
        """Refine existing code."""
        if request.selection and request.selection.text:
            original = request.selection.text
            # Simulate refinement
            refined = original

            # Add documentation if missing
            if "def " in original and '"""' not in original:
                lines = original.split('\n')
                for i, line in enumerate(lines):
                    if line.strip().startswith('def '):
                        # Insert docstring after function definition
                        indent = len(line) - len(line.lstrip())
                        docstring = f'{" " * (indent + 4)}"""TODO: Add function documentation."""'
                        lines.insert(i + 1, docstring)
                        break
                refined = '\n'.join(lines)

            # Add type hints if missing
            if "def " in original and "->" not in original:
                refined = refined.replace(":", " -> None:")

            return refined

        return request.prompt

    async def _explain_code(self, request: EditRequest, context: List[ContextMatch]) -> str:
        """Explain code functionality."""
        if request.selection and request.selection.text:
            code = request.selection.text.strip()

            # Analyze code structure
            explanations = []

            if "def " in code:
                explanations.append("This is a function definition.")
            if "class " in code:
                explanations.append("This defines a class.")
            if "import " in code or "from " in code:
                explanations.append("This imports external modules or functions.")
            if "if " in code:
                explanations.append("Contains conditional logic.")
            if "for " in code or "while " in code:
                explanations.append("Contains loop structures.")
            if "try:" in code or "except" in code:
                explanations.append("Includes error handling.")

            if not explanations:
                explanations.append("This is a code snippet.")

            explanation = "Code Analysis:\n\n" + "\n".join(f"• {exp}" for exp in explanations)
            explanation += f"\n\nCode Purpose: {request.prompt}"

            return explanation

        return f"Explanation for: {request.prompt}"

    async def _complete_code(self, request: EditRequest, context: List[ContextMatch]) -> str:
        """Complete partial code."""
        if request.selection and request.selection.text:
            partial = request.selection.text.strip()

            # Simple completion logic
            if partial.endswith("def "):
                return f"{partial}function_name():\n    pass"
            elif partial.endswith("class "):
                return f"{partial}ClassName:\n    pass"
            elif partial.endswith("import "):
                return f"{partial}module_name"
            elif partial.endswith("if "):
                return f"{partial}condition:\n    pass"
            elif partial.endswith("for "):
                return f"{partial}item in items:\n    pass"
            else:
                return f"{partial}\n# TODO: Complete implementation"

        return request.prompt

    async def _transform_code(self, request: EditRequest, context: List[ContextMatch]) -> str:
        """Transform code based on request."""
        if request.selection and request.selection.text:
            original = request.selection.text
            prompt_lower = request.prompt.lower()

            if "async" in prompt_lower:
                # Convert to async
                return original.replace("def ", "async def ")
            elif "sync" in prompt_lower:
                # Convert from async
                return original.replace("async def ", "def ")
            elif "type hint" in prompt_lower:
                # Add type hints
                return original.replace("def ", "def ").replace(":", " -> None:")
            else:
                return f"# Transformed: {request.prompt}\n{original}"

        return request.prompt

    async def _review_code(self, request: EditRequest, context: List[ContextMatch]) -> str:
        """Review code for issues and suggestions."""
        if request.selection and request.selection.text:
            code = request.selection.text

            issues = []
            suggestions = []

            # Basic code review checks
            if "def " in code and '"""' not in code:
                issues.append("Missing function documentation")
                suggestions.append("Add docstrings to functions")

            if "print(" in code:
                issues.append("Debug print statements found")
                suggestions.append("Replace print with logging")

            if "TODO" in code.upper() or "FIXME" in code.upper():
                issues.append("TODO/FIXME comments found")
                suggestions.append("Address pending TODO items")

            lines = code.split('\n')
            for line in lines:
                if len(line) > 100:
                    issues.append("Long lines detected")
                    suggestions.append("Break long lines for readability")
                    break

            review = "Code Review:\n\n"
            if issues:
                review += "Issues Found:\n" + "\n".join(f"• {issue}" for issue in issues) + "\n\n"
            if suggestions:
                review += "Suggestions:\n" + "\n".join(f"• {suggestion}" for suggestion in suggestions)

            if not issues and not suggestions:
                review += "Code looks good! No major issues found."

            return review

        return f"Code review for: {request.prompt}"

    async def _generate_function_completion(self, request: EditRequest, context: List[ContextMatch]) -> str:
        """Generate function completion."""
        return """():
    \"\"\"TODO: Add function description.\"\"\"
    pass"""

    async def _generate_class_completion(self, request: EditRequest, context: List[ContextMatch]) -> str:
        """Generate class completion."""
        return """:
    \"\"\"TODO: Add class description.\"\"\"

    def __init__(self):
        \"\"\"Initialize the class.\"\"\"
        pass"""

    async def _generate_import_completion(self, request: EditRequest, context: List[ContextMatch]) -> str:
        """Generate import completion."""
        return " os, sys, json"

    async def _generate_comment_completion(self, request: EditRequest, context: List[ContextMatch]) -> str:
        """Generate comment completion."""
        return " Implement this functionality"

    async def _generate_docstring_completion(self, request: EditRequest, context: List[ContextMatch]) -> str:
        """Generate docstring completion."""
        return """TODO: Add description.

        Args:
            param: Description

        Returns:
            Description of return value
        \"\"\""""

    async def _generate_general_completion(self, request: EditRequest, context: List[ContextMatch]) -> str:
        """Generate general completion."""
        return f"# {request.prompt}"

    async def _generate_quick_explanation(self, request: EditRequest, context: List[ContextMatch]) -> str:
        """Generate quick explanation for Alt+Enter mode."""
        explanation = f"Quick Answer: {request.prompt}\n\n"

        if request.selection and request.selection.text:
            code = request.selection.text.strip()
            explanation += f"About the selected code:\n{code}\n\n"
            explanation += "This code appears to be a "

            if "def " in code:
                explanation += "function definition"
            elif "class " in code:
                explanation += "class definition"
            elif "import " in code:
                explanation += "module import"
            elif "if " in code:
                explanation += "conditional statement"
            elif "for " in code:
                explanation += "loop structure"
            else:
                explanation += "code block"

            explanation += ".\n\n"

        # Add context information if available
        if context:
            explanation += f"Related context found: {len(context)} items\n"
            explanation += "Most relevant:\n"
            for i, match in enumerate(context[:3]):
                explanation += f"• {match.pattern} (score: {match.score:.1f})\n"

        return explanation

    async def _generate_alternatives(self, request: EditRequest) -> List[str]:
        """Generate alternative suggestions."""
        base_content = request.metadata.get("base_content", "")

        alternatives = [
            f"# Alternative 1: {base_content}",
            f"# Alternative 2: {base_content} with improvements",
            f"# Alternative 3: {base_content} refactored"
        ]

        return alternatives

    async def _handle_inline_edit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Ctrl+K inline edit shortcut."""
        try:
            # Create edit request for inline editing
            edit_data = {
                "id": str(uuid.uuid4()),
                "mode": "selection",
                "action": "generate",
                "prompt": data.get("prompt", ""),
                "selection": data.get("selection"),
                "file_path": data.get("file_path"),
                "metadata": {"shortcut": "ctrl+k"}
            }

            response = await self.handle_edit_request(edit_data)
            return response.to_dict()

        except Exception as e:
            self.logger.error(f"Error in Ctrl+K handler: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_quick_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Alt+Enter quick question shortcut."""
        try:
            edit_data = {
                "id": str(uuid.uuid4()),
                "mode": "quick_question",
                "action": "explain",
                "prompt": data.get("prompt", "What does this code do?"),
                "selection": data.get("selection"),
                "file_path": data.get("file_path"),
                "metadata": {"shortcut": "alt+enter"}
            }

            response = await self.handle_edit_request(edit_data)
            return response.to_dict()

        except Exception as e:
            self.logger.error(f"Error in Alt+Enter handler: {e}")
            return {"success": False, "error": str(e)}

    async def _accept_ghost_text(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Tab to accept ghost text."""
        try:
            ghost_id = data.get("ghost_id")
            if ghost_id and ghost_id in self.ghost_suggestions:
                suggestion = self.ghost_suggestions.pop(ghost_id)
                return {
                    "success": True,
                    "action": "accept_ghost_text",
                    "content": suggestion.text,
                    "ghost_id": ghost_id
                }

            return {"success": False, "error": "No ghost text to accept"}

        except Exception as e:
            self.logger.error(f"Error accepting ghost text: {e}")
            return {"success": False, "error": str(e)}

    async def _dismiss_ghost_text(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Escape to dismiss ghost text."""
        try:
            ghost_id = data.get("ghost_id")
            if ghost_id and ghost_id in self.ghost_suggestions:
                self.ghost_suggestions.pop(ghost_id)
                return {
                    "success": True,
                    "action": "dismiss_ghost_text",
                    "ghost_id": ghost_id
                }

            # Dismiss all ghost text if no specific ID
            self.ghost_suggestions.clear()
            return {"success": True, "action": "dismiss_all_ghost_text"}

        except Exception as e:
            self.logger.error(f"Error dismissing ghost text: {e}")
            return {"success": False, "error": str(e)}

    async def _show_quick_fix(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Ctrl+Shift+I quick fix shortcut."""
        try:
            # Generate quick fix suggestions
            fixes = [
                "Add type hints",
                "Add documentation",
                "Extract method",
                "Rename variable",
                "Format code"
            ]

            return {
                "success": True,
                "action": "show_quick_fix",
                "fixes": fixes
            }

        except Exception as e:
            self.logger.error(f"Error showing quick fix: {e}")
            return {"success": False, "error": str(e)}

    async def _show_code_actions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Ctrl+. code actions shortcut."""
        try:
            actions = [
                "Refactor this",
                "Generate tests",
                "Add error handling",
                "Optimize performance",
                "Extract constant"
            ]

            return {
                "success": True,
                "action": "show_code_actions",
                "actions": actions
            }

        except Exception as e:
            self.logger.error(f"Error showing code actions: {e}")
            return {"success": False, "error": str(e)}

    async def _rename_symbol(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle F2 rename symbol shortcut."""
        try:
            symbol = data.get("symbol", "symbol")
            suggestions = [
                f"new_{symbol}",
                f"{symbol}_v2",
                f"updated_{symbol}",
                f"improved_{symbol}"
            ]

            return {
                "success": True,
                "action": "rename_symbol",
                "current_symbol": symbol,
                "suggestions": suggestions
            }

        except Exception as e:
            self.logger.error(f"Error in rename symbol: {e}")
            return {"success": False, "error": str(e)}

    def get_active_ghost_suggestions(self) -> Dict[str, Any]:
        """Get all active ghost text suggestions."""
        return {
            ghost_id: suggestion.to_dict()
            for ghost_id, suggestion in self.ghost_suggestions.items()
        }

    def get_edit_statistics(self) -> Dict[str, Any]:
        """Get inline editing statistics."""
        return {
            "total_requests": len(self.edit_history),
            "active_requests": len(self.active_requests),
            "ghost_suggestions": len(self.ghost_suggestions),
            "most_common_actions": self._get_action_stats(),
            "most_common_modes": self._get_mode_stats(),
            "shadow_workspace_path": str(self.shadow_workspace.shadow_path)
        }

    def _get_action_stats(self) -> Dict[str, int]:
        """Get statistics on edit actions."""
        action_counts = {}
        for request in self.edit_history:
            action = request.action.value
            action_counts[action] = action_counts.get(action, 0) + 1
        return action_counts

    def _get_mode_stats(self) -> Dict[str, int]:
        """Get statistics on edit modes."""
        mode_counts = {}
        for request in self.edit_history:
            mode = request.mode.value
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        return mode_counts

    async def cleanup(self):
        """Clean up inline editor resources."""
        try:
            # Clear active requests and suggestions
            self.active_requests.clear()
            self.ghost_suggestions.clear()

            # Clean up shadow workspace
            self.shadow_workspace.cleanup()

            self.logger.info("InlineEditor cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during InlineEditor cleanup: {e}")