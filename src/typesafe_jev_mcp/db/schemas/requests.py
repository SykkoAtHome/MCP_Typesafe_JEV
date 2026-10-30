"""Validated System One evaluation request."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from typesafe_jev_mcp.db.schemas.assets import validate_assets
from typesafe_jev_mcp.db.schemas.primitives import BoxQuestion, JsonValue, QuestionItem, validate_json_state
from typesafe_jev_mcp.errors import ValidationError


class EvaluationRequest(BaseModel):
    """Validated payload for `POST https://api.typesafe.ai/v1/systemone`."""

    model_config = ConfigDict(extra="forbid")

    model: str = "jev-latest"
    state: JsonValue = ""
    questions: dict[str, QuestionItem]
    assets: dict[str, dict[str, str]] | None = None
    long_context: bool = False
    enable_images: bool = False

    @field_validator("state")
    @classmethod
    def _validate_state(cls, val: Any) -> Any:
        return validate_json_state(val)

    @field_validator("assets")
    @classmethod
    def _validate_assets(cls, val: dict[str, dict[str, str]] | None) -> dict[str, dict[str, str]] | None:
        return validate_assets(val)

    @model_validator(mode="after")
    def _validate_questions(self) -> EvaluationRequest:
        if not self.questions:
            raise ValidationError("EvaluationRequest requires at least one question.")
        has_box = any(isinstance(q, BoxQuestion) for q in self.questions.values())
        if has_box and not self.assets:
            raise ValidationError("Box questions require at least one image asset.")
        if has_box or self.assets:
            self.enable_images = True
        return self

    def to_api_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "state": self.state,
            "questions": {qid: q.to_api_dict() for qid, q in self.questions.items()},
        }
        if self.assets:
            payload["assets"] = self.assets
        return payload
