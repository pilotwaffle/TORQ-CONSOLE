#!/usr/bin/env python3
"""
Agent Consolidation Script

Migrates from scattered agent files to the new consolidated core architecture.
This script helps identify, analyze, and consolidate existing agent functionality.
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter


@dataclass
class AgentInfo:
    """Information about an existing agent file."""
    file_path: str
    agent_name: str
    capabilities: Set[str]
    dependencies: List[str]
    lines_of_code: int
    imports: Set[str]
    classes: List[str]
    functions: List[str]


@dataclass
class ConsolidationResult:
    """Result of consolidation analysis."""
    total_files: int
    total_lines: int
    duplicate_code_estimate: float
    consolidation_targets: Dict[str, List[AgentInfo]]
    recommended_core_agents: Dict[str, List[str]]
    migration_plan: List[Dict[str, str]]


class AgentConsolidator:
    """
    Analyzes and plans consolidation of scattered agent files.
    """

    def __init__(self, base_path: str = "TORQ-CONSOLE"):
        """Initialize consolidator."""
        self.base_path = Path(base_path)
        self.logger = logging.getLogger(__name__)

        # Patterns for identifying agent files
        self.agent_patterns = [
            r".*_agent\.py$",
            r".*_prince_flowers.*\.py$",
            r".*_marvin.*\.py$",
            r".*orchestrat.*\.py$",
            r".*router.*\.py$",
            r".*workflow.*\.py$"
        ]

        # Capability keyword mappings
        self.capability_keywords = {
            "conversation": ["conversation", "chat", "dialog", "message", "session"],
            "code_generation": ["code", "generate", "write", "implement", "create"],
            "debugging": ["debug", "fix", "error", "issue", "problem"],
            "documentation": ["document", "docs", "readme", "guide", "api"],
            "testing": ["test", "testing", "unittest", "coverage"],
            "research": ["research", "search", "find", "analyze", "extract"],
            "architecture": ["architecture", "design", "structure", "system"],
            "orchestration": ["orchestrat", "coordinate", "manage", "workflow"],
            "learning": ["learn", "train", "adapt", "improve"],
            "memory": ["memory", "remember", "store", "recall"]
        }

    async def analyze_agents(self) -> ConsolidationResult:
        """Analyze existing agent files and create consolidation plan."""
        self.logger.info("Starting agent consolidation analysis")

        # Find all agent files
        agent_files = self._find_agent_files()
        self.logger.info(f"Found {len(agent_files)} agent files")

        # Analyze each file
        agent_infos = []
        total_lines = 0

        for file_path in agent_files:
            try:
                info = await self._analyze_agent_file(file_path)
                if info:
                    agent_infos.append(info)
                    total_lines += info.lines_of_code
            except Exception as e:
                self.logger.error(f"Failed to analyze {file_path}: {e}")

        # Group by consolidation targets
        consolidation_targets = self._group_by_consolidation_targets(agent_infos)

        # Estimate duplicate code
        duplicate_estimate = self._estimate_duplicate_code(agent_infos)

        # Create consolidation plan
        consolidation_plan = self._create_consolidation_plan(consolidation_targets)

        result = ConsolidationResult(
            total_files=len(agent_infos),
            total_lines=total_lines,
            duplicate_code_estimate=duplicate_estimate,
            consolidation_targets=consolidation_targets,
            recommended_core_agents=self._get_recommended_core_agents(),
            migration_plan=consolidation_plan
        )

        self.logger.info("Agent consolidation analysis completed")
        return result

    def _find_agent_files(self) -> List[Path]:
        """Find all agent-related Python files."""
        agent_files = []

        for pattern in self.agent_patterns:
            try:
                # Search in agents directories and other common locations
                search_paths = [
                    self.base_path / "torq_console" / "agents",
                    self.base_path / "archive" / "agents",
                    self.base_path / "orchestration" / "agents",
                    self.base_path / "swarm" / "agents"
                ]

                for search_path in search_paths:
                    if search_path.exists():
                        agent_files.extend(search_path.glob(pattern))

                # Also search at base level
                agent_files.extend(self.base_path.glob(pattern))

            except Exception as e:
                self.logger.warning(f"Error searching pattern {pattern}: {e}")

        # Remove duplicates and sort
        return sorted(list(set(agent_files)))

    async def _analyze_agent_file(self, file_path: Path) -> Optional[AgentInfo]:
        """Analyze a single agent file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines_of_code = len([line for line in content.split('\n') if line.strip()])

            # Extract agent name
            agent_name = self._extract_agent_name(file_path, content)

            # Extract capabilities
            capabilities = self._extract_capabilities(content)

            # Extract dependencies
            dependencies = self._extract_dependencies(content)

            # Extract imports
            imports = self._extract_imports(content)

            # Extract classes and functions
            classes = self._extract_classes(content)
            functions = self._extract_functions(content)

            return AgentInfo(
                file_path=str(file_path),
                agent_name=agent_name,
                capabilities=capabilities,
                dependencies=dependencies,
                lines_of_code=lines_of_code,
                imports=imports,
                classes=classes,
                functions=functions
            )

        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return None

    def _extract_agent_name(self, file_path: Path, content: str) -> str:
        """Extract agent name from file path and content."""
        # Try to get from class name first
        class_match = re.search(r'class\s+(\w+Agent)', content, re.IGNORECASE)
        if class_match:
            return class_match.group(1)

        # Try to get from function name
        func_match = re.search(r'def\s+(create_\w+|get_\w+)_agent', content, re.IGNORECASE)
        if func_match:
            return func_match.group(1)

        # Use filename
        return file_path.stem

    def _extract_capabilities(self, content: str) -> Set[str]:
        """Extract capabilities from file content."""
        content_lower = content.lower()
        capabilities = set()

        for capability, keywords in self.capability_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                capabilities.add(capability)

        return capabilities

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from imports."""
        dependencies = []

        # Find import statements
        import_patterns = [
            r'from\s+(.*?)\s+import',
            r'import\s+(.*?)$'
        ]

        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                # Clean up the import
                dep = match.split('.')[0].strip()
                if dep and not dep.startswith('.'):
                    dependencies.append(dep)

        return list(set(dependencies))

    def _extract_imports(self, content: str) -> Set[str]:
        """Extract all import statements."""
        imports = set()

        # Find all import lines
        import_lines = re.findall(r'^(?:from\s+.*?|import\s+).*$', content, re.MULTILINE)
        imports.update(line.strip() for line in import_lines)

        return imports

    def _extract_classes(self, content: str) -> List[str]:
        """Extract class names."""
        classes = re.findall(r'class\s+(\w+)', content)
        return classes

    def _extract_functions(self, content: str) -> List[str]:
        """Extract function names."""
        functions = re.findall(r'def\s+(\w+)', content)
        return functions

    def _group_by_consolidation_targets(self, agent_infos: List[AgentInfo]) -> Dict[str, List[AgentInfo]]:
        """Group agents by consolidation targets."""
        targets = defaultdict(list)

        for info in agent_infos:
            # Determine primary consolidation target based on capabilities
            primary_capability = self._determine_primary_capability(info.capabilities)
            targets[primary_capability].append(info)

        return dict(targets)

    def _determine_primary_capability(self, capabilities: Set[str]) -> str:
        """Determine the primary capability for consolidation."""
        # Priority order for consolidation
        capability_priority = [
            "conversation",
            "orchestration",
            "workflow",
            "research",
            "code_generation",
            "debugging",
            "documentation",
            "testing",
            "architecture",
            "learning",
            "memory"
        ]

        for capability in capability_priority:
            if capability in capabilities:
                return capability

        return "general"

    def _estimate_duplicate_code(self, agent_infos: List[AgentInfo]) -> float:
        """Estimate percentage of duplicate code."""
        # This is a simplified heuristic
        # In a real implementation, you'd use code similarity analysis

        capability_counts = Counter()
        for info in agent_infos:
            for capability in info.capabilities:
                capability_counts[capability] += 1

        # Estimate duplication based on capability overlap
        total_capabilities = sum(capability_counts.values())
        unique_capabilities = len(capability_counts)

        if total_capabilities == 0:
            return 0.0

        # Simple heuristic: if capabilities overlap significantly, estimate duplication
        duplication_factor = max(0, (total_capabilities - unique_capabilities) / total_capabilities)

        # Scale to percentage
        return duplication_factor * 50  # Max 50% duplication estimate

    def _get_recommended_core_agents(self) -> Dict[str, List[str]]:
        """Get recommended core agents and their capabilities."""
        return {
            "ConversationalAgent": [
                "conversation", "memory", "learning"
            ],
            "WorkflowAgent": [
                "code_generation", "debugging", "documentation",
                "testing", "architecture", "code_review"
            ],
            "ResearchAgent": [
                "research", "web_search", "data_analysis"
            ],
            "OrchestrationAgent": [
                "orchestration", "workflow_automation", "learning"
            ]
        }

    def _create_consolidation_plan(self, targets: Dict[str, List[AgentInfo]]) -> List[Dict[str, str]]:
        """Create a step-by-step consolidation plan."""
        plan = []

        # Map capabilities to core agents
        capability_to_agent = {
            "conversation": "ConversationalAgent",
            "memory": "ConversationalAgent",
            "learning": "ConversationalAgent",
            "code_generation": "WorkflowAgent",
            "debugging": "WorkflowAgent",
            "documentation": "WorkflowAgent",
            "testing": "WorkflowAgent",
            "architecture": "WorkflowAgent",
            "code_review": "WorkflowAgent",
            "research": "ResearchAgent",
            "web_search": "ResearchAgent",
            "data_analysis": "ResearchAgent",
            "orchestration": "OrchestrationAgent",
            "workflow_automation": "OrchestrationAgent"
        }

        for capability, agents in targets.items():
            if capability in capability_to_agent:
                target_agent = capability_to_agent[capability]

                for agent_info in agents:
                    plan.append({
                        "step": f"Consolidate {agent_info.agent_name}",
                        "source_file": agent_info.file_path,
                        "target_agent": target_agent,
                        "capability": capability,
                        "action": "migrate_functionality"
                    })

        return plan

    def generate_report(self, result: ConsolidationResult) -> str:
        """Generate a comprehensive consolidation report."""
        report = [
            "# TORQ Console Agent Consolidation Report",
            "",
            "## Executive Summary",
            f"- **Total Agent Files**: {result.total_files}",
            f"- **Total Lines of Code**: {result.total_lines:,}",
            f"- **Estimated Duplicate Code**: {result.duplicate_code_estimate:.1f}%",
            f"- **Consolidation Targets**: {len(result.consolidation_targets)}",
            f"- **Recommended Core Agents**: {len(result.recommended_core_agents)}",
            "",
            "## Consolidation Impact",
            f"**Files Reduction**: {result.total_files} → {len(result.recommended_core_agents)} ({((result.total_files - len(result.recommended_core_agents)) / result.total_files * 100):.1f}% reduction)",
            f"**Code Reduction**: {result.total_lines:,} → ~{result.total_lines * (1 - result.duplicate_code_estimate/100):,.0f} ({result.duplicate_code_estimate:.1f}% reduction)",
            "",
            "## Consolidation Targets",
        ]

        for capability, agents in result.consolidation_targets.items():
            report.append(f"\n### {capability.title()} ({len(agents)} files)")

            for agent in agents[:5]:  # Show first 5
                report.append(f"- **{agent.agent_name}** ({agent.lines_of_code} lines, {len(agent.capabilities)} capabilities)")

            if len(agents) > 5:
                report.append(f"- ... and {len(agents) - 5} more files")

        report.extend([
            "",
            "## Recommended Core Agents",
        ])

        for agent, capabilities in result.recommended_core_agents.items():
            report.append(f"\n### {agent}")
            report.append(f"Capabilities: {', '.join(capabilities)}")

        report.extend([
            "",
            "## Migration Plan",
        ])

        for i, step in enumerate(result.migration_plan[:10], 1):  # Show first 10 steps
            report.append(f"{i}. **{step['step']}**")
            report.append(f"   - Source: `{step['source_file']}`")
            report.append(f"   - Target: `{step['target_agent']}`")
            report.append(f"   - Action: {step['action']}")

        if len(result.migration_plan) > 10:
            report.append(f"... and {len(result.migration_plan) - 10} more migration steps")

        report.extend([
            "",
            "## Benefits of Consolidation",
            "",
            "### 1. **Maintainability**",
            "- Single point of change for each capability",
            "- Consistent APIs and interfaces",
            "- Reduced code duplication",
            "- Easier testing and debugging",
            "",
            "### 2. **Performance**",
            "- Reduced memory footprint",
            "- Shared capabilities and resources",
            "- Optimized agent discovery and routing",
            "",
            "### 3. **Developer Experience**",
            "- Clear, documented APIs",
            "- Type-safe interfaces",
            "- Consistent configuration",
            "- Easy to extend and customize",
            "",
            "## Next Steps",
            "1. Review and approve the consolidation plan",
            "2. Create backup of existing agent files",
            "3. Implement core agent architecture",
            "4. Migrate functionality from scattered agents",
            "5. Update imports and configurations",
            "6. Test consolidated agents",
            "7. Remove deprecated agent files",
            "",
            "---",
            "*This report was generated by the Agent Consolidation Tool*"
        ])

        return "\n".join(report)


async def main():
    """Main function to run consolidation analysis."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Initialize consolidator
    consolidator = AgentConsolidator()

    # Run analysis
    result = await consolidator.analyze_agents()

    # Generate report
    report = consolidator.generate_report(result)

    # Save report
    report_path = Path("agent_consolidation_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Agent consolidation report saved to: {report_path}")

    # Save detailed analysis as JSON
    analysis_data = {
        "summary": {
            "total_files": result.total_files,
            "total_lines": result.total_lines,
            "duplicate_code_estimate": result.duplicate_code_estimate,
            "consolidation_targets_count": len(result.consolidation_targets),
            "recommended_core_agents_count": len(result.recommended_core_agents)
        },
        "consolidation_targets": {
            capability: [
                {
                    "file_path": info.file_path,
                    "agent_name": info.agent_name,
                    "capabilities": list(info.capabilities),
                    "lines_of_code": info.lines_of_code
                }
                for info in agents
            ]
            for capability, agents in result.consolidation_targets.items()
        },
        "migration_plan": result.migration_plan
    }

    json_path = Path("agent_consolidation_analysis.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2)

    print(f"Detailed analysis saved to: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())