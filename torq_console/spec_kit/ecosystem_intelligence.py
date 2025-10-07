#!/usr/bin/env python3
"""
Phase 3: Ecosystem Intelligence
GitHub/GitLab integration, team collaboration, and advanced analytics
"""

import asyncio
import json
import time
import hashlib
import base64
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import aiohttp
import websockets
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GitRepository:
    """Git repository configuration"""
    provider: str  # 'github', 'gitlab', 'bitbucket'
    owner: str
    repo: str
    branch: str
    token: Optional[str] = None
    url: str = ""
    webhook_url: Optional[str] = None


@dataclass
class TeamMember:
    """Team member information"""
    id: str
    name: str
    email: str
    role: str  # 'owner', 'admin', 'member', 'viewer'
    avatar_url: Optional[str] = None
    permissions: List[str] = None
    last_active: Optional[datetime] = None


@dataclass
class CollaborationSession:
    """Real-time collaboration session"""
    session_id: str
    specification_id: str
    participants: List[TeamMember]
    created_at: datetime
    last_activity: datetime
    changes: List[Dict[str, Any]]
    lock_holders: Dict[str, str]  # section -> user_id
    concurrent_editors: int


@dataclass
class SpecificationVersion:
    """Specification version information"""
    version: str
    specification_id: str
    author: str
    timestamp: datetime
    changes: List[str]
    diff: Dict[str, Any]
    parent_version: Optional[str] = None
    tags: List[str] = None
    approved_by: Optional[str] = None


