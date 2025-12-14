"""
Security Manager for Tool Safety System

Provides comprehensive security protections including input validation,
prompt injection detection, and threat assessment
"""

import re
import hashlib
import hmac
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
import logging

from .models import SecurityContext, RiskLevel, ToolRequest

logger = logging.getLogger(__name__)


class SecurityManager:
    """Comprehensive security manager for tool safety"""

    def __init__(self):
        """Initialize security manager"""
        self.threat_patterns = self._initialize_threat_patterns()
        self.suspicious_indicators = self._initialize_suspicious_indicators()
        self.trusted_sources: Set[str] = set()
        self.blocked_sources: Set[str] = set()
        self.session_risk_scores: Dict[str, float] = {}
        self.security_events: List[Dict[str, Any]] = []

    def _initialize_threat_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Initialize threat detection patterns"""
        return {
            "command_injection": [
                re.compile(r';\s*(rm|del|format|fdisk|mkfs)\s', re.IGNORECASE),
                re.compile(r'\|\s*(sh|bash|cmd|powershell)\s', re.IGNORECASE),
                re.compile(r'&&\s*(rm|del|format)\s', re.IGNORECASE),
                re.compile(r'\$\([^)]*\)\s*&&', re.IGNORECASE),
                re.compile(r'`[^`]*`\s*&&', re.IGNORECASE),
            ],
            "path_traversal": [
                re.compile(r'\.\.[/\\]', re.IGNORECASE),
                re.compile(r'%2e%2e[/\\]', re.IGNORECASE),
                re.compile(r'\.\.%2f', re.IGNORECASE),
                re.compile(r'\.\.%5c', re.IGNORECASE),
            ],
            "code_injection": [
                re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
                re.compile(r'javascript:', re.IGNORECASE),
                re.compile(r'on\w+\s*=', re.IGNORECASE),
                re.compile(r'eval\s*\(', re.IGNORECASE),
                re.compile(r'function\s*\(', re.IGNORECASE),
            ],
            "data_exfiltration": [
                re.compile(r'(password|passwd|pwd)\s*[:=]\s*\w+', re.IGNORECASE),
                re.compile(r'(secret|key|token)\s*[:=]\s*\w+', re.IGNORECASE),
                re.compile(r'(api[_-]?key)\s*[:=]\s*\w+', re.IGNORECASE),
                re.compile(r'(access[_-]?token)\s*[:=]\s*\w+', re.IGNORECASE),
            ],
            "privilege_escalation": [
                re.compile(r'sudo\s+', re.IGNORECASE),
                re.compile(r'su\s+', re.IGNORECASE),
                re.compile(r'chmod\s+777', re.IGNORECASE),
                re.compile(r'chown\s+root', re.IGNORECASE),
                re.compile(r'runas\s+', re.IGNORECASE),
            ],
            "system_disruption": [
                re.compile(r'fork\s*bomb', re.IGNORECASE),
                re.compile(r':\(\)\{\.*\}', re.IGNORECASE),
                re.compile(r'while\s+true', re.IGNORECASE),
                re.compile(r'reboot\s+', re.IGNORECASE),
                re.compile(r'shutdown\s+', re.IGNORECASE),
            ],
            "network_attacks": [
                re.compile(r'nc\s+-l', re.IGNORECASE),  # netcat listener
                re.compile(r'wget\s+.*\|.*sh', re.IGNORECASE),
                re.compile(r'curl\s+.*\|.*bash', re.IGNORECASE),
                re.compile(r'ping\s+-f', re.IGNORECASE),  # flood ping
            ],
            "obfuscation": [
                re.compile(r'base64\s+-d', re.IGNORECASE),
                re.compile(r'printf\s+"\\x', re.IGNORECASE),
                re.compile(r'echo\s+"\\x', re.IGNORECASE),
                re.compile(r'\$\{[^}]*\}', re.IGNORECASE),
            ]
        }

    def _initialize_suspicious_indicators(self) -> Dict[str, List[str]]:
        """Initialize suspicious activity indicators"""
        return {
            "high_frequency_requests": [
                "requests_per_minute > 100",
                "requests_per_hour > 1000"
            ],
            "unusual_tool_combinations": [
                "file_operations + network_access",
                "system_commands + data_access"
            ],
            "suspicious_timing": [
                "requests outside business hours",
                "rapid successive requests"
            ],
            "anomalous_parameters": [
                "extremely long strings",
                "special character sequences",
                "encoded content"
            ]
        }

    def validate_input(
        self,
        input_data: Any,
        input_type: str = "general",
        max_length: Optional[int] = None
    ) -> Tuple[bool, List[str], RiskLevel]:
        """
        Validate input data for security threats

        Args:
            input_data: Input data to validate
            input_type: Type of input (file_path, command, text, etc.)
            max_length: Maximum allowed length

        Returns:
            Tuple of (is_valid, threat_list, risk_level)
        """
        threats = []
        risk_level = RiskLevel.LOW

        if not isinstance(input_data, str):
            try:
                input_data = str(input_data)
            except Exception:
                return False, ["Invalid input type"], RiskLevel.HIGH

        # Length check
        if max_length and len(input_data) > max_length:
            threats.append(f"Input too long: {len(input_data)} > {max_length}")
            risk_level = max(risk_level, RiskLevel.MEDIUM, key=lambda x: ["low", "medium", "high", "critical"].index(x.value))

        # Check for threat patterns
        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if pattern.search(input_data):
                    threats.append(f"Potential {threat_type} detected")
                    risk_level = max(risk_level, RiskLevel.HIGH, key=lambda x: ["low", "medium", "high", "critical"].index(x.value))

        # Specific input type validation
        if input_type == "file_path":
            path_threats = self._validate_file_path(input_data)
            threats.extend(path_threats)
            if path_threats:
                risk_level = max(risk_level, RiskLevel.CRITICAL, key=lambda x: ["low", "medium", "high", "critical"].index(x.value))

        elif input_type == "command":
            cmd_threats = self._validate_command(input_data)
            threats.extend(cmd_threats)
            if cmd_threats:
                risk_level = max(risk_level, RiskLevel.HIGH, key=lambda x: ["low", "medium", "high", "critical"].index(x.value))

        # Check for encoded content
        if self._detect_encoding(input_data):
            threats.append("Potentially encoded content detected")
            risk_level = max(risk_level, RiskLevel.MEDIUM, key=lambda x: ["low", "medium", "high", "critical"].index(x.value))

        is_valid = len(threats) == 0
        return is_valid, threats, risk_level

    def _validate_file_path(self, file_path: str) -> List[str]:
        """Validate file path for security threats"""
        threats = []

        # Check for path traversal
        if ".." in file_path or "%2e%2e" in file_path.lower():
            threats.append("Path traversal attempt detected")

        # Check for suspicious file extensions
        suspicious_extensions = {'.exe', '.bat', '.cmd', '.scr', '.vbs', '.js', '.ps1'}
        if any(file_path.lower().endswith(ext) for ext in suspicious_extensions):
            threats.append(f"Suspicious file extension: {file_path}")

        # Check for system directories
        system_paths = [
            '/etc/', '/bin/', '/sbin/', '/usr/bin/', '/usr/sbin/',
            'C:\\Windows\\', 'C:\\Program Files\\', 'C:\\Users\\'
        ]
        if any(file_path.startswith(path) for path in system_paths):
            threats.append("Access to system directory detected")

        return threats

    def _validate_command(self, command: str) -> List[str]:
        """Validate command for security threats"""
        threats = []

        # Check for dangerous commands
        dangerous_commands = [
            'rm -rf', 'del /f', 'format', 'fdisk', 'mkfs',
            'shutdown', 'reboot', 'halt', 'poweroff'
        ]
        for dangerous_cmd in dangerous_commands:
            if dangerous_cmd in command.lower():
                threats.append(f"Dangerous command detected: {dangerous_cmd}")

        # Check for pipe chains to shells
        if re.search(r'\|\s*(sh|bash|cmd|powershell)', command, re.IGNORECASE):
            threats.append("Shell execution via pipe detected")

        # Check for background execution
        if '&' in command and command.count('&') > 1:
            threats.append("Suspicious background execution detected")

        return threats

    def _detect_encoding(self, input_data: str) -> bool:
        """Detect if input contains encoded content"""
        encoding_patterns = [
            r'[A-Za-z0-9+/]{20,}={0,2}',  # Base64
            r'%[0-9A-Fa-f]{2}',  # URL encoding
            r'\\x[0-9A-Fa-f]{2}',  # Hex encoding
        ]

        for pattern in encoding_patterns:
            if re.search(pattern, input_data):
                return True
        return False

    def assess_request_risk(
        self,
        request: ToolRequest,
        context: Optional[SecurityContext] = None,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> RiskLevel:
        """
        Assess the risk level of a tool request

        Args:
            request: Tool request to assess
            context: Security context
            history: Request history for analysis

        Returns:
            Calculated risk level
        """
        risk_score = 0.0

        # Tool-specific risk factors
        tool_risk_factors = {
            "file_operations_tool": 0.3,
            "browser_automation_tool": 0.4,
            "mcp_client_tool": 0.2,
            "code_generation_tool": 0.2,
            "system_commands": 0.8,
            "network_operations": 0.5,
        }

        risk_score += tool_risk_factors.get(request.tool_name, 0.1)

        # Operation-specific risk factors
        operation_risk_factors = {
            "write": 0.2,
            "delete": 0.6,
            "execute": 0.8,
            "system": 0.9,
            "network": 0.4,
        }

        risk_score += operation_risk_factors.get(request.operation.value, 0.1)

        # Parameter risk assessment
        for key, value in request.parameters.items():
            is_valid, threats, param_risk = self.validate_input(value, key)
            if not is_valid:
                risk_score += len(threats) * 0.1
                if param_risk == RiskLevel.CRITICAL:
                    risk_score += 0.5

        # Context-based risk assessment
        if context:
            # Authentication level
            auth_risk = {
                "none": 0.3,
                "basic": 0.1,
                "oauth": 0.05,
                "mfa": 0.0
            }
            risk_score += auth_risk.get(context.authentication_level, 0.3)

            # Session risk
            if context.session_id:
                session_risk = self.session_risk_scores.get(context.session_id, 0.0)
                risk_score += session_risk * 0.2

            # Time-based risk
            current_hour = datetime.now().hour
            if current_hour < 6 or current_hour > 22:  # Off-hours
                risk_score += 0.1

        # History-based risk assessment
        if history:
            recent_requests = [
                req for req in history[-10:]  # Last 10 requests
                if (datetime.utcnow() - datetime.fromisoformat(req.get('timestamp', '1970-01-01'))).total_seconds() < 3600
            ]

            if len(recent_requests) > 50:  # High frequency
                risk_score += 0.2

            # Check for repeated failures
            failures = sum(1 for req in recent_requests if req.get('decision') == 'deny')
            if failures > 5:
                risk_score += 0.3

        # Convert risk score to risk level
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def detect_prompt_injection(self, prompt: str) -> Tuple[bool, List[str]]:
        """
        Detect prompt injection attempts

        Args:
            prompt: Prompt text to analyze

        Returns:
            Tuple of (is_injection, injection_indicators)
        """
        injection_indicators = []

        # Direct instruction patterns
        injection_patterns = [
            r'ignore\s+(previous|all)\s+(instructions|prompts)',
            r'forget\s+(everything|all\s+previous)',
            r'you\s+are\s+now\s+a',
            r'act\s+as\s+(if\s+)?you\s+are',
            r'from\s+now\s+on',
            r'system\s*:\s*you\s+are',
            r'developer\s*:\s*ignore',
            r'\b(jailbreak|jail\s*break)\b',
            r'dan\s+\d+',
        ]

        for pattern in injection_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                injection_indicators.append(f"Prompt injection pattern: {pattern}")

        # Role-playing indicators
        role_patterns = [
            r'pretend\s+(you\s+are|to\s+be)',
            r'imagine\s+you\s+are',
            r'suppose\s+you\s+are',
            r'roleplay\s+as',
        ]

        for pattern in role_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                injection_indicators.append(f"Role-playing attempt: {pattern}")

        # Encoding and obfuscation
        if self._detect_encoding(prompt):
            injection_indicators.append("Encoded content detected")

        # Multiple instructions in single prompt
        instruction_separators = ['---', '===', '###', '***', '>>>', '<<<']
        separator_count = sum(prompt.count(sep) for sep in instruction_separators)
        if separator_count > 2:
            injection_indicators.append(f"Multiple instruction separators: {separator_count}")

        # Length-based detection
        if len(prompt) > 2000:
            injection_indicators.append(f"Unusually long prompt: {len(prompt)} characters")

        return len(injection_indicators) > 0, injection_indicators

    def generate_session_id(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a secure session ID

        Args:
            user_context: Context information for session

        Returns:
            Secure session ID
        """
        timestamp = str(time.time())
        context_str = str(user_context or {}) + timestamp
        session_hash = hashlib.sha256(context_str.encode()).hexdigest()

        return f"sess_{int(time.time())}_{session_hash[:16]}"

    def update_session_risk(self, session_id: str, risk_delta: float):
        """
        Update risk score for a session

        Args:
            session_id: Session identifier
            risk_delta: Risk score change (-1.0 to 1.0)
        """
        current_risk = self.session_risk_scores.get(session_id, 0.0)
        new_risk = max(0.0, min(1.0, current_risk + risk_delta))
        self.session_risk_scores[session_id] = new_risk

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """
        Clean up old session risk scores

        Args:
            max_age_hours: Maximum age for sessions in hours
        """
        # This is a simplified implementation
        # In production, you'd track session timestamps
        cutoff_time = time.time() - (max_age_hours * 3600)

        sessions_to_remove = []
        for session_id in self.session_risk_scores:
            try:
                # Extract timestamp from session ID
                timestamp_str = session_id.split('_')[1] if '_' in session_id else '0'
                session_time = float(timestamp_str)

                if session_time < cutoff_time:
                    sessions_to_remove.append(session_id)
            except:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.session_risk_scores[session_id]

        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} old security sessions")

    def get_security_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive security report

        Returns:
            Security report dictionary
        """
        return {
            "active_sessions": len(self.session_risk_scores),
            "average_session_risk": sum(self.session_risk_scores.values()) / max(1, len(self.session_risk_scores)),
            "high_risk_sessions": len([s for s in self.session_risk_scores.values() if s > 0.7]),
            "security_events_count": len(self.security_events),
            "recent_events": self.security_events[-10:],  # Last 10 events
            "threat_patterns_loaded": len(self.threat_patterns),
            "trusted_sources": len(self.trusted_sources),
            "blocked_sources": len(self.blocked_sources)
        }

    def add_trusted_source(self, source: str):
        """Add a trusted source"""
        self.trusted_sources.add(source)
        logger.info(f"Added trusted source: {source}")

    def add_blocked_source(self, source: str):
        """Add a blocked source"""
        self.blocked_sources.add(source)
        logger.info(f"Added blocked source: {source}")

    def is_source_trusted(self, source: str) -> bool:
        """Check if a source is trusted"""
        return source in self.trusted_sources

    def is_source_blocked(self, source: str) -> bool:
        """Check if a source is blocked"""
        return source in self.blocked_sources