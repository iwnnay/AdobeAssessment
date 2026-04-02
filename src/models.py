from typing import List, Optional

from pydantic import BaseModel, Field, validator


class MarketingExtraction(BaseModel):
    """Structured output from marketing extraction task."""
    language: str = Field(..., description="Primary language code (e.g., 'US_en', 'ES_es', 'FR_fr')")
    marketing_research: str = Field(..., description="Comprehensive marketing research and insights")


class ImageRecord(BaseModel):
    aspectRatio: str
    path: str
    brandingReport: str = ""


class Campaign(BaseModel):
    id: int
    name: str
    products: List[str]
    target_region: str
    target_audience: str
    campaign_message: str
    language: str = "US_en"
    approved: bool = False
    generated_images: List[ImageRecord] = Field(default_factory=list)
    brandingDetails: str = ""
    marketingDetails: str = ""
    futureCampaigns: str = ""
    logo_path: str = "inputs/logo.png"

    @validator("products")
    def products_must_have_two(cls, v):
        uniq = [p.strip() for p in v if p.strip()]
        if len(set(uniq)) < 2:
            raise ValueError("Please provide at least two different products")
        return uniq