@dataclass
class ProjectWorkspace:
    """Multi-project workspace"""
    workspace_id: str
    name: str
    description: str
    owner: str
    members: List[TeamMember]
    projects: List[str]  # project IDs
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class GitHubIntegration:
    """GitHub integration for specification sync"""

    def __init__(self, token: str = None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.session = None

    async def initialize(self):
        """Initialize GitHub integration"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"token {self.token}" if self.token else None,
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "TORQ-Console-Spec-Kit/1.0"
            }
        )

    async def close(self):
        """Close GitHub integration"""
        if self.session:
            await self.session.close()

    async def sync_specification_to_repo(self, repo: GitRepository, spec_id: str,
                                       spec_content: Dict[str, Any]) -> Dict[str, Any]:
        """Sync specification to GitHub repository"""
        try:
            # Create specification file content
            file_content = {
                "specification_id": spec_id,
                "title": spec_content.get("title", ""),
                "description": spec_content.get("description", ""),
                "requirements": spec_content.get("requirements", []),
                "acceptance_criteria": spec_content.get("acceptance_criteria", []),
                "tech_stack": spec_content.get("tech_stack", []),
                "dependencies": spec_content.get("dependencies", []),
                "analysis": spec_content.get("analysis", {}),
                "updated_at": datetime.now().isoformat(),
                "synced_by": "TORQ-Console"
            }

            # Create file path in repository
            file_path = f"specs/{spec_id}.json"

            # Encode content
            content_encoded = base64.b64encode(
                json.dumps(file_content, indent=2).encode()
            ).decode()

            # Check if file exists
            url = f"{self.base_url}/repos/{repo.owner}/{repo.repo}/contents/{file_path}"

            async with self.session.get(url) as response:
                file_exists = response.status == 200
                existing_file = await response.json() if file_exists else None

            # Prepare commit data
            commit_data = {
                "message": f"Update specification: {spec_content.get('title', spec_id)}",
                "content": content_encoded,
                "branch": repo.branch
            }

            if file_exists and existing_file:
                commit_data["sha"] = existing_file["sha"]

            # Create or update file
            async with self.session.put(url, json=commit_data) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    logger.info(f"Successfully synced specification {spec_id} to GitHub")
                    return {
                        "success": True,
                        "commit_sha": result["commit"]["sha"],
                        "file_url": result["content"]["html_url"]
                    }
                else:
                    error_msg = await response.text()
                    logger.error(f"Failed to sync to GitHub: {error_msg}")
                    return {"success": False, "error": error_msg}

        except Exception as e:
            logger.error(f"GitHub sync error: {e}")
            return {"success": False, "error": str(e)}

    async def fetch_specification_from_repo(self, repo: GitRepository, spec_id: str) -> Optional[Dict[str, Any]]:
        """Fetch specification from GitHub repository"""
        try:
            file_path = f"specs/{spec_id}.json"
            url = f"{self.base_url}/repos/{repo.owner}/{repo.repo}/contents/{file_path}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    file_data = await response.json()
                    content = base64.b64decode(file_data["content"]).decode()
                    return json.loads(content)
                else:
                    logger.warning(f"Specification {spec_id} not found in repository")
                    return None

        except Exception as e:
            logger.error(f"Error fetching from GitHub: {e}")
            return None

    async def create_webhook(self, repo: GitRepository, webhook_url: str) -> Dict[str, Any]:
        """Create webhook for repository events"""
        try:
            url = f"{self.base_url}/repos/{repo.owner}/{repo.repo}/hooks"
            webhook_data = {
                "name": "web",
                "active": True,
                "events": ["push", "pull_request"],
                "config": {
                    "url": webhook_url,
                    "content_type": "json",
                    "secret": hashlib.sha256(f"{repo.owner}{repo.repo}".encode()).hexdigest()[:20]
                }
            }

            async with self.session.post(url, json=webhook_data) as response:
                if response.status == 201:
                    result = await response.json()
                    return {
                        "success": True,
                        "webhook_id": result["id"],
                        "secret": webhook_data["config"]["secret"]
                    }
                else:
                    error = await response.text()
                    return {"success": False, "error": error}

        except Exception as e:
            logger.error(f"Webhook creation error: {e}")
            return {"success": False, "error": str(e)}

    async def list_repository_specs(self, repo: GitRepository) -> List[str]:
        """List all specifications in repository"""
        try:
            url = f"{self.base_url}/repos/{repo.owner}/{repo.repo}/contents/specs"

            async with self.session.get(url) as response:
                if response.status == 200:
                    files = await response.json()
                    spec_ids = []
                    for file in files:
                        if file["name"].endswith(".json"):
                            spec_ids.append(file["name"][:-5])  # Remove .json extension
                    return spec_ids
                else:
                    return []

        except Exception as e:
            logger.error(f"Error listing repository specs: {e}")
            return []


class GitLabIntegration:
    """GitLab integration for specification sync"""

    def __init__(self, token: str = None, base_url: str = "https://gitlab.com"):
        self.token = token
        self.base_url = f"{base_url}/api/v4"
        self.session = None

    async def initialize(self):
        """Initialize GitLab integration"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.token}" if self.token else None,
                "Content-Type": "application/json",
                "User-Agent": "TORQ-Console-Spec-Kit/1.0"
            }
        )

    async def close(self):
        """Close GitLab integration"""
        if self.session:
            await self.session.close()

    async def sync_specification_to_repo(self, repo: GitRepository, spec_id: str,
                                       spec_content: Dict[str, Any]) -> Dict[str, Any]:
        """Sync specification to GitLab repository"""
        try:
            # Get project ID
            project_path = f"{repo.owner}/{repo.repo}"
            project_url = f"{self.base_url}/projects/{project_path.replace('/', '%2F')}"

            async with self.session.get(project_url) as response:
                if response.status != 200:
                    return {"success": False, "error": "Project not found"}

                project = await response.json()
                project_id = project["id"]

            # Create specification content
            file_content = {
                "specification_id": spec_id,
                "title": spec_content.get("title", ""),
                "description": spec_content.get("description", ""),
                "requirements": spec_content.get("requirements", []),
                "acceptance_criteria": spec_content.get("acceptance_criteria", []),
                "tech_stack": spec_content.get("tech_stack", []),
                "dependencies": spec_content.get("dependencies", []),
                "analysis": spec_content.get("analysis", {}),
                "updated_at": datetime.now().isoformat(),
                "synced_by": "TORQ-Console"
            }

            # File path and content
            file_path = f"specs/{spec_id}.json"
            content = json.dumps(file_content, indent=2)

            # Create or update file
            file_url = f"{self.base_url}/projects/{project_id}/repository/files/{file_path.replace('/', '%2F')}"

            # Check if file exists
            async with self.session.get(f"{file_url}?ref={repo.branch}") as response:
                file_exists = response.status == 200

            # Prepare commit data
            commit_data = {
                "branch": repo.branch,
                "content": content,
                "commit_message": f"Update specification: {spec_content.get('title', spec_id)}",
                "encoding": "text"
            }

            method = "put" if file_exists else "post"
            async with getattr(self.session, method)(file_url, json=commit_data) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    logger.info(f"Successfully synced specification {spec_id} to GitLab")
                    return {
                        "success": True,
                        "file_path": result["file_path"],
                        "branch": result["branch"]
                    }
                else:
                    error = await response.text()
                    return {"success": False, "error": error}

        except Exception as e:
            logger.error(f"GitLab sync error: {e}")
            return {"success": False, "error": str(e)}


