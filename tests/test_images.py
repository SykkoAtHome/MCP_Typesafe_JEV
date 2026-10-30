"""Image input validation and HTTP/MCP transport regression tests."""

from __future__ import annotations

import base64
import json
from email import policy
from email.parser import BytesParser
from pathlib import Path

import httpx
import pytest

from typesafe_jev_mcp.db.schemas import BoxQuestion, EvaluationRequest, NoulQuestion
from typesafe_jev_mcp.errors import ValidationError
from typesafe_jev_mcp.repositories.jev import JevGateway
from typesafe_jev_mcp.routes.mcp import create_mcp_server
from typesafe_jev_mcp.services.evaluation import EvaluationService

SYNTHETIC_KEY = "apikey_0000111122223333444455556666_aaaa1111bbbb2222cccc3333dddd4444eeee5555ffff6666"
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1sAAAAASUVORK5CYII="
)
INLINE = {"format": "png", "data_base64": base64.b64encode(PNG).decode("ascii")}


def image_request(assets: dict, **kwargs: object) -> EvaluationRequest:
    return EvaluationRequest(
        state={"photo": "image-ref"},
        questions={"q": NoulQuestion(instructions="Is `photo` red?")},
        assets=assets,
        **kwargs,
    )


@pytest.mark.parametrize("model", ["jev-latest", "jev-preview", "jev-1.14.0"])
def test_box_preserves_requested_model(model: str) -> None:
    request = EvaluationRequest(
        model=model, state="image-ref", assets={"image-ref": INLINE},
        questions={"q": BoxQuestion(instructions="the red square")},
    )
    assert request.model == model
    assert request.enable_images is True


def test_box_requires_an_image() -> None:
    with pytest.raises(ValidationError, match="image"):
        EvaluationRequest(questions={"q": BoxQuestion(instructions="the red square")})


@pytest.mark.parametrize("asset", [
    {}, {"format": "gif", "data_base64": "eA=="},
    {"data_base64": "eA=="}, {"format": "png", "data_base64": "data:image/png;base64,eA=="},
    {"format": "png", "data_base64": "eA==\n"},
    {"format": "png", "data_base64": "%%%"},
    {"format": "png", "data_base64": ""},
    {"format": "png", "data_base64": "eB=="},
    {"path": "image.png", **INLINE}, {"path": ""},
    {"part": "photo"}, {"type": "audio", **INLINE},
])
def test_invalid_image_assets_raise_domain_error(asset: dict) -> None:
    with pytest.raises(ValidationError):
        image_request({"image-ref": asset})


@pytest.mark.parametrize("reference", ["", "  ", "x" * 1025, "ą" * 513], ids=["empty", "blank", "ascii-limit", "utf8-limit"])
def test_invalid_image_reference_is_rejected(reference: str) -> None:
    with pytest.raises(ValidationError):
        image_request({reference: INLINE})


def test_inline_assets_default_to_image_type() -> None:
    request = image_request({"image-ref": INLINE})
    assert request.to_api_payload()["assets"]["image-ref"] == {"type": "image", **INLINE}


async def test_local_image_uses_multipart_and_preserves_inline_assets(tmp_path: Path) -> None:
    image_path = tmp_path / "photo.png"
    image_path.write_bytes(PNG)
    captured = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={
            "model": "jev-1.14.0", "answers": {"q": {"type": "noul", "noul": 0.9}},
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        gateway = JevGateway(explicit_api_key=SYNTHETIC_KEY, http_client=client)
        await gateway.evaluate(image_request({
            "image-ref": {"path": str(image_path)}, "inline-ref": INLINE,
        }))
    request = captured[0]
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {request.headers['content-type']}\r\n\r\n".encode() + request.content
    )
    parts = list(message.iter_parts())
    payload = json.loads(parts[0].get_payload(decode=True))
    image_asset = payload["assets"]["image-ref"]
    assert parts[0].get_param("name", header="content-disposition") == "request"
    assert image_asset["part"] == parts[1].get_param("name", header="content-disposition")
    assert parts[1].get_payload(decode=True) == PNG
    assert payload["assets"]["inline-ref"] == {"type": "image", **INLINE}
    assert str(image_path) not in json.dumps(payload)
    assert request.headers["TypeSafe-Danger-Zone-Images"] == "true"


async def test_missing_local_image_returns_domain_error(tmp_path: Path) -> None:
    gateway = JevGateway(explicit_api_key=SYNTHETIC_KEY)
    with pytest.raises(ValidationError, match="image"):
        await gateway.evaluate(image_request({"image-ref": {"path": str(tmp_path / "missing.png")}}))


