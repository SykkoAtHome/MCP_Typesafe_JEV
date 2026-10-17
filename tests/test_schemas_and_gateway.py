"""Unit tests for System One schemas, numeric validators, and JevGateway HTTP client."""

from __future__ import annotations

import httpx
import pytest

from typesafe_jev_mcp.db.schemas import (
    ChoiceQuestion,
    EvaluationRequest,
    NoulAnswer,
    NoulQuestion,
    ScoreQuestion,
    derive_noul_confidence,
)
from typesafe_jev_mcp.errors import AuthenticationError, ValidationError
from typesafe_jev_mcp.repositories.jev import JevGateway

SYNTHETIC_KEY = "apikey_0000111122223333444455556666_aaaa1111bbbb2222cccc3333dddd4444eeee5555ffff6666"


def test_derive_noul_confidence_math() -> None:
    assert derive_noul_confidence(0.5) == 0.0
    assert derive_noul_confidence(1.0) == 1.0
    assert derive_noul_confidence(0.0) == 1.0
    assert derive_noul_confidence(0.75) == 0.5
    ans = NoulAnswer(noul=0.9)
    assert ans.confidence == 0.8


def test_schema_validation_rejects_nan_and_invalid_rubrics() -> None:
    with pytest.raises(ValidationError):
        EvaluationRequest(
            state={"bad": float("nan")},
            questions={"q": NoulQuestion(instructions="Is it valid?")},
        )
    with pytest.raises(ValidationError):
        ScoreQuestion(instructions="Rate this", criteria=["only one level"])
    with pytest.raises(ValidationError):
        ChoiceQuestion(instructions="Pick one", criteria={})


async def test_jev_gateway_retries_on_429_and_parses_response() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        assert request.headers["Authorization"] == f"Bearer {SYNTHETIC_KEY}"
        if attempts == 1:
            return httpx.Response(429, headers={"retry-after": "0.01"}, json={"error": {"message": "Rate limit"}})
        return httpx.Response(
            200,
            json={
                "id": "eval_123",
                "created_at": 1760000000,
                "model": "jev-1.13.0",
                "answers": {
                    "route": {
                        "type": "choice",
                        "choice": "haiku",
                        "probabilities": {"haiku": 0.85, "sonnet": 0.12, "opus": 0.03},
                        "confidence": 0.78,
                    },
                    "safe": {
                        "type": "noul",
                        "noul": 0.95,
                    },
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        gateway = JevGateway(explicit_api_key=SYNTHETIC_KEY, http_client=client)
        req = EvaluationRequest(
            state={"task": "Format README"},
            questions={
                "route": ChoiceQuestion(
                    instructions="Pick model",
                    criteria={"haiku": "fast", "sonnet": "balanced", "opus": "deep"},
                ),
                "safe": NoulQuestion(instructions="Is it safe?"),
            },
        )
        res = await gateway.evaluate(req)

    assert attempts == 2
    assert res.id == "eval_123"
    assert res.answers["route"].type == "choice"
    assert res.answers["safe"].confidence == 0.9


async def test_jev_gateway_redacts_key_on_auth_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"message": f"Invalid token {SYNTHETIC_KEY}"}},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        gateway = JevGateway(explicit_api_key=SYNTHETIC_KEY, http_client=client)
        req = EvaluationRequest(
            state="test",
            questions={"q": NoulQuestion(instructions="Check?")},
        )
        with pytest.raises(AuthenticationError) as exc_info:
            await gateway.evaluate(req)
        assert SYNTHETIC_KEY not in str(exc_info.value)
