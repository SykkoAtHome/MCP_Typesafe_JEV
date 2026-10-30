"""Validate requests published through the MCP usage resources."""

import json
import re

import pytest

from typesafe_jev_mcp.db.schemas import EvaluationRequest
from typesafe_jev_mcp.routes.mcp import create_mcp_server


async def _published_examples(uri: str) -> list[dict]:
    contents = await create_mcp_server().read_resource(uri)
    text = "\n".join(item.content for item in contents)
    return [json.loads(block) for block in re.findall(r"```json\s*\n(.*?)\n```", text, re.S)]


@pytest.mark.parametrize("uri", ["jev://guide", "jev://skill"])
async def test_published_examples_are_complete_evaluation_requests(uri: str) -> None:
    examples = await _published_examples(uri)
    assert len(examples) >= 2, "Publish complete image and missing-evidence examples"
    for example in examples:
        request = EvaluationRequest.model_validate(example)
        assert request.questions
        for question in request.questions.values():
            assert question.instructions


@pytest.mark.parametrize("uri", ["jev://guide", "jev://skill"])
async def test_published_visual_example_pairs_presence_with_box(uri: str) -> None:
    examples = await _published_examples(uri)
    visual = next(example for example in examples if example.get("assets"))
    assert {q["type"] for q in visual["questions"].values()} >= {"noul", "box"}
    for reference in visual["assets"]:
        assert reference in visual["state"].values()
    assert all(asset.get("path", "").startswith("/") for asset in visual["assets"].values())


@pytest.mark.parametrize("uri", ["jev://guide", "jev://skill"])
async def test_published_missing_evidence_example_has_unknown_option(uri: str) -> None:
    examples = await _published_examples(uri)
    choices = [question for example in examples for question in example["questions"].values()
               if question["type"] == "choice"]
    assert any("unknown" in question["criteria"] and len(question["criteria"]) >= 3 for question in choices)
