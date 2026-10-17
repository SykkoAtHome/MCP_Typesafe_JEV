"""Domain exception hierarchy with automatic secret redaction."""

from __future__ import annotations

import re

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"apikey_[A-Za-z0-9_]{8,}"),
    re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._\-]{8,}"),
    re.compile(r"(?i)(TYPESAFE_API_KEY\s*=\s*)[^\s\"']+"),
)


def redact_secrets(text: str) -> str:
    """Scrub API keys and bearer tokens from any diagnostic or error string."""
    if not text:
        return text
    redacted = _SECRET_PATTERNS[0].sub(lambda m: _mask_token(m.group(0)), text)
    redacted = _SECRET_PATTERNS[1].sub(r"\1[REDACTED]", redacted)
    return _SECRET_PATTERNS[2].sub(r"\1[REDACTED]", redacted)


def _mask_token(token: str) -> str:
    if len(token) <= 16:
        return "apikey_****"
    return f"{token[:11]}****...****{token[-4:]}"


class JevError(Exception):
    """Base domain error that guarantees its message never leaks raw API keys."""

    def __init__(self, message: str, *, code: str = "jev_error") -> None:
        clean_message = redact_secrets(message)
        super().__init__(clean_message)
        self.message = clean_message
        self.code = code


class AuthenticationError(JevError):
    """Raised when the TypeSafe API key is missing, malformed, or rejected (401/403)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="authentication_error")


class ValidationError(JevError):
    """Raised when a System One evaluation payload violates schema or numeric rules."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class RateLimitError(JevError):
    """Raised when upstream 429/529 rate limits persist after retries."""

    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        super().__init__(message, code="rate_limit_error")
        self.retry_after = retry_after


class UpstreamApiError(JevError):
    """Raised on upstream HTTP or transport failures from api.typesafe.ai."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message, code="upstream_api_error")
        self.status_code = status_code


class ConfigurationError(JevError):
    """Raised when local credential or harness configuration files cannot be read or written."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="configuration_error")
