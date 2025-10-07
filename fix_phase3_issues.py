#!/usr/bin/env python3
"""
Fix Phase 3 ecosystem intelligence issues for proper testing
"""

import re
from pathlib import Path

def fix_ecosystem_intelligence():
    """Fix issues in ecosystem_intelligence.py"""

    file_path = Path("torq_console/spec_kit/ecosystem_intelligence.py")
    content = file_path.read_text(encoding='utf-8')

    # Add missing Workspace class after the imports
    workspace_class = '''
@dataclass
class Workspace:
    """Multi-project workspace for team collaboration"""
    id: str
    name: str
    description: str
    projects: List[str]
    team_members: List[TeamMember]
    created_at: str
    updated_at: str = ""
'''

    # Add missing get_repository_info method to GitHubIntegration
    github_method = '''
    async def get_repository_info(self, repo_name: str) -> Dict[str, Any]:
        """Get repository information from GitHub"""
        url = f"https://api.github.com/repos/{repo_name}"
        headers = {"Authorization": f"token {self.token}"}

        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"GitHub API error: {response.status}")
'''

    # Find where to insert the Workspace class
    # Insert after TeamMember class
    pattern = r'(class TeamMember.*?\n    updated_at: str = "")\n'
    replacement = r'\1\n' + workspace_class
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Find where to insert the GitHub method
    # Insert in GitHubIntegration class
    pattern = r'(class GitHubIntegration:.*?def __init__.*?\n        self\.session = aiohttp\.ClientSession\(\))\n'
    replacement = r'\1\n' + github_method
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Fix the EcosystemIntelligence constructor to use proper attribute names
    content = content.replace(
        'self.github_integration = self.github or GitHubIntegration()',
        'self.github_integration = self.github or GitHubIntegration()'
    )
    content = content.replace(
        'self.gitlab_integration = self.gitlab or GitLabIntegration()',
        'self.gitlab_integration = self.gitlab or GitLabIntegration()'
    )
    content = content.replace(
        'self.team_collaboration = self.collaboration',
        'self.team_collaboration = self.collaboration'
    )

    # Add missing workspace methods to EcosystemIntelligence
    workspace_methods = '''
    def create_workspace(self, name: str, description: str) -> Workspace:
        """Create a new workspace"""
        workspace_id = f"ws_{len(self.workspaces) + 1:04d}"
        workspace = Workspace(
            id=workspace_id,
            name=name,
            description=description,
            projects=[],
            team_members=[],
            created_at=datetime.now().isoformat()
        )
        self.workspaces[workspace_id] = workspace
        return workspace

    def get_workspaces(self) -> List[Workspace]:
        """Get all workspaces"""
        return list(self.workspaces.values())
'''

    # Insert workspace methods before the last method in EcosystemIntelligence
    pattern = r'(class EcosystemIntelligence:.*?)(    def get_collaboration_status.*)'
    replacement = r'\1' + workspace_methods + r'\n\2'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    file_path.write_text(content, encoding='utf-8')
    print("✅ Fixed ecosystem_intelligence.py")

def fix_test_file():
    """Fix the test file to match the updated implementation"""

    file_path = Path("test_phase3_ecosystem_intelligence.py")
    content = file_path.read_text(encoding='utf-8')

    # Fix the test initialization to use default storage path
    content = content.replace(
        'ecosystem = EcosystemIntelligence()',
        'ecosystem = EcosystemIntelligence(storage_path=Path("test_storage"))'
    )

    # Fix GitHubIntegration initialization test
    content = content.replace(
        'github = GitHubIntegration("mock_token")',
        'github = GitHubIntegration("mock_token")\n            github.session = Mock()  # Mock the session'
    )

    file_path.write_text(content, encoding='utf-8')
    print("✅ Fixed test_phase3_ecosystem_intelligence.py")

if __name__ == "__main__":
    print("🔧 Fixing Phase 3 ecosystem intelligence issues...")

    try:
        fix_ecosystem_intelligence()
        fix_test_file()
        print("🎉 All Phase 3 issues fixed!")
    except Exception as e:
        print(f"❌ Error fixing issues: {e}")