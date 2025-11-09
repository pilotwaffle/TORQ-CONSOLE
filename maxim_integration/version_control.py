"""
Maxim AI Integration - Phase 2: Version Control System
Advanced version control for Prince Flowers agent improvements

This module implements comprehensive version management:
- Agent versioning with semantic versioning
- Change tracking and documentation
- Rollback capabilities
- Performance comparison across versions
- Deployment management
"""

import asyncio
import json
import time
import logging
import hashlib
import difflib
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime, timedelta
import os
import shutil
import subprocess

class VersionType(Enum):
    """Types of version changes"""
    MAJOR = "major"      # Breaking changes
    MINOR = "minor"      # New features, backward compatible
    PATCH = "patch"      # Bug fixes, backward compatible
    HOTFIX = "hotfix"    # Critical fixes
    EXPERIMENTAL = "experimental"  # Experimental features

class ChangeCategory(Enum):
    """Categories of changes"""
    PROMPT_OPTIMIZATION = "prompt_optimization"
    ROUTING_IMPROVEMENT = "routing_improvement"
    TOOL_INTEGRATION = "tool_integration"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    BUG_FIX = "bug_fix"
    FEATURE_ADDITION = "feature_addition"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"

class DeploymentStatus(Enum):
    """Deployment status tracking"""
    DRAFT = "draft"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    ROLLED_BACK = "rolled_back"
    DEPRECATED = "deprecated"

@dataclass
class AgentVersion:
    """Version information for an agent"""
    version: str  # Semantic version (e.g., "2.1.3")
    version_type: VersionType
    agent_type: str  # torq_prince, marvin_prince, orchestrator
    changes: List['ChangeRecord']
    performance_metrics: Dict[str, float]
    created_at: datetime
    created_by: str
    parent_version: Optional[str] = None
    git_commit: Optional[str] = None
    deployment_status: DeploymentStatus = DeploymentStatus.DRAFT
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChangeRecord:
    """Record of a specific change"""
    category: ChangeCategory
    description: str
    files_modified: List[str]
    test_results: Dict[str, Any]
    performance_impact: Dict[str, float]
    breaking_change: bool = False
    migration_required: bool = False

@dataclass
class VersionComparison:
    """Comparison between two versions"""
    from_version: str
    to_version: str
    performance_delta: Dict[str, float]
    improvement_summary: str
    regression_detected: bool
    breaking_changes: List[str]
    migration_requirements: List[str]
    recommendation: str

@dataclass
class DeploymentRecord:
    """Record of a version deployment"""
    version: str
    environment: str  # testing, staging, production
    deployed_at: datetime
    deployed_by: str
    deployment_config: Dict[str, Any]
    rollback_plan: Dict[str, Any]
    monitoring_setup: Dict[str, Any]
    status: DeploymentStatus

