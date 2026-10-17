"""Async HTTP gateway for `https://api.typesafe.ai/v1/systemone` and `/v1/models`."""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import httpx

from typesafe_jev_mcp.db.credentials import CredentialStore, SecretApiKey
from typesafe_jev_mcp.db.schemas import EvaluationRequest, EvaluationResponse
from typesafe_jev_mcp.errors import (
    AuthenticationError,
    RateLimitError,
    UpstreamApiError,
    ValidationError,
    redact_secrets,
)

DEFAULT_BASE_URL = "https://api.typesafe.ai"
DEFAULT_TIMEOUT_SECONDS = 15.0
MAX_RETRIES = 3


class JevGateway:
    """Executes calibrated System One evaluations against the TypeSafe HTTP API."""

    def __init__(
        self,
        *,
        credential_store: CredentialStore | None = None,
        explicit_api_key: str | SecretApiKey | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._store = credential_store or CredentialStore()
        self._explicit_key = explicit_api_key
        env_url = os.environ.get("TYPESAFE_BASE_URL", "").strip()
        self._base_url = (base_url or env_url or DEFAULT_BASE_URL).rstrip("/")
        env_timeout = os.environ.get("TYPESAFE_TIMEOUT_SECONDS", "").strip()
        self._timeout = timeout_seconds or (
            float(env_timeout) if env_timeout else DEFAULT_TIMEOUT_SECONDS
        )
        self._external_client = http_client

    async def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        """Send a batch of questions to `POST /v1/systemone` and parse the calibrated answers."""
        resolution = self._store.resolve(self._explicit_key)
        headers = self._build_headers(
            resolution.key,
            long_context=request.long_context,
            enable_images=request.enable_images,
        )
        payload = request.to_api_payload()

        started = time.perf_counter()
        raw_json = await self._request_json(
            method="POST",
            path="/v1/systemone",
            headers=headers,
            json_body=payload,
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000.0, 2)
        raw_json["latency_ms"] = elapsed_ms
        return EvaluationResponse.model_validate(raw_json)

    async def list_models(self) -> tuple[list[dict[str, Any]], float]:
        """Fetch available Jev models and aliases from `GET /v1/models`."""
        resolution = self._store.resolve(self._explicit_key)
        headers = self._build_headers(
            resolution.key,
            long_context=False,
            enable_images=False,
        )
        started = time.perf_counter()
        raw_json = await self._request_json(
            method="GET",
            path="/v1/models",
            headers=headers,
            json_body=None,
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000.0, 2)
        models = self._extract_models(raw_json)
        return models, elapsed_ms

    @staticmethod
    def _extract_models(raw_json: Any) -> list[dict[str, Any]]:
        if isinstance(raw_json, list):
            return [item if isinstance(item, dict) else {"id": str(item)} for item in raw_json]
        if isinstance(raw_json, dict):
            for key in ("data", "models"):
                candidate = raw_json.get(key)
                if isinstance(candidate, list):
                    return [
                        item if isinstance(item, dict) else {"id": str(item)}
                        for item in candidate
                    ]
                if isinstance(candidate, dict):
                    return [
                        {"id": k, **(v if isinstance(v, dict) else {"value": v})}
                        for k, v in candidate.items()
                    ]
            return [
                {"id": k, **(v if isinstance(v, dict) else {"value": v})}
                for k, v in raw_json.items()
            ]
        return []

    @staticmethod
    def _build_headers(
        secret_key: SecretApiKey,
        *,
        long_context: bool,
        enable_images: bool,
    ) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {secret_key.get_secret_value()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if long_context:
            headers["TypeSafe-Danger-Zone-Long-Context"] = "true"
        if enable_images:
            headers["TypeSafe-Danger-Zone-Images"] = "true"
        return headers

    async def _request_json(
        self,
        *,
        method: str,
        path: str,
        headers: dict[str, str],
        json_body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        if self._external_client is not None:
            return await self._send_with_retries(
                self._external_client, method=method, url=url, headers=headers, json_body=json_body
            )
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await self._send_with_retries(
                client, method=method, url=url, headers=headers, json_body=json_body
            )

    async def _send_with_retries(
        self,
        client: httpx.AsyncClient,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        json_body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await client.request(method, url, headers=headers, json=json_body)
            except httpx.HTTPError as exc:
                raise UpstreamApiError(
                    f"Network error contacting TypeSafe API: {redact_secrets(str(exc))}"
                ) from exc

            if response.status_code == 200:
                return response.json()

            if response.status_code in (429, 529) and attempt < MAX_RETRIES:
                wait_seconds = self._parse_retry_after(response, attempt)
                await asyncio.sleep(wait_seconds)
                continue

            self._raise_for_status(response)

        raise UpstreamApiError("Exhausted retries contacting TypeSafe API.")

    @staticmethod
    def _parse_retry_after(response: httpx.Response, attempt: int) -> float:
        header = response.headers.get("retry-after", "").strip()
        if header:
            try:
                return min(10.0, max(0.1, float(header)))
            except ValueError:
                pass
        return min(8.0, 0.5 * (2**attempt))

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        status = response.status_code
        detail = redact_secrets(response.text[:500])
        try:
            body = response.json()
            if isinstance(body, dict) and isinstance(body.get("error"), dict):
                detail = redact_secrets(str(body["error"].get("message", detail)))
        except ValueError:
            pass

        if status in (401, 403):
            raise AuthenticationError(f"TypeSafe API authentication failed ({status}): {detail}")
        if status in (400, 413, 422):
            raise ValidationError(f"TypeSafe API rejected request payload ({status}): {detail}")
        if status in (429, 529):
            raise RateLimitError(f"TypeSafe API rate limit or overload ({status}): {detail}")
        raise UpstreamApiError(
            f"TypeSafe API returned HTTP {status}: {detail}", status_code=status
        )
