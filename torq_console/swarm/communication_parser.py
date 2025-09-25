"""
Directional Communication Parser for TORQ Console - Agency Swarm Compatible.

Parses directional communication syntax like 'agent1 > agent2: message'
and converts it to internal messaging format for the swarm system.
"""

import re
import logging
from typing import Dict, List, Any, Optional, NamedTuple
from dataclasses import dataclass


@dataclass
class DirectionalMessage:
    """Represents a parsed directional message."""
    source_agent: str
    target_agents: List[str]
    message_content: str
    priority: str = 'normal'
    require_ack: bool = False
    metadata: Dict[str, Any] = None


class CommunicationParser:
    """
    Parser for Agency Swarm compatible directional communication syntax.

    Supports formats:
    - agent1 > agent2: message
    - agent1 > [agent2, agent3]: message
    - agent1 > agent2 (priority=high): message
    - agent1 > agent2 (ack=true): message
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Regex patterns for parsing directional communication
        self.simple_pattern = re.compile(
            r'^(\w+)\s*>\s*(\w+)\s*:\s*(.+)$',
            re.MULTILINE | re.DOTALL
        )

        self.multi_target_pattern = re.compile(
            r'^(\w+)\s*>\s*\[([^\]]+)\]\s*:\s*(.+)$',
            re.MULTILINE | re.DOTALL
        )

        self.advanced_pattern = re.compile(
            r'^(\w+)\s*>\s*(\w+|\[[^\]]+\])\s*\(([^)]+)\)\s*:\s*(.+)$',
            re.MULTILINE | re.DOTALL
        )

    def parse_directional_syntax(self, content: str) -> List[DirectionalMessage]:
        """
        Parse directional communication syntax from content.

        Args:
            content: Text content that may contain directional communication

        Returns:
            List of DirectionalMessage objects
        """
        messages = []

        # Split content into lines for parsing
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if not line or '>' not in line:
                continue

            # Try parsing with different patterns
            parsed_msg = self._parse_line(line)
            if parsed_msg:
                messages.append(parsed_msg)

        return messages

    def _parse_line(self, line: str) -> Optional[DirectionalMessage]:
        """Parse a single line for directional communication syntax."""

        # Try advanced pattern first (with parameters)
        match = self.advanced_pattern.match(line)
        if match:
            source = match.group(1)
            targets_str = match.group(2)
            params_str = match.group(3)
            message = match.group(4).strip()

            targets = self._parse_targets(targets_str)
            params = self._parse_parameters(params_str)

            return DirectionalMessage(
                source_agent=source,
                target_agents=targets,
                message_content=message,
                priority=params.get('priority', 'normal'),
                require_ack=params.get('ack', False),
                metadata=params
            )

        # Try multi-target pattern
        match = self.multi_target_pattern.match(line)
        if match:
            source = match.group(1)
            targets_str = match.group(2)
            message = match.group(3).strip()

            targets = self._parse_targets(f"[{targets_str}]")

            return DirectionalMessage(
                source_agent=source,
                target_agents=targets,
                message_content=message
            )

        # Try simple pattern
        match = self.simple_pattern.match(line)
        if match:
            source = match.group(1)
            target = match.group(2)
            message = match.group(3).strip()

            return DirectionalMessage(
                source_agent=source,
                target_agents=[target],
                message_content=message
            )

        return None

    def _parse_targets(self, targets_str: str) -> List[str]:
        """Parse target agents from string format."""
        targets_str = targets_str.strip()

        # Handle single target
        if not targets_str.startswith('['):
            return [targets_str.strip()]

        # Handle multiple targets: [agent1, agent2, agent3]
        targets_str = targets_str.strip('[]')
        targets = [t.strip() for t in targets_str.split(',')]
        return [t for t in targets if t]  # Filter empty strings

    def _parse_parameters(self, params_str: str) -> Dict[str, Any]:
        """Parse parameters from string format like 'priority=high, ack=true'."""
        params = {}

        for param in params_str.split(','):
            param = param.strip()
            if '=' in param:
                key, value = param.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Convert value to appropriate type
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)

                params[key] = value

        return params

    def has_directional_syntax(self, content: str) -> bool:
        """Check if content contains directional communication syntax."""
        # Quick check for '>' character followed by ':'
        return bool(re.search(r'\w+\s*>\s*[\w\[\]]+\s*:', content))

    def extract_base_query(self, content: str) -> str:
        """Extract the base query after removing directional communication syntax."""
        messages = self.parse_directional_syntax(content)

        if not messages:
            return content

        # Remove directional communication lines
        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if not self.has_directional_syntax(line):
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

    def validate_agents(self, messages: List[DirectionalMessage],
                       available_agents: List[str]) -> Dict[str, List[str]]:
        """
        Validate that all agents in messages exist.

        Args:
            messages: List of DirectionalMessage objects
            available_agents: List of available agent names

        Returns:
            Dict with 'valid' and 'invalid' agent lists
        """
        all_mentioned_agents = set()

        for msg in messages:
            all_mentioned_agents.add(msg.source_agent)
            all_mentioned_agents.update(msg.target_agents)

        valid_agents = [agent for agent in all_mentioned_agents if agent in available_agents]
        invalid_agents = [agent for agent in all_mentioned_agents if agent not in available_agents]

        return {
            'valid': valid_agents,
            'invalid': invalid_agents
        }

    def format_examples(self) -> List[str]:
        """Return example syntax formats for user reference."""
        return [
            "code_agent > testing_agent: Please test the updated function",
            "search_agent > [analysis_agent, synthesis_agent]: Found relevant data",
            "code_agent > testing_agent (priority=high): Critical bug fix needed",
            "documentation_agent > code_agent (ack=true): Documentation updated",
            "performance_agent > [code_agent, testing_agent] (priority=low): Optimization suggestions"
        ]


# Export parser instance
communication_parser = CommunicationParser()

def parse_directional_communication(content: str) -> List[DirectionalMessage]:
    """
    Convenience function for parsing directional communication.
    Compatible with Agency Swarm directional syntax.
    """
    return communication_parser.parse_directional_syntax(content)

def has_directional_communication(content: str) -> bool:
    """
    Check if content contains directional communication syntax.
    """
    return communication_parser.has_directional_syntax(content)