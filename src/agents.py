"""
CrewAI Agent Definitions for Campaign Generation
"""
import os

from crewai import Agent, LLM
from tools import (
    BrandingExtractionTool,
    LogoExtractionTool,
    MarketingExtractionTool,
    ImageSummaryTool,
    BrandingReportTool,
    FutureCampaignsTool
)

llm = LLM(model=os.getenv("GEMINI_MODEL_NAME"))

def create_branding_extract_agent() -> Agent:
    """
    Agent for extracting branding details from campaign brief and images.
    """
    return Agent(
        role="Branding and product marketing expert",
        goal="To evaluate a given image, target audience and campaign message to create a summary to be used in image generation that determines details about the logo, branding, and relevant product information. And to determine what should and what should not be included in the image.",
        backstory="You are a product branding expert with 25 years of experience in successful marketing campaigns.",
        tools=[BrandingExtractionTool()],
        verbose=True,
        allow_delegation=False,
        llm=llm
    )


def create_logo_extract_agent() -> Agent:
    """
    Agent for extracting logo from uploaded images using Gemini Pro.
    """
    return Agent(
        role="Logo extraction expert",
        goal="To lift the logo from a given image using advanced image analysis.",
        backstory="You are a visual analysis expert specializing in logo detection and extraction from complex images.",
        tools=[LogoExtractionTool()],
        verbose=True,
        allow_delegation=False,
        llm=llm
    )


def create_marketing_extract_agent() -> Agent:
    """
    Agent for extracting marketing details based on region, audience, and message.
    """
    return Agent(
        role="Global Marketing Researcher",
        goal="To evaluate a given region, target audience and campaign message to create a summary to be used in image generation that determines details about the language of the region, current trends for the target audience, and to customize an appropriate marketing message with professional guardrails in mind. Along with focusing the campaign on performance and trying to engage new audiences.",
        backstory="You are a global marketing researcher, intune with localized social trends and what makes a successful ad campaign.",
        tools=[MarketingExtractionTool()],
        verbose=True,
        allow_delegation=False,
        llm=llm
    )


def create_image_summary_agent() -> Agent:
    """
    Agent for creating image generation summaries from branding and marketing details.
    """
    return Agent(
        role="Image generation expert",
        goal="To evaluate a given image, branding details and marketing details to create a summary to be used in image generation that determines what should and what should not be included in the image.",
        backstory="You are an AI image generation specialist with deep understanding of prompt engineering and visual composition.",
        tools=[ImageSummaryTool()],
        verbose=True,
        allow_delegation=False,
        llm=llm
    )


def create_branding_report_agent() -> Agent:
    """
    Agent for evaluating generated images against branding guidelines.
    """
    return Agent(
        role="Branding and product marketing expert",
        goal="To evaluate a given image and branding details and produce a report scoring how closely the two align and details about what is working and what could be improved.",
        backstory="You are a product branding expert with 25 years of experience in successful marketing campaigns.",
        tools=[BrandingReportTool()],
        verbose=True,
        allow_delegation=False,
        llm=llm
    )


def create_future_campaigns_agent() -> Agent:
    """
    Agent for generating future campaign ideas.
    """
    return Agent(
        role="Marketing Manager",
        goal="To look at the given campaign brief and determine 3 future campaign ideas to be delivered on a monthly basis talking about the long term strategy and why you think it will be an efficient next step given the target audience and target region. The future campaigns need to include campaign briefs of their own.",
        backstory="You are a marketing manager specializing in multi-month campaigns.",
        tools=[FutureCampaignsTool()],
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