class TeamCollaboration:
    """Team collaboration features"""

    def __init__(self):
        self.active_sessions = {}
        self.team_members = {}
        self.websocket_connections = {}
        self.message_queue = defaultdict(list)

    async def create_team(self, team_name: str, owner: TeamMember) -> str:
        """Create a new team"""
        team_id = f"team_{int(time.time())}"

        self.team_members[team_id] = {
            "name": team_name,
            "owner": owner.id,
            "members": {owner.id: owner},
            "created_at": datetime.now(),
            "settings": {
                "default_permissions": ["read", "write"],
                "require_approval": False,
                "auto_sync": True
            }
        }

        logger.info(f"Created team {team_name} with ID {team_id}")
        return team_id

    async def add_team_member(self, team_id: str, member: TeamMember,
                            permissions: List[str] = None) -> bool:
        """Add member to team"""
        if team_id not in self.team_members:
            return False

        member.permissions = permissions or ["read", "write"]
        self.team_members[team_id]["members"][member.id] = member

        # Notify existing team members
        await self._broadcast_team_event(team_id, {
            "type": "member_added",
            "member": asdict(member),
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"Added member {member.name} to team {team_id}")
        return True

    async def start_collaboration_session(self, spec_id: str, initiator: TeamMember) -> str:
        """Start collaborative editing session"""
        session_id = f"collab_{spec_id}_{int(time.time())}"

        session = CollaborationSession(
            session_id=session_id,
            specification_id=spec_id,
            participants=[initiator],
            created_at=datetime.now(),
            last_activity=datetime.now(),
            changes=[],
            lock_holders={},
            concurrent_editors=1
        )

        self.active_sessions[session_id] = session

        logger.info(f"Started collaboration session {session_id} for spec {spec_id}")
        return session_id

    async def join_collaboration_session(self, session_id: str, member: TeamMember) -> bool:
        """Join existing collaboration session"""
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]

        # Check if member is already in session
        if any(p.id == member.id for p in session.participants):
            return True

        session.participants.append(member)
        session.concurrent_editors += 1
        session.last_activity = datetime.now()

        # Notify other participants
        await self._broadcast_session_event(session_id, {
            "type": "member_joined",
            "member": asdict(member),
            "concurrent_editors": session.concurrent_editors,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"Member {member.name} joined collaboration session {session_id}")
        return True

    async def handle_collaborative_edit(self, session_id: str, user_id: str,
                                      edit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle collaborative edit with conflict resolution"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}

        session = self.active_sessions[session_id]

        # Check if section is locked by another user
        section = edit_data.get("section", "")
        if section in session.lock_holders and session.lock_holders[section] != user_id:
            return {
                "success": False,
                "error": "Section locked by another user",
                "locked_by": session.lock_holders[section]
            }

        # Apply edit
        change_record = {
            "id": f"change_{len(session.changes)}",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "section": section,
            "operation": edit_data.get("operation", "update"),
            "old_value": edit_data.get("old_value"),
            "new_value": edit_data.get("new_value"),
            "cursor_position": edit_data.get("cursor_position", 0)
        }

        session.changes.append(change_record)
        session.last_activity = datetime.now()

        # Broadcast change to other participants
        await self._broadcast_session_event(session_id, {
            "type": "edit_applied",
            "change": change_record,
            "editor": user_id
        })

        return {
            "success": True,
            "change_id": change_record["id"],
            "conflicts": []  # TODO: Implement conflict detection
        }

    async def lock_specification_section(self, session_id: str, user_id: str, section: str) -> bool:
        """Lock a section for exclusive editing"""
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]

        # Check if section is already locked
        if section in session.lock_holders:
            return session.lock_holders[section] == user_id

        # Lock section
        session.lock_holders[section] = user_id

        # Broadcast lock notification
        await self._broadcast_session_event(session_id, {
            "type": "section_locked",
            "section": section,
            "locked_by": user_id,
            "timestamp": datetime.now().isoformat()
        })

        return True

    async def unlock_specification_section(self, session_id: str, user_id: str, section: str) -> bool:
        """Unlock a section"""
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]

        # Check if user owns the lock
        if section not in session.lock_holders or session.lock_holders[section] != user_id:
            return False

        # Unlock section
        del session.lock_holders[section]

        # Broadcast unlock notification
        await self._broadcast_session_event(session_id, {
            "type": "section_unlocked",
            "section": section,
            "unlocked_by": user_id,
            "timestamp": datetime.now().isoformat()
        })

        return True

    async def _broadcast_session_event(self, session_id: str, event: Dict[str, Any]):
        """Broadcast event to all session participants"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            for participant in session.participants:
                if participant.id in self.websocket_connections:
                    try:
                        await self.websocket_connections[participant.id].send(
                            json.dumps(event)
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send event to {participant.id}: {e}")

    async def _broadcast_team_event(self, team_id: str, event: Dict[str, Any]):
        """Broadcast event to all team members"""
        if team_id in self.team_members:
            team = self.team_members[team_id]
            for member_id in team["members"]:
                if member_id in self.websocket_connections:
                    try:
                        await self.websocket_connections[member_id].send(
                            json.dumps(event)
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send team event to {member_id}: {e}")


class VersionControl:
    """Specification versioning and history tracking"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.versions = {}
        self.version_index = defaultdict(list)

    async def create_version(self, spec_id: str, content: Dict[str, Any],
                           author: str, changes: List[str] = None) -> str:
        """Create new version of specification"""
        # Get current version number
        current_versions = self.version_index.get(spec_id, [])
        version_number = f"v{len(current_versions) + 1}.0"

        # Calculate diff from previous version
        diff = {}
        parent_version = None
        if current_versions:
            parent_version = current_versions[-1]
            parent_content = self.versions[parent_version].get("content", {})
            diff = self._calculate_diff(parent_content, content)

        # Create version record
        version = SpecificationVersion(
            version=version_number,
            specification_id=spec_id,
            author=author,
            timestamp=datetime.now(),
            changes=changes or [],
            diff=diff,
            parent_version=parent_version
        )

        version_key = f"{spec_id}_{version_number}"
        self.versions[version_key] = {
            "metadata": asdict(version),
            "content": content.copy()
        }

        self.version_index[spec_id].append(version_key)

        # Save to disk
        await self._save_version(version_key)

        logger.info(f"Created version {version_number} for specification {spec_id}")
        return version_number

    async def get_version(self, spec_id: str, version: str) -> Optional[Dict[str, Any]]:
        """Get specific version of specification"""
        version_key = f"{spec_id}_{version}"
        return self.versions.get(version_key)

    async def get_version_history(self, spec_id: str) -> List[SpecificationVersion]:
        """Get version history for specification"""
        versions = []
        for version_key in self.version_index.get(spec_id, []):
            version_data = self.versions.get(version_key, {})
            if "metadata" in version_data:
                versions.append(SpecificationVersion(**version_data["metadata"]))
        return versions

    async def compare_versions(self, spec_id: str, version1: str, version2: str) -> Dict[str, Any]:
        """Compare two versions of specification"""
        v1_data = await self.get_version(spec_id, version1)
        v2_data = await self.get_version(spec_id, version2)

        if not v1_data or not v2_data:
            return {"error": "Version not found"}

        v1_content = v1_data.get("content", {})
        v2_content = v2_data.get("content", {})

        return {
            "spec_id": spec_id,
            "version1": version1,
            "version2": version2,
            "diff": self._calculate_diff(v1_content, v2_content),
            "timestamp": datetime.now().isoformat()
        }

    def _calculate_diff(self, old_content: Dict[str, Any], new_content: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate difference between two content versions"""
        diff = {
            "added": {},
            "removed": {},
            "modified": {},
            "unchanged": {}
        }

        all_keys = set(old_content.keys()) | set(new_content.keys())

        for key in all_keys:
            old_value = old_content.get(key)
            new_value = new_content.get(key)

            if old_value is None:
                diff["added"][key] = new_value
            elif new_value is None:
                diff["removed"][key] = old_value
            elif old_value != new_value:
                diff["modified"][key] = {
                    "old": old_value,
                    "new": new_value
                }
            else:
                diff["unchanged"][key] = old_value

        return diff

    async def _save_version(self, version_key: str):
        """Save version to disk"""
        try:
            version_file = self.storage_path / f"{version_key}.json"
            version_data = self.versions[version_key]

            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            logger.error(f"Failed to save version {version_key}: {e}")


class EcosystemIntelligence:
    """
    Phase 3: Ecosystem Intelligence
    Orchestrates GitHub/GitLab integration, team collaboration, and version control
    """

    def __init__(self, storage_path: Path, github_token: str = None, gitlab_token: str = None):
        self.storage_path = storage_path
        self.github = GitHubIntegration(github_token) if github_token else None
        self.gitlab = GitLabIntegration(gitlab_token) if gitlab_token else None
        self.collaboration = TeamCollaboration()
        self.version_control = VersionControl(storage_path / "versions")
        self.workspaces = {}
        self.connected_repos = {}

    async def initialize(self):
        """Initialize ecosystem intelligence"""
        if self.github:
            await self.github.initialize()
        if self.gitlab:
            await self.gitlab.initialize()

        # Ensure version storage exists
        (self.storage_path / "versions").mkdir(parents=True, exist_ok=True)

        logger.info("Ecosystem Intelligence initialized")

    async def close(self):
        """Close ecosystem intelligence"""
        if self.github:
            await self.github.close()
        if self.gitlab:
            await self.gitlab.close()

    async def connect_repository(self, repo_config: Dict[str, Any]) -> Dict[str, Any]:
        """Connect to Git repository"""
        try:
            repo = GitRepository(**repo_config)

            # Test connection
            if repo.provider == "github" and self.github:
                specs = await self.github.list_repository_specs(repo)
                self.connected_repos[f"{repo.owner}/{repo.repo}"] = repo
                return {
                    "success": True,
                    "provider": "github",
                    "specs_found": len(specs),
                    "specs": specs
                }
            elif repo.provider == "gitlab" and self.gitlab:
                # TODO: Implement GitLab spec listing
                self.connected_repos[f"{repo.owner}/{repo.repo}"] = repo
                return {
                    "success": True,
                    "provider": "gitlab",
                    "specs_found": 0,
                    "specs": []
                }
            else:
                return {
                    "success": False,
                    "error": f"Provider {repo.provider} not supported or not configured"
                }

        except Exception as e:
            logger.error(f"Repository connection error: {e}")
            return {"success": False, "error": str(e)}

    async def sync_specification_to_git(self, spec_id: str, spec_content: Dict[str, Any],
                                      repo_name: str) -> Dict[str, Any]:
        """Sync specification to connected Git repository"""
        if repo_name not in self.connected_repos:
            return {"success": False, "error": "Repository not connected"}

        repo = self.connected_repos[repo_name]

        try:
            if repo.provider == "github" and self.github:
                result = await self.github.sync_specification_to_repo(repo, spec_id, spec_content)
            elif repo.provider == "gitlab" and self.gitlab:
                result = await self.gitlab.sync_specification_to_repo(repo, spec_id, spec_content)
            else:
                return {"success": False, "error": "Provider not available"}

            # Create version if sync successful
            if result.get("success"):
                version = await self.version_control.create_version(
                    spec_id, spec_content, "system",
                    [f"Synced to {repo.provider}"]
                )
                result["version_created"] = version

            return result

        except Exception as e:
            logger.error(f"Git sync error: {e}")
            return {"success": False, "error": str(e)}

    def create_workspace(self, workspace_data: Dict[str, Any]) -> str:
        """Create multi-project workspace"""
        workspace_id = f"ws_{int(time.time())}"

        workspace = ProjectWorkspace(
            workspace_id=workspace_id,
            name=workspace_data["name"],
            description=workspace_data.get("description", ""),
            owner=workspace_data["owner"],
            members=[],
            projects=[],
            settings=workspace_data.get("settings", {}),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.workspaces[workspace_id] = workspace

        logger.info(f"Created workspace {workspace_data['name']} with ID {workspace_id}")
        return workspace_id

    async def get_ecosystem_analytics(self) -> Dict[str, Any]:
        """Get comprehensive ecosystem analytics"""
        return {
            "repositories": {
                "connected": len(self.connected_repos),
                "providers": list(set(repo.provider for repo in self.connected_repos.values())),
                "total_syncs": 0  # TODO: Track sync statistics
            },
            "collaboration": {
                "active_sessions": len(self.collaboration.active_sessions),
                "total_teams": len(self.collaboration.team_members),
                "concurrent_editors": sum(
                    session.concurrent_editors
                    for session in self.collaboration.active_sessions.values()
                )
            },
            "versioning": {
                "total_versions": len(self.version_control.versions),
                "specifications_tracked": len(self.version_control.version_index),
                "average_versions_per_spec": (
                    len(self.version_control.versions) / len(self.version_control.version_index)
                    if self.version_control.version_index else 0
                )
            },
            "workspaces": {
                "total": len(self.workspaces),
                "total_projects": sum(len(ws.projects) for ws in self.workspaces.values()),
                "total_members": sum(len(ws.members) for ws in self.workspaces.values())
            },
            "timestamp": datetime.now().isoformat()
        }