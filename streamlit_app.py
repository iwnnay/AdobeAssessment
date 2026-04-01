import json
import os
import io
from typing import List, Optional, Dict

import streamlit as st
from pydantic import BaseModel, Field, validator
from PIL import Image as PILImage, ImageDraw, ImageFont


# ---------------------- Models ----------------------

class ImageRecord(BaseModel):
    aspectRatio: str
    path: str


class Campaign(BaseModel):
    id: int
    name: str
    products: List[str]
    target_region: str
    target_audience: str
    campaign_message: str
    language: str = "US_en"
    approved: bool = False
    initialImages: List[ImageRecord] = Field(default_factory=list)
    generatedImages: List[ImageRecord] = Field(default_factory=list)
    brandingDetails: str = ""
    brandingReport: str = ""
    marketingDetails: str = ""
    futureCampaigns: str = ""
    logoImage: Optional[ImageRecord] = None

    @validator("products")
    def products_must_have_two(cls, v):
        uniq = [p.strip() for p in v if p.strip()]
        if len(set(uniq)) < 2:
            raise ValueError("Please provide at least two different products")
        return uniq


# ---------------------- Database ----------------------

DB_PATH = os.path.join(os.getcwd(), "database.json")


class Database:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read(self) -> List[Dict]:
        with open(self.path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _write(self, data: List[Dict]):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def next_id(self) -> int:
        data = self._read()
        return (max([row.get("id", 0) for row in data]) + 1) if data else 1

    def add(self, campaign: Campaign) -> Campaign:
        data = self._read()
        data.append(json.loads(campaign.json()))
        self._write(data)
        return campaign

    def update(self, campaign: Campaign):
        data = self._read()
        for i, row in enumerate(data):
            if row.get("id") == campaign.id:
                data[i] = json.loads(campaign.json())
                self._write(data)
                return
        raise KeyError(f"Campaign {campaign.id} not found")

    def get(self, id_: int) -> Optional[Campaign]:
        data = self._read()
        for row in data:
            if row.get("id") == id_:
                return Campaign(**row)
        return None

    def all(self) -> List[Campaign]:
        return [Campaign(**row) for row in self._read()]


# ---------------------- Utils ----------------------

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
    # Allow small tolerance
    def close(a, b, tol=0.02):
        return abs(a - b) <= tol

    for key, val in RATIO_BUCKETS.items():
        if close(aspect, val):
            return key
    return "general"


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def save_uploaded_images(campaign_id: int, images: List[io.BytesIO]) -> List[ImageRecord]:
    saved: List[ImageRecord] = []
    base_dir = os.path.join("storage", f"campaign_{campaign_id}")
    ensure_dir(base_dir)
    for idx, file in enumerate(images):
        img = PILImage.open(file).convert("RGBA")
        bucket = detect_ratio_bucket(img)
        sub = "general" if bucket == "general" else bucket.replace(":", "x")
        out_dir = os.path.join(base_dir, sub)
        ensure_dir(out_dir)
        out_path = os.path.join(out_dir, f"initial_{idx+1}.png")
        img.save(out_path)
        saved.append(ImageRecord(aspectRatio=bucket, path=os.path.relpath(out_path)))
    return saved


def generate_placeholder(width: int, height: int, text: str) -> PILImage.Image:
    img = PILImage.new("RGB", (width, height), color=(240, 242, 246))
    draw = ImageDraw.Draw(img)
    # Simple gradient bands
    for y in range(height):
        shade = int(200 + 55 * (y / max(1, height)))
        draw.line([(0, y), (width, y)], fill=(shade, 220, 255))
    # Overlay text centered
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    tw, th = draw.textsize(text, font=font)
    draw.rectangle([(0, height - th - 20), (width, height)], fill=(0, 0, 0, 128))
    draw.text(((width - tw) / 2, height - th - 10), text, fill=(255, 255, 255), font=font)
    return img


def overlay_logo(base: PILImage.Image, logo_path: Optional[str]) -> PILImage.Image:
    # Deprecated: The logo is no longer composited via Pillow.
    # It should be provided to the image generation service (e.g., Gemini Pro) instead.
    return base


def required_ratios(initial: List[ImageRecord]) -> List[str]:
    have = {img.aspectRatio for img in initial if img.aspectRatio in RATIO_BUCKETS}
    return [r for r in RATIO_BUCKETS.keys() if r not in have]


# ---------------------- Image Generator (stub) ----------------------

class ImageGenerator:
    def __init__(self, storage_root: str = "storage", outputs_root: str = "images"):
        self.storage_root = storage_root
        self.outputs_root = outputs_root

    def extract_details(self, campaign: Campaign, initial_images: List[ImageRecord]) -> Campaign:
        # Very light heuristic placeholders
        campaign.brandingDetails = (
            f"Branding should emphasize: {', '.join(campaign.products)}.\n"
            f"Tone: clean, modern, energetic.\n"
            f"Use color accents aligned with region {campaign.target_region}."
        )
        campaign.marketingDetails = (
            f"Audience: {campaign.target_audience}.\n"
            f"Message focus: '{campaign.campaign_message}'.\n"
            f"Trends: short-form, high-contrast visuals, clear CTA."
        )
        campaign.language = "US_en" if campaign.target_region.upper() in {"US", "USA", "UNITED STATES"} else "EN"

        # Stubbed logo extraction: in a real system, this would be handled by an agent calling Gemini Pro
        if initial_images:
            first_path = initial_images[0].path
            abs_path = os.path.abspath(first_path)
            try:
                img = PILImage.open(abs_path).convert("RGBA")
                # Create a small square with average color as a "logo"
                logo = PILImage.new("RGBA", (256, 256), (255, 255, 255, 0))
                draw = ImageDraw.Draw(logo)
                draw.ellipse((0, 0, 256, 256), fill=(30, 144, 255, 220))
                logo_dir = os.path.join(self.storage_root, f"campaign_{campaign.id}", "logo")
                ensure_dir(logo_dir)
                logo_path = os.path.join(logo_dir, "logo.png")
                logo.save(logo_path)
                campaign.logoImage = ImageRecord(aspectRatio="square", path=os.path.relpath(logo_path))
            except Exception:
                campaign.logoImage = None
        else:
            campaign.logoImage = None
        return campaign

    def generate_with_gemini(self, size, campaign: Campaign) -> PILImage.Image:
        """
        Placeholder for a Gemini Pro image generation call.
        In production, pass brandingDetails, marketingDetails, campaign_message, required aspect ratio,
        and optional campaign.logoImage.path to the generation request. Here we fallback to a local placeholder.
        """
        text = f"{campaign.campaign_message[:80]}"
        return generate_placeholder(*size, text=text)

    def generate_missing(self, campaign: Campaign) -> Campaign:
        to_make = required_ratios(campaign.initialImages)
        if not to_make:
            return campaign
        # Save generated outputs under images/campaign{campaignId}/{ratio}.png
        # Note: Windows does not allow ':' in filenames, so we store filenames as 1x1.png, 9x16.png, 16x9.png
        out_dir = os.path.join(self.outputs_root, f"campaign{campaign.id}")
        ensure_dir(out_dir)
        for ratio in to_make:
            if ratio == "1:1":
                size = (1024, 1024)
            elif ratio == "9:16":
                size = (1080, 1920)
            else:  # 16:9
                size = (1600, 900)
            # Use Gemini Pro (stubbed) to generate the image; logo is provided to the model, not overlaid here
            img = self.generate_with_gemini(size, campaign)
            ratio_fname = ratio.replace(":", "x") + ".png"
            out_path = os.path.join(out_dir, ratio_fname)
            img.convert("RGB").save(out_path)
            campaign.generatedImages.append(
                ImageRecord(aspectRatio=ratio, path=os.path.relpath(out_path))
            )
        return campaign

    def evaluate_and_plan(self, campaign: Campaign) -> Campaign:
        campaign.brandingReport = (
            "Branding Alignment Score: 7/10.\n"
            "Positives: Clear message placement, consistent palette.\n"
            "Improvements: Increase logo contrast on 9:16, add subtle product highlight."
        )
        campaign.futureCampaigns = (
            "Month 1: Product education carousel focusing on convenience.\n"
            "Month 2: UGC remix with regional influencers.\n"
            "Month 3: Seasonal promo with localized CTA."
        )
        return campaign


# ---------------------- Frontend (Streamlit) ----------------------

st.set_page_config(page_title="Campaign Generator", layout="wide")

db = Database()
generator = ImageGenerator()


def create_campaign_from_form(name: str, products_csv: str, region: str, audience: str, message: str) -> Campaign:
    products = [p.strip() for p in products_csv.split(",") if p.strip()]
    new_id = db.next_id()
    campaign = Campaign(
        id=new_id,
        name=name.strip(),
        products=products,
        target_region=region.strip(),
        target_audience=audience.strip(),
        campaign_message=message.strip(),
    )
    return campaign


def create_campaign_from_brief(brief: Dict) -> Campaign:
    new_id = db.next_id()
    campaign = Campaign(
        id=new_id,
        name=brief.get("name") or f"Campaign {new_id}",
        products=brief["products"],
        target_region=brief["target_region"],
        target_audience=brief["target_audience"],
        campaign_message=brief["campaign_message"],
        language=brief.get("language", "US_en"),
    )
    return campaign


def show_campaign(campaign: Campaign):
    col_left, col_right = st.columns([4, 1])
    with col_left:
        st.markdown(f"## {campaign.name}")
        st.write(
            {
                "Products": campaign.products,
                "Region": campaign.target_region,
                "Audience": campaign.target_audience,
                "Message": campaign.campaign_message,
                "Language": campaign.language,
            }
        )
    with col_right:
        # Shareable link
        share_key = f"{slugify(campaign.name)}-{campaign.id}"
        st.text_input("Share link", value=f"?c={share_key}", help="Copy and share this suffix.")
        # Approval toggle
        color = "green" if campaign.approved else "red"
        label = "Approved" if campaign.approved else "Needs Approval"
        if st.button(label, type="secondary"):
            campaign.approved = not campaign.approved
            db.update(campaign)
            st.experimental_rerun()
        st.markdown(f"Status: :{color}[{label}]")

    # Images grid
    st.markdown("### Images")
    imgs = campaign.generatedImages + campaign.initialImages
    if imgs:
        cols = st.columns(3)
        for i, rec in enumerate(sorted(imgs, key=lambda r: r.aspectRatio)):
            with cols[i % 3]:
                try:
                    st.image(os.path.abspath(rec.path), caption=f"{rec.aspectRatio}")
                except Exception:
                    st.write(rec.path)
    else:
        st.info("No images yet.")

    st.markdown("### Branding Report")
    st.write(campaign.brandingReport or "No report yet.")

    st.markdown("### Future Campaigns")
    st.write(campaign.futureCampaigns or "No plans yet.")

    with st.expander("Branding Details"):
        st.write(campaign.brandingDetails or "-")
    with st.expander("Marketing Details"):
        st.write(campaign.marketingDetails or "-")


def run_generation_flow(campaign: Campaign, uploaded_images: List[io.BytesIO]) -> Campaign:
    # persist initial record first
    db.add(campaign)
    # save images
    saved = save_uploaded_images(campaign.id, uploaded_images)
    campaign.initialImages = saved
    campaign = generator.extract_details(campaign, saved)
    campaign = generator.generate_missing(campaign)
    campaign = generator.evaluate_and_plan(campaign)
    db.update(campaign)
    return campaign


def sidebar_nav() -> Optional[int]:
    st.sidebar.markdown("## Navigation")
    # Create new campaign shortcut
    if st.sidebar.button("Generate Campaign +"):
        st.session_state["page"] = "new"
    # Existing campaigns
    st.sidebar.markdown("### Previously Generated")
    for c in db.all():
        if st.sidebar.button(c.name, key=f"nav_{c.id}"):
            st.session_state["page"] = f"view:{c.id}"
    # Handle share link param
    qp = st.experimental_get_query_params()
    if "c" in qp:
        key = qp["c"][0]
        try:
            cid = int(key.split("-")[-1])
            st.session_state["page"] = f"view:{cid}"
        except Exception:
            pass
    return None


def page_new_campaign():
    st.markdown("## Generate Campaign")

    # Toggle between file upload and manual form
    use_upload = st.checkbox("Upload brief (JSON)?", value=True)

    uploaded_images = st.file_uploader(
        "Upload images (optional)", type=["png", "jpg", "jpeg"], accept_multiple_files=True
    )

    error_msgs = {}
    campaign: Optional[Campaign] = None

    if use_upload:
        uploaded_brief = st.file_uploader("Brief file (JSON only)", type=["json"], accept_multiple_files=False)
        if uploaded_brief is not None:
            try:
                data = uploaded_brief.read()
                text = data.decode("utf-8")
                brief = json.loads(text)
                if "name" not in brief:
                    brief["name"] = os.path.splitext(uploaded_brief.name)[0]
                campaign = create_campaign_from_brief(brief)
            except Exception as e:
                st.error(f"Failed to parse brief: {e}")
    else:
        with st.form("manual_form"):
            name = st.text_input("Campaign Name", value="")
            products = st.text_input("Products (comma-separated)", value="")
            region = st.text_input("Target Region/Market", value="")
            audience = st.text_input("Target Audience", value="")
            message = st.text_input("Campaign Message", value="")

            submitted = st.form_submit_button("Generate Campaign")
            if submitted:
                # validations
                if not name.strip():
                    error_msgs["name"] = "Name is required"
                prod_list = [p.strip() for p in products.split(",") if p.strip()]
                if len(set(prod_list)) < 2:
                    error_msgs["products"] = "Please enter at least two different products"
                if not region.strip():
                    error_msgs["region"] = "Region is required"
                if not audience.strip():
                    error_msgs["audience"] = "Audience is required"
                if not message.strip():
                    error_msgs["message"] = "Message is required"

                if error_msgs:
                    for k, v in error_msgs.items():
                        st.warning(f"{k}: {v}")
                else:
                    campaign = create_campaign_from_form(name, products, region, audience, message)

    # Separate generate button when using upload path
    if use_upload:
        if st.button("Generate Campaign"):
            if campaign is None:
                st.warning("Please provide a valid brief file first.")
            else:
                with st.spinner("Generating..."):
                    files = [io.BytesIO(f.read()) for f in uploaded_images] if uploaded_images else []
                    campaign = run_generation_flow(campaign, files)
                st.success("Campaign generated!")
                st.session_state["page"] = f"view:{campaign.id}"
                st.experimental_rerun()
    else:
        # Manual form handles its own submit
        if campaign is not None and not error_msgs:
            with st.spinner("Generating..."):
                files = [io.BytesIO(f.read()) for f in uploaded_images] if uploaded_images else []
                campaign = run_generation_flow(campaign, files)
            st.success("Campaign generated!")
            st.session_state["page"] = f"view:{campaign.id}"
            st.experimental_rerun()


def page_view_campaign(cid: int):
    campaign = db.get(cid)
    if not campaign:
        st.error("Campaign not found")
        return
    show_campaign(campaign)


def main():
    sidebar_nav()
    page = st.session_state.get("page", "new")
    if page == "new":
        page_new_campaign()
    elif page.startswith("view:"):
        try:
            cid = int(page.split(":")[1])
            page_view_campaign(cid)
        except Exception:
            page_new_campaign()
    else:
        page_new_campaign()


if __name__ == "__main__":
    main()
