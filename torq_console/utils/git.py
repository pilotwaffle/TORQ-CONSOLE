"""
Git utilities for TORQ CONSOLE.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

import git
from git import Repo, InvalidGitRepositoryError


logger = logging.getLogger(__name__)


class GitManager:
    """Git repository manager."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.repo: Optional[Repo] = None
        self._is_repo = False
        
    async def initialize(self) -> None:
        """Initialize Git repository access."""
        try:
            self.repo = Repo(self.project_root)
            self._is_repo = True
            logger.info(f"Git repository found at {self.project_root}")
        except InvalidGitRepositoryError:
            logger.warning(f"No Git repository found at {self.project_root}")
            self._is_repo = False
    
    def is_repo(self) -> bool:
        """Check if current directory is a Git repository."""
        return self._is_repo
    
    def current_branch(self) -> Optional[str]:
        """Get current branch name."""
        if not self.repo:
            return None
        
        try:
            return self.repo.active_branch.name
        except Exception:
            return "detached HEAD"
    
    def get_tracked_files(self) -> List[Path]:
        """Get list of tracked files."""
        if not self.repo:
            return []
        
        try:
            tracked_files = []
            for item in self.repo.index.entries:
                file_path = Path(self.project_root) / item[0]
                if file_path.exists():
                    tracked_files.append(file_path)
            return tracked_files
        except Exception as e:
            logger.error(f"Error getting tracked files: {e}")
            return []
    
    def get_modified_files(self) -> List[Path]:
        """Get list of modified files."""
        if not self.repo:
            return []
        
        try:
            modified = []
            for item in self.repo.index.diff(None):
                file_path = Path(self.project_root) / item.a_path
                modified.append(file_path)
            return modified
        except Exception as e:
            logger.error(f"Error getting modified files: {e}")
            return []
    
    def get_untracked_files(self) -> List[Path]:
        """Get list of untracked files."""
        if not self.repo:
            return []
        
        try:
            untracked = []
            for file_path in self.repo.untracked_files:
                full_path = Path(self.project_root) / file_path
                untracked.append(full_path)
            return untracked
        except Exception as e:
            logger.error(f"Error getting untracked files: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get repository status."""
        if not self.repo:
            return {"error": "Not a Git repository"}
        
        try:
            return {
                "branch": self.current_branch(),
                "modified": len(self.get_modified_files()),
                "untracked": len(self.get_untracked_files()),
                "clean": not self.repo.is_dirty(),
                "ahead": self._get_ahead_behind()[0],
                "behind": self._get_ahead_behind()[1],
            }
        except Exception as e:
            logger.error(f"Error getting Git status: {e}")
            return {"error": str(e)}
    
    def _get_ahead_behind(self) -> tuple[int, int]:
        """Get ahead/behind counts for current branch."""
        if not self.repo or not self.repo.active_branch.tracking_branch():
            return (0, 0)
        
        try:
            ahead = len(list(self.repo.iter_commits('HEAD..@{u}')))
            behind = len(list(self.repo.iter_commits('@{u}..HEAD')))
            return (ahead, behind)
        except Exception:
            return (0, 0)
    
    def add_files(self, files: List[Path]) -> bool:
        """Add files to Git index."""
        if not self.repo:
            return False
        
        try:
            file_paths = [str(f.relative_to(self.project_root)) for f in files]
            self.repo.index.add(file_paths)
            return True
        except Exception as e:
            logger.error(f"Error adding files to Git: {e}")
            return False
    
    def commit(self, message: str, author: Optional[str] = None) -> bool:
        """Create a Git commit."""
        if not self.repo:
            return False
        
        try:
            commit_kwargs = {"message": message}
            if author:
                commit_kwargs["author"] = author
            
            self.repo.index.commit(**commit_kwargs)
            return True
        except Exception as e:
            logger.error(f"Error creating Git commit: {e}")
            return False
    
    def create_branch(self, branch_name: str) -> bool:
        """Create a new Git branch."""
        if not self.repo:
            return False
        
        try:
            self.repo.create_head(branch_name)
            return True
        except Exception as e:
            logger.error(f"Error creating branch {branch_name}: {e}")
            return False
    
    def switch_branch(self, branch_name: str) -> bool:
        """Switch to a different branch."""
        if not self.repo:
            return False
        
        try:
            self.repo.heads[branch_name].checkout()
            return True
        except Exception as e:
            logger.error(f"Error switching to branch {branch_name}: {e}")
            return False
    
    def get_diff(self, file_path: Optional[Path] = None) -> str:
        """Get diff for file or entire repository."""
        if not self.repo:
            return ""
        
        try:
            if file_path:
                rel_path = str(file_path.relative_to(self.project_root))
                return self.repo.git.diff(rel_path)
            else:
                return self.repo.git.diff()
        except Exception as e:
            logger.error(f"Error getting diff: {e}")
            return ""