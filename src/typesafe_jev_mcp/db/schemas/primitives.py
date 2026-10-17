"""Pydantic schemas for TypeSafe Jev System One primitives (`noul`, `choice`, `score`, `box`)."""

from __future__ import annotations

import math
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from typesafe_jev_mcp.errors import ValidationError

MAX_NESTING_DEPTH = 64
MAX_CHOICE_OPTIONS = 255
MIN_SCORE_LEVELS = 2
MAX_SCORE_LEVELS = 10

JsonValue = Any


def derive_noul_confidence(probability: float) -> float:
    """Compute calibrated distance from maximum uncertainty (0.5): |2p - 1| in [0.0, 1.0]."""
    clamped = max(0.0, min(1.0, float(probability)))
    return round(abs(2.0 * clamped - 1.0), 6)


def validate_json_state(value: Any, *, _depth: int = 0) -> Any:
    """Ensure JSON data contains only finite numbers and stays within Jev's 64-level nesting limit."""
    if _depth > MAX_NESTING_DEPTH:
        raise ValidationError(f"JSON nesting depth exceeds maximum of {MAX_NESTING_DEPTH} levels.")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValidationError("Non-finite float (NaN or Infinity) is not allowed in Jev state.")
        return value
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): validate_json_state(v, _depth=_depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [validate_json_state(item, _depth=_depth + 1) for item in value]
    raise ValidationError(f"Unsupported type in JSON state: {type(value).__name__}")


class NoulCriteria(BaseModel):
    """Optional explicit true/false criteria for a Noul question."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    true_branch: JsonValue = Field(default=None, alias="true")
    false_branch: JsonValue = Field(default=None, alias="false")

    def to_api_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.true_branch is not None:
            payload["true"] = validate_json_state(self.true_branch)
        if self.false_branch is not None:
            payload["false"] = validate_json_state(self.false_branch)
        return payload


class NoulQuestion(BaseModel):
    """Binary probability question returning P(true) in [0.0, 1.0]."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    type: Literal["noul"] = "noul"
    instructions: JsonValue
    criteria: NoulCriteria | dict[str, Any] | None = None

    @field_validator("instructions")
    @classmethod
    def _check_instructions(cls, val: Any) -> Any:
        if val is None or (isinstance(val, str) and not val.strip()):
            raise ValidationError("Noul question instructions cannot be empty.")
        return validate_json_state(val)

    def to_api_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"type": "noul", "instructions": self.instructions}
        if isinstance(self.criteria, NoulCriteria):
            crit = self.criteria.to_api_dict()
            if crit:
                out["criteria"] = crit
        elif isinstance(self.criteria, dict) and self.criteria:
            out["criteria"] = validate_json_state(self.criteria)
        return out


class ChoiceQuestion(BaseModel):
    """Categorical question selecting 1 of up to 255 named options."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["choice"] = "choice"
    instructions: JsonValue
    criteria: dict[str, JsonValue]

    @field_validator("instructions")
    @classmethod
    def _check_instructions(cls, val: Any) -> Any:
        if val is None or (isinstance(val, str) and not val.strip()):
            raise ValidationError("Choice question instructions cannot be empty.")
        return validate_json_state(val)

    @field_validator("criteria")
    @classmethod
    def _check_criteria(cls, val: dict[str, Any]) -> dict[str, Any]:
        if not val:
            raise ValidationError("Choice question requires at least 1 option in criteria.")
        if len(val) > MAX_CHOICE_OPTIONS:
            raise ValidationError(
                f"Choice question supports at most {MAX_CHOICE_OPTIONS} options (got {len(val)})."
            )
        return {
            str(k): None if v is None else validate_json_state(v)
            for k, v in val.items()
        }

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "type": "choice",
            "instructions": self.instructions,
            "criteria": self.criteria,
        }


class ScoreQuestion(BaseModel):
    """Ordinal rubric question with 2 to 10 ordered levels (indexed 0 to n-1)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["score"] = "score"
    instructions: JsonValue
    criteria: list[JsonValue]

    @field_validator("instructions")
    @classmethod
    def _check_instructions(cls, val: Any) -> Any:
        if val is None or (isinstance(val, str) and not val.strip()):
            raise ValidationError("Score question instructions cannot be empty.")
        return validate_json_state(val)

    @field_validator("criteria")
    @classmethod
    def _check_criteria(cls, val: list[Any]) -> list[Any]:
        if not (MIN_SCORE_LEVELS <= len(val) <= MAX_SCORE_LEVELS):
            raise ValidationError(
                f"Score question requires between {MIN_SCORE_LEVELS} and {MAX_SCORE_LEVELS} "
                f"rubric levels (got {len(val)})."
            )
        return [validate_json_state(item) for item in val]

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "type": "score",
            "instructions": self.instructions,
            "criteria": self.criteria,
        }


