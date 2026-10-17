"""Domain-agnostic TypeSafe Jev evaluation service."""

from __future__ import annotations

from typing import Any

from typesafe_jev_mcp.db.credentials import CredentialStore
from typesafe_jev_mcp.db.schemas import (
    AnswerItem,
    BoxAnswer,
    BoxQuestion,
    ChoiceAnswer,
    ChoiceQuestion,
    EvaluationRequest,
    NoulAnswer,
    NoulQuestion,
    QuestionItem,
    ScoreAnswer,
    ScoreQuestion,
)
from typesafe_jev_mcp.errors import JevError, ValidationError
from typesafe_jev_mcp.repositories.jev import JevGateway


class EvaluationService:
    """Executes calibrated System One evaluations (`noul`, `choice`, `score`, `box`) on any state."""

    def __init__(
        self,
        *,
        gateway: JevGateway | None = None,
        credential_store: CredentialStore | None = None,
    ) -> None:
        self._store = credential_store or CredentialStore()
        self._gateway = gateway or JevGateway(credential_store=self._store)

    async def evaluate(
        self,
        *,
        state: Any,
        questions: dict[str, dict[str, Any] | QuestionItem],
        model: str = "jev-latest",
        assets: dict[str, dict[str, str]] | None = None,
        weights: dict[str, float] | None = None,
        confidence_threshold: float | None = None,
        long_context: bool = False,
    ) -> dict[str, Any]:
        """Run a parallel batch of Jev questions over `state` in a single `/v1/systemone` call."""
        parsed_questions = {
            qid: self._coerce_question(qid, spec) for qid, spec in questions.items()
        }
        request = EvaluationRequest(
            model=model,
            state=state,
            questions=parsed_questions,
            assets=assets,
            long_context=long_context,
        )
        response = await self._gateway.evaluate(request)
        serialized_answers = {
            qid: self._format_answer(ans) for qid, ans in response.answers.items()
        }
        confidences = [ans.confidence for ans in response.answers.values()]
        min_conf = round(min(confidences), 6) if confidences else 0.0
        mean_conf = round(sum(confidences) / len(confidences), 6) if confidences else 0.0

        result: dict[str, Any] = {
            "id": response.id,
            "model": response.model,
            "latency_ms": response.latency_ms,
            "usage": response.usage,
            "answers": serialized_answers,
            "summary": {
                "question_count": len(serialized_answers),
                "min_confidence": min_conf,
                "mean_confidence": mean_conf,
            },
        }
        if weights:
            result["composite_score"] = self._compute_composite(response.answers, weights)
        if confidence_threshold is not None:
            result["confidence_gate_passed"] = min_conf >= confidence_threshold
        return result

    async def noul(
        self,
        *,
        state: Any,
        instructions: Any,
        true_criteria: Any | None = None,
        false_criteria: Any | None = None,
        assets: dict[str, dict[str, str]] | None = None,
        model: str = "jev-latest",
        long_context: bool = False,
    ) -> dict[str, Any]:
        """Evaluate a single binary `noul` question returning P(true) and derived confidence."""
        criteria: dict[str, Any] = {}
        if true_criteria is not None:
            criteria["true"] = true_criteria
        if false_criteria is not None:
            criteria["false"] = false_criteria
        question = NoulQuestion(instructions=instructions, criteria=criteria or None)
        res = await self.evaluate(
            state=state,
            questions={"q": question},
            assets=assets,
            model=model,
            long_context=long_context,
        )
        ans = res["answers"]["q"]
        return {
            **ans,
            "model": res["model"],
            "latency_ms": res["latency_ms"],
            "usage": res["usage"],
        }

    async def choice(
        self,
        *,
        state: Any,
        instructions: Any,
        criteria: dict[str, Any],
        assets: dict[str, dict[str, str]] | None = None,
        model: str = "jev-latest",
        long_context: bool = False,
    ) -> dict[str, Any]:
        """Evaluate a single `choice` question over up to 255 options."""
        question = ChoiceQuestion(instructions=instructions, criteria=criteria)
        res = await self.evaluate(
            state=state,
            questions={"q": question},
            assets=assets,
            model=model,
            long_context=long_context,
        )
        ans = res["answers"]["q"]
        return {
            **ans,
            "model": res["model"],
            "latency_ms": res["latency_ms"],
            "usage": res["usage"],
        }

    async def score(
        self,
        *,
        state: Any,
        instructions: Any,
        criteria: list[Any],
        assets: dict[str, dict[str, str]] | None = None,
        model: str = "jev-latest",
        long_context: bool = False,
    ) -> dict[str, Any]:
        """Evaluate a single `score` rubric question over 2 to 10 ordered levels."""
        question = ScoreQuestion(instructions=instructions, criteria=criteria)
        res = await self.evaluate(
            state=state,
            questions={"q": question},
            assets=assets,
            model=model,
            long_context=long_context,
        )
        ans = res["answers"]["q"]
        return {
            **ans,
            "model": res["model"],
            "latency_ms": res["latency_ms"],
            "usage": res["usage"],
        }

    async def box(
        self,
        *,
        state: Any,
        instructions: Any,
        assets: dict[str, dict[str, str]],
        model: str = "jev-preview",
        long_context: bool = False,
    ) -> dict[str, Any]:
        """Evaluate a single `box` bounding-box detection question on an image asset."""
        question = BoxQuestion(instructions=instructions)
        res = await self.evaluate(
            state=state,
            questions={"q": question},
            assets=assets,
            model=model,
            long_context=long_context,
        )
        ans = res["answers"]["q"]
        return {
            **ans,
            "model": res["model"],
            "latency_ms": res["latency_ms"],
            "usage": res["usage"],
        }

    async def check_health(self, *, verify_upstream: bool = True) -> dict[str, Any]:
        """Return safe masked credential metadata and optional upstream `/v1/models` check."""
        try:
            resolution = self._store.resolve()
        except JevError as exc:
            return {
                "configured": False,
                "error": exc.message,
                "hint": "Set TYPESAFE_API_KEY or run `typesafe-jev-mcp auth set-key`.",
            }

        report: dict[str, Any] = {
            "configured": True,
            "credential_source": resolution.source,
            "masked_key": resolution.key.masked,
            "key_fingerprint": resolution.key.fingerprint,
            "standard_format": resolution.key.is_standard_format,
        }
        if not verify_upstream:
            return report

        try:
            models, latency_ms = await self._gateway.list_models()
            report["upstream_ok"] = True
            report["latency_ms"] = latency_ms
            report["available_models"] = models
        except JevError as exc:
            report["upstream_ok"] = False
            report["upstream_error"] = exc.message
        return report

    @staticmethod
    def _coerce_question(qid: str, spec: dict[str, Any] | QuestionItem) -> QuestionItem:
        if isinstance(spec, (NoulQuestion, ChoiceQuestion, ScoreQuestion, BoxQuestion)):
            return spec
        if not isinstance(spec, dict):
            raise ValidationError(
                f"Question '{qid}' must be an object with 'type' and 'instructions'."
            )
        qtype = spec.get("type", "noul")
        if qtype == "noul":
            return NoulQuestion.model_validate(spec)
        if qtype == "choice":
            return ChoiceQuestion.model_validate(spec)
        if qtype == "score":
            return ScoreQuestion.model_validate(spec)
        if qtype == "box":
            return BoxQuestion.model_validate(spec)
        raise ValidationError(
            f"Unsupported question type '{qtype}' in '{qid}'. "
            "Expected 'noul', 'choice', 'score', or 'box'."
        )

    @staticmethod
    def _format_answer(answer: AnswerItem) -> dict[str, Any]:
        if isinstance(answer, NoulAnswer):
            return {
                "type": "noul",
                "noul": answer.noul,
                "verdict": answer.noul >= 0.5,
                "confidence": answer.confidence,
                "normalized": answer.normalized_value,
            }
        if isinstance(answer, ChoiceAnswer):
            return {
                "type": "choice",
                "choice": answer.choice,
                "probabilities": answer.probabilities,
                "confidence": answer.confidence,
            }
        if isinstance(answer, ScoreAnswer):
            return {
                "type": "score",
                "score": answer.score,
                "normalized": answer.normalized_value,
                "confidence": answer.confidence,
                "probabilities": answer.probabilities,
                "legend": answer.legend,
            }
        if isinstance(answer, BoxAnswer):
            return {
                "type": "box",
                "box": answer.box.model_dump(),
                "confidence": answer.confidence,
            }
        return answer.model_dump()

    @staticmethod
    def _compute_composite(
        answers: dict[str, AnswerItem],
        weights: dict[str, float],
    ) -> float:
        total_weight = 0.0
        weighted_sum = 0.0
        for qid, weight in weights.items():
            ans = answers.get(qid)
            if ans is None or weight == 0.0:
                continue
            if isinstance(ans, (NoulAnswer, ScoreAnswer)):
                weighted_sum += ans.normalized_value * weight
                total_weight += abs(weight)
        if total_weight == 0.0:
            return 0.0
        return round(weighted_sum / total_weight, 6)
