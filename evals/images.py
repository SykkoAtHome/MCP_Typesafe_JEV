from __future__ import annotations

import struct
import zlib
from pathlib import Path


WIDTH = 400
HEIGHT = 400
WHITE = (250, 249, 245)
INK = (45, 49, 54)
RED = (205, 65, 57)
BLUE = (57, 111, 184)
GREEN = (53, 142, 95)
YELLOW = (235, 190, 54)
PURPLE = (135, 91, 164)
GRAY = (150, 154, 160)


def _png(path: Path, pixels: bytearray) -> None:
    rows = b"".join(
        b"\x00" + pixels[y * WIDTH * 3:(y + 1) * WIDTH * 3]
        for y in range(HEIGHT)
    )

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    content = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows))
        + chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _canvas() -> bytearray:
    return bytearray(WHITE * (WIDTH * HEIGHT))


def _pixel(pixels: bytearray, x: int, y: int, color: tuple[int, int, int]) -> None:
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        offset = (y * WIDTH + x) * 3
        pixels[offset:offset + 3] = bytes(color)


def _rect(
    pixels: bytearray,
    left: int,
    top: int,
    right: int,
    bottom: int,
    color: tuple[int, int, int],
) -> None:
    for y in range(max(0, top), min(HEIGHT, bottom)):
        start = (y * WIDTH + max(0, left)) * 3
        end = (y * WIDTH + min(WIDTH, right)) * 3
        if end > start:
            pixels[start:end] = bytes(color) * ((end - start) // 3)


def _circle(
    pixels: bytearray,
    cx: int,
    cy: int,
    radius: int,
    color: tuple[int, int, int],
) -> None:
    radius_sq = radius * radius
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius_sq:
                _pixel(pixels, x, y, color)


def _asset(asset_dir: Path, name: str, shapes: list[tuple]) -> str:
    pixels = _canvas()
    for shape in shapes:
        kind, color, *coords = shape
        if kind == "rect":
            _rect(pixels, *coords, color)
        else:
            _circle(pixels, *coords, color)
    path = (asset_dir / f"{name}.png").resolve()
    _png(path, pixels)
    return str(path)


def _case(
    case_id: str,
    category: str,
    task: str,
    state: str,
    asset_paths: dict[str, str],
    answer: object,
    grading: str,
    jev: str,
    strategies: list[str],
    oracle: str,
    canonical: dict | None,
    box: dict | None = None,
    abstain: bool = False,
) -> dict:
    expected = {"answer": answer}
    if case_id == "image_leftmost_color":
        expected["normalization"] = "casefold"
    if box is not None or grading == "box":
        expected["box"] = box
    if abstain:
        expected["abstain"] = True
    return {
        "id": case_id,
        "category": category,
        "task": task,
        "state": state,
        "assets": {ref: {"path": path} for ref, path in asset_paths.items()},
        "expected": expected,
        "grading": {"kind": grading},
        "jev": jev,
        "acceptable_strategies": strategies,
        "oracle": oracle,
        "canonical": canonical,
    }


def _choice_canonical(
    state: str,
    choices: dict[str, str],
    assets: dict[str, str] | None = None,
    instructions: str = "Select the answer supported by the visual evidence.",
) -> dict:
    arguments = {
        "state": state,
        "instructions": instructions,
        "criteria": choices,
    }
    if assets:
        arguments["assets"] = {ref: {"path": path} for ref, path in assets.items()}
    return {
        "tool": "jev_choice",
        "arguments": arguments,
    }


def _box_canonical(
    state: str,
    asset_ref: str,
    asset_path: str,
    instructions: str,
) -> dict:
    return {
        "tool": "jev_box",
        "arguments": {
            "state": state,
            "assets": {asset_ref: {"path": asset_path}},
            "instructions": instructions,
        },
    }


def build_cases(asset_dir: Path) -> list[dict]:
    cases = []
    make = lambda name, shapes: _asset(asset_dir, name, shapes)

    ref = "scene_01"
    path = make("scene_01", [
        ("circle", GREEN, 72, 72, 24), ("circle", GREEN, 187, 84, 24),
        ("circle", GREEN, 304, 76, 24), ("rect", RED, 142, 220, 204, 282),
    ])
    state = f"Image reference: {ref}. Count only the green circles."
    cases.append(_case(
        "image_count_green_circles", "image",
        "How many green circles are in the image? Return the matching count identifier as a string: '1', '2', '3', or '4'.",
        state, {ref: path}, "3", "exact", "optional",
        ["visual_counting", "jev_choice"],
        "Three green circles are visible near the top; a red square is a distractor.",
        _choice_canonical(state, {"1": "One green circle", "2": "Two green circles", "3": "Three green circles", "4": "Four green circles"}, {ref: path}),
    ))

    ref = "scene_02"
    path = make("scene_02", [
        ("rect", YELLOW, 52, 68, 158, 174), ("circle", BLUE, 229, 74, 45),
        ("rect", GRAY, 260, 236, 342, 318),
    ])
    state = f"Image reference: {ref}. Objects: A=yellow object, B=blue object, C=gray object."
    cases.append(_case(
        "image_color_shape_match", "image",
        "Which object is a circle? Return A, B, or C.",
        state, {ref: path}, "B", "exact", "optional",
        ["visual_recognition", "jev_choice"],
        "The blue circle is the only circular object.",
        _choice_canonical(state, {"A": "Yellow object", "B": "Blue object", "C": "Gray object"}, {ref: path}, "Which object is a circle?"),
    ))

    ref = "scene_03"
    path = make("scene_03", [
        ("rect", PURPLE, 240, 80, 330, 145), ("circle", YELLOW, 55, 245, 28),
        ("circle", RED, 162, 112, 22), ("rect", BLUE, 290, 260, 355, 325),
    ])
    state = f"Image reference: {ref}. Identify the leftmost object."
    cases.append(_case(
        "image_leftmost_color", "image",
        "What color is the leftmost object? Return the color name.",
        state, {ref: path}, "yellow", "exact", "optional",
        ["spatial_relation", "direct_visual_answer"],
        "The yellow circle centered at x=55 is left of every other shape.",
        _choice_canonical(state, {"red": "Red circle", "yellow": "Yellow circle", "purple": "Purple rectangle", "blue": "Blue rectangle"}, {ref: path}),
    ))

    ref_a, ref_b = "scene_04a", "scene_04b"
    path_a = make("scene_04a", [
        ("circle", BLUE, 72, 76, 25), ("circle", BLUE, 180, 78, 25),
        ("rect", RED, 70, 220, 120, 275), ("rect", GRAY, 240, 230, 300, 290),
    ])
    path_b = make("scene_04b", [
        ("circle", BLUE, 85, 75, 25), ("rect", RED, 180, 210, 230, 260),
        ("rect", BLUE, 278, 220, 328, 270), ("circle", BLUE, 90, 305, 22),
    ])
    state = f"Images: {ref_a} and {ref_b}. Count all blue objects in each image."
    cases.append(_case(
        "image_compare_blue_count", "image",
        "Which image contains more blue objects? Return A or B.",
        state, {ref_a: path_a, ref_b: path_b}, "B", "exact", "optional",
        ["cross_image_comparison", "jev_choice"],
        "Image A has two blue circles. Image B has a blue circle, a blue rectangle, and another blue circle, so it has three blue objects.",
        _choice_canonical(state, {"A": "First image", "B": "Second image"}, {ref_a: path_a, ref_b: path_b}, "Which image contains more blue objects?"),
    ))

    ref_a, ref_b = "scene_05a", "scene_05b"
    path_a = make("scene_05a", [
        ("circle", RED, 98, 100, 37), ("rect", BLUE, 230, 225, 300, 295),
    ])
    path_b = make("scene_05b", [
        ("circle", BLUE, 105, 92, 35), ("rect", YELLOW, 232, 222, 302, 292),
    ])
    state = f"Images: {ref_a} and {ref_b}. Determine which one contains a red circle."
    cases.append(_case(
        "image_compare_red_circle", "image",
        "Which image contains a red circle? Return A or B.",
        state, {ref_a: path_a, ref_b: path_b}, "A", "exact", "optional",
        ["cross_image_comparison", "jev_choice"],
        "The first image has a red circle; the second has a blue circle.",
        _choice_canonical(state, {"A": "First image", "B": "Second image"}, {ref_a: path_a, ref_b: path_b}),
    ))

    box_records = [
        ("image_locate_red_square", "scene_06", [("rect", RED, 60, 80, 150, 180), ("circle", GRAY, 270, 250, 28)], "red square", {"top": 0.20, "bottom": 0.45, "left": 0.15, "right": 0.375}, "The red square occupies x=60..149 and y=80..179 pixels."),
        ("image_locate_blue_circle", "scene_07", [("circle", BLUE, 220, 50, 40), ("rect", GRAY, 45, 275, 105, 325)], "blue circle", {"top": 0.025, "bottom": 0.225, "left": 0.45, "right": 0.65}, "The blue circle's drawn extent is x=180..260 and y=10..90 pixels."),
        ("image_locate_yellow_rectangle", "scene_08", [("rect", YELLOW, 250, 220, 350, 310), ("circle", PURPLE, 80, 85, 25)], "yellow rectangle", {"top": 0.55, "bottom": 0.775, "left": 0.625, "right": 0.875}, "The yellow rectangle occupies x=250..349 and y=220..309 pixels."),
        ("image_locate_green_circle", "scene_09", [("circle", GREEN, 90, 220, 35), ("rect", RED, 260, 45, 320, 105)], "green circle", {"top": 0.4625, "bottom": 0.6375, "left": 0.1375, "right": 0.3125}, "The green circle's drawn extent is x=55..125 and y=185..255 pixels."),
        ("image_locate_purple_square", "scene_10", [("rect", PURPLE, 205, 190, 305, 290), ("circle", YELLOW, 70, 70, 24)], "purple square", {"top": 0.475, "bottom": 0.725, "left": 0.5125, "right": 0.7625}, "The purple square occupies x=205..304 and y=190..289 pixels."),
    ]
    for case_id, name, shapes, target, box, manual_extent in box_records:
        ref = name
        path = make(name, shapes)
        state = f"Image reference: {ref}. Locate the {target}."
        instructions = f"Return the normalized bounding box [top, bottom, left, right] for the {target} in image {ref}."
        cases.append(_case(
            case_id, "image", f"Locate the {target} and return its normalized bounding box.",
            state, {ref: path}, target.replace(" ", "_"), "box", "optional",
            ["visual_localization", "jev_box"],
            f"{manual_extent} Coordinates are normalized by the 400-pixel image dimensions.",
            _box_canonical(state, ref, path, instructions), box=box,
        ))

    ref = "scene_11"
    path = make("scene_11", [
        ("circle", BLUE, 80, 90, 30), ("rect", RED, 225, 235, 315, 305),
        ("circle", GREEN, 310, 100, 24),
    ])
    state = f"Image reference: {ref}. Inspect the image for a pink star."
    cases.append(_case(
        "ambiguous_absent_object", "ambiguous",
        "Is a pink star present? Answer present or absent. If absent, return no box and abstain; if present, return its normalized bounding box.",
        state, {ref: path}, "absent", "exact", "optional",
        ["object_presence_check", "jev_choice", "optional_localization", "abstention"],
        "The image contains a blue circle, a red rectangle, and a green circle; no pink star is present.",
        {
            "tool": "jev_choice",
            "arguments": {
                "state": state,
                "assets": {ref: {"path": path}},
                "instructions": "Is a pink star present?",
                "criteria": {
                    "present": "A pink star is visible",
                    "absent": "No pink star is visible",
                },
            },
        },
        box=None, abstain=True,
    ))

    return cases
