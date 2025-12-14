"""
Rate Limiter for Tool Operations

Implements configurable rate limiting to prevent abuse and resource exhaustion
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
import logging

from .models import RateLimitInfo, ToolRequest, Decision

logger = logging.getLogger(__name__)


class RateLimitRule:
    """Rate limiting rule configuration"""

    def __init__(
        self,
        requests: int,
        window_seconds: int,
        burst_size: Optional[int] = None,
        priority: int = 0
    ):
        """
        Initialize rate limit rule

        Args:
            requests: Number of requests allowed
            window_seconds: Time window in seconds
            burst_size: Maximum burst size (default: requests)
            priority: Rule priority (higher = more restrictive)
        """
        self.requests = requests
        self.window_seconds = window_seconds
        self.burst_size = burst_size or requests
        self.priority = priority

    def __lt__(self, other):
        """Compare rules by priority"""
        return self.priority < other.priority


class TokenBucket:
    """Token bucket implementation for rate limiting"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket

        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens per second refill rate
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Consume tokens from bucket

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        with self._lock:
            now = time.time()
            # Add tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate
            )
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get bucket status"""
        with self._lock:
            return {
                "tokens": self.tokens,
                "capacity": self.capacity,
                "refill_rate": self.refill_rate,
                "last_refill": self.last_refill
            }


class SlidingWindowCounter:
    """Sliding window counter implementation"""

    def __init__(self, window_seconds: int, max_requests: int):
        """
        Initialize sliding window counter

        Args:
            window_seconds: Size of the sliding window
            max_requests: Maximum requests in window
        """
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.requests = deque()
        self._lock = threading.Lock()

    def is_allowed(self) -> bool:
        """
        Check if request is allowed

        Returns:
            True if request is within limits
        """
        with self._lock:
            now = time.time()

            # Remove old requests outside the window
            while self.requests and self.requests[0] <= now - self.window_seconds:
                self.requests.popleft()

            # Check if we're within limits
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True

            return False

    def get_status(self) -> Dict[str, Any]:
        """Get sliding window status"""
        with self._lock:
            now = time.time()
            # Count requests in current window
            current_requests = sum(
                1 for req_time in self.requests
                if req_time > now - self.window_seconds
            )

            return {
                "current_requests": current_requests,
                "max_requests": self.max_requests,
                "window_seconds": self.window_seconds,
                "oldest_request": self.requests[0] if self.requests else None
            }


class RateLimiter:
    """Advanced rate limiting system"""

    def __init__(self, cleanup_interval: int = 60):
        """
        Initialize rate limiter

        Args:
            cleanup_interval: Cleanup interval in seconds
        """
        self.cleanup_interval = cleanup_interval

        # Store different types of rate limiters
        self.global_limiters: Dict[str, Any] = {}  # Global limits
        self.tool_limiters: Dict[str, Dict[str, Any]] = defaultdict(dict)  # Per-tool limits
        self.user_limiters: Dict[str, Dict[str, Any]] = defaultdict(dict)  # Per-user limits
        self.session_limiters: Dict[str, Dict[str, Any]] = defaultdict(dict)  # Per-session limits

        # Configuration storage
        self.global_rules: List[RateLimitRule] = []
        self.tool_rules: Dict[str, List[RateLimitRule]] = defaultdict(list)
        self.user_rules: Dict[str, List[RateLimitRule]] = defaultdict(list)

        # Statistics
        self.stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "denied_requests": 0,
            "rules_active": 0
        }

        # Cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()

        self._lock = threading.Lock()

    def add_global_rule(self, rule: RateLimitRule):
        """Add a global rate limit rule"""
        with self._lock:
            self.global_rules.append(rule)
            self.global_rules.sort()  # Sort by priority
            self.stats["rules_active"] += 1
            logger.info(f"Added global rate limit rule: {rule.requests}/{rule.window_seconds}s")

    def add_tool_rule(self, tool_name: str, rule: RateLimitRule):
        """Add a tool-specific rate limit rule"""
        with self._lock:
            self.tool_rules[tool_name].append(rule)
            self.tool_rules[tool_name].sort()
            self.stats["rules_active"] += 1
            logger.info(f"Added tool rate limit rule for {tool_name}: {rule.requests}/{rule.window_seconds}s")

    def add_user_rule(self, user_id: str, rule: RateLimitRule):
        """Add a user-specific rate limit rule"""
        with self._lock:
            self.user_rules[user_id].append(rule)
            self.user_rules[user_id].sort()
            self.stats["rules_active"] += 1
            logger.info(f"Added user rate limit rule for {user_id}: {rule.requests}/{rule.window_seconds}s")

    def check_rate_limit(
        self,
        request: ToolRequest,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        custom_rules: Optional[List[RateLimitRule]] = None
    ) -> Tuple[bool, Optional[RateLimitInfo]]:
        """
        Check if request is within rate limits

        Args:
            request: Tool request to check
            user_id: User identifier
            session_id: Session identifier
            custom_rules: Additional custom rules to apply

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        with self._lock:
            self.stats["total_requests"] += 1

            # Collect all applicable rules
            applicable_rules = []

            # Global rules
            applicable_rules.extend(self.global_rules)

            # Tool-specific rules
            if request.tool_name in self.tool_rules:
                applicable_rules.extend(self.tool_rules[request.tool_name])

            # User-specific rules
            if user_id and user_id in self.user_rules:
                applicable_rules.extend(self.user_rules[user_id])

            # Custom rules
            if custom_rules:
                applicable_rules.extend(custom_rules)

            # Sort by priority (most restrictive first)
            applicable_rules.sort()

            # Check each rule
            for rule in applicable_rules:
                if not self._check_rule(rule, request, user_id, session_id):
                    # Find the most restrictive rule that was violated
                    rate_info = self._create_rate_limit_info(rule, request.tool_name, user_id, session_id)
                    self.stats["denied_requests"] += 1
                    logger.info(f"Rate limit exceeded for {request.tool_name}: {rule.requests}/{rule.window_seconds}s")
                    return False, rate_info

            # All checks passed
            self.stats["allowed_requests"] += 1
            return True, None

    def _check_rule(
        self,
        rule: RateLimitRule,
        request: ToolRequest,
        user_id: Optional[str],
        session_id: Optional[str]
    ) -> bool:
        """Check a specific rate limit rule"""
        limiter_key = f"{rule.requests}_{rule.window_seconds}_{rule.priority}"

        # Use sliding window counter for simplicity and accuracy
        limiter = self._get_or_create_limiter(limiter_key, rule)

        return limiter.is_allowed()

    def _get_or_create_limiter(self, key: str, rule: RateLimitRule) -> SlidingWindowCounter:
        """Get or create a rate limiter"""
        if key not in self.global_limiters:
            self.global_limiters[key] = SlidingWindowCounter(
                rule.window_seconds,
                rule.requests
            )
        return self.global_limiters[key]

    def _create_rate_limit_info(
        self,
        rule: RateLimitRule,
        tool_name: str,
        user_id: Optional[str],
        session_id: Optional[str]
    ) -> RateLimitInfo:
        """Create rate limit information for exceeded rule"""
        limiter_key = f"{rule.requests}_{rule.window_seconds}_{rule.priority}"
        limiter = self.global_limiters.get(limiter_key)

        current_requests = 0
        if limiter:
            status = limiter.get_status()
            current_requests = status["current_requests"]

        return RateLimitInfo(
            requests_made=current_requests,
            requests_allowed=rule.requests,
            window_seconds=rule.window_seconds,
            reset_time=datetime.utcnow() + timedelta(seconds=rule.window_seconds),
            retry_after_seconds=rule.window_seconds
        )

    def get_rate_limit_status(
        self,
        tool_name: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current rate limit status

        Args:
            tool_name: Specific tool to check
            user_id: Specific user to check
            session_id: Specific session to check

        Returns:
            Rate limit status dictionary
        """
        status = {
            "global_limits": {},
            "tool_limits": {},
            "user_limits": {},
            "statistics": self.stats.copy()
        }

        # Global limit status
        for key, limiter in self.global_limiters.items():
            status["global_limits"][key] = limiter.get_status()

        # Tool-specific status
        if tool_name and tool_name in self.tool_limiters:
            for key, limiter in self.tool_limiters[tool_name].items():
                status["tool_limits"][key] = limiter.get_status()

        # User-specific status
        if user_id and user_id in self.user_limiters:
            for key, limiter in self.user_limiters[user_id].items():
                status["user_limits"][key] = limiter.get_status()

        return status

    def reset_user_limits(self, user_id: str):
        """Reset rate limits for a specific user"""
        with self._lock:
            if user_id in self.user_limiters:
                del self.user_limiters[user_id]
                logger.info(f"Reset rate limits for user: {user_id}")

    def reset_tool_limits(self, tool_name: str):
        """Reset rate limits for a specific tool"""
        with self._lock:
            if tool_name in self.tool_limiters:
                del self.tool_limiters[tool_name]
                logger.info(f"Reset rate limits for tool: {tool_name}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        with self._lock:
            stats = self.stats.copy()

            # Calculate additional statistics
            if stats["total_requests"] > 0:
                stats["allowance_rate"] = stats["allowed_requests"] / stats["total_requests"]
                stats["denial_rate"] = stats["denied_requests"] / stats["total_requests"]
            else:
                stats["allowance_rate"] = 0.0
                stats["denial_rate"] = 0.0

            stats["active_global_limiters"] = len(self.global_limiters)
            stats["active_tool_limiters"] = sum(len(limiters) for limiters in self.tool_limiters.values())
            stats["active_user_limiters"] = sum(len(limiters) for limiters in self.user_limiters.values())

            return stats

    def _cleanup_worker(self):
        """Background worker to clean up old limiters"""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                self._cleanup_old_limiters()
            except Exception as e:
                logger.error(f"Error in rate limiter cleanup: {e}")

    def _cleanup_old_limiters(self):
        """Clean up old and unused limiters"""
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - (self.cleanup_interval * 2)  # Keep for 2 cleanup intervals

            # Cleanup user limiters
            users_to_remove = []
            for user_id, limiters in self.user_limiters.items():
                # Check if any limiter has recent activity
                has_activity = any(
                    hasattr(limiter, 'last_used') and limiter.last_used > cutoff_time
                    for limiter in limiters.values()
                )
                if not has_activity:
                    users_to_remove.append(user_id)

            for user_id in users_to_remove:
                del self.user_limiters[user_id]

            # Cleanup tool limiters
            tools_to_remove = []
            for tool_name, limiters in self.tool_limiters.items():
                has_activity = any(
                    hasattr(limiter, 'last_used') and limiter.last_used > cutoff_time
                    for limiter in limiters.values()
                )
                if not has_activity:
                    tools_to_remove.append(tool_name)

            for tool_name in tools_to_remove:
                del self.tool_limiters[tool_name]

            if users_to_remove or tools_to_remove:
                logger.debug(f"Cleaned up rate limiters: {len(users_to_remove)} users, {len(tools_to_remove)} tools")

    def export_rate_limits(self) -> Dict[str, Any]:
        """Export current rate limit configuration"""
        with self._lock:
            export_data = {
                "global_rules": [
                    {
                        "requests": rule.requests,
                        "window_seconds": rule.window_seconds,
                        "burst_size": rule.burst_size,
                        "priority": rule.priority
                    }
                    for rule in self.global_rules
                ],
                "tool_rules": {
                    tool_name: [
                        {
                            "requests": rule.requests,
                            "window_seconds": rule.window_seconds,
                            "burst_size": rule.burst_size,
                            "priority": rule.priority
                        }
                        for rule in rules
                    ]
                    for tool_name, rules in self.tool_rules.items()
                },
                "user_rules": {
                    user_id: [
                        {
                            "requests": rule.requests,
                            "window_seconds": rule.window_seconds,
                            "burst_size": rule.burst_size,
                            "priority": rule.priority
                        }
                        for rule in rules
                    ]
                    for user_id, rules in self.user_rules.items()
                },
                "statistics": self.get_statistics()
            }

            return export_data