from typing import List, Optional

from pydantic import BaseModel, Field, validator


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
    generatedImages: List[ImageRecord] = Field(default_factory=list)
    brandingDetails: str = ""
    marketingDetails: str = ""
    futureCampaigns: str = ""

    @validator("products")
    def products_must_have_two(cls, v):
        uniq = [p.strip() for p in v if p.strip()]
        if len(set(uniq)) < 2:
            raise ValueError("Please provide at least two different products")
        return uniq
