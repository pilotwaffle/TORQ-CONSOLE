"""
GitHub Push Integration for TORQ Console
Handles pushing projects to GitHub repositories
"""

import os
import logging
from typing import Optional
from pathlib import Path

try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    logging.warning("PyGithub not installed. Install with: pip install PyGithub")

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    logging.warning("GitPython not installed. Install with: pip install GitPython")


class GitHubPusher:
    """Handle GitHub repository operations."""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub Pusher.

        Args:
            token: GitHub personal access token
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.logger = logging.getLogger(__name__)

        if not GITHUB_AVAILABLE:
            raise ImportError("PyGithub is required. Install with: pip install PyGithub")

        if not GIT_AVAILABLE:
            raise ImportError("GitPython is required. Install with: pip install GitPython")

        if self.token:
            self.gh = Github(self.token)
            self.logger.info("GitHub Pusher initialized")
        else:
            self.gh = None
            self.logger.warning("GitHub Pusher initialized without token")

    def is_configured(self) -> bool:
        """Check if GitHub token is configured."""
        return bool(self.token and self.gh)

    async def push_project(
        self,
        path: str,
        repo_name: str,
        private: bool = False,
        commit_msg: str = "Initial commit via TORQ Console",
        branch: str = "main",
        create_if_missing: bool = True
    ) -> dict:
        """
        Push local project to GitHub.

        Args:
            path: Path to local project
            repo_name: Name for GitHub repository
            private: Whether repository should be private
            commit_msg: Commit message
            branch: Branch name (default: main)
            create_if_missing: Create repo if it doesn't exist

        Returns:
            dict with 'success', 'url', and optional 'error' keys
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'GitHub token not configured. Set GITHUB_TOKEN environment variable.'
            }

        try:
            path_obj = Path(path).resolve()
            if not path_obj.exists():
                return {
                    'success': False,
                    'error': f'Project path does not exist: {path}'
                }

            # Get or create GitHub repository
            user = self.gh.get_user()
            try:
                gh_repo = user.get_repo(repo_name)
                self.logger.info(f"Found existing repository: {repo_name}")
            except GithubException as e:
                if e.status == 404 and create_if_missing:
                    self.logger.info(f"Creating new repository: {repo_name}")
                    gh_repo = user.create_repo(
                        repo_name,
                        private=private,
                        description=f"Project created via TORQ Console"
                    )
                else:
                    return {
                        'success': False,
                        'error': f'Repository not found and create_if_missing=False: {repo_name}'
                    }

            # Initialize or open Git repository
            try:
                repo = git.Repo(path_obj)
                self.logger.info("Opened existing git repository")
            except git.exc.InvalidGitRepositoryError:
                self.logger.info("Initializing new git repository")
                repo = git.Repo.init(path_obj)

            # Add files and commit
            repo.git.add(A=True)  # Add all files
            try:
                repo.index.commit(commit_msg)
                self.logger.info(f"Created commit: {commit_msg}")
            except git.exc.GitCommandError as e:
                # If no changes to commit, that's okay
                if "nothing to commit" not in str(e):
                    raise

            # Add remote if not exists
            remote_name = 'origin'
            try:
                origin = repo.remote(remote_name)
                self.logger.info(f"Remote '{remote_name}' already exists")
            except ValueError:
                self.logger.info(f"Adding remote '{remote_name}'")
                origin = repo.create_remote(remote_name, gh_repo.clone_url)

            # Push to GitHub
            self.logger.info(f"Pushing to GitHub: {branch}")
            try:
                # Set upstream and push
                push_info = origin.push(refspec=f'{branch}:{branch}', set_upstream=True)
                self.logger.info(f"Push completed: {push_info}")
            except git.exc.GitCommandError as e:
                if "rejected" in str(e):
                    # Try force push if rejected (only for initial setup)
                    self.logger.warning("Push rejected, attempting force push")
                    push_info = origin.push(refspec=f'{branch}:{branch}', force=True, set_upstream=True)
                else:
                    raise

            return {
                'success': True,
                'url': gh_repo.html_url,
                'message': f'Successfully pushed to {gh_repo.html_url}'
            }

        except Exception as e:
            self.logger.error(f"Error pushing to GitHub: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def create_repository(
        self,
        repo_name: str,
        private: bool = False,
        description: str = ""
    ) -> dict:
        """
        Create a new GitHub repository.

        Args:
            repo_name: Repository name
            private: Whether repository should be private
            description: Repository description

        Returns:
            dict with 'success', 'url', and optional 'error' keys
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'GitHub token not configured'
            }

        try:
            user = self.gh.get_user()
            repo = user.create_repo(
                repo_name,
                private=private,
                description=description or f"Repository created via TORQ Console"
            )

            return {
                'success': True,
                'url': repo.html_url,
                'message': f'Successfully created repository: {repo.html_url}'
            }

        except GithubException as e:
            self.logger.error(f"Error creating repository: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_user_info(self) -> dict:
        """Get authenticated user information."""
        if not self.is_configured():
            return {'error': 'Not configured'}

        try:
            user = self.gh.get_user()
            return {
                'login': user.login,
                'name': user.name,
                'email': user.email,
                'repos': user.public_repos,
            }
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            return {'error': str(e)}
