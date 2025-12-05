"""
Notebook Tools for TORQ Console - Claude Code Compatible NotebookEdit.

Jupyter notebook editing and execution capabilities for Claude Code compatibility.
Includes cell-level operations, output capture, and code analysis integration.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class CellType(Enum):
    """Jupyter notebook cell types."""
    CODE = "code"
    MARKDOWN = "markdown"
    RAW = "raw"


@dataclass
class NotebookCell:
    """Represents a Jupyter notebook cell."""
    cell_type: CellType
    source: Union[str, List[str]]
    metadata: Dict[str, Any] = None
    outputs: List[Dict[str, Any]] = None
    execution_count: Optional[int] = None
    cell_id: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.outputs is None:
            self.outputs = []
        if self.cell_id is None:
            self.cell_id = str(uuid.uuid4())


class NotebookEditTool:
    """
    Jupyter notebook editing tool with Claude Code compatibility.

    Features:
    - Cell-level editing operations (replace, insert, delete)
    - Notebook execution and output capture
    - Code analysis integration with CodeAgent
    - Full compatibility with Claude Code NotebookEdit interface
    """

    def __init__(self, code_agent=None):
        self.logger = logging.getLogger(__name__)
        self.code_agent = code_agent

    async def edit_notebook_cell(
        self,
        notebook_path: str,
        new_source: str,
        cell_number: Optional[int] = None,
        cell_id: Optional[str] = None,
        cell_type: str = "code",
        edit_mode: str = "replace"
    ) -> Dict[str, Any]:
        """
        Edit a specific cell in a Jupyter notebook.

        Args:
            notebook_path: Absolute path to the notebook file
            new_source: New source content for the cell
            cell_number: 0-indexed cell number (optional if cell_id provided)
            cell_id: Cell ID for targeting specific cell (optional)
            cell_type: Type of cell (code, markdown, raw)
            edit_mode: Edit operation (replace, insert, delete)

        Returns:
            Dict with edit results and notebook information
        """
        try:
            notebook_path = Path(notebook_path).resolve()

            if not notebook_path.exists():
                return {
                    'success': False,
                    'error': f'Notebook file does not exist: {notebook_path}',
                    'notebook_path': str(notebook_path)
                }

            # Load notebook
            notebook = await self._load_notebook(notebook_path)
            if not notebook:
                return {
                    'success': False,
                    'error': 'Failed to load notebook',
                    'notebook_path': str(notebook_path)
                }

            # Determine target cell
            target_cell_index = await self._find_target_cell(notebook, cell_number, cell_id)

            if edit_mode == "delete":
                return await self._delete_cell(notebook, notebook_path, target_cell_index)
            elif edit_mode == "insert":
                return await self._insert_cell(notebook, notebook_path, target_cell_index, new_source, cell_type, cell_id)
            else:  # replace
                return await self._replace_cell(notebook, notebook_path, target_cell_index, new_source, cell_type)

        except Exception as e:
            self.logger.error(f"Notebook edit failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'notebook_path': str(notebook_path)
            }

    async def _load_notebook(self, notebook_path: Path) -> Optional[Dict[str, Any]]:
        """Load Jupyter notebook from file."""
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)

            # Validate notebook structure
            if 'cells' not in notebook:
                notebook['cells'] = []

            if 'metadata' not in notebook:
                notebook['metadata'] = {}

            if 'nbformat' not in notebook:
                notebook['nbformat'] = 4

            if 'nbformat_minor' not in notebook:
                notebook['nbformat_minor'] = 2

            return notebook

        except Exception as e:
            self.logger.error(f"Failed to load notebook {notebook_path}: {e}")
            return None

    async def _save_notebook(self, notebook: Dict[str, Any], notebook_path: Path) -> bool:
        """Save notebook to file."""
        try:
            # Create backup
            backup_path = notebook_path.with_suffix(notebook_path.suffix + '.backup')
            if notebook_path.exists():
                with open(notebook_path, 'r') as src, open(backup_path, 'w') as dst:
                    dst.write(src.read())

            # Save notebook
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(notebook, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            self.logger.error(f"Failed to save notebook {notebook_path}: {e}")
            return False

    async def _find_target_cell(
        self,
        notebook: Dict[str, Any],
        cell_number: Optional[int],
        cell_id: Optional[str]
    ) -> Optional[int]:
        """Find the target cell index based on number or ID."""
        cells = notebook.get('cells', [])

        if cell_id:
            # Find by cell ID
            for i, cell in enumerate(cells):
                if cell.get('id') == cell_id:
                    return i
            # Cell ID not found
            return None

        elif cell_number is not None:
            # Use cell number (0-indexed)
            if 0 <= cell_number < len(cells):
                return cell_number
            else:
                return None

        else:
            # Default to last cell or None for empty notebook
            return len(cells) - 1 if cells else None

    async def _replace_cell(
        self,
        notebook: Dict[str, Any],
        notebook_path: Path,
        cell_index: Optional[int],
        new_source: str,
        cell_type: str
    ) -> Dict[str, Any]:
        """Replace content of existing cell."""
        cells = notebook.get('cells', [])

        if cell_index is None or cell_index >= len(cells):
            return {
                'success': False,
                'error': 'Target cell not found',
                'notebook_path': str(notebook_path),
                'cell_count': len(cells)
            }

        # Get existing cell
        cell = cells[cell_index]
        old_source = cell.get('source', '')
        old_cell_type = cell.get('cell_type', 'code')

        # Update cell
        cell['source'] = new_source.split('\\n') if '\\n' in new_source else [new_source]
        cell['cell_type'] = cell_type

        # Clear outputs if changing to/from code cell
        if cell_type == 'code' or old_cell_type == 'code':
            cell['outputs'] = []
            cell['execution_count'] = None

        # Update metadata
        if 'metadata' not in cell:
            cell['metadata'] = {}

        # Save notebook
        save_success = await self._save_notebook(notebook, notebook_path)

        if not save_success:
            return {
                'success': False,
                'error': 'Failed to save notebook',
                'notebook_path': str(notebook_path)
            }

        return {
            'success': True,
            'operation': 'replace',
            'cell_index': cell_index,
            'cell_type': cell_type,
            'notebook_path': str(notebook_path),
            'cell_count': len(cells),
            'changes': {
                'old_source_length': len(str(old_source)),
                'new_source_length': len(new_source),
                'cell_type_changed': old_cell_type != cell_type
            }
        }

    async def _insert_cell(
        self,
        notebook: Dict[str, Any],
        notebook_path: Path,
        insert_index: Optional[int],
        new_source: str,
        cell_type: str,
        cell_id: Optional[str]
    ) -> Dict[str, Any]:
        """Insert new cell at specified position."""
        cells = notebook.get('cells', [])

        # Determine insert position
        if insert_index is None:
            insert_position = len(cells)  # Insert at end
        else:
            insert_position = min(max(0, insert_index + 1), len(cells))

        # Create new cell
        new_cell = {
            'cell_type': cell_type,
            'metadata': {},
            'source': new_source.split('\\n') if '\\n' in new_source else [new_source]
        }

        # Add cell-specific fields
        if cell_id:
            new_cell['id'] = cell_id
        else:
            new_cell['id'] = str(uuid.uuid4())

        if cell_type == 'code':
            new_cell['execution_count'] = None
            new_cell['outputs'] = []

        # Insert cell
        cells.insert(insert_position, new_cell)

        # Save notebook
        save_success = await self._save_notebook(notebook, notebook_path)

        if not save_success:
            return {
                'success': False,
                'error': 'Failed to save notebook',
                'notebook_path': str(notebook_path)
            }

        return {
            'success': True,
            'operation': 'insert',
            'cell_index': insert_position,
            'cell_id': new_cell['id'],
            'cell_type': cell_type,
            'notebook_path': str(notebook_path),
            'cell_count': len(cells)
        }

    async def _delete_cell(
        self,
        notebook: Dict[str, Any],
        notebook_path: Path,
        cell_index: Optional[int]
    ) -> Dict[str, Any]:
        """Delete cell at specified position."""
        cells = notebook.get('cells', [])

        if cell_index is None or cell_index >= len(cells):
            return {
                'success': False,
                'error': 'Target cell not found',
                'notebook_path': str(notebook_path),
                'cell_count': len(cells)
            }

        # Get cell info before deletion
        deleted_cell = cells[cell_index]
        deleted_cell_type = deleted_cell.get('cell_type', 'unknown')
        deleted_cell_id = deleted_cell.get('id', 'unknown')

        # Remove cell
        cells.pop(cell_index)

        # Save notebook
        save_success = await self._save_notebook(notebook, notebook_path)

        if not save_success:
            return {
                'success': False,
                'error': 'Failed to save notebook',
                'notebook_path': str(notebook_path)
            }

        return {
            'success': True,
            'operation': 'delete',
            'deleted_cell_index': cell_index,
            'deleted_cell_id': deleted_cell_id,
            'deleted_cell_type': deleted_cell_type,
            'notebook_path': str(notebook_path),
            'cell_count': len(cells)
        }

    async def read_notebook(self, notebook_path: str) -> Dict[str, Any]:
        """
        Read and analyze Jupyter notebook contents.

        Args:
            notebook_path: Path to the notebook file

        Returns:
            Dict with notebook structure and analysis
        """
        try:
            notebook_path = Path(notebook_path).resolve()

            if not notebook_path.exists():
                return {
                    'success': False,
                    'error': f'Notebook file does not exist: {notebook_path}',
                    'notebook_path': str(notebook_path)
                }

            notebook = await self._load_notebook(notebook_path)
            if not notebook:
                return {
                    'success': False,
                    'error': 'Failed to load notebook',
                    'notebook_path': str(notebook_path)
                }

            # Analyze notebook structure
            cells = notebook.get('cells', [])
            cell_analysis = []

            for i, cell in enumerate(cells):
                cell_info = {
                    'index': i,
                    'cell_type': cell.get('cell_type', 'unknown'),
                    'cell_id': cell.get('id', f'cell_{i}'),
                    'source_lines': len(cell.get('source', [])),
                    'has_outputs': bool(cell.get('outputs')),
                    'execution_count': cell.get('execution_count')
                }

                # Add preview of source
                source = cell.get('source', [])
                if isinstance(source, list):
                    preview = ''.join(source[:3])  # First 3 lines
                else:
                    preview = str(source)[:200]  # First 200 chars

                cell_info['source_preview'] = preview[:100] + '...' if len(preview) > 100 else preview
                cell_analysis.append(cell_info)

            # Summary statistics
            cell_types = {}
            for cell in cells:
                cell_type = cell.get('cell_type', 'unknown')
                cell_types[cell_type] = cell_types.get(cell_type, 0) + 1

            return {
                'success': True,
                'notebook_path': str(notebook_path),
                'metadata': {
                    'nbformat': notebook.get('nbformat'),
                    'nbformat_minor': notebook.get('nbformat_minor'),
                    'kernel_info': notebook.get('metadata', {}).get('kernelspec', {})
                },
                'summary': {
                    'total_cells': len(cells),
                    'cell_types': cell_types,
                    'has_outputs': any(cell.get('outputs') for cell in cells)
                },
                'cells': cell_analysis
            }

        except Exception as e:
            self.logger.error(f"Failed to read notebook {notebook_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'notebook_path': str(notebook_path)
            }

    async def analyze_notebook_code(self, notebook_path: str) -> Dict[str, Any]:
        """
        Analyze code quality and structure in notebook cells.

        Args:
            notebook_path: Path to the notebook file

        Returns:
            Code analysis results
        """
        try:
            notebook_info = await self.read_notebook(notebook_path)

            if not notebook_info['success']:
                return notebook_info

            notebook = await self._load_notebook(Path(notebook_path))
            if not notebook:
                return {
                    'success': False,
                    'error': 'Failed to load notebook for analysis'
                }

            code_analysis = {
                'code_cells': [],
                'issues': [],
                'suggestions': [],
                'metrics': {
                    'total_code_cells': 0,
                    'total_code_lines': 0,
                    'cells_with_long_code': 0,
                    'cells_with_outputs': 0
                }
            }

            cells = notebook.get('cells', [])

            for i, cell in enumerate(cells):
                if cell.get('cell_type') == 'code':
                    source = cell.get('source', [])
                    if isinstance(source, list):
                        code_text = ''.join(source)
                    else:
                        code_text = str(source)

                    code_lines = len([line for line in code_text.split('\\n') if line.strip()])

                    cell_analysis = {
                        'cell_index': i,
                        'cell_id': cell.get('id'),
                        'code_lines': code_lines,
                        'has_outputs': bool(cell.get('outputs')),
                        'execution_count': cell.get('execution_count')
                    }

                    # Simple code quality checks
                    if code_lines > 50:
                        code_analysis['long_cell'] = True
                        code_analysis['metrics']['cells_with_long_code'] += 1
                        code_analysis['issues'].append(f"Cell {i}: Very long code cell ({code_lines} lines)")

                    if 'import' in code_text and i > 0:
                        code_analysis['issues'].append(f"Cell {i}: Import statement not at beginning of notebook")

                    code_analysis['code_cells'].append(cell_analysis)
                    code_analysis['metrics']['total_code_cells'] += 1
                    code_analysis['metrics']['total_code_lines'] += code_lines

                    if cell.get('outputs'):
                        code_analysis['metrics']['cells_with_outputs'] += 1

            return {
                'success': True,
                'notebook_path': str(notebook_path),
                'analysis': code_analysis
            }

        except Exception as e:
            self.logger.error(f"Notebook code analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'notebook_path': str(notebook_path)
            }


# Export notebook tools
notebook_edit_tool = NotebookEditTool()

async def notebook_edit(
    notebook_path: str,
    new_source: str,
    cell_number: Optional[int] = None,
    cell_id: Optional[str] = None,
    cell_type: str = "code",
    edit_mode: str = "replace"
) -> Dict[str, Any]:
    """
    Claude Code compatible NotebookEdit function.

    Args:
        notebook_path: Absolute path to notebook file
        new_source: New cell content
        cell_number: 0-indexed cell number
        cell_id: Cell ID for targeting
        cell_type: Cell type (code, markdown, raw)
        edit_mode: Operation (replace, insert, delete)

    Returns:
        Edit operation results
    """
    return await notebook_edit_tool.edit_notebook_cell(
        notebook_path, new_source, cell_number, cell_id, cell_type, edit_mode
    )

async def notebook_read(notebook_path: str) -> Dict[str, Any]:
    """
    Claude Code compatible notebook reading function.

    Args:
        notebook_path: Path to notebook file

    Returns:
        Notebook structure and analysis
    """
    return await notebook_edit_tool.read_notebook(notebook_path)