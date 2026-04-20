from __future__ import annotations
import base64
from pathlib import Path


def _b64(filename: str, mime: str = "image/png") -> str:
    # __file__ is ui/assets.py; parent.parent is the project root
    with open(Path(__file__).parent.parent / "image" / filename, "rb") as _f:
        return f"data:{mime};base64,{base64.b64encode(_f.read()).decode()}"


TEXTURE        = _b64("image_7.jpg",   "image/jpeg")
WRINKLED_PAPER = _b64("image_10.jpg",  "image/jpeg")
GREEN_PAINT    = _b64("green_paint.png")
YELLOW_PAINT   = _b64("yellow_paint.png")
RED_PAINT      = _b64("red_paint.png")
