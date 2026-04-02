import os
import io
from typing import List, Optional

from PIL import Image as PILImage, ImageDraw, ImageFont

from src.models import ImageRecord


RATIO_BUCKETS = {
    "1:1": 1 / 1,
    "9:16": 9 / 16,
    "16:9": 16 / 9,
}


def slugify(value: str) -> str:
    import re
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\-\s]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value or "campaign"


def detect_ratio_bucket(img: PILImage.Image) -> str:
    w, h = img.size
    aspect = w / h if h else 0

    def close(a, b, tol=0.02):
        return abs(a - b) <= tol

    for key, val in RATIO_BUCKETS.items():
        if close(aspect, val):
            return key
    return "general"


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def generate_placeholder(width: int, height: int, text: str) -> PILImage.Image:
    img = PILImage.new("RGB", (width, height), color=(240, 242, 246))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        shade = int(200 + 55 * (y / max(1, height)))
        draw.line([(0, y), (width, y)], fill=(shade, 220, 255))
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    # Use textbbox instead of deprecated textsize
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.rectangle([(0, height - th - 20), (width, height)], fill=(0, 0, 0, 128))
    draw.text(((width - tw) / 2, height - th - 10), text, fill=(255, 255, 255), font=font)
    return img


def overlay_logo(base: PILImage.Image, logo_path: Optional[str]) -> PILImage.Image:
    # Deprecated: The logo is no longer composited via Pillow.
    # It should be provided to the image generation service (e.g., Gemini Pro) instead.
    return base


def required_ratios() -> List[str]:
    return [r for r in RATIO_BUCKETS.keys()]
