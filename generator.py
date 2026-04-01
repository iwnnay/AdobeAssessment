import os
from typing import List, Optional

from PIL import Image as PILImage, ImageDraw

from models import Campaign, ImageRecord
from utils import ensure_dir, required_ratios, generate_placeholder


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
                _ = PILImage.open(abs_path).convert("RGBA")
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
        out_dir = os.path.join(self.outputs_root, f"campaign{campaign.id}")
        ensure_dir(out_dir)
        for ratio in to_make:
            if ratio == "1:1":
                size = (1024, 1024)
            elif ratio == "9:16":
                size = (1080, 1920)
            else:  # 16:9
                size = (1600, 900)
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
