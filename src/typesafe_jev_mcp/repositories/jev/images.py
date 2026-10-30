"""Prepare local image files for the System One multipart transport."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typesafe_jev_mcp.db.schemas.assets import MAX_IMAGE_BYTES
from typesafe_jev_mcp.errors import ValidationError

MultipartFiles = list[tuple[str, tuple[str | None, bytes, str]]]


def prepare_image_upload(payload: dict[str, Any]) -> MultipartFiles | None:
    assets = dict(payload.get("assets", {}))
    files: MultipartFiles = []
    for index, (ref, asset) in enumerate(assets.items()):
        if "path" not in asset:
            continue
        data, fmt = _read_image(asset["path"])
        part = f"image_{index}"
        assets[ref] = {"type": "image", "part": part}
        files.append((part, (f"{part}.{fmt}", data, f"image/{fmt}")))
    if not files:
        return None
    payload["assets"] = assets
    request_part = ("request", (None, json.dumps(payload).encode("utf-8"), "application/json"))
    return [request_part, *files]


def _read_image(path_value: str) -> tuple[bytes, str]:
    path = Path(path_value)
    if not path.is_absolute():
        raise ValidationError("Local image paths must be absolute paths on the MCP server host.")
    try:
        with path.open("rb") as image_file:
            data = image_file.read(MAX_IMAGE_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise ValidationError("Cannot read local image file.") from exc
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValidationError("Local image must be nonempty and at most 16 MiB.")
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return data, "png"
    if data.startswith(b"\xff\xd8\xff"):
        return data, "jpeg"
    raise ValidationError("Local image must contain PNG or JPEG data.")