class BoxQuestion(BaseModel):
    """Bounding box detection question for an image asset (`jev-preview` / `jev-1.14.0`)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["box"] = "box"
    instructions: JsonValue
    asset: str | None = None

    @field_validator("instructions")
    @classmethod
    def _check_instructions(cls, val: Any) -> Any:
        if val is None or (isinstance(val, str) and not val.strip()):
            raise ValidationError("Box question instructions cannot be empty.")
        return validate_json_state(val)

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "type": "box",
            "instructions": self.instructions,
        }


QuestionItem = Annotated[
    Union[NoulQuestion, ChoiceQuestion, ScoreQuestion, BoxQuestion],
    Field(discriminator="type"),
]


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

    @model_validator(mode="after")
    def _validate_questions(self) -> EvaluationRequest:
        if not self.questions:
            raise ValidationError("EvaluationRequest requires at least one question.")
        has_box = any(isinstance(q, BoxQuestion) for q in self.questions.values())
        if has_box or self.assets:
            self.enable_images = True
        if has_box and self.model == "jev-latest":
            self.model = "jev-preview"
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


class NoulAnswer(BaseModel):
    """Parsed answer for a Noul question with derived confidence |2p - 1|."""

    type: Literal["noul"] = "noul"
    noul: float
    confidence: float = 0.0

    @model_validator(mode="after")
    def _compute_confidence(self) -> NoulAnswer:
        self.confidence = derive_noul_confidence(self.noul)
        return self

    @property
    def normalized_value(self) -> float:
        return max(0.0, min(1.0, self.noul))


class ChoiceAnswer(BaseModel):
    """Parsed answer for a Choice question."""

    type: Literal["choice"] = "choice"
    choice: str
    probabilities: dict[str, float]
    confidence: float


class ScoreAnswer(BaseModel):
    """Parsed answer for a Score question with normalized [0.0, 1.0] helper."""

    type: Literal["score"] = "score"
    score: float
    legend: dict[str, JsonValue]
    probabilities: dict[str, float]
    confidence: float

    @property
    def max_index(self) -> int:
        return max(1, len(self.legend) - 1)

    @property
    def normalized_value(self) -> float:
        return round(max(0.0, min(1.0, self.score / self.max_index)), 6)


class BoxCoordinates(BaseModel):
    """Normalized [0, 1] bounding box edges (`top`, `bottom`, `left`, `right`)."""

    top: float
    bottom: float
    left: float
    right: float


class BoxAnswer(BaseModel):
    """Parsed answer for a Box question."""

    type: Literal["box"] = "box"
    box: BoxCoordinates
    confidence: float = 1.0


AnswerItem = Annotated[
    Union[NoulAnswer, ChoiceAnswer, ScoreAnswer, BoxAnswer],
    Field(discriminator="type"),
]


class EvaluationResponse(BaseModel):
    """Parsed response from `POST /v1/systemone`."""

    id: str | None = None
    created_at: int | None = None
    model: str
    answers: dict[str, AnswerItem]
    usage: dict[str, Any] | None = None
    latency_ms: float | None = None

