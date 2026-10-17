"""Immutable value object protecting TypeSafe API keys from accidental leakage."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from typesafe_jev_mcp.errors import AuthenticationError

_KEY_FORMAT_RE = re.compile(r"^apikey_[A-Za-z0-9]+_[A-Za-z0-9]{16,}$")


@dataclass(frozen=True, slots=True)
class SecretApiKey:
    """Wraps a raw TypeSafe API key so __str__ and __repr__ always mask the secret."""

    _raw: str

    def __post_init__(self) -> None:
        cleaned = self._raw.strip()
        if not cleaned:
            raise AuthenticationError("TypeSafe API key cannot be empty.")
        if any(ch.isspace() for ch in cleaned):
            raise AuthenticationError("TypeSafe API key must not contain whitespace.")
        if len(cleaned) < 20:
            raise AuthenticationError("TypeSafe API key is too short to be valid.")
        object.__setattr__(self, "_raw", cleaned)

    def get_secret_value(self) -> str:
        """Return the raw API key exclusively for setting the HTTP Authorization header."""
        return self._raw

    @property
    def is_standard_format(self) -> bool:
        """Return True when the key matches the canonical `apikey_<id>_<secret>` format."""
        return bool(_KEY_FORMAT_RE.match(self._raw))

    @property
    def masked(self) -> str:
        """Return a safe preview keeping only a short prefix and the last 4 characters."""
        if len(self._raw) <= 16:
            return "apikey_****"
        prefix = self._raw[:11] if self._raw.startswith("apikey_") else self._raw[:6]
        return f"{prefix}****...****{self._raw[-4:]}"

    @property
    def fingerprint(self) -> str:
        """Short SHA-256 fingerprint useful for debugging which key is active without exposing it."""
        digest = hashlib.sha256(self._raw.encode("utf-8")).hexdigest()
        return f"sha256:{digest[:12]}"

    def __str__(self) -> str:
        return self.masked

    def __repr__(self) -> str:
        return f"SecretApiKey({self.masked!r})"
