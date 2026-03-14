"""
Federation Layer Error Types

Phase 1B - Error hierarchy for federation operations.
"""


class FederationError(Exception):
    """Base exception for all federation-related errors."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class IdentityValidationError(FederationError):
    """Raised when node identity validation fails."""

    pass


class SignatureVerificationError(FederationError):
    """Raised when artifact signature verification fails."""

    pass


class TrustEvaluationError(FederationError):
    """Raised when trust evaluation fails."""

    pass


class UnknownNodeError(FederationError):
    """Raised when a node is not recognized in the registry."""

    pass


class QuarantineException(FederationError):
    """Raised when an inbound claim is quarantined."""

    def __init__(self, message: str, quarantine_reasons: list[str]):
        self.quarantine_reasons = quarantine_reasons
        super().__init__(message, details={"reasons": quarantine_reasons})


class ProtocolVersionError(FederationError):
    """Raised when protocol version is unsupported or mismatched."""

    pass


class ReplayAttackError(FederationError):
    """Raised when a replayed message is detected."""

    pass


class DuplicateSuppressionError(FederationError):
    """Raised when a duplicate claim is detected."""

    pass
