"""
Security Guardrails for Web Research

Protects against common web fetch vulnerabilities:
- localhost/private IP access
- Large content DoS
- Secret leakage in prompts
- Suspicious domains
"""

import re
import logging
import ipaddress
from typing import List, Optional, Set, Dict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Configuration for web research security."""

    # Blocked IP ranges
    BLOCKED_IP_RANGES = [
        "127.0.0.0/8",          # Loopback
        "10.0.0.0/8",           # Private Class A
        "172.16.0.0/12",        # Private Class B
        "192.168.0.0/16",       # Private Class C
        "169.254.0.0/16",       # Link-local
        "::1/128",              # IPv6 loopback
        "fc00::/7",             # IPv6 private
        "fe80::/10",            # IPv6 link-local
    ]

    # Content size limits
    MAX_CONTENT_SIZE = 1_000_000  # 1MB
    MAX_SNIPPET_SIZE = 10_000     # 10KB

    # Timeout limits
    FETCH_TIMEOUT = 30  # seconds

    # Suspicious TLDs (commonly used for spam/malware)
    SUSPICIOUS_TLDS = {
        ".xyz", ".top", ".zip", ".tk", ".gq", ".ml",
        ".cf", ".ga", ".men",
    }

    # Low-trust domains (downrank in results)
    LOW_TRUST_DOMAINS = {
        "contentsmartz.com", "blogspot.com", "wordpress.com",
        "medium.com", "substack.com",  # Can be good but vary in quality
    }

    # Secrets patterns to redact
    SECRET_PATTERNS = [
        r'sk-[a-zA-Z0-9]{48}',  # OpenAI API key
        r'sk-ant-[a-zA-Z0-9_-]{95}',  # Anthropic API key
        r'tvly-[a-zA-Z0-9_-]{40}',  # Tavily API key
        r'[a-zA-Z0-9]{32}',  # Generic 32-char key (Supabase anon, etc.)
        r'Bearer\s+[a-zA-Z0-9_-]{20,}',  # Bearer tokens
        r'password["\']?\s*[:=]\s*["\']?[^\s"\']+',  # password="..."
        r'api[_-]?key["\']?\s*[:=]\s*["\']?[^\s"\']+',  # api_key="..."
    ]

    # Allowed domains (whitelist approach for fetch)
    # If set, only these domains can be fetched
    ALLOWED_DOMAINS: Optional[Set[str]] = None


class WebSecurityChecker:
    """
    Validates web requests and responses for security issues.
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()

    def is_url_allowed(self, url: str) -> tuple[bool, Optional[str]]:
        """
        Check if a URL is allowed to be fetched.

        Returns:
            (allowed, reason_if_denied)
        """
        try:
            parsed = urlparse(url)

            # Check for missing scheme
            if parsed.scheme not in ["http", "https"]:
                return False, "Invalid scheme"

            # Check hostname against blocked IPs
            hostname = parsed.hostname
            if not hostname:
                return False, "Missing hostname"

            # Check if it's an IP address in blocked range
            try:
                ip = ipaddress.ip_address(hostname)
                for blocked_range in self.config.BLOCKED_IP_RANGES:
                    if ip in ipaddress.ip_network(blocked_range):
                        return False, f"Blocked IP range: {blocked_range}"
            except ValueError:
                pass  # Not an IP, continue

            # Check for localhost variants
            if hostname.lower() in [
                "localhost", "127.0.0.1", "0.0.0.0",
                "::1", "local",
            ]:
                return False, "Blocked hostname (localhost)"

            # Check TLD if not using IP
            if hostname and "." in hostname:
                tld = "." + hostname.rsplit(".", 1)[-1].lower()
                if tld in self.config.SUSPICIOUS_TLDS:
                    return False, f"Suspicious TLD: {tld}"

            # Check domain whitelist if configured
            if self.config.ALLOWED_DOMAINS is not None:
                if hostname not in self.config.ALLOWED_DOMAINS:
                    return False, f"Domain not in whitelist: {hostname}"

            return True, None

        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False, f"Validation error: {e}"

    def sanitize_prompt(self, prompt: str) -> str:
        """
        Remove secrets and sensitive info from prompt before web request.

        Returns sanitized prompt.
        """
        sanitized = prompt

        # Redact common secret patterns
        for pattern in self.config.SECRET_PATTERNS:
            sanitized = re.sub(
                pattern,
                "[REDACTED_SECRET]",
                sanitized,
                flags=re.IGNORECASE,
            )

        return sanitized

    def validate_content_size(self, content_length: int) -> tuple[bool, Optional[str]]:
        """Check if content size is within limits."""
        if content_length > self.config.MAX_CONTENT_SIZE:
            return False, f"Content too large: {content_length} bytes"
        return True, None

    def validate_snippet(self, snippet: str) -> str:
        """Trim snippet to max size and validate."""
        if len(snippet) > self.config.MAX_SNIPPET_SIZE:
            snippet = snippet[:self.config.MAX_SNIPPET_SIZE] + "..."
        return snippet

    def score_domain_trust(self, domain: str) -> float:
        """
        Score domain trust from 0.0 (untrusted) to 1.0 (highly trusted).

        Factors:
        - Is it a well-known primary source?
        - Is it a news outlet with editorial standards?
        - Is it in low-trust list?
        - TLD reputation
        """
        score = 0.5  # Base score

        # Penalize low-trust domains
        if domain in self.config.LOW_TRUST_DOMAINS:
            score -= 0.2

        # Penalize suspicious TLDs
        for tld in self.config.SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                score -= 0.3

        # Boost well-known sources
        high_trust = [
            # News
            "reuters.com", "apnews.com", "bloomberg.com", "wsj.com",
            "ft.com", "economist.com", "nytimes.com", "washingtonpost.com",
            # Tech
            "arxiv.org", "nature.com", "science.org", "ieee.org",
            # Official sources
            "gov", "edu", "org",
        ]

        if any(trusted in domain for trusted in high_trust):
            score += 0.3

        # Boost .gov, .edu, .org
        if any(domain.endswith(tld) for tld in [".gov", ".edu", ".org"]):
            score += 0.2

        return max(0.0, min(1.0, score))

    def check_response_headers(
        self,
        headers: Dict[str, str],
    ) -> tuple[bool, Optional[str]]:
        """Validate HTTP response headers for security issues."""
        content_type = headers.get("content-type", "")
        content_length = int(headers.get("content-length", 0))

        # Only allow text-based content
        if content_type and not content_type.startswith("text/"):
            if not any(ct in content_type for ct in ["application/json", "application/xml", "application/xml+rss"]):
                return False, f"Blocked content-type: {content_type}"

        # Check content length
        allowed, reason = self.validate_content_size(content_length)
        if not allowed:
            return False, reason

        return True, None