async def test_inline_images_use_json_and_opt_in_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["content-type"] == "application/json"
        assert request.headers["TypeSafe-Danger-Zone-Images"] == "true"
        assert json.loads(request.content)["assets"]["image-ref"]["data_base64"] == INLINE["data_base64"]
        return httpx.Response(200, json={"model": "jev-1.14.0", "answers": {"q": {"type": "noul", "noul": 0.9}}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        gateway = JevGateway(explicit_api_key=SYNTHETIC_KEY, http_client=client)
        await gateway.evaluate(image_request({"image-ref": INLINE}))


async def test_mcp_returns_safe_validation_error_for_bad_image() -> None:
    server = create_mcp_server()
    result = await server.call_tool("jev_noul", {
        "state": "image-ref", "instructions": "Is this red?",
        "assets": {"image-ref": {"format": "png", "data_base64": "private-invalid-image"}},
    })
    assert "validation_error" in str(result)
    assert "private-invalid-image" not in str(result)


@pytest.mark.parametrize("status", [429, 529])
async def test_multipart_retry_and_request_reuse_keep_original_assets(tmp_path: Path, status: int) -> None:
    image_path = tmp_path / "photo.png"
    image_path.write_bytes(PNG)
    bodies = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["TypeSafe-Danger-Zone-Long-Context"] == "true"
        bodies.append(request.content)
        if len(bodies) == 1:
            return httpx.Response(status, headers={"retry-after": "0.01"})
        return httpx.Response(200, json={"model": "jev-1.14.0", "answers": {"q": {"type": "noul", "noul": 0.9}}})

    evaluation = image_request({"image-ref": {"path": str(image_path)}}, long_context=True)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        gateway = JevGateway(explicit_api_key=SYNTHETIC_KEY, http_client=client)
        await gateway.evaluate(evaluation)
        await gateway.evaluate(evaluation)
    assert evaluation.assets == {"image-ref": {"type": "image", "path": str(image_path)}}
    assert len(bodies) == 3
    assert all(PNG in body for body in bodies)


@pytest.mark.parametrize("data", [b"", b"not-an-image", b"x" * (16 * 1024 * 1024 + 1)], ids=["empty", "invalid", "oversized"])
async def test_unusable_local_images_are_rejected(tmp_path: Path, data: bytes) -> None:
    image_path = tmp_path / "photo.png"
    image_path.write_bytes(data)
    gateway = JevGateway(explicit_api_key=SYNTHETIC_KEY)
    with pytest.raises(ValidationError, match="image"):
        await gateway.evaluate(image_request({"image-ref": {"path": str(image_path)}}))


async def test_relative_image_path_is_rejected() -> None:
    gateway = JevGateway(explicit_api_key=SYNTHETIC_KEY)
    with pytest.raises(ValidationError, match="absolute"):
        await gateway.evaluate(image_request({"image-ref": {"path": "photo.png"}}))


def test_combined_image_reference_limit() -> None:
    assets = {f"{index:03d}" + "x" * 1021: INLINE for index in range(65)}
    with pytest.raises(ValidationError, match="65536"):
        image_request(assets)


@pytest.mark.parametrize("format", ["jpg", "jpeg"])
def test_jpeg_inline_aliases(format: str) -> None:
    request = image_request({"image-ref": {"format": format, "data_base64": "/9j/"}})
    assert request.enable_images is True


@pytest.mark.parametrize("data", [b"\xff\xd8\xff\xe0jpeg", PNG])
async def test_local_format_is_detected_from_bytes(tmp_path: Path, data: bytes) -> None:
    path = tmp_path / "image-without-extension"
    path.write_bytes(data)

    def handler(request: httpx.Request) -> httpx.Response:
        assert data in request.content
        assert b"image/jpeg" in request.content if data != PNG else b"image/png" in request.content
        return httpx.Response(200, json={"model": "jev-1.14.0", "answers": {"q": {"type": "noul", "noul": 0.9}}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        gateway = JevGateway(explicit_api_key=SYNTHETIC_KEY, http_client=client)
        await gateway.evaluate(image_request({"image-ref": {"path": str(path)}}))


ANSWERS = {
    "noul": {"type": "noul", "noul": 0.9},
    "choice": {"type": "choice", "choice": "red", "probabilities": {"red": 1.0}, "confidence": 0.9},
    "score": {"type": "score", "score": 1.0, "legend": {"0": "no", "1": "yes"}, "probabilities": {"0": 0.0, "1": 1.0}, "confidence": 0.9},
    "box": {"type": "box", "box": {"top": 0.2, "bottom": 0.8, "left": 0.1, "right": 0.9}, "confidence": 0.9},
}


def image_response(request: httpx.Request) -> httpx.Response:
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {request.headers['content-type']}\r\n\r\n".encode() + request.content
    )
    payload = json.loads(next(message.iter_parts()).get_payload(decode=True))
    assert payload["model"] == "jev-latest"
    assert payload["state"] == {"nested": ["image-ref"]}
    assert request.headers["TypeSafe-Danger-Zone-Images"] == "true"
    return httpx.Response(200, json={
        "model": "jev-1.14.0",
        "answers": {qid: ANSWERS[spec["type"]] for qid, spec in payload["questions"].items()},
    })


@pytest.mark.parametrize("tool,extra", [
    ("jev_noul", {"true_criteria": {"example": "image-ref"}}),
    ("jev_choice", {"criteria": {"red": {"examples": ["image-ref"]}}}),
    ("jev_score", {"criteria": ["no", {"example": "image-ref"}]}),
    ("jev_box", {}),
    ("jev_evaluate", {"questions": {
        "present": {"type": "noul", "instructions": {"photo": "image-ref"}},
        "location": {"type": "box", "instructions": "Find red in image-ref"},
    }}),
])
async def test_all_mcp_evaluation_tools_accept_local_images(tmp_path: Path, tool: str, extra: dict) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(PNG)
    arguments = {"state": {"nested": ["image-ref"]}, "assets": {"image-ref": {"path": str(path)}}, **extra}
    if tool != "jev_evaluate":
        arguments["instructions"] = {"question": "Find red in image-ref"}
    async with httpx.AsyncClient(transport=httpx.MockTransport(image_response)) as client:
        gateway = JevGateway(explicit_api_key=SYNTHETIC_KEY, http_client=client)
        server = create_mcp_server(EvaluationService(gateway=gateway))
        result = await server.call_tool(tool, arguments)
    structured = json.loads(result.content[0].text)
    output = structured.get("result", structured)
    assert "error" not in output
    assert output["model"] == "jev-1.14.0"
    if tool == "jev_box":
        assert output["box"]["left"] == 0.1
    elif tool == "jev_evaluate":
        assert output["answers"]["location"]["box"]["right"] == 0.9
