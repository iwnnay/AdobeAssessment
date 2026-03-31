import argparse
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple

try:
    import yaml  # type: ignore
    YAML_AVAILABLE = True
except Exception:
    YAML_AVAILABLE = False

from PIL import Image, ImageDraw, ImageFont


ASPECT_RATIOS: Dict[str, Tuple[int, int]] = {
    "1:1": (1080, 1080),
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
}

# Simple brand settings for demo purposes
BRAND_PRIMARY = (25, 118, 210)  # Blue
BRAND_SECONDARY = (255, 193, 7)  # Amber
BRAND_TEXT = (255, 255, 255)

PROHIBITED_WORDS = [
    "guaranteed",  # risky legal claim
    "cure",        # medical claim
    "free beer",   # age-restricted implication
]


def load_brief(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
        # Try JSON first, then YAML if available
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if YAML_AVAILABLE:
                return yaml.safe_load(text)
            raise ValueError("Brief file is not valid JSON. Install pyyaml to support YAML.")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def find_or_generate_base_asset(product: str, assets_dir: str, size: Tuple[int, int]) -> Image.Image:
    """Find existing product image under assets_dir or generate a placeholder hero image."""
    # Try common extensions
    for ext in (".png", ".jpg", ".jpeg"):
        p = os.path.join(assets_dir, f"{product}{ext}")
        if os.path.isfile(p):
            try:
                return Image.open(p).convert("RGBA").resize(size)
            except Exception:
                pass

    # Generate gradient background placeholder with product name
    w, h = size
    img = Image.new("RGBA", size, BRAND_PRIMARY + (255,))
    # simple vertical gradient overlay
    grad = Image.new("RGBA", size)
    gdraw = ImageDraw.Draw(grad)
    for y in range(h):
        alpha = int(180 * (y / max(1, h - 1)))
        gdraw.line([(0, y), (w, y)], fill=BRAND_SECONDARY + (alpha,))
    img = Image.alpha_composite(img, grad)

    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    text = product
    tw, th = measure_text(draw, text, font)
    draw.rectangle([(20, 20), (20 + tw + 20, 20 + th + 20)], fill=(0, 0, 0, 100))
    draw.text((30, 30), text, font=font, fill=BRAND_TEXT)
    return img


def overlay_logo(img: Image.Image, assets_dir: str) -> Tuple[Image.Image, bool]:
    """Overlay logo if available. Returns (image, logo_present)."""
    for name in ("logo.png", "logo.jpg", "logo.jpeg"):
        p = os.path.join(assets_dir, name)
        if os.path.isfile(p):
            try:
                logo = Image.open(p).convert("RGBA")
                # scale logo to ~10% of width
                w, h = img.size
                target_w = max(64, int(w * 0.12))
                ratio = target_w / logo.width
                logo = logo.resize((target_w, int(logo.height * ratio)))
                img = img.copy()
                img.alpha_composite(logo, (w - logo.width - 24, 24))
                return img, True
            except Exception:
                return img, False
    return img, False


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        tw, _ = measure_text(draw, test, font)
        if tw <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def render_message(img: Image.Image, message: str) -> Image.Image:
    img = img.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    # Text box area near bottom
    pad = int(min(w, h) * 0.04)
    box_h = int(h * 0.26)
    box = (pad, h - box_h - pad, w - pad, h - pad)

    # semi-transparent panel
    panel = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 120))
    img.alpha_composite(panel, (box[0], box[1]))

    # Text
    font = ImageFont.load_default()
    max_text_w = box[2] - box[0] - pad * 2
    lines = wrap_text(draw, message, font, max_text_w)
    y = box[1] + pad
    for line in lines[:6]:  # avoid overflow
        draw.text((box[0] + pad, y), line, font=font, fill=BRAND_TEXT)
        _, th = measure_text(draw, line, font)
        y += th + int(pad * 0.4)
    return img


