"""
Content Safety Module for TORQ Console Web Research

Provides security features for web scraping and content processing:
1. Content Sanitization - Remove malicious HTML/JS/scripts
2. Connection Guards - Whitelist/blacklist domains, connection logging
3. Rate Limiting - Per-domain rate limiting to prevent IP bans
4. Security Logging - Audit trail for all web requests

Author: TORQ Console Development Team
Version: 1.0.0
"""

import re
import time
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from urllib.parse import urlparse
import html


class ContentSanitizer:
    """
    Sanitize scraped web content to remove malicious code and scripts.

    Features:
    - HTML/JavaScript injection prevention
    - Script tag removal
    - Event handler attribute removal
    - URL validation
    - File type validation
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Dangerous HTML tags that should be removed
        self.dangerous_tags = [
            'script', 'iframe', 'object', 'embed', 'applet',
            'link', 'style', 'meta', 'base', 'form'
        ]

        # Dangerous HTML attributes (event handlers)
        self.dangerous_attributes = [
            'onclick', 'onload', 'onerror', 'onmouseover',
            'onmouseout', 'onfocus', 'onblur', 'onchange',
            'onsubmit', 'onkeydown', 'onkeyup', 'onkeypress'
        ]

        # Allowed URL schemes
        self.allowed_schemes = ['http', 'https']

        # Dangerous file extensions
        self.dangerous_extensions = [
            '.exe', '.bat', '.cmd', '.sh', '.ps1', '.vbs',
            '.jar', '.app', '.deb', '.rpm', '.dmg', '.pkg'
        ]

    def sanitize_html(self, content: str) -> str:
        """
        Remove dangerous HTML tags and attributes from content.

        Args:
            content: Raw HTML content

        Returns:
            Sanitized content safe for processing
        """
        if not content:
            return ""

        try:
            # Remove dangerous tags
            for tag in self.dangerous_tags:
                # Case-insensitive removal
                pattern = re.compile(f'<{tag}[^>]*?>.*?</{tag}>', re.IGNORECASE | re.DOTALL)
                content = pattern.sub('', content)

                # Remove self-closing tags
                pattern = re.compile(f'<{tag}[^>]*?/>', re.IGNORECASE)
                content = pattern.sub('', content)

            # Remove dangerous attributes
            for attr in self.dangerous_attributes:
                pattern = re.compile(f'{attr}="[^"]*"', re.IGNORECASE)
                content = pattern.sub('', content)
                pattern = re.compile(f"{attr}='[^']*'", re.IGNORECASE)
                content = pattern.sub('', content)

            # Remove javascript: URLs
            content = re.sub(r'href="javascript:[^"]*"', '', content, flags=re.IGNORECASE)
            content = re.sub(r"href='javascript:[^']*'", '', content, flags=re.IGNORECASE)

            # HTML entity decode to prevent encoding-based attacks
            content = html.unescape(content)

            self.logger.debug(f"[SANITIZER] Cleaned content ({len(content)} chars)")
            return content

        except Exception as e:
            self.logger.error(f"[SANITIZER] Error sanitizing content: {e}")
            return ""

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize plain text content.

        Args:
            text: Raw text content

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        try:
            # Remove control characters
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)

            # Trim
            text = text.strip()

            return text

        except Exception as e:
            self.logger.error(f"[SANITIZER] Error sanitizing text: {e}")
            return ""

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Validate URL for safety.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in self.allowed_schemes:
                return False, f"Invalid scheme: {parsed.scheme}"

            # Check for file extensions
            path_lower = parsed.path.lower()
            for ext in self.dangerous_extensions:
                if path_lower.endswith(ext):
                    return False, f"Dangerous file extension: {ext}"

            # Check for localhost/private IPs (prevent SSRF)
            if parsed.hostname:
                if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
                    return False, "Localhost connections not allowed"

                # Check for private IP ranges
                if parsed.hostname.startswith(('10.', '172.16.', '192.168.')):
                    return False, "Private IP addresses not allowed"

            return True, "Valid"

        except Exception as e:
            return False, f"URL parsing error: {e}"


class ConnectionGuard:
    """
    Guard for outbound web connections with whitelist/blacklist support.

    Features:
    - Domain whitelist/blacklist
    - Connection attempt logging
    - Security event tracking
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # Domain blacklist (known malicious or problematic domains)
        self.blacklist: Set[str] = set(self.config.get('blacklist', []))

        # Domain whitelist (if set, only these domains are allowed)
        self.whitelist: Optional[Set[str]] = None
        if self.config.get('whitelist'):
            self.whitelist = set(self.config['whitelist'])

        # Connection attempt log
        self.connection_log: List[Dict] = []

        # Security events
        self.security_events: List[Dict] = []

    def check_domain(self, url: str) -> Tuple[bool, str]:
        """
        Check if connection to domain is allowed.

        Args:
            url: URL to check

        Returns:
            Tuple of (is_allowed, reason)
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Log connection attempt
            self._log_connection_attempt(url, domain)

            # Check blacklist first
            if domain in self.blacklist:
                self._log_security_event('BLOCKED_BLACKLIST', url, domain)
                return False, f"Domain {domain} is blacklisted"

            # Check whitelist if configured
            if self.whitelist and domain not in self.whitelist:
                self._log_security_event('BLOCKED_NOT_WHITELISTED', url, domain)
                return False, f"Domain {domain} not in whitelist"

            return True, "Allowed"

        except Exception as e:
            self._log_security_event('ERROR', url, '', str(e))
            return False, f"Error checking domain: {e}"

    def _log_connection_attempt(self, url: str, domain: str):
        """Log connection attempt."""
        self.connection_log.append({
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'domain': domain
        })

        # Keep only last 1000 entries
        if len(self.connection_log) > 1000:
            self.connection_log = self.connection_log[-1000:]

    def _log_security_event(self, event_type: str, url: str, domain: str, details: str = ''):
        """Log security event."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'url': url,
            'domain': domain,
            'details': details
        }

        self.security_events.append(event)
        self.logger.warning(f"[SECURITY] {event_type}: {domain} - {details}")

        # Keep only last 500 events
        if len(self.security_events) > 500:
            self.security_events = self.security_events[-500:]

    def get_connection_stats(self) -> Dict:
        """Get connection statistics."""
        return {
            'total_connections': len(self.connection_log),
            'security_events': len(self.security_events),
            'recent_domains': list(set([
                c['domain'] for c in self.connection_log[-50:]
            ]))
        }


