"""Multi-source credential resolution and user-scoped secure storage."""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from typesafe_jev_mcp.db.credentials.secret import SecretApiKey
from typesafe_jev_mcp.errors import AuthenticationError, ConfigurationError

ENV_API_KEY = "TYPESAFE_API_KEY"
ENV_API_KEY_FILE = "TYPESAFE_API_KEY_FILE"


@dataclass(frozen=True, slots=True)
class CredentialResolution:
    """Holds the resolved API key alongside non-sensitive provenance metadata."""

    key: SecretApiKey
    source: str


def default_credentials_path() -> Path:
    """Resolve OS-appropriate user config path for stored credentials."""
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "typesafe-jev-mcp" / "credentials.json"


class CredentialStore:
    """Resolves, saves, and deletes the user's TypeSafe API key safely."""

    def __init__(
        self,
        *,
        credentials_file: Path | None = None,
        dotenv_file: Path | None = None,
    ) -> None:
        self._credentials_file = credentials_file or default_credentials_path()
        self._dotenv_file = dotenv_file or (Path.cwd() / ".env")

    @property
    def credentials_file(self) -> Path:
        return self._credentials_file

    def resolve(self, explicit_key: str | SecretApiKey | None = None) -> CredentialResolution:
        """Resolve API key by priority: explicit -> env -> key file -> .env -> user store."""
        if isinstance(explicit_key, SecretApiKey):
            return CredentialResolution(key=explicit_key, source="explicit")
        if isinstance(explicit_key, str) and explicit_key.strip():
            return CredentialResolution(key=SecretApiKey(explicit_key), source="explicit")

        env_val = os.environ.get(ENV_API_KEY, "").strip()
        if env_val:
            return CredentialResolution(key=SecretApiKey(env_val), source=f"env:{ENV_API_KEY}")

        key_file_Result = self._read_key_file_env()
        if key_file_Result is not None:
            return key_file_Result

        dotenv_result = self._read_dotenv()
        if dotenv_result is not None:
            return dotenv_result

        stored_result = self._read_user_store()
        if stored_result is not None:
            return stored_result

        raise AuthenticationError(
            "TypeSafe API key not found. Set TYPESAFE_API_KEY in your MCP config env, "
            "or run `typesafe-jev-mcp auth set-key` to save it securely in your user profile."
        )

    def save_key(self, raw_key: str | SecretApiKey) -> CredentialResolution:
        """Persist API key in the user's OS profile directory with restricted permissions."""
        secret = raw_key if isinstance(raw_key, SecretApiKey) else SecretApiKey(raw_key)
        target = self._credentials_file
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps({"api_key": secret.get_secret_value()}, indent=2)
            target.write_text(payload, encoding="utf-8")
            if os.name != "nt":
                target.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except OSError as exc:
            raise ConfigurationError(f"Failed to write credentials file {target}: {exc}") from exc
        return CredentialResolution(key=secret, source=f"store:{target}")

    def clear_key(self) -> bool:
        """Remove stored credentials file if present."""
        if not self._credentials_file.exists():
            return False
        try:
            self._credentials_file.unlink()
            return True
        except OSError as exc:
            raise ConfigurationError(f"Failed to remove {self._credentials_file}: {exc}") from exc

    def _read_key_file_env(self) -> CredentialResolution | None:
        file_path_str = os.environ.get(ENV_API_KEY_FILE, "").strip()
        if not file_path_str:
            return None
        path = Path(file_path_str).expanduser()
        if not path.is_file():
            raise AuthenticationError(f"{ENV_API_KEY_FILE} points to missing file: {path}")
        content = path.read_text(encoding="utf-8").strip()
        return CredentialResolution(key=SecretApiKey(content), source=f"file:{path}")

    def _read_dotenv(self) -> CredentialResolution | None:
        if not self._dotenv_file.is_file():
            return None
        try:
            lines = self._dotenv_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            return None
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == ENV_API_KEY:
                cleaned = v.strip().strip("\"'")
                if cleaned and cleaned != "apikey_replace_with_your_key":
                    return CredentialResolution(
                        key=SecretApiKey(cleaned),
                        source=f"dotenv:{self._dotenv_file}",
                    )
        return None

    def _read_user_store(self) -> CredentialResolution | None:
        if not self._credentials_file.is_file():
            return None
        try:
            data = json.loads(self._credentials_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigurationError(
                f"Corrupted credentials file at {self._credentials_file}: {exc}"
            ) from exc
        raw_key = data.get("api_key", "") if isinstance(data, dict) else ""
        if not isinstance(raw_key, str) or not raw_key.strip():
            return None
        return CredentialResolution(
            key=SecretApiKey(raw_key),
            source=f"store:{self._credentials_file}",
        )