class VersionControlSystem:
    """
    Advanced version control system for Prince Flowers agents
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

        # Version storage
        self.versions: Dict[str, AgentVersion] = {}
        self.agent_versions: Dict[str, List[str]] = {}  # agent_type -> list of versions
        self.deployment_records: Dict[str, List[DeploymentRecord]] = {}
        self.comparisons: Dict[Tuple[str, str], VersionComparison] = {}

        # Configuration
        self.version_control_dir = "E:/TORQ-CONSOLE/version_control"
        self.backup_dir = f"{self.version_control_dir}/backups"
        self.config_dir = f"{self.version_control_dir}/config"

        # Initialize directories
        self._initialize_directories()

        # Load existing versions
        self._load_versions()

        self.logger.info("Version Control System initialized")

    def setup_logging(self):
        """Setup logging for version control system"""
        os.makedirs("E:/TORQ-CONSOLE/logs", exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('E:/TORQ-CONSOLE/logs/version_control.log'),
                logging.StreamHandler()
            ]
        )

    def _initialize_directories(self):
        """Initialize required directories"""
        directories = [
            self.version_control_dir,
            self.backup_dir,
            self.config_dir,
            f"{self.version_control_dir}/agents",
            f"{self.version_control_dir}/deployments",
            f"{self.version_control_dir}/comparisons"
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def _load_versions(self):
        """Load existing versions from storage"""
        versions_file = f"{self.config_dir}/versions.json"
        if os.path.exists(versions_file):
            try:
                with open(versions_file, 'r') as f:
                    versions_data = json.load(f)

                for version_str, version_data in versions_data.items():
                    # Reconstruct AgentVersion objects
                    version = AgentVersion(
                        version=version_data["version"],
                        version_type=VersionType(version_data["version_type"]),
                        agent_type=version_data["agent_type"],
                        changes=[self._deserialize_change(change) for change in version_data["changes"]],
                        performance_metrics=version_data["performance_metrics"],
                        created_at=datetime.fromisoformat(version_data["created_at"]),
                        created_by=version_data["created_by"],
                        parent_version=version_data.get("parent_version"),
                        git_commit=version_data.get("git_commit"),
                        deployment_status=DeploymentStatus(version_data.get("deployment_status", "draft")),
                        metadata=version_data.get("metadata", {})
                    )
                    self.versions[version_str] = version

                    # Update agent versions mapping
                    if version.agent_type not in self.agent_versions:
                        self.agent_versions[version.agent_type] = []
                    self.agent_versions[version.agent_type].append(version_str)

                self.logger.info(f"Loaded {len(self.versions)} versions from storage")
            except Exception as e:
                self.logger.error(f"Error loading versions: {e}")

    def _deserialize_change(self, change_data: Dict) -> ChangeRecord:
        """Deserialize change record from dictionary"""
        return ChangeRecord(
            category=ChangeCategory(change_data["category"]),
            description=change_data["description"],
            files_modified=change_data["files_modified"],
            test_results=change_data["test_results"],
            performance_impact=change_data["performance_impact"],
            breaking_change=change_data.get("breaking_change", False),
            migration_required=change_data.get("migration_required", False)
        )

    def create_version(self, agent_type: str, version_type: VersionType,
                      changes: List[ChangeRecord], performance_metrics: Dict[str, float],
                      created_by: str, parent_version: Optional[str] = None) -> str:
        """
        Create a new agent version

        Args:
            agent_type: Type of agent (torq_prince, marvin_prince, orchestrator)
            version_type: Type of version change
            changes: List of changes in this version
            performance_metrics: Performance metrics for this version
            created_by: Who created this version
            parent_version: Parent version this is based on

        Returns:
            New version string
        """
        # Determine next version number
        if parent_version and parent_version in self.versions:
            new_version = self._increment_version(parent_version, version_type)
        else:
            new_version = self._get_initial_version(agent_type, version_type)

        # Create version record
        version = AgentVersion(
            version=new_version,
            version_type=version_type,
            agent_type=agent_type,
            changes=changes,
            performance_metrics=performance_metrics,
            created_at=datetime.now(),
            created_by=created_by,
            parent_version=parent_version,
            git_commit=self._get_git_commit(),
            metadata={
                "changelog": self._generate_changelog(changes),
                "affected_components": self._identify_affected_components(changes)
            }
        )

        # Store version
        self.versions[new_version] = version

        # Update agent versions mapping
        if agent_type not in self.agent_versions:
            self.agent_versions[agent_type] = []
        self.agent_versions[agent_type].append(new_version)

        # Save to storage
        self._save_versions()

        # Create backup
        self._create_version_backup(version)

        self.logger.info(f"Created version {new_version} for {agent_type}")
        return new_version

    def _increment_version(self, current_version: str, version_type: VersionType) -> str:
        """Increment semantic version based on version type"""
        try:
            parts = current_version.split('.')
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

            if version_type == VersionType.MAJOR:
                major += 1
                minor = 0
                patch = 0
            elif version_type == VersionType.MINOR:
                minor += 1
                patch = 0
            elif version_type in [VersionType.PATCH, VersionType.HOTFIX]:
                patch += 1
            elif version_type == VersionType.EXPERIMENTAL:
                # Add experimental suffix
                return f"{major}.{minor}.{patch}-exp.{int(time.time())}"

            return f"{major}.{minor}.{patch}"
        except (IndexError, ValueError):
            # Fallback for invalid version format
            return "1.0.0"

    def _get_initial_version(self, agent_type: str, version_type: VersionType) -> str:
        """Get initial version for new agent"""
        existing_versions = self.agent_versions.get(agent_type, [])
        if existing_versions:
            # Get latest version and increment
            latest_version = max(existing_versions, key=self._version_sort_key)
            return self._increment_version(latest_version, version_type)
        else:
            # First version for this agent
            return "1.0.0" if version_type != VersionType.EXPERIMENTAL else "1.0.0-exp.0"

    def _version_sort_key(self, version_str: str) -> Tuple[int, int, int]:
        """Get sort key for version strings"""
        try:
            parts = version_str.split('-')[0].split('.')  # Remove suffix
            return tuple(int(part) for part in parts[:3])
        except (IndexError, ValueError):
            return (0, 0, 0)

    def _generate_changelog(self, changes: List[ChangeRecord]) -> str:
        """Generate changelog from changes"""
        changelog_lines = [f"Changes ({len(changes)} total):"]

        # Group by category
        by_category = {}
        for change in changes:
            if change.category not in by_category:
                by_category[change.category] = []
            by_category[change.category].append(change)

        for category, category_changes in by_category.items():
            changelog_lines.append(f"\n{category.value.replace('_', ' ').title()}:")
            for change in category_changes:
                prefix = "🔴" if change.breaking_change else "  "
                changelog_lines.append(f"{prefix} {change.description}")

        return "\n".join(changelog_lines)

    def _identify_affected_components(self, changes: List[ChangeRecord]) -> List[str]:
        """Identify components affected by changes"""
        components = set()
        for change in changes:
            for file_path in change.files_modified:
                # Extract component from file path
                if 'agents' in file_path:
                    components.add('agent_logic')
                elif 'routing' in file_path:
                    components.add('routing_system')
                elif 'tools' in file_path:
                    components.add('tool_integration')
                elif 'prompts' in file_path:
                    components.add('prompt_system')
                else:
                    components.add('core_system')
        return list(components)

    def _get_git_commit(self) -> Optional[str]:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd='E:/TORQ-CONSOLE',
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def compare_versions(self, from_version: str, to_version: str) -> VersionComparison:
        """Compare two versions and analyze differences"""
        if from_version not in self.versions or to_version not in self.versions:
            raise ValueError("One or both versions not found")

        from_version_data = self.versions[from_version]
        to_version_data = self.versions[to_version]

        # Calculate performance deltas
        performance_delta = {}
        for metric in set(from_version_data.performance_metrics.keys()) | set(to_version_data.performance_metrics.keys()):
            from_value = from_version_data.performance_metrics.get(metric, 0)
            to_value = to_version_data.performance_metrics.get(metric, 0)
            if from_value != 0:
                delta = (to_value - from_value) / from_value
                performance_delta[metric] = delta

        # Check for regressions
        regression_detected = any(delta < -0.05 for delta in performance_delta.values())  # 5% threshold

        # Identify breaking changes
        breaking_changes = []
        for change in to_version_data.changes:
            if change.breaking_change:
                breaking_changes.append(change.description)

        # Identify migration requirements
        migration_requirements = []
        for change in to_version_data.changes:
            if change.migration_required:
                migration_requirements.append(change.description)

        # Generate improvement summary
        improvement_summary = self._generate_improvement_summary(performance_delta, to_version_data.changes)

        # Generate recommendation
        recommendation = self._generate_upgrade_recommendation(performance_delta, regression_detected, breaking_changes)

        comparison = VersionComparison(
            from_version=from_version,
            to_version=to_version,
            performance_delta=performance_delta,
            improvement_summary=improvement_summary,
            regression_detected=regression_detected,
            breaking_changes=breaking_changes,
            migration_requirements=migration_requirements,
            recommendation=recommendation
        )

        # Store comparison
        self.comparisons[(from_version, to_version)] = comparison
        self._save_comparison(comparison)

        return comparison

    def _generate_improvement_summary(self, performance_delta: Dict[str, float], changes: List[ChangeRecord]) -> str:
        """Generate summary of improvements"""
        improvements = []
        degradations = []

        for metric, delta in performance_delta.items():
            if delta > 0.05:  # 5% improvement threshold
                improvements.append(f"{metric}: +{delta:.1%}")
            elif delta < -0.05:  # 5% degradation threshold
                degradations.append(f"{metric}: {delta:.1%}")

        summary_parts = []
        if improvements:
            summary_parts.append(f"Improvements in {', '.join(improvements)}")
        if degradations:
            summary_parts.append(f"Degradations in {', '.join(degradations)}")

        # Add change summary
        if changes:
            summary_parts.append(f"{len(changes)} changes implemented")

        return "; ".join(summary_parts) if summary_parts else "No significant changes"

    def _generate_upgrade_recommendation(self, performance_delta: Dict[str, float],
                                       regression_detected: bool, breaking_changes: List[str]) -> str:
        """Generate upgrade recommendation"""
        if breaking_changes:
            return "⚠️ BREAKING CHANGES - Requires careful planning and migration"

        if regression_detected:
            return "⚠️ REGRESSIONS DETECTED - Recommend thorough testing before upgrade"

        # Check overall performance
        positive_changes = sum(1 for delta in performance_delta.values() if delta > 0.01)
        negative_changes = sum(1 for delta in performance_delta.values() if delta < -0.01)

        if positive_changes > negative_changes and positive_changes > 0:
            return "✅ RECOMMENDED - Shows overall improvement"
        elif positive_changes == negative_changes == 0:
            return "➡️ NEUTRAL - No significant impact"
        else:
            return "❌ NOT RECOMMENDED - Shows overall degradation"

    async def deploy_version(self, version: str, environment: str, deployed_by: str,
                           deployment_config: Optional[Dict] = None) -> DeploymentRecord:
        """
        Deploy a version to a specific environment

        Args:
            version: Version to deploy
            environment: Target environment (testing, staging, production)
            deployed_by: Person performing deployment
            deployment_config: Additional deployment configuration

        Returns:
            Deployment record
        """
        if version not in self.versions:
            raise ValueError(f"Version {version} not found")

        version_data = self.versions[version]

        # Create deployment record
        deployment = DeploymentRecord(
            version=version,
            environment=environment,
            deployed_at=datetime.now(),
            deployed_by=deployed_by,
            deployment_config=deployment_config or {},
            rollback_plan=self._generate_rollback_plan(version),
            monitoring_setup=self._setup_monitoring(version, environment),
            status=DeploymentStatus.DEPLOYING if environment == "production" else DeploymentStatus.TESTING
        )

        # Add to deployment records
        if version not in self.deployment_records:
            self.deployment_records[version] = []
        self.deployment_records[version].append(deployment)

        # Update version status
        if environment == "production":
            version_data.deployment_status = DeploymentStatus.PRODUCTION
        elif environment == "staging":
            version_data.deployment_status = DeploymentStatus.STAGING
        else:
            version_data.deployment_status = DeploymentStatus.TESTING

        # Save deployment record
        self._save_deployment_record(deployment)

        # Simulate deployment process
        await self._simulate_deployment(deployment)

        self.logger.info(f"Deployed version {version} to {environment}")
        return deployment

    def _generate_rollback_plan(self, version: str) -> Dict[str, Any]:
        """Generate rollback plan for a version"""
        version_data = self.versions[version]

        # Find previous stable version
        previous_versions = [v for v in self.agent_versions.get(version_data.agent_type, [])
                          if v != version and self.versions[v].deployment_status == DeploymentStatus.PRODUCTION]

        rollback_target = max(previous_versions, key=self._version_sort_key) if previous_versions else None

        return {
            "rollback_target": rollback_target,
            "rollback_steps": [
                "Stop current deployment",
                f"Rollback to version {rollback_target}" if rollback_target else "Rollback to previous stable version",
                "Verify system functionality",
                "Monitor for issues"
            ],
            "estimated_downtime": "5-10 minutes",
            "risk_level": "low" if not any(c.breaking_change for c in version_data.changes) else "medium"
        }

    def _setup_monitoring(self, version: str, environment: str) -> Dict[str, Any]:
        """Setup monitoring for deployed version"""
        return {
            "metrics_to_monitor": [
                "success_rate",
                "response_time",
                "error_rate",
                "confidence_scores"
            ],
            "alert_thresholds": {
                "success_rate": 0.90,
                "response_time": 3.0,
                "error_rate": 0.10
            },
            "monitoring_duration": "72 hours",
            "dashboard_url": f"/monitoring/{version}/{environment}"
        }

    async def _simulate_deployment(self, deployment: DeploymentRecord):
        """Simulate deployment process"""
        # Simulate deployment time
        await asyncio.sleep(0.5)

        # Update status based on environment
        if deployment.environment == "production":
            deployment.status = DeploymentStatus.PRODUCTION
        else:
            deployment.status = DeploymentStatus.TESTING

        self.logger.info(f"Deployment simulation completed for {deployment.version} to {deployment.environment}")

    async def rollback_version(self, version: str, reason: str, rolled_back_by: str) -> bool:
        """
        Rollback a deployed version

        Args:
            version: Version to rollback
            reason: Reason for rollback
            rolled_back_by: Person performing rollback

        Returns:
            Success status
        """
        if version not in self.versions:
            raise ValueError(f"Version {version} not found")

        version_data = self.versions[version]

        # Find rollback target
        rollback_plan = version_data.metadata.get("rollback_plan", {})
        rollback_target = rollback_plan.get("rollback_target")

        if not rollback_target:
            self.logger.error(f"No rollback target available for version {version}")
            return False

        # Perform rollback
        await asyncio.sleep(1.0)  # Simulate rollback time

        # Update statuses
        version_data.deployment_status = DeploymentStatus.ROLLED_BACK

        # Add rollback reason to metadata
        version_data.metadata["rollback"] = {
            "reason": reason,
            "rolled_back_by": rolled_back_by,
            "rolled_back_at": datetime.now().isoformat(),
            "rolled_back_to": rollback_target
        }

        # Save changes
        self._save_versions()

        self.logger.info(f"Rolled back version {version} to {rollback_target}")
        return True

    def get_version_history(self, agent_type: Optional[str] = None) -> List[AgentVersion]:
        """Get version history, optionally filtered by agent type"""
        versions = list(self.versions.values())

        if agent_type:
            versions = [v for v in versions if v.agent_type == agent_type]

        # Sort by version (descending)
        versions.sort(key=lambda v: self._version_sort_key(v.version), reverse=True)
        return versions

    def get_latest_version(self, agent_type: str, environment: Optional[str] = None) -> Optional[str]:
        """Get latest version for an agent, optionally filtered by deployment status"""
        agent_versions = self.agent_versions.get(agent_type, [])
        if not agent_versions:
            return None

        for version_str in sorted(agent_versions, key=self._version_sort_key, reverse=True):
            version_data = self.versions[version_str]
            if environment is None or version_data.deployment_status.value == environment:
                return version_str

        return None

    def print_version_comparison(self, from_version: str, to_version: str):
        """Print formatted version comparison"""
        comparison = self.comparisons.get((from_version, to_version))
        if not comparison:
            try:
                comparison = self.compare_versions(from_version, to_version)
            except ValueError as e:
                print(f"Error comparing versions: {e}")
                return

        print(f"\n{'='*80}")
        print(f"VERSION COMPARISON: {from_version} → {to_version}")
        print(f"{'='*80}")

        print(f"\nPERFORMANCE DELTAS:")
        for metric, delta in comparison.performance_delta.items():
            arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
            color = "🟢" if delta > 0.05 else "🔴" if delta < -0.05 else "🟡"
            print(f"  {color} {metric}: {arrow} {delta:+.1%}")

        print(f"\nIMPROVEMENT SUMMARY:")
        print(f"  {comparison.improvement_summary}")

        print(f"\nSTATUS:")
        if comparison.regression_detected:
            print(f"  🔴 REGRESSIONS DETECTED")
        if comparison.breaking_changes:
            print(f"  ⚠️ BREAKING CHANGES: {len(comparison.breaking_changes)}")
            for change in comparison.breaking_changes:
                print(f"    - {change}")
        if comparison.migration_requirements:
            print(f"  📋 MIGRATION REQUIRED: {len(comparison.migration_requirements)}")
            for req in comparison.migration_requirements:
                print(f"    - {req}")

        print(f"\nRECOMMENDATION:")
        print(f"  {comparison.recommendation}")

        print(f"{'='*80}")

    def _save_versions(self):
        """Save versions to storage"""
        versions_data = {}
        for version_str, version in self.versions.items():
            versions_data[version_str] = {
                "version": version.version,
                "version_type": version.version_type.value,
                "agent_type": version.agent_type,
                "changes": [
                    {
                        "category": change.category.value,
                        "description": change.description,
                        "files_modified": change.files_modified,
                        "test_results": change.test_results,
                        "performance_impact": change.performance_impact,
                        "breaking_change": change.breaking_change,
                        "migration_required": change.migration_required
                    }
                    for change in version.changes
                ],
                "performance_metrics": version.performance_metrics,
                "created_at": version.created_at.isoformat(),
                "created_by": version.created_by,
                "parent_version": version.parent_version,
                "git_commit": version.git_commit,
                "deployment_status": version.deployment_status.value,
                "metadata": version.metadata
            }

        with open(f"{self.config_dir}/versions.json", 'w') as f:
            json.dump(versions_data, f, indent=2)

    def _create_version_backup(self, version: AgentVersion):
        """Create backup of version files"""
        backup_dir = f"{self.backup_dir}/{version.version}"
        os.makedirs(backup_dir, exist_ok=True)

        # Save version metadata
        with open(f"{backup_dir}/version_metadata.json", 'w') as f:
            json.dump(asdict(version), f, indent=2, default=str)

        self.logger.info(f"Created backup for version {version.version}")

    def _save_comparison(self, comparison: VersionComparison):
        """Save version comparison to storage"""
        comparison_file = f"{self.version_control_dir}/comparisons/{comparison.from_version}_to_{comparison.to_version}.json"

        comparison_data = asdict(comparison)
        comparison_data["comparison_date"] = datetime.now().isoformat()

        with open(comparison_file, 'w') as f:
            json.dump(comparison_data, f, indent=2)

    def _save_deployment_record(self, deployment: DeploymentRecord):
        """Save deployment record to storage"""
        deployment_file = f"{self.version_control_dir}/deployments/{deployment.version}_{deployment.environment}_{deployment.deployed_at.strftime('%Y%m%d_%H%M%S')}.json"

        deployment_data = asdict(deployment)
        deployment_data["deployed_at"] = deployment.deployed_at.isoformat()
        deployment_data["status"] = deployment.status.value

        with open(deployment_file, 'w') as f:
            json.dump(deployment_data, f, indent=2)

# Main execution function for testing
async def main():
    """Main execution function for testing version control system"""
    print("🔧 Maxim AI - Phase 2: Version Control System")
    print("=" * 60)

    # Initialize version control system
    vcs = VersionControlSystem()

    # Create example changes
    changes = [
        ChangeRecord(
            category=ChangeCategory.PROMPT_OPTIMIZATION,
            description="Improved structured prompt templates for better reasoning",
            files_modified=["agents/torq_prince_flowers.py", "prompts/structured_templates.md"],
            test_results={"accuracy": 0.92, "coherence": 0.89},
            performance_impact={"reasoning_quality": 0.15, "response_relevance": 0.08},
            breaking_change=False,
            migration_required=False
        ),
        ChangeRecord(
            category=ChangeCategory.ROUTING_IMPROVEMENT,
            description="Enhanced query routing with better keyword detection",
            files_modified=["agents/marvin_orchestrator.py", "routing/keyword_detector.py"],
            test_results={"routing_accuracy": 0.94, "misrouting_rate": 0.02},
            performance_impact={"tool_selection_efficiency": 0.12, "execution_performance": 0.05},
            breaking_change=False,
            migration_required=False
        )
    ]

    performance_metrics = {
        "overall_quality_score": 0.91,
        "reasoning_quality": 0.93,
        "response_relevance": 0.89,
        "tool_selection_efficiency": 0.88,
        "execution_performance": 0.92,
        "error_handling": 0.96,
        "confidence_calibration": 0.90
    }

    # Create new version
    print("\n📝 Creating new version...")
    version = vcs.create_version(
        agent_type="torq_prince",
        version_type=VersionType.MINOR,
        changes=changes,
        performance_metrics=performance_metrics,
        created_by="ai_system"
    )

    print(f"✅ Created version: {version}")

    # Create another version for comparison
    changes_v2 = [
        ChangeRecord(
            category=ChangeCategory.PERFORMANCE_OPTIMIZATION,
            description="Optimized response generation for 20% faster execution",
            files_modified=["agents/response_generator.py", "utils/cache_manager.py"],
            test_results={"response_time": 0.8, "cache_hit_rate": 0.75},
            performance_impact={"execution_performance": 0.20, "response_time": -0.20},
            breaking_change=False,
            migration_required=False
        )
    ]

    performance_metrics_v2 = performance_metrics.copy()
    performance_metrics_v2["execution_performance"] = 0.95  # Improved

    version_v2 = vcs.create_version(
        agent_type="torq_prince",
        version_type=VersionType.PATCH,
        changes=changes_v2,
        performance_metrics=performance_metrics_v2,
        created_by="ai_system",
        parent_version=version
    )

    print(f"✅ Created version: {version_v2}")

    # Compare versions
    print("\n📊 Comparing versions...")
    vcs.print_version_comparison(version, version_v2)

    # Deploy version
    print("\n🚀 Deploying version to testing...")
    deployment = await vcs.deploy_version(
        version=version_v2,
        environment="testing",
        deployed_by="test_engineer"
    )

    print(f"✅ Deployed {deployment.version} to {deployment.environment}")

    # Show version history
    print("\n📚 Version History:")
    history = vcs.get_version_history("torq_prince")
    for ver in history[:3]:  # Show last 3 versions
        print(f"  {ver.version} - {ver.version_type.value} - {ver.deployment_status.value} - {ver.created_at.strftime('%Y-%m-%d')}")

    # Show latest version
    latest = vcs.get_latest_version("torq_prince")
    print(f"\n🏆 Latest Version: {latest}")

    print(f"\n✅ Version control system demonstration completed!")

if __name__ == "__main__":
    asyncio.run(main())