class RateLimiter:
    """
    Per-domain rate limiter to prevent IP bans and abuse.

    Features:
    - Configurable rate limits per domain
    - Token bucket algorithm
    - Automatic cooldown periods
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # Default rate limits
        self.default_requests_per_minute = self.config.get('default_rpm', 10)
        self.default_requests_per_hour = self.config.get('default_rph', 100)

        # Per-domain custom limits
        self.domain_limits: Dict[str, Dict] = self.config.get('domain_limits', {})

        # Request tracking
        self.request_history: Dict[str, List[float]] = defaultdict(list)

        # Cooldown tracking
        self.cooldowns: Dict[str, float] = {}

    def check_rate_limit(self, url: str) -> Tuple[bool, str, Optional[float]]:
        """
        Check if request is within rate limits.

        Args:
            url: URL to check

        Returns:
            Tuple of (is_allowed, reason, wait_time_seconds)
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Check if domain is in cooldown
            if domain in self.cooldowns:
                cooldown_until = self.cooldowns[domain]
                if time.time() < cooldown_until:
                    wait_time = cooldown_until - time.time()
                    return False, f"Domain in cooldown", wait_time
                else:
                    # Cooldown expired
                    del self.cooldowns[domain]

            # Get rate limits for domain
            rpm, rph = self._get_domain_limits(domain)

            # Clean up old requests
            current_time = time.time()
            self._cleanup_old_requests(domain, current_time)

            # Check minute limit
            recent_minute = [
                t for t in self.request_history[domain]
                if current_time - t < 60
            ]

            if len(recent_minute) >= rpm:
                wait_time = 60 - (current_time - min(recent_minute))
                self.logger.warning(f"[RATE_LIMIT] {domain} exceeded {rpm} req/min")
                return False, f"Rate limit exceeded: {rpm} req/min", wait_time

            # Check hour limit
            recent_hour = [
                t for t in self.request_history[domain]
                if current_time - t < 3600
            ]

            if len(recent_hour) >= rph:
                wait_time = 3600 - (current_time - min(recent_hour))
                self.logger.warning(f"[RATE_LIMIT] {domain} exceeded {rph} req/hour")

                # Put domain in cooldown for 5 minutes
                self.cooldowns[domain] = current_time + 300

                return False, f"Rate limit exceeded: {rph} req/hour", wait_time

            # Record request
            self.request_history[domain].append(current_time)

            return True, "Within limits", None

        except Exception as e:
            self.logger.error(f"[RATE_LIMIT] Error checking rate limit: {e}")
            return False, f"Rate limit check error: {e}", None

    def _get_domain_limits(self, domain: str) -> Tuple[int, int]:
        """Get rate limits for domain."""
        if domain in self.domain_limits:
            limits = self.domain_limits[domain]
            return limits.get('rpm', self.default_requests_per_minute), \
                   limits.get('rph', self.default_requests_per_hour)

        return self.default_requests_per_minute, self.default_requests_per_hour

    def _cleanup_old_requests(self, domain: str, current_time: float):
        """Remove requests older than 1 hour."""
        if domain in self.request_history:
            self.request_history[domain] = [
                t for t in self.request_history[domain]
                if current_time - t < 3600
            ]

    def get_rate_limit_stats(self) -> Dict:
        """Get rate limiting statistics."""
        current_time = time.time()

        stats = {
            'domains_tracked': len(self.request_history),
            'domains_in_cooldown': len(self.cooldowns),
            'per_domain_stats': {}
        }

        for domain, requests in self.request_history.items():
            recent_minute = len([t for t in requests if current_time - t < 60])
            recent_hour = len([t for t in requests if current_time - t < 3600])

            stats['per_domain_stats'][domain] = {
                'requests_last_minute': recent_minute,
                'requests_last_hour': recent_hour,
                'in_cooldown': domain in self.cooldowns
            }

        return stats


