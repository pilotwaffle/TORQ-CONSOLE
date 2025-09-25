"""
Edit Tools for TORQ Console - Claude Code Compatible MultiEdit Tool.

Implements MultiEdit functionality for batch file operations.
Compatible with Claude Code's editing patterns and safety features.
"""

import asyncio
import logging
import os
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, NamedTuple
from dataclasses import dataclass


@dataclass
class EditOperation:
    """Represents a single edit operation."""
    old_string: str
    new_string: str
    replace_all: bool = False


@dataclass
class EditResult:
    """Result of a single edit operation."""
    success: bool
    operation_index: int
    old_string: str
    new_string: str
    replacements_made: int
    error: Optional[str] = None


class MultiEditTool:
    """
    Multi-edit tool for batch file operations.

    Built on top of standard string replacement operations and compatible
    with Claude Code's MultiEdit tool interface and safety features.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def multi_edit(
        self,
        file_path: str,
        edits: List[Dict[str, Any]],
        create_backup: bool = True,
        validate_before_save: bool = True
    ) -> Dict[str, Any]:
        """
        Perform multiple edits on a single file in one operation.

        Args:
            file_path: Absolute path to the file to modify
            edits: List of edit operations, each with old_string, new_string, replace_all
            create_backup: Create backup file before editing
            validate_before_save: Validate all edits before applying any

        Returns:
            Dict with edit results and file information
        """
        try:
            return await asyncio.to_thread(
                self._multi_edit_sync,
                file_path, edits, create_backup, validate_before_save
            )
        except Exception as e:
            self.logger.error(f"MultiEdit failed for {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'edits_attempted': len(edits),
                'edits_successful': 0,
                'results': []
            }

    def _multi_edit_sync(
        self,
        file_path: str,
        edits: List[Dict[str, Any]],
        create_backup: bool = True,
        validate_before_save: bool = True
    ) -> Dict[str, Any]:
        """Synchronous multi-edit implementation."""

        start_time = time.time()

        # Convert to Path object
        file_path = Path(file_path).resolve()

        # Validate file exists
        if not file_path.exists():
            return {
                'success': False,
                'error': f"File does not exist: {file_path}",
                'file_path': str(file_path),
                'edits_attempted': len(edits),
                'edits_successful': 0,
                'results': []
            }

        if not file_path.is_file():
            return {
                'success': False,
                'error': f"Path is not a file: {file_path}",
                'file_path': str(file_path),
                'edits_attempted': len(edits),
                'edits_successful': 0,
                'results': []
            }

        # Parse edit operations
        edit_operations = []
        for i, edit_dict in enumerate(edits):
            try:
                operation = EditOperation(
                    old_string=edit_dict['old_string'],
                    new_string=edit_dict['new_string'],
                    replace_all=edit_dict.get('replace_all', False)
                )
                edit_operations.append(operation)
            except KeyError as e:
                return {
                    'success': False,
                    'error': f"Invalid edit operation {i}: missing {e}",
                    'file_path': str(file_path),
                    'edits_attempted': len(edits),
                    'edits_successful': 0,
                    'results': []
                }

        # Read original file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except (IOError, UnicodeDecodeError) as e:
            return {
                'success': False,
                'error': f"Could not read file: {e}",
                'file_path': str(file_path),
                'edits_attempted': len(edits),
                'edits_successful': 0,
                'results': []
            }

        # Create backup if requested
        backup_path = None
        if create_backup:
            try:
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                shutil.copy2(file_path, backup_path)
            except (IOError, OSError) as e:
                self.logger.warning(f"Could not create backup: {e}")

        # Validate all edits before applying (if requested)
        if validate_before_save:
            validation_result = self._validate_edits(original_content, edit_operations)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': f"Edit validation failed: {validation_result['error']}",
                    'file_path': str(file_path),
                    'edits_attempted': len(edits),
                    'edits_successful': 0,
                    'results': [],
                    'validation_error': validation_result['error']
                }

        # Apply edits sequentially
        current_content = original_content
        edit_results = []
        successful_edits = 0

        for i, operation in enumerate(edit_operations):
            try:
                # Check if old_string exists in current content
                if operation.old_string not in current_content:
                    edit_results.append(EditResult(
                        success=False,
                        operation_index=i,
                        old_string=operation.old_string,
                        new_string=operation.new_string,
                        replacements_made=0,
                        error=f"String not found: '{operation.old_string[:100]}...'"
                    ))
                    continue

                # Check for identical strings
                if operation.old_string == operation.new_string:
                    edit_results.append(EditResult(
                        success=False,
                        operation_index=i,
                        old_string=operation.old_string,
                        new_string=operation.new_string,
                        replacements_made=0,
                        error="old_string and new_string are identical"
                    ))
                    continue

                # Perform replacement
                if operation.replace_all:
                    replacements_made = current_content.count(operation.old_string)
                    current_content = current_content.replace(operation.old_string, operation.new_string)
                else:
                    # Single replacement
                    if current_content.count(operation.old_string) > 1:
                        edit_results.append(EditResult(
                            success=False,
                            operation_index=i,
                            old_string=operation.old_string,
                            new_string=operation.new_string,
                            replacements_made=0,
                            error=f"String appears {current_content.count(operation.old_string)} times. Use replace_all=true for multiple replacements"
                        ))
                        continue

                    replacements_made = 1
                    current_content = current_content.replace(operation.old_string, operation.new_string, 1)

                edit_results.append(EditResult(
                    success=True,
                    operation_index=i,
                    old_string=operation.old_string,
                    new_string=operation.new_string,
                    replacements_made=replacements_made
                ))
                successful_edits += 1

            except Exception as e:
                edit_results.append(EditResult(
                    success=False,
                    operation_index=i,
                    old_string=operation.old_string,
                    new_string=operation.new_string,
                    replacements_made=0,
                    error=f"Edit failed: {e}"
                ))

        # Write modified content back to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(current_content)
        except (IOError, OSError) as e:
            return {
                'success': False,
                'error': f"Could not write file: {e}",
                'file_path': str(file_path),
                'edits_attempted': len(edits),
                'edits_successful': successful_edits,
                'results': [vars(result) for result in edit_results],
                'backup_path': str(backup_path) if backup_path else None
            }

        edit_time = time.time() - start_time

        return {
            'success': successful_edits > 0,
            'file_path': str(file_path),
            'edits_attempted': len(edits),
            'edits_successful': successful_edits,
            'results': [vars(result) for result in edit_results],
            'backup_path': str(backup_path) if backup_path else None,
            'edit_time_ms': round(edit_time * 1000, 2),
            'content_changed': current_content != original_content,
            'original_size': len(original_content),
            'final_size': len(current_content)
        }

    def _validate_edits(
        self,
        content: str,
        edit_operations: List[EditOperation]
    ) -> Dict[str, Any]:
        """Validate all edit operations before applying."""

        # Simulate applying all edits to check for conflicts
        test_content = content

        for i, operation in enumerate(edit_operations):
            # Check if string exists
            if operation.old_string not in test_content:
                return {
                    'valid': False,
                    'error': f"Edit {i}: String not found: '{operation.old_string[:100]}...'"
                }

            # Check for identical strings
            if operation.old_string == operation.new_string:
                return {
                    'valid': False,
                    'error': f"Edit {i}: old_string and new_string are identical"
                }

            # Check uniqueness for single replacements
            if not operation.replace_all and test_content.count(operation.old_string) > 1:
                return {
                    'valid': False,
                    'error': f"Edit {i}: String appears multiple times but replace_all=false"
                }

            # Apply the edit to test content
            if operation.replace_all:
                test_content = test_content.replace(operation.old_string, operation.new_string)
            else:
                test_content = test_content.replace(operation.old_string, operation.new_string, 1)

        return {'valid': True}

    async def single_edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False
    ) -> Dict[str, Any]:
        """
        Perform a single edit operation (wrapper for compatibility).

        Args:
            file_path: Path to file to edit
            old_string: Text to replace
            new_string: Replacement text
            replace_all: Replace all occurrences

        Returns:
            Edit result dictionary
        """
        edit_operation = {
            'old_string': old_string,
            'new_string': new_string,
            'replace_all': replace_all
        }

        return await self.multi_edit(file_path, [edit_operation])


# Export main tool
multi_edit_tool = MultiEditTool()

async def multi_edit(
    file_path: str,
    edits: List[Dict[str, Any]],
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for multi-edit operations.
    Compatible with Claude Code's MultiEdit tool interface.
    """
    return await multi_edit_tool.multi_edit(file_path, edits, **kwargs)

async def single_edit(
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False
) -> Dict[str, Any]:
    """
    Convenience function for single edit operations.
    Compatible with Claude Code's Edit tool interface.
    """
    return await multi_edit_tool.single_edit(file_path, old_string, new_string, replace_all)