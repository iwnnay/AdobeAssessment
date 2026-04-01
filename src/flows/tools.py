"""
Custom Tools for CrewAI Agents using Gemini Pro API
"""
import os
from typing import Type, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from PIL import Image as PILImage
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini client with new API
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class BrandingExtractionInput(BaseModel):
    """Input schema for BrandingExtractionTool."""
    image_paths: List[str] = Field(..., description="List of image file paths to analyze")
    target_audience: str = Field(..., description="Target audience for the campaign")
    campaign_message: str = Field(..., description="Campaign message")
    products: List[str] = Field(..., description="List of products in the campaign")


class BrandingExtractionTool(BaseTool):
    name: str = "Branding Extraction Tool"
    description: str = "Analyzes images and campaign details to extract branding guidelines for image generation"
    args_schema: Type[BaseModel] = BrandingExtractionInput

    def _run(self, image_paths: List[str], target_audience: str, campaign_message: str, products: List[str]) -> str:
        """Extract branding details using Gemini Pro Vision."""
        try:
            prompt = f"""Analyze these images for a marketing campaign with the following details:
Products: {', '.join(products)}
Target Audience: {target_audience}
Campaign Message: {campaign_message}

As a branding expert with 25 years of experience, provide:
1. Logo characteristics (colors, style, placement preferences)
2. Brand color palette and typography style
3. Visual tone and aesthetic (modern, classic, playful, professional, etc.)
4. Key brand elements that should be included in generated images
5. Elements to avoid that might clash with brand identity

Format your response as a structured branding guide suitable for image generation."""

            # Build content parts
            contents = [prompt]

            # Add images if available
            for path in image_paths[:3]:  # Limit to first 3 images
                if os.path.exists(path):
                    with open(path, 'rb') as f:
                        image_bytes = f.read()
                    contents.append(types.Part.from_bytes(data=image_bytes, mime_type='image/png'))

            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL_NAME"),
                contents=contents
            )

            return response.text
        except Exception as e:
            return f"Error extracting branding details: {str(e)}"


class MarketingExtractionInput(BaseModel):
    """Input schema for MarketingExtractionTool."""
    target_region: str = Field(..., description="Target region/market")
    target_audience: str = Field(..., description="Target audience")
    campaign_message: str = Field(..., description="Campaign message")


class MarketingExtractionTool(BaseTool):
    name: str = "Marketing Extraction Tool"
    description: str = "Analyzes target region and audience to extract marketing insights and trends"
    args_schema: Type[BaseModel] = MarketingExtractionInput

    def _run(self, target_region: str, target_audience: str, campaign_message: str) -> str:
        """Extract marketing details using Gemini Pro."""
        try:
            prompt = f"""As a global marketing researcher specialized in localized campaigns, analyze:
Target Region: {target_region}
Target Audience: {target_audience}
Campaign Message: {campaign_message}

Provide:
1. Primary language and cultural considerations for {target_region}
2. Current visual and social trends relevant to {target_audience} in this region
3. Refined marketing message with professional guardrails
4. Audience engagement strategies to attract new customers
5. Performance optimization recommendations

Focus on creating compelling, culturally-appropriate content that drives engagement."""

            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL_NAME"),
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error extracting marketing details: {str(e)}"


class ImageSummaryInput(BaseModel):
    """Input schema for ImageSummaryTool."""
    branding_details: str = Field(..., description="Branding details from branding extraction")
    marketing_details: str = Field(..., description="Marketing details from marketing extraction")
    campaign_message: str = Field(..., description="Campaign message")
    aspect_ratio: str = Field(..., description="Target aspect ratio (1:1, 9:16, or 16:9)")


class ImageSummaryTool(BaseTool):
    name: str = "Image Summary Tool"
    description: str = "Creates detailed image generation prompts from branding and marketing details"
    args_schema: Type[BaseModel] = ImageSummaryInput

    def _run(self, branding_details: str, marketing_details: str, campaign_message: str, aspect_ratio: str) -> str:
        """Create image generation summary."""
        try:
            prompt = f"""As an AI image generation expert, create a detailed image generation prompt for:

Aspect Ratio: {aspect_ratio}
Campaign Message: {campaign_message}

Branding Guidelines:
{branding_details}

Marketing Context:
{marketing_details}

Create a comprehensive image generation prompt that:
1. Incorporates all key branding elements
2. Aligns with marketing strategy and audience preferences
3. Optimizes composition for {aspect_ratio} format
4. Specifies what should and should NOT be included
5. Ensures the campaign message is visually communicated

Provide a structured prompt suitable for AI image generation."""

            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL_NAME"),
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error creating image summary: {str(e)}"


class BrandingReportInput(BaseModel):
    """Input schema for BrandingReportTool."""
    generated_image_path: str = Field(..., description="Path to generated image")
    logo_path: str = Field(..., description="Path to the logo file")
    branding_details: str = Field(..., description="Original branding details")


class BrandingReportTool(BaseTool):
    name: str = "Branding Report Tool"
    description: str = "Evaluates a single generated image against branding guidelines and verifies logo inclusion"
    args_schema: Type[BaseModel] = BrandingReportInput

    def _run(self, generated_image_path: str, logo_path: str, branding_details: str) -> str:
        """Evaluate a single image against branding and verify logo inclusion."""
        try:
            prompt = f"""As a branding expert with 25 years of experience, evaluate this generated campaign image against the branding guidelines.

Branding Guidelines:
{branding_details}

IMPORTANT TASK: Compare the generated image with the provided logo reference to determine if the logo appears in the generated image.

Provide:
1. Overall branding alignment score (0-10)
2. Logo Detection - Is the input logo visible in the generated image? (Answer YES or NO, then explain what you see)
3. What's working well in terms of branding
4. What could be improved
5. Specific recommendations for refinement

Provide a detailed branding report for this image."""

            # Build content parts
            contents = [prompt]

            # Add generated image
            if os.path.exists(generated_image_path):
                with open(generated_image_path, 'rb') as f:
                    image_bytes = f.read()
                contents.append(types.Part.from_bytes(data=image_bytes, mime_type='image/png'))
                contents.append("This is the generated campaign image to evaluate.")

            # Add logo reference
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    logo_bytes = f.read()
                contents.append(types.Part.from_bytes(data=logo_bytes, mime_type='image/png'))
                contents.append("This is the logo that should be present in the generated image.")

            if len(contents) == 1:
                contents[0] += "\n\nNote: No images were provided for evaluation."

            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL_NAME"),
                contents=contents
            )

            return response.text
        except Exception as e:
            return f"Error generating branding report: {str(e)}"


class FutureCampaignsInput(BaseModel):
    """Input schema for FutureCampaignsTool."""
    campaign_brief: dict = Field(..., description="Current campaign details")
    branding_details: str = Field(..., description="Branding details")
    marketing_details: str = Field(..., description="Marketing details")


class FutureCampaignsTool(BaseTool):
    name: str = "Future Campaigns Tool"
    description: str = "Generates 3 future campaign ideas for the next 3 months"
    args_schema: Type[BaseModel] = FutureCampaignsInput

    def _run(self, campaign_brief: dict, branding_details: str, marketing_details: str) -> str:
        """Generate future campaign ideas."""
        try:
            prompt = f"""As a marketing manager specializing in multi-month campaigns, create 3 future campaign ideas based on:

Current Campaign:
Products: {campaign_brief.get('products', [])}
Target Region: {campaign_brief.get('target_region', '')}
Target Audience: {campaign_brief.get('target_audience', '')}
Campaign Message: {campaign_brief.get('campaign_message', '')}

Branding Context:
{branding_details}

Marketing Context:
{marketing_details}

For each of the next 3 months, provide:
1. Campaign Name
2. Campaign Brief (products, target audience, message)
3. Strategic rationale (why this is the logical next step)
4. Expected outcomes and KPIs
5. How it builds on the current campaign

Focus on long-term strategy and sustained audience engagement."""

            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL_NAME"),
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error generating future campaigns: {str(e)}"
