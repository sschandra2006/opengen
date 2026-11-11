"""
OpenGen Domain Exceptions Hierarchy.
Provides strongly-typed, taggable exceptions for error handling and recovery.
"""

class OpenGenError(Exception):
    """Base exception for all OpenGen domain and operational errors."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class SecurityViolationError(OpenGenError):
    """Raised when an operation violates a security boundary (path traversal, zip bomb, etc.)."""
    pass

class ProviderError(OpenGenError):
    """Raised when an external AI provider fails or exhausts retries."""
    pass

class RateLimitExceededError(ProviderError):
    """Raised when a provider returns HTTP 429 and retry budget is exhausted."""
    pass

class InvalidTemplateError(OpenGenError):
    """Raised when an input document or presentation template is corrupt or malformed."""
    pass

class MappingAmbiguityError(OpenGenError):
    """Raised when required reference facts are missing or conflicting and need clarification."""
    pass

class LayoutValidationError(OpenGenError):
    """Raised when generated document/presentation fails visual formatting constraints."""
    pass
