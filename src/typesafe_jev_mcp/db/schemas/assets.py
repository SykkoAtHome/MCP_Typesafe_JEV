"""Validate image assets without exposing their contents in diagnostics."""

from __future__ import annotations

import base64
import binascii

from typesafe_jev_mcp.errors import ValidationError

MAX_IMAGE_BYTES = 16 * 1024 * 1024
IMAGE_FORMATS = {"png", "jpg", "jpeg"}


def validate_assets(assets: dict[str, dict[str, str]] | None) -> dict[str, dict[str, str]] | None:
    if assets is None:
        return None
    reference_bytes = [len(ref.encode("utf-8")) for ref in assets]
    if any(not ref.strip() for ref in assets) or any(size > 1024 for size in reference_bytes):
        raise ValidationError("Image references must be nonempty and at most 1024 UTF-8 bytes.")
    if sum(reference_bytes) > 65536:
        raise ValidationError("Image references exceed the combined 65536-byte limit.")
    return {ref: _validate_asset(asset) for ref, asset in assets.items()}


def _validate_asset(asset: dict[str, str]) -> dict[str, str]:
    if set(asset) - {"type", "format", "data_base64", "path"}:
        raise ValidationError("Image assets accept type, format, data_base64, or local path; not multipart part names.")
    if asset.get("type", "image") != "image":
        raise ValidationError("Only image assets are supported.")
    if ("path" in asset) == ("data_base64" in asset):
        raise ValidationError("Provide exactly one image source: path or data_base64.")
    if "format" in asset and asset["format"] not in IMAGE_FORMATS:
        raise ValidationError("Image format must be png, jpg, or jpeg.")
    if "path" in asset:
        if not asset["path"].strip():
            raise ValidationError("Local image path cannot be empty.")
    else:
        if "format" not in asset:
            raise ValidationError("Base64 images require a format: png, jpg, or jpeg.")
        _validate_base64(asset["data_base64"])
    return {"type": "image", **asset}


def _validate_base64(value: str) -> None:
    if not value or len(value) > 4 * ((MAX_IMAGE_BYTES + 2) // 3):
        raise ValidationError("Image data must be nonempty and at most 16 MiB after decoding.")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValidationError("Image data must use standard base64 with padding and no data: prefix or whitespace.") from exc
    if len(decoded) > MAX_IMAGE_BYTES:
        raise ValidationError("Image exceeds the 16 MiB file size limit.")
    if base64.b64encode(decoded).decode("ascii") != value:
        raise ValidationError("Image data must use canonical padded base64.")
