"""
File Operations Tool for Prince Flowers
Safe CRUD operations with undo/backup functionality
"""
import logging
import os
import shutil
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import hashlib


class FileOperationsTool:
    """
    Safe file operations with comprehensive CRUD and undo capabilities.
    Follows Cline's best practices for file handling.
    """

    def __init__(self, backup_dir: Optional[str] = None, max_backups: int = 10):
        """
        Initialize File Operations Tool.

        Args:
            backup_dir: Directory for backups (default: E:/file_operations_backups)
            max_backups: Maximum number of backups per file
        """
        self.logger = logging.getLogger(__name__)
        self.backup_dir = Path(backup_dir or "E:/file_operations_backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = max_backups

        # Operation history for undo
        self.history_file = self.backup_dir / "operation_history.json"
        self.operation_history = self._load_history()

    def is_available(self) -> bool:
        """Check if file operations are available."""
        try:
            # Check if backup directory is writable
            test_file = self.backup_dir / '.write_test'
            test_file.write_text('test')
            test_file.unlink()
            return True
        except Exception as e:
            self.logger.error(f"File operations not available: {e}")
            return False

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load operation history from disk."""
        try:
            if self.history_file.exists():
                return json.loads(self.history_file.read_text())
            return []
        except Exception as e:
            self.logger.error(f"Failed to load history: {e}")
            return []

    def _save_history(self):
        """Save operation history to disk."""
        try:
            self.history_file.write_text(json.dumps(self.operation_history, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save history: {e}")

    def _add_to_history(self, operation: Dict[str, Any]):
        """Add operation to history."""
        operation['timestamp'] = datetime.now().isoformat()
        self.operation_history.append(operation)

        # Keep only recent operations (last 100)
        if len(self.operation_history) > 100:
            self.operation_history = self.operation_history[-100:]

        self._save_history()

    def _create_backup(self, filepath: str) -> Optional[str]:
        """
        Create backup of file before modification.

        Args:
            filepath: Path to file to backup

        Returns:
            Path to backup file, or None if backup failed
        """
        try:
            source_path = Path(filepath)
            if not source_path.exists():
                return None

            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source_path.name}.{timestamp}.backup"
            backup_path = self.backup_dir / backup_name

            # Copy file to backup
            shutil.copy2(source_path, backup_path)

            # Clean old backups (keep only max_backups)
            self._cleanup_old_backups(source_path.name)

            self.logger.info(f"[BACKUP] Created: {backup_path}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"[BACKUP] Failed to create backup: {e}")
            return None

    def _cleanup_old_backups(self, filename: str):
        """Remove old backups, keeping only max_backups most recent."""
        try:
            # Find all backups for this file
            backups = sorted(
                self.backup_dir.glob(f"{filename}.*.backup"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            # Remove old backups
            for backup in backups[self.max_backups:]:
                backup.unlink()
                self.logger.info(f"[CLEANUP] Removed old backup: {backup}")

        except Exception as e:
            self.logger.error(f"[CLEANUP] Failed to cleanup backups: {e}")

    def _calculate_checksum(self, filepath: str) -> Optional[str]:
        """Calculate SHA256 checksum of file."""
        try:
            sha256 = hashlib.sha256()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate checksum: {e}")
            return None

    async def create(self, filepath: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        Create a new file.

        Args:
            filepath: Path where file should be created
            content: Content to write to file
            overwrite: Whether to overwrite existing file

        Returns:
            Dict with success status and metadata
        """
        try:
            file_path = Path(filepath)

            # Check if file exists
            if file_path.exists() and not overwrite:
                return {
                    'success': False,
                    'error': f"File already exists: {filepath}. Use overwrite=True to replace.",
                    'operation': 'create'
                }

            # Create backup if overwriting
            backup_path = None
            if file_path.exists() and overwrite:
                backup_path = self._create_backup(filepath)

            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            file_path.write_text(content, encoding='utf-8')

            # Calculate metadata
            file_size = file_path.stat().st_size
            checksum = self._calculate_checksum(filepath)

            # Add to history
            self._add_to_history({
                'operation': 'create',
                'filepath': filepath,
                'backup_path': backup_path,
                'checksum': checksum,
                'size': file_size,
                'overwrite': overwrite
            })

            self.logger.info(f"[CREATE] File created: {filepath} ({file_size} bytes)")

            return {
                'success': True,
                'operation': 'create',
                'filepath': filepath,
                'size': file_size,
                'checksum': checksum,
                'backup_path': backup_path
            }

        except Exception as e:
            error_msg = f"Failed to create file: {str(e)}"
            self.logger.error(f"[CREATE] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'operation': 'create'
            }

    async def read(self, filepath: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Read contents of a file.

        Args:
            filepath: Path to file to read
            encoding: File encoding (default: utf-8)

        Returns:
            Dict with success status and file contents
        """
        try:
            file_path = Path(filepath)

            if not file_path.exists():
                return {
                    'success': False,
                    'error': f"File not found: {filepath}",
                    'operation': 'read'
                }

            if not file_path.is_file():
                return {
                    'success': False,
                    'error': f"Not a file: {filepath}",
                    'operation': 'read'
                }

            # Read file
            content = file_path.read_text(encoding=encoding)
            file_size = file_path.stat().st_size
            checksum = self._calculate_checksum(filepath)

            self.logger.info(f"[READ] File read: {filepath} ({file_size} bytes)")

            return {
                'success': True,
                'operation': 'read',
                'filepath': filepath,
                'content': content,
                'size': file_size,
                'checksum': checksum,
                'encoding': encoding
            }

        except Exception as e:
            error_msg = f"Failed to read file: {str(e)}"
            self.logger.error(f"[READ] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'operation': 'read'
            }

    async def update(self, filepath: str, content: str, create_backup: bool = True) -> Dict[str, Any]:
        """
        Update (overwrite) contents of existing file.

        Args:
            filepath: Path to file to update
            content: New content
            create_backup: Whether to create backup before update

        Returns:
            Dict with success status and metadata
        """
        try:
            file_path = Path(filepath)

            if not file_path.exists():
                return {
                    'success': False,
                    'error': f"File not found: {filepath}. Use create() instead.",
                    'operation': 'update'
                }

            # Create backup
            backup_path = None
            old_checksum = self._calculate_checksum(filepath)

            if create_backup:
                backup_path = self._create_backup(filepath)

            # Write new content
            file_path.write_text(content, encoding='utf-8')

            # Calculate new metadata
            file_size = file_path.stat().st_size
            new_checksum = self._calculate_checksum(filepath)

            # Add to history
            self._add_to_history({
                'operation': 'update',
                'filepath': filepath,
                'backup_path': backup_path,
                'old_checksum': old_checksum,
                'new_checksum': new_checksum,
                'size': file_size
            })

            self.logger.info(f"[UPDATE] File updated: {filepath} ({file_size} bytes)")

            return {
                'success': True,
                'operation': 'update',
                'filepath': filepath,
                'size': file_size,
                'old_checksum': old_checksum,
                'new_checksum': new_checksum,
                'backup_path': backup_path
            }

        except Exception as e:
            error_msg = f"Failed to update file: {str(e)}"
            self.logger.error(f"[UPDATE] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'operation': 'update'
            }

    async def delete(self, filepath: str, create_backup: bool = True) -> Dict[str, Any]:
        """
        Delete a file.

        Args:
            filepath: Path to file to delete
            create_backup: Whether to create backup before deletion

        Returns:
            Dict with success status and metadata
        """
        try:
            file_path = Path(filepath)

            if not file_path.exists():
                return {
                    'success': False,
                    'error': f"File not found: {filepath}",
                    'operation': 'delete'
                }

            # Create backup
            backup_path = None
            checksum = self._calculate_checksum(filepath)
            file_size = file_path.stat().st_size

            if create_backup:
                backup_path = self._create_backup(filepath)

            # Delete file
            file_path.unlink()

            # Add to history
            self._add_to_history({
                'operation': 'delete',
                'filepath': filepath,
                'backup_path': backup_path,
                'checksum': checksum,
                'size': file_size
            })

            self.logger.info(f"[DELETE] File deleted: {filepath}")

            return {
                'success': True,
                'operation': 'delete',
                'filepath': filepath,
                'backup_path': backup_path,
                'checksum': checksum,
                'size': file_size
            }

        except Exception as e:
            error_msg = f"Failed to delete file: {str(e)}"
            self.logger.error(f"[DELETE] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'operation': 'delete'
            }

    async def move(self, source: str, destination: str, create_backup: bool = True) -> Dict[str, Any]:
        """
        Move/rename a file.

        Args:
            source: Current file path
            destination: New file path
            create_backup: Whether to create backup

        Returns:
            Dict with success status and metadata
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination)

            if not source_path.exists():
                return {
                    'success': False,
                    'error': f"Source file not found: {source}",
                    'operation': 'move'
                }

            if dest_path.exists():
                return {
                    'success': False,
                    'error': f"Destination already exists: {destination}",
                    'operation': 'move'
                }

            # Create backup
            backup_path = None
            checksum = self._calculate_checksum(source)

            if create_backup:
                backup_path = self._create_backup(source)

            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(source, destination)

            # Add to history
            self._add_to_history({
                'operation': 'move',
                'source': source,
                'destination': destination,
                'backup_path': backup_path,
                'checksum': checksum
            })

            self.logger.info(f"[MOVE] File moved: {source} → {destination}")

            return {
                'success': True,
                'operation': 'move',
                'source': source,
                'destination': destination,
                'backup_path': backup_path,
                'checksum': checksum
            }

        except Exception as e:
            error_msg = f"Failed to move file: {str(e)}"
            self.logger.error(f"[MOVE] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'operation': 'move'
            }

    async def copy(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy a file.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            Dict with success status and metadata
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination)

            if not source_path.exists():
                return {
                    'success': False,
                    'error': f"Source file not found: {source}",
                    'operation': 'copy'
                }

            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(source, destination)

            # Calculate metadata
            file_size = dest_path.stat().st_size
            checksum = self._calculate_checksum(destination)

            # Add to history
            self._add_to_history({
                'operation': 'copy',
                'source': source,
                'destination': destination,
                'checksum': checksum,
                'size': file_size
            })

            self.logger.info(f"[COPY] File copied: {source} → {destination}")

            return {
                'success': True,
                'operation': 'copy',
                'source': source,
                'destination': destination,
                'size': file_size,
                'checksum': checksum
            }

        except Exception as e:
            error_msg = f"Failed to copy file: {str(e)}"
            self.logger.error(f"[COPY] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'operation': 'copy'
            }

    async def undo_last(self) -> Dict[str, Any]:
        """
        Undo the last operation using backup.

        Returns:
            Dict with success status and details
        """
        try:
            if not self.operation_history:
                return {
                    'success': False,
                    'error': 'No operations to undo',
                    'operation': 'undo'
                }

            last_op = self.operation_history[-1]
            operation_type = last_op['operation']
            filepath = last_op.get('filepath') or last_op.get('destination')
            backup_path = last_op.get('backup_path')

            if operation_type in ['create', 'update']:
                if backup_path and Path(backup_path).exists():
                    # Restore from backup
                    shutil.copy2(backup_path, filepath)
                    self.logger.info(f"[UNDO] Restored from backup: {filepath}")
                elif operation_type == 'create':
                    # Delete the created file
                    Path(filepath).unlink()
                    self.logger.info(f"[UNDO] Deleted created file: {filepath}")

            elif operation_type == 'delete':
                if backup_path and Path(backup_path).exists():
                    # Restore deleted file
                    shutil.copy2(backup_path, filepath)
                    self.logger.info(f"[UNDO] Restored deleted file: {filepath}")
                else:
                    return {
                        'success': False,
                        'error': 'No backup available to restore',
                        'operation': 'undo'
                    }

            elif operation_type == 'move':
                source = last_op['source']
                # Move back to original location
                shutil.move(filepath, source)
                self.logger.info(f"[UNDO] Moved back: {filepath} → {source}")

            # Remove from history
            self.operation_history.pop()
            self._save_history()

            return {
                'success': True,
                'operation': 'undo',
                'undone_operation': operation_type,
                'filepath': filepath
            }

        except Exception as e:
            error_msg = f"Failed to undo operation: {str(e)}"
            self.logger.error(f"[UNDO] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'operation': 'undo'
            }

    async def list_backups(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        List available backups.

        Args:
            filename: Optional filename to filter backups

        Returns:
            Dict with list of backups
        """
        try:
            if filename:
                backups = list(self.backup_dir.glob(f"{filename}.*.backup"))
            else:
                backups = list(self.backup_dir.glob("*.backup"))

            backup_list = []
            for backup in sorted(backups, key=lambda p: p.stat().st_mtime, reverse=True):
                backup_list.append({
                    'path': str(backup),
                    'size': backup.stat().st_size,
                    'modified': datetime.fromtimestamp(backup.stat().st_mtime).isoformat()
                })

            return {
                'success': True,
                'operation': 'list_backups',
                'count': len(backup_list),
                'backups': backup_list
            }

        except Exception as e:
            error_msg = f"Failed to list backups: {str(e)}"
            self.logger.error(f"[LIST_BACKUPS] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'operation': 'list_backups'
            }


def create_file_operations_tool(backup_dir: Optional[str] = None, max_backups: int = 10) -> FileOperationsTool:
    """
    Factory function to create FileOperationsTool instance.

    Args:
        backup_dir: Optional custom backup directory
        max_backups: Maximum backups per file

    Returns:
        FileOperationsTool instance
    """
    return FileOperationsTool(backup_dir=backup_dir, max_backups=max_backups)