class SecurityLogger:
    """
    Security event logger for web research activities.

    Provides audit trail for:
    - All web requests
    - Security events
    - Rate limit violations
    - Content sanitization events
    """

    def __init__(self, log_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.log_file = log_file
        self.events: List[Dict] = []

    def log_request(self, url: str, method: str, status: str, details: str = ''):
        """Log a web request."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': 'WEB_REQUEST',
            'url': url,
            'method': method,
            'status': status,
            'details': details
        }

        self._record_event(event)

    def log_security_event(self, event_type: str, url: str, severity: str, details: str):
        """Log a security event."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': 'SECURITY_EVENT',
            'event_type': event_type,
            'url': url,
            'severity': severity,
            'details': details
        }

        self._record_event(event)

        if severity in ['HIGH', 'CRITICAL']:
            self.logger.error(f"[SECURITY] {event_type}: {url} - {details}")
        else:
            self.logger.warning(f"[SECURITY] {event_type}: {url} - {details}")

    def _record_event(self, event: Dict):
        """Record event to log."""
        self.events.append(event)

        # Keep only last 10000 events in memory
        if len(self.events) > 10000:
            self.events = self.events[-10000:]

        # TODO: Write to file if log_file is configured

    def get_recent_events(self, count: int = 100) -> List[Dict]:
        """Get recent security events."""
        return self.events[-count:]


# Singleton instances for easy access
_sanitizer = ContentSanitizer()
_connection_guard = ConnectionGuard()
_rate_limiter = RateLimiter()
_security_logger = SecurityLogger()


def get_sanitizer() -> ContentSanitizer:
    """Get global ContentSanitizer instance."""
    return _sanitizer


def get_connection_guard() -> ConnectionGuard:
    """Get global ConnectionGuard instance."""
    return _connection_guard


def get_rate_limiter() -> RateLimiter:
    """Get global RateLimiter instance."""
    return _rate_limiter


def get_security_logger() -> SecurityLogger:
    """Get global SecurityLogger instance."""
    return _security_logger