def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    """Return (width, height) of text for the given draw context and font.

    Uses ImageDraw.textbbox when available (Pillow 8.0+), with graceful
    fallbacks for older/newer versions to avoid relying on deprecated/removed
    methods like draw.textsize.
    """
    # Preferred: textbbox provides precise bounds
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        pass

    # Fallback to font.getbbox if available
    try:
        fb = font.getbbox(text)
        return fb[2] - fb[0], fb[3] - fb[1]
    except Exception:
        pass

    # Last resort: estimate using textlength (width) and a baseline height
    try:
        w = int(draw.textlength(text, font=font))  # type: ignore[attr-defined]
        # Approximate height from font metrics if possible
        try:
            ascent, descent = font.getmetrics()  # type: ignore[attr-defined]
            h = ascent + descent
        except Exception:
            h = 12
        return w, h
    except Exception:
        # Very rough fallback to avoid crashes
        return max(1, len(text) * 6), 12


def legal_checks(text: str) -> List[str]:
    issues = []
    low = text.lower()
    for w in PROHIBITED_WORDS:
        if w in low:
            issues.append(f"Contains prohibited term: '{w}'")
    return issues


def generate_creatives(brief: Dict, assets_dir: str, out_dir: str, ratios: List[str]) -> Dict:
    ensure_dir(out_dir)
    products: List[str] = brief.get("products") or []
    message: str = brief.get("campaign_message") or ""
    region: str = brief.get("target_region") or ""
    audience: str = brief.get("target_audience") or ""

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "region": region,
        "audience": audience,
        "products": {},
        "ratios": ratios,
        "notes": [],
    }

    # Simple campaign-level legal check
    report["legal_issues"] = legal_checks(message)

    for product in products:
        prod_dir = os.path.join(out_dir, safe_name(product))
        ensure_dir(prod_dir)
        prod_entries = []
        for r in ratios:
            if r not in ASPECT_RATIOS:
                report["notes"].append(f"Unsupported ratio {r}; skipping.")
                continue
            size = ASPECT_RATIOS[r]
            base = find_or_generate_base_asset(product, assets_dir, size)
            with_logo, has_logo = overlay_logo(base, assets_dir)
            final_img = render_message(with_logo, message)

            ratio_dir = os.path.join(prod_dir, r.replace(":", "x"))
            ensure_dir(ratio_dir)
            out_path = os.path.join(ratio_dir, f"{safe_name(product)}_{r.replace(':','x')}.png")
            final_img.convert("RGBA").save(out_path)

            entry = {
                "ratio": r,
                "path": out_path,
                "brand_logo_present": has_logo,
                "brand_colors_used": True,
                "legal_issues": legal_checks(message),
            }
            prod_entries.append(entry)

        report["products"][product] = prod_entries

    # Write report
    with open(os.path.join(out_dir, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


def safe_name(name: str) -> str:
    s = name.strip().lower()
    for ch in " \/:\\|?*<>\"":
        s = s.replace(ch, "_")
    return s


def parse_args():
    p = argparse.ArgumentParser(description="Creative Automation Pipeline (PoC)")
    p.add_argument("--brief", default="campaign.json", help="Path to campaign brief (JSON or YAML)")
    p.add_argument("--assets-dir", default="assets", help="Directory containing input assets (optional)")
    p.add_argument("--out-dir", default="outputs", help="Directory to save generated creatives")
    p.add_argument(
        "--ratios",
        default="1:1,9:16,16:9",
        help="Comma-separated list of aspect ratios to generate (supported: 1:1,9:16,16:9)",
    )
    return p.parse_args()


def main():
    args = parse_args()
    brief = load_brief(args.brief)
    ratios = [r.strip() for r in args.ratios.split(",") if r.strip()]
    report = generate_creatives(brief, args.assets_dir, args.out_dir, ratios)

    # Simple console summary
    total = sum(len(v) for v in report["products"].values())
    print(f"Generated {total} creatives to '{args.out_dir}'.")
    li = report.get("legal_issues") or []
    if li:
        print("Legal checks flagged issues:")
        for issue in li:
            print(f" - {issue}")
    print("Done.")


if __name__ == "__main__":
    main()
