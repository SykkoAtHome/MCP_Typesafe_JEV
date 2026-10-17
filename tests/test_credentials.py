"""Unit tests for SecretApiKey, secret redaction, and multi-source CredentialStore."""

from __future__ import annotations

from pathlib import Path

import pytest

from typesafe_jev_mcp.db.credentials import CredentialStore, SecretApiKey
from typesafe_jev_mcp.errors import AuthenticationError, JevError, redact_secrets

SYNTHETIC_KEY = "apikey_0000111122223333444455556666_aaaa1111bbbb2222cccc3333dddd4444eeee5555ffff6666"


def test_secret_api_key_masks_str_and_repr() -> None:
    secret = SecretApiKey(SYNTHETIC_KEY)
    assert secret.get_secret_value() == SYNTHETIC_KEY
    assert secret.is_standard_format is True
    assert SYNTHETIC_KEY not in str(secret)
    assert SYNTHETIC_KEY not in repr(secret)
    assert str(secret).startswith("apikey_0000")
    assert str(secret).endswith("6666")
    assert secret.fingerprint.startswith("sha256:")


def test_secret_api_key_rejects_invalid_values() -> None:
    with pytest.raises(AuthenticationError):
        SecretApiKey("   ")
    with pytest.raises(AuthenticationError):
        SecretApiKey("apikey_short")
    with pytest.raises(AuthenticationError):
        SecretApiKey("apikey_with space_12345678901234567890")


def test_redact_secrets_scrubs_keys_and_bearer_tokens() -> None:
    raw_msg = (
        f"Failed with Authorization: Bearer {SYNTHETIC_KEY} "
        f"and TYPESAFE_API_KEY={SYNTHETIC_KEY}"
    )
    scrubbed = redact_secrets(raw_msg)
    assert SYNTHETIC_KEY not in scrubbed
    err = JevError(raw_msg)
    assert SYNTHETIC_KEY not in str(err)
    assert SYNTHETIC_KEY not in err.message


def test_credential_store_resolution_priority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_API_KEY_FILE", raising=False)

    cred_file = tmp_path / "credentials.json"
    dotenv_file = tmp_path / ".env"
    store = CredentialStore(credentials_file=cred_file, dotenv_file=dotenv_file)

    with pytest.raises(AuthenticationError):
        store.resolve()

    stored_key = "apikey_stored111122223333_11112222333344445555666677778888"
    store.save_key(stored_key)
    res_store = store.resolve()
    assert res_store.key.get_secret_value() == stored_key
    assert res_store.source.startswith("store:")

    dotenv_key = "apikey_dotenv111122223333_aaaabbbbccccddddeeeeffff00001111"
    dotenv_file.write_text(f"TYPESAFE_API_KEY={dotenv_key}\n", encoding="utf-8")
    res_dotenv = store.resolve()
    assert res_dotenv.key.get_secret_value() == dotenv_key
    assert res_dotenv.source.startswith("dotenv:")

    file_key = "apikey_filekey11112222333_99998888777766665555444433332222"
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text(file_key, encoding="utf-8")
    monkeypatch.setenv("TYPESAFE_API_KEY_FILE", str(secret_file))
    res_file = store.resolve()
    assert res_file.key.get_secret_value() == file_key
    assert res_file.source.startswith("file:")

    env_key = "apikey_envkey111122223333_abababababababababababababababab"
    monkeypatch.setenv("TYPESAFE_API_KEY", env_key)
    res_env = store.resolve()
    assert res_env.key.get_secret_value() == env_key
    assert res_env.source == "env:TYPESAFE_API_KEY"

    assert store.clear_key() is True
    assert store.clear_key() is False