class SecretSanitizer:
    """
    Sanitizes prompts to prevent secret leakage in web requests.
    """

    def __init__(self):
        # Patterns for common secret formats
        self.patterns = [
            # API keys
            (r'(?i)api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', "[API_KEY]"),
            (r'(?i)token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', "[TOKEN]"),
            (r'(?i)secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', "[SECRET]"),

            # Provider-specific keys
            (r'sk-[a-zA-Z0-9]{48}', "[OPENAI_KEY]"),
            (r'sk-ant-[a-zA-Z0-9_-]{95}', "[ANTHROPIC_KEY]"),
            (r'tvly-[a-zA-Z0-9_-]{40}', "[TAVILY_KEY]"),
            (r'BSA[a-zA-Z0-9]{32}', "[BRAVE_KEY]"),

            # URLs with potential tokens
            (r'https?://[^\s/]+/[a-zA-Z0-9_-]{32,}', "[URL_WITH_TOKEN]"),
            (r'https?://[^\s/]+/[a-zA-Z0-9_-]{20,}@', "[URL_WITH_CREDS]"),
        ]

    def sanitize(self, prompt: str) -> tuple[str, int]:
        """
        Sanitize prompt by removing secrets.

        Returns:
            (sanitized_prompt, number_of_replacements)
        """
        sanitized = prompt
        count = 0

        for pattern, replacement in self.patterns:
            matches = len(re.findall(pattern, sanitized))
            if matches > 0:
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
                count += matches

        return sanitized, count


def create_security_checker(**kwargs) -> WebSecurityChecker:
    """Factory to create a security checker."""
    return WebSecurityChecker(**kwargs)


# Singleton
_default_checker: Optional[WebSecurityChecker] = None


def get_security_checker() -> WebSecurityChecker:
    """Get the default security checker."""
    global _default_checker
    if _default_checker is None:
        _default_checker = WebSecurityChecker()
    return _default_checker